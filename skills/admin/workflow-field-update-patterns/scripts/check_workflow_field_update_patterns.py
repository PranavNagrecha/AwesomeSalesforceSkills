#!/usr/bin/env python3
"""Static checks for field-update automation anti-patterns.

Scans Salesforce metadata for the high-confidence patterns documented
in this skill:

  1. Workflow Rule (.workflow-meta.xml) with `<fieldUpdates>` action —
     deprecated for new actions; should be migrated to flow.
  2. After-save record-triggered flow (`<triggerType>RecordAfterSave`)
     that performs `<recordUpdates>` against the same SObject as the
     trigger AND has no `<filters>` mentioning ISCHANGED — likely
     recursion risk.
  3. Multiple record-triggered flows with the same `<object>` and
     `<triggerType>` in the same project — non-deterministic ordering.

Stdlib only. Walks `*.flow-meta.xml` and `*.workflow-meta.xml`.

Usage:
    python3 check_workflow_field_update_patterns.py --src-root .
    python3 check_workflow_field_update_patterns.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"


def _strip_ns(tag: str) -> str:
    return tag[len(_NS_TAG):] if tag.startswith(_NS_TAG) else tag


def _scan_workflow_xml(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return findings
    root = tree.getroot()
    if _strip_ns(root.tag) != "Workflow":
        return findings

    field_updates = root.findall(f"{_NS_TAG}fieldUpdates")
    if field_updates:
        names = []
        for fu in field_updates[:5]:
            name_el = fu.find(f"{_NS_TAG}fullName")
            if name_el is not None and name_el.text:
                names.append(name_el.text)
        findings.append(
            f"{path}: contains {len(field_updates)} <fieldUpdates> action(s) "
            f"({', '.join(names)}{'…' if len(field_updates) > 5 else ''}) — "
            "Workflow Rule field updates are deprecated for new actions. "
            "Migrate to record-triggered flow via Setup → Migrate to Flow "
            "(references/gotchas.md § 3)"
        )
    return findings


def _scan_flow_xml(path: Path) -> tuple[list[str], tuple[str, str] | None]:
    """Scan one flow file for after-save same-record-update without
    recursion guard. Also return ``(object, triggerType)`` for the
    duplicate-flow check."""
    findings: list[str] = []
    object_trigger: tuple[str, str] | None = None

    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return findings, None
    root = tree.getroot()
    if _strip_ns(root.tag) != "Flow":
        return findings, None

    start_el = root.find(f"{_NS_TAG}start")
    if start_el is None:
        return findings, None

    object_el = start_el.find(f"{_NS_TAG}object")
    trigger_type_el = start_el.find(f"{_NS_TAG}triggerType")
    if object_el is None or trigger_type_el is None:
        return findings, None
    if not (object_el.text and trigger_type_el.text):
        return findings, None
    object_name = object_el.text
    trigger_type = trigger_type_el.text
    object_trigger = (object_name, trigger_type)

    # Only after-save record-triggered flows have the recursion concern.
    if "RecordAfterSave" not in trigger_type:
        return findings, object_trigger

    # Find recordUpdates that target the same SObject as the trigger.
    record_updates = root.findall(f"{_NS_TAG}recordUpdates")
    same_object_updates: list[ET.Element] = []
    for ru in record_updates:
        # The target SObject is in <object> (for filtered update) or via
        # <inputReference> (for $Record). $Record is always same-object.
        ru_object_el = ru.find(f"{_NS_TAG}object")
        input_ref_el = ru.find(f"{_NS_TAG}inputReference")
        target_is_record = (
            input_ref_el is not None
            and input_ref_el.text
            and input_ref_el.text.strip() in {"$Record", "Record", "$Record__Prior"}
        )
        target_is_same_obj = (
            ru_object_el is not None
            and ru_object_el.text == object_name
        )
        if target_is_record or target_is_same_obj:
            same_object_updates.append(ru)

    if not same_object_updates:
        return findings, object_trigger

    # Check for ISCHANGED in the start filter (entry condition).
    has_ischanged_filter = False
    for f in start_el.findall(f"{_NS_TAG}filters"):
        op_el = f.find(f"{_NS_TAG}operator")
        if op_el is not None and op_el.text and "Changed" in op_el.text:
            has_ischanged_filter = True
            break
    # Also accept formula-based filters that reference ISCHANGED.
    formula_el = start_el.find(f"{_NS_TAG}filterFormula")
    if formula_el is not None and formula_el.text and "ISCHANGED" in formula_el.text.upper():
        has_ischanged_filter = True

    if not has_ischanged_filter:
        update_names = []
        for ru in same_object_updates[:3]:
            n = ru.find(f"{_NS_TAG}name")
            if n is not None and n.text:
                update_names.append(n.text)
        findings.append(
            f"{path}: after-save record-triggered flow on `{object_name}` "
            f"updates the same record ({', '.join(update_names)}"
            f"{'…' if len(same_object_updates) > 3 else ''}) but the start "
            "filter has no ISCHANGED operator — recursion risk. Add "
            "ISCHANGED entry condition or move to before-save flow "
            "(references/gotchas.md § 2)"
        )

    return findings, object_trigger


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    findings: list[str] = []
    flows_by_object_trigger: dict[tuple[str, str], list[Path]] = defaultdict(list)

    for f in root.rglob("*.workflow-meta.xml"):
        findings.extend(_scan_workflow_xml(f))

    for f in root.rglob("*.flow-meta.xml"):
        flow_findings, ot = _scan_flow_xml(f)
        findings.extend(flow_findings)
        if ot is not None:
            flows_by_object_trigger[ot].append(f)

    # Smell 3: multiple flows on same object + trigger type.
    for (obj, trig), files in flows_by_object_trigger.items():
        if len(files) > 1:
            files_short = [str(p.relative_to(root)) if p.is_relative_to(root) else str(p) for p in files[:3]]
            findings.append(
                f"{files[0].parent}: {len(files)} record-triggered flow(s) "
                f"on `{obj}` with trigger type `{trig}` — non-deterministic "
                "ordering between them. Consolidate into one flow per "
                "object per save-time slot "
                "(references/gotchas.md § 7) — files: "
                f"{', '.join(files_short)}{'…' if len(files) > 3 else ''}"
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for field-update automation "
            "anti-patterns (deprecated WFR field updates, after-save "
            "same-record updates without ISCHANGED guard, multiple "
            "flows on same object/trigger)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the metadata tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no field-update automation anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
