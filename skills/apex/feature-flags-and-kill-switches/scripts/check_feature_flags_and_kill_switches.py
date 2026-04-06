#!/usr/bin/env python3
"""Checker script for Feature Flags And Kill Switches skill.

Scans Apex source files for common feature flag anti-patterns:
- DML operations on Custom Metadata Types (__mdt)
- Missing null checks on getInstance() calls
- SOQL queries on CMDT instead of getInstance()
- Nonexistent UserInfo.hasPermission() calls
- Custom Object usage for flag storage patterns

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_feature_flags_and_kill_switches.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for feature flag and kill switch anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


def find_apex_files(root: Path) -> list[Path]:
    """Recursively find all .cls and .trigger files."""
    files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        files.extend(root.rglob(ext))
    return sorted(files)


def check_dml_on_cmdt(content: str, filepath: str) -> list[str]:
    """Detect insert/update/delete/upsert on Custom Metadata Type objects."""
    issues: list[str] = []
    # Match DML keywords followed by something ending in __mdt
    pattern = re.compile(
        r'\b(insert|update|delete|upsert)\s+.*?__mdt', re.IGNORECASE
    )
    for i, line in enumerate(content.splitlines(), start=1):
        if pattern.search(line):
            issues.append(
                f"{filepath}:{i} — DML operation on Custom Metadata Type. "
                "CMDT records cannot be modified via DML; use Metadata API instead."
            )
    return issues


def check_missing_null_check(content: str, filepath: str) -> list[str]:
    """Detect direct property access on getInstance() without null check."""
    issues: list[str] = []
    # Pattern: something__mdt.getInstance(...).SomeField__c on a single line
    pattern = re.compile(
        r'\w+__mdt\.getInstance\([^)]*\)\.\w+', re.IGNORECASE
    )
    for i, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        # Skip comments
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if pattern.search(line):
            issues.append(
                f"{filepath}:{i} — Direct property access on getInstance() without "
                "null check. If the record does not exist, this throws NullPointerException. "
                "Assign to a variable and null-check first."
            )
    return issues


def check_soql_on_cmdt(content: str, filepath: str) -> list[str]:
    """Detect SOQL queries on Custom Metadata Types."""
    issues: list[str] = []
    pattern = re.compile(
        r'SELECT\s+.*?\s+FROM\s+\w+__mdt', re.IGNORECASE
    )
    for i, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if pattern.search(line):
            issues.append(
                f"{filepath}:{i} — SOQL query on Custom Metadata Type. "
                "Use getInstance() or getAll() instead — they are cached and free of SOQL limits."
            )
    return issues


def check_userinfo_haspermission(content: str, filepath: str) -> list[str]:
    """Detect the nonexistent UserInfo.hasPermission() method."""
    issues: list[str] = []
    pattern = re.compile(r'UserInfo\.(hasPermission|checkPermission)\s*\(', re.IGNORECASE)
    for i, line in enumerate(content.splitlines(), start=1):
        if pattern.search(line):
            issues.append(
                f"{filepath}:{i} — UserInfo does not have hasPermission() or "
                "checkPermission(). Use FeatureManagement.checkPermission() instead."
            )
    return issues


def check_custom_object_as_flag(content: str, filepath: str) -> list[str]:
    """Detect Custom Object patterns that look like feature flag storage."""
    issues: list[str] = []
    # Heuristic: SOQL on an object named *Flag* or *Feature* with IsEnabled or Is_Enabled
    pattern = re.compile(
        r'SELECT\s+.*?Is_?Enabled.*?\s+FROM\s+\w+__c\b', re.IGNORECASE
    )
    for i, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if pattern.search(line):
            issues.append(
                f"{filepath}:{i} — Possible feature flag stored in a Custom Object (__c). "
                "Consider using Custom Metadata Types (__mdt) for cached, deployable flags."
            )
    return issues


def check_feature_flags_and_kill_switches(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_apex_files(manifest_dir)
    if not apex_files:
        issues.append(
            f"No Apex files (.cls, .trigger) found under {manifest_dir}. "
            "Verify the --manifest-dir points to the Salesforce source root."
        )
        return issues

    checkers = [
        check_dml_on_cmdt,
        check_missing_null_check,
        check_soql_on_cmdt,
        check_userinfo_haspermission,
        check_custom_object_as_flag,
    ]

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            issues.append(f"Could not read {apex_file}: {e}")
            continue

        rel_path = str(apex_file)
        for checker in checkers:
            issues.extend(checker(content, rel_path))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_feature_flags_and_kill_switches(manifest_dir)

    if not issues:
        print("No feature flag anti-patterns found.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for issue in issues:
        print(f"  ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
