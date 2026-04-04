#!/usr/bin/env python3
"""Checker script for Debug Logs And Developer Console skill.

Scans Apex source files in a Salesforce project for common debug-log anti-patterns:
- Excessive System.debug calls (more than 10 per class/trigger)
- System.debug calls without a LoggingLevel parameter (defaults to DEBUG, noisy)
- Hard-coded string concatenation inside System.debug calls (performance hit)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_debug_logs_and_developer_console.py [--help]
    python3 check_debug_logs_and_developer_console.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Matches System.debug( without a LoggingLevel argument
# e.g. System.debug('foo') — missing the LoggingLevel.INFO, ... pattern
SYSTEM_DEBUG_NO_LEVEL = re.compile(
    r'\bSystem\.debug\s*\(\s*(?!LoggingLevel\.)',
    re.IGNORECASE,
)

# Matches System.debug calls at all (for counting)
SYSTEM_DEBUG_ANY = re.compile(r'\bSystem\.debug\s*\(', re.IGNORECASE)

# Matches string concatenation inside System.debug
SYSTEM_DEBUG_CONCAT = re.compile(
    r'\bSystem\.debug\s*\([^)]*\+[^)]*\)',
    re.IGNORECASE,
)

APEX_EXTENSIONS = {'.cls', '.trigger'}
DEBUG_PER_FILE_THRESHOLD = 10


def check_apex_file(path: Path) -> list[str]:
    """Return issues found in a single Apex source file."""
    issues: list[str] = []
    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    lines = source.splitlines()
    debug_count = len(SYSTEM_DEBUG_ANY.findall(source))

    if debug_count > DEBUG_PER_FILE_THRESHOLD:
        issues.append(
            f"{path}: {debug_count} System.debug calls — consider a logging framework "
            f"(threshold: {DEBUG_PER_FILE_THRESHOLD})"
        )

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('*'):
            continue
        if SYSTEM_DEBUG_NO_LEVEL.search(line):
            issues.append(
                f"{path}:{i}: System.debug without LoggingLevel — "
                "add LoggingLevel.DEBUG (or appropriate level) as first argument "
                "to enable log-level filtering"
            )
        if SYSTEM_DEBUG_CONCAT.search(line):
            issues.append(
                f"{path}:{i}: String concatenation inside System.debug — "
                "this evaluates the concatenation even when logging is off; "
                "use lazy formatting or remove the debug call"
            )

    return issues


def find_apex_files(manifest_dir: Path) -> list[Path]:
    """Recursively find all Apex class and trigger files under manifest_dir."""
    return [
        p for p in manifest_dir.rglob('*')
        if p.suffix in APEX_EXTENSIONS and p.is_file()
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Apex source for common debug-log anti-patterns: "
            "excessive System.debug calls, missing LoggingLevel parameters, "
            "and string concatenation inside debug statements."
        ),
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help='Root directory of the Salesforce project (default: current directory).',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ISSUE: Manifest directory not found: {manifest_dir}")
        return 1

    apex_files = find_apex_files(manifest_dir)

    if not apex_files:
        print(f"No Apex files found under {manifest_dir}. Nothing to check.")
        return 0

    all_issues: list[str] = []
    for apex_file in sorted(apex_files):
        all_issues.extend(check_apex_file(apex_file))

    if not all_issues:
        print(f"No debug-log issues found across {len(apex_files)} Apex file(s).")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(all_issues)} issue(s) found across {len(apex_files)} Apex file(s).")
    return 1


if __name__ == '__main__':
    sys.exit(main())
