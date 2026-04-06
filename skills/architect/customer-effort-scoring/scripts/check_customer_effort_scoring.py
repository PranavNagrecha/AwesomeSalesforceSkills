#!/usr/bin/env python3
"""Checker script for Customer Effort Scoring skill.

Inspects Salesforce metadata in a project directory for common CX measurement
configuration issues: missing opted-out email guards in survey flows, missing
case-linkage fields, and survey flow timing problems.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_customer_effort_scoring.py [--help]
    python3 check_customer_effort_scoring.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Customer Effort Scoring configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files(root: Path, pattern: str) -> list[Path]:
    """Recursively find files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def check_flow_survey_invitation_guards(flow_path: Path) -> list[str]:
    """Check a Flow metadata XML file for survey invitation anti-patterns.

    Looks for:
    1. SurveyInvitation Create Records elements without a HasOptedOutOfEmail decision guard
    2. Scheduled Path delays of 0 minutes or 24+ hours for survey sends
    """
    issues: list[str] = []

    try:
        tree = ET.parse(flow_path)
    except ET.ParseError as exc:
        issues.append(f"{flow_path.name}: XML parse error — {exc}")
        return issues

    root = tree.getroot()
    ns = ""
    # Salesforce Flow XML may have a namespace prefix
    tag = root.tag
    if tag.startswith("{"):
        ns = tag[: tag.index("}") + 1]

    # Collect all recordCreate elements
    record_creates = root.findall(f".//{ns}recordCreates")

    creates_survey_invitation = False
    for rc in record_creates:
        object_elem = rc.find(f"{ns}object")
        if object_elem is not None and object_elem.text == "SurveyInvitation":
            creates_survey_invitation = True
            break

    if not creates_survey_invitation:
        # No SurveyInvitation creation in this flow — skip further checks
        return issues

    # Flow creates SurveyInvitation — check for HasOptedOutOfEmail reference
    flow_text = flow_path.read_text(encoding="utf-8")
    if "HasOptedOutOfEmail" not in flow_text:
        issues.append(
            f"{flow_path.name}: Creates SurveyInvitation but no 'HasOptedOutOfEmail' "
            "guard found. Add a Decision element checking Contact.HasOptedOutOfEmail "
            "before creating the invitation (Gotcha 2 in references/gotchas.md)."
        )

    # Check for ContactId null guard
    if "ContactId" in flow_text and "isNull" not in flow_text and "null" not in flow_text.lower():
        issues.append(
            f"{flow_path.name}: Creates SurveyInvitation using ContactId but no null "
            "check for ContactId detected. Cases without a linked Contact will cause "
            "Flow errors at runtime."
        )

    # Check for Scheduled Path timing (look for scheduledPaths elements)
    scheduled_paths = root.findall(f".//{ns}scheduledPaths")
    for sp in scheduled_paths:
        offset_elem = sp.find(f"{ns}offsetNumber")
        unit_elem = sp.find(f"{ns}offsetUnit")
        if offset_elem is not None and unit_elem is not None:
            try:
                offset = int(offset_elem.text or "0")
                unit = (unit_elem.text or "").lower()
                if unit == "minutes" and offset == 0:
                    issues.append(
                        f"{flow_path.name}: Scheduled Path has a 0-minute delay. "
                        "CES surveys sent immediately on case closure precede the "
                        "customer's closure notification email. Use a 15-minute minimum delay."
                    )
                if unit in ("days", "hours") and offset >= 1:
                    actual_hours = offset if unit == "hours" else offset * 24
                    if actual_hours >= 2:
                        issues.append(
                            f"{flow_path.name}: Scheduled Path delay of {offset} {unit} "
                            f"({actual_hours}h) exceeds the 60-minute CES trigger window. "
                            "CES data quality degrades significantly beyond 2 hours post-closure "
                            "(Gotcha 5 in references/gotchas.md)."
                        )
            except (ValueError, TypeError):
                pass

    return issues


def check_custom_fields_for_case_linkage(manifest_dir: Path) -> list[str]:
    """Check whether a custom Case lookup field exists on SurveyInvitation.

    A common omission: no case-linkage field means CES scores cannot be
    reported at the case level (Gotcha 3 in references/gotchas.md).
    """
    issues: list[str] = []

    # Look for SurveyInvitation custom field definitions
    field_files = find_files(manifest_dir, "SurveyInvitation.*.field-meta.xml")
    if not field_files:
        # No custom fields on SurveyInvitation found — warn
        issues.append(
            "No custom fields found on SurveyInvitation in this metadata package. "
            "If this org uses post-case surveys, a custom Lookup field to Case "
            "(e.g., Related_Case__c) is required for case-level CES reporting "
            "(Gotcha 3 in references/gotchas.md)."
        )
        return issues

    has_case_lookup = False
    for ff in field_files:
        content = ff.read_text(encoding="utf-8")
        if "Lookup" in content and "Case" in content:
            has_case_lookup = True
            break

    if not has_case_lookup:
        issues.append(
            "Custom fields on SurveyInvitation exist but none appear to be a Lookup to Case. "
            "Verify that a case-linkage field (e.g., Related_Case__c) is present and populated "
            "by the survey trigger Flow for case-level CES reporting."
        )

    return issues


def check_customer_effort_scoring(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check all Flow metadata files
    flow_files = find_files(manifest_dir, "*.flow-meta.xml")
    for flow_file in flow_files:
        issues.extend(check_flow_survey_invitation_guards(flow_file))

    # Check for SurveyInvitation case-linkage field
    issues.extend(check_custom_fields_for_case_linkage(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_customer_effort_scoring(manifest_dir)

    if not issues:
        print("No customer effort scoring issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
