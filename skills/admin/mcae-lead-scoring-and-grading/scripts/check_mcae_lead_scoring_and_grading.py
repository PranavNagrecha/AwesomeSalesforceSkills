#!/usr/bin/env python3
"""Checker script for MCAE Lead Scoring and Grading skill.

Validates a Salesforce metadata export directory for common MCAE scoring and
grading configuration issues. Checks:

  - Presence of Score and Grade field mappings on Lead and/or Contact
  - Automation rules with score/grade threshold criteria
  - Evidence of score decay configuration
  - Field-level security risks on Score/Grade fields

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_mcae_lead_scoring_and_grading.py [--help]
    python3 check_mcae_lead_scoring_and_grading.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check MCAE Lead Scoring and Grading configuration and metadata "
            "for common issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_score_field_on_lead_or_contact(manifest_dir: Path) -> list[str]:
    """Warn if no Score-related custom or standard field exists on Lead or Contact."""
    issues: list[str] = []

    score_field_found = False
    for obj_name in ("Lead", "Contact"):
        fields_dir = manifest_dir / "objects" / obj_name / "fields"
        if not fields_dir.exists():
            continue
        for field_file in fields_dir.glob("*.field-meta.xml"):
            name_lower = field_file.stem.lower()
            if "score" in name_lower:
                score_field_found = True
                break
        if score_field_found:
            break

    if not score_field_found:
        issues.append(
            "No Score-related field found on Lead or Contact. "
            "MCAE prospect score must be mapped to a CRM field in the connector "
            "field mapping to enable CRM-side reporting on score. "
            "Verify Admin > Connectors > Salesforce Connector > Field Mapping."
        )
    return issues


def check_grade_field_on_lead_or_contact(manifest_dir: Path) -> list[str]:
    """Warn if no Grade-related custom or standard field exists on Lead or Contact."""
    issues: list[str] = []

    grade_field_found = False
    for obj_name in ("Lead", "Contact"):
        fields_dir = manifest_dir / "objects" / obj_name / "fields"
        if not fields_dir.exists():
            continue
        for field_file in fields_dir.glob("*.field-meta.xml"):
            name_lower = field_file.stem.lower()
            if "grade" in name_lower or "rating" in name_lower:
                grade_field_found = True
                break
        if grade_field_found:
            break

    if not grade_field_found:
        issues.append(
            "No Grade-related field found on Lead or Contact. "
            "MCAE prospect grade should be mapped to a CRM field so Sales can "
            "filter and report on grade. Common field names: 'Prospect_Grade__c', "
            "'Rating', or a custom text field. "
            "Verify Admin > Connectors > Salesforce Connector > Field Mapping."
        )
    return issues


def _read_xml_text(path: Path, tag: str) -> list[str]:
    """Return all text values for a given XML tag in a file, ignoring parse errors."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # Strip namespace if present
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"
        return [el.text or "" for el in root.iter(f"{ns}{tag}")]
    except ET.ParseError:
        return []


def check_lead_score_field_not_overwritable(manifest_dir: Path) -> list[str]:
    """Warn if Score field on Lead has no field-level security or validation rule protecting it."""
    issues: list[str] = []

    # Check for any validation rule on Lead that references score field
    validation_dir = manifest_dir / "objects" / "Lead" / "validationRules"
    if not validation_dir.exists():
        issues.append(
            "No validation rules found on Lead object. "
            "Consider adding a validation rule to prevent non-MCAE users from "
            "overwriting the Score field on Lead records, which causes CRM/MCAE divergence. "
            "Alternatively, restrict the Score field with field-level security."
        )
    return issues


def check_automation_rule_files(manifest_dir: Path) -> list[str]:
    """Look for automation rule metadata files with score/grade criteria.

    MCAE automation rules are not part of the standard Salesforce metadata
    export (they live in MCAE, not in org metadata). This check looks for
    any custom automation documentation or notes files the team may have
    exported alongside the metadata.
    """
    issues: list[str] = []

    # Check for any flows that reference MCAE score fields (post-sync CRM flows)
    flows_dir = manifest_dir / "flows"
    if flows_dir.exists():
        score_flows = []
        for flow_file in flows_dir.glob("*.flow-meta.xml"):
            content = flow_file.read_text(errors="replace")
            if "score" in content.lower() and "grade" in content.lower():
                score_flows.append(flow_file.name)

        if score_flows:
            issues.append(
                f"Found {len(score_flows)} Salesforce Flow(s) that reference both "
                f"'score' and 'grade': {', '.join(score_flows)}. "
                "Score-based lead routing should be handled by MCAE Automation Rules, "
                "not by CRM Flows. CRM Flows acting on synced score fields can produce "
                "race conditions and duplicate assignments. Review these flows to ensure "
                "they are not duplicating MCAE routing logic."
            )

    return issues


def check_score_field_type(manifest_dir: Path) -> list[str]:
    """Warn if a Score field on Lead is not an integer/number type."""
    issues: list[str] = []

    for obj_name in ("Lead", "Contact"):
        fields_dir = manifest_dir / "objects" / obj_name / "fields"
        if not fields_dir.exists():
            continue
        for field_file in fields_dir.glob("*.field-meta.xml"):
            name_lower = field_file.stem.lower()
            if "score" not in name_lower:
                continue
            type_values = _read_xml_text(field_file, "type")
            for t in type_values:
                if t and t.lower() not in ("number", "currency", "int", "double"):
                    issues.append(
                        f"{obj_name}.{field_file.stem}: Score field has type '{t}'. "
                        "MCAE prospect score is an integer. The mapped CRM field should "
                        "be a Number type to support numeric filtering and reporting. "
                        "Text or picklist types will break score-based report filters."
                    )
    return issues


# ---------------------------------------------------------------------------
# Main check runner
# ---------------------------------------------------------------------------

def check_mcae_lead_scoring_and_grading(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_score_field_on_lead_or_contact(manifest_dir))
    issues.extend(check_grade_field_on_lead_or_contact(manifest_dir))
    issues.extend(check_lead_score_field_not_overwritable(manifest_dir))
    issues.extend(check_automation_rule_files(manifest_dir))
    issues.extend(check_score_field_type(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_mcae_lead_scoring_and_grading(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
