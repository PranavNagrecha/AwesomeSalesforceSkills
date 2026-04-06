#!/usr/bin/env python3
"""Checker script for Territory Design Requirements skill.

Validates Salesforce ETM territory metadata exported as XML (Metadata API format)
against best practices documented in the territory-design-requirements skill:
  - Territory count vs. org limit
  - Assignment rule criteria count per territory (performance threshold)
  - Assignment rule criteria field type warnings (date fields not supported)
  - Hierarchy depth
  - Territory type priority value presence

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_territory_design_requirements.py [--help]
    python3 check_territory_design_requirements.py --manifest-dir path/to/metadata

The manifest directory should contain Salesforce Metadata API XML files, typically:
  - territory2Models/<ModelName>.territory2Model-meta.xml
  - territory2Types/<TypeName>.territory2Type-meta.xml
  - territory2s/<TerritoryName>.territory2-meta.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Thresholds (from skill documentation and official Salesforce best practices)
# ---------------------------------------------------------------------------

TERRITORY_COUNT_LIMIT = 1000
TERRITORY_COUNT_WARNING_THRESHOLD = 800
ASSIGNMENT_RULE_CRITERIA_PERFORMANCE_THRESHOLD = 10
HIERARCHY_DEPTH_WARNING = 5
HIERARCHY_DEPTH_MAX = 6

DATE_TYPE_INDICATORS = [
    "date", "datetime", "Date__c", "DateTime__c",
    "CreatedDate", "LastModifiedDate", "CloseDate",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check ETM territory metadata against territory-design-requirements "
            "best practices. Pass the root of a Salesforce metadata directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Salesforce metadata XML files (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def find_xml_files(root: Path, suffix: str) -> list:
    return sorted(root.rglob("*" + suffix))


def parse_xml_safe(path: Path):
    try:
        tree = ET.parse(str(path))
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def find_text(element, tag: str) -> str:
    for child in element:
        if strip_ns(child.tag) == tag:
            return (child.text or "").strip()
    return ""


def find_all(element, tag: str) -> list:
    return [child for child in element if strip_ns(child.tag) == tag]


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_territory_count(manifest_dir: Path) -> list:
    issues = []
    territory_files = find_xml_files(manifest_dir, ".territory2-meta.xml")
    count = len(territory_files)
    if count == 0:
        return issues
    if count >= TERRITORY_COUNT_LIMIT:
        issues.append(
            "LIMIT: Territory count ({}) has reached or exceeded the Enterprise Edition "
            "default limit of {}. Request a limit increase from Salesforce Support.".format(
                count, TERRITORY_COUNT_LIMIT
            )
        )
    elif count >= TERRITORY_COUNT_WARNING_THRESHOLD:
        issues.append(
            "WARNING: Territory count ({}) is approaching the Enterprise Edition default "
            "limit of {}. Plan a Salesforce Support limit increase request "
            "before territory expansion.".format(count, TERRITORY_COUNT_LIMIT)
        )
    return issues


def check_assignment_rule_criteria_count(manifest_dir: Path) -> list:
    issues = []
    rule_files = find_xml_files(manifest_dir, ".accountTerritoryAssignmentRule-meta.xml")
    for rule_file in rule_files:
        root = parse_xml_safe(rule_file)
        if root is None:
            continue
        for criteria_tag in ("ruleItems", "filterItems", "criteriaItems"):
            items = find_all(root, criteria_tag)
            count = len(items)
            if count > ASSIGNMENT_RULE_CRITERIA_PERFORMANCE_THRESHOLD:
                issues.append(
                    "PERFORMANCE: {} has {} assignment rule criteria "
                    "(recommended max: {}). High criteria counts degrade assignment rule "
                    "execution time. Refactor using a custom proxy picklist or numeric "
                    "field.".format(rule_file.name, count, ASSIGNMENT_RULE_CRITERIA_PERFORMANCE_THRESHOLD)
                )
    return issues


def check_date_field_criteria(manifest_dir: Path) -> list:
    issues = []
    rule_files = find_xml_files(manifest_dir, ".accountTerritoryAssignmentRule-meta.xml")
    for rule_file in rule_files:
        root = parse_xml_safe(rule_file)
        if root is None:
            continue
        for criteria_tag in ("ruleItems", "filterItems", "criteriaItems"):
            for item in find_all(root, criteria_tag):
                field_name = find_text(item, "field") or find_text(item, "name")
                if not field_name:
                    continue
                for date_indicator in DATE_TYPE_INDICATORS:
                    if date_indicator.lower() in field_name.lower():
                        issues.append(
                            "UNSUPPORTED_FIELD_TYPE: {} references field '{}' in an assignment "
                            "rule. Date/datetime fields are NOT supported as ETM assignment rule "
                            "criteria. Replace with a custom picklist or numeric proxy "
                            "field.".format(rule_file.name, field_name)
                        )
                        break
    return issues


def check_territory_type_priority(manifest_dir: Path) -> list:
    issues = []
    type_files = find_xml_files(manifest_dir, ".territory2Type-meta.xml")
    for type_file in type_files:
        root = parse_xml_safe(type_file)
        if root is None:
            continue
        priority = find_text(root, "priority")
        if not priority:
            issues.append(
                "MISSING_PRIORITY: Territory type '{}' has no priority value. "
                "Territory type priority controls Opportunity Territory Assignment when an "
                "account belongs to multiple territories. Set an explicit integer priority "
                "value.".format(type_file.stem)
            )
    return issues


def check_territory_hierarchy_depth(manifest_dir: Path) -> list:
    issues = []
    territory_files = find_xml_files(manifest_dir, ".territory2-meta.xml")
    if not territory_files:
        return issues

    parent_map = {}
    for tf in territory_files:
        root = parse_xml_safe(tf)
        if root is None:
            continue
        name = tf.stem.replace(".territory2", "")
        parent = find_text(root, "parentTerritory") or find_text(root, "parentTerritoryId")
        parent_map[name] = parent if parent else None

    def get_depth(name, visited):
        if name in visited:
            return 0
        visited.add(name)
        parent = parent_map.get(name)
        if not parent:
            return 1
        return 1 + get_depth(parent, visited)

    max_depth = 0
    deepest_territory = ""
    for name in parent_map:
        depth = get_depth(name, set())
        if depth > max_depth:
            max_depth = depth
            deepest_territory = name

    if max_depth > HIERARCHY_DEPTH_MAX:
        issues.append(
            "HIERARCHY_DEPTH: Territory hierarchy depth is {} levels "
            "(deepest: '{}'). Depths above {} significantly increase forecast rollup "
            "complexity and admin overhead. Target 3-5 levels. Review whether intermediate "
            "levels have real forecast consumers.".format(max_depth, deepest_territory, HIERARCHY_DEPTH_MAX)
        )
    elif max_depth > HIERARCHY_DEPTH_WARNING:
        issues.append(
            "HIERARCHY_DEPTH_WARNING: Territory hierarchy depth is {} levels "
            "(deepest: '{}'). Best practice is 3-5 levels. Verify each level corresponds "
            "to a real forecast consumer in the management structure.".format(max_depth, deepest_territory)
        )
    return issues


def check_unassigned_territory_strategy(manifest_dir: Path) -> list:
    issues = []
    territory_files = find_xml_files(manifest_dir, ".territory2-meta.xml")
    if not territory_files:
        return issues

    territory_names = [tf.stem.lower() for tf in territory_files]
    catchall_keywords = ["unassigned", "catch", "default", "other", "global", "worldwide"]

    has_catchall = any(
        any(keyword in name for keyword in catchall_keywords)
        for name in territory_names
    )

    if not has_catchall:
        issues.append(
            "MISSING_CATCHALL: No territory with a name suggesting catch-all coverage was found "
            "(searched for: unassigned, catch, default, other, global, worldwide). "
            "Accounts not matching any assignment rule will be unassigned and will not appear "
            "in any territory forecast. Define a catch-all territory or document the unassigned "
            "account strategy explicitly."
        )
    return issues


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def check_territory_design_requirements(manifest_dir: Path) -> list:
    issues = []
    if not manifest_dir.exists():
        issues.append("Manifest directory not found: {}".format(manifest_dir))
        return issues
    issues.extend(check_territory_count(manifest_dir))
    issues.extend(check_assignment_rule_criteria_count(manifest_dir))
    issues.extend(check_date_field_criteria(manifest_dir))
    issues.extend(check_territory_type_priority(manifest_dir))
    issues.extend(check_territory_hierarchy_depth(manifest_dir))
    issues.extend(check_unassigned_territory_strategy(manifest_dir))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_territory_design_requirements(manifest_dir)

    if not issues:
        print("No territory design issues found.")
        return 0

    for issue in issues:
        print("ISSUE: " + issue)

    print("\n{} issue(s) found.".format(len(issues)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
