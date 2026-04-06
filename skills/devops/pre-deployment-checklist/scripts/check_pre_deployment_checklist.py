#!/usr/bin/env python3
"""Checker script for Pre-Deployment Checklist skill.

Scans a Salesforce metadata project directory for common pre-deployment issues:
- Missing package.xml manifest
- Destructive changes without a corresponding constructive manifest
- Apex classes without corresponding test classes
- Empty or malformed package.xml

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_pre_deployment_checklist.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


METADATA_NS = "http://soap.sforce.com/2006/04/metadata"
NS = {"md": METADATA_NS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check pre-deployment readiness of a Salesforce metadata project.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


def find_package_xml(root: Path) -> Path | None:
    """Locate the primary package.xml in the project."""
    candidates = [
        root / "manifest" / "package.xml",
        root / "package.xml",
        root / "src" / "package.xml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def parse_package_xml(path: Path) -> dict[str, list[str]]:
    """Parse package.xml and return {type_name: [member, ...]}."""
    result: dict[str, list[str]] = {}
    try:
        tree = ET.parse(path)
        root_el = tree.getroot()
        for types_el in root_el.findall("md:types", NS):
            name_el = types_el.find("md:name", NS)
            if name_el is None or not name_el.text:
                continue
            type_name = name_el.text.strip()
            members = []
            for member_el in types_el.findall("md:members", NS):
                if member_el.text:
                    members.append(member_el.text.strip())
            result[type_name] = members
    except ET.ParseError:
        pass
    return result


def check_pre_deployment_checklist(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # 1. Check for package.xml
    pkg_xml = find_package_xml(manifest_dir)
    if pkg_xml is None:
        issues.append(
            "No package.xml found. A deployment manifest is required. "
            "Expected at manifest/package.xml, package.xml, or src/package.xml."
        )
        return issues

    # 2. Parse and validate package.xml
    components = parse_package_xml(pkg_xml)
    if not components:
        issues.append(
            f"package.xml at {pkg_xml} is empty or malformed. "
            "It must contain at least one <types> element with <name> and <members>."
        )
        return issues

    # 3. Check for wildcard members in production-bound manifests
    for type_name, members in components.items():
        if "*" in members:
            issues.append(
                f"Wildcard member '*' found in {type_name}. "
                "Wildcard deploys retrieve all components of that type, which is risky for production. "
                "List explicit member names instead."
            )

    # 4. Check for API version
    try:
        tree = ET.parse(pkg_xml)
        root_el = tree.getroot()
        version_el = root_el.find("md:version", NS)
        if version_el is None or not version_el.text:
            issues.append(
                "No <version> element in package.xml. "
                "Always specify the API version to avoid defaulting to an unexpected version."
            )
    except ET.ParseError:
        issues.append(f"Failed to parse {pkg_xml} as valid XML.")

    # 5. Check for destructive changes without constructive manifest
    destructive_files = list(manifest_dir.rglob("destructiveChanges*.xml"))
    if destructive_files and not pkg_xml:
        issues.append(
            "Destructive changes manifest found without a constructive package.xml. "
            "Destructive deploys still require a package.xml (even if empty with just a version)."
        )

    # 6. Check for Apex classes without test classes
    apex_classes: list[str] = components.get("ApexClass", [])
    if apex_classes:
        test_pattern = re.compile(r"(?i)(test|_test$|tests$|test_)", re.IGNORECASE)
        non_test_classes = [c for c in apex_classes if not test_pattern.search(c)]
        test_classes = [c for c in apex_classes if test_pattern.search(c)]

        if non_test_classes and not test_classes:
            issues.append(
                f"Package includes {len(non_test_classes)} Apex class(es) but no test classes. "
                "Production deployments require Apex tests. Include test classes in the manifest."
            )

    # 7. Check for profiles (high-risk component)
    if "Profile" in components:
        profile_members = components["Profile"]
        issues.append(
            f"Package includes {len(profile_members)} Profile(s): {', '.join(profile_members[:5])}. "
            "Profile deployments overwrite the entire profile in the target org, not just changed settings. "
            "Consider using PermissionSet instead unless full profile deployment is intentional."
        )

    # 8. Check for backup directory
    backup_dirs = [
        manifest_dir / "backups",
        manifest_dir / "backup",
        manifest_dir.parent / "backups",
    ]
    has_backup = any(d.exists() and any(d.iterdir()) for d in backup_dirs if d.exists())
    if not has_backup:
        issues.append(
            "No backup directory found. Before deploying to production, retrieve the current state "
            "of all components being deployed: "
            "sf project retrieve start --manifest package.xml --target-org production --output-dir backups/YYYY-MM-DD/"
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_pre_deployment_checklist(manifest_dir)

    if not issues:
        print("Pre-deployment check passed. No issues found.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
