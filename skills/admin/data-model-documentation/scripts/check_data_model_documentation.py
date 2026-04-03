#!/usr/bin/env python3
"""Checker script for Data Model Documentation skill.

Scans retrieved Salesforce metadata (SFDX source format) to identify
documentation debt: custom fields with blank or missing Description values.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_model_documentation.py [--manifest-dir path/to/metadata]

The script expects SFDX source format where custom fields live at:
    <manifest-dir>/force-app/main/default/objects/<ObjectName>/fields/<FieldName>.field-meta.xml

If the standard SFDX path is not found, it also accepts any directory and
recursively searches for *.field-meta.xml files.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FIELD_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan retrieved Salesforce metadata for custom fields with missing "
            "or blank Description values (documentation debt)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def get_description(field_xml: Path) -> str:
    """Parse a .field-meta.xml file and return its <description> value, or '' if absent."""
    try:
        tree = ET.parse(field_xml)
        root = tree.getroot()
        # ElementTree includes the namespace in tag names
        ns = FIELD_NAMESPACE
        desc_el = root.find(f"{{{ns}}}description")
        if desc_el is None:
            # Try without namespace (some retrieved files omit it)
            desc_el = root.find("description")
        if desc_el is not None and desc_el.text:
            return desc_el.text.strip()
        return ""
    except ET.ParseError:
        return ""


def check_field_documentation(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings for custom fields missing a Description.

    Searches recursively for *.field-meta.xml files under manifest_dir.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    field_files = list(manifest_dir.rglob("*.field-meta.xml"))

    if not field_files:
        issues.append(
            f"No *.field-meta.xml files found under {manifest_dir}. "
            "Run 'sf project retrieve start --metadata CustomObject' first."
        )
        return issues

    missing_desc: list[tuple[str, str]] = []  # (object_name, field_name)

    for field_file in sorted(field_files):
        field_name = field_file.stem.replace(".field-meta", "")
        # Skip standard fields (they are not in retrieved metadata)
        # Custom fields end with __c in their API name
        if not field_name.endswith("__c"):
            continue

        # Infer object name from directory structure
        # Expected: .../objects/<ObjectName>/fields/<FieldName>.field-meta.xml
        parts = field_file.parts
        try:
            fields_idx = list(parts).index("fields")
            object_name = parts[fields_idx - 1]
        except ValueError:
            object_name = "<unknown>"

        description = get_description(field_file)
        if not description:
            missing_desc.append((object_name, field_name))

    if missing_desc:
        issues.append(
            f"{len(missing_desc)} custom field(s) have no Description (documentation debt):"
        )
        for obj, fld in missing_desc:
            issues.append(f"  - {obj}.{fld}")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_field_documentation(manifest_dir)

    if not issues:
        print("No documentation issues found. All custom fields have descriptions.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
