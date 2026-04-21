#!/usr/bin/env python3
"""Audit Flow metadata for transaction-boundary smells.

A "transactional smell" is a Flow structure that almost always straddles
a governor-limit boundary badly. This checker flags:

  - Record-triggered flows with `triggerType = RecordAfterSave` that do
    DML inside a loop (classic after-save bulkification issue — the loop
    shares the caller's DML allowance).
  - After-save flows that perform `actionCalls` of kind `emailSimple` or
    `apex` without a fault connector (fault cascades into caller
    transaction, rolling back unrelated work).
  - Screen flows that do DML before a `waits` (pause) — pause starts a
    new transaction, so DML committed before pause cannot be rolled back
    if the resumed transaction fails.
  - Scheduled-path entries missing a timeSource — almost always a misfire.

Usage:
    python3 check_flow_transactional_boundaries.py path/to/force-app
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FLOW_SUFFIX = ".flow-meta.xml"
DML_ELEMENTS = {"recordCreates", "recordUpdates", "recordDeletes"}


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, name: str) -> str:
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def has_child(element: ET.Element, name: str) -> bool:
    return any(local_name(child.tag) == name for child in element)


def iter_flow_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(p for p in path.rglob(f"*{FLOW_SUFFIX}") if p.is_file())
        elif path.is_file() and path.name.endswith(FLOW_SUFFIX):
            files.append(path)
    return sorted(set(files))


def flow_metadata(root: ET.Element) -> dict[str, str]:
    meta = {"processType": "", "triggerType": "", "start_object": ""}
    for child in root:
        tag = local_name(child.tag)
        if tag == "processType" and child.text:
            meta["processType"] = child.text.strip()
        if tag == "start":
            for grand in child:
                gname = local_name(grand.tag)
                if gname == "triggerType" and grand.text:
                    meta["triggerType"] = grand.text.strip()
                if gname == "object" and grand.text:
                    meta["start_object"] = grand.text.strip()
                if gname == "scheduledPaths":
                    for sp in grand:
                        if local_name(sp.tag) == "scheduledPaths":
                            continue
                        if not has_child(sp, "timeSource"):
                            meta.setdefault("scheduled_path_issues", "")
                            label = child_text(sp, "label") or "<unnamed scheduled path>"
                            meta["scheduled_path_issues"] += f"{label};"
    return meta


def audit_flow(path: Path) -> list[str]:
    findings: list[str] = []
    root = ET.parse(path).getroot()
    meta = flow_metadata(root)

    is_after_save = meta["triggerType"] == "RecordAfterSave"
    is_screen = meta["processType"] == "Flow"

    dml_elements: list[ET.Element] = []
    action_calls: list[ET.Element] = []
    loops: list[ET.Element] = []
    waits: list[ET.Element] = []

    for child in root:
        tag = local_name(child.tag)
        if tag in DML_ELEMENTS:
            dml_elements.append(child)
        elif tag == "actionCalls":
            action_calls.append(child)
        elif tag == "loops":
            loops.append(child)
        elif tag == "waits":
            waits.append(child)

    if is_after_save and loops and dml_elements:
        findings.append(
            f"ISSUE {path}: after-save flow contains {len(loops)} loop(s) alongside {len(dml_elements)} DML element(s); "
            "verify DML is not inside the loop (shared governor budget with caller)"
        )

    if is_after_save:
        for action in action_calls:
            action_type = child_text(action, "actionType")
            if action_type in ("emailSimple", "apex") and not has_child(action, "faultConnector"):
                label = child_text(action, "label") or child_text(action, "name") or "<unnamed>"
                findings.append(
                    f"ISSUE {path}: after-save action `{label}` ({action_type}) has no fault connector — "
                    "failure will cascade and roll back the caller transaction"
                )

    if is_screen and waits and dml_elements:
        findings.append(
            f"WARN {path}: screen flow has {len(waits)} wait/pause element(s) and {len(dml_elements)} DML element(s); "
            "confirm DML does not precede the pause (pause opens a new transaction)"
        )

    sp_issues = meta.get("scheduled_path_issues", "")
    if sp_issues:
        findings.append(f"ERROR {path}: scheduled path(s) missing timeSource: {sp_issues}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Flow metadata files or directories")
    args = parser.parse_args()

    files = iter_flow_files(args.paths)
    if not files:
        print(json.dumps({"findings": [], "summary": "no Flow metadata found"}))
        print("WARN: no Flow metadata under provided paths", file=sys.stderr)
        return 0

    findings: list[str] = []
    for path in files:
        findings.extend(audit_flow(path))

    summary = f"Scanned {len(files)} Flow metadata file(s); {len(findings)} finding(s)."
    print(json.dumps({"findings": findings, "summary": summary}, indent=2))

    hard = sum(1 for f in findings if f.startswith(("ERROR", "ISSUE")))
    if hard:
        print(f"ERROR: {hard} transaction-boundary issue(s) require action", file=sys.stderr)
        return 1
    if findings:
        print(f"WARN: {len(findings)} advisory finding(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
