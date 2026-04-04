#!/usr/bin/env python3
"""Checker script for Metadata API and Package.xml skill.

Validates a Salesforce metadata project directory for common package.xml and
destructiveChanges.xml issues described in the skill's gotchas.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_metadata_api_and_package_xml.py [--help]
    python3 check_metadata_api_and_package_xml.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

METADATA_NS = "http://soap.sforce.com/2006/04/metadata"

# Standard objects that must be named explicitly (wildcard does not cover them)
COMMON_STANDARD_OBJECTS = {
    "Account", "Contact", "Lead", "Opportunity", "Case", "Task", "Event",
    "User", "Campaign", "Product2", "Pricebook2", "Contract", "Order",
    "Asset", "Quote", "Solution", "KnowledgeArticle",
}

# Minimum supported API version
MIN_SUPPORTED_VERSION = 31.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check package.xml and destructiveChanges.xml for common Metadata API issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing package.xml and optional destructiveChanges.xml (default: current directory).",
    )
    return parser.parse_args()


def parse_package_xml(path: Path) -> tuple[list[dict], float | None]:
    """Parse a package.xml-style file.

    Returns (types_list, version) where types_list is a list of
    {'name': str, 'members': list[str]} dicts and version is a float or None.
    """
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [], None

    root = tree.getroot()
    ns = {"m": METADATA_NS}

    version_el = root.find("m:version", ns)
    version: float | None = None
    if version_el is not None and version_el.text:
        try:
            version = float(version_el.text.strip())
        except ValueError:
            pass

    types_list = []
    for type_el in root.findall("m:types", ns):
        name_el = type_el.find("m:name", ns)
        name = name_el.text.strip() if name_el is not None and name_el.text else ""
        members = [
            m.text.strip()
            for m in type_el.findall("m:member", ns)
            if m.text
        ]
        # Also check plural <members> tag used in official docs
        members += [
            m.text.strip()
            for m in type_el.findall("m:members", ns)
            if m.text
        ]
        types_list.append({"name": name, "members": members})

    return types_list, version


def check_package_xml(path: Path) -> list[str]:
    """Check a package.xml file for common issues."""
    issues: list[str] = []
    types_list, version = parse_package_xml(path)

    filename = path.name

    # Check version element
    if version is None:
        issues.append(
            f"{filename}: Missing or unparseable <version> element. "
            "Every package.xml must include an API version (e.g., <version>66.0</version>)."
        )
    elif version < MIN_SUPPORTED_VERSION:
        issues.append(
            f"{filename}: API version {version} is retired (minimum supported: {MIN_SUPPORTED_VERSION}). "
            "Update <version> to at least 31.0 — preferably to the current release version."
        )

    # Check CustomObject members — wildcard does not cover standard objects
    for type_entry in types_list:
        if type_entry["name"] == "CustomObject":
            members = type_entry["members"]
            has_wildcard = "*" in members
            if has_wildcard:
                # Check if any standard objects are absent
                named_members = {m for m in members if m != "*"}
                missing_standard = COMMON_STANDARD_OBJECTS - named_members
                if missing_standard:
                    issues.append(
                        f"{filename}: CustomObject uses wildcard (*) but standard objects are not "
                        f"covered by it. If you need these standard objects, add them explicitly: "
                        f"{', '.join(sorted(missing_standard)[:5])}... "
                        "(Wildcard only retrieves custom objects, not standard objects.)"
                    )

    # Check destructiveChanges files for wildcards (not supported)
    if "destructive" in filename.lower():
        for type_entry in types_list:
            if "*" in type_entry["members"]:
                issues.append(
                    f"{filename}: Wildcards (*) are not supported in destructiveChanges manifests. "
                    f"Type '{type_entry['name']}' uses a wildcard member. "
                    "List each component to delete by its exact full name."
                )

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Check all manifest files in the given directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Directory not found: {manifest_dir}")
        return issues

    manifest_files = list(manifest_dir.glob("package.xml")) + \
                     list(manifest_dir.glob("destructiveChanges*.xml"))

    if not manifest_files:
        issues.append(
            f"No package.xml or destructiveChanges*.xml found in {manifest_dir}. "
            "Make sure you are pointing to the correct metadata root directory."
        )
        return issues

    for mf in manifest_files:
        issues.extend(check_package_xml(mf))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_manifest_dir(manifest_dir)

    if not issues:
        print("No issues found in manifest files.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
