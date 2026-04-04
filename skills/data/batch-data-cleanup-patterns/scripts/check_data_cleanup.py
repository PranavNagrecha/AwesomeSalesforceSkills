#!/usr/bin/env python3
"""Checker script for Batch Data Cleanup Patterns skill.

Scans Apex (.cls) files in the target directory for common data cleanup
anti-patterns. Reports issues for:
  - delete DML or Database.delete() calls without a nearby emptyRecycleBin call
  - Database.executeBatch() calls without a Schedulable class in scope
  - @isTest(SeeAllData=true) on test classes that also contain delete logic
  - Bare 'delete scope' calls (allOrNone=true risk) in execute() methods

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cleanup.py [--help]
    python3 check_data_cleanup.py --manifest-dir path/to/force-app/main/default/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches delete DML: "delete someVar;" or "delete [SELECT ..."
_RE_DELETE_DML = re.compile(
    r'\bdelete\b\s+(?!\s*\()',  # 'delete ' not followed by '(' (which would be keyword delete)
    re.IGNORECASE,
)
# Matches Database.delete(...)
_RE_DB_DELETE = re.compile(r'\bDatabase\.delete\s*\(', re.IGNORECASE)
# Matches Database.emptyRecycleBin(...)
_RE_EMPTY_RECYCLE_BIN = re.compile(r'\bDatabase\.emptyRecycleBin\s*\(', re.IGNORECASE)
# Matches Database.executeBatch(...)
_RE_EXECUTE_BATCH = re.compile(r'\bDatabase\.executeBatch\s*\(', re.IGNORECASE)
# Matches Schedulable interface declaration
_RE_SCHEDULABLE = re.compile(r'\bimplements\b[^{]*\bSchedulable\b', re.IGNORECASE)
# Matches @isTest(SeeAllData=true)
_RE_SEE_ALL_DATA = re.compile(r'@isTest\s*\(\s*SeeAllData\s*=\s*true', re.IGNORECASE)
# Matches bare 'delete varName;' — the allOrNone=true default risk
_RE_BARE_DELETE = re.compile(r'^\s*delete\s+\w+\s*;', re.MULTILINE)
# Matches Database.Batchable implementation
_RE_BATCHABLE = re.compile(r'\bimplements\b[^{]*\bDatabase\.Batchable\b', re.IGNORECASE)


def _read_cls_files(directory: Path) -> list[tuple[Path, str]]:
    """Return (path, content) pairs for all .cls files found recursively."""
    results = []
    for cls_file in sorted(directory.rglob('*.cls')):
        try:
            content = cls_file.read_text(encoding='utf-8', errors='replace')
            results.append((cls_file, content))
        except OSError:
            pass
    return results


def check_delete_without_empty_recycle_bin(files: list[tuple[Path, str]]) -> list[str]:
    """Flag files that delete records but never call emptyRecycleBin."""
    issues = []
    for path, content in files:
        has_delete = _RE_DELETE_DML.search(content) or _RE_DB_DELETE.search(content)
        has_empty = _RE_EMPTY_RECYCLE_BIN.search(content)
        if has_delete and not has_empty:
            issues.append(
                f"{path}: contains delete DML but no Database.emptyRecycleBin() call — "
                "deleted records remain in the Recycle Bin and still count against storage."
            )
    return issues


def check_bare_delete_in_execute(files: list[tuple[Path, str]]) -> list[str]:
    """Flag bare 'delete varName;' in Batchable classes (allOrNone=true risk)."""
    issues = []
    for path, content in files:
        if not _RE_BATCHABLE.search(content):
            continue  # Not a batch class
        bare_deletes = _RE_BARE_DELETE.findall(content)
        if bare_deletes:
            issues.append(
                f"{path}: bare 'delete' statement found in a Database.Batchable class — "
                "use Database.delete(scope, false) to allow partial failure without aborting the chunk."
            )
    return issues


def check_see_all_data_with_delete(files: list[tuple[Path, str]]) -> list[str]:
    """Flag test classes that use SeeAllData=true and contain delete logic."""
    issues = []
    for path, content in files:
        if not _RE_SEE_ALL_DATA.search(content):
            continue
        has_delete = _RE_DELETE_DML.search(content) or _RE_DB_DELETE.search(content)
        if has_delete:
            issues.append(
                f"{path}: @isTest(SeeAllData=true) combined with delete logic — "
                "this can delete real org records in the test environment. "
                "Use @TestSetup with explicitly inserted data instead."
            )
    return issues


def check_execute_batch_without_schedulable(files: list[tuple[Path, str]]) -> list[str]:
    """Warn if Database.executeBatch() appears in a file without a Schedulable class nearby."""
    # Collect all files that implement Schedulable
    schedulable_files = {path for path, content in files if _RE_SCHEDULABLE.search(content)}

    issues = []
    for path, content in files:
        if not _RE_EXECUTE_BATCH.search(content):
            continue
        if path in schedulable_files:
            continue  # This file itself is a Schedulable dispatcher — OK
        # Check if any file in the same directory is a Schedulable
        sibling_schedulable = any(
            p.parent == path.parent for p in schedulable_files
        )
        if not sibling_schedulable:
            issues.append(
                f"{path}: Database.executeBatch() found but no Schedulable class detected "
                "in the same directory — ensure a Schedulable wrapper registers this batch "
                "via System.schedule() for automated nightly execution."
            )
    return issues


def check_batch_data_cleanup_patterns(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    files = _read_cls_files(manifest_dir)
    if not files:
        # No .cls files found — not necessarily an error; just report
        return issues

    issues.extend(check_delete_without_empty_recycle_bin(files))
    issues.extend(check_bare_delete_in_execute(files))
    issues.extend(check_see_all_data_with_delete(files))
    issues.extend(check_execute_batch_without_schedulable(files))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Apex classes for batch data cleanup anti-patterns. "
            "Scans .cls files for delete-without-emptyRecycleBin, bare delete DML "
            "in batch classes, SeeAllData=true in deletion tests, and missing "
            "Schedulable wrappers."
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help='Root directory containing Apex .cls files (default: current directory).',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_batch_data_cleanup_patterns(manifest_dir)

    if not issues:
        print('No batch data cleanup issues found.')
        return 0

    for issue in issues:
        print(f'ISSUE: {issue}')

    return 1


if __name__ == '__main__':
    sys.exit(main())
