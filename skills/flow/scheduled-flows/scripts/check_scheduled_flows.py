#!/usr/bin/env python3
"""Check schedule-triggered Flow metadata for common scope and reliability issues.

A flow is schedule-triggered when its ``<start>`` has ``<triggerType>Scheduled``
(api_meta 264 L75270). Rules:

  ERROR  Scheduled start without a ``<schedule>`` (required when triggerType is
         Scheduled, api_meta 264 L75199-75200), or flow XML that does not parse.
  WARN   ``schedule/frequency`` other than Once, Daily or Weekly: Hourly,
         Monthly, Weekdays, Yearly and OnActivate are listed "for
         segment-triggered flows only" (api_meta 264 L74076-74096).
  WARN   Object selected but no filters, filterLogic or filterFormula: the job
         scans every record of the object.
  WARN   Loops plus three or more data/action elements (review for Batch Apex).
  WARN   DML or action element without a fault connector (subflows are
         exempt: FlowSubflow has no faultConnector, api_meta 264 L75363-75397).

Exit codes: ERROR findings exit 1 always; WARN findings exit 0 unless
``--strict``; a directory with no scheduled flows prints one WARN and exits 0;
a missing directory is an ERROR and exits 1. Stdlib only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

# Elements that carry a faultConnector. FlowSubflow has no faultConnector field
# (api_meta 264 L75363-75397), so subflows count toward volume only.
DML_ACTION_TAGS = {"recordCreates", "recordUpdates", "recordDeletes", "actionCalls"}
RISKY_TAGS = DML_ACTION_TAGS | {"recordLookups", "subflows"}
NON_SEGMENT_FREQUENCIES = {"Once", "Daily", "Weekly"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check scheduled flows for broad scope, weak fault handling, and batch-style design smells.",
    )
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata (default: .).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def children(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in element if local_name(c.tag) == name]


def child_text(element: ET.Element, name: str) -> str:
    for child in children(element, name):
        if child.text:
            return child.text.strip()
    return ""


def check_flow(path: Path) -> tuple[bool, list[tuple[str, str]]]:
    """Return (is_scheduled, findings)."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return False, [("ERROR", f"{path}: unable to parse flow metadata ({exc})")]
    starts = children(root, "start")
    if not starts or child_text(starts[0], "triggerType") != "Scheduled":
        return False, []
    start = starts[0]
    out: list[tuple[str, str]] = []
    schedules = children(start, "schedule")
    if not schedules:
        out.append(("ERROR", f"{path}: triggerType Scheduled without a <schedule> element"))
    else:
        freq = child_text(schedules[0], "frequency")
        if freq and freq not in NON_SEGMENT_FREQUENCIES:
            out.append(("WARN", f"{path}: schedule frequency '{freq}' is documented for segment-triggered flows only"))
    has_filter = any(children(start, n) for n in ("filters", "filterLogic", "filterFormula"))
    if child_text(start, "object") and not has_filter:
        out.append(("WARN", f"{path}: object-selected scheduled flow has no filters; the record scope may be unbounded"))
    loops = sum(1 for e in root.iter() if local_name(e.tag) == "loops")
    risky = sum(1 for e in root.iter() if local_name(e.tag) in RISKY_TAGS)
    if loops and risky >= 3:
        out.append(("WARN", f"{path}: {loops} loop(s) and {risky} data or action elements; review whether the workload belongs in Batch Apex"))
    for element in root.iter():
        if local_name(element.tag) in DML_ACTION_TAGS and not children(element, "faultConnector"):
            label = child_text(element, "label") or child_text(element, "name") or "<unnamed element>"
            out.append(("WARN", f"{path}: scheduled element `{label}` has no fault connector; background automation should fail observably"))
    return True, out


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    findings: list[tuple[str, str]] = []
    scheduled = 0
    for flow_path in sorted(root.rglob("*.flow-meta.xml")):
        is_sched, found = check_flow(flow_path)
        scheduled += is_sched
        findings.extend(found)
    if not scheduled and not findings:
        print(f"WARN: no schedule-triggered flows (*.flow-meta.xml with triggerType Scheduled) under {root}")
        return 0
    for level, msg in findings:
        print(f"{level}: {msg}")
    if not findings:
        print("No issues found.")
    has_error = any(level == "ERROR" for level, _ in findings)
    has_warn = any(level == "WARN" for level, _ in findings)
    return 1 if has_error or (args.strict and has_warn) else 0


if __name__ == "__main__":
    sys.exit(main())
