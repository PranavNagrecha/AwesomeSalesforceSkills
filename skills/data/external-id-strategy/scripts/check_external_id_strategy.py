#!/usr/bin/env python3
"""Checker script for External ID Strategy skill.

Scans Salesforce metadata (SFDX project layout) for common external ID field
configuration mistakes described in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_external_id_strategy.py [--help]
    python3 check_external_id_strategy.py --manifest-dir path/to/sfdx/root
    python3 check_external_id_strategy.py --manifest-dir force-app/main/default

Checks performed:
  1. External ID fields without the Unique constraint set.
  2. Text external ID fields without explicit case-sensitive setting documented.
  3. Number external ID fields with non-zero scale (decimals) — potential key precision issues.
  4. Objects with more than 20 external ID fields (approaching the 25-field limit).
  5. CustomField XML files with externalId=true but missing the <unique> element entirely.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SF_METADATA_NS = "http://soap.sforce.com/2006/04/metadata"
EXTERNAL_ID_FIELD_LIMIT = 25
EXTERNAL_ID_WARNING_THRESHOLD = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for external ID field configuration issues. "
            "Expects an SFDX project layout with .field-meta.xml files."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory of the Salesforce metadata source (default: current directory). "
            "The script searches recursively for *.field-meta.xml files."
        ),
    )
    return parser.parse_args()


def _tag(local_name: str) -> str:
    """Return a namespaced tag string for ElementTree queries."""
    return f"{{{SF_METADATA_NS}}}{local_name}"


def parse_field_file(field_path: Path) -> dict | None:
    """Parse a .field-meta.xml file and return a dict of relevant attributes.

    Returns None if the file cannot be parsed or is not a CustomField.
    """
    try:
        tree = ET.parse(field_path)
    except ET.ParseError:
        return None

    root = tree.getroot()
    if root.tag != _tag("CustomField"):
        return None

    def text(local_name: str) -> str:
        el = root.find(_tag(local_name))
        return el.text.strip() if el is not None and el.text else ""

    return {
        "path": field_path,
        "full_name": text("fullName"),
        "type": text("type"),
        "external_id": text("externalId").lower() == "true",
        "unique": text("unique").lower() == "true",
        "case_sensitive": text("caseSensitive").lower() == "true",
        "scale": text("scale"),
        "has_unique_element": root.find(_tag("unique")) is not None,
    }


def find_field_files(manifest_dir: Path) -> list[Path]:
    """Recursively find all .field-meta.xml files under manifest_dir."""
    return list(manifest_dir.rglob("*.field-meta.xml"))


def derive_object_name(field_path: Path) -> str:
    """Derive the Salesforce object API name from a field file path.

    Expects SFDX layout: .../objects/<ObjectName>/fields/<FieldName>.field-meta.xml
    Falls back to the parent directory name if the layout does not match.
    """
    parts = field_path.parts
    try:
        fields_idx = [p.lower() for p in parts].index("fields")
        if fields_idx >= 2:
            return parts[fields_idx - 1]
    except ValueError:
        pass
    return field_path.parent.parent.name


def check_external_id_fields(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    field_files = find_field_files(manifest_dir)

    if not field_files:
        # No field metadata found — not necessarily an error; caller may be running
        # against a non-SFDX directory. Report informational message only.
        issues.append(
            f"No .field-meta.xml files found under {manifest_dir}. "
            "Ensure --manifest-dir points to an SFDX project root or source directory."
        )
        return issues

    # Group external ID fields by object for limit checking.
    external_id_by_object: dict[str, list[dict]] = {}

    for field_path in field_files:
        field = parse_field_file(field_path)
        if field is None or not field["external_id"]:
            continue

        object_name = derive_object_name(field_path)
        external_id_by_object.setdefault(object_name, []).append(field)

        rel_path = field_path

        # Check 1: External ID without Unique element present at all.
        if not field["has_unique_element"]:
            issues.append(
                f"[MISSING_UNIQUE] {rel_path}: field '{field['full_name']}' on object "
                f"'{object_name}' is marked externalId=true but has no <unique> element. "
                "Add <unique>true</unique> if this field will be used as an upsert key."
            )

        # Check 2: External ID with Unique element present but set to false.
        elif not field["unique"]:
            issues.append(
                f"[UNIQUE_FALSE] {rel_path}: field '{field['full_name']}' on object "
                f"'{object_name}' is marked externalId=true but unique=false. "
                "Set <unique>true</unique> to prevent duplicate external ID values "
                "and enable safe upsert operations."
            )

        # Check 3: Text external ID — note case-sensitivity for the author to verify.
        if field["type"] == "Text" and not field["case_sensitive"]:
            issues.append(
                f"[CASE_SENSITIVITY] {rel_path}: Text external ID field "
                f"'{field['full_name']}' on object '{object_name}' does not have "
                "<caseSensitive>true</caseSensitive> set. The default is case-INSENSITIVE "
                "uniqueness. Verify this matches the source system's key behavior. "
                "If the source system distinguishes 'ABC' from 'abc', set caseSensitive=true "
                "and normalize ETL input to a consistent case."
            )

        # Check 4: Number external ID with non-zero scale (decimals in the key value).
        if field["type"] == "Number" and field["scale"] not in ("", "0"):
            issues.append(
                f"[NUMBER_SCALE] {rel_path}: Number external ID field "
                f"'{field['full_name']}' on object '{object_name}' has scale={field['scale']}. "
                "Non-zero scale means the key includes decimal places. "
                "Confirm the source system key is truly a decimal value and not an integer — "
                "using scale=0 for integer keys avoids precision mismatch issues."
            )

    # Check 5: Objects approaching or exceeding the 25 external ID field limit.
    for object_name, fields in external_id_by_object.items():
        count = len(fields)
        if count >= EXTERNAL_ID_FIELD_LIMIT:
            field_names = ", ".join(f["full_name"] for f in fields)
            issues.append(
                f"[EXT_ID_LIMIT] Object '{object_name}' has {count} external ID fields, "
                f"which equals or exceeds the platform limit of {EXTERNAL_ID_FIELD_LIMIT}. "
                f"Fields: {field_names}. "
                "Remove unused external ID fields or consolidate using a composite key pattern."
            )
        elif count >= EXTERNAL_ID_WARNING_THRESHOLD:
            issues.append(
                f"[EXT_ID_NEAR_LIMIT] Object '{object_name}' has {count} external ID fields "
                f"(warning threshold: {EXTERNAL_ID_WARNING_THRESHOLD}, limit: {EXTERNAL_ID_FIELD_LIMIT}). "
                "Review whether all fields are actively used before adding more."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_external_id_fields(manifest_dir)

    if not issues:
        print("No external ID strategy issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
        print()

    print(f"Total issues found: {len(issues)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
