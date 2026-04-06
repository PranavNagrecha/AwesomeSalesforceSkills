#!/usr/bin/env python3
"""Checker script for Lead Data Import and Dedup skill.

Inspects a Salesforce metadata directory for common lead dedup configuration
issues: Duplicate Rule action modes, missing Lead Matching Rules, and active
rule count limits.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lead_data_import_and_dedup.py [--help]
    python3 check_lead_data_import_and_dedup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce metadata XML namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Hard limit: max 5 active Duplicate Rules per object
MAX_ACTIVE_DUPLICATE_RULES = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Lead data import and dedup configuration for common issues. "
            "Inspects DuplicateRule and MatchingRule metadata XML files."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    """Return a qualified XML tag name for the Salesforce metadata namespace."""
    return f"{{{SF_NS}}}{local}"


def _text(element: ET.Element, local: str, default: str = "") -> str:
    """Return text content of a child element, or default if not found."""
    child = element.find(_tag(local))
    return child.text.strip() if child is not None and child.text else default


def check_duplicate_rules(manifest_dir: Path) -> list[str]:
    """Check DuplicateRule XML files for Lead object issues."""
    issues: list[str] = []

    dup_rule_dir = manifest_dir / "duplicateRules"
    if not dup_rule_dir.exists():
        # No duplicate rules directory is not necessarily an error — skip silently
        return issues

    lead_rules: list[dict] = []

    for xml_file in sorted(dup_rule_dir.glob("Lead.*.duplicateRule")):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"Could not parse {xml_file.name}: {exc}")
            continue

        rule_name = xml_file.stem  # e.g. "Lead.Standard_Lead_Duplicate_Rule"
        is_active = _text(root, "isActive").lower() == "true"
        action = _text(root, "duplicateRuleFilters")  # may be empty
        # The action type is inside <duplicateRuleFilters> > <filterLogic> or
        # directly as <actionOnInsert> / <actionOnEdit> at the rule level.
        action_on_insert = _text(root, "actionOnInsert")
        action_on_edit = _text(root, "actionOnEdit")

        lead_rules.append({
            "name": rule_name,
            "active": is_active,
            "actionOnInsert": action_on_insert,
            "actionOnEdit": action_on_edit,
            "file": xml_file.name,
        })

    active_rules = [r for r in lead_rules if r["active"]]

    # Check 1: Active rule count limit
    if len(active_rules) >= MAX_ACTIVE_DUPLICATE_RULES:
        issues.append(
            f"Lead Duplicate Rules: {len(active_rules)} active rules found. "
            f"Salesforce enforces a maximum of {MAX_ACTIVE_DUPLICATE_RULES} active "
            "Duplicate Rules per object. Activating any additional rule will fail."
        )

    # Check 2: Any active rule set to Block — warn about Web-to-Lead bypass
    for rule in active_rules:
        if rule["actionOnInsert"].lower() == "block":
            issues.append(
                f"Lead Duplicate Rule '{rule['name']}' has actionOnInsert='Block'. "
                "Block mode does NOT prevent Web-to-Lead, API, or Apex inserts from "
                "creating duplicate leads. Add an after-insert Apex trigger or Flow "
                "to handle duplicate detection for non-UI channels."
            )

    # Check 3: No active Lead Duplicate Rules at all
    if not active_rules and lead_rules:
        issues.append(
            "Lead Duplicate Rules exist but none are active. "
            "No duplicate detection is currently enforced for the Lead object."
        )

    return issues


def check_matching_rules(manifest_dir: Path) -> list[str]:
    """Check MatchingRule XML files for Lead object issues."""
    issues: list[str] = []

    matching_rule_dir = manifest_dir / "matchingRules"
    if not matching_rule_dir.exists():
        return issues

    lead_matching_file = matching_rule_dir / "Lead.matchingRule"
    if not lead_matching_file.exists():
        issues.append(
            "No Lead.matchingRule file found. "
            "Ensure the Standard Lead Matching Rule is deployed and active."
        )
        return issues

    try:
        tree = ET.parse(lead_matching_file)
        root = tree.getroot()
    except ET.ParseError as exc:
        issues.append(f"Could not parse Lead.matchingRule: {exc}")
        return issues

    # Check that at least one matching rule is active on Lead
    active_rules = []
    for rule_elem in root.findall(_tag("matchingRules")):
        is_active = _text(rule_elem, "isActive").lower() == "true"
        label = _text(rule_elem, "label")
        if is_active:
            active_rules.append(label)

    if not active_rules:
        issues.append(
            "No active Matching Rules found for Lead. "
            "At least the Standard Lead Matching Rule should be active "
            "for Duplicate Rules to evaluate records."
        )

    return issues


def check_lead_data_import_and_dedup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_duplicate_rules(manifest_dir))
    issues.extend(check_matching_rules(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lead_data_import_and_dedup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
