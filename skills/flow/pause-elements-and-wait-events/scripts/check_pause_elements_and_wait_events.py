#!/usr/bin/env python3
"""Checker script for Pause Elements and Wait Events skill.

Scans Salesforce flow metadata XML files under a manifest directory and
reports issues related to Pause (Wait) element configuration:

  - Platform Event wait events with no resume conditions (stray-event risk)
  - Pause elements with no fault connector (silent failure risk)
  - Platform Event wait events with no companion Alarm timeout watchdog
  - Flows using a Pause element that are of type RecordTriggered (likely should use scheduled path)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_pause_elements_and_wait_events.py [--help]
    python3 check_pause_elements_and_wait_events.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce Flow metadata XML namespace
_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    return f"{{{_NS}}}{local}"


def _find_all(root: ET.Element, path_parts: list[str]) -> list[ET.Element]:
    """Walk a path of tag names under root and return all matching leaf elements."""
    results: list[ET.Element] = [root]
    for part in path_parts:
        next_results: list[ET.Element] = []
        for el in results:
            next_results.extend(el.findall(_tag(part)))
        results = next_results
    return results


def _text(el: ET.Element | None, tag: str) -> str:
    if el is None:
        return ""
    child = el.find(_tag(tag))
    return (child.text or "").strip() if child is not None else ""


def check_flow_file(flow_path: Path) -> list[str]:
    """Parse a single .flow-meta.xml file and return a list of issue strings."""
    issues: list[str] = []

    try:
        tree = ET.parse(flow_path)
    except ET.ParseError as exc:
        issues.append(f"{flow_path.name}: XML parse error — {exc}")
        return issues

    root = tree.getroot()

    # Determine flow type (processType element)
    process_type_el = root.find(_tag("processType"))
    process_type = (process_type_el.text or "").strip() if process_type_el is not None else ""

    # Collect all wait (Pause) elements
    wait_elements = root.findall(_tag("waits"))

    if not wait_elements:
        # No wait elements — nothing to check
        return issues

    flow_name = flow_path.stem.replace(".flow-meta", "")

    # Check 1: Pause element in a RecordTriggered flow (scheduled path is usually correct)
    if process_type == "AutoLaunchedFlow":
        # RecordTriggered flows in SFDX are typically processType=AutoLaunchedFlow
        # with a triggerType on the start element
        start_elements = root.findall(_tag("start"))
        for start_el in start_elements:
            trigger_type = _text(start_el, "triggerType")
            if trigger_type in ("RecordBeforeSave", "RecordAfterSave"):
                issues.append(
                    f"{flow_name}: Pause (Wait) element found in a record-triggered flow "
                    f"(triggerType={trigger_type}). Consider using a Scheduled Path on the "
                    f"Start element instead, which does not consume async interview storage."
                )

    for wait_el in wait_elements:
        wait_name = _text(wait_el, "name")
        label = _text(wait_el, "label") or wait_name

        # Collect wait events (waitEvents children)
        wait_events = wait_el.findall(_tag("waitEvents"))

        has_alarm = False
        has_platform_event = False

        for event_el in wait_events:
            event_type = _text(event_el, "eventType")
            event_name = _text(event_el, "name") or event_type

            if event_type == "AlarmEvent":
                has_alarm = True

            if event_type == "PlatformEvent":
                has_platform_event = True

                # Check 2: Platform Event wait event with no resume conditions
                conditions = event_el.findall(_tag("conditions"))
                if not conditions:
                    issues.append(
                        f"{flow_name} > Wait element '{label}' > event '{event_name}': "
                        f"Platform Event wait event has NO resume conditions. Every published "
                        f"message of this event type will attempt to resume this interview. "
                        f"Add at least one field-filter resume condition (e.g., RecordId__c = {{!recordId}})."
                    )

        # Check 3: Platform Event wait event with no Alarm timeout watchdog
        if has_platform_event and not has_alarm:
            issues.append(
                f"{flow_name} > Wait element '{label}': "
                f"Contains a Platform Event wait event but no Alarm wait event as a timeout "
                f"watchdog. If the expected event is never published, this interview will be "
                f"paused indefinitely. Add an Alarm wait event with an appropriate maximum "
                f"wait duration and route its output to an error-handling path."
            )

        # Check 4: Pause element with no fault connector
        # The fault connector is represented as a connector with targetReference under faultConnector
        fault_connector = wait_el.find(_tag("faultConnector"))
        if fault_connector is None:
            issues.append(
                f"{flow_name} > Wait element '{label}': "
                f"No fault connector configured. If the flow faults on resume (e.g., DML error, "
                f"missing required field), the failure will be silent. Connect the fault path to "
                f"an error-handling element."
            )

    return issues


def check_pause_elements_and_wait_events(manifest_dir: Path) -> list[str]:
    """Scan all flow metadata files under manifest_dir and return all issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Find all flow metadata files
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))
    if not flow_files:
        # Also try .flow files (older format or extracted metadata)
        flow_files = list(manifest_dir.rglob("*.flow"))

    if not flow_files:
        # No flow files found — report informational note only
        print(
            f"INFO: No flow metadata files (*.flow-meta.xml) found under {manifest_dir}. "
            "Nothing to check."
        )
        return issues

    for flow_path in sorted(flow_files):
        file_issues = check_flow_file(flow_path)
        issues.extend(file_issues)

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce flow metadata for common Pause (Wait) element issues: "
            "missing resume conditions, missing fault paths, missing timeout watchdogs, "
            "and incorrect flow type usage."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_pause_elements_and_wait_events(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
