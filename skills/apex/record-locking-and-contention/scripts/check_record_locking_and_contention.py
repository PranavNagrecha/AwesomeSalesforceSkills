#!/usr/bin/env python3
"""Checker script for Record Locking and Contention skill.

Scans Apex source files for common lock-contention anti-patterns:
- FOR UPDATE with excessive post-query logic
- Missing sort-before-DML in batch execute methods
- Synchronous retry loops for UNABLE_TO_LOCK_ROW
- FOR UPDATE in batch start queries

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_record_locking_and_contention.py [--help]
    python3 check_record_locking_and_contention.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for record locking and contention anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_apex_files(manifest_dir: Path) -> list[Path]:
    """Find all .cls and .trigger files under the manifest directory."""
    files: list[Path] = []
    for pattern in ("**/*.cls", "**/*.trigger"):
        files.extend(manifest_dir.glob(pattern))
    return sorted(files)


def check_for_update_in_batch_start(content: str, filepath: str) -> list[str]:
    """Detect FOR UPDATE inside Database.getQueryLocator calls."""
    issues: list[str] = []
    # Look for getQueryLocator containing FOR UPDATE
    pattern = re.compile(
        r"getQueryLocator\s*\([^)]*FOR\s+UPDATE",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(content):
        line_num = content[:match.start()].count("\n") + 1
        issues.append(
            f"{filepath}:{line_num} — FOR UPDATE in Database.getQueryLocator() "
            f"is not allowed and will throw a runtime error."
        )
    return issues


def check_sync_retry_loop(content: str, filepath: str) -> list[str]:
    """Detect synchronous retry loops catching UNABLE_TO_LOCK_ROW."""
    issues: list[str] = []
    # Look for while/for loops containing UNABLE_TO_LOCK_ROW catch
    loop_pattern = re.compile(
        r"(while|for)\s*\(.*\)\s*\{[^}]*UNABLE_TO_LOCK_ROW",
        re.IGNORECASE | re.DOTALL,
    )
    for match in loop_pattern.finditer(content):
        line_num = content[:match.start()].count("\n") + 1
        issues.append(
            f"{filepath}:{line_num} — Synchronous retry loop for UNABLE_TO_LOCK_ROW detected. "
            f"Use Queueable-based async retry instead."
        )
    return issues


def check_for_update_usage(content: str, filepath: str) -> list[str]:
    """Flag FOR UPDATE usage as an advisory to verify it is intentional."""
    issues: list[str] = []
    pattern = re.compile(r"\bFOR\s+UPDATE\b", re.IGNORECASE)
    matches = list(pattern.finditer(content))
    if len(matches) > 2:
        issues.append(
            f"{filepath} — {len(matches)} FOR UPDATE statements found. "
            f"Verify each is a deliberate read-modify-write pattern; "
            f"excessive FOR UPDATE increases contention."
        )
    return issues


def check_unsorted_batch_dml(content: str, filepath: str) -> list[str]:
    """Detect batch execute methods that perform DML without ORDER BY in start."""
    issues: list[str] = []
    # Only check files that implement Database.Batchable
    if "Database.Batchable" not in content:
        return issues

    # Check if start method has ORDER BY
    start_pattern = re.compile(
        r"(Database\.getQueryLocator|Database\.getQueryLocatorWithBinds)\s*\(\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    )
    for match in start_pattern.finditer(content):
        query = match.group(2)
        if "ORDER BY" not in query.upper():
            line_num = content[:match.start()].count("\n") + 1
            issues.append(
                f"{filepath}:{line_num} — Batch start query has no ORDER BY clause. "
                f"Add ORDER BY on a parent-key field to prevent lock contention "
                f"across parallel batch scopes."
            )
    return issues


def check_record_locking_and_contention(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_apex_files(manifest_dir)
    if not apex_files:
        issues.append(
            f"No Apex files (.cls, .trigger) found under {manifest_dir}. "
            f"Point --manifest-dir at the force-app or src directory."
        )
        return issues

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        filepath = str(apex_file)
        issues.extend(check_for_update_in_batch_start(content, filepath))
        issues.extend(check_sync_retry_loop(content, filepath))
        issues.extend(check_for_update_usage(content, filepath))
        issues.extend(check_unsorted_batch_dml(content, filepath))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_record_locking_and_contention(manifest_dir)

    if not issues:
        print("No record-locking anti-patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
