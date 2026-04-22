#!/usr/bin/env python3
"""Checker for Activity and Task Patterns skill.

Scans Apex for:
- Query against the abstract Activity object
- DML on ActivityHistory / OpenActivity (read-only)
- Loop-DML on Task / Event
- Polymorphic What.* access without TYPEOF

Usage:
    python3 check_activity_and_task_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FROM_ACTIVITY = re.compile(r"\bFROM\s+Activity\b", re.IGNORECASE)
DML_READONLY = re.compile(r"\b(insert|update|upsert|delete)\s+\w*(ActivityHistory|OpenActivity)", re.IGNORECASE)
LOOP_TASK_DML = re.compile(r"for\s*\([^)]*\)\s*\{[^}]*\binsert\s+new\s+(Task|Event)\b", re.DOTALL | re.IGNORECASE)
WHAT_WITHOUT_TYPEOF = re.compile(r"What\.(Name|Industry|Amount|StageName|[A-Za-z_]+__c)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Task/Event/Activity anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def iter_apex(root: Path):
    for path in root.rglob("*.cls"):
        yield path
    for path in root.rglob("*.trigger"):
        yield path


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_apex(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in FROM_ACTIVITY.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: query FROM Activity; query Task or Event"
            )

        for m in DML_READONLY.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: DML on {m.group(2)}; it is read-only"
            )

        for m in LOOP_TASK_DML.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: insert new {m.group(1)} inside loop; bulkify"
            )

        if "TYPEOF" not in text.upper():
            for m in WHAT_WITHOUT_TYPEOF.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: What.{m.group(1)} without TYPEOF; polymorphic access will fail"
                )
                break
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_apex(root)
    if not issues:
        print("No Activity/Task anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
