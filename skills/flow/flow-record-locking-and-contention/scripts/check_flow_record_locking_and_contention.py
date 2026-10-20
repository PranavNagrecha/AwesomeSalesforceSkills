#!/usr/bin/env python3
"""Static checker for flow-record-locking-and-contention.

Parses *.flow-meta.xml and platform-event *__e.object-meta.xml under --manifest-dir.
Stdlib only; never contacts an org and cannot see a lock, so it flags only the shapes
this skill's patterns remove.

WARN (exit 0 unless --strict)
  * Create/Update/Delete Records inside a loop body: one DML statement per iteration.
    The synchronous limit is 150 DML statements (apexdev 264 L19757), and every
    statement is a separate lock window (Pattern 1).
  * Create/Update/Delete Records with no faultConnector (Review Checklist; gotcha 5).
  * A platform event with publishBehavior PublishImmediately. The platform-events
    guide says a subscriber "can sometimes receive the event message before the data
    is committed" with that option and recommends Publish After Commit when the
    subscriber needs committed data (platform_events 264 L346-351). Pattern 2 relies
    on that choice. An event with no publishBehavior is flagged too, because "If you
    don't specify this field, the default value used is PublishImmediately" (api_meta
    264 L44513). REVIEW only: Publish Immediately is the guide's default.
ERROR (exit 1 always)
  * A file that does not parse, or a loops element whose nextValueConnector targets
    an element that is not in the file (a broken reference). A loop with no
    nextValueConnector at all is a WARN: FlowLoop does not mark the field Required
    (api_meta 264 L73420).

An empty tree prints one WARN and exits 0 (1 with --strict). A missing path prints an
ERROR and exits 1.

Usage:
    python3 check_flow_record_locking_and_contention.py --manifest-dir force-app/main/default [--strict]
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
DML = {"recordCreates", "recordUpdates", "recordDeletes"}


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
    for name, node in nodes.items():
        if local(node) in DML and not any(tag == "faultConnector" for tag, _ in targets(node)):
            warns.append(f"{path}: {local(node)} {name} has no faultConnector (gotcha 5)")
        if local(node) != "loops":
            continue
        first = [t for tag, t in targets(node) if tag == "nextValueConnector"]
        if not first:
            warns.append(f"{path}: loop {name} has no nextValueConnector (an empty loop body)")
            continue
        if first[0] not in nodes:
            errors.append(f"{path}: loop {name} nextValueConnector targets {first[0]}, which is not in the file")
            continue
        seen: set[str] = set()
        stack = [first[0]]
        while stack:
            cur = stack.pop()
            if cur in seen or cur == name or cur not in nodes:
                continue
            seen.add(cur)
            if local(nodes[cur]) in DML:
                warns.append(f"{path}: {local(nodes[cur])} {cur} runs once per iteration of loop {name}; collect then update once (apexdev 264 L19757)")
            stack.extend(t for _, t in targets(nodes[cur]))
    return errors, warns


def check_event(path: Path) -> tuple[list[str], list[str]]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path}: XML does not parse ({exc})"], []
    behavior = text(root, "publishBehavior")
    if behavior in ("", "PublishImmediately"):
        shown = behavior or "<absent: defaults to PublishImmediately, api_meta 264 L44513>"
        return [], [f"{path}: REVIEW publishBehavior {shown}; a subscriber can run before the publisher commits (platform_events 264 L346-351)"]
    return [], []


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Flow metadata for the lock-contention shapes this skill removes.")
    parser.add_argument("--manifest-dir", default=".", help="Root of the metadata tree (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    args = parser.parse_args()
    root_dir = Path(args.manifest_dir)
    if not root_dir.is_dir():
        print(f"ERROR: manifest directory not found: {root_dir}")
        sys.exit(1)
    errors: list[str] = []
    warns: list[str] = []
    seen = 0
    for f in sorted(root_dir.rglob("*.flow-meta.xml")):
        seen += 1
        e, w = check_flow(f)
        errors += e
        warns += w
    for f in sorted(root_dir.rglob("*__e.object-meta.xml")):
        seen += 1
        e, w = check_event(f)
        errors += e
        warns += w
    if seen == 0:
        print(f"WARN: no flow or platform-event metadata found under {root_dir}")
        return 1 if args.strict else 0
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
