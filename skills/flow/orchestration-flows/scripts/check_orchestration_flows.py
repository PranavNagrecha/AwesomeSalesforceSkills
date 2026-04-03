#!/usr/bin/env python3
"""Checker script for Orchestration Flows skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Orchestration Flows configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def count_matches(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def check_orchestration_flows(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        text = flow_path.read_text(encoding="utf-8", errors="ignore")
        lower = text.lower()
        if "orchestration" not in lower:
            continue

        stage_count = count_matches(r"stage", lower)
        step_count = count_matches(r"step", lower)
        work_item_count = count_matches(r"workitem|work item", lower)

        if stage_count > 8:
            issues.append(f"{flow_path}: orchestration appears to define many stages ({stage_count}); review whether the stage model is too granular.")
        if step_count > 20:
            issues.append(f"{flow_path}: orchestration appears to define many steps ({step_count}); review whether the process should be simplified or decomposed.")
        if work_item_count > 0 and "queue" not in lower and "assignee" not in lower:
            issues.append(f"{flow_path}: work-item markers found with no obvious queue or assignee references; confirm interactive ownership is explicit.")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_orchestration_flows(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
