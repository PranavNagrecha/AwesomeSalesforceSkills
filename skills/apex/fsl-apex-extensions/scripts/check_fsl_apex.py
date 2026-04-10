#!/usr/bin/env python3
"""Checker script for FSL Apex Extensions skill.

Scans Apex source files for common FSL Apex anti-patterns:
  1. FSL scheduling API calls after DML in the same method (callout-DML conflict)
  2. Database.executeBatch calls without explicit batchSize=1
  3. Queueable or Batchable classes that call FSL methods but do not implement Database.AllowsCallouts
  4. GetSlots return value accessed without an isEmpty() / null check
  5. FSL.OAAS calls without a license/feature guard

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_apex.py [--help]
    python3 check_fsl_apex.py --apex-dir path/to/force-app/main/default/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# DML statements (simplified — catches the common forms)
_DML_RE = re.compile(
    r'\b(insert|update|upsert|delete|undelete)\s+\w',
    re.IGNORECASE,
)

# FSL scheduling callout methods
_FSL_CALLOUT_RE = re.compile(
    r'FSL\.(AppointmentBookingService\.GetSlots|ScheduleService\.schedule)\s*\(',
    re.IGNORECASE,
)

# FSL.OAAS calls
_OAAS_RE = re.compile(r'FSL\.OAAS\.', re.IGNORECASE)

# Database.executeBatch without an explicit size-1 argument
# Matches executeBatch(expr) — missing second arg, or executeBatch(expr, N) where N != 1
_BATCH_EXECUTE_RE = re.compile(
    r'Database\.executeBatch\s*\(([^)]+)\)',
    re.IGNORECASE,
)

# implements clause for AllowsCallouts
_ALLOWS_CALLOUTS_RE = re.compile(r'Database\.AllowsCallouts', re.IGNORECASE)

# Class declaration with Queueable or Batchable
_ASYNC_CLASS_RE = re.compile(
    r'implements\s+[^{]*\b(Queueable|Database\.Batchable)\b',
    re.IGNORECASE,
)

# GetSlots assignment — var name capture
_GETSLOTS_ASSIGN_RE = re.compile(
    r'(\w+)\s*=\s*FSL\.AppointmentBookingService\.GetSlots\s*\(',
    re.IGNORECASE,
)

# isEmpty check
_ISEMPTY_RE = re.compile(r'\.isEmpty\s*\(\s*\)', re.IGNORECASE)

# Feature/permission guard near OAAS
_FEATURE_GUARD_RE = re.compile(
    r'(checkPermission|Custom_Metadata|FeatureManagement|CustomPermission)',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def _check_dml_before_fsl_callout(lines: list[str], path: Path) -> list[str]:
    """Flag methods where a DML statement appears before an FSL callout call."""
    issues: list[str] = []
    in_method = False
    dml_seen = False
    brace_depth = 0
    method_start_line = 0

    for lineno, line in enumerate(lines, start=1):
        opens = line.count('{')
        closes = line.count('}')

        # Rough heuristic: a new method starts when brace depth goes from 1 to 2
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
                    f'{path}:{lineno}: FSL scheduling callout follows uncommitted DML '
                    f'(method started ~line {method_start_line}). '
                    'Split into separate transactions using Queueable or Batch(batchSize=1).'
                )

    return issues


def _check_batch_size(lines: list[str], path: Path) -> list[str]:
    """Flag Database.executeBatch calls without explicit batchSize=1."""
    issues: list[str] = []
    content = '\n'.join(lines)

    # Only flag files that also reference FSL methods
    if not _FSL_CALLOUT_RE.search(content) and not _OAAS_RE.search(content):
        return issues

    for lineno, line in enumerate(lines, start=1):
        m = _BATCH_EXECUTE_RE.search(line)
        if not m:
            continue
        args_str = m.group(1)
        # Split on comma to find second arg
        args = [a.strip() for a in args_str.split(',')]
        if len(args) < 2:
            issues.append(
                f'{path}:{lineno}: Database.executeBatch() missing explicit batchSize. '
                'FSL scheduling APIs require batchSize=1 to avoid callout-DML conflict.'
            )
        elif args[1] != '1':
            issues.append(
                f'{path}:{lineno}: Database.executeBatch() batchSize={args[1]}. '
                'FSL scheduling APIs require batchSize=1.'
            )

    return issues


def _check_allows_callouts(content: str, path: Path) -> list[str]:
    """Flag async classes that call FSL methods but lack Database.AllowsCallouts."""
    issues: list[str] = []
    if not (_FSL_CALLOUT_RE.search(content) or _OAAS_RE.search(content)):
        return issues
    if not _ASYNC_CLASS_RE.search(content):
        return issues
    if not _ALLOWS_CALLOUTS_RE.search(content):
        issues.append(
            f'{path}: Class implements Queueable or Database.Batchable and calls FSL APIs '
            'but does not implement Database.AllowsCallouts. Add it to the implements clause.'
        )
    return issues


def _check_getslots_empty_guard(lines: list[str], path: Path) -> list[str]:
    """Flag GetSlots return values accessed without an isEmpty() guard."""
    issues: list[str] = []
    # Find variable names assigned from GetSlots
    content = '\n'.join(lines)
    slot_vars: set[str] = set()
    for m in _GETSLOTS_ASSIGN_RE.finditer(content):
        slot_vars.add(m.group(1).lower())

    if not slot_vars:
        return issues

    # For each variable, check if there is an isEmpty() check before first index access
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
                # Check if any guard appears in file before this line
                preceding = '\n'.join(lines[:lineno])
                if not guard_re.search(preceding):
                    issues.append(
                        f'{path}:{lineno}: Variable `{var}` from GetSlots() is indexed without '
                        'a preceding isEmpty() or null check. GetSlots returns an empty list '
                        'when no slots are available.'
                    )
                break  # Only flag the first unguarded access per variable

    return issues


def _check_oaas_license_guard(lines: list[str], path: Path) -> list[str]:
    """Flag FSL.OAAS calls not preceded by a feature/license guard."""
    issues: list[str] = []
    content = '\n'.join(lines)
    if not _OAAS_RE.search(content):
        return issues

    for lineno, line in enumerate(lines, start=1):
        if _OAAS_RE.search(line):
            # Check a window of preceding lines for a guard
            window_start = max(0, lineno - 20)
            preceding_window = '\n'.join(lines[window_start:lineno])
            if not _FEATURE_GUARD_RE.search(preceding_window):
                issues.append(
                    f'{path}:{lineno}: FSL.OAAS call detected without a visible license or '
                    'feature guard. OAAS requires the Enhanced Scheduling and Optimization '
                    'add-on. Gate this call behind a FeatureManagement.checkPermission() or '
                    'Custom Metadata flag.'
                )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_apex_dir(apex_dir: Path) -> list[str]:
    """Run all checks against .cls files in apex_dir. Returns list of issue strings."""
    issues: list[str] = []

    if not apex_dir.exists():
        issues.append(f'Apex directory not found: {apex_dir}')
        return issues

    cls_files = list(apex_dir.rglob('*.cls'))
    if not cls_files:
        # Not an error — just no Apex files to check
        return issues

    for cls_file in cls_files:
        try:
            raw = cls_file.read_text(encoding='utf-8', errors='replace')
        except OSError as exc:
            issues.append(f'Could not read {cls_file}: {exc}')
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
            'Reports callout-DML conflicts, missing batchSize=1, missing AllowsCallouts, '
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

    return 1


if __name__ == '__main__':
    sys.exit(main())
