#!/usr/bin/env python3
"""check_permission_set_expiration.py — time-boxed access shape checker.

Two independent checks, both stdlib-only:

1. ``--manifest-dir`` scans a Salesforce DX project or MDAPI package for the
   two metadata shapes that break time-boxed access:

   * ``UserManagement.settings`` — ``psaExpirationUIEnabled`` is documented as
     defaulting to ``false``. When it is absent or false, the Setup assignment
     screens show no expiration control and admins conclude the feature does
     not exist in their org. (Metadata API Developer Guide v67.0,
     UserManagementSettings.)
   * ``*.useraccesspolicy`` — ``UserAccessPolicyAction`` has exactly three
     fields: ``action``, ``target``, ``type``. Anything else inside
     ``<userAccessPolicyActions>`` is invented — most often a hallucinated
     expiration attribute — and will fail deployment. (Metadata API Developer
     Guide v67.0, UserAccessPolicy.)

2. ``--plan`` validates a JSON time-boxed assignment plan before anyone loads
   it. ``PermissionSetAssignment`` field properties from the Object Reference
   v67.0 drive the rules: ``ExpirationDate`` is the only field an admin
   updates on an existing row (``IsRevoked`` also carries the Update property,
   but user access policies own it); ``AssigneeId``, ``PermissionSetId`` and
   ``PermissionSetGroupId`` are Create-only; and only
   ``PermissionSetAssignment`` carries an expiry at all.

Exit code 0 when nothing is wrong, 1 when at least one issue is found.

Usage:
    python3 check_permission_set_expiration.py --manifest-dir force-app
    python3 check_permission_set_expiration.py --plan elevation-plan.json
    python3 check_permission_set_expiration.py --manifest-dir . --plan plan.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Documented facts this script encodes. Sources are named in the module
# docstring; do not widen these sets without a fetched citation.
# ---------------------------------------------------------------------------

# UserAccessPolicyAction has exactly these three fields.
UAP_ACTION_FIELDS = {"action", "target", "type"}

# Objects in the permission model that can carry an expiration date.
EXPIRY_CAPABLE = {"permissionSet", "permissionSetGroup"}

# PermissionSetAssignment supported calls, minus the read-only ones.
SUPPORTED_OPERATIONS = {"insert", "update", "delete"}

# Plan keys that would retarget a Create-only field on an existing row.
# AssigneeId, PermissionSetId and PermissionSetGroupId carry no Update
# property, so changing any of them is a delete plus an insert.
RETARGET_KEYS = {"newAssignee", "newPermissionSet", "newPermissionSetGroup"}

# Keys an LLM commonly invents when it assumes a duration-style API exists.
INVENTED_DURATION_KEYS = {
    "duration",
    "durationDays",
    "expiresAfterDays",
    "expiresIn",
    "ttl",
    "validForDays",
    "accessEndDate",
}

SETTINGS_FILENAMES = ("UserManagement.settings-meta.xml", "UserManagement.settings")

# ISO 8601 instant: a date, a time, and an explicit offset or Z.
ISO_INSTANT_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})$"
)
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check permission set expiration metadata and time-boxed assignment "
            "plans for the shapes that silently defeat time-boxing."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        help="Root of a Salesforce DX project or MDAPI package to scan.",
    )
    parser.add_argument(
        "--plan",
        help="Path to a JSON time-boxed assignment plan to validate.",
    )
    return parser.parse_args()


def localname(tag: str) -> str:
    """Strip the Metadata API namespace from an element tag."""
    return tag.rsplit("}", 1)[-1]


# ---------------------------------------------------------------------------
# Metadata scan
# ---------------------------------------------------------------------------


def find_settings_files(base: Path) -> list[Path]:
    found: list[Path] = []
    for name in SETTINGS_FILENAMES:
        found.extend(sorted(base.rglob(name)))
    return found


def check_user_management_settings(base: Path) -> tuple[list[str], list[str]]:
    """Return (issues, notes) for the UserManagement settings file."""
    issues: list[str] = []
    notes: list[str] = []

    files = find_settings_files(base)
    if not files:
        notes.append(
            "No UserManagement.settings file found under "
            f"{base} — the org's expiration UI state is unknown. Retrieve it with: "
            'sf project retrieve start --metadata "Settings:UserManagement"'
        )
        return issues, notes

    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            issues.append(f"[{path}] XML parse error: {exc}")
            continue

        values = {localname(child.tag): (child.text or "").strip() for child in root}
        flag = values.get("psaExpirationUIEnabled")
        if flag is None:
            issues.append(
                f"[{path}] psaExpirationUIEnabled is absent. Its documented default "
                "is false, so the Setup assignment screens will show no expiration "
                "control. Add <psaExpirationUIEnabled>true</psaExpirationUIEnabled>."
            )
        elif flag.lower() != "true":
            issues.append(
                f"[{path}] psaExpirationUIEnabled is '{flag}'. Admins working through "
                "Setup cannot set an expiration date while it is not true."
            )
        else:
            notes.append(f"[{path}] psaExpirationUIEnabled = true.")

        if values.get("userAccessPoliciesEnabled", "").lower() == "true":
            notes.append(
                f"[{path}] userAccessPoliciesEnabled = true — assignment rows also "
                "carry IsRevoked, and revoked rows need ALL ROWS to retrieve. Audit "
                "queries must cover that population separately from IsActive = false."
            )
    return issues, notes


def check_user_access_policies(base: Path) -> tuple[list[str], list[str]]:
    """Return (issues, notes) for UserAccessPolicy action shapes."""
    issues: list[str] = []
    notes: list[str] = []

    files = sorted(base.rglob("*.useraccesspolicy-meta.xml"))
    files += sorted(base.rglob("*.useraccesspolicy"))
    if not files:
        return issues, notes

    for path in sorted(set(files)):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            issues.append(f"[{path}] XML parse error: {exc}")
            continue

        actions = [c for c in root if localname(c.tag) == "userAccessPolicyActions"]
        if not actions:
            notes.append(f"[{path}] no userAccessPolicyActions elements.")
            continue

        for index, action in enumerate(actions, start=1):
            present = {localname(field.tag) for field in action}
            unknown = sorted(present - UAP_ACTION_FIELDS)
            if unknown:
                issues.append(
                    f"[{path}] userAccessPolicyActions[{index}] contains "
                    f"{', '.join(unknown)}. UserAccessPolicyAction has exactly three "
                    "fields — action, target, type. A user access policy cannot carry "
                    "an expiration; use PermissionSetAssignment.ExpirationDate instead."
                )
            missing = sorted(UAP_ACTION_FIELDS - present)
            if missing:
                issues.append(
                    f"[{path}] userAccessPolicyActions[{index}] is missing required "
                    f"field(s): {', '.join(missing)}."
                )
        notes.append(f"[{path}] {len(actions)} policy action(s) checked.")
    return issues, notes


# ---------------------------------------------------------------------------
# Assignment-plan validation
# ---------------------------------------------------------------------------


def check_plan(path: Path) -> tuple[list[str], list[str]]:
    """Validate a JSON time-boxed assignment plan.

    Expected shape — a list, or an object with an "assignments" list:

        [
          {
            "assignee": "user@example.com",
            "permissionSet": "PS_Temp_ManageUsers",
            "expirationDate": "2026-09-30T23:00:00Z",
            "approver": "security-lead@example.com",
            "operation": "insert"
          }
        ]
    """
    issues: list[str] = []
    notes: list[str] = []

    if not path.exists():
        return [f"Plan file not found: {path}"], notes

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"[{path}] could not be read as JSON: {exc}"], notes

    if isinstance(data, dict):
        data = data.get("assignments", data.get("plan", []))
    if not isinstance(data, list):
        return [
            f"[{path}] expected a JSON list of assignments, or an object with an "
            "'assignments' list."
        ], notes
    if not data:
        return [f"[{path}] contains no assignments."], notes

    for index, row in enumerate(data, start=1):
        label = f"[{path}] assignment {index}"
        if not isinstance(row, dict):
            issues.append(f"{label}: expected an object, got {type(row).__name__}.")
            continue

        invented = sorted(set(row) & INVENTED_DURATION_KEYS)
        if invented:
            issues.append(
                f"{label}: {', '.join(invented)} is not a Salesforce concept. "
                "PermissionSetAssignment.ExpirationDate is an absolute dateTime; "
                "there is no duration-style API."
            )

        if not row.get("assignee"):
            issues.append(f"{label}: 'assignee' is required.")

        targets = [key for key in EXPIRY_CAPABLE if row.get(key)]
        if not targets:
            issues.append(
                f"{label}: name exactly one of permissionSet or permissionSetGroup. "
                "Only PermissionSetAssignment carries an expiry — profiles, permission "
                "set licences, muting permission sets and group membership cannot."
            )
        elif len(targets) > 1:
            issues.append(
                f"{label}: names both {' and '.join(targets)}. One assignment row "
                "grants one permission set OR one permission set group, never both."
            )

        operation = str(row.get("operation", "insert")).lower()
        if operation not in SUPPORTED_OPERATIONS:
            issues.append(
                f"{label}: operation '{operation}' is not supported. "
                f"PermissionSetAssignment supports {', '.join(sorted(SUPPORTED_OPERATIONS))}."
            )
        if operation == "update":
            if not row.get("assignmentId"):
                issues.append(
                    f"{label}: operation 'update' needs an assignmentId naming the "
                    "existing row whose ExpirationDate is being extended."
                )
            retargets = sorted(set(row) & RETARGET_KEYS)
            if retargets:
                issues.append(
                    f"{label}: operation 'update' carries {', '.join(retargets)}. "
                    "AssigneeId, PermissionSetId and PermissionSetGroupId are Create-only "
                    "— retargeting is a delete plus an insert. Only ExpirationDate can be "
                    "updated in place."
                )

        expiry = row.get("expirationDate")
        if expiry in (None, ""):
            issues.append(
                f"{label}: no expirationDate. The field is Nillable, so nothing rejects "
                "a permanent grant — this is how a time-boxing programme accumulates "
                "standing privilege. Set a date or move the grant out of this plan."
            )
        elif not isinstance(expiry, str):
            issues.append(f"{label}: expirationDate must be a string, got {type(expiry).__name__}.")
        elif DATE_ONLY_RE.match(expiry):
            issues.append(
                f"{label}: expirationDate '{expiry}' is date-only. ExpirationDate is a "
                "dateTime — write a full instant with an explicit offset (for example "
                f"'{expiry}T23:00:00Z') so the cutoff is unambiguous."
            )
        elif not ISO_INSTANT_RE.match(expiry):
            issues.append(
                f"{label}: expirationDate '{expiry}' is not an ISO 8601 instant with an "
                "explicit offset or Z."
            )

        if not row.get("approver"):
            notes.append(
                f"{label}: no approver recorded. The assignment row stores the date and "
                "nothing else — capture the approver and justification outside it."
            )

    notes.append(f"[{path}] {len(data)} assignment(s) checked.")
    return issues, notes


# ---------------------------------------------------------------------------


def main() -> int:
    args = parse_args()

    if not args.manifest_dir and not args.plan:
        print(
            "Nothing to check. Pass --manifest-dir to scan a Salesforce project, "
            "--plan to validate a JSON assignment plan, or both.\n",
            file=sys.stderr,
        )
        print("Run with --help for usage.", file=sys.stderr)
        return 1

    issues: list[str] = []
    notes: list[str] = []

    if args.manifest_dir:
        base = Path(args.manifest_dir).resolve()
        if not base.is_dir():
            print(f"ERROR: not a directory: {base}", file=sys.stderr)
            return 1
        print(f"Scanning metadata: {base}\n")
        for check in (check_user_management_settings, check_user_access_policies):
            found_issues, found_notes = check(base)
            issues.extend(found_issues)
            notes.extend(found_notes)

    if args.plan:
        plan_path = Path(args.plan).resolve()
        print(f"Validating plan: {plan_path}\n")
        found_issues, found_notes = check_plan(plan_path)
        issues.extend(found_issues)
        notes.extend(found_notes)

    for note in notes:
        print(f"NOTE : {note}")
    if notes:
        print()

    if issues:
        print(f"Issues found ({len(issues)}):", file=sys.stderr)
        for issue in issues:
            print(f"ISSUE: {issue}", file=sys.stderr)
        return 1

    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
