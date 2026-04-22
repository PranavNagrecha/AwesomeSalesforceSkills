#!/usr/bin/env python3
"""Checker for Apex Test Setup Patterns skill.

Scans Apex test classes for:
- SeeAllData=true on new tests
- Async enqueue (Queueable/future/Batch) without Test.startTest/stopTest
- User-DML + sObject-DML without System.runAs guard

Usage:
    python3 check_apex_test_setup_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SEE_ALL_DATA = re.compile(r"@IsTest\s*\(\s*SeeAllData\s*=\s*true\s*\)", re.IGNORECASE)
TEST_CLASS = re.compile(r"@IsTest", re.IGNORECASE)
ENQUEUE = re.compile(r"System\.enqueueJob|Database\.executeBatch|@future", re.IGNORECASE)
START_STOP = re.compile(r"Test\.startTest\s*\(\s*\)", re.IGNORECASE)
USER_DML = re.compile(r"insert\s+new\s+User\b|insert\s+\w*[Uu]ser[A-Za-z]*\s*;", re.IGNORECASE)
RUNAS = re.compile(r"System\.runAs\s*\(", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex test-setup anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if not TEST_CLASS.search(text):
            continue

        for m in SEE_ALL_DATA.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: @IsTest(SeeAllData=true) couples test to org data"
            )

        if ENQUEUE.search(text) and not START_STOP.search(text):
            issues.append(
                f"{path.relative_to(root)}: async enqueue without Test.startTest/stopTest — async may not flush"
            )

        if USER_DML.search(text) and not RUNAS.search(text):
            issues.append(
                f"{path.relative_to(root)}: inserts User without System.runAs guard — mixed-DML risk"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_apex(root)
    if not issues:
        print("No Apex test-setup anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
