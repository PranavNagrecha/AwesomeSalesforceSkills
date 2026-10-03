#!/usr/bin/env python3
"""Checker script for Test Data Factory Patterns skill.

Scans Apex test files for test data anti-patterns:
- @isTest(SeeAllData=true) usage
- Missing @IsTest annotation on factory utility classes
- Hardcoded Salesforce IDs (Profile, RecordType)
- Per-record DML in loops (insert inside for loop)
- @testSetup in a class that also uses SeeAllData=true (not supported)
- Static variables assigned in @testSetup (reinitialized before each test method)
- Setup-object DML (UserRole, PermissionSetAssignment, GroupMember, User with
  UserRoleId) in a test class that never uses System.runAs
- Hardcoded Username literals with no unique suffix

Rules are grounded on the Apex Developer Guide v67.0 (Using Test Setup Methods,
sObjects That Cannot Be Used Together in DML Operations, Mixed DML Operations in
Test Methods, Using the runAs Method).

Correction (2026-10-03): the docstring of an earlier version promised a check
for "Contact-linked portal users" without System.runAs. The guide allows a User
insert alongside other sObjects when UserRoleId is null, so a role-less portal
user is not itself a mixed DML defect; the check now targets the setup objects
that do collide.

Uses stdlib only; no pip dependencies.

Usage:
    python3 check_test_data_factory_patterns.py [--help]
    python3 check_test_data_factory_patterns.py --apex-dir path/to/classes
    python3 check_test_data_factory_patterns.py --self-test
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
    parser.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    return parser.parse_args()


TESTSETUP_RE = re.compile(r"@testSetup", re.IGNORECASE)
SEEALL_RE = re.compile(r"SeeAllData\s*=\s*true", re.IGNORECASE)
SETUP_DML_RE = re.compile(r"new\s+(UserRole|PermissionSetAssignment|GroupMember|PermissionSet|QueueSObject)\s*\(|UserRoleId\s*=", re.IGNORECASE)
NON_SETUP_DML_RE = re.compile(r"\b(insert|update|upsert|delete)\s+(new\s+)?(Account|Contact|Case|Opportunity|Lead)\b|\binsert\s+new\s+(Account|Contact|Case|Opportunity|Lead)\s*\(", re.IGNORECASE)
USERNAME_LITERAL_RE = re.compile(r"Username\s*=\s*'[^']*'\s*[,)]", re.IGNORECASE)


def _testsetup_body(content: str) -> str:
    m = TESTSETUP_RE.search(content)
    if not m:
        return ""
    start = content.find("{", m.end())
    if start == -1:
        return ""
    depth = 0
    for i in range(start, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                return content[start:i]
    return content[start:]


def extra_checks(cls_file: Path, content: str) -> list[str]:
    issues: list[str] = []
    if TESTSETUP_RE.search(content) and SEEALL_RE.search(content):
        issues.append(
            f"{cls_file.name}: @testSetup in a class that uses SeeAllData=true. The Apex Developer Guide says "
            f"test setup methods aren't supported when the class or any test method has SeeAllData=true."
        )
    statics = set(re.findall(r"\bstatic\s+(?!void\b)[\w<>,\s]+?\s+(\w+)\s*;", content))
    body = _testsetup_body(content)
    for name in sorted(statics):
        if re.search(rf"\b{name}\s*=", body):
            issues.append(
                f"{cls_file.name}: static '{name}' is assigned in @testSetup. Static context is reinitialized "
                f"before every test method, so the value is lost; query the setup records instead."
            )
    if SETUP_DML_RE.search(content) and NON_SETUP_DML_RE.search(content) and "System.runAs" not in content:
        issues.append(
            f"{cls_file.name}: setup-object DML (UserRole, PermissionSetAssignment, GroupMember, PermissionSet, "
            f"or a User with UserRoleId) next to Account/Contact/Case DML with no System.runAs. Enclose the "
            f"setup DML in System.runAs to avoid mixed DML."
        )
    if USERNAME_LITERAL_RE.search(content):
        issues.append(
            f"{cls_file.name}: hardcoded Username literal. Build usernames with a unique suffix, as the Apex "
            f"Developer Guide runAs example does with DateTime.now().getTime()."
        )
    return issues


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

        issues.extend(extra_checks(cls_file, content))

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


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    good = scan_apex_files(here / "good")
    bad = scan_apex_files(here / "bad")
    expected = ["(SeeAllData=true) detected", "aren't supported", "is assigned in @testSetup",
                "setup-object DML", "hardcoded Username", "hardcoded Profile ID", "inside a for loop",
                "missing the @IsTest annotation"]
    missing = [e for e in expected if not any(e in issue for issue in bad)]
    print(f"good fixtures: {len(good)} issue(s) (expected 0)")
    for g in good:
        print(f"  unexpected: {g}")
    print(f"bad fixtures: {len(bad)} issue(s); missing expected: {missing or 'none'}")
    return 0 if not good and not missing else 1


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
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
