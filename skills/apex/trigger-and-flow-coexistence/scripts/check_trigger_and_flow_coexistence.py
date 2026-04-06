#!/usr/bin/env python3
"""Checker script for Trigger And Flow Coexistence skill.

Scans a Salesforce metadata directory for objects that have both Apex triggers
and record-triggered Flows, then flags potential coexistence risks:
  - Same object with both trigger and Flow at the same timing
  - After-save Flows that perform DML (recursion risk)
  - Legacy automation (workflow rules, process builder) alongside triggers/Flows

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_trigger_and_flow_coexistence.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check for trigger-and-flow coexistence risks in Salesforce metadata.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_triggers(manifest_dir: Path) -> dict[str, list[str]]:
    """Return a dict mapping sObject name -> list of trigger file paths."""
    triggers: dict[str, list[str]] = {}
    triggers_dir = manifest_dir / "triggers"
    if not triggers_dir.exists():
        # Also check force-app structure
        triggers_dir = manifest_dir / "force-app" / "main" / "default" / "triggers"
    if not triggers_dir.exists():
        return triggers

    for trig_file in triggers_dir.glob("*.trigger-meta.xml"):
        try:
            tree = ET.parse(trig_file)
            root = tree.getroot()
            # Remove namespace prefix if present
            ns = ""
            match = re.match(r"\{(.+)\}", root.tag)
            if match:
                ns = f"{{{match.group(1)}}}"
            sobject_el = root.find(f"{ns}sObject") if ns else root.find("sObject")
            if sobject_el is not None and sobject_el.text:
                obj_name = sobject_el.text
                triggers.setdefault(obj_name, []).append(str(trig_file))
        except ET.ParseError:
            continue

    # Also check .trigger files for sObject via content parsing
    for trig_file in triggers_dir.glob("*.trigger"):
        try:
            content = trig_file.read_text(encoding="utf-8", errors="ignore")
            # Pattern: trigger TriggerName on ObjectName (events)
            m = re.search(r"trigger\s+\w+\s+on\s+(\w+)", content)
            if m:
                obj_name = m.group(1)
                triggers.setdefault(obj_name, []).append(str(trig_file))
        except OSError:
            continue

    return triggers


def find_record_triggered_flows(manifest_dir: Path) -> dict[str, list[dict[str, str]]]:
    """Return a dict mapping sObject name -> list of flow info dicts.

    Each dict has keys: name, path, trigger_type (RecordBeforeSave, RecordAfterSave, etc.), has_dml.
    """
    flows: dict[str, list[dict[str, str]]] = {}
    flow_dirs = [
        manifest_dir / "flows",
        manifest_dir / "force-app" / "main" / "default" / "flows",
    ]

    for flow_dir in flow_dirs:
        if not flow_dir.exists():
            continue
        for flow_file in flow_dir.glob("*.flow-meta.xml"):
            try:
                tree = ET.parse(flow_file)
                root = tree.getroot()
                ns = ""
                match = re.match(r"\{(.+)\}", root.tag)
                if match:
                    ns = f"{{{match.group(1)}}}"

                # Check if it's a record-triggered flow
                process_type_el = root.find(f"{ns}processType") if ns else root.find("processType")
                if process_type_el is None or process_type_el.text != "AutoLaunchedFlow":
                    # Also check for the start element with triggerType
                    pass

                start_el = root.find(f"{ns}start") if ns else root.find("start")
                if start_el is None:
                    continue

                trigger_type_el = start_el.find(f"{ns}triggerType") if ns else start_el.find("triggerType")
                if trigger_type_el is None or trigger_type_el.text not in (
                    "RecordBeforeSave",
                    "RecordAfterSave",
                    "RecordBeforeDelete",
                ):
                    continue

                object_el = start_el.find(f"{ns}object") if ns else start_el.find("object")
                if object_el is None or not object_el.text:
                    continue

                obj_name = object_el.text
                trigger_type = trigger_type_el.text

                # Check for DML elements (recordCreates, recordUpdates, recordDeletes)
                content = flow_file.read_text(encoding="utf-8", errors="ignore")
                has_dml = any(
                    tag in content
                    for tag in ["<recordCreates>", "<recordUpdates>", "<recordDeletes>"]
                )

                flow_info = {
                    "name": flow_file.stem.replace(".flow-meta", ""),
                    "path": str(flow_file),
                    "trigger_type": trigger_type,
                    "has_dml": str(has_dml),
                }
                flows.setdefault(obj_name, []).append(flow_info)

            except ET.ParseError:
                continue

    return flows


def find_workflow_rules(manifest_dir: Path) -> dict[str, list[str]]:
    """Return a dict mapping sObject name -> list of workflow file paths."""
    workflows: dict[str, list[str]] = {}
    wf_dirs = [
        manifest_dir / "workflows",
        manifest_dir / "force-app" / "main" / "default" / "workflows",
    ]

    for wf_dir in wf_dirs:
        if not wf_dir.exists():
            continue
        for wf_file in wf_dir.glob("*.workflow-meta.xml"):
            # Object name is typically the file name
            obj_name = wf_file.stem.replace(".workflow-meta", "")
            try:
                content = wf_file.read_text(encoding="utf-8", errors="ignore")
                # Only flag if there are actual rules with field updates
                if "<fieldUpdates>" in content or "<rules>" in content:
                    workflows.setdefault(obj_name, []).append(str(wf_file))
            except OSError:
                continue

    return workflows


def check_trigger_and_flow_coexistence(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    triggers = find_triggers(manifest_dir)
    flows = find_record_triggered_flows(manifest_dir)
    workflows = find_workflow_rules(manifest_dir)

    if not triggers and not flows:
        issues.append(
            "INFO: No triggers or record-triggered Flows found in metadata directory. "
            "Ensure the --manifest-dir points to the correct metadata root."
        )
        return issues

    # Find objects with both triggers and flows
    coexistence_objects = set(triggers.keys()) & set(flows.keys())

    for obj in sorted(coexistence_objects):
        obj_triggers = triggers[obj]
        obj_flows = flows[obj]

        issues.append(
            f"COEXISTENCE: {obj} has {len(obj_triggers)} trigger(s) and "
            f"{len(obj_flows)} record-triggered Flow(s). "
            f"Review field ownership to prevent silent overwrites."
        )

        # Check for before-save timing overlap
        before_flows = [f for f in obj_flows if f["trigger_type"] == "RecordBeforeSave"]
        if before_flows:
            flow_names = ", ".join(f["name"] for f in before_flows)
            issues.append(
                f"FIELD-CONFLICT-RISK: {obj} has before trigger(s) AND before-save Flow(s) "
                f"({flow_names}). Both run at step 3 with no guaranteed order. "
                f"Verify they write to disjoint field sets."
            )

        # Check for after-save flows with DML (recursion risk)
        after_flows_with_dml = [
            f for f in obj_flows
            if f["trigger_type"] == "RecordAfterSave" and f["has_dml"] == "True"
        ]
        if after_flows_with_dml:
            flow_names = ", ".join(f["name"] for f in after_flows_with_dml)
            issues.append(
                f"RECURSION-RISK: {obj} has after-save Flow(s) with DML ({flow_names}) "
                f"alongside trigger(s). DML in the Flow will re-enter the save cycle "
                f"and re-fire triggers. Ensure cross-automation recursion guards are in place."
            )

    # Check for objects with triggers/flows AND workflow rules (triple coexistence)
    for obj in sorted(set(workflows.keys()) & (set(triggers.keys()) | set(flows.keys()))):
        automation_types = []
        if obj in triggers:
            automation_types.append("triggers")
        if obj in flows:
            automation_types.append("Flows")
        automation_types.append("workflow rules")
        issues.append(
            f"LEGACY-COEXISTENCE: {obj} has {', '.join(automation_types)}. "
            f"Workflow rules with field updates re-fire triggers but not before-save Flows. "
            f"Plan migration of workflow rules to reduce automation complexity."
        )

    # Report objects with only triggers or only flows (no coexistence issue)
    trigger_only = set(triggers.keys()) - set(flows.keys())
    flow_only = set(flows.keys()) - set(triggers.keys())

    if trigger_only:
        issues.append(
            f"INFO: {len(trigger_only)} object(s) have triggers only (no coexistence risk): "
            f"{', '.join(sorted(trigger_only))}"
        )
    if flow_only:
        issues.append(
            f"INFO: {len(flow_only)} object(s) have record-triggered Flows only (no coexistence risk): "
            f"{', '.join(sorted(flow_only))}"
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_trigger_and_flow_coexistence(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    exit_code = 0
    for issue in issues:
        print(f"ISSUE: {issue}")
        if not issue.startswith("INFO:"):
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
