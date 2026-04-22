#!/usr/bin/env python3
"""Checker for Apex Trigger Context Variables skill.

Scans Apex triggers for:
- Trigger.oldMap access in insert-only events
- Trigger.newMap access in before insert
- Branching on Trigger.size (bulkification smell)

Usage:
    python3 check_apex_trigger_context_variables.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TRIGGER_HEADER = re.compile(
    r"trigger\s+(\w+)\s+on\s+\w+\s*\(([^)]+)\)", re.IGNORECASE
)
TRIGGER_SIZE_BRANCH = re.compile(r"Trigger\.size\s*[<>=!]")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Trigger context variable misuse.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_trigger(path: Path, root: Path) -> list[str]:
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return issues

    header = TRIGGER_HEADER.search(text)
    if not header:
        return issues
    events = {e.strip().lower() for e in header.group(2).split(",")}

    only_insert = events.issubset({"before insert", "after insert"})
    is_before_insert = "before insert" in events and len(events) == 1

    if only_insert and "Trigger.oldMap" in text:
        issues.append(
            f"{path.relative_to(root)}: Trigger.oldMap used in insert-only trigger; oldMap is null"
        )
    if is_before_insert and "Trigger.newMap" in text:
        issues.append(
            f"{path.relative_to(root)}: Trigger.newMap used in before-insert trigger; records have no Id"
        )
    for m in TRIGGER_SIZE_BRANCH.finditer(text):
        line_no = text[: m.start()].count("\n") + 1
        issues.append(
            f"{path.relative_to(root)}:{line_no}: branching on Trigger.size; bulkify unconditionally"
        )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for trg in root.rglob("*.trigger"):
        issues.extend(check_trigger(trg, root))

    if not issues:
        print("No Trigger context-variable issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
