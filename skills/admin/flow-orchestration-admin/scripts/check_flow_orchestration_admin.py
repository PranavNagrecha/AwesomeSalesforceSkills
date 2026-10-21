#!/usr/bin/env python3
"""Checker script for Flow Orchestration Admin skill.

Scans a metadata source tree (flows/ and classes/) for orchestration defects.
Field names follow the Metadata API Flow type (api_meta 264):
- FlowStageStep.actionName is Required (L74746)            -> ERROR when absent
- FlowStageStepAssignee.assigneeType is Required, valid values
  Group / Queue / User / invalid (L74889-74894)             -> ERROR when absent or other
- FlowStageStep.assignees is NOT marked Required (L74763)   -> WARN when a
  stepInteractive step has none
- stepApproval is "available only for flow approval processes" (L74750-74753)
                                                             -> WARN inside an Orchestrator flow
- EvaluationFlow with more than 5 decision/assignment/loop/lookup/update
  elements (heuristic)                                       -> WARN
- Schedulable Apex that references orchestration objects (polling) -> WARN
- A flow file that does not parse                            -> ERROR

Exit codes: 1 on any ERROR or a missing --manifest-dir; WARN findings exit 0
unless --strict; an empty directory prints one WARN and exits 0.

Usage:
    python3 check_flow_orchestration_admin.py --manifest-dir path/to/force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
ORCH_TYPES = {"Orchestrator", "ApprovalWorkflow"}
ASSIGNEE_TYPES = {"Group", "Queue", "User", "invalid"}
EVAL_TAGS = ("decisions", "assignments", "loops", "recordLookups", "recordUpdates")
ORCH_REF_PAT = re.compile(r"\b(FlowOrchestration\w*|ConnectApi\.Orchestration)\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Flow Orchestration configuration for issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return parser.parse_args()


def _child(el: ET.Element, tag: str) -> ET.Element | None:
    found = el.find(NS + tag)
    if found is None:
        found = el.find(tag)
    return found


def _children(el: ET.Element, tag: str) -> list[ET.Element]:
    return el.findall(NS + tag) + el.findall(tag)


def _text(el: ET.Element, tag: str) -> str:
    node = _child(el, tag)
    return (node.text or "").strip() if node is not None else ""


def check_flow(path: Path, rel: str, errors: list[str], warns: list[str]) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        errors.append(f"{rel}: XML does not parse ({exc})")
        return
    process_type = _text(root, "processType")
    if process_type == "EvaluationFlow":
        count = sum(len(_children(root, tag)) for tag in EVAL_TAGS)
        if count > 5:
            warns.append(f"{rel}: EvaluationFlow has {count} elements; keep it lean (<=5)")
        return
    if process_type not in ORCH_TYPES:
        return
    for stage in _children(root, "orchestratedStages"):
        stage_name = _text(stage, "name") or "?"
        for step in _children(stage, "stageSteps"):
            step_name = _text(step, "name") or "?"
            where = f"{rel}: stage {stage_name} step {step_name}"
            action_type = _text(step, "actionType")
            if not _text(step, "actionName"):
                errors.append(f"{where}: missing Required actionName")
            if action_type == "stepApproval" and process_type == "Orchestrator":
                warns.append(f"{where}: stepApproval is documented only for flow approval processes")
            assignees = _children(step, "assignees")
            if action_type == "stepInteractive" and not assignees:
                warns.append(f"{where}: stepInteractive has no <assignees>; name a User, Group, or Queue")
            for assignee in assignees:
                a_type = _text(assignee, "assigneeType")
                if a_type not in ASSIGNEE_TYPES:
                    errors.append(f"{where}: assigneeType '{a_type}' is not Group, Queue, User or invalid")


def check_polling_apex(root: Path, warns: list[str]) -> None:
    for path in sorted(root.rglob("*.cls")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if re.search(r"\bSchedulable\b", text) and ORCH_REF_PAT.search(text):
            warns.append(
                f"{path.relative_to(root)}: Schedulable Apex references orchestration objects; "
                "resume runs by publishing FlowOrchestrationEvent instead of polling"
            )


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    flows = sorted(root.rglob("*.flow-meta.xml")) + sorted(root.rglob("*.flow"))
    classes = list(root.rglob("*.cls"))
    if not flows and not classes:
        print(f"WARN: no *.flow-meta.xml or *.cls files under {root}; nothing to check")
        return 0

    errors: list[str] = []
    warns: list[str] = []
    for path in flows:
        check_flow(path, str(path.relative_to(root)), errors, warns)
    check_polling_apex(root, warns)

    for msg in errors:
        print(f"ERROR: {msg}")
    for msg in warns:
        print(f"WARN: {msg}")
    if not errors and not warns:
        print("OK: no Flow Orchestration issues detected.")
    if errors:
        return 1
    if warns and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
