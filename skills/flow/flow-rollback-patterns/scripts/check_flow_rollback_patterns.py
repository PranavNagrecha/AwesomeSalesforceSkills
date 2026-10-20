#!/usr/bin/env python3
"""Static checker for flow-rollback-patterns.

Parses *.flow-meta.xml under --manifest-dir. Stdlib only; reads metadata, never runs a
flow or contacts an org. Grounding is the Metadata API Developer Guide 264 ("api_meta");
line numbers come from `grep -n`.

ERROR (exit 1 always)
  * A flow file that does not parse.
  * A recordRollbacks (Roll Back Records) element in a flow whose processType is
    AutoLaunchedFlow or that has a start triggerType (record-triggered, scheduled,
    platform-event). The guide: "Available only in screen flows" (api_meta 264
    L73987). Other processTypes than Flow (the screen flow, L70802-70804) are a
    REVIEW WARN, because several of them also carry screens.
  * A recordRollbacks element carrying a faultConnector. The type has a single
    connector field and no fault connector (api_meta 264 L73990-73992).
WARN (exit 0 unless --strict)
  * A path from a fault connector that creates a record on a non-event object and then
    reaches a Roll Back Records element. The rollback "cancels its pending record
    changes" (api_meta 264 L73986), and the log record is one of them. A write to an
    object ending __e is the documented way to leave evidence: a Publish Immediately
    event "can't be rolled back" (platform_events 264 L276-277).

An empty tree prints one WARN and exits 0 (1 with --strict). A missing path prints an
ERROR and exits 1.

Usage:
    python3 check_flow_rollback_patterns.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CONNECTORS = {"connector", "faultConnector", "defaultConnector", "nextValueConnector", "noMoreValuesConnector"}
NODES = {
    "actionCalls", "apexPluginCalls", "assignments", "collectionProcessors", "decisions", "loops", "recordCreates",
    "recordDeletes", "recordLookups", "recordUpdates", "screens", "subflows", "transforms", "waits", "customErrors",
    "recordRollbacks", "steps",
}


def local(el: ET.Element) -> str:
    return el.tag.split("}")[-1]


def text(parent: ET.Element, name: str) -> str:
    for c in parent:
        if local(c) == name:
            return (c.text or "").strip()
    return ""


def targets(node: ET.Element) -> list[tuple[str, str]]:
    return [(local(e), text(e, "targetReference")) for e in node.iter() if local(e) in CONNECTORS and text(e, "targetReference")]


def check_flow(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path}: XML does not parse ({exc})"], warns
    nodes = {text(el, "name"): el for el in root if local(el) in NODES}
    rollbacks = [n for n, el in nodes.items() if local(el) == "recordRollbacks"]
    process_type = text(root, "processType")
    start = next((el for el in root if local(el) == "start"), None)
    triggered = start is not None and bool(text(start, "triggerType"))
    for name in rollbacks:
        if process_type == "AutoLaunchedFlow" or triggered:
            errors.append(f"{path}: recordRollbacks {name} is in a flow with processType {process_type or '<none>'}; Roll Back Records is screen-flow only (api_meta 264 L73987)")
        elif process_type != "Flow":
            warns.append(f"{path}: REVIEW recordRollbacks {name} is in a flow with processType {process_type or '<none>'}; Roll Back Records is screen-flow only (api_meta 264 L73987)")
        if any(tag == "faultConnector" for tag, _ in targets(nodes[name])):
            errors.append(f"{path}: recordRollbacks {name} has a faultConnector; the element has only a connector (api_meta 264 L73990-73992)")
    seen: set[tuple[str, bool]] = set()
    reported: set[str] = set()
    stack = [(t, False) for node in nodes.values() for tag, t in targets(node) if tag == "faultConnector"]
    while stack:
        cur, logged = stack.pop()
        if (cur, logged) in seen or cur not in nodes:
            continue
        seen.add((cur, logged))
        node = nodes[cur]
        if local(node) == "recordRollbacks" and logged and cur not in reported:
            reported.add(cur)
            warns.append(f"{path}: a fault path creates a record and then reaches rollback {cur}; the record is cancelled with it (api_meta 264 L73986); use a Publish Immediately event")
        if local(node) == "recordCreates" and not text(node, "object").endswith("__e"):
            logged = True
        stack.extend((t, logged) for _, t in targets(node))
    return errors, warns


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Flow metadata for rollback placement and cancelled log writes.")
    parser.add_argument("--manifest-dir", default=".", help="Root of the metadata tree (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    args = parser.parse_args()
    root_dir = Path(args.manifest_dir)
    if not root_dir.is_dir():
        print(f"ERROR: manifest directory not found: {root_dir}")
        sys.exit(1)
    files = sorted(root_dir.rglob("*.flow-meta.xml"))
    if not files:
        print(f"WARN: no *.flow-meta.xml files found under {root_dir}")
        return 1 if args.strict else 0
    errors: list[str] = []
    warns: list[str] = []
    for f in files:
        e, w = check_flow(f)
        errors += e
        warns += w
    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if not errors and not warns:
        print("No issues found.")
    if errors:
        sys.exit(1)
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
