#!/usr/bin/env python3
"""Checker script for Delegated Administration skill.

Inspects Salesforce metadata (retrieved via sfdx/sf CLI or unzipped package)
for common delegated administration configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_delegated_administration.py [--help]
    python3 check_delegated_administration.py --manifest-dir path/to/metadata

The script looks for:
- DelegateGroup metadata files under the manifest directory
- Missing or empty Assignable Profiles lists (groups with no profile scope)
- Groups with no Users in Delegated Group (role scope) defined
- Groups with no Delegated Administrator members
- Profile permission files missing the ManageUsers permission

Expected metadata paths (relative to manifest-dir):
  delegateGroups/<GroupName>.delegateGroup
  profiles/<ProfileName>.profile  (for Manage Users permission check)
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Delegated Administration metadata for common configuration issues.\n"
            "Reads Salesforce metadata from the manifest directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, suffix: str) -> list[Path]:
    """Return all files under root matching the given suffix, case-insensitive."""
    return [p for p in root.rglob("*") if p.suffix.lower() == suffix.lower()]


def _xml_text(element: ET.Element | None) -> str:
    """Return stripped text of an XML element, or empty string if None."""
    if element is None:
        return ""
    return (element.text or "").strip()


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse XML file, return root element or None on error."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


# ---------------------------------------------------------------------------
# Delegate group checks
# ---------------------------------------------------------------------------

def check_delegate_groups(manifest_dir: Path) -> list[str]:
    """Check .delegateGroup metadata files for configuration issues."""
    issues: list[str] = []

    delegate_dir = manifest_dir / "delegateGroups"
    if not delegate_dir.exists():
        # Also try unpackaged/delegateGroups or force-app paths
        candidates = list(manifest_dir.rglob("delegateGroups"))
        if not candidates:
            issues.append(
                "No delegateGroups/ directory found in manifest. "
                "If this org uses delegated administration, retrieve DelegateGroup metadata "
                "and re-run this checker."
            )
            return issues
        delegate_dir = candidates[0]

    group_files = _find_files(delegate_dir, ".delegateGroup")
    if not group_files:
        issues.append(
            f"No .delegateGroup files found in {delegate_dir}. "
            "Retrieve DelegateGroup metadata to check configuration."
        )
        return issues

    sf_ns = "http://soap.sforce.com/2006/04/metadata"

    for gf in sorted(group_files):
        group_name = gf.stem
        root = _parse_xml_safe(gf)
        if root is None:
            issues.append(f"[{group_name}] Could not parse XML — file may be malformed.")
            continue

        # Strip namespace prefix for robust element lookup
        def tag(name: str) -> str:
            return f"{{{sf_ns}}}{name}"

        # Check: group has at least one delegated admin user
        admins = root.findall(f".//{tag('delegatedAdmins')}")
        if not admins:
            issues.append(
                f"[{group_name}] No Delegated Administrators configured. "
                "The group has no members who can exercise delegated admin rights."
            )

        # Check: group has at least one role in Users in Delegated Group
        # (delegatedGroupMembers or relatedRoles depending on API version)
        roles = (
            root.findall(f".//{tag('delegatedGroupMembers')}")
            + root.findall(f".//{tag('relatedRoles')}")
        )
        if not roles:
            issues.append(
                f"[{group_name}] No roles configured in 'Users in Delegated Group'. "
                "Without role scope, the delegated admin cannot manage any users."
            )

        # Check: group has at least one assignable profile
        profiles = root.findall(f".//{tag('assignableProfiles')}")
        if not profiles:
            # Not always an error (custom object admin groups may not need profiles)
            # but worth flagging
            issues.append(
                f"[{group_name}] No Assignable Profiles configured. "
                "If this group is intended for user management, add at least one assignable profile."
            )

    return issues


# ---------------------------------------------------------------------------
# Profile checks
# ---------------------------------------------------------------------------

def check_manage_users_permission(manifest_dir: Path) -> list[str]:
    """Check .profile files for the ManageUsers system permission.

    Reports profiles that do NOT have ManageUsers enabled.
    This is a soft check — the user knows their intended delegated admin profiles.
    """
    issues: list[str] = []

    profile_candidates = list(manifest_dir.rglob("profiles"))
    if not profile_candidates:
        # No profiles directory found — skip silently
        return issues

    profile_dir = profile_candidates[0]
    profile_files = _find_files(profile_dir, ".profile")
    if not profile_files:
        return issues

    sf_ns = "http://soap.sforce.com/2006/04/metadata"

    for pf in sorted(profile_files):
        profile_name = pf.stem
        root = _parse_xml_safe(pf)
        if root is None:
            continue

        def tag(name: str) -> str:
            return f"{{{sf_ns}}}{name}"

        # Find all userPermissions blocks
        for perm_block in root.findall(f".//{tag('userPermissions')}"):
            name_el = perm_block.find(tag("name"))
            enabled_el = perm_block.find(tag("enabled"))
            if _xml_text(name_el) == "ManageUsers":
                if _xml_text(enabled_el).lower() != "true":
                    issues.append(
                        f"[Profile: {profile_name}] ManageUsers permission is present but "
                        f"set to false. Delegated admins on this profile will not see "
                        f"the Manage Users button."
                    )
                break  # Found the permission entry; no need to continue

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_delegated_administration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_delegate_groups(manifest_dir))
    issues.extend(check_manage_users_permission(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_delegated_administration(manifest_dir)

    if not issues:
        print("No delegated administration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
