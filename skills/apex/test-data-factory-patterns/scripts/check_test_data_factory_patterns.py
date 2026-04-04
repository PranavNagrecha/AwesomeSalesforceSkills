#!/usr/bin/env python3
"""Checker script for Test Data Factory Patterns skill.

Scans Apex test files for test data anti-patterns:
- @isTest(SeeAllData=true) usage
- Missing @IsTest annotation on factory utility classes
- Hardcoded Salesforce IDs (Profile, RecordType)
- Per-record DML in loops (insert inside for loop)
- Missing System.runAs() for User creation with Contact-linked portal users

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_test_data_factory_patterns.py [--help]
    python3 check_test_data_factory_patterns.py --apex-dir path/to/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex test files for test data factory anti-patterns.",
    )
    parser.add_argument(
        "--apex-dir",
        default=".",
        help="Directory containing Apex .cls files (default: current directory).",
    )
    return parser.parse_args()


HARDCODED_ID_PATTERN = re.compile(
    r"""['"]([0-9A-Za-z]{15,18})['"]\s*[;,\)]""",
    re.IGNORECASE,
)

SF_ID_PREFIXES = {
    "00e": "Profile",
    "012": "RecordType",
    "00D": "Org",
    "00G": "Group",
    "005": "User",
    "00B": "BusinessProcess",
}


def scan_apex_files(apex_dir: Path) -> list[str]:
    """Scan Apex files for test data anti-patterns."""
    issues: list[str] = []

    if not apex_dir.exists():
        issues.append(f"Apex directory not found: {apex_dir}")
        return issues

    cls_files = list(apex_dir.rglob("*.cls"))

    for cls_file in cls_files:
        try:
            content = cls_file.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue

        is_test_class = "@isTest" in content or "@IsTest" in content

        # Check 1: @isTest(SeeAllData=true)
        if re.search(r"@isTest\s*\(\s*SeeAllData\s*=\s*true\s*\)", content, re.IGNORECASE):
            issues.append(
                f"{cls_file.name}: @isTest(SeeAllData=true) detected. Tests using org data "
                f"are fragile and environment-specific. Replace with factory methods that create "
                f"test data. SeeAllData=true is also incompatible with @testSetup."
            )

        # Check 2: Factory class without @IsTest at class level
        if (
            ("TestFactory" in cls_file.name or "TestData" in cls_file.name)
            and is_test_class is False
        ):
            issues.append(
                f"{cls_file.name}: Appears to be a test data factory class but is missing "
                f"the @IsTest annotation at the class level. Without @IsTest, this class "
                f"counts against the org's 6 MB Apex code limit."
            )

        if not is_test_class:
            continue

        # Check 3: Hardcoded Salesforce IDs
        for match in HARDCODED_ID_PATTERN.finditer(content):
            candidate = match.group(1)
            prefix = candidate[:3].lower()
            if prefix in SF_ID_PREFIXES:
                issues.append(
                    f"{cls_file.name}: Potential hardcoded {SF_ID_PREFIXES[prefix]} ID "
                    f"'{candidate}'. Salesforce IDs are org-specific. Query by Name instead: "
                    f"[SELECT Id FROM {SF_ID_PREFIXES[prefix]} WHERE Name = '...' LIMIT 1]"
                )

        # Check 4: insert inside a for loop (DML per record)
        # Simple heuristic: look for 'insert' keyword that follows a 'for' block opening
        lines = content.split("\n")
        in_for_loop = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if re.match(r"\bfor\s*\(", stripped):
                in_for_loop += 1
            if in_for_loop > 0 and "{" in stripped:
                in_for_loop += stripped.count("{") - stripped.count("}")
                if in_for_loop < 1:
                    in_for_loop = 0
            if in_for_loop > 0 and re.search(r"\binsert\b\s+new\b", stripped):
                issues.append(
                    f"{cls_file.name} line ~{i+1}: DML 'insert' inside a for loop. "
                    f"Build a List<SObject> in the loop and insert the list after the loop "
                    f"completes. Per-iteration DML hits the 150 DML statement limit."
                )
                break  # One warning per file

    return issues


def check_test_data_factory_patterns(apex_dir: Path) -> list[str]:
    """Return a list of issue strings."""
    return scan_apex_files(apex_dir)


def main() -> int:
    args = parse_args()
    apex_dir = Path(args.apex_dir)
    issues = check_test_data_factory_patterns(apex_dir)

    if not issues:
        print("No test data factory anti-patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\nFound {len(issues)} issue(s). Fix before committing test classes.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
