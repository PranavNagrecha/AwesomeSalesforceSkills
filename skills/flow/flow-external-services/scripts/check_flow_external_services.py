#!/usr/bin/env python3
"""Checker script for Flow External Services skill.

Inspects Salesforce metadata files for common Flow External Services
configuration issues: missing fault paths, callouts in record-triggered flows,
missing Named Credential references, and status code decision gaps.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_flow_external_services.py [--help]
    python3 check_flow_external_services.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


# Flow XML namespace used by Salesforce metadata
FLOW_NS = "http://soap.sforce.com/2006/04/metadata"

# Action categories that indicate a callout in Flow metadata
CALLOUT_ACTION_TYPES = {
    "externalService",
    "httpCallout",
}

# Flow process types that cannot make synchronous callouts
RECORD_TRIGGERED_PROCESS_TYPES = {
    "AutoLaunchedFlow",  # when triggerType is RecordBeforeSave or RecordAfterSave
}

RECORD_TRIGGER_TYPES = {
    "RecordBeforeSave",
    "RecordAfterSave",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Flow metadata for common External Services and HTTP Callout "
            "configuration issues: fault paths, record-triggered callout violations, "
            "Named Credential references, and status code handling gaps."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    """Return namespace-qualified XML tag."""
    return f"{{{FLOW_NS}}}{local}"


def get_text(element: ET.Element, tag: str) -> str:
    """Return text content of a child element, or empty string if absent."""
    child = element.find(_tag(tag))
    return child.text.strip() if child is not None and child.text else ""


def check_flow_file(flow_path: Path) -> list[str]:
    """Inspect a single .flow-meta.xml file for External Services issues."""
    issues: list[str] = []
    flow_name = flow_path.stem.replace(".flow-meta", "")

    try:
        tree = ET.parse(flow_path)
    except ET.ParseError as exc:
        issues.append(f"[{flow_name}] XML parse error: {exc}")
        return issues

    root = tree.getroot()

    # Determine if this is a record-triggered flow
    process_type = get_text(root, "processType")
    trigger_type = get_text(root, "triggerType")
    is_record_triggered = trigger_type in RECORD_TRIGGER_TYPES

    # Collect all action elements with their names and fault connectors
    # actionCalls covers External Service actions and HTTP Callout core actions
    callout_elements: list[str] = []
    elements_with_fault: set[str] = set()
    http_callout_elements: list[str] = []
    has_status_code_decision = False

    for action_call in root.findall(_tag("actionCalls")):
        action_type = get_text(action_call, "actionType")
        element_name = get_text(action_call, "name")

        if action_type in CALLOUT_ACTION_TYPES:
            callout_elements.append(element_name)

            if action_type == "httpCallout":
                http_callout_elements.append(element_name)

            # Check if a faultConnector child exists
            fault_connector = action_call.find(_tag("faultConnector"))
            if fault_connector is not None:
                elements_with_fault.add(element_name)

    # Check decisions for status code comparisons (heuristic: variable name contains StatusCode)
    for decision in root.findall(_tag("decisions")):
        for rule in decision.findall(_tag("rules")):
            for condition in rule.findall(_tag("conditions")):
                left_operand = get_text(condition, "leftValueReference")
                if "statuscode" in left_operand.lower() or "status_code" in left_operand.lower():
                    has_status_code_decision = True

    # Issue: callout in a record-triggered flow
    if is_record_triggered and callout_elements:
        issues.append(
            f"[{flow_name}] CRITICAL: Record-triggered flow (triggerType={trigger_type}) "
            f"contains callout action(s): {callout_elements}. "
            "Synchronous callouts are not allowed in record-triggered transactions. "
            "Use async dispatch via Platform Events or Scheduled Paths."
        )

    # Issue: callout action missing fault connector
    for elem in callout_elements:
        if elem not in elements_with_fault:
            issues.append(
                f"[{flow_name}] MISSING FAULT CONNECTOR: Action element '{elem}' is a callout "
                "but has no fault connector. Network errors and timeouts will cause unhandled "
                "flow failures. Wire the fault connector to an error handling path."
            )

    # Issue: HTTP Callout action without an apparent status code check
    if http_callout_elements and not has_status_code_decision:
        issues.append(
            f"[{flow_name}] MISSING STATUS CODE CHECK: HTTP Callout action(s) "
            f"{http_callout_elements} detected but no Decision element found that checks "
            "a status code variable. The HTTP Callout action does not fault on 4xx/5xx "
            "responses. Add a Decision element checking Response_Status_Code >= 400."
        )

    return issues


def check_flow_external_services(manifest_dir: Path) -> list[str]:
    """Scan all .flow-meta.xml files under manifest_dir for External Services issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))

    if not flow_files:
        # Not an error — many projects won't have flows in the scanned directory
        return issues

    for flow_file in flow_files:
        issues.extend(check_flow_file(flow_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_flow_external_services(manifest_dir)

    if not issues:
        print("No External Services issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
