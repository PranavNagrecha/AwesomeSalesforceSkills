#!/usr/bin/env python3
"""Checker script for User Access Policies skill.

Checks Salesforce metadata in a local project directory for common
User Access Policy (UAP) configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_user_access_policies.py [--help]
    python3 check_user_access_policies.py --manifest-dir path/to/metadata
    python3 check_user_access_policies.py --manifest-dir force-app/main/default

Checks performed:
    1. Detects UserAccessPolicy metadata files present in the project.
    2. Warns if both Grant and Revoke policies exist — prompts the
       practitioner to verify evaluation order.
    3. Detects Apex trigger files on the User object that may conflict
       with UAP policies.
    4. Checks for PermissionSetAssignment DML inside User triggers
       (potential UAP conflict).
    5. Warns if no UserAccessPolicy metadata is found but User triggers
       with permission set logic are present (potential missed migration).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files under root matching the given glob pattern."""
    return sorted(root.rglob(pattern))


def _read_text(path: Path) -> str:
    """Read file text safely, returning empty string on decode errors."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_xml_root(path: Path) -> ElementTree.Element | None:
    """Parse an XML file and return the root element, or None on error."""
    try:
        return ElementTree.parse(path).getroot()
    except ElementTree.ParseError:
        return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_uap_files_present(manifest_dir: Path) -> tuple[list[Path], list[str]]:
    """Return (uap_files, issues). Issues are warnings, not hard failures."""
    uap_files = _find_files(manifest_dir, "*.userAccessPolicy")
    # Also look for the folder-based layout used by sf CLI
    uap_files += _find_files(manifest_dir, "userAccessPolicies/*.xml")
    # Deduplicate
    seen: set[Path] = set()
    unique: list[Path] = []
    for f in uap_files:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    issues: list[str] = []
    if not unique:
        issues.append(
            "No UserAccessPolicy metadata files found in the project. "
            "If UAP policies are expected, ensure they are retrieved from the org "
            "and included in the deployment package."
        )
    return unique, issues


def check_grant_revoke_overlap(uap_files: list[Path]) -> list[str]:
    """Warn if both Grant and Revoke policy files are present — prompts review."""
    issues: list[str] = []
    grant_policies: list[str] = []
    revoke_policies: list[str] = []

    for f in uap_files:
        root = _parse_xml_root(f)
        if root is None:
            continue
        # Strip namespace for comparison
        ns_pattern = re.compile(r"\{.*?\}")
        for elem in root.iter():
            tag = ns_pattern.sub("", elem.tag)
            if tag == "accessPolicyType":
                policy_type = (elem.text or "").strip()
                if policy_type == "Grant":
                    grant_policies.append(f.name)
                elif policy_type == "Revoke":
                    revoke_policies.append(f.name)

    if grant_policies and revoke_policies:
        issues.append(
            f"Both Grant and Revoke policies detected. "
            f"Grant policies: {grant_policies}. "
            f"Revoke policies: {revoke_policies}. "
            "Verify that no Grant and Revoke policy pair targets the same permission "
            "set for the same user segment — the Revoke always wins in the same "
            "evaluation pass."
        )
    return issues


def check_user_triggers_for_psa_dml(manifest_dir: Path) -> list[str]:
    """Detect Apex triggers on the User object that contain PermissionSetAssignment DML."""
    issues: list[str] = []

    trigger_files = _find_files(manifest_dir, "*.trigger")
    user_trigger_files: list[Path] = []

    for tf in trigger_files:
        text = _read_text(tf)
        # A trigger on the User object will have: trigger <Name> on User (
        if re.search(r"trigger\s+\w+\s+on\s+User\s*\(", text, re.IGNORECASE):
            user_trigger_files.append(tf)

    for tf in user_trigger_files:
        text = _read_text(tf)
        if "PermissionSetAssignment" in text:
            issues.append(
                f"Apex trigger '{tf.name}' operates on the User object and contains "
                "PermissionSetAssignment DML. This may conflict with active User Access "
                "Policies managing the same permission sets. Deactivate or remove this "
                "trigger before activating UAP policies that cover the same assignments."
            )

    return issues


def check_trigger_metadata_for_active_status(manifest_dir: Path) -> list[str]:
    """Warn if User trigger metadata files have status Active (potential conflict)."""
    issues: list[str] = []

    meta_files = _find_files(manifest_dir, "*.trigger-meta.xml")
    for mf in meta_files:
        # Match trigger name: if the corresponding .trigger file is a User trigger
        trigger_name = mf.name.replace(".trigger-meta.xml", "")
        trigger_file = mf.parent / f"{trigger_name}.trigger"
        if not trigger_file.exists():
            continue
        text = _read_text(trigger_file)
        if not re.search(r"trigger\s+\w+\s+on\s+User\s*\(", text, re.IGNORECASE):
            continue
        if "PermissionSetAssignment" not in text:
            continue
        # Check metadata status
        root = _parse_xml_root(mf)
        if root is None:
            continue
        ns_pattern = re.compile(r"\{.*?\}")
        for elem in root.iter():
            tag = ns_pattern.sub("", elem.tag)
            if tag == "status" and (elem.text or "").strip() == "Active":
                issues.append(
                    f"Trigger '{trigger_name}' is Active in metadata and contains "
                    "PermissionSetAssignment logic on the User object. If UAP policies "
                    "are also active for the same user segment, deactivate this trigger "
                    "to prevent conflicts."
                )
    return issues


def check_custom_field_filters_note(uap_files: list[Path]) -> list[str]:
    """Warn if UAP files reference custom fields in filters (require release 246+)."""
    issues: list[str] = []
    custom_field_pattern = re.compile(r"__c\b")
    for f in uap_files:
        text = _read_text(f)
        if custom_field_pattern.search(text):
            issues.append(
                f"Policy file '{f.name}' appears to reference a custom user field "
                "(contains '__c'). Custom user fields as UAP filter criteria require "
                "release 246 (Spring '26) or later. Confirm the target org is on "
                "the correct release before deploying."
            )
    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def check_user_access_policies(manifest_dir: Path) -> list[str]:
    """Run all UAP checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    uap_files, uap_presence_issues = check_uap_files_present(manifest_dir)
    issues.extend(uap_presence_issues)

    if uap_files:
        issues.extend(check_grant_revoke_overlap(uap_files))
        issues.extend(check_custom_field_filters_note(uap_files))

    issues.extend(check_user_triggers_for_psa_dml(manifest_dir))
    issues.extend(check_trigger_metadata_for_active_status(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for User Access Policy configuration issues. "
            "Detects missing UAP metadata, grant/revoke evaluation order conflicts, "
            "and Apex triggers that may conflict with UAP policies."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_user_access_policies(manifest_dir)

    if not issues:
        print("No User Access Policy issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
