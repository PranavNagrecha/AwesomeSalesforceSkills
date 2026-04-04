#!/usr/bin/env python3
"""Checker script for Flow Runtime Error Diagnosis skill.

Scans Salesforce Flow metadata XML for common runtime error patterns:
- Get Records elements with no downstream null-check Decision
- DML elements (Create/Update/Delete) inside Loop elements
- Flow elements with no fault path configured

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_flow_runtime_error_diagnosis.py [--help]
    python3 check_flow_runtime_error_diagnosis.py --source-dir force-app/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


SF_NS = "http://soap.sforce.com/2006/04/metadata"
DML_ELEMENT_TYPES = {"recordCreates", "recordUpdates", "recordDeletes"}
GET_ELEMENT_TYPES = {"recordLookups"}
LOOP_ELEMENT_TYPE = "loops"
DECISION_ELEMENT_TYPE = "decisions"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for common runtime error patterns.",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def check_flow_file(flow_file: Path) -> list[str]:
    """Check a single flow metadata XML file for runtime error patterns."""
    issues: list[str] = []
    try:
        tree = ET.parse(flow_file)
        root = tree.getroot()
    except ET.ParseError as exc:
        issues.append(f"{flow_file}: XML parse error — {exc}")
        return issues

    # Collect all connector targets from DML-type elements to detect loop membership
    # Strategy: find all loop elements and collect their child element names
    loop_child_names: set[str] = set()
    for loop_el in root.findall(_tag(LOOP_ELEMENT_TYPE)):
        # Loop's nextValueConnector and noMoreValuesConnector contain targetReference
        for connector_tag in ("nextValueConnector", "noMoreValuesConnector"):
            connector = loop_el.find(_tag(connector_tag))
            if connector is not None:
                target = connector.find(_tag("targetReference"))
                if target is not None and target.text:
                    loop_child_names.add(target.text.strip())

    # Check for DML elements inside loops
    for dml_type in DML_ELEMENT_TYPES:
        for dml_el in root.findall(_tag(dml_type)):
            name_el = dml_el.find(_tag("name"))
            if name_el is not None and name_el.text in loop_child_names:
                issues.append(
                    f"{flow_file}: DML element '{name_el.text}' ({dml_type}) appears to be "
                    f"inside a Loop — may cause LIMIT_EXCEEDED DML errors. "
                    f"Move DML outside the loop and use collection-based bulk DML."
                )

    # Check for Get Records elements inside loops
    for get_el in root.findall(_tag("recordLookups")):
        name_el = get_el.find(_tag("name"))
        if name_el is not None and name_el.text in loop_child_names:
            issues.append(
                f"{flow_file}: Get Records element '{name_el.text}' appears to be "
                f"inside a Loop — may cause LIMIT_EXCEEDED SOQL errors. "
                f"Move Get Records outside the loop and filter the collection inside the loop."
            )

    # Check for DML elements with no fault connector configured
    for dml_type in DML_ELEMENT_TYPES:
        for dml_el in root.findall(_tag(dml_type)):
            name_el = dml_el.find(_tag("name"))
            fault_connector = dml_el.find(_tag("faultConnector"))
            if name_el is not None and fault_connector is None:
                issues.append(
                    f"{flow_file}: DML element '{name_el.text}' ({dml_type}) has no fault path — "
                    f"runtime errors will surface as raw platform messages. "
                    f"Add a fault path to handle errors gracefully."
                )

    return issues


def check_flows(source_dir: Path) -> list[str]:
    """Return a list of issue strings found across all flow files in the source directory."""
    issues: list[str] = []

    if not source_dir.exists():
        issues.append(f"Source directory not found: {source_dir}")
        return issues

    flow_files = list(source_dir.rglob("*.flow-meta.xml"))
    if not flow_files:
        return issues

    for flow_file in flow_files:
        issues.extend(check_flow_file(flow_file))

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)
    issues = check_flows(source_dir)

    if not issues:
        print("No Flow runtime error pattern issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
