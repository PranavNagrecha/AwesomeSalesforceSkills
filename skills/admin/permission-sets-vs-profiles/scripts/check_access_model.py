#!/usr/bin/env python3
"""Audit Salesforce profiles and permission sets for risky access grants.

Two entry shapes, both supported:

    check_access_model.py force-app/main/default          # positional paths (legacy)
    check_access_model.py --manifest-dir force-app/main/default

Checks
------
1. HIGH   dangerous system permissions and object-level sharing bypass on any file
2. HIGH   a profile carrying object/field permissions or system permissions outside
          the documented residue allow-list -- those belong in a permission set.
          Kept blocking (not downgraded to WARN) alongside check 1: a permission
          still sitting on a profile after a permission-set-led decomposition is
          exactly the residual-access bug this skill exists to catch.
3. ERROR  a permission set carrying an element that only a Profile can hold
          (loginHours, loginIpRanges, layoutAssignments, `default` app/record type,
          tabVisibilities), which the PermissionSet schema has no home for
4. WARN   a standard profile (`custom` = false) carrying object-permission edits;
          editing standard objects on standard profiles is disabled in API 50.0+
5. INFO   the same object granted by both a profile and a permission set reachable
          through a permission set group -- redundant grant, ambiguous revocation
6. PSVP-DESC-01 (ERROR) / PSVP-DESC-02 (WARN) -- `description` length on any
          Profile, PermissionSet, or PermissionSetGroup file. PermissionSet.description
          and Profile.description are both "Limit: 255 characters" in the Metadata API
          Developer Guide (api_meta L94788, L97678). Empirically confirmed by
          `sf project deploy start --dry-run` against a Summer '26 developer org on
          2026-09-11: four PermissionSet files and three Profile files were rejected
          with `Description: data value too large ... (max length=255)`
          (examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md, once exported).
          PermissionSetGroup.description carries no documented limit (api_meta L95328)
          -- UNVERIFIED (2026-09-11) as a direct rejection; the same 255-character
          threshold is applied here anyway because a PSG that references a rejected
          member PermissionSet fails to deploy as a cascade ("permission set names
          are invalid") regardless of its own description length.

Exit policy
-----------
Exit 1 only on CRITICAL/ERROR/HIGH-class findings -- checks 1, 2, 3, and
PSVP-DESC-01. WARN/INFO findings (checks 4, 5, PSVP-DESC-02, and an empty scan)
print but exit 0; pass --strict to promote every finding to a failure. A
missing --manifest-dir is a usage error, not a finding, and exits 1 immediately
with a single-line message on stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


DANGEROUS_PERMISSIONS = {
    "ViewAllData",
    "ModifyAllData",
    "ManageUsers",
    "AuthorApex",
    "CustomizeApplication",
    "ManageAuthProviders",
    "SingleSignOn",
    "ApiEnabled",
}

# Elements a Profile is allowed to keep once permissions live in permission sets.
# Sourced from the Metadata API Developer Guide Profile field table: these are the
# entries with no counterpart in the PermissionSet field table.
PROFILE_RESIDUE_ELEMENTS = {
    "categoryGroupVisibilities",
    "custom",
    "description",
    "fullName",
    "layoutAssignments",
    "loginFlows",
    "loginHours",
    "loginIpRanges",
    "profileActionOverrides",
    "userLicense",
}

# Elements that exist only on Profile and therefore cannot appear in a permission set.
PROFILE_ONLY_ELEMENTS = {
    "categoryGroupVisibilities",
    "custom",
    "layoutAssignments",
    "loginFlows",
    "loginHours",
    "loginIpRanges",
    "profileActionOverrides",
    "tabVisibilities",
}

# System permissions that stay on a profile without being flagged as migratable.
# Everything else belongs in a permission set under a permission-set-led model.
PROFILE_ALLOWED_USER_PERMISSIONS: set[str] = set()

METADATA_SUFFIXES = (
    ".profile-meta.xml",
    ".permissionset-meta.xml",
    ".permissionsetgroup-meta.xml",
    ".profile",
    ".permissionset",
    ".permissionsetgroup",
)
# PSVP-DESC-01 / PSVP-DESC-02 thresholds. 255 is the Metadata API's documented
# ceiling for PermissionSet.description and Profile.description; 200 is
# headroom to catch a description before it grows past the limit.
DESC_MAX_LEN = 255
DESC_WARN_LEN = 200

SEVERITY_WEIGHTS = {
    "CRITICAL": 20,
    "ERROR": 15,
    "HIGH": 10,
    "MEDIUM": 5,
    "WARN": 3,
    "LOW": 1,
    "REVIEW": 0,
    "INFO": 0,
}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def find_child(element: ET.Element, child_name: str) -> ET.Element | None:
    """Return the first child with this local name, or None.

    A leaf Element is falsy, so `element.find(a) or element.find(b)` silently
    discards a real match. Always compare against None.
    """
    for child in element:
        if local_name(child.tag) == child_name:
            return child
    return None


def child_text(element: ET.Element, child_name: str) -> str:
    child = find_child(element, child_name)
    if child is None:
        return ""
    return (child.text or "").strip()


def is_true(element: ET.Element, child_name: str) -> bool:
    return child_text(element, child_name).lower() == "true"


def api_name(path: Path) -> str:
    """Metadata API name for a profile/permission set file."""
    name = path.name
    for suffix in METADATA_SUFFIXES:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def iter_metadata_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.name.endswith(METADATA_SUFFIXES):
                    files.append(candidate)
        elif path.is_file() and path.name.endswith(METADATA_SUFFIXES):
            files.append(path)
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


BLOCKING_SEVERITIES = {"CRITICAL", "ERROR", "HIGH"}


def emit_result(findings: list[str], summary: str, strict: bool = False) -> int:
    """Print the JSON report and return the exit code.

    Exit 1 only on CRITICAL/ERROR/HIGH findings (platform facts that will fail
    or misbehave at deploy or run time -- dangerous grants, migratable
    permissions still on a profile, profile-only elements in a permission set,
    and PSVP-DESC-01). WARN/INFO findings (a standard-profile edit, a
    duplicate grant, PSVP-DESC-02, an empty scan) are advisory and exit 0 so a
    build with only cosmetic findings stays green; pass --strict to promote
    every finding to a failure.
    """
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    blocking = [item for item in normalized if item["severity"] in BLOCKING_SEVERITIES]
    print(json.dumps(
        {"score": score, "findings": normalized, "summary": summary, "blocking": len(blocking)},
        indent=2,
    ))
    if normalized:
        print(
            f"WARN: {len(normalized)} finding(s) detected ({len(blocking)} blocking)",
            file=sys.stderr,
        )
    if blocking:
        return 1
    return 1 if (strict and normalized) else 0


# --------------------------------------------------------------------------- checks


def check_description_length(path: Path, root: ET.Element, root_type: str) -> list[str]:
    """PSVP-DESC-01 (ERROR, >255 chars) / PSVP-DESC-02 (WARN, >200 chars).

    Grounded for PermissionSet and Profile: Metadata API Developer Guide,
    "The permission set description. Limit: 255 characters." (api_meta
    L94788) and "The profile description. Limit: 255 characters." (api_meta
    L97678). PermissionSetGroup.description has no documented limit (api_meta
    L95328) -- UNVERIFIED (2026-09-11) as a direct rejection, applied here for
    symmetry because a PSG deploy fails as a cascade once a member
    PermissionSet it references is rejected on this exact error (verified by
    `sf project deploy start --dry-run` against a Summer '26 developer org on
    2026-09-11, examples/builds/case-onboarding/reports/MOCK-DEPLOY-M2.md,
    once exported).
    """
    findings: list[str] = []
    description = child_text(root, "description")
    if not description:
        return findings
    length = len(description)
    if length > DESC_MAX_LEN:
        findings.append(
            f"ERROR {path}: PSVP-DESC-01 {root_type} description is {length} characters, "
            f"over the {DESC_MAX_LEN}-character limit; move rationale to deploy-order.md "
            "or the configuration workbook."
        )
    elif length > DESC_WARN_LEN:
        findings.append(
            f"WARN {path}: PSVP-DESC-02 {root_type} description is {length} characters, "
            f"approaching the {DESC_MAX_LEN}-character limit."
        )
    return findings


def check_dangerous_grants(path: Path, root: ET.Element, root_type: str) -> list[str]:
    """Check 1 -- system permissions and object-level sharing bypass."""
    findings: list[str] = []

    for block in root.iter():
        tag = local_name(block.tag)

        if tag == "userPermissions":
            name = child_text(block, "name")
            if is_true(block, "enabled") and name in DANGEROUS_PERMISSIONS:
                findings.append(
                    f"HIGH {path}: {root_type} grants dangerous system permission `{name}`"
                )

        if tag == "objectPermissions":
            object_name = child_text(block, "object") or "<unknown object>"
            if is_true(block, "viewAllRecords"):
                findings.append(f"HIGH {path}: {object_name} has `viewAllRecords=true`")
            if is_true(block, "modifyAllRecords"):
                findings.append(f"HIGH {path}: {object_name} has `modifyAllRecords=true`")

    return findings


def check_profile_carries_migratable_grants(path: Path, root: ET.Element) -> list[str]:
    """Check 2 -- migratable permissions still sitting on a profile.

    HIGH, not WARN: this is a permission-set-led model's core residual-access
    bug -- a grant the design meant to move already has a permission-set
    equivalent and stayed reachable through the profile anyway.
    """
    findings: list[str] = []

    objects: list[str] = []
    fields: list[str] = []
    permissions: list[str] = []

    for block in root:
        tag = local_name(block.tag)
        if tag in PROFILE_RESIDUE_ELEMENTS:
            continue
        if tag == "objectPermissions":
            objects.append(child_text(block, "object") or "<unknown object>")
        elif tag == "fieldPermissions":
            fields.append(child_text(block, "field") or "<unknown field>")
        elif tag == "userPermissions":
            name = child_text(block, "name")
            if is_true(block, "enabled") and name not in PROFILE_ALLOWED_USER_PERMISSIONS:
                permissions.append(name or "<unnamed permission>")

    if objects:
        findings.append(
            f"HIGH {path}: profile grants object permissions on "
            f"{len(objects)} object(s) ({', '.join(sorted(set(objects))[:5])}"
            f"{', ...' if len(set(objects)) > 5 else ''}) — object CRUD has a "
            "permission-set equivalent and belongs there"
        )
    if fields:
        findings.append(
            f"HIGH {path}: profile grants field permissions on {len(fields)} field(s) "
            "— field-level security has a permission-set equivalent and belongs there"
        )
    if permissions:
        findings.append(
            f"HIGH {path}: profile enables {len(permissions)} system permission(s) "
            f"({', '.join(sorted(set(permissions))[:5])}"
            f"{', ...' if len(set(permissions)) > 5 else ''}) — `userPermissions` "
            "has a permission-set equivalent and belongs there"
        )

    return findings


def check_permission_set_holds_profile_only(path: Path, root: ET.Element) -> list[str]:
    """Check 3 -- a permission set carrying something only a profile can hold."""
    findings: list[str] = []

    for block in root:
        tag = local_name(block.tag)

        if tag in PROFILE_ONLY_ELEMENTS:
            findings.append(
                f"ERROR {path}: permission set contains `{tag}`, which exists only on "
                "the Profile metadata type — move it to the base profile"
            )
            continue

        # `default` is a Profile-only child of applicationVisibilities and
        # recordTypeVisibilities; the PermissionSet variants carry `visible` only.
        if tag in ("applicationVisibilities", "recordTypeVisibilities"):
            for child_name in ("default", "personAccountDefault"):
                if find_child(block, child_name) is not None:
                    subject = (
                        child_text(block, "application")
                        or child_text(block, "recordType")
                        or "<unnamed>"
                    )
                    findings.append(
                        f"ERROR {path}: `{tag}` for `{subject}` carries `{child_name}`, "
                        "which exists only on the Profile variant — the default stays "
                        "on the base profile"
                    )

    return findings


def check_standard_profile_edited(path: Path, root: ET.Element) -> list[str]:
    """Check 4 -- object-permission edits on a standard (`custom=false`) profile."""
    findings: list[str] = []

    custom = find_child(root, "custom")
    if custom is None or (custom.text or "").strip().lower() != "false":
        return findings

    edited = [
        local_name(block.tag)
        for block in root
        if local_name(block.tag) in ("objectPermissions", "fieldPermissions")
    ]
    if edited:
        findings.append(
            f"WARN {path}: standard profile (`custom` = false) carries "
            f"{len(edited)} object/field permission block(s); editing standard objects "
            "on standard profiles is disabled in API version 50.0 and later — clone to "
            "a custom profile before deploying this change"
        )

    return findings


def check_duplicate_object_grants(files: list[Path]) -> list[str]:
    """Check 5 -- an object granted by both a profile and a PSG member."""
    findings: list[str] = []

    profile_objects: dict[str, set[str]] = {}
    permset_objects: dict[str, set[str]] = {}
    group_members: dict[str, list[str]] = {}

    for path in files:
        root = parse_file(path)
        if root is None:
            continue
        root_type = local_name(root.tag)
        name = api_name(path)

        if root_type == "PermissionSetGroup":
            members = [
                (block.text or "").strip()
                for block in root
                if local_name(block.tag) == "permissionSets" and (block.text or "").strip()
            ]
            if members:
                group_members[name] = members
            continue

        granted = {
            child_text(block, "object")
            for block in root
            if local_name(block.tag) == "objectPermissions" and child_text(block, "object")
        }
        if not granted:
            continue
        if root_type == "Profile":
            profile_objects[name] = granted
        elif root_type == "PermissionSet":
            permset_objects[name] = granted

    if not profile_objects or not group_members:
        return findings

    for group, members in sorted(group_members.items()):
        reachable: set[str] = set()
        for member in members:
            reachable |= permset_objects.get(member, set())
        if not reachable:
            continue
        for profile, granted in sorted(profile_objects.items()):
            overlap = sorted(granted & reachable)
            if overlap:
                findings.append(
                    f"INFO {profile}: object(s) {', '.join(overlap)} granted by both this "
                    f"profile and permission set group `{group}` — the duplicate grant "
                    "means removing it from one side revokes nothing"
                )

    return findings


# ----------------------------------------------------------------------------- run


def parse_file(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def audit_file(path: Path) -> list[str]:
    root = parse_file(path)
    if root is None:
        return [f"ERROR {path}: file is not well-formed XML and could not be parsed"]

    root_type = local_name(root.tag)
    findings = check_description_length(path, root, root_type)

    if root_type == "PermissionSetGroup":
        return findings

    findings.extend(check_dangerous_grants(path, root, root_type))

    if root_type == "Profile":
        findings.extend(check_profile_carries_migratable_grants(path, root))
        findings.extend(check_standard_profile_edited(path, root))
    elif root_type == "PermissionSet":
        findings.extend(check_permission_set_holds_profile_only(path, root))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce profile and permission set metadata for dangerous "
            "system permissions, sharing bypass grants, migratable permissions "
            "left on a profile, and profile-only elements placed in a permission set."
        )
    )
    parser.add_argument("paths", nargs="*", help="Files or directories to scan")
    parser.add_argument(
        "--manifest-dir",
        help="Root directory of the Salesforce metadata (e.g. force-app/main/default).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any finding, including WARN/INFO advisories.",
    )
    args = parser.parse_args()

    if args.manifest_dir and not Path(args.manifest_dir).exists():
        print(f"ERROR: --manifest-dir does not exist: {args.manifest_dir}", file=sys.stderr)
        return 1

    targets = [Path(value) for value in args.paths]
    if args.manifest_dir:
        targets.append(Path(args.manifest_dir))
    if not targets:
        targets = [Path(".")]

    files = iter_metadata_files(targets)
    if not files:
        return emit_result(
            ["WARN no profile, permission set, or permission set group metadata files found"],
            "Scanned 0 access-model metadata file(s); no files matched the provided paths.",
            strict=args.strict,
        )

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))
    findings.extend(check_duplicate_object_grants(files))

    summary = (
        f"Scanned {len(files)} access-model metadata file(s); "
        f"{len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
