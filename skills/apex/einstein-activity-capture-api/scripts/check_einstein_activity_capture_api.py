#!/usr/bin/env python3
"""Checker script for Einstein Activity Capture API skill.

Scans Apex source files in a Salesforce metadata directory for common EAC
anti-patterns: querying Task/Event/EmailMessage for EAC data, trigger-based
EAC reaction patterns, DML against ActivityMetric outside test contexts,
empty-result exception anti-patterns, missing date filters, and sharing violations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_activity_capture_api.py [--help]
    python3 check_einstein_activity_capture_api.py --manifest-dir path/to/metadata
    python3 check_einstein_activity_capture_api.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# SOQL queries against Task/Event/EmailMessage
_TASK_SOQL_PATTERN = re.compile(
    r"\bSELECT\b[^;]*\bFROM\s+(Task|Event|EmailMessage)\b",
    re.IGNORECASE | re.DOTALL,
)

# EAC-specific context indicator in file
_EAC_CONTEXT_PATTERN = re.compile(
    r"\beac\b|\beinstein.activity\b|\bactivity.capture\b",
    re.IGNORECASE,
)

# Trigger on Task/Event/EmailMessage
_TRIGGER_EAC_PATTERN = re.compile(
    r"trigger\s+\w+\s+on\s+(Task|Event|EmailMessage)\s*\(",
    re.IGNORECASE,
)

_ACTIVITY_SOURCE_IN_TRIGGER = re.compile(
    r"ActivitySource\s*==?\s*['\"]EAC['\"]",
    re.IGNORECASE,
)

# DML against ActivityMetric
_DML_ACTIVITY_METRIC = re.compile(
    r"\b(insert|update|delete|upsert)\s+\w*[Aa]ctivity[Mm]etric",
    re.IGNORECASE,
)

_IS_TEST_ANNOTATION = re.compile(r"@isTest", re.IGNORECASE)

# isEmpty() followed by throw — anti-pattern near ActivityMetric
_EMPTY_THROW_PATTERN = re.compile(
    r"\.isEmpty\(\)\s*\)\s*\{[^}]*throw\b",
    re.IGNORECASE | re.DOTALL,
)

# ActivityMetric query missing a date filter
_ACTIVITY_METRIC_QUERY = re.compile(
    r"\bFROM\s+ActivityMetric\b",
    re.IGNORECASE,
)
_ACTIVITY_DATE_FILTER = re.compile(
    r"\bActivityDate\b",
    re.IGNORECASE,
)

# without sharing class declaration in EAC context
_WITHOUT_SHARING = re.compile(
    r"\bpublic\s+without\s+sharing\s+class\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File scanning helpers
# ---------------------------------------------------------------------------

def _read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _find_apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .cls and .trigger files under manifest_dir."""
    apex_files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        apex_files.extend(manifest_dir.rglob(ext))
    return sorted(apex_files)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_task_event_email_for_eac(path: Path, content: str) -> list[str]:
    """Flag SOQL against Task/Event/EmailMessage in files with EAC context."""
    issues: list[str] = []
    if not _EAC_CONTEXT_PATTERN.search(content):
        return issues  # no EAC context — skip to avoid false positives

    for match in _TASK_SOQL_PATTERN.finditer(content):
        object_name = match.group(1)
        line_no = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_no}: SOQL query against '{object_name}' in file with EAC "
            f"context. Standard EAC orgs do not write synced records to "
            f"Task/Event/EmailMessage. Use ActivityMetric, or verify Write-Back is enabled."
        )
    return issues


def check_trigger_eac_source_filter(path: Path, content: str) -> list[str]:
    """Flag trigger files on Task/Event/EmailMessage that filter by ActivitySource='EAC'."""
    issues: list[str] = []
    if not _TRIGGER_EAC_PATTERN.search(content):
        return issues

    if _ACTIVITY_SOURCE_IN_TRIGGER.search(content):
        issues.append(
            f"{path}: Apex trigger on Task/Event/EmailMessage filters by "
            f"ActivitySource='EAC'. EAC sync does not fire standard object triggers "
            f"in non-Write-Back orgs. Use a scheduled batch or flow instead."
        )
    return issues


def check_dml_activity_metric_in_production(path: Path, content: str) -> list[str]:
    """Flag DML against ActivityMetric outside @isTest files."""
    issues: list[str] = []
    if _IS_TEST_ANNOTATION.search(content):
        return issues  # test files — DML on ActivityMetric is valid for seeding

    for match in _DML_ACTIVITY_METRIC.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        dml_op = match.group(1).lower()
        issues.append(
            f"{path}:{line_no}: '{dml_op}' DML against ActivityMetric in non-test "
            f"code. ActivityMetric is read-only in production. "
            f"Move this DML to a @isTest context for test data seeding only."
        )
    return issues


def check_empty_result_exception(path: Path, content: str) -> list[str]:
    """Flag isEmpty() + throw patterns near ActivityMetric usage."""
    issues: list[str] = []
    if "ActivityMetric" not in content:
        return issues

    for match in _EMPTY_THROW_PATTERN.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_no}: isEmpty() followed by throw detected near ActivityMetric "
            f"usage. Empty EAC results are valid when users have no connected account. "
            f"Return a zero-default value instead of throwing an exception."
        )
    return issues


def check_activity_metric_no_date_filter(path: Path, content: str) -> list[str]:
    """Flag ActivityMetric queries that lack a date filter."""
    issues: list[str] = []
    if not _ACTIVITY_METRIC_QUERY.search(content):
        return issues

    # Check each SOQL statement containing ActivityMetric for a date filter
    # Simple heuristic: if file has ActivityMetric queries but no ActivityDate reference
    if not _ACTIVITY_DATE_FILTER.search(content):
        issues.append(
            f"{path}: ActivityMetric query detected without an ActivityDate filter. "
            f"ActivityMetric accumulates one row per contact per day — queries without "
            f"a date range may scan full history and hit SOQL row limits. "
            f"Add 'AND ActivityDate >= :cutoff' with an appropriate date window."
        )
    return issues


def check_without_sharing_eac_class(path: Path, content: str) -> list[str]:
    """Flag EAC-related classes declared without sharing."""
    issues: list[str] = []
    has_eac = "ActivityMetric" in content or _EAC_CONTEXT_PATTERN.search(content)
    if not has_eac:
        return issues

    if _WITHOUT_SHARING.search(content):
        issues.append(
            f"{path}: Class declared 'without sharing' in file with EAC/ActivityMetric "
            f"context. EAC engagement data is user-owned and should respect sharing rules. "
            f"Use 'with sharing' unless there is an explicit documented reason to bypass."
        )
    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_einstein_activity_capture_api(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found across all Apex files in manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _find_apex_files(manifest_dir)
    if not apex_files:
        return issues  # no Apex files — not an error

    checkers = [
        check_task_event_email_for_eac,
        check_trigger_eac_source_filter,
        check_dml_activity_metric_in_production,
        check_empty_result_exception,
        check_activity_metric_no_date_filter,
        check_without_sharing_eac_class,
    ]

    for apex_file in apex_files:
        content = _read_file(apex_file)
        if not content:
            continue
        for checker in checkers:
            issues.extend(checker(apex_file, content))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex source files for Einstein Activity Capture anti-patterns: "
            "incorrect SOQL surfaces, trigger-based EAC reactions, DML against "
            "read-only objects, missing date filters, and sharing violations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata to scan (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_einstein_activity_capture_api(manifest_dir)

    if not issues:
        print("No EAC anti-patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
