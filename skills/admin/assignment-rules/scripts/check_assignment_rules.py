#!/usr/bin/env python3
"""Checker script for Assignment Rules skill.

Inspects Salesforce metadata in SFDX source format or retrieved XML to detect
common assignment rule anti-patterns documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_assignment_rules.py [--manifest-dir path/to/metadata]

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Assignment Rules metadata for common anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce project or retrieved metadata (default: current directory).",
    )
    return parser.parse_args()


def find_assignment_rule_files(root: Path) -> list[Path]:
    """Return all .assignmentRules-meta.xml files under root."""
    results = list(root.rglob("*.assignmentRules-meta.xml"))
    # Also handle retrieved metadata layout (assignmentRules/ folder)
    for candidate in root.rglob("*.assignmentRules"):
        if candidate.is_file():
            results.append(candidate)
    return results


SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def check_rule_file(path: Path) -> list[str]:
    """Parse one assignment rule metadata file and return issues."""
    issues: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"{path.name}: XML parse error — {exc}"]

    root = tree.getroot()
    # Handle both namespaced and bare XML
    rules = root.findall(_tag("assignmentRule")) or root.findall("assignmentRule")

    active_rules: list[str] = []
    for rule in rules:
        name_el = rule.find(_tag("fullName")) or rule.find("fullName")
        active_el = rule.find(_tag("active")) or rule.find("active")
        rule_name = name_el.text if name_el is not None else "<unnamed>"
        is_active = (active_el is not None and active_el.text == "true")

        if is_active:
            active_rules.append(rule_name)

        entries = rule.findall(_tag("ruleEntry")) or rule.findall("ruleEntry")

        if is_active and not entries:
            issues.append(
                f"{path.name} / rule '{rule_name}': active rule has no rule entries — "
                "no records will be routed."
            )
            continue

        # Check for a catch-all entry (entry with no criteriaItems)
        has_catch_all = False
        for entry in entries:
            criteria_items = (
                entry.findall(_tag("criteriaItems")) or entry.findall("criteriaItems")
            )
            criteria_filter = entry.find(_tag("criteriaFilterType")) or entry.find("criteriaFilterType")
            is_catch_all = (
                len(criteria_items) == 0
                and (criteria_filter is None or criteria_filter.text in (None, "", "AllCriteriaTrue"))
            )
            if is_catch_all:
                has_catch_all = True

        if is_active and not has_catch_all:
            issues.append(
                f"{path.name} / rule '{rule_name}': no catch-all entry found — "
                "records that match no criteria will not be routed by this rule "
                "(they go to the Default Lead/Case Owner). "
                "Add a final entry with no criteria to make the fallback explicit."
            )

        # Warn if entry count is approaching the 3,000-entry limit
        if len(entries) > 2500:
            issues.append(
                f"{path.name} / rule '{rule_name}': {len(entries)} rule entries — "
                "approaching the 3,000-entry platform limit. Consider consolidating criteria."
            )

        # Check for entries that assign to the same target consecutively
        # (usually means a duplicate or copy-paste error)
        targets = []
        for entry in entries:
            assigned_to = entry.find(_tag("assignedTo")) or entry.find("assignedTo")
            targets.append(assigned_to.text if assigned_to is not None else None)

        seen: set[str | None] = set()
        for t in targets:
            if t and t in seen:
                issues.append(
                    f"{path.name} / rule '{rule_name}': target '{t}' appears in "
                    "multiple rule entries. Verify this is intentional and not a "
                    "copy-paste error."
                )
                break  # Report once per rule to avoid noise
            if t:
                seen.add(t)

    # Multiple active rules for same object would violate the one-active-rule limit,
    # but metadata typically stores only one rule per file. Flag if multiple active found.
    if len(active_rules) > 1:
        issues.append(
            f"{path.name}: multiple rules marked active: {active_rules}. "
            "Salesforce enforces only one active rule per object. "
            "Review metadata before deploying — deployment may succeed but behavior will be unpredictable."
        )

    return issues


def check_assignment_rules(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    rule_files = find_assignment_rule_files(manifest_dir)

    if not rule_files:
        # Not an error — the project may not have assignment rules deployed
        print(f"INFO: No assignment rule metadata files found under {manifest_dir}.")
        return []

    for rule_file in rule_files:
        issues.extend(check_rule_file(rule_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_assignment_rules(manifest_dir)

    if not issues:
        print("No assignment rule issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
