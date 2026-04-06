#!/usr/bin/env python3
"""Checker script for Lead Scoring Requirements skill.

Inspects a Salesforce metadata directory for common lead scoring
configuration issues: missing required custom fields on the Lead object,
formula fields used where Number fields are required, and absence of
MQL/SQL timestamp fields needed for funnel reporting.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lead_scoring_requirements.py [--help]
    python3 check_lead_scoring_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Custom fields expected on the Lead object for a compliant scoring model.
# Each entry: (api_name_stem, required_type_hint, description)
REQUIRED_FIELDS = [
    ("Fit_Score__c", "Number", "Fit dimension score — must be Number, not Formula"),
    ("Engagement_Score__c", "Number", "Engagement dimension score — must be Number, not Formula"),
    ("Composite_Score__c", "Number", "Composite score used in Flow/Assignment Rules — must be Number, not Formula"),
    ("Is_MQL__c", "Checkbox", "MQL flag field"),
    ("MQL_Date__c", "DateTime", "MQL timestamp for funnel reporting"),
    ("SQL_Date__c", "DateTime", "SQL timestamp for funnel reporting"),
    ("Lead_Stage__c", "Picklist", "Marketing lifecycle stage — separate from standard Status"),
    ("Recycle_Count__c", "Number", "Recycle counter for attribution tracking"),
    ("Recycle_Reason__c", "Picklist", "Recycle reason for feedback loop"),
]

# Field stems that are scoring-critical and MUST be stored Number, not Formula.
MUST_NOT_BE_FORMULA = {"Fit_Score__c", "Engagement_Score__c", "Composite_Score__c"}

# Salesforce Metadata API namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_lead_metadata(manifest_dir: Path) -> Path | None:
    """Locate the Lead object metadata file or fields directory."""
    # MDAPI-style: objects/Lead.object or objects/Lead.object-meta.xml
    for candidate in [
        manifest_dir / "objects" / "Lead.object",
        manifest_dir / "objects" / "Lead.object-meta.xml",
    ]:
        if candidate.exists():
            return candidate

    # SFDX-style: objects/Lead/fields/
    sfdx_dir = manifest_dir / "objects" / "Lead" / "fields"
    if sfdx_dir.is_dir():
        return sfdx_dir

    return None


def _load_mdapi_fields(object_file: Path) -> dict[str, str]:
    """Parse an MDAPI-style .object or .object-meta.xml and return {fieldName: type}."""
    fields: dict[str, str] = {}
    try:
        tree = ET.parse(object_file)
        root = tree.getroot()
        ns = {"sf": SF_NS}
        for field_el in root.findall("sf:fields", ns):
            name_el = field_el.find("sf:fullName", ns)
            type_el = field_el.find("sf:type", ns)
            if name_el is not None and type_el is not None:
                fields[name_el.text or ""] = type_el.text or ""
    except ET.ParseError:
        pass
    return fields


def _load_sfdx_fields(fields_dir: Path) -> dict[str, str]:
    """Parse SFDX-style field XML files and return {fieldName: type}."""
    fields: dict[str, str] = {}
    for xml_file in fields_dir.glob("*.field-meta.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            ns = {"sf": SF_NS}
            name_el = root.find("sf:fullName", ns)
            type_el = root.find("sf:type", ns)
            if name_el is not None and type_el is not None:
                fields[name_el.text or ""] = type_el.text or ""
        except ET.ParseError:
            pass
    return fields


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_lead_scoring_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    lead_path = _find_lead_metadata(manifest_dir)

    if lead_path is None:
        issues.append(
            "Lead object metadata not found. "
            "Expected objects/Lead.object-meta.xml (MDAPI) or objects/Lead/fields/ (SFDX). "
            "Cannot validate lead scoring field configuration."
        )
        return issues

    # Load fields
    if lead_path.is_dir():
        present_fields = _load_sfdx_fields(lead_path)
    else:
        present_fields = _load_mdapi_fields(lead_path)

    if not present_fields:
        issues.append(
            f"No custom fields parsed from Lead metadata at {lead_path}. "
            "Check that the file is valid Salesforce Metadata API XML."
        )
        return issues

    # Check 1: Required fields presence
    for field_name, expected_type, description in REQUIRED_FIELDS:
        if field_name not in present_fields:
            issues.append(
                f"MISSING FIELD: {field_name} ({expected_type}) — {description}. "
                f"Add this field to the Lead object."
            )

    # Check 2: Scoring-critical fields must not be Formula type
    for field_name in MUST_NOT_BE_FORMULA:
        if field_name in present_fields:
            actual_type = present_fields[field_name]
            if "formula" in actual_type.lower() or actual_type == "Summary":
                issues.append(
                    f"FORMULA FIELD RISK: {field_name} is type '{actual_type}'. "
                    f"Scoring fields used in Flow conditions or Assignment Rules must be "
                    f"Number (stored), not Formula. Formula fields cannot be reliably "
                    f"evaluated at DML time in record-triggered Flow entry criteria."
                )

    # Check 3: Lead_Stage__c must be Picklist, not Text
    if "Lead_Stage__c" in present_fields:
        stage_type = present_fields["Lead_Stage__c"]
        if stage_type not in ("Picklist", "MultiselectPicklist"):
            issues.append(
                f"FIELD TYPE: Lead_Stage__c is type '{stage_type}'. "
                f"Expected Picklist. A text field cannot be used safely in Flow conditions "
                f"or for grouping in funnel reports."
            )

    # Check 4: Warn if a custom Status__c field exists (suggests Status field confusion)
    if "Status__c" in present_fields:
        issues.append(
            "FIELD NAMING: Found Status__c custom field. "
            "Do not shadow the standard Lead Status field. "
            "Use Lead_Stage__c for marketing lifecycle stage to avoid confusion with "
            "the system-controlled Status field that governs lead conversion."
        )

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata directory for lead scoring configuration issues. "
            "Validates required custom fields on the Lead object, field types, and common "
            "anti-patterns (formula fields for score routing, Status field overloading)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lead_scoring_requirements(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
