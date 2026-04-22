#!/usr/bin/env python3
"""Checker script for Flow Orchestration Admin skill.

Scans metadata for Flow Orchestration anti-patterns:
- Evaluation flows that exceed element-count complexity thresholds
- Interactive steps without assignee
- Scheduled Apex that advances orchestrations via polling

Usage:
    python3 check_flow_orchestration_admin.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ORCH_ADVANCE_PAT = re.compile(r"(?i)FlowOrchestration|OrchestrationInstance|resume.*orchestration")
INTERACTIVE_STEP_PAT = re.compile(
    r"(?is)<stepType>InteractiveStep</stepType>(.*?)</step>"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Flow Orchestration configuration for issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_orchestrations(root: Path) -> list[str]:
    issues: list[str] = []
    orch_dir = root / "orchestrations"
    flows_dir = root / "flows"
    orch_files: list[Path] = []
    if orch_dir.exists():
        orch_files.extend(orch_dir.rglob("*.xml"))
    if flows_dir.exists():
        # Some deployments keep orchestration metadata in flows/ with Orchestrator processType
        for path in flows_dir.rglob("*.flow-meta.xml"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if "<processType>Orchestrator</processType>" in text:
                orch_files.append(path)

    for path in orch_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for block in INTERACTIVE_STEP_PAT.findall(text):
            if "<assignee" not in block and "<relatedRecordFields" not in block:
                issues.append(
                    f"{path.relative_to(root)}: InteractiveStep with no assignee; work items will not surface"
                )
    return issues


def check_evaluation_flow_complexity(root: Path) -> list[str]:
    issues: list[str] = []
    flows_dir = root / "flows"
    if not flows_dir.exists():
        return issues
    for path in flows_dir.rglob("*.flow-meta.xml"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "<processType>EvaluationFlow</processType>" not in text:
            continue
        element_count = sum(
            len(re.findall(rf"<{tag}>", text))
            for tag in ("decisions", "assignments", "loops", "recordLookups", "recordUpdates")
        )
        if element_count > 5:
            issues.append(
                f"{path.relative_to(root)}: EvaluationFlow has {element_count} elements; keep lean (<=5)"
            )
    return issues


def check_polling_apex(root: Path) -> list[str]:
    issues: list[str] = []
    classes_dir = root / "classes"
    if not classes_dir.exists():
        return issues
    for path in classes_dir.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Schedulable" in text and ORCH_ADVANCE_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: scheduled Apex advances orchestration via polling; prefer Platform Events"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_orchestrations(manifest_dir))
    issues.extend(check_evaluation_flow_complexity(manifest_dir))
    issues.extend(check_polling_apex(manifest_dir))

    if not issues:
        print("No Flow Orchestration anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
