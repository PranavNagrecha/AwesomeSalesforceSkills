#!/usr/bin/env python3
"""Checker script for Integration User Management skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_integration_user_management.py [--help]
    python3 check_integration_user_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check profile metadata for integration user anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_profiles(manifest_dir: Path) -> list[str]:
    """Check profile metadata for admin-profile flags that should not be on integration profiles."""
    issues: list[str] = []

    profiles_dir = manifest_dir / "profiles"
    if not profiles_dir.exists():
        return issues

    # Integration-named profiles that should enforce API-only
    integration_keywords = {"integration", "api", "middleware", "etl", "mulesoft", "boomi"}

    for profile_file in profiles_dir.glob("*.profile"):
        profile_name = profile_file.stem.lower()

        # Only check profiles that appear to be integration profiles
        if not any(kw in profile_name for kw in integration_keywords):
            continue

        try:
            tree = ET.parse(profile_file)
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            # Check for user permissions that indicate admin-level access
            admin_perms = {"ModifyAllData", "ViewAllData", "ManageUsers", "ModifyMetadata"}

            for user_perm in root.findall(f"{ns}userPermissions"):
                perm_name_elem = user_perm.find(f"{ns}name")
                enabled_elem = user_perm.find(f"{ns}enabled")

                if (perm_name_elem is not None and
                        enabled_elem is not None and
                        enabled_elem.text == "true" and
                        perm_name_elem.text in admin_perms):
                    issues.append(
                        f"Profile '{profile_file.stem}' (appears to be an integration profile): "
                        f"Has '{perm_name_elem.text}' permission enabled. "
                        "Integration profiles should use Minimum Access - API Only Integrations "
                        "as the base and grant only specific object-level permissions."
                    )

        except (ET.ParseError, OSError):
            pass

    return issues


def check_integration_user_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_profiles(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_integration_user_management(manifest_dir)

    if not issues:
        print("No integration user management issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
