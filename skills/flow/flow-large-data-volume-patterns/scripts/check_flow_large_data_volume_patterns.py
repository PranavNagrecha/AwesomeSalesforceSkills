#!/usr/bin/env python3
"""Checker script for Flow Large Data Volume Patterns skill.

Statically reviews Flow metadata (flow-meta.xml) for patterns that explode
query row volume or commonly precede LDV failures. Uses stdlib only.

Usage:
    python3 check_flow_large_data_volume_patterns.py [--help]
    python3 check_flow_large_data_volume_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for large data volume risk patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def text_of(element: ET.Element, child_name: str) -> str:
    for child in element:
        if local_name(child.tag) == child_name and child.text:
            return child.text.strip()
    return ""


def parse_flow(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def has_non_empty_filters(record_lookup: ET.Element) -> bool:
    for child in record_lookup:
        if local_name(child.tag) != "filters":
            continue
        if any(local_name(grand.tag) == "field" for grand in child.iter()):
            return True
    return False


def check_flow_large_data_volume_patterns(manifest_dir: Path) -> list[str]:
    """Return actionable issue strings for LDV-sensitive Flow patterns."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    flow_paths = sorted(manifest_dir.rglob("*.flow-meta.xml"))
    if not flow_paths:
        return issues

    risk_tags = {"recordLookups", "recordCreates", "recordUpdates", "recordDeletes", "actionCalls", "subflows"}

    for flow_path in flow_paths:
        root = parse_flow(flow_path)
        if root is None:
            issues.append(f"{flow_path}: unable to parse flow metadata.")
            continue

        loop_names = {
            text_of(elem, "name")
            for elem in root.iter()
            if local_name(elem.tag) == "loops" and text_of(elem, "name")
        }

        risky_targets: list[str] = []
        for elem in root.iter():
            tag = local_name(elem.tag)
            name = text_of(elem, "name")
            targets = {
                child.text.strip()
                for child in elem.iter()
                if local_name(child.tag) == "targetReference" and child.text
            }
            if tag in risk_tags and name and targets & loop_names:
                risky_targets.append(f"{tag}:{name}")

        if risky_targets:
            issues.append(
                f"{flow_path}: elements wired after a loop ({', '.join(sorted(risky_targets))}) "
                f"may run per iteration — review query row and SOQL volume under bulk loads."
            )

        multi_row_lookups: list[str] = []
        unconstrained_lookups: list[str] = []

        for elem in root.iter():
            if local_name(elem.tag) != "recordLookups":
                continue
            ename = text_of(elem, "name") or "(unnamed lookup)"
            first_only = text_of(elem, "getFirstRecordOnly").lower()
            if first_only == "false":
                multi_row_lookups.append(ename)
                if not has_non_empty_filters(elem):
                    unconstrained_lookups.append(ename)

        if multi_row_lookups:
            issues.append(
                f"{flow_path}: Get Records (recordLookups) configured to return multiple records: "
                f"{', '.join(sorted(multi_row_lookups))}. Confirm filters, sort, and row caps "
                f"keep total returned rows safe at production volume."
            )

        if unconstrained_lookups:
            issues.append(
                f"{flow_path}: Get Records elements have no filters in metadata: "
                f"{', '.join(sorted(unconstrained_lookups))}. "
                f"Verify in Flow Builder — unscoped queries are high risk for LDV."
            )

        lookup_count = sum(1 for e in root.iter() if local_name(e.tag) == "recordLookups")
        if lookup_count >= 8:
            issues.append(
                f"{flow_path}: {lookup_count} Get Records elements — review cumulative "
                f"query row usage across all lookups in the same transaction path."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_flow_large_data_volume_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
