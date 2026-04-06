#!/usr/bin/env python3
"""Checker script for System Field Behavior and Audit skill.

Scans Apex classes and SOQL queries for common system-field anti-patterns:
  - Using LastModifiedDate instead of SystemModstamp in sync/delta queries
  - Querying IsDeleted without ALL ROWS
  - Attempting DML update on audit fields (CreatedDate, CreatedById)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_system_field_behavior_and_audit.py [--help]
    python3 check_system_field_behavior_and_audit.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex and SOQL for system-field anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# --- Pattern definitions ---

# Matches SOQL WHERE clauses using LastModifiedDate for filtering (likely delta sync)
RE_LMD_FILTER = re.compile(
    r"WHERE\s+.*LastModifiedDate\s*[><=!]",
    re.IGNORECASE,
)

# Matches IsDeleted in a query without ALL ROWS
RE_ISDELETED = re.compile(r"\bIsDeleted\b", re.IGNORECASE)
RE_ALL_ROWS = re.compile(r"\bALL\s+ROWS\b", re.IGNORECASE)

# Matches DML update attempts on audit fields
RE_AUDIT_FIELD_UPDATE = re.compile(
    r"\b(?:update|Database\.update)\b",
    re.IGNORECASE,
)
RE_AUDIT_FIELD_SET = re.compile(
    r"\.\s*(?:CreatedDate|CreatedById|LastModifiedDate|LastModifiedById)\s*=",
    re.IGNORECASE,
)


def check_apex_file(filepath: Path) -> list[str]:
    """Check a single Apex file for system-field anti-patterns."""
    issues: list[str] = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        # Check 1: LastModifiedDate used in WHERE clause (likely delta sync)
        if RE_LMD_FILTER.search(line):
            issues.append(
                f"{filepath}:{i}: SOQL filters on LastModifiedDate — "
                f"consider SystemModstamp for delta sync (indexed, captures all changes)"
            )

        # Check 2: IsDeleted referenced without ALL ROWS in the surrounding context
        if RE_ISDELETED.search(line):
            # Look at surrounding lines (up to 5 after) for ALL ROWS
            context_block = "\n".join(lines[max(0, i - 2) : min(len(lines), i + 5)])
            if not RE_ALL_ROWS.search(context_block):
                issues.append(
                    f"{filepath}:{i}: IsDeleted referenced without ALL ROWS — "
                    f"standard SOQL excludes deleted records regardless of IsDeleted filter"
                )

        # Check 3: Setting audit fields followed by update DML
        if RE_AUDIT_FIELD_SET.search(line):
            # Look ahead for update DML in the next 10 lines
            ahead_block = "\n".join(lines[i - 1 : min(len(lines), i + 10)])
            if RE_AUDIT_FIELD_UPDATE.search(ahead_block):
                issues.append(
                    f"{filepath}:{i}: Audit field assignment followed by update DML — "
                    f"CreatedDate/CreatedById can only be set on insert with Create Audit Fields permission"
                )

    return issues


def check_system_field_behavior_and_audit(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan all Apex class and trigger files
    apex_patterns = ["**/*.cls", "**/*.trigger"]
    files_found = False
    for pattern in apex_patterns:
        for filepath in manifest_dir.glob(pattern):
            files_found = True
            issues.extend(check_apex_file(filepath))

    if not files_found:
        # Not an error — the manifest may not contain Apex files
        pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_system_field_behavior_and_audit(manifest_dir)

    if not issues:
        print("No system-field anti-patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
