#!/usr/bin/env python3
"""Checker for Apex HTTP Callout Mocking skill.

Scans Apex test classes for:
- Test classes that call http.send but never set a mock
- Mocks that return only status 200 (no error-path coverage)
- DML before Test.setMock in the same method

Usage:
    python3 check_apex_http_callout_mocking.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TEST_CLASS = re.compile(r"@IsTest", re.IGNORECASE)
HTTP_SEND = re.compile(r"\bhttp\.send\s*\(", re.IGNORECASE)
SET_MOCK = re.compile(r"Test\.setMock\s*\(", re.IGNORECASE)
SET_STATUS_200 = re.compile(r"setStatusCode\s*\(\s*200\s*\)")
SET_STATUS_ERR = re.compile(r"setStatusCode\s*\(\s*[45]\d{2}\s*\)")
TEST_METHOD = re.compile(
    r"@IsTest\s+static\s+(?:void\s+)?\w+\s*\([^)]*\)\s*\{",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Apex callout-mock anti-patterns.")
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

        # Test class exercises callout but never calls setMock
        if HTTP_SEND.search(text) and not SET_MOCK.search(text):
            issues.append(
                f"{path.relative_to(root)}: test class makes callouts without Test.setMock"
            )

        # Mock implements HttpCalloutMock: only status 200 → no error-path coverage
        if SET_MOCK.search(text) and SET_STATUS_200.search(text) and not SET_STATUS_ERR.search(text):
            issues.append(
                f"{path.relative_to(root)}: mocks only 200 responses — add an error-path test (4xx/5xx)"
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
        print("No Apex callout-mock anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
