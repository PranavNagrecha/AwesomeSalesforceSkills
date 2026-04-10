#!/usr/bin/env python3
"""Checker script for FSL Apex Extensions skill.

Scans Apex source files for common FSL Apex anti-patterns:
  1. FSL scheduling API calls after DML in the same method (callout-DML conflict)
  2. Database.executeBatch calls without explicit batchSize=1
  3. Queueable/Batchable classes calling FSL methods without Database.AllowsCallouts
  4. GetSlots return value accessed without an isEmpty() / null check
  5. FSL.OAAS calls without a license/feature guard

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_apex_extensions.py [--help]
    python3 check_fsl_apex_extensions.py --apex-dir path/to/force-app/main/default/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

_DML_RE = re.compile(
    r'\b(insert|update|upsert|delete|undelete)\s+\w',
    re.IGNORECASE,
)
_FSL_CALLOUT_RE = re.compile(
    r'FSL\.(AppointmentBookingService\.GetSlots|ScheduleService\.schedule)\s*\(',
    re.IGNORECASE,
)
_OAAS_RE = re.compile(r'FSL\.OAAS\.', re.IGNORECASE)
_BATCH_EXECUTE_RE = re.compile(
    r'Database\.executeBatch\s*\(([^)]+)\)',
    re.IGNORECASE,
)
_ALLOWS_CALLOUTS_RE = re.compile(r'Database\.AllowsCallouts', re.IGNORECASE)
_ASYNC_CLASS_RE = re.compile(
    r'implements\s+[^{]*\b(Queueable|Database\.Batchable)\b',
    re.IGNORECASE,
)
_GETSLOTS_ASSIGN_RE = re.compile(
    r'(\w+)\s*=\s*FSL\.AppointmentBookingService\.GetSlots\s*\(',
    re.IGNORECASE,
)
_FEATURE_GUARD_RE = re.compile(
    r'(checkPermission|Custom_Metadata|FeatureManagement|CustomPermission)',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def _check_dml_before_fsl_callout(lines: list[str], path: Path) -> list[str]:
    issues: list[str] = []
    brace_depth = 0
    in_method = False
    dml_seen = False
    method_start_line = 0

    for lineno, line in enumerate(lines, start=1):
        opens = line.count('{')
        closes = line.count('}')

        if brace_depth == 1 and opens > 0:
            in_method = True
            dml_seen = False
            method_start_line = lineno

        brace_depth += opens - closes

        if brace_depth <= 1:
            in_method = False
            dml_seen = False

        if in_method:
            if _DML_RE.search(line):
                dml_seen = True
            if dml_seen and _FSL_CALLOUT_RE.search(line):
                issues.append(
                    f'ISSUE [{path}:{lineno}] FSL callout follows uncommitted DML '
                    f'(method ~line {method_start_line}). '
                    'Use Queueable or Batch(batchSize=1) to split the transaction.'
                )

    return issues


def _check_batch_size(lines: list[str], path: Path) -> list[str]:
    issues: list[str] = []
    content = '\n'.join(lines)
    if not (_FSL_CALLOUT_RE.search(content) or _OAAS_RE.search(content)):
        return issues

    for lineno, line in enumerate(lines, start=1):
        m = _BATCH_EXECUTE_RE.search(line)
        if not m:
            continue
        args = [a.strip() for a in m.group(1).split(',')]
        if len(args) < 2:
            issues.append(
                f'ISSUE [{path}:{lineno}] Database.executeBatch() missing explicit batchSize. '
                'FSL scheduling APIs require batchSize=1.'
            )
        elif args[1] != '1':
            issues.append(
                f'ISSUE [{path}:{lineno}] Database.executeBatch() batchSize={args[1]}; '
                'FSL scheduling APIs require batchSize=1.'
            )

    return issues


def _check_allows_callouts(content: str, path: Path) -> list[str]:
    issues: list[str] = []
    if not (_FSL_CALLOUT_RE.search(content) or _OAAS_RE.search(content)):
        return issues
    if not _ASYNC_CLASS_RE.search(content):
        return issues
    if not _ALLOWS_CALLOUTS_RE.search(content):
        issues.append(
            f'ISSUE [{path}] Class implements Queueable or Database.Batchable and calls FSL '
            'APIs but does not implement Database.AllowsCallouts.'
        )
    return issues


def _check_getslots_empty_guard(lines: list[str], path: Path) -> list[str]:
    issues: list[str] = []
    content = '\n'.join(lines)
    slot_vars: set[str] = set()
    for m in _GETSLOTS_ASSIGN_RE.finditer(content):
        slot_vars.add(m.group(1).lower())

    for var in slot_vars:
        index_re = re.compile(rf'\b{re.escape(var)}\s*\[', re.IGNORECASE)
        guard_re = re.compile(
            rf'({re.escape(var)}\s*==\s*null'
            rf'|{re.escape(var)}\s*!=\s*null'
            rf'|{re.escape(var)}\.isEmpty'
            rf'|{re.escape(var)}\.size\s*\(\s*\))',
            re.IGNORECASE,
        )
        for lineno, line in enumerate(lines, start=1):
            if index_re.search(line):
                preceding = '\n'.join(lines[:lineno])
                if not guard_re.search(preceding):
                    issues.append(
                        f'ISSUE [{path}:{lineno}] `{var}` from GetSlots() accessed without '
                        'isEmpty() or null check. GetSlots returns empty list when no slots exist.'
                    )
                break

    return issues


def _check_oaas_license_guard(lines: list[str], path: Path) -> list[str]:
    issues: list[str] = []
    for lineno, line in enumerate(lines, start=1):
        if _OAAS_RE.search(line):
            window_start = max(0, lineno - 20)
            window = '\n'.join(lines[window_start:lineno])
            if not _FEATURE_GUARD_RE.search(window):
                issues.append(
                    f'ISSUE [{path}:{lineno}] FSL.OAAS call without visible license/feature '
                    'guard. OAAS requires Enhanced Scheduling and Optimization add-on.'
                )
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def check_apex_dir(apex_dir: Path) -> list[str]:
    issues: list[str] = []

    if not apex_dir.exists():
        issues.append(f'ISSUE [config] Apex directory not found: {apex_dir}')
        return issues

    cls_files = list(apex_dir.rglob('*.cls'))
    if not cls_files:
        return issues

    for cls_file in cls_files:
        try:
            raw = cls_file.read_text(encoding='utf-8', errors='replace')
        except OSError as exc:
            issues.append(f'ISSUE [{cls_file}] Could not read file: {exc}')
            continue

        lines = raw.splitlines()
        issues.extend(_check_dml_before_fsl_callout(lines, cls_file))
        issues.extend(_check_batch_size(lines, cls_file))
        issues.extend(_check_allows_callouts(raw, cls_file))
        issues.extend(_check_getslots_empty_guard(lines, cls_file))
        issues.extend(_check_oaas_license_guard(lines, cls_file))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            'Check Apex source files for FSL scheduling API anti-patterns. '
            'Detects callout-DML conflicts, missing batchSize=1, missing AllowsCallouts, '
            'unguarded GetSlots access, and OAAS calls without license guards.'
        ),
    )
    parser.add_argument(
        '--apex-dir',
        default='.',
        help='Root directory containing .cls Apex source files (default: current directory).',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apex_dir = Path(args.apex_dir)
    issues = check_apex_dir(apex_dir)

    if not issues:
        print('No FSL Apex anti-patterns found.')
        return 0

    for issue in issues:
        print(f'WARN: {issue}', file=sys.stderr)

    sys.exit(1)


if __name__ == '__main__':
    sys.exit(main())
