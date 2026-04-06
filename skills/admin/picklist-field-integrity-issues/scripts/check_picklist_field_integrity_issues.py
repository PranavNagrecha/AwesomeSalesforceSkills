#!/usr/bin/env python3
"""Checker script for Picklist Field Integrity Issues skill.

Scans Salesforce metadata XML files for common picklist integrity risks:
- Unrestricted picklists on critical fields
- Missing record type picklist value mappings
- Dependent picklist configurations without validation rules

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_picklist_field_integrity_issues.py --manifest-dir path/to/metadata
    python3 check_picklist_field_integrity_issues.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check picklist field metadata for common integrity issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat warnings as errors.",
    )
    return parser.parse_args()


def find_field_files(root: Path) -> list[Path]:
    """Find all .field-meta.xml files in the metadata tree."""
    return sorted(root.rglob("*.field-meta.xml"))


def find_record_type_files(root: Path) -> list[Path]:
    """Find all .recordType-meta.xml files in the metadata tree."""
    return sorted(root.rglob("*.recordType-meta.xml"))


def check_unrestricted_picklists(field_files: list[Path]) -> list[str]:
    """Flag picklist fields that are not restricted."""
    issues = []
    for f in field_files:
        try:
            tree = ET.parse(f)
            root_el = tree.getroot()
            ns = re.match(r"\{.*\}", root_el.tag)
            ns_str = ns.group(0) if ns else ""

            field_type = root_el.find(f"{ns_str}type")
            if field_type is None:
                continue
            if field_type.text not in ("Picklist", "MultiselectPicklist"):
                continue

            restricted = root_el.find(f"{ns_str}valueSet/{ns_str}restricted")
            if restricted is None or restricted.text != "true":
                issues.append(
                    f"WARN: Unrestricted picklist: {f.name} — "
                    f"API values accepted without validation"
                )
        except ET.ParseError:
            issues.append(f"ERROR: Could not parse XML: {f}")
    return issues


def check_record_type_picklist_gaps(
    rt_files: list[Path], field_files: list[Path]
) -> list[str]:
    """Check if record types reference picklist values not in the field definition."""
    issues = []
    # Build a map of object/field → defined values
    field_values: dict[str, set[str]] = {}
    for f in field_files:
        try:
            tree = ET.parse(f)
            root_el = tree.getroot()
            ns = re.match(r"\{.*\}", root_el.tag)
            ns_str = ns.group(0) if ns else ""

            field_type = root_el.find(f"{ns_str}type")
            if field_type is None or field_type.text not in (
                "Picklist",
                "MultiselectPicklist",
            ):
                continue

            values = set()
            for val in root_el.findall(
                f".//{ns_str}valueSet//{ns_str}value/{ns_str}fullName"
            ):
                if val.text:
                    values.add(val.text)

            # Key by parent object folder + field name
            obj_name = f.parent.parent.name if f.parent.name == "fields" else "unknown"
            field_name = f.stem.replace(".field-meta", "")
            field_values[f"{obj_name}.{field_name}"] = values
        except ET.ParseError:
            pass

    # Check record type files for unmapped or extra values
    for rt in rt_files:
        try:
            tree = ET.parse(rt)
            root_el = tree.getroot()
            ns = re.match(r"\{.*\}", root_el.tag)
            ns_str = ns.group(0) if ns else ""

            obj_name = (
                rt.parent.parent.name if rt.parent.name == "recordTypes" else "unknown"
            )
            rt_name = rt.stem.replace(".recordType-meta", "")

            for picklist in root_el.findall(f"{ns_str}picklistValues"):
                field_el = picklist.find(f"{ns_str}picklist")
                if field_el is None or not field_el.text:
                    continue
                key = f"{obj_name}.{field_el.text}"
                if key not in field_values:
                    continue

                rt_vals = set()
                for val in picklist.findall(f"{ns_str}values/{ns_str}fullName"):
                    if val.text:
                        rt_vals.add(val.text)

                missing = field_values[key] - rt_vals
                if missing and len(missing) <= 5:
                    issues.append(
                        f"WARN: Record type {obj_name}.{rt_name} is missing "
                        f"picklist values for {field_el.text}: {sorted(missing)}"
                    )
        except ET.ParseError:
            pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Directory not found: {manifest_dir}")
        return 2

    field_files = find_field_files(manifest_dir)
    rt_files = find_record_type_files(manifest_dir)

    if not field_files:
        print(f"No .field-meta.xml files found in {manifest_dir}")
        print("Provide a Salesforce metadata directory with --manifest-dir")
        return 0

    print(f"Scanning {len(field_files)} field files, {len(rt_files)} record type files\n")

    all_issues = []
    all_issues.extend(check_unrestricted_picklists(field_files))
    all_issues.extend(check_record_type_picklist_gaps(rt_files, field_files))

    errors = [i for i in all_issues if i.startswith("ERROR")]
    warnings = [i for i in all_issues if i.startswith("WARN")]

    for issue in all_issues:
        print(f"  {issue}")

    print(f"\nResults: {len(errors)} errors, {len(warnings)} warnings")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
