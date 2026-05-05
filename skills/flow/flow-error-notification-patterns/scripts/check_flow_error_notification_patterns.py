#!/usr/bin/env python3
"""Static checks for Flow fault-path / error-notification anti-patterns.

Scans Flow XML metadata files for the high-confidence anti-patterns
documented in this skill:

  1. Element with `<faultConnector>` whose target is a `<screens>`,
     `<recordCreates>`, etc. that doesn't reference `$Flow.FaultMessage`
     and doesn't call any Action / log step — the "do-nothing" Fault
     path that silently succeeds the flow.
  2. Flow with `<recordCreates>`, `<recordUpdates>`, `<recordDeletes>`,
     or `<actionCalls>` element(s) and NO `<faultConnector>` anywhere
     — relies on the org-default exception-email recipient.
  3. Email Action (`<actionCalls actionType="emailSimple">`) reached
     from a `<faultConnector>` — risky inside Fault paths
     (governor pressure, secondary fault has no further fault path).

Stdlib only. Walks `*.flow-meta.xml` files.

Usage:
    python3 check_flow_error_notification_patterns.py --src-root .
    python3 check_flow_error_notification_patterns.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"


def _strip_ns(tag: str) -> str:
    if tag.startswith(_NS_TAG):
        return tag[len(_NS_TAG):]
    return tag


def _scan_flow(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return findings
    root = tree.getroot()
    if _strip_ns(root.tag) != "Flow":
        return findings

    # Build a name -> element map.
    elements_by_name: dict[str, ET.Element] = {}
    for child in root:
        name_el = child.find(f"{_NS_TAG}name")
        if name_el is not None and name_el.text:
            elements_by_name[name_el.text] = child

    fault_capable_tags = {
        "recordCreates", "recordUpdates", "recordDeletes", "recordLookups",
        "actionCalls", "subflows",
    }

    fault_capable_count = 0
    flows_with_fault_connector = 0
    fault_connector_targets: list[tuple[str, str, ET.Element]] = []  # (source_name, target_name, source_element)

    for child in root:
        tag = _strip_ns(child.tag)
        if tag not in fault_capable_tags:
            continue
        fault_capable_count += 1
        fault_conn = child.find(f"{_NS_TAG}faultConnector")
        if fault_conn is None:
            continue
        flows_with_fault_connector += 1
        target_ref = fault_conn.find(f"{_NS_TAG}targetReference")
        if target_ref is None or not target_ref.text:
            continue
        source_name_el = child.find(f"{_NS_TAG}name")
        source_name = source_name_el.text if source_name_el is not None else "<unknown>"
        fault_connector_targets.append((source_name, target_ref.text, child))

    # Smell 2: fault-capable elements but no fault connectors anywhere.
    if fault_capable_count > 0 and flows_with_fault_connector == 0:
        findings.append(
            f"{path}: flow has {fault_capable_count} fault-capable element(s) "
            "(recordCreates / recordUpdates / actionCalls / subflows) but NO "
            "<faultConnector> anywhere — relies on the org-default exception-email "
            "recipient. Add explicit Fault paths "
            "(references/gotchas.md § 2)"
        )

    # Smell 1 + 3: trace each fault target.
    for source_name, target_name, _src_el in fault_connector_targets:
        target = elements_by_name.get(target_name)
        if target is None:
            continue
        target_tag = _strip_ns(target.tag)

        # Smell 1: fault path that does nothing observable.
        # Heuristic: target element has NO further connector AND is not
        # an Action / Subflow / Record-Create that produces visible side
        # effect. End-screens-without-content count as "do nothing".
        target_text_xml = ET.tostring(target, encoding="unicode")
        references_fault_msg = "$Flow.FaultMessage" in target_text_xml or "FaultMessage" in target_text_xml
        is_observable_action = target_tag in {
            "actionCalls",       # invoking an action — likely a logger
            "recordCreates",     # writing a log record
            "subflows",          # likely a Log_Flow_Error sub-flow
        }
        has_outgoing = target.find(f"{_NS_TAG}connector") is not None

        # If the target is a screen, require it to reference FaultMessage OR have visible
        # text fields.
        if target_tag == "screens" and not references_fault_msg:
            findings.append(
                f"{path}: Fault path on `{source_name}` lands on screen `{target_name}` "
                "that does not reference $Flow.FaultMessage — likely showing the user a "
                "blank or generic screen with the actionable message thrown away "
                "(references/gotchas.md § 4)"
            )
        elif not is_observable_action and not has_outgoing and not references_fault_msg:
            findings.append(
                f"{path}: Fault path on `{source_name}` lands on `{target_name}` "
                f"({target_tag}) that has no outgoing connector, no observable action, "
                "and no FaultMessage reference — \"do-nothing\" fault path silently "
                "succeeds the flow "
                "(references/gotchas.md § 1)"
            )

        # Smell 3: Send Email Action reached from a Fault path.
        if target_tag == "actionCalls":
            action_type = target.find(f"{_NS_TAG}actionType")
            if action_type is not None and action_type.text and "email" in action_type.text.lower():
                findings.append(
                    f"{path}: Fault path on `{source_name}` invokes email action "
                    f"`{target_name}` — risky in high-volume flows (governor pressure, "
                    "secondary fault has no further fault path). Publish a Platform "
                    "Event or insert into a custom log object instead "
                    "(references/gotchas.md § 5, § 6)"
                )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []
    for f in root.rglob("*.flow-meta.xml"):
        findings.extend(_scan_flow(f))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Flow XML for fault-path anti-patterns "
            "(do-nothing Fault paths, missing Fault paths, email-action "
            "in fault paths)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the metadata tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Flow fault-path anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
