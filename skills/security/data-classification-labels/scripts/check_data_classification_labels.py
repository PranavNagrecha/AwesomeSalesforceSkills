#!/usr/bin/env python3
"""Checker script for Data Classification Labels skill.

Validates Salesforce metadata to confirm that custom fields in high-sensitivity
objects have SecurityClassification and BusinessStatus set, and that common
high-sensitivity standard fields have classification stub files present.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_classification_labels.py [--manifest-dir path/to/metadata]

The manifest-dir should be the root of an SFDX or Metadata API project, e.g.:
    - SFDX: the project root (looks under force-app/main/default/)
    - Metadata API: the unpackaged/ or src/ directory

What this checker validates:
    1. Custom fields in high-sensitivity objects have SecurityClassification set.
    2. Custom fields with SecurityClassification set also have BusinessStatus set.
    3. Standard field classification stubs exist for common PII-bearing standard fields.
    4. Classification attributes are not present in projects targeting API version < 46.0
       (warns that classification will be silently dropped on deploy).
    5. Fields classified Restricted or MissionCritical have BusinessOwnerId set.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Objects considered high-sensitivity — custom fields on these should be classified.
HIGH_SENSITIVITY_OBJECTS: list[str] = [
    "Contact",
    "Lead",
    "Account",
    "Case",
    "User",
]

# Standard fields that commonly hold PII data and should have classification stubs.
# These are (ObjectName, FieldName) pairs.
PII_STANDARD_FIELDS: list[tuple[str, str]] = [
    ("Contact", "Email"),
    ("Contact", "Phone"),
    ("Contact", "MobilePhone"),
    ("Contact", "HomePhone"),
    ("Contact", "Birthdate"),
    ("Lead", "Email"),
    ("Lead", "Phone"),
    ("Lead", "MobilePhone"),
    ("User", "Email"),
    ("User", "Phone"),
    ("User", "MobilePhone"),
]

# SecurityClassification values that require BusinessOwnerId to be set.
HIGH_RESTRICTION_CLASSIFICATIONS: set[str] = {"Restricted", "MissionCritical"}

# Minimum API version for classification metadata support.
MIN_API_VERSION_FOR_CLASSIFICATION = 46.0

# Salesforce Metadata API namespace.
SF_NS = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


def find_objects_dir(manifest_dir: Path) -> Path | None:
    """Locate the objects/ directory under the manifest root."""
    candidates = [
        manifest_dir / "force-app" / "main" / "default" / "objects",
        manifest_dir / "src" / "objects",
        manifest_dir / "unpackaged" / "objects",
        manifest_dir / "objects",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def find_sfdx_project_json(manifest_dir: Path) -> Path | None:
    """Locate sfdx-project.json in the manifest root."""
    candidate = manifest_dir / "sfdx-project.json"
    if candidate.is_file():
        return candidate
    return None


# ---------------------------------------------------------------------------
# XML parsing helpers
# ---------------------------------------------------------------------------


def _ns(tag: str) -> str:
    return f"{{{SF_NS}}}{tag}"


def parse_field_metadata(field_xml: Path) -> dict:
    """Parse a Salesforce field metadata XML file.

    Returns a dict with classification-relevant fields:
        - full_name: the field's fullName
        - security_classification: value or None
        - compliance_group: list of values (may be empty)
        - business_status: value or None
        - business_owner_id: value or None
        - error: parse error string or None
    """
    result: dict = {
        "full_name": None,
        "security_classification": None,
        "compliance_group": [],
        "business_status": None,
        "business_owner_id": None,
        "error": None,
    }

    try:
        tree = ET.parse(field_xml)
        root = tree.getroot()
    except ET.ParseError as exc:
        result["error"] = str(exc)
        return result

    def get_text(tag: str) -> str | None:
        el = root.find(_ns(tag))
        if el is not None:
            return (el.text or "").strip() or None
        return None

    result["full_name"] = get_text("fullName")
    result["security_classification"] = get_text("securityClassification")
    result["business_status"] = get_text("businessStatus")
    result["business_owner_id"] = get_text("businessOwnerId")

    # complianceGroup may appear multiple times
    for cg_el in root.findall(_ns("complianceGroup")):
        if cg_el.text:
            result["compliance_group"].append(cg_el.text.strip())

    return result


def get_api_version_from_sfdx_project(project_json: Path) -> float | None:
    """Extract sourceApiVersion from sfdx-project.json.

    Returns the version as a float, or None if not found or not parseable.
    Uses stdlib json module — no pip dependencies.
    """
    import json

    try:
        with project_json.open() as f:
            data = json.load(f)
        version_str = data.get("sourceApiVersion")
        if version_str is not None:
            return float(str(version_str))
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    return None


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def check_api_version(manifest_dir: Path) -> list[str]:
    """Warn if sfdx-project.json uses an API version that drops classification metadata."""
    issues: list[str] = []

    project_json = find_sfdx_project_json(manifest_dir)
    if project_json is None:
        return issues  # Not an SFDX project — skip check

    version = get_api_version_from_sfdx_project(project_json)
    if version is None:
        issues.append(
            f"[sfdx-project.json] Could not read sourceApiVersion. "
            f"Ensure it is set to {MIN_API_VERSION_FOR_CLASSIFICATION:.0f}.0 or later — "
            f"classification metadata is silently dropped on deploys using API v45.0 or lower."
        )
    elif version < MIN_API_VERSION_FOR_CLASSIFICATION:
        issues.append(
            f"[sfdx-project.json] sourceApiVersion is {version:.1f} — "
            f"classification metadata (securityClassification, complianceGroup, businessStatus) "
            f"requires API v{MIN_API_VERSION_FOR_CLASSIFICATION:.0f}.0 or later. "
            f"Classification attributes will be silently dropped on deploy. "
            f"Update sourceApiVersion to 61.0 or later."
        )

    return issues


def check_custom_field_classification(objects_dir: Path) -> list[str]:
    """Check custom fields on high-sensitivity objects for missing classification."""
    issues: list[str] = []

    for object_name in HIGH_SENSITIVITY_OBJECTS:
        # SFDX layout: objects/<ObjectName>/fields/
        fields_dir = objects_dir / object_name / "fields"
        if not fields_dir.is_dir():
            continue

        field_files = list(fields_dir.glob("*.field-meta.xml"))
        for field_file in field_files:
            # Skip standard field stubs (no __c in name)
            if "__c" not in field_file.stem:
                continue

            parsed = parse_field_metadata(field_file)
            if parsed["error"]:
                issues.append(
                    f"[{object_name}/{field_file.name}] Parse error: {parsed['error']}"
                )
                continue

            field_label = parsed["full_name"] or field_file.stem

            # Check SecurityClassification is set
            if not parsed["security_classification"]:
                issues.append(
                    f"[{object_name}.{field_label}] SecurityClassification is not set. "
                    f"All custom fields on high-sensitivity objects should have an explicit "
                    f"SecurityClassification value (Public, Internal, Confidential, "
                    f"Restricted, or MissionCritical)."
                )

            # Check BusinessStatus is set when SecurityClassification is set
            if (
                parsed["security_classification"]
                and not parsed["business_status"]
            ):
                issues.append(
                    f"[{object_name}.{field_label}] SecurityClassification is set to "
                    f"'{parsed['security_classification']}' but BusinessStatus is not set. "
                    f"Set BusinessStatus to Active, Deprecated, or Inactive to complete "
                    f"the classification record."
                )

            # Check BusinessOwnerId for high-restriction fields
            if (
                parsed["security_classification"]
                in HIGH_RESTRICTION_CLASSIFICATIONS
                and not parsed["business_owner_id"]
            ):
                issues.append(
                    f"[{object_name}.{field_label}] SecurityClassification is "
                    f"'{parsed['security_classification']}' but BusinessOwnerId is not set. "
                    f"High-restriction fields should have a designated Business Owner "
                    f"for accountability."
                )

    return issues


def check_standard_field_stubs(objects_dir: Path) -> list[str]:
    """Check that common PII-bearing standard fields have classification stub files."""
    issues: list[str] = []

    for object_name, field_name in PII_STANDARD_FIELDS:
        stub_path = objects_dir / object_name / "fields" / f"{field_name}.field-meta.xml"
        if not stub_path.exists():
            continue  # Object/fields dir may not be in this project — skip

        parsed = parse_field_metadata(stub_path)
        if parsed["error"]:
            issues.append(
                f"[{object_name}.{field_name}] Classification stub parse error: {parsed['error']}"
            )
            continue

        if not parsed["security_classification"]:
            issues.append(
                f"[{object_name}.{field_name}] Standard field classification stub exists "
                f"but SecurityClassification is not set. This is a known PII-bearing "
                f"standard field — set SecurityClassification (e.g., Confidential or Restricted)."
            )

    return issues


def check_missing_standard_stubs(objects_dir: Path) -> list[str]:
    """Suggest creating classification stubs for PII standard fields where objects are in scope."""
    issues: list[str] = []

    for object_name, field_name in PII_STANDARD_FIELDS:
        object_fields_dir = objects_dir / object_name / "fields"
        if not object_fields_dir.is_dir():
            continue  # Object not in project scope — skip

        stub_path = object_fields_dir / f"{field_name}.field-meta.xml"
        if not stub_path.exists():
            issues.append(
                f"[{object_name}.{field_name}] No classification stub found for this "
                f"PII-bearing standard field. Create a stub .field-meta.xml containing "
                f"only securityClassification and complianceGroup elements to classify it "
                f"in source control."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_data_classification_labels(manifest_dir: Path) -> list[str]:
    """Run all data classification checks against the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # API version check (independent of objects dir)
    issues.extend(check_api_version(manifest_dir))

    objects_dir = find_objects_dir(manifest_dir)
    if objects_dir is None:
        # No objects/ directory — cannot check field classification
        # Only warn if there's also an sfdx-project.json (i.e., it looks like a project)
        if find_sfdx_project_json(manifest_dir) is not None:
            issues.append(
                f"Could not locate an objects/ directory under {manifest_dir}. "
                "Field classification checks require an SFDX or Metadata API project "
                "with an objects/ directory."
            )
        return issues

    issues.extend(check_custom_field_classification(objects_dir))
    issues.extend(check_standard_field_stubs(objects_dir))
    issues.extend(check_missing_standard_stubs(objects_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Data Classification Label issues. "
            "Validates that custom fields on high-sensitivity objects have SecurityClassification "
            "and BusinessStatus set, that PII standard fields have classification stubs, "
            "and that the project API version supports classification metadata deployment."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    print(f"Checking Data Classification Labels in: {manifest_dir}")
    print()

    issues = check_data_classification_labels(manifest_dir)

    if not issues:
        print("No issues found. Data classification metadata looks correct.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"  [{i}] {issue}")
    print()
    print(
        "Resolve these issues before claiming classification coverage. "
        "See skills/security/data-classification-labels/references/gotchas.md for details."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
