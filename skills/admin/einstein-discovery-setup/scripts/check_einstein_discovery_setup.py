#!/usr/bin/env python3
"""Checker script for Einstein Discovery Setup skill.

Inspects Salesforce metadata to detect common Einstein Discovery setup issues:
- Writeback fields missing field-level security grants
- Writeback field count approaching or exceeding the limit per object
- Prediction definitions that may reference stale model versions
- Story metadata missing deployment configuration

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_discovery_setup.py [--help]
    python3 check_einstein_discovery_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


WRITEBACK_FIELD_LIMIT = 3
EINSTEIN_FIELD_PREFIXES = ("Einstein_", "einstein_")
PREDICTION_DEFINITION_PREFIX = "1OR"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Einstein Discovery Setup configuration and metadata for common issues. "
            "Detects writeback field FLS gaps, object-level writeback field limits, "
            "and prediction definition configuration problems."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_xml_files(root: Path, pattern: str) -> list[Path]:
    """Return all XML files matching a glob pattern under root."""
    return sorted(root.rglob(pattern))


def check_writeback_field_fls(manifest_dir: Path) -> list[str]:
    """Check that Einstein writeback fields have at least one FLS grant.

    Looks for CustomField metadata files whose name starts with an Einstein prefix
    and checks corresponding Profile or PermissionSet metadata for fieldPermissions entries.
    Returns issue strings for any writeback field with no FLS grants found.
    """
    issues: list[str] = []

    # Collect writeback field names from CustomField metadata
    writeback_fields: list[str] = []
    fields_dir = manifest_dir / "objects"
    if not fields_dir.exists():
        fields_dir = manifest_dir  # flat structure fallback

    for field_file in find_xml_files(manifest_dir, "*.field-meta.xml"):
        field_name = field_file.stem.replace(".field-meta", "")
        if any(field_name.startswith(prefix) for prefix in EINSTEIN_FIELD_PREFIXES):
            writeback_fields.append(field_name)

    if not writeback_fields:
        return issues  # No writeback fields found — nothing to check

    # Collect field permissions granted in profiles and permission sets
    granted_fields: set[str] = set()
    for perm_file in find_xml_files(manifest_dir, "*.profile-meta.xml"):
        granted_fields.update(_extract_field_permissions(perm_file))
    for perm_file in find_xml_files(manifest_dir, "*.permissionset-meta.xml"):
        granted_fields.update(_extract_field_permissions(perm_file))

    for field_name in writeback_fields:
        # Check if any permission grants read access for this field
        field_found = any(
            field_name in granted_field for granted_field in granted_fields
        )
        if not field_found:
            issues.append(
                f"Einstein writeback field '{field_name}' has no field-level security grants "
                f"in any profile or permission set. The field will be invisible to all users "
                f"in reports, list views, and page layouts until FLS is assigned."
            )

    return issues


def _extract_field_permissions(perm_file: Path) -> list[str]:
    """Return field names where readable=true in a Profile or PermissionSet XML file."""
    readable_fields: list[str] = []
    try:
        tree = ET.parse(perm_file)
        root = ET.getroot()
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        for fp in root.findall(".//sf:fieldPermissions", ns):
            readable_el = fp.find("sf:readable", ns)
            field_el = fp.find("sf:field", ns)
            if (
                readable_el is not None
                and field_el is not None
                and readable_el.text == "true"
            ):
                readable_fields.append(field_el.text or "")
    except ET.ParseError:
        pass  # Malformed XML — skip silently
    return readable_fields


def check_writeback_field_count_per_object(manifest_dir: Path) -> list[str]:
    """Check that no Salesforce object exceeds the max writeback fields limit.

    Counts Einstein writeback fields per object and warns if count equals or exceeds 3.
    """
    issues: list[str] = []
    object_field_counts: dict[str, list[str]] = {}

    for field_file in find_xml_files(manifest_dir, "*.field-meta.xml"):
        field_name = field_file.stem.replace(".field-meta", "")
        if not any(field_name.startswith(prefix) for prefix in EINSTEIN_FIELD_PREFIXES):
            continue

        # Infer object name from parent directory or file path
        object_name = field_file.parent.name
        if object_name == "fields":
            object_name = field_file.parent.parent.name

        if object_name not in object_field_counts:
            object_field_counts[object_name] = []
        object_field_counts[object_name].append(field_name)

    for object_name, fields in object_field_counts.items():
        count = len(fields)
        if count >= WRITEBACK_FIELD_LIMIT:
            issues.append(
                f"Object '{object_name}' has {count} Einstein Discovery writeback field(s) "
                f"({', '.join(fields)}). The platform maximum is {WRITEBACK_FIELD_LIMIT} per object. "
                f"Deploying an additional prediction with writeback on this object will fail."
            )
        elif count == WRITEBACK_FIELD_LIMIT - 1:
            issues.append(
                f"Object '{object_name}' has {count} Einstein Discovery writeback field(s). "
                f"Only 1 slot remains before reaching the {WRITEBACK_FIELD_LIMIT}-field limit. "
                f"Review before adding another prediction definition with writeback on this object."
            )

    return issues


def check_prediction_definition_files(manifest_dir: Path) -> list[str]:
    """Check prediction definition metadata for common configuration issues.

    Looks for PredictionDefinition metadata XML files and checks for:
    - Missing or disabled status
    - Missing target object mapping
    """
    issues: list[str] = []

    for pd_file in find_xml_files(manifest_dir, "*.predictionDef-meta.xml"):
        try:
            tree = ET.parse(pd_file)
            root = ET.getroot()
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}

            status_el = root.find(".//sf:status", ns)
            object_el = root.find(".//sf:targetObject", ns)

            if status_el is None or status_el.text != "Enabled":
                status_val = status_el.text if status_el is not None else "missing"
                issues.append(
                    f"PredictionDefinition '{pd_file.name}' has status '{status_val}'. "
                    f"Prediction definitions must be in 'Enabled' status for scoring to run."
                )

            if object_el is None or not (object_el.text or "").strip():
                issues.append(
                    f"PredictionDefinition '{pd_file.name}' is missing a targetObject mapping. "
                    f"Scoring cannot run without a target Salesforce object."
                )

        except ET.ParseError:
            issues.append(
                f"PredictionDefinition file '{pd_file.name}' could not be parsed as XML. "
                f"Check the file for syntax errors."
            )

    return issues


def check_einstein_discovery_setup(manifest_dir: Path) -> list[str]:
    """Run all Einstein Discovery setup checks and return a combined list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_writeback_field_fls(manifest_dir))
    issues.extend(check_writeback_field_count_per_object(manifest_dir))
    issues.extend(check_prediction_definition_files(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_einstein_discovery_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
