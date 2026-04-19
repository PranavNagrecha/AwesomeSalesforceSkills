#!/usr/bin/env python3
"""Checker script for Apex DML Patterns skill.

Scans Apex source files for common DML anti-patterns:
- DML statements inside loops
- Database.insert/update with allOrNone=false but no SaveResult check
- Database.merge usage (flags for manual review — restricted to Account/Contact/Lead)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_dml_patterns.py [--help]
    python3 check_apex_dml_patterns.py --manifest-dir path/to/apex/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex classes for DML anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Apex .cls files (default: current directory).",
    )
    return parser.parse_args()


DML_STATEMENTS = re.compile(
    r'\b(insert|update|delete|upsert|merge|undelete)\b\s+\w',
    re.IGNORECASE
)
FOR_LOOP = re.compile(r'\bfor\s*\(', re.IGNORECASE)
PARTIAL_SUCCESS = re.compile(
    r'Database\.(insert|update|delete|upsert)\s*\([^,]+,\s*false\s*\)',
    re.IGNORECASE
)
SAVE_RESULT_CHECK = re.compile(r'\.isSuccess\s*\(\s*\)', re.IGNORECASE)
DATABASE_MERGE = re.compile(r'Database\.merge\s*\(', re.IGNORECASE)


def check_dml_in_loops(content: str, filepath: Path) -> list[str]:
    """Detect DML statements that appear inside loop bodies (heuristic)."""
    issues = []
    lines = content.split('\n')
    brace_depth = 0
    loop_depths: list[int] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if FOR_LOOP.search(stripped) or re.search(r'\bwhile\s*\(', stripped, re.IGNORECASE):
            loop_depths.append(brace_depth + stripped.count('{') - stripped.count('}'))
        brace_depth += stripped.count('{') - stripped.count('}')
        # Clean depths that have closed
        loop_depths = [d for d in loop_depths if brace_depth > d]
        if loop_depths and DML_STATEMENTS.search(stripped):
            issues.append(
                f"{filepath}:{i+1}: DML statement inside a loop — "
                "collect records in a list and DML outside the loop"
            )
    return issues


def check_partial_success_no_result_check(content: str, filepath: Path) -> list[str]:
    """Warn when Database.insert(list, false) is used without SaveResult inspection."""
    issues = []
    if PARTIAL_SUCCESS.search(content) and not SAVE_RESULT_CHECK.search(content):
        issues.append(
            f"{filepath}: Database.insert/update/delete with allOrNone=false "
            "but no SaveResult.isSuccess() check found — errors may be silently ignored"
        )
    return issues


def check_database_merge(content: str, filepath: Path) -> list[str]:
    """Flag Database.merge usage for manual review (Account/Contact/Lead only)."""
    issues = []
    for m in DATABASE_MERGE.finditer(content):
        line_num = content[:m.start()].count('\n') + 1
        issues.append(
            f"{filepath}:{line_num}: Database.merge() detected — "
            "verify the object type is Account, Contact, or Lead (only supported types)"
        )
    return issues


def check_apex_files(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    cls_files = list(manifest_dir.rglob("*.cls"))
    for cls_file in cls_files:
        try:
            content = cls_file.read_text(encoding="utf-8")
        except OSError:
            continue
        issues.extend(check_dml_in_loops(content, cls_file))
        issues.extend(check_partial_success_no_result_check(content, cls_file))
        issues.extend(check_database_merge(content, cls_file))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    issues = check_apex_files(manifest_dir)

    if not issues:
        print("No DML pattern issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
