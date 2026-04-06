#!/usr/bin/env python3
"""Checker script for Mixed DML and Setup Objects skill.

Scans Apex source files for patterns that indicate potential MIXED_DML_OPERATION
violations: setup-object DML (User, UserRole, Group, GroupMember, PermissionSet,
PermissionSetAssignment, QueueSObject) occurring in the same method as
non-setup-object DML without System.runAs() isolation.

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_mixed_dml_and_setup_objects.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Setup objects that trigger the mixed DML restriction
SETUP_OBJECTS = {
    "user",
    "userrole",
    "group",
    "groupmember",
    "permissionset",
    "permissionsetassignment",
    "permissionsetgroup",
    "queuesobject",
    "objectterritory2association",
    "territory2",
    "userterritory2association",
    "userpackagelicense",
}

# DML keywords to detect
DML_KEYWORDS = re.compile(
    r"\b(insert|update|upsert|delete|undelete)\b", re.IGNORECASE
)

# Pattern to detect System.runAs(
RUN_AS_PATTERN = re.compile(r"\bSystem\.runAs\s*\(", re.IGNORECASE)

# Pattern to detect @future annotation
FUTURE_PATTERN = re.compile(r"@future", re.IGNORECASE)

# Pattern to detect @IsTest or @isTest
IS_TEST_PATTERN = re.compile(r"@isTest|@IsTest|testMethod", re.IGNORECASE)

# Pattern to detect new SObject() or SObject variable in DML context
SOBJECT_IN_DML = re.compile(
    r"\b(insert|update|upsert|delete|undelete)\s+(\w+)", re.IGNORECASE
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for potential mixed DML violations.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_apex_files(root: Path) -> list[Path]:
    """Find all .cls files under the root directory."""
    return sorted(root.rglob("*.cls"))


def is_setup_object_reference(line: str) -> bool:
    """Check if a line references a setup object in a DML context."""
    lower = line.lower().strip()
    # Skip comments
    if lower.startswith("//") or lower.startswith("*") or lower.startswith("/*"):
        return False
    for obj in SETUP_OBJECTS:
        # Match: new User(...), variable typed as User, etc.
        if re.search(rf"\bnew\s+{obj}\s*\(", lower):
            return True
        # Match DML on a variable that is clearly typed as a setup object
        if re.search(rf"\b{obj}\b", lower) and DML_KEYWORDS.search(lower):
            return True
    return False


def has_non_setup_dml(line: str) -> bool:
    """Check if a line has DML that is clearly not on a setup object."""
    lower = line.lower().strip()
    if lower.startswith("//") or lower.startswith("*") or lower.startswith("/*"):
        return False
    if not DML_KEYWORDS.search(lower):
        return False
    # If it references a setup object, it's setup DML, not non-setup
    for obj in SETUP_OBJECTS:
        if re.search(rf"\b{obj}\b", lower):
            return False
    return True


def check_file(filepath: Path) -> list[str]:
    """Check a single Apex file for potential mixed DML issues."""
    issues: list[str] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    lines = content.split("\n")
    is_test_class = bool(IS_TEST_PATTERN.search(content))

    # Simple heuristic: look for files that have both setup and non-setup DML
    has_setup = False
    has_nonsetup = False
    has_runas = bool(RUN_AS_PATTERN.search(content))
    has_future = bool(FUTURE_PATTERN.search(content))
    setup_lines: list[int] = []
    nonsetup_lines: list[int] = []

    for i, line in enumerate(lines, 1):
        if is_setup_object_reference(line):
            has_setup = True
            setup_lines.append(i)
        if has_non_setup_dml(line):
            has_nonsetup = True
            nonsetup_lines.append(i)

    if has_setup and has_nonsetup:
        if is_test_class and not has_runas:
            issues.append(
                f"{filepath.name}: Test class has both setup-object DML "
                f"(lines {setup_lines[:3]}) and non-setup DML "
                f"(lines {nonsetup_lines[:3]}) but no System.runAs() — "
                f"likely MIXED_DML_OPERATION risk."
            )
        elif not is_test_class and not has_future:
            issues.append(
                f"{filepath.name}: Non-test class has both setup-object DML "
                f"(lines {setup_lines[:3]}) and non-setup DML "
                f"(lines {nonsetup_lines[:3]}) without @future — "
                f"likely MIXED_DML_OPERATION risk."
            )

    return issues


def check_mixed_dml_and_setup_objects(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_apex_files(manifest_dir)
    if not apex_files:
        # Not an error — the project may not have Apex classes
        return issues

    for f in apex_files:
        issues.extend(check_file(f))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_mixed_dml_and_setup_objects(manifest_dir)

    if not issues:
        print("No mixed DML issues detected.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
