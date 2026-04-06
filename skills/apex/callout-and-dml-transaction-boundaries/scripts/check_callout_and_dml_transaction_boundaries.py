#!/usr/bin/env python3
"""Checker script for Callout and DML Transaction Boundaries skill.

Scans Apex source files for patterns that mix DML and callouts in the same
synchronous method, trigger handlers making direct callouts, and Queueable
classes that make callouts without implementing Database.AllowsCallouts.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_callout_and_dml_transaction_boundaries.py [--help]
    python3 check_callout_and_dml_transaction_boundaries.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for callout-after-DML anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# Patterns
DML_PATTERN = re.compile(
    r"\b(insert|update|upsert|delete|undelete|Database\.(insert|update|upsert|delete|undelete))\b",
    re.IGNORECASE,
)
EVENTBUS_PATTERN = re.compile(r"\bEventBus\.publish\b", re.IGNORECASE)
CALLOUT_PATTERN = re.compile(r"\bnew\s+Http\s*\(\s*\)\s*\.\s*send\b", re.IGNORECASE)
HTTP_REQUEST_PATTERN = re.compile(r"\bnew\s+HttpRequest\s*\(", re.IGNORECASE)
TRIGGER_HANDLER_PATTERN = re.compile(
    r"\b(afterInsert|afterUpdate|beforeInsert|beforeUpdate|afterDelete|beforeDelete)\b"
)
QUEUEABLE_DECL = re.compile(r"\bimplements\b[^{]*\bQueueable\b", re.IGNORECASE)
ALLOWS_CALLOUTS_DECL = re.compile(
    r"\bimplements\b[^{]*\bDatabase\.AllowsCallouts\b", re.IGNORECASE
)
ROLLBACK_PATTERN = re.compile(r"\bDatabase\.rollback\b", re.IGNORECASE)


def _has_callout(content: str) -> bool:
    return bool(CALLOUT_PATTERN.search(content) or HTTP_REQUEST_PATTERN.search(content))


def _has_dml(content: str) -> bool:
    return bool(DML_PATTERN.search(content) or EVENTBUS_PATTERN.search(content))


def check_file(filepath: Path) -> list[str]:
    """Check a single Apex class file for boundary violations."""
    issues: list[str] = []
    content = filepath.read_text(encoding="utf-8", errors="replace")
    rel = filepath.name

    # Check 1: Queueable without Database.AllowsCallouts that has callout code
    if QUEUEABLE_DECL.search(content) and _has_callout(content):
        if not ALLOWS_CALLOUTS_DECL.search(content):
            issues.append(
                f"{rel}: Queueable class makes callouts but does not implement "
                f"Database.AllowsCallouts."
            )

    # Check 2: Trigger handler method with direct callout
    if TRIGGER_HANDLER_PATTERN.search(content) and _has_callout(content):
        # Only flag if there is no System.enqueueJob wrapping the callout
        if "System.enqueueJob" not in content:
            issues.append(
                f"{rel}: Trigger handler method appears to make a direct callout. "
                f"Callouts in trigger context will fail because the triggering DML "
                f"is uncommitted. Move callout to a Queueable."
            )

    # Check 3: Database.rollback() before callout in same file
    if ROLLBACK_PATTERN.search(content) and _has_callout(content):
        issues.append(
            f"{rel}: Uses Database.rollback() in a file that also makes callouts. "
            f"Rollback does not clear the uncommitted-work flag for callout purposes."
        )

    # Check 4: DML + callout in same file without async boundary
    # This is a heuristic — flag only if there is no enqueueJob or @future
    if _has_dml(content) and _has_callout(content):
        has_async = (
            "System.enqueueJob" in content
            or "@future" in content
            or QUEUEABLE_DECL.search(content)
        )
        if not has_async:
            issues.append(
                f"{rel}: Contains both DML operations and HTTP callouts without an "
                f"async boundary. Verify that callouts always execute before DML in "
                f"every code path, or move callouts to a Queueable."
            )

    return issues


def check_callout_and_dml_transaction_boundaries(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = list(manifest_dir.rglob("*.cls"))
    trigger_files = list(manifest_dir.rglob("*.trigger"))
    all_files = apex_files + trigger_files

    if not all_files:
        # No Apex files found is not an error — may be a non-Apex project
        return issues

    for f in all_files:
        issues.extend(check_file(f))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_callout_and_dml_transaction_boundaries(manifest_dir)

    if not issues:
        print("No callout/DML boundary issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
