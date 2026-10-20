#!/usr/bin/env python3
"""Static checker for flow-performance-optimization.

Parses every *.flow-meta.xml under --manifest-dir and reports the two shapes this
skill ranks first. Stdlib only; reads metadata, never runs a flow or contacts an org.

WARN (exit 0 unless --strict)
  * A Get Records (recordLookups) or Create/Update/Delete Records element sits inside
    a loop body, so it runs once per iteration. Grounding: the per-transaction limits
    are 100 SOQL queries and 150 DML statements, apexdev 264 L19747 and L19757.
  * A flow whose triggerType is RecordAfterSave contains an Update Records element
    whose inputReference is $Record, i.e. it edits the record that triggered it.
    FlowStart documents RecordBeforeSave as the type that makes "more updates to that
    record before it's saved" (api_meta 264 L75266-75268). REVIEW only: the claim that
    before-save is cheaper is UNVERIFIED in the corpus (see SKILL.md Pattern 1).
ERROR (exit 1 always)
  * A flow file that does not parse, or a loops element whose nextValueConnector
    targets an element that is not in the file (a broken reference). A loop with no
    nextValueConnector at all is a WARN: FlowLoop does not mark the field Required
    (api_meta 264 L73420).

An empty tree prints one WARN and exits 0 (1 with --strict). A missing path prints an
ERROR and exits 1.

Usage:
    python3 check_flow_performance_optimization.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CONNECTOR_TAGS = {"connector", "faultConnector", "defaultConnector", "nextValueConnector", "noMoreValuesConnector"}
NODE_TAGS = {
    "actionCalls", "apexPluginCalls", "assignments", "collectionProcessors", "decisions", "loops", "recordCreates",
    "recordDeletes", "recordLookups", "recordUpdates", "screens", "subflows", "transforms", "waits", "customErrors",
    "recordRollbacks", "steps",
}
PER_ITERATION = {"recordLookups": "SOQL", "recordCreates": "DML", "recordUpdates": "DML", "recordDeletes": "DML"}


def local(el: ET.Element) -> str:
    return el.tag.split("}")[-1]


def child_text(parent: ET.Element, name: str) -> str:
    for c in parent:
        if local(c) == name:
            return (c.text or "").strip()
    return ""


def targets(node: ET.Element) -> list[tuple[str, str]]:
    """(connector tag, target name) for every connector at any depth in this node."""
    out = []
    for el in node.iter():
        if local(el) in CONNECTOR_TAGS:
            t = child_text(el, "targetReference")
            if t:
                out.append((local(el), t))
    return out


def analyse(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path}: XML does not parse ({exc})"], warns
    nodes: dict[str, ET.Element] = {}
    for el in root:
        if local(el) in NODE_TAGS:
            nodes[child_text(el, "name")] = el
    for name, node in nodes.items():
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
        queue = [first[0]]
        while queue:
            cur = queue.pop()
            if cur in seen or cur == name or cur not in nodes:
                continue
            seen.add(cur)
            kind = PER_ITERATION.get(local(nodes[cur]))
            if kind:
                warns.append(f"{path}: {local(nodes[cur])} {cur} runs {kind} once per iteration of loop {name} (apexdev 264 {'L19747' if kind == 'SOQL' else 'L19757'})")
            queue.extend(t for _, t in targets(nodes[cur]))
    start = next((el for el in root if local(el) == "start"), None)
    if start is not None and child_text(start, "triggerType") == "RecordAfterSave":
        for name, node in nodes.items():
            if local(node) == "recordUpdates" and child_text(node, "inputReference") == "$Record":
                warns.append(f"{path}: REVIEW after-save flow updates $Record in {name}; before-save may fit (api_meta 264 L75266-75268)")
    return errors, warns


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Flow metadata for per-iteration SOQL/DML and avoidable after-save updates.")
    parser.add_argument("--manifest-dir", default=".", help="Root of the metadata tree (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    args = parser.parse_args()
    root_dir = Path(args.manifest_dir)
    if not root_dir.is_dir():
        print(f"ERROR: manifest directory not found: {root_dir}")
        sys.exit(1)
    errors: list[str] = []
    warns: list[str] = []
    files = sorted(root_dir.rglob("*.flow-meta.xml"))
    for f in files:
        e, w = analyse(f)
        errors += e
        warns += w
    if not files:
        print(f"WARN: no *.flow-meta.xml files found under {root_dir}")
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
