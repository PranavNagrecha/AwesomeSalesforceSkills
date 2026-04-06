#!/usr/bin/env python3
"""Checker script for Entitlement Apex Hooks skill.

Scans Apex source files in a Salesforce metadata directory for common
anti-patterns specific to CaseMilestone / entitlement milestone automation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_entitlement_apex_hooks.py [--help]
    python3 check_entitlement_apex_hooks.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex source for CaseMilestone anti-patterns: "
            "IsCompleted writes, SlaExitDate writes, SOQL inside loops, "
            "and violation trigger misuse."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_apex_files(root: Path) -> list[Path]:
    """Return all .cls and .trigger files under root."""
    apex_files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        apex_files.extend(root.rglob(ext))
    return apex_files


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_is_completed_write(path: Path, source: str) -> list[str]:
    """Flag any assignment of IsCompleted = true on CaseMilestone."""
    issues: list[str] = []
    # Match patterns like: .IsCompleted = true  or  IsCompleted=true
    pattern = re.compile(r'\.IsCompleted\s*=\s*true', re.IGNORECASE)
    for i, line in enumerate(source.splitlines(), start=1):
        if pattern.search(line):
            issues.append(
                f"{path}:{i}: IsCompleted is read-only — write CompletionDate = System.now() instead. "
                f"Line: {line.strip()}"
            )
    return issues


def check_sla_exit_date_write(path: Path, source: str) -> list[str]:
    """Flag any write assignment to SlaExitDate."""
    issues: list[str] = []
    pattern = re.compile(r'\.SlaExitDate\s*=', re.IGNORECASE)
    for i, line in enumerate(source.splitlines(), start=1):
        if pattern.search(line):
            issues.append(
                f"{path}:{i}: SlaExitDate is system-managed and cannot be written by Apex. "
                f"Line: {line.strip()}"
            )
    return issues


def check_before_trigger_with_milestone_dml(path: Path, source: str) -> list[str]:
    """Flag trigger files that are 'before update/insert' and contain CaseMilestone DML."""
    issues: list[str] = []
    if path.suffix.lower() != ".trigger":
        return issues

    is_before_trigger = bool(
        re.search(r'\btrigger\b[^{]+\bbefore\s+(update|insert)\b', source, re.IGNORECASE)
    )
    has_milestone_dml = bool(
        re.search(r'\b(update|insert)\s+[^;]*CaseMilestone\b', source, re.IGNORECASE)
        or re.search(r'CaseMilestone[^;]*(update|insert)\b', source, re.IGNORECASE)
    )
    if is_before_trigger and has_milestone_dml:
        issues.append(
            f"{path}: Trigger appears to use 'before update/insert' context while also containing "
            "CaseMilestone DML. Use 'after update' to avoid mixed-DML issues."
        )
    return issues


def check_soql_inside_loop(path: Path, source: str) -> list[str]:
    """Heuristic: flag SOQL SELECT inside a for-loop body targeting CaseMilestone."""
    issues: list[str] = []
    lines = source.splitlines()
    inside_for = False
    brace_depth = 0
    for_brace_depth = 0

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Detect for loop opening (very simplified heuristic)
        if re.search(r'\bfor\s*\(', stripped):
            inside_for = True
            for_brace_depth = brace_depth

        brace_depth += stripped.count('{') - stripped.count('}')

        if inside_for and brace_depth <= for_brace_depth:
            inside_for = False

        if inside_for:
            if re.search(r'\[\s*SELECT\b', stripped, re.IGNORECASE):
                if 'CaseMilestone' in stripped:
                    issues.append(
                        f"{path}:{i}: SOQL on CaseMilestone inside a loop — "
                        "collect IDs first, then query outside the loop. "
                        f"Line: {stripped}"
                    )

    return issues


def check_violation_trigger_pattern(path: Path, source: str) -> list[str]:
    """Flag trigger files on CaseMilestone that check IsViolated transitions."""
    issues: list[str] = []
    if path.suffix.lower() != ".trigger":
        return issues

    is_milestone_trigger = bool(
        re.search(r'\btrigger\b[^{]+\bCaseMilestone\b', source, re.IGNORECASE)
    )
    checks_is_violated = bool(
        re.search(r'\bIsViolated\b', source, re.IGNORECASE)
    )
    if is_milestone_trigger and checks_is_violated:
        issues.append(
            f"{path}: A CaseMilestone trigger that checks IsViolated will never fire for "
            "platform-initiated violation state changes. Use Scheduled Apex polling instead."
        )
    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_entitlement_apex_hooks(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in Apex files under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _find_apex_files(manifest_dir)
    if not apex_files:
        # Not necessarily an error — the project may have no Apex
        return issues

    for apex_path in sorted(apex_files):
        source = _read_text(apex_path)
        if not source:
            continue

        issues.extend(check_is_completed_write(apex_path, source))
        issues.extend(check_sla_exit_date_write(apex_path, source))
        issues.extend(check_before_trigger_with_milestone_dml(apex_path, source))
        issues.extend(check_soql_inside_loop(apex_path, source))
        issues.extend(check_violation_trigger_pattern(apex_path, source))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_entitlement_apex_hooks(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
