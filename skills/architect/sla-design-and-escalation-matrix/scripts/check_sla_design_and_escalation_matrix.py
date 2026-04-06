#!/usr/bin/env python3
"""Checker script for SLA Design and Escalation Matrix skill.

Validates Salesforce metadata for common SLA design defects:
  - Entitlement processes missing Business Hours
  - Escalation rule entries missing Business Hours
  - Entitlement processes at or near the milestone-per-process limit (10)
  - Milestone actions at or near the per-milestone limit (40)
  - References to the "Default" Business Hours record without annotation

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sla_design_and_escalation_matrix.py [--help]
    python3 check_sla_design_and_escalation_matrix.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce platform limits relevant to SLA design
MILESTONES_PER_PROCESS_LIMIT = 10
MILESTONE_ACTIONS_PER_MILESTONE_LIMIT = 40
MILESTONE_WARNING_THRESHOLD = 8  # warn when >= this many milestones in one process

# Salesforce ships "Default" as a 24/7 business hours record — using it without
# verification is a known design defect (see gotchas.md).
SUSPECT_BUSINESS_HOURS_NAME = "Default"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common SLA design defects: "
            "missing business hours on entitlement processes and escalation rule entries, "
            "milestone limit proximity, and suspect Default business hours references."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# XML namespace helpers
# ---------------------------------------------------------------------------

SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    """Return a Clark-notation tag for the Salesforce metadata namespace."""
    return f"{{{SF_NS}}}{local}"


def _text(element: ET.Element, tag: str) -> str:
    """Return the text content of a child element, or empty string if absent."""
    child = element.find(_tag(tag))
    return (child.text or "").strip() if child is not None else ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_entitlement_processes(manifest_dir: Path) -> list[str]:
    """Check EntitlementProcess metadata files for missing or suspect Business Hours."""
    issues: list[str] = []

    entitlement_dir = manifest_dir / "entitlementProcesses"
    if not entitlement_dir.exists():
        # Not every org has entitlement processes; skip silently.
        return issues

    for xml_file in sorted(entitlement_dir.glob("*.entitlementProcess-meta.xml")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"Cannot parse {xml_file.name}: {exc}")
            continue

        root = tree.getroot()
        process_name = _text(root, "name") or xml_file.stem

        # Check business hours
        bh_name = _text(root, "businessHours")
        if not bh_name:
            issues.append(
                f"EntitlementProcess '{process_name}': no businessHours set — "
                "milestone clocks will run on 24/7 calendar time. "
                "Set businessHours to a named Business Hours record with restricted working hours."
            )
        elif bh_name == SUSPECT_BUSINESS_HOURS_NAME:
            issues.append(
                f"EntitlementProcess '{process_name}': references businessHours='{SUSPECT_BUSINESS_HOURS_NAME}'. "
                "The Default Business Hours record is 24/7 unless manually changed. "
                "Verify Setup > Business Hours > Default has correct day/time restrictions, "
                "or create a named record with an explicit schedule."
            )

        # Check milestone count
        milestones = root.findall(_tag("milestones"))
        milestone_count = len(milestones)
        if milestone_count >= MILESTONES_PER_PROCESS_LIMIT:
            issues.append(
                f"EntitlementProcess '{process_name}': has {milestone_count} milestones — "
                f"at or above the platform limit of {MILESTONES_PER_PROCESS_LIMIT}. "
                "No additional milestones can be added. Consolidate tiers or split into separate processes."
            )
        elif milestone_count >= MILESTONE_WARNING_THRESHOLD:
            issues.append(
                f"EntitlementProcess '{process_name}': has {milestone_count} milestones — "
                f"approaching the platform limit of {MILESTONES_PER_PROCESS_LIMIT}. "
                "Plan for the limit before adding more milestones."
            )

        # Check milestone action counts
        for milestone_el in milestones:
            milestone_name = _text(milestone_el, "name") or "(unnamed)"
            action_count = len(
                milestone_el.findall(_tag("milestoneCriteriaItems"))
            ) + len(
                milestone_el.findall(_tag("successActions"))
            ) + len(
                milestone_el.findall(_tag("timeTriggers"))
            )
            if action_count >= MILESTONE_ACTIONS_PER_MILESTONE_LIMIT:
                issues.append(
                    f"EntitlementProcess '{process_name}', Milestone '{milestone_name}': "
                    f"has {action_count} actions — at or above the limit of "
                    f"{MILESTONE_ACTIONS_PER_MILESTONE_LIMIT}. Remove or consolidate actions."
                )

    return issues


def check_escalation_rules(manifest_dir: Path) -> list[str]:
    """Check EscalationRules metadata for missing or suspect Business Hours on entries."""
    issues: list[str] = []

    escalation_dir = manifest_dir / "escalationRules"
    if not escalation_dir.exists():
        return issues

    for xml_file in sorted(escalation_dir.glob("*.escalationRules-meta.xml")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"Cannot parse {xml_file.name}: {exc}")
            continue

        root = tree.getroot()
        rule_name = _text(root, "fullName") or xml_file.stem

        entries = root.findall(_tag("escalationRule")) or root.findall(_tag("ruleEntry"))
        # Handle both single-rule and multi-rule file shapes
        for rule_el in (root.findall(_tag("escalationRule")) or [root]):
            for entry_el in rule_el.findall(_tag("ruleEntry")):
                entry_name = _text(entry_el, "name") or "(unnamed entry)"
                bh = _text(entry_el, "businessHours")
                if not bh:
                    issues.append(
                        f"EscalationRule '{rule_name}', entry '{entry_name}': "
                        "no businessHours set on this entry — escalation will fire on "
                        "calendar time 24/7 even if the related entitlement process has "
                        "business hours configured. Add the Business Hours field to this entry."
                    )
                elif bh == SUSPECT_BUSINESS_HOURS_NAME:
                    issues.append(
                        f"EscalationRule '{rule_name}', entry '{entry_name}': "
                        f"references businessHours='{SUSPECT_BUSINESS_HOURS_NAME}'. "
                        "Verify the Default record is not 24/7 in Setup > Business Hours."
                    )

    return issues


def check_business_hours_files(manifest_dir: Path) -> list[str]:
    """Check BusinessHours metadata for records named Default (advisory only)."""
    issues: list[str] = []

    bh_dir = manifest_dir / "businessHours"
    if not bh_dir.exists():
        return issues

    for xml_file in sorted(bh_dir.glob("*.businessHours-meta.xml")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"Cannot parse {xml_file.name}: {exc}")
            continue

        root = tree.getroot()
        name = _text(root, "name") or xml_file.stem

        if name == SUSPECT_BUSINESS_HOURS_NAME:
            # Check whether it is truly 24/7 (all days active and hours = 00:00/24:00)
            # This is advisory — we cannot determine intent from metadata alone.
            issues.append(
                f"BusinessHours record '{name}' exists — verify it has restricted working hours "
                "and is not 24/7. The Salesforce-shipped Default record is 24/7 unless changed. "
                "Rename it or create a new record with an explicit schedule to avoid ambiguity."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_sla_design_and_escalation_matrix(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_entitlement_processes(manifest_dir))
    issues.extend(check_escalation_rules(manifest_dir))
    issues.extend(check_business_hours_files(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sla_design_and_escalation_matrix(manifest_dir)

    if not issues:
        print("No SLA design issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
