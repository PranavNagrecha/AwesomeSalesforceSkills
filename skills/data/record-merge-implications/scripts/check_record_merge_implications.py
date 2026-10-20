#!/usr/bin/env python3
"""Checker script for Record Merge Implications skill.

Scans Apex files for common record merge anti-patterns:
- Database.merge() calls without a preceding update (field copy risk; the main record's
  values, nulls included, supersede the duplicates', apexdev 264 L8349-8352)
- Lead merge queries missing IsConverted = false filter (the converted-Lead exclusion is
  UNVERIFIED (2026-10-20): Help-only, so this finding is INFO)

Exit codes: ERROR (missing directory) exits 1 always; WARN and INFO findings exit 0
unless --strict is given. A directory with no .cls files prints one WARN and exits 0.

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

# Database.merge(...) and the merge DML statement the guide's own example uses
# ("merge mainAcct dupAcct;", apexdev 264 L8220).
_MERGE_CALL = re.compile(r"Database\.merge\s*\(|^\s*merge\s+(?:as\s+(?:user|system)\s+)?\w+\s+\w+", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex files for record merge anti-patterns.",
    )
    parser.add_argument(
        "--source-dir",
        "--manifest-dir",
        dest="source_dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN and INFO findings to exit 1 (ERROR always exits 1).",
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
            if _MERGE_CALL.search(line):
                # Look back up to 20 lines for an 'update' call
                context_start = max(0, i - 20)
                context_lines = lines[context_start : i - 1]
                context = "\n".join(context_lines)
                if not re.search(r"\bupdate\b", context):
                    issues.append(
                        f"WARN: {apex_file}:{i}: Database.merge() called without a preceding "
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
        if not any(_MERGE_CALL.search(l) for l in content.splitlines()):
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
                    f"INFO: {apex_file}:{line_no}: Lead SOQL query near Database.merge() "
                    f"does not filter 'IsConverted = false'. Converted Leads are reported to be "
                    f"excluded from merges (UNVERIFIED (2026-10-20): Help-only, not in the corpus); "
                    f"consider adding 'AND IsConverted = false' to the WHERE clause."
                )
    except OSError:
        pass
    return issues


def check_apex_files(source_dir: Path) -> list[str]:
    """Return a list of issue strings found in Apex files under source_dir."""
    issues: list[str] = []

    if not source_dir.exists():
        issues.append(f"ERROR: Source directory not found: {source_dir}")
        return issues

    if not any(source_dir.rglob("*.cls")):
        issues.append(f"WARN: no .cls files under {source_dir}; nothing to check")
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
        print(issue)

    if any(i.startswith("ERROR:") for i in issues):
        sys.exit(1)
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
