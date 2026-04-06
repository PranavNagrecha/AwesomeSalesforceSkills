#!/usr/bin/env python3
"""Checker script for Rollback And Hotfix Strategy skill.

Validates rollback readiness by checking for pre-deploy archives,
destructive changes coverage, and non-rollbackable component detection.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_rollback_and_hotfix_strategy.py --manifest-dir path/to/metadata
    python3 check_rollback_and_hotfix_strategy.py --manifest-dir deploy/ --archive-dir rollback-archives/
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

METADATA_NS = "http://soap.sforce.com/2006/04/metadata"

# Metadata types that cannot be deleted or fully rolled back via Metadata API
NON_ROLLBACKABLE_TYPES = {
    "RecordType",
    "StandardValueSet",  # picklist values on standard fields
}

# Types where active versions complicate rollback
VERSION_SENSITIVE_TYPES = {
    "Flow",
    "FlowDefinition",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check rollback and hotfix readiness for a Salesforce deployment.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing package.xml and optional destructiveChanges*.xml.",
    )
    parser.add_argument(
        "--archive-dir",
        default="",
        help="Directory containing the pre-deploy archive. If empty, checks for archive are skipped.",
    )
    return parser.parse_args()


def parse_package_members(xml_path: Path) -> dict[str, list[str]]:
    """Parse a package.xml or destructiveChanges*.xml and return {type: [members]}."""
    members: dict[str, list[str]] = {}
    if not xml_path.exists():
        return members
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        ns = {"md": METADATA_NS}
        for types_el in root.findall("md:types", ns):
            name_el = types_el.find("md:name", ns)
            if name_el is None or name_el.text is None:
                continue
            type_name = name_el.text.strip()
            for member_el in types_el.findall("md:members", ns):
                if member_el.text:
                    members.setdefault(type_name, []).append(member_el.text.strip())
        # Also try without namespace (some manifests omit it)
        if not members:
            for types_el in root.findall("types"):
                name_el = types_el.find("name")
                if name_el is None or name_el.text is None:
                    continue
                type_name = name_el.text.strip()
                for member_el in types_el.findall("members"):
                    if member_el.text:
                        members.setdefault(type_name, []).append(member_el.text.strip())
    except ET.ParseError as e:
        members["__parse_error__"] = [str(e)]
    return members


def check_rollback_readiness(manifest_dir: Path, archive_dir: Path | None) -> list[str]:
    """Return a list of issue strings found."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for package.xml
    package_xml = manifest_dir / "package.xml"
    if not package_xml.exists():
        issues.append("No package.xml found in manifest directory. Cannot determine deployment scope.")
        return issues

    deploy_members = parse_package_members(package_xml)
    if "__parse_error__" in deploy_members:
        issues.append(f"Failed to parse package.xml: {deploy_members['__parse_error__'][0]}")
        return issues

    if not deploy_members:
        issues.append("package.xml contains no metadata types. Nothing to roll back.")
        return issues

    # Check for non-rollbackable types in the deployment
    for type_name in NON_ROLLBACKABLE_TYPES:
        if type_name in deploy_members:
            members = deploy_members[type_name]
            issues.append(
                f"Non-rollbackable type '{type_name}' found in deployment with "
                f"{len(members)} member(s): {', '.join(members[:5])}. "
                f"These cannot be deleted via Metadata API — manual Setup intervention required."
            )

    for type_name in VERSION_SENSITIVE_TYPES:
        if type_name in deploy_members:
            members = deploy_members[type_name]
            issues.append(
                f"Version-sensitive type '{type_name}' found in deployment with "
                f"{len(members)} member(s): {', '.join(members[:5])}. "
                f"Active Flow versions cannot be deactivated via deployment — "
                f"manual deactivation in Setup may be required before rollback."
            )

    # Check for wildcard usage in destructive manifests
    destructive_files = [
        manifest_dir / "destructiveChanges.xml",
        manifest_dir / "destructiveChangesPre.xml",
        manifest_dir / "destructiveChangesPost.xml",
    ]
    for dc_file in destructive_files:
        if dc_file.exists():
            dc_members = parse_package_members(dc_file)
            for type_name, members in dc_members.items():
                if type_name == "__parse_error__":
                    issues.append(f"Failed to parse {dc_file.name}: {members[0]}")
                    continue
                for member in members:
                    if member == "*":
                        issues.append(
                            f"Wildcard '*' found in {dc_file.name} for type '{type_name}'. "
                            f"Wildcards are not supported in destructive manifests — "
                            f"list every member explicitly."
                        )
                # Check for non-rollbackable types in destructive manifests
                if type_name in NON_ROLLBACKABLE_TYPES:
                    issues.append(
                        f"Non-rollbackable type '{type_name}' listed in {dc_file.name}. "
                        f"This deletion will fail — remove from manifest and handle manually."
                    )

    # Check for pre-deploy archive if path provided
    if archive_dir and archive_dir.exists():
        archive_package = archive_dir / "package.xml"
        if not archive_package.exists():
            issues.append(
                f"Pre-deploy archive directory exists ({archive_dir}) but contains no package.xml. "
                f"The archive may be incomplete."
            )
        else:
            archive_members = parse_package_members(archive_package)
            # Identify new components: in deployment but not in archive
            new_components: list[str] = []
            for type_name, members in deploy_members.items():
                archive_type_members = set(archive_members.get(type_name, []))
                for member in members:
                    if member not in archive_type_members:
                        new_components.append(f"{type_name}.{member}")

            if new_components:
                # Check if destructive changes cover these
                all_destructive_members: set[str] = set()
                for dc_file in destructive_files:
                    if dc_file.exists():
                        dc_members = parse_package_members(dc_file)
                        for type_name, members in dc_members.items():
                            for member in members:
                                all_destructive_members.add(f"{type_name}.{member}")

                uncovered = [c for c in new_components if c not in all_destructive_members]
                if uncovered:
                    issues.append(
                        f"{len(uncovered)} new component(s) in deployment are not covered by "
                        f"any destructive changes manifest. These will remain in the org after "
                        f"rollback: {', '.join(uncovered[:10])}"
                    )
    elif archive_dir:
        issues.append(
            f"Pre-deploy archive directory not found: {archive_dir}. "
            f"No archive available for rollback — reconstruct from source control."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    archive_dir = Path(args.archive_dir) if args.archive_dir else None
    issues = check_rollback_readiness(manifest_dir, archive_dir)

    if not issues:
        print("No rollback readiness issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
