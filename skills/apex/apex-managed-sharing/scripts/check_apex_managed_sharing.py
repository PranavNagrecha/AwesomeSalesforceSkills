#!/usr/bin/env python3
"""Checker script for Apex Managed Sharing skill.

Scans Apex class files (.cls) for common Apex managed sharing patterns and
anti-patterns described in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_managed_sharing.py [--help]
    python3 check_apex_managed_sharing.py --manifest-dir path/to/force-app

Checks performed:
  1. Detects share inserts (insert.*Share) and warns if no DUPLICATE_VALUE
     guard pattern (Database.insert with false, or pre-query) is nearby.
  2. Detects classes that implement Database.Batchable and insert share records
     but are NOT declared without sharing.
  3. Detects share inserts that use AccessLevel = 'All' (invalid at runtime).
  4. Detects share inserts using RowCause = 'Manual' on custom Share objects
     (warns that grants won't survive manual recalculation).
  5. Reports Apex classes that insert share records but have no corresponding
     delete (potential share row accumulation / DUPLICATE_VALUE risk).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches lines that insert a Share sObject: insert <varname> where var or
# list type ends in Share or __Share
RE_SHARE_INSERT = re.compile(
    r'\binsert\b.*\bShare\b',
    re.IGNORECASE,
)

# Detects Database.insert( with allOrNone=false (safe pattern)
RE_DB_INSERT_FALSE = re.compile(
    r'Database\.insert\s*\([^)]+,\s*false\s*\)',
    re.IGNORECASE,
)

# Detects Database.Batchable implementation
RE_BATCHABLE = re.compile(
    r'implements\s+Database\.Batchable',
    re.IGNORECASE,
)

# Detects without sharing declaration
RE_WITHOUT_SHARING = re.compile(
    r'\bwithout\s+sharing\b',
    re.IGNORECASE,
)

# Detects AccessLevel = 'All'  (invalid for Apex share inserts)
RE_ACCESS_LEVEL_ALL = re.compile(
    r'''AccessLevel\s*=\s*['"]All['"]\s*''',
    re.IGNORECASE,
)

# Detects RowCause = 'Manual' on a custom Share object line
# Looks for __Share context somewhere in the class + RowCause = 'Manual'
RE_ROW_CAUSE_MANUAL = re.compile(
    r'''RowCause\s*=\s*['"]Manual['"]\s*''',
    re.IGNORECASE,
)

# Detects delete of a Share object
RE_SHARE_DELETE = re.compile(
    r'\bdelete\b.*\bShare\b',
    re.IGNORECASE,
)

# Detects custom __Share object (vs. standard Share)
RE_CUSTOM_SHARE = re.compile(
    r'\b\w+__Share\b',
)


# ---------------------------------------------------------------------------
# Per-file analysis
# ---------------------------------------------------------------------------

def analyse_file(path: Path) -> list[str]:
    """Return a list of issue strings for a single Apex class file."""
    issues: list[str] = []

    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    lines = source.splitlines()
    has_share_insert = bool(RE_SHARE_INSERT.search(source))
    has_share_delete = bool(RE_SHARE_DELETE.search(source))
    has_db_insert_false = bool(RE_DB_INSERT_FALSE.search(source))
    has_batchable = bool(RE_BATCHABLE.search(source))
    has_without_sharing = bool(RE_WITHOUT_SHARING.search(source))
    has_custom_share = bool(RE_CUSTOM_SHARE.search(source))

    # Check 1: Share insert without safe Database.insert(list, false) pattern
    if has_share_insert and not has_db_insert_false:
        issues.append(
            f"{path.name}: Share insert detected but Database.insert(list, false) "
            "not found. Raw 'insert' on Share objects throws on DUPLICATE_VALUE "
            "and rolls back the transaction. Use Database.insert(list, false) and "
            "inspect SaveResult errors."
        )

    # Check 2: Batchable class that inserts shares but is NOT without sharing
    if has_batchable and has_share_insert and not has_without_sharing:
        issues.append(
            f"{path.name}: Class implements Database.Batchable and inserts Share "
            "records but is NOT declared 'without sharing'. The start() query will "
            "silently exclude records the running user cannot see, producing "
            "incomplete share coverage. Declare the class 'without sharing'."
        )

    # Check 3: AccessLevel = 'All'
    for i, line in enumerate(lines, start=1):
        if RE_ACCESS_LEVEL_ALL.search(line):
            issues.append(
                f"{path.name}:{i}: AccessLevel = 'All' is invalid for Share inserts "
                "and causes a runtime DmlException. Valid values are 'Read' and 'Edit'."
            )

    # Check 4: RowCause = 'Manual' on a custom Share object
    if has_custom_share and RE_ROW_CAUSE_MANUAL.search(source):
        issues.append(
            f"{path.name}: Custom Share object (__Share) uses RowCause = 'Manual'. "
            "Manual row causes are cleared during manual sharing recalculation. "
            "Create an Apex sharing reason in Setup and use the custom row cause "
            "constant (e.g., Object__Share.rowCause.MyReason__c) instead."
        )

    # Check 5: Share inserts without any corresponding delete (accumulation risk)
    if has_share_insert and not has_share_delete:
        issues.append(
            f"{path.name}: Share inserts found but no Share deletes found in this "
            "class. If shares are never cleaned up, duplicate row causes accumulate "
            "and DUPLICATE_VALUE errors will appear on re-run. Ensure a companion "
            "delete path exists (trigger on delete, or recalculation class)."
        )

    return issues


# ---------------------------------------------------------------------------
# Directory scan
# ---------------------------------------------------------------------------

def check_apex_managed_sharing(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found across all .cls files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    cls_files = list(manifest_dir.rglob('*.cls'))
    if not cls_files:
        issues.append(
            f"No .cls files found under {manifest_dir}. "
            "Pass the root of your Salesforce source directory with --manifest-dir."
        )
        return issues

    share_files_found = 0
    for cls_file in cls_files:
        source_peek = cls_file.read_text(encoding='utf-8', errors='replace')
        if not RE_SHARE_INSERT.search(source_peek) and not RE_SHARE_DELETE.search(source_peek):
            # Skip files that have no sharing-related code at all
            continue
        share_files_found += 1
        file_issues = analyse_file(cls_file)
        issues.extend(file_issues)

    if share_files_found == 0:
        # Not necessarily a problem — org may not use Apex managed sharing
        print(
            f"INFO: No Apex classes with Share inserts or deletes found under "
            f"{manifest_dir}. If this org uses Apex managed sharing, verify the "
            f"--manifest-dir path points to the Apex classes directory."
        )

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex classes for common Apex managed sharing issues: "
            "missing DUPLICATE_VALUE guards, missing 'without sharing' on "
            "recalculation batches, invalid AccessLevel values, and share row "
            "accumulation risk."
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help=(
            'Root directory of the Salesforce source (default: current directory). '
            'Scans all .cls files recursively.'
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_apex_managed_sharing(manifest_dir)

    if not issues:
        print('No Apex managed sharing issues found.')
        return 0

    for issue in issues:
        print(f'ISSUE: {issue}')

    return 1


if __name__ == '__main__':
    sys.exit(main())
