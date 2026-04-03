#!/usr/bin/env python3
"""Checker script for Custom Field Creation skill.

Scans Salesforce metadata (SFDX source format or retrieved metadata) for
common custom field anti-patterns:
  - Text fields with API names that look like enumerated categories
    (e.g., *_Type__c, *_Status__c, *_Category__c) — these often should be Picklists
  - Custom fields with no Help Text set
  - Long Text Area fields sized at minimum (256 chars) — often should be set higher

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_custom_field_creation.py [--help]
    python3 check_custom_field_creation.py --manifest-dir path/to/sfdx/force-app
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Suffixes that suggest a field holds categorical/enumerated values
# but may have been created as Text instead of Picklist
CATEGORICAL_SUFFIXES = (
    "_type",
    "_status",
    "_category",
    "_segment",
    "_tier",
    "_stage",
    "_region",
    "_reason",
    "_source",
)

# Namespace used in Salesforce field XML files
SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(name: str) -> str:
    """Return a namespace-qualified XML tag name."""
    return f"{{{SF_NS}}}{name}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common custom field anti-patterns. "
            "Point --manifest-dir at the root of your SFDX source tree or "
            "retrieved metadata directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_field_file(field_file: Path) -> list[str]:
    """Parse one .field-meta.xml file and return a list of issue strings."""
    issues: list[str] = []

    try:
        tree = ET.parse(field_file)
    except ET.ParseError as exc:
        issues.append(f"{field_file}: XML parse error — {exc}")
        return issues

    root = tree.getroot()

    # Extract field type
    type_el = root.find(_tag("type"))
    field_type = type_el.text.strip() if type_el is not None and type_el.text else ""

    # Extract full field name from the file path
    # Typical path: .../objects/Account/fields/My_Field__c.field-meta.xml
    field_api_name = field_file.stem  # e.g. My_Field__c
    object_name = field_file.parents[1].name  # e.g. Account

    full_name = f"{object_name}.{field_api_name}"

    # Check 1: Text fields with names suggesting categorical data
    if field_type == "Text":
        lower_name = field_api_name.lower().replace("__c", "")
        for suffix in CATEGORICAL_SUFFIXES:
            if lower_name.endswith(suffix):
                issues.append(
                    f"{full_name}: Field type is Text but the API name ends in "
                    f"'{suffix.lstrip('_')}' — consider whether this should be "
                    f"a Picklist to enforce a controlled vocabulary."
                )
                break

    # Check 2: Missing Help Text (not a hard error, but a quality warning)
    help_el = root.find(_tag("inlineHelpText"))
    if help_el is None or not (help_el.text or "").strip():
        issues.append(
            f"{full_name}: No Help Text (inlineHelpText) set. "
            f"Help Text improves user experience and admin maintainability."
        )

    # Check 3: Long Text Area at minimum size (256 chars)
    if field_type == "LongTextArea":
        length_el = root.find(_tag("length"))
        if length_el is not None and length_el.text:
            try:
                length = int(length_el.text.strip())
                if length <= 256:
                    issues.append(
                        f"{full_name}: Long Text Area is set to minimum size ({length} chars). "
                        f"Consider whether a larger size (e.g. 32768) is more appropriate "
                        f"for the expected content."
                    )
            except ValueError:
                pass

    return issues


def check_custom_field_creation(manifest_dir: Path) -> list[str]:
    """Scan manifest_dir for .field-meta.xml files and return all issues found."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    field_files = list(manifest_dir.rglob("*.field-meta.xml"))

    if not field_files:
        # Not an error — the directory may be a non-SFDX layout
        return issues

    for field_file in sorted(field_files):
        issues.extend(check_field_file(field_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_custom_field_creation(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
