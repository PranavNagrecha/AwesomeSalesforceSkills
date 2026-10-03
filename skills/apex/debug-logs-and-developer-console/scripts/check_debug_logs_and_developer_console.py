#!/usr/bin/env python3
"""Checker script for Debug Logs And Developer Console skill.

Scans a Salesforce project for debug-log anti-patterns. Stdlib only.

Apex source (*.cls, *.trigger, *.apex):
- More than 10 System.debug calls in one file (consider a logging framework)
- System.debug without a LoggingLevel argument
- String concatenation inside System.debug (evaluated even when the level is off)
- Anonymous Apex scripts (*.apex) with DML and an unbounded query (no LIMIT)

Tooling API records saved as JSON (TraceFlag, DebugLevel), each rule citing the
Tooling API Developer Guide (262):
- TraceFlag whose ExpirationDate is 24 hours or more after StartDate ("ExpirationDate
  must be less than 24 hours after StartDate")
- CLASS_TRACING trace flags with no USER_DEBUG or DEVELOPER_LOG flag in the same JSON file
  ("CLASS_TRACING trace flags ... don't generate logs")
- DebugLevel with ApexCode FINEST (Apex Developer Guide: logs all variable assignments)

Usage:
    python3 check_debug_logs_and_developer_console.py --manifest-dir path/to/folder
    python3 check_debug_logs_and_developer_console.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
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

APEX_EXTENSIONS = {'.cls', '.trigger', '.apex'}
DML_RE = re.compile(r'\b(insert|update|upsert|delete|merge|undelete)\s+\w|Database\.(insert|update|upsert|delete|merge)\s*\(', re.IGNORECASE)
SOQL_RE = re.compile(r'\[\s*SELECT\b[^\]]*\]', re.IGNORECASE | re.DOTALL)
DEBUG_PER_FILE_THRESHOLD = 10


def check_apex_file(path: Path) -> list[str]:
    """Return issues found in a single Apex source file."""
    issues: list[str] = []
    try:
        source = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read file: {exc}"]

    lines = source.splitlines()
    debug_count = len(SYSTEM_DEBUG_ANY.findall(source))

    if debug_count > DEBUG_PER_FILE_THRESHOLD:
        issues.append(
            f"{path}: {debug_count} System.debug calls ; consider a logging framework "
            f"(threshold: {DEBUG_PER_FILE_THRESHOLD})"
        )

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('*'):
            continue
        if SYSTEM_DEBUG_NO_LEVEL.search(line):
            issues.append(
                f"{path}:{i}: System.debug without LoggingLevel; "
                "add LoggingLevel.DEBUG (or appropriate level) as first argument "
                "to enable log-level filtering"
            )
        if path.suffix != '.apex' and SYSTEM_DEBUG_CONCAT.search(line):
            issues.append(
                f"{path}:{i}: String concatenation inside System.debug; "
                "this evaluates the concatenation even when logging is off; "
                "use lazy formatting or remove the debug call"
            )

    if path.suffix == '.apex' and DML_RE.search(source):
        unbounded = [q for q in SOQL_RE.findall(source) if not re.search(r'\bLIMIT\b', q, re.IGNORECASE)]
        if unbounded:
            issues.append(
                f"{path}: anonymous Apex runs DML after an unbounded query; add LIMIT and a dry-run "
                "switch, and run it in a sandbox first"
            )

    return issues


def _parse_dt(value):
    if not isinstance(value, str):
        return None
    text = value.strip().replace('Z', '+0000')
    for fmt in ('%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%dT%H:%M:%S%z'):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _records(doc):
    if isinstance(doc, dict):
        if isinstance(doc.get('result'), dict) and isinstance(doc['result'].get('records'), list):
            return doc['result']['records']
        if isinstance(doc.get('records'), list):
            return doc['records']
        return [doc]
    if isinstance(doc, list):
        return [d for d in doc if isinstance(d, dict)]
    return []


def check_tooling_json(paths: list[Path]) -> list[str]:
    issues: list[str] = []
    for path in paths:
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        log_types: list[tuple[Path, str]] = []
        for rec in _records(doc):
            if 'LogType' in rec:
                log_types.append((path, str(rec.get('LogType'))))
                start = _parse_dt(rec.get('StartDate'))
                end = _parse_dt(rec.get('ExpirationDate'))
                if start and end and end - start >= timedelta(hours=24):
                    issues.append(f"{path}: TraceFlag ExpirationDate is 24 hours or more after StartDate; the Tooling API requires less than 24 hours")
            if str(rec.get('ApexCode', '')).upper() == 'FINEST' and ('DeveloperName' in rec or 'MasterLabel' in rec):
                issues.append(f"{path}: DebugLevel sets ApexCode FINEST, which logs every variable assignment; avoid it where sensitive values are handled")
        kinds = {t for _, t in log_types}
        if 'CLASS_TRACING' in kinds and not kinds & {'USER_DEBUG', 'DEVELOPER_LOG'}:
            issues.append(f"{path}: CLASS_TRACING trace flag without a USER_DEBUG or DEVELOPER_LOG flag in the same set; class trace flags change levels but don't generate logs")
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
    parser.add_argument('--self-test', action='store_true', help='Run against scripts/fixtures/good and bad.')
    return parser.parse_args()


def scan(manifest_dir: Path) -> tuple[list[str], int]:
    apex_files = find_apex_files(manifest_dir)
    json_files = sorted(p for p in manifest_dir.rglob('*.json') if p.is_file())
    issues: list[str] = []
    for apex_file in sorted(apex_files):
        issues.extend(check_apex_file(apex_file))
    issues.extend(check_tooling_json(json_files))
    return issues, len(apex_files) + len(json_files)


def self_test() -> int:
    base = Path(__file__).resolve().parent / 'fixtures'
    good, bad = base / 'good', base / 'bad'
    if not good.is_dir() or not bad.is_dir():
        print('ERROR: fixtures/good or fixtures/bad is missing')
        return 1
    failures = 0
    good_issues, _ = scan(good)
    if good_issues:
        failures += 1
        print(f'ERROR: self-test: fixtures/good produced {good_issues}')
    bad_issues, _ = scan(bad)
    for path in sorted(p for p in bad.iterdir() if p.is_file()):
        if not any(str(path) in issue for issue in bad_issues):
            failures += 1
            print(f'ERROR: self-test: bad fixture {path.name} produced no issue')
    if failures:
        return 1
    print('self-test passed')
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ISSUE: Manifest directory not found: {manifest_dir}")
        return 1

    all_issues, scanned = scan(manifest_dir)

    if scanned == 0:
        print(f"WARN: No Apex or Tooling JSON files found under {manifest_dir}. Nothing to check.")
        return 0

    if not all_issues:
        print(f"No debug-log issues found across {scanned} file(s).")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(all_issues)} issue(s) found across {scanned} file(s).")
    return 1


if __name__ == '__main__':
    sys.exit(main())
