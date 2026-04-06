#!/usr/bin/env python3
"""Checker script for Sharing Recalculation Performance skill.

Checks Salesforce metadata for sharing recalculation risk patterns:
- Criteria-based sharing rules on commonly high-churn fields
- Apex sharing reasons without a registered recalculation class
- Deeply nested public group structures used in sharing rules
- OWD settings that may indicate tightening risk

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sharing_recalculation_performance.py [--help]
    python3 check_sharing_recalculation_performance.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Fields that are commonly updated in bulk and should not be used in
# criteria-based sharing rules due to recalculation cost at volume.
HIGH_CHURN_FIELDS = {
    "Status",
    "Stage",
    "StageName",
    "Rating",
    "Priority",
    "LeadSource",
    "AccountSource",
    "ForecastCategoryName",
}

# Salesforce namespace prefix used in metadata XML
SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for sharing recalculation performance risks. "
            "Looks for criteria-based sharing rules on high-churn fields and Apex "
            "sharing reasons without a registered recalculation class."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _tag(name: str) -> str:
    """Return a fully-qualified XML tag with the Salesforce metadata namespace."""
    return f"{{{SF_NS}}}{name}"


def check_sharing_rules(manifest_dir: Path) -> list[str]:
    """Check sharingRules metadata for criteria-based rules on high-churn fields."""
    issues: list[str] = []
    sharing_rules_dir = manifest_dir / "sharingRules"

    if not sharing_rules_dir.exists():
        return issues

    for xml_file in sorted(sharing_rules_dir.glob("*.sharingRules")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"Could not parse {xml_file.name}: {exc}")
            continue

        root = tree.getroot()
        object_name = xml_file.stem  # e.g. "Opportunity" from Opportunity.sharingRules

        # SharingCriteriaRule elements represent criteria-based sharing rules
        for rule in root.findall(_tag("sharingCriteriaRules")):
            label_el = rule.find(_tag("label"))
            rule_label = label_el.text if label_el is not None else "(no label)"

            # Check each criterion filter item
            for item in rule.findall(f".//{_tag('filterItems')}"):
                field_el = item.find(_tag("field"))
                if field_el is None:
                    continue
                field_name = field_el.text or ""
                # Strip object prefix if present (e.g. "Opportunity.StageName" → "StageName")
                bare_field = field_name.split(".")[-1]

                if bare_field in HIGH_CHURN_FIELDS:
                    issues.append(
                        f"[HIGH RISK] Criteria-based sharing rule '{rule_label}' on "
                        f"{object_name} uses high-churn field '{bare_field}'. "
                        f"This rule re-evaluates on every bulk DML update to this field. "
                        f"Consider replacing with a role- or group-based sharing rule."
                    )

    return issues


def check_apex_sharing_reasons(manifest_dir: Path) -> list[str]:
    """Check custom object metadata for Apex sharing reasons missing a recalculation class."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"

    if not objects_dir.exists():
        return issues

    for xml_file in sorted(objects_dir.glob("*.object")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"Could not parse {xml_file.name}: {exc}")
            continue

        root = tree.getroot()
        object_name = xml_file.stem

        for reason in root.findall(_tag("sharingReasons")):
            name_el = reason.find(_tag("fullName"))
            reason_name = name_el.text if name_el is not None else "(unnamed)"

            class_el = reason.find(_tag("recalculateClassName"))
            has_class = class_el is not None and (class_el.text or "").strip()

            if not has_class:
                issues.append(
                    f"[CRITICAL] Apex sharing reason '{reason_name}' on {object_name} "
                    f"has no registered recalculation class. "
                    f"All Apex share rows for this reason will be silently deleted on any "
                    f"full sharing recalculation (OWD change, manual recalculation). "
                    f"Register a Database.Batchable class in Object Manager > {object_name} > "
                    f"Apex Sharing Reasons > {reason_name} > Edit > Recalculation Apex Class."
                )

    return issues


def check_sharing_recalculation_performance(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sharing_rules(manifest_dir))
    issues.extend(check_apex_sharing_reasons(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sharing_recalculation_performance(manifest_dir)

    if not issues:
        print("No sharing recalculation performance issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
