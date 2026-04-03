#!/usr/bin/env python3
"""Checker script for Record Triggered Flow Patterns skill."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Record Triggered Flow Patterns configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_record_triggered_flow_patterns(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        text = flow_path.read_text(encoding="utf-8", errors="ignore")
        if "RecordBeforeSave" not in text and "RecordAfterSave" not in text:
            continue

        if "RecordAfterSave" in text and "<recordUpdates>" in text and "$Record" in text:
            issues.append(
                f"{flow_path}: after-save flow appears to update the triggering record; review for recursion and consider before-save if only same-record fields change."
            )

        if "RecordBeforeSave" in text:
            forbidden = ("<recordCreates>", "<recordDeletes>", "<actionCalls>", "<subflows>")
            if any(marker in text for marker in forbidden):
                issues.append(
                    f"{flow_path}: before-save flow contains creates, deletes, action calls, or subflows; verify the design belongs in after-save or Apex."
                )

        if not re.search(r"(Record__Prior|PriorValue|ISCHANGED|isChanged)", text):
            issues.append(
                f"{flow_path}: record-triggered flow has no obvious prior-value or changed-field logic; confirm the start criteria are not broader than the business event."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_record_triggered_flow_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
