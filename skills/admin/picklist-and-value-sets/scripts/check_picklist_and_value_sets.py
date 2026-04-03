#!/usr/bin/env python3
"""Checker script for Picklist and Value Sets skill.

Scans Salesforce metadata XML files in a sfdx source-format project and
checks for common picklist anti-patterns:

  1. Multi-select picklist fields with more than 500 values (platform limit)
  2. Standard picklist fields with more than 1,000 total values (active + inactive)
  3. Picklist fields with no values defined (empty value list)
  4. Custom picklist fields that appear to duplicate another field's values
     without using a Global Value Set (heuristic: same object has 2+ picklist
     fields with identical sorted value labels)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_picklist_and_value_sets.py [--help]
    python3 check_picklist_and_value_sets.py --manifest-dir path/to/sfdx/project
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce platform limits
PICKLIST_MAX_VALUES = 1000        # standard and custom picklist (active + inactive)
MULTISELECT_MAX_VALUES = 500      # multi-select picklist active values
EMPTY_FIELD_WARN_THRESHOLD = 0    # warn if a picklist has zero values

SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common picklist anti-patterns. "
            "Expects sfdx source-format layout: objects/<ObjectName>/<ObjectName>.object-meta.xml "
            "or fields/<FieldName>.field-meta.xml files."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce SFDX project (default: current directory).",
    )
    return parser.parse_args()


def _ns(tag: str) -> str:
    """Prepend Salesforce metadata namespace to a tag name."""
    return f"{{{SF_NAMESPACE}}}{tag}"


def _find_field_files(manifest_dir: Path) -> list[Path]:
    """Find all .field-meta.xml files in the project."""
    return list(manifest_dir.rglob("*.field-meta.xml"))


def _parse_picklist_values(field_root: ET.Element) -> tuple[str, list[str], bool, bool]:
    """
    Parse a field XML element and return:
      (field_type, value_labels, is_multi_select, uses_global_value_set)
    """
    field_type_el = field_root.find(_ns("type"))
    field_type = field_type_el.text.strip() if field_type_el is not None else ""

    is_multi = field_type in ("MultiselectPicklist",)
    is_picklist = field_type in ("Picklist", "MultiselectPicklist")

    # Check for global value set reference
    gvs_el = field_root.find(_ns("valueSet") + "/" + _ns("valueSetName"))
    # Also handle direct child valueSetName
    if gvs_el is None:
        vs_el = field_root.find(_ns("valueSet"))
        if vs_el is not None:
            gvs_el = vs_el.find(_ns("valueSetName"))
    uses_gvs = gvs_el is not None and bool(gvs_el.text and gvs_el.text.strip())

    # Collect value labels from inline value set
    labels: list[str] = []
    for value_el in field_root.iter(_ns("value")):
        label_el = value_el.find(_ns("label"))
        if label_el is not None and label_el.text:
            labels.append(label_el.text.strip())

    return field_type, labels, is_multi, uses_gvs


def check_picklist_and_value_sets(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    field_files = _find_field_files(manifest_dir)

    if not field_files:
        # No field files found — may not be an sfdx project, skip silently
        return issues

    # Track (object_name → {sorted_labels_tuple → [field_names]}) for duplication check
    object_value_map: dict[str, dict[tuple[str, ...], list[str]]] = {}

    for field_path in field_files:
        try:
            tree = ET.parse(field_path)
        except ET.ParseError as exc:
            issues.append(f"XML parse error in {field_path}: {exc}")
            continue

        root = tree.getroot()
        field_type, labels, is_multi, uses_gvs = _parse_picklist_values(root)

        if field_type not in ("Picklist", "MultiselectPicklist"):
            continue

        # Derive a human-readable field identifier from the path
        # Expected: .../objects/ObjectName/fields/FieldName.field-meta.xml
        parts = field_path.parts
        field_name = field_path.stem.replace(".field-meta", "")
        try:
            obj_idx = parts.index("objects")
            object_name = parts[obj_idx + 1] if obj_idx + 1 < len(parts) else "Unknown"
        except ValueError:
            object_name = "Unknown"
        field_id = f"{object_name}.{field_name}"

        # Check 1: empty value list (and not using a GVS)
        if not labels and not uses_gvs:
            issues.append(
                f"{field_id}: Picklist field has no values defined and does not reference "
                "a Global Value Set. Add values or link to a Global Value Set."
            )

        # Check 2: exceeds platform limits
        value_count = len(labels)
        if is_multi and value_count > MULTISELECT_MAX_VALUES:
            issues.append(
                f"{field_id}: Multi-select picklist has {value_count} values, "
                f"exceeding the platform limit of {MULTISELECT_MAX_VALUES}. "
                "Reduce active values or reconsider field design."
            )
        elif not is_multi and value_count > PICKLIST_MAX_VALUES:
            issues.append(
                f"{field_id}: Picklist has {value_count} values (active + inactive), "
                f"exceeding the platform limit of {PICKLIST_MAX_VALUES}."
            )

        # Check 3: collect for duplication heuristic (only for inline value sets)
        if labels and not uses_gvs:
            sorted_key = tuple(sorted(labels))
            if object_name not in object_value_map:
                object_value_map[object_name] = {}
            bucket = object_value_map[object_name].setdefault(sorted_key, [])
            bucket.append(field_name)

    # Check 3 (continued): flag objects with 2+ picklist fields sharing identical value lists
    for obj_name, value_buckets in object_value_map.items():
        for value_key, field_names in value_buckets.items():
            if len(field_names) >= 2 and len(value_key) >= 2:
                issues.append(
                    f"{obj_name}: Fields {field_names} share identical picklist values "
                    f"({len(value_key)} values) without using a Global Value Set. "
                    "Consider using a Global Value Set to manage shared values centrally."
                )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_picklist_and_value_sets(manifest_dir)

    if not issues:
        print("No picklist issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
