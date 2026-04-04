#!/usr/bin/env python3
"""Checker script for Apex Scheduled Jobs skill.

Statically analyzes Apex source files in a metadata directory for common
Scheduled Apex anti-patterns and structural issues.

This file is the canonical entry point used by the skill validation pipeline.
It delegates to check_apex_scheduled.py for the implementation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_scheduled_jobs.py [--manifest-dir path/to/metadata]
    python3 check_apex_scheduled_jobs.py --help

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Detects classes that implement Schedulable
SCHEDULABLE_CLASS_RE = re.compile(
    r'\bimplements\b[^{]*\bSchedulable\b',
    re.IGNORECASE,
)

# Detects execute() method signature within a Schedulable class
EXECUTE_METHOD_RE = re.compile(
    r'\bvoid\s+execute\s*\(\s*SchedulableContext\b',
    re.IGNORECASE,
)

# Detects global class declaration (required for Schedulable)
GLOBAL_CLASS_RE = re.compile(
    r'\bglobal\s+(virtual\s+|abstract\s+)?class\b',
    re.IGNORECASE,
)

# Detects inline SOQL — [ SELECT pattern
INLINE_SOQL_RE = re.compile(
    r'\[\s*SELECT\b',
    re.IGNORECASE,
)

# Detects Database.executeBatch or System.enqueueJob dispatch calls
DISPATCH_RE = re.compile(
    r'\b(Database\.executeBatch|System\.enqueueJob)\s*\(',
    re.IGNORECASE,
)

# Detects direct Http callout construction
CALLOUT_RE = re.compile(
    r'\b(new\s+Http\b|new\s+HttpRequest\b|Http\(\)\.send\b)',
    re.IGNORECASE,
)

# Detects System.schedule() calls
SYSTEM_SCHEDULE_RE = re.compile(
    r'\bSystem\.schedule\s*\(',
    re.IGNORECASE,
)

# Detects inline DML keywords
INLINE_DML_RE = re.compile(
    r'\b(insert|update|delete|upsert|merge|undelete)\s+\w',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File-level analysis
# ---------------------------------------------------------------------------

def analyze_apex_file(path: Path) -> list[str]:
    """Return a list of issue strings for a single Apex file."""
    issues: list[str] = []
    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    if not SCHEDULABLE_CLASS_RE.search(source):
        return issues

    label = str(path)

    # 1. Class must be declared global
    if not GLOBAL_CLASS_RE.search(source):
        issues.append(
            f"{label}: Schedulable class is not declared 'global'. "
            "The Schedulable interface requires a global class declaration."
        )

    # 2. execute() method must be present
    if not EXECUTE_METHOD_RE.search(source):
        issues.append(
            f"{label}: No execute(SchedulableContext) method found. "
            "Every Schedulable class must implement this method."
        )

    # 3. Warn if no dispatch call but there is inline SOQL or DML
    has_dispatch = bool(DISPATCH_RE.search(source))
    has_inline_soql = bool(INLINE_SOQL_RE.search(source))
    has_inline_dml = bool(INLINE_DML_RE.search(source))

    if not has_dispatch and (has_inline_soql or has_inline_dml):
        issues.append(
            f"{label}: Schedulable class contains SOQL or DML but no "
            "Database.executeBatch() or System.enqueueJob() dispatch call. "
            "Delegate heavy work to Batch Apex or a Queueable to avoid governor "
            "limit failures as data volume grows."
        )

    # 4. Warn on direct HTTP callouts
    if CALLOUT_RE.search(source):
        issues.append(
            f"{label}: Possible direct HTTP callout detected in a Schedulable class. "
            "Callouts from Scheduled Apex throw a runtime CalloutException. "
            "Delegate callout work to a @future(callout=true) method or a Queueable "
            "implementing Database.AllowsCallouts."
        )

    # 5. Warn if System.schedule() appears alongside an execute() method
    if EXECUTE_METHOD_RE.search(source) and SYSTEM_SCHEDULE_RE.search(source):
        issues.append(
            f"{label}: System.schedule() call detected in a file that also contains "
            "an execute(SchedulableContext) method. Calling System.schedule() from "
            "within execute() throws System.AsyncException at runtime. "
            "If rescheduling is needed, delegate to a Queueable."
        )

    return issues


# ---------------------------------------------------------------------------
# Directory walk
# ---------------------------------------------------------------------------

def check_apex_scheduled_jobs(manifest_dir: Path) -> list[str]:
    """Walk manifest_dir and analyze all .cls Apex files for Schedulable issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = list(manifest_dir.rglob('*.cls'))

    for apex_file in sorted(apex_files):
        file_issues = analyze_apex_file(apex_file)
        issues.extend(file_issues)

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex source files for common Scheduled Apex anti-patterns. "
            "Analyzes .cls files under the manifest directory for structural "
            "issues with classes implementing the Schedulable interface."
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help='Root directory of the Salesforce metadata / project source (default: current directory).',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_apex_scheduled_jobs(manifest_dir)

    if not issues:
        print('No Apex Scheduled Jobs issues found.')
        return 0

    for issue in issues:
        print(f'ISSUE: {issue}')

    return 1


if __name__ == '__main__':
    sys.exit(main())
