#!/usr/bin/env python3
"""Checker script for Record Merge Implications skill.

Scans Apex files for common record merge anti-patterns:
- Database.merge() calls without a preceding update (field copy risk)
- Lead merge queries missing IsConverted = false filter

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_record_merge_implications.py [--help]
    python3 check_record_merge_implications.py --source-dir force-app/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for record merge anti-patterns.",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


def check_merge_without_field_copy(apex_file: Path) -> list[str]:
    """Warn if Database.merge() is called without a preceding update in the same method scope."""
    issues: list[str] = []
    try:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        # Find all lines with Database.merge()
        for i, line in enumerate(lines, start=1):
            if re.search(r"Database\.merge\s*\(", line):
                # Look back up to 20 lines for an 'update' call
                context_start = max(0, i - 20)
                context_lines = lines[context_start : i - 1]
                context = "\n".join(context_lines)
                if not re.search(r"\bupdate\b", context):
                    issues.append(
                        f"{apex_file}:{i}: Database.merge() called without a preceding "
                        f"'update' in the surrounding context — ensure field values from "
                        f"losing records are copied to the master record before merging."
                    )
    except OSError:
        pass
    return issues


def check_lead_merge_query_missing_converted_filter(apex_file: Path) -> list[str]:
    """Warn if a Lead SOQL query used near Database.merge() lacks IsConverted = false."""
    issues: list[str] = []
    try:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        # Only check files that use Database.merge() on Leads
        if "Database.merge" not in content:
            return issues
        # Find SOQL queries that select from Lead
        soql_pattern = re.compile(
            r"SELECT\s+[^;]+FROM\s+Lead\b[^;]*;",
            re.IGNORECASE | re.DOTALL,
        )
        for match in soql_pattern.finditer(content):
            query = match.group(0)
            if "IsConverted" not in query:
                # Get approximate line number
                line_no = content[: match.start()].count("\n") + 1
                issues.append(
                    f"{apex_file}:{line_no}: Lead SOQL query near Database.merge() "
                    f"does not filter 'IsConverted = false' — merging converted Leads "
                    f"raises FIELD_INTEGRITY_EXCEPTION. Add 'AND IsConverted = false' "
                    f"to the WHERE clause."
                )
    except OSError:
        pass
    return issues


def check_apex_files(source_dir: Path) -> list[str]:
    """Return a list of issue strings found in Apex files under source_dir."""
    issues: list[str] = []

    if not source_dir.exists():
        issues.append(f"Source directory not found: {source_dir}")
        return issues

    for apex_file in source_dir.rglob("*.cls"):
        issues.extend(check_merge_without_field_copy(apex_file))
        issues.extend(check_lead_merge_query_missing_converted_filter(apex_file))

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)
    issues = check_apex_files(source_dir)

    if not issues:
        print("No record merge anti-patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
