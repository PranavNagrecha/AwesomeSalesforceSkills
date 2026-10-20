#!/usr/bin/env python3
"""Checker script for Apex Managed Sharing skill.

Scans Apex class files (.cls) for common Apex managed sharing patterns and
anti-patterns described in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_managed_sharing.py [--help]
    python3 check_apex_managed_sharing.py --manifest-dir path/to/force-app [--strict]

Exit codes: findings are WARN and exit 0 unless --strict; a directory with no .cls files
is one WARN and exit 0; a missing directory is ERROR and exit 1.

Checks performed:
  1. Detects share inserts and warns if no partial-success pattern
     (Database.insert(list, false[, AccessLevel])) is present.
  2. Detects classes that implement Database.Batchable and insert share records
     but are NOT declared without sharing.
  3. Detects share inserts that use AccessLevel = 'All' (invalid at runtime).
  4. Detects share inserts using RowCause = 'Manual' on custom Share objects
     (warns that Manual shares are removed when the record owner changes).
  5. Reports Apex classes that insert share records but have no corresponding
     delete (potential share row accumulation).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches lines that insert a Share sObject: the line names an identifier containing
# 'share' (Project__Share, AccountShare, shareList). The earlier \bShare\b form never
# matched __Share or AccountShare because underscore and letters are word characters.
RE_SHARE_INSERT = re.compile(
    r'\binsert\b[^;\n]*\w*share\w*',
    re.IGNORECASE,
)

# Detects Database.insert( with allOrNone=false (safe pattern), with or without the
# third AccessLevel argument the guide's samples pass (apex dev guide 264 L12788, L12978)
RE_DB_INSERT_FALSE = re.compile(
    r'Database\.insert\s*\([^)]+,\s*false\s*(?:,[^)]*)?\)',
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
    r'\bdelete\b[^;\n]*\w*share\w*',
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
            "not found. A raw 'insert' has no partial-success handling; the guide's "
            "samples use Database.insert(list, false, AccessLevel.USER_MODE) and "
            "inspect SaveResult errors (apex dev guide 264 L12975-12978)."
        )

    # Check 2: Batchable class that inserts shares but is NOT without sharing
    if has_batchable and has_share_insert and not has_without_sharing:
        issues.append(
            f"{path.name}: Class implements Database.Batchable and inserts Share "
            "records but is NOT declared 'without sharing'. The guide's recalculation "
            "sample is 'public without sharing' (apex dev guide 264 L13095); a "
            "'with sharing' start() query is limited to records the running user can see."
        )

    # Check 3: AccessLevel = 'All'
    for i, line in enumerate(lines, start=1):
        if RE_ACCESS_LEVEL_ALL.search(line):
            issues.append(
                f"{path.name}:{i}: AccessLevel = 'All' is invalid for Share inserts "
                "which the guide calls an internal value that can't be granted (apex dev guide 264 L12730). Use 'Read' or 'Edit'."
            )

    # Check 4: RowCause = 'Manual' on a custom Share object
    if has_custom_share and RE_ROW_CAUSE_MANUAL.search(source):
        issues.append(
            f"{path.name}: Custom Share object (__Share) uses RowCause = 'Manual'. "
            "Manual shares are removed when the record owner changes (apex dev guide 264 "
            "L12606, L12756-12757). Create an Apex sharing reason and use the custom row "
            "cause constant (e.g., Object__Share.rowCause.MyReason__c) instead."
        )

    # Check 5: Share inserts without any corresponding delete (accumulation risk)
    if has_share_insert and not has_share_delete:
        issues.append(
            f"{path.name}: Share inserts found but no Share deletes found in this "
            "class. If shares are never cleaned up, stale grants accumulate. Ensure a "
            "companion delete path exists (trigger on delete, or recalculation class)."
        )

    return issues


# ---------------------------------------------------------------------------
# Directory scan
# ---------------------------------------------------------------------------

def check_apex_managed_sharing(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found across all .cls files."""
    issues: list[str] = []

    cls_files = list(manifest_dir.rglob('*.cls'))

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
            "missing partial-success inserts, missing 'without sharing' on "
            "recalculation batches, invalid AccessLevel values, and share row "
            "accumulation risk."
        ),
    )
    parser.add_argument('--strict', action='store_true', help='Exit 1 on findings or when there is nothing to check.')
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

    if not manifest_dir.exists():
        print(f'ERROR: manifest directory not found: {manifest_dir}')
        sys.exit(1)

    if not list(manifest_dir.rglob('*.cls')):
        print(f'WARN: no .cls files found under {manifest_dir}; nothing to check.')
        return 1 if args.strict else 0

    issues = check_apex_managed_sharing(manifest_dir)

    if not issues:
        print('No Apex managed sharing issues found.')
        return 0

    for issue in issues:
        print(f'WARN: {issue}')

    return 1 if args.strict else 0


if __name__ == '__main__':
    sys.exit(main())
