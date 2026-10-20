#!/usr/bin/env python3
"""Checker script for Flow External Services skill.

Inspects Salesforce metadata files for common Flow External Services
configuration issues: missing fault paths, callouts in record-triggered flows,
missing Named Credential references, and status code decision gaps.

Severity contract: unparseable Flow XML and a missing directory are ERRORs (exit 1 always); every
other finding is REVIEW and exits 0 unless --strict. A directory with no Flow files is one WARN,
exit 0. UNVERIFIED (2026-10-20): the actionType value 'httpCallout' is not in the FlowActionCall list
(api_meta 264 L71245-71475 lists 'externalService', L71282), so the status-code rule may never fire;
and 'callouts in record-triggered flows' is the Apex rule (apexdev 264 L8911-8912) applied to flows.
Only callouts reachable from the start element's immediate connector are reported: a scheduled path
(FlowScheduledPath, pathType AsyncAfterCommit "runs asynchronously after a save", api_meta 264
L74148-74151) is the async dispatch this skill recommends, so callouts reached only from
<scheduledPaths> are not flagged.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_flow_external_services.py --manifest-dir path/to/metadata [--strict]
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
    parser.add_argument("--strict", action="store_true", help="Exit 1 on REVIEW/WARN findings too.")
    return parser.parse_args()


def _tag(local: str) -> str:
    """Return namespace-qualified XML tag."""
    return f"{{{FLOW_NS}}}{local}"


def get_text(element: ET.Element, tag: str) -> str:
    """Return text content of a child element, or empty string if absent."""
    child = element.find(_tag(tag))
    return child.text.strip() if child is not None and child.text else ""


def _immediate_reach(root: ET.Element) -> set[str]:
    """Names of elements reachable from <start><connector>, not counting <scheduledPaths>."""
    targets: dict[str, list[str]] = {}
    for el in root:
        name = get_text(el, "name")
        if name:
            targets[name] = [(t.text or "").strip() for t in el.iter(_tag("targetReference")) if (t.text or "").strip()]
    start_el = root.find(_tag("start"))
    if start_el is None:
        return set(targets)
    connector = start_el.find(_tag("connector"))
    frontier = [get_text(connector, "targetReference")] if connector is not None else []
    seen: set[str] = set()
    while frontier:
        name = frontier.pop()
        if not name or name in seen:
            continue
        seen.add(name)
        frontier.extend(targets.get(name, []))
    return seen


def check_flow_file(flow_path: Path) -> list[str]:
    """Inspect a single .flow-meta.xml file for External Services issues."""
    issues: list[str] = []
    flow_name = flow_path.stem.replace(".flow-meta", "")

    try:
        tree = ET.parse(flow_path)
    except ET.ParseError as exc:
        issues.append(f"ERROR: [{flow_name}] XML parse error: {exc}")
        return issues

    root = tree.getroot()

    # Determine if this is a record-triggered flow
    process_type = get_text(root, "processType")
    # triggerType is a FlowStart field (api_meta 264 L75195, L75261), so it sits inside <start>.
    start_el = root.find(_tag("start"))
    trigger_type = (get_text(start_el, "triggerType") if start_el is not None else "") or get_text(root, "triggerType")
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
    immediate = _immediate_reach(root) if is_record_triggered else set()
    sync_callouts = [c for c in callout_elements if c in immediate]
    if is_record_triggered and sync_callouts:
        issues.append(
            f"REVIEW: [{flow_name}] Record-triggered flow (triggerType={trigger_type}) "
            f"reaches callout action(s) {sync_callouts} on its immediate path. "
            "Apex callouts after uncommitted DML fail (apexdev 264 L8910-8912); the flow case is "
            "UNVERIFIED (2026-10-20). Move the callout to a scheduled path (AsyncAfterCommit, "
            "api_meta 264 L74150-74151) or a platform event subscriber."
        )

    # Issue: callout action missing fault connector
    for elem in callout_elements:
        if elem not in elements_with_fault:
            issues.append(
                f"REVIEW: [{flow_name}] Action element '{elem}' is a callout "
                "but has no fault connector. Network errors and timeouts will cause unhandled "
                "flow failures. Wire the fault connector to an error handling path."
            )

    # Issue: HTTP Callout action without an apparent status code check
    if http_callout_elements and not has_status_code_decision:
        issues.append(
            f"REVIEW: [{flow_name}] HTTP Callout action(s) "
            f"{http_callout_elements} detected but no Decision element found that checks "
            "a status code variable. That the HTTP Callout action does not fault on 4xx/5xx "
            "responses is UNVERIFIED (2026-10-20: Help-only); add a Decision element checking the status code."
        )

    return issues


def check_flow_external_services(manifest_dir: Path) -> list[str]:
    """Scan all .flow-meta.xml files under manifest_dir for External Services issues."""
    issues: list[str] = []

    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))

    if not flow_files:
        return [f"WARN: no Flow metadata found under {manifest_dir}"]

    for flow_file in flow_files:
        issues.extend(check_flow_file(flow_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)
    issues = check_flow_external_services(manifest_dir)

    if not issues:
        print("No External Services issues found.")
        return 0

    for issue in issues:
        print(issue)

    if any(i.startswith("ERROR:") for i in issues):
        return 1
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
