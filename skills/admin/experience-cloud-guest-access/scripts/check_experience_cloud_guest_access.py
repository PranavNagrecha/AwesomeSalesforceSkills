#!/usr/bin/env python3
"""Checker script for Experience Cloud Guest Access skill.

Inspects Salesforce metadata in a SFDX/DX project layout and reports
issues related to guest user access configuration.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_guest_access.py --help
    python3 check_experience_cloud_guest_access.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Permissions that must never appear on a guest user profile
_DANGEROUS_OBJECT_PERMISSIONS = {
    "allowEdit",
    "allowDelete",
    "viewAllRecords",
    "modifyAllRecords",
}

# System permissions that are unsafe on a guest user profile
_DANGEROUS_SYSTEM_PERMISSIONS = {
    "ApiEnabled",
    "ApiUserOnly",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud guest access configuration in Salesforce "
            "metadata for common issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def _iter_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all files with the given suffix under root."""
    return sorted(root.rglob(f"*{suffix}"))


def check_guest_profile_permissions(manifest_dir: Path) -> list[str]:
    """Check Profile metadata files for dangerous guest user permissions.

    Looks for any Profile XML whose name contains 'Guest User' or 'SiteGuest'
    and flags dangerous object or system permissions.
    """
    issues: list[str] = []
    profile_files = _iter_xml_files(manifest_dir, ".profile-meta.xml")
    if not profile_files:
        profile_files = _iter_xml_files(manifest_dir, ".profile")

    for profile_path in profile_files:
        name = profile_path.stem.lower()
        # Heuristic: guest profiles contain 'guest' or 'siteguest' in the filename
        if "guest" not in name and "siteguest" not in name:
            continue

        try:
            tree = ET.parse(profile_path)
        except ET.ParseError as exc:
            issues.append(f"[{profile_path.name}] XML parse error: {exc}")
            continue

        root_elem = tree.getroot()
        # Strip namespace for easier querying
        ns = ""
        if root_elem.tag.startswith("{"):
            ns = root_elem.tag.split("}")[0] + "}"

        # Check object permissions
        for obj_perm in root_elem.findall(f"{ns}objectPermissions"):
            obj_name_elem = obj_perm.find(f"{ns}object")
            obj_name = obj_name_elem.text if obj_name_elem is not None else "unknown"
            for perm_name in _DANGEROUS_OBJECT_PERMISSIONS:
                perm_elem = obj_perm.find(f"{ns}{perm_name}")
                if perm_elem is not None and perm_elem.text and perm_elem.text.strip().lower() == "true":
                    issues.append(
                        f"[{profile_path.name}] Dangerous object permission '{perm_name}' "
                        f"is enabled for object '{obj_name}' on guest user profile."
                    )

        # Check system permissions
        for sys_perm in root_elem.findall(f"{ns}userPermissions"):
            perm_name_elem = sys_perm.find(f"{ns}name")
            enabled_elem = sys_perm.find(f"{ns}enabled")
            if perm_name_elem is None or enabled_elem is None:
                continue
            perm_name = perm_name_elem.text or ""
            enabled = enabled_elem.text and enabled_elem.text.strip().lower() == "true"
            if perm_name in _DANGEROUS_SYSTEM_PERMISSIONS and enabled:
                issues.append(
                    f"[{profile_path.name}] Dangerous system permission '{perm_name}' "
                    f"is enabled on guest user profile."
                )

    return issues


def check_experience_site_settings(manifest_dir: Path) -> list[str]:
    """Check ExperienceBundle or Network metadata for unsafe guest API settings."""
    issues: list[str] = []

    # ExperienceBundle site configuration files (DX layout)
    experience_configs = list(manifest_dir.rglob("*.json"))
    for cfg_path in experience_configs:
        # Only check files that look like ExperienceBundle site configuration
        if "experiences" not in str(cfg_path).lower():
            continue
        # Heuristic: look for 'allowGuestMemberAccess' or 'selfRegistration' patterns
        try:
            content = cfg_path.read_text(encoding="utf-8")
        except OSError:
            continue
        if '"allowGuestMemberAccess": true' in content or "'allowGuestMemberAccess': true" in content:
            issues.append(
                f"[{cfg_path.name}] 'allowGuestMemberAccess' is enabled. "
                "Review whether public API access for guests is intentional."
            )

    # Network metadata XML (classic deployment)
    network_files = _iter_xml_files(manifest_dir, ".network-meta.xml")
    if not network_files:
        network_files = _iter_xml_files(manifest_dir, ".network")

    for net_path in network_files:
        try:
            tree = ET.parse(net_path)
        except ET.ParseError as exc:
            issues.append(f"[{net_path.name}] XML parse error: {exc}")
            continue

        root_elem = tree.getroot()
        ns = ""
        if root_elem.tag.startswith("{"):
            ns = root_elem.tag.split("}")[0] + "}"

        allow_guest_api = root_elem.find(f"{ns}allowGuestSupportApi")
        if allow_guest_api is not None and allow_guest_api.text and allow_guest_api.text.strip().lower() == "true":
            issues.append(
                f"[{net_path.name}] 'allowGuestSupportApi' is true — "
                "public API access for guest users is enabled. Disable unless explicitly required."
            )

    return issues


def check_guest_sharing_rules_present(manifest_dir: Path) -> list[str]:
    """Warn when sharing rule metadata exists but no guest user sharing rules are found.

    This is a heuristic advisory check only — not a hard failure.
    """
    issues: list[str] = []
    sharing_files = _iter_xml_files(manifest_dir, ".sharingRules-meta.xml")
    if not sharing_files:
        sharing_files = _iter_xml_files(manifest_dir, ".sharingRules")

    for sharing_path in sharing_files:
        try:
            content = sharing_path.read_text(encoding="utf-8")
        except OSError:
            continue
        # Guest user sharing rules include 'SiteGuest' or 'GuestUser' in the shared to name
        if "guestUser" not in content.lower() and "siteguest" not in content.lower():
            continue
        # If we find a guest user sharing rule reference, it is a positive signal — skip
        break
    else:
        # No sharing rule file contained a guest user reference
        if sharing_files:
            issues.append(
                "No Guest User Sharing Rules found in sharing rule metadata. "
                "If this project includes an Experience Cloud site with public pages, "
                "verify that external OWD is set to Public Read Only for all publicly "
                "displayed objects, or add Guest User Sharing Rules to expose specific records."
            )

    return issues


def check_experience_cloud_guest_access(manifest_dir: Path) -> list[str]:
    """Aggregate all guest access checks and return a list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_guest_profile_permissions(manifest_dir))
    issues.extend(check_experience_site_settings(manifest_dir))
    issues.extend(check_guest_sharing_rules_present(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_guest_access(manifest_dir)

    if not issues:
        print("No guest access issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
