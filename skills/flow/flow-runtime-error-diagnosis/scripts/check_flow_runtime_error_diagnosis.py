#!/usr/bin/env python3
"""Checker for the Flow Runtime Error Diagnosis skill.

Parses every *.flow-meta.xml under --manifest-dir (--source-dir is accepted as an alias)
and reports the two shapes behind the limit errors this skill diagnoses, plus the
missing fault path it asks you to add. Stdlib only; reads metadata, never runs a flow.

WARN (exit 0 unless --strict)
  * Get Records (recordLookups) or Create/Update/Delete Records inside a loop body: one
    SOQL query or DML statement per iteration. Synchronous per-transaction limits are
    100 SOQL queries and 150 DML statements (apexdev 264 L19747, L19757).
  * Create/Update/Delete Records with no faultConnector (Review Checklist; a fault
    connector is documented on these types in api_meta 264).
ERROR (exit 1 always)
  * A flow file that does not parse.
  * A loops element whose nextValueConnector targets an element that is not in the
    file (a broken reference). A loop with no nextValueConnector at all is a WARN:
    FlowLoop does not mark the field Required (api_meta 264 L73420).

An empty tree prints one WARN and exits 0 (1 with --strict). A missing path prints an
ERROR and exits 1.

Usage:
    python3 check_flow_runtime_error_diagnosis.py --manifest-dir force-app/main/default [--strict]
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
        return [f"{path}: XML parse error ({exc})"], warns
    nodes = {text(el, "name"): el for el in root if local(el) in NODES}
    for name, node in nodes.items():
        if local(node) in DML and not any(tag == "faultConnector" for tag, _ in targets(node)):
            warns.append(f"{path}: {local(node)} {name} has no fault path; runtime errors surface as raw platform messages")
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
            kind = {"recordLookups": "SOQL query", "recordCreates": "DML statement", "recordUpdates": "DML statement", "recordDeletes": "DML statement"}.get(local(nodes[cur]))
            if kind:
                cite = "L19747" if kind == "SOQL query" else "L19757"
                warns.append(f"{path}: {local(nodes[cur])} {cur} runs one {kind} per iteration of loop {name} (apexdev 264 {cite})")
            stack.extend(t for _, t in targets(nodes[cur]))
    return errors, warns


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Flow metadata for runtime error patterns.")
    parser.add_argument("--manifest-dir", "--source-dir", dest="manifest_dir", default=".", help="Root of the metadata tree (default: current directory).")
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
        print("No Flow runtime error pattern issues found.")
    if errors:
        sys.exit(1)
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
