#!/usr/bin/env python3
"""Checker script for Permission Set Architecture skill."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Permission Set Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def count_children(root: ET.Element, child_name: str) -> int:
    return sum(1 for elem in root.iter() if local_name(elem.tag) == child_name)


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def check_permission_set_architecture(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    profiles = sorted(manifest_dir.rglob("*.profile-meta.xml"))
    permission_sets = sorted(manifest_dir.rglob("*.permissionset-meta.xml"))
    permission_set_groups = sorted(manifest_dir.rglob("*.permissionsetgroup-meta.xml"))

    custom_profiles = [path for path in profiles if "-" not in path.stem]
    if len(custom_profiles) > 8:
        issues.append(
            f"Found {len(custom_profiles)} custom profiles; review whether feature access should move into permission sets and PSGs."
        )

    if len(permission_sets) >= 12 and not permission_set_groups:
        issues.append(
            f"Found {len(permission_sets)} permission sets but no permission set groups; recurring access bundles may be managed as manual assignments."
        )

    for profile_path in custom_profiles:
        root = parse_xml(profile_path)
        if root is None:
            issues.append(f"{profile_path}: unable to parse profile metadata.")
            continue

        object_permissions = count_children(root, "objectPermissions")
        field_permissions = count_children(root, "fieldPermissions")
        class_accesses = count_children(root, "classAccesses")

        if object_permissions > 18 or field_permissions > 120 or class_accesses > 20:
            issues.append(
                f"{profile_path}: profile is feature-heavy ({object_permissions} object perms, {field_permissions} field perms, {class_accesses} Apex class grants); review for profile sprawl."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_permission_set_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
