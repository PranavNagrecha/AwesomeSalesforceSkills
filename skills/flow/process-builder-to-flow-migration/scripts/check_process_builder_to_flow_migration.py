#!/usr/bin/env python3
"""Checker script for Process Builder to Flow Migration skill.

Scans Salesforce metadata directory for Process Builder migration anti-patterns:
- Active Process Builder processes that coexist with active record-triggered flows on same object
- Flow-meta.xml files with DML elements that have no fault path connectors
- Process Builder .flow-meta.xml files with ISCHANGED/ISNEW criteria (cannot use migration tool)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_process_builder_to_flow_migration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce metadata for Process Builder to Flow migration issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_flow_files(manifest_dir: Path) -> list[Path]:
    """Find all .flow-meta.xml files under the manifest directory."""
    return list(manifest_dir.rglob("*.flow-meta.xml"))


def check_active_pb_and_flow_on_same_object(flow_files: list[Path]) -> list[str]:
    """Detect objects that have both an active Process Builder process and an active Flow."""
    issues: list[str] = []
    ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}

    # Track by (object, flow_type)
    object_pb: dict[str, list[str]] = defaultdict(list)
    object_rtf: dict[str, list[str]] = defaultdict(list)

    for path in flow_files:
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError:
            continue

        # Get processType: Flow (PB), AutoLaunchedFlow, RecordTriggeredFlow
        proc_type_el = root.find("sf:processType", ns) or root.find("processType")
        proc_type = proc_type_el.text if proc_type_el is not None else ""

        # Get status
        status_el = root.find("sf:status", ns) or root.find("status")
        status = status_el.text if status_el is not None else ""

        if status != "Active":
            continue

        # Get triggerType / start element object
        start_el = root.find(".//sf:start", ns) or root.find(".//start")
        if start_el is None:
            continue
        obj_el = start_el.find("sf:object", ns) or start_el.find("object")
        obj_name = obj_el.text if obj_el is not None else ""

        if proc_type == "Flow":  # Process Builder
            object_pb[obj_name].append(path.name)
        elif proc_type in ("RecordTriggeredFlow", "AutoLaunchedFlow"):
            object_rtf[obj_name].append(path.name)

    for obj in object_pb:
        if obj in object_rtf:
            issues.append(
                f"OBJECT '{obj}' has both active Process Builder processes {object_pb[obj]} "
                f"and active record-triggered flows {object_rtf[obj]}. "
                "Deactivate Process Builder processes after activating replacement flows to avoid undefined execution order."
            )

    return issues


def check_flows_missing_fault_paths(flow_files: list[Path]) -> list[str]:
    """Find record-triggered flows with DML elements that have no fault connector."""
    issues: list[str] = []
    ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
    dml_element_types = {"recordUpdates", "recordCreates", "recordDeletes"}

    for path in flow_files:
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError:
            continue

        proc_type_el = root.find("sf:processType", ns) or root.find("processType")
        proc_type = proc_type_el.text if proc_type_el is not None else ""
        if proc_type not in ("RecordTriggeredFlow", "AutoLaunchedFlow"):
            continue

        status_el = root.find("sf:status", ns) or root.find("status")
        status = status_el.text if status_el is not None else ""
        if status != "Active":
            continue

        for dml_type in dml_element_types:
            for dml_el in root.findall(f".//sf:{dml_type}", ns) or root.findall(f".//{dml_type}"):
                # Check if faultConnector exists as a child
                fc = dml_el.find("sf:faultConnector", ns) or dml_el.find("faultConnector")
                if fc is None:
                    name_el = dml_el.find("sf:name", ns) or dml_el.find("name")
                    name = name_el.text if name_el is not None else "(unnamed)"
                    issues.append(
                        f"Flow '{path.name}': DML element '{name}' ({dml_type}) has no fault connector. "
                        "Add a Fault Path to handle DML errors and prevent unhandled exceptions."
                    )

    return issues


def check_pb_ischanged_criteria(flow_files: list[Path]) -> list[str]:
    """Find Process Builder flows using ISCHANGED or ISNEW in criteria (not tool-migratable)."""
    issues: list[str] = []

    for path in flow_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only check .flow-meta.xml that look like Process Builder (processType=Flow)
        if "processType>Flow<" not in content and "<processType>Flow</processType>" not in content:
            continue

        if "ISCHANGED" in content.upper() or "ISNEW" in content.upper():
            issues.append(
                f"Process Builder flow '{path.name}' uses ISCHANGED() or ISNEW() criteria. "
                "The Migrate to Flow tool cannot convert these — manual rebuild using "
                "{!$Record__Prior.FieldName} comparisons is required."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    flow_files = _find_flow_files(manifest_dir)

    if not flow_files:
        print("No .flow-meta.xml files found. Pass --manifest-dir pointing to your SFDX source directory.")
        return 0

    all_issues: list[str] = []
    all_issues.extend(check_active_pb_and_flow_on_same_object(flow_files))
    all_issues.extend(check_flows_missing_fault_paths(flow_files))
    all_issues.extend(check_pb_ischanged_criteria(flow_files))

    if not all_issues:
        print(f"No migration issues found in {len(flow_files)} flow file(s).")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
