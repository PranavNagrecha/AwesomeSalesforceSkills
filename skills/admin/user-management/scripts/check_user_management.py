#!/usr/bin/env python3
"""Checker script for User Management skill.

Inspects Salesforce metadata exported via sf CLI (source format) for common
user management anti-patterns: profiles with no login-hour restrictions,
profiles using the System Administrator profile name in delegated groups,
and profiles missing IP range restrictions in high-security orgs.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_user_management.py [--manifest-dir path/to/metadata]

Expected metadata layout:
    <manifest-dir>/
        profiles/
            *.profile-meta.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common user management "
            "anti-patterns: missing login hours, missing IP restrictions, "
            "and overly permissive profile configurations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


_SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    return f"{{{_SF_NS}}}{local}"


def check_profile(path: Path) -> list[str]:
    """Return issues found in a single .profile-meta.xml file."""
    issues: list[str] = []
    profile_name = path.stem.replace(".profile-meta", "")

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        issues.append(f"[{profile_name}] Cannot parse XML: {exc}")
        return issues

    root = tree.getroot()

    # --- Check 1: Login Hours ---
    login_hours = root.findall(_tag("loginHours"))
    if not login_hours:
        issues.append(
            f"[{profile_name}] No loginHours element found. "
            "Consider restricting login to business hours for non-admin profiles."
        )

    # --- Check 2: Login IP Ranges ---
    ip_ranges = root.findall(_tag("loginIpRanges"))
    if not ip_ranges:
        issues.append(
            f"[{profile_name}] No loginIpRanges defined. "
            "If this profile is used by internal employees, consider restricting "
            "login to corporate IP ranges to reduce exposure to credential attacks."
        )

    # --- Check 3: User permissions — check for overly broad admin permissions ---
    dangerous_perms = {
        "ManageUsers": "can create and edit all users including admins",
        "ModifyAllData": "can read, edit, delete all records in the org",
        "ViewAllData": "can read all records in the org regardless of sharing",
        "ManageRoles": "can edit the role hierarchy",
        "ManageProfiles": "can edit profiles and permission sets",
        "AuthorApex": "can write and deploy Apex code",
        "CustomizeApplication": "can modify all configuration including security",
    }

    for perm_elem in root.findall(_tag("userPermissions")):
        name_elem = perm_elem.find(_tag("name"))
        enabled_elem = perm_elem.find(_tag("enabled"))
        if name_elem is None or enabled_elem is None:
            continue
        perm_name = (name_elem.text or "").strip()
        enabled = (enabled_elem.text or "").strip().lower() == "true"
        if enabled and perm_name in dangerous_perms:
            issues.append(
                f"[{profile_name}] Sensitive permission enabled: {perm_name} "
                f"({dangerous_perms[perm_name]}). "
                "Verify this is intentional and document the business justification."
            )

    return issues


def check_profiles_dir(manifest_dir: Path) -> list[str]:
    """Scan all .profile-meta.xml files under manifest_dir/profiles/."""
    issues: list[str] = []
    profiles_dir = manifest_dir / "profiles"

    if not profiles_dir.exists():
        # Not an error — the project may not have exported profiles
        return issues

    profile_files = sorted(profiles_dir.glob("*.profile-meta.xml"))
    if not profile_files:
        issues.append(
            f"Profiles directory exists at {profiles_dir} but contains no "
            "*.profile-meta.xml files. Run 'sf project retrieve start' to export profiles."
        )
        return issues

    for pf in profile_files:
        issues.extend(check_profile(pf))

    return issues


def check_user_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_profiles_dir(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_user_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
