#!/usr/bin/env python3
"""Audit Flow metadata for Platform Event publish/subscribe anti-patterns.

Detects three recurring defect classes called out in SKILL.md:

  - Publisher flows that use `recordCreates` against a `__e` sObject without
    setting `eventPublishingBehavior` — ambiguous publish semantics (Publish
    After Commit vs. Publish Immediately must be explicit).
  - Platform-Event-Triggered Flows (`start.object` ending in `__e`) missing a
    fault connector on the first risky DML/action — a subscriber failure
    silently drops the event and there's no compensation path.
  - Subscriber flows with no `formula` or `decision` gate that would support
    idempotency — replays will re-run side effects.

Emits JSON findings to stdout and a WARN/ERROR summary to stderr. Exits
non-zero when any ISSUE-level finding is present, so CI can gate on it.

Usage:
    python3 check_flow_platform_events_integration.py path/to/force-app
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FLOW_SUFFIX = ".flow-meta.xml"
RISKY_ELEMENTS = {"recordCreates", "recordUpdates", "recordDeletes", "actionCalls", "subflows"}


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


def find_start_object(root: ET.Element) -> str:
    for child in root:
        if local_name(child.tag) == "start":
            return child_text(child, "object")
    return ""


def audit_flow(path: Path) -> list[str]:
    findings: list[str] = []
    root = ET.parse(path).getroot()
    start_object = find_start_object(root)
    is_pe_triggered = start_object.endswith("__e")

    publisher_element_count = 0
    has_idempotency_gate = False

    for child in root:
        tag = local_name(child.tag)
        if tag in ("decisions", "formulas"):
            has_idempotency_gate = True

        if tag == "recordCreates":
            target_obj = child_text(child, "object")
            label = child_text(child, "label") or child_text(child, "name") or "<unnamed>"
            if target_obj.endswith("__e"):
                publisher_element_count += 1
                behavior = child_text(child, "eventPublishingBehavior")
                if not behavior:
                    findings.append(
                        f"ISSUE {path}: publisher `{label}` to `{target_obj}` has no eventPublishingBehavior — "
                        "publish semantics (AfterCommit vs Immediate) must be explicit"
                    )

        if is_pe_triggered and tag in RISKY_ELEMENTS and not has_child(child, "faultConnector"):
            label = child_text(child, "label") or child_text(child, "name") or "<unnamed>"
            findings.append(
                f"ISSUE {path}: subscriber flow element `{label}` ({tag}) has no fault connector — "
                "event will be dropped on failure with no compensation"
            )

    if is_pe_triggered and not has_idempotency_gate:
        findings.append(
            f"WARN {path}: Platform-Event-Triggered Flow has no decision/formula gate — "
            "subscriber may re-run side effects on event replay"
        )

    if publisher_element_count == 0 and not is_pe_triggered and start_object:
        # Not a PE publisher, not a PE subscriber. Ignore — out of scope for this checker.
        return findings

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

    has_issue = any(f.startswith("ISSUE") for f in findings)
    if has_issue:
        print(f"ERROR: {sum(1 for f in findings if f.startswith('ISSUE'))} platform-event integration issue(s)", file=sys.stderr)
        return 1
    if findings:
        print(f"WARN: {len(findings)} advisory finding(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
