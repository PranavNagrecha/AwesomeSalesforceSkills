#!/usr/bin/env python3
"""Checker script for Einstein Activity Capture API skill.

Scans Apex source files in a Salesforce metadata directory for EAC anti-patterns:
references to the retiring Activity Metrics layer, bogus ActivitySource='EAC'
filters, DML against ActivityMetric outside test contexts, empty-result exception
anti-patterns, missing date filters, and sharing violations.

Two EAC architectures exist and they invert each other's rules:

  * Sync Email as Salesforce Activity (default assumption here) --- captured email
    is stored as standard Task and EmailMessage records, so querying those objects
    and writing triggers on them is CORRECT.
  * Legacy EAC (pass --legacy-eac) --- captured email lives in an external store
    invisible to SOQL and triggers, so those same patterns return zero rows.

Either way, Activity Metrics, the Activities Dashboard, Recommended Connections and
A360 Reports retire in Spring '27 (February 2027), and the fields return null before
then. Salesforce Help instructs orgs to "Search your Apex, flows, and validation
rules for references to Activity Metrics fields, for example, the ActivityMetric
object" --- check_activity_metric_retirement is that search.
See https://help.salesforce.com/s/articleView?id=005384640&language=en_US&type=1

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_activity_capture_api.py [--help]
    python3 check_einstein_activity_capture_api.py --manifest-dir path/to/metadata
    python3 check_einstein_activity_capture_api.py --manifest-dir force-app/main/default
    python3 check_einstein_activity_capture_api.py --manifest-dir . --legacy-eac
"""

from __future__ import annotations

import argparse
import re
import sys
from functools import partial
from pathlib import Path

# Retirement of Activity Metrics / Activities Dashboard / Recommended Connections /
# A360 Reports. Verified 2026-08-14 against Salesforce Help article 005384640.
# The A360 objects below are the exact six the article enumerates. UnifiedActivity is
# deliberately NOT in that regex -- it is not on the published retirement list.
RETIREMENT_RELEASE = "Spring '27 (February 2027)"


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

# Any reference to the retiring Activity Metrics layer, or to the A360 report
# objects that retire alongside it.
_ACTIVITY_METRIC_REFERENCE = re.compile(r"\bActivityMetric\b")
_A360_RETIRING_OBJECTS = re.compile(
    r"\b(UnifiedEmail|UnifiedEmailParticipant|UnifiedMeeting"
    r"|UnifiedMeetingParticipant|UnifiedTask|UnifiedTaskParticipant)\b"
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

def check_task_event_email_for_eac(
    path: Path, content: str, legacy_eac: bool = False
) -> list[str]:
    """Flag SOQL against Task/Event/EmailMessage in EAC files --- legacy orgs only.

    Under Sync Email as Salesforce Activity captured email IS a standard Task /
    EmailMessage record, so this query is the correct pattern and flagging it would
    push the developer back onto the retiring ActivityMetric surface. Only orgs
    still on the legacy external store hit the zero-row failure.
    """
    issues: list[str] = []
    if not legacy_eac:
        return issues
    if not _EAC_CONTEXT_PATTERN.search(content):
        return issues  # no EAC context — skip to avoid false positives

    for match in _TASK_SOQL_PATTERN.finditer(content):
        object_name = match.group(1)
        line_no = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_no}: SOQL query against '{object_name}' in file with EAC "
            f"context, scanned with --legacy-eac. Legacy EAC does not write synced "
            f"records to Task/Event/EmailMessage, so this returns zero rows. Either "
            f"read ActivityMetric (retiring {RETIREMENT_RELEASE} — log the debt) or, "
            f"preferably, move the org to Sync Email as Salesforce Activity."
        )
    return issues


def check_trigger_eac_source_filter(
    path: Path, content: str, legacy_eac: bool = False
) -> list[str]:
    """Flag trigger files on Task/Event/EmailMessage that filter by ActivitySource='EAC'.

    The literal filter is wrong on both architectures --- it is an invented value.
    What differs is the remedy, so the message is architecture-aware.
    """
    issues: list[str] = []
    if not _TRIGGER_EAC_PATTERN.search(content):
        return issues

    if _ACTIVITY_SOURCE_IN_TRIGGER.search(content):
        remedy = (
            "Legacy EAC fires no standard object trigger at all — use a scheduled "
            "batch or flow."
            if legacy_eac
            else "Under Sync Email as Salesforce Activity the trigger DOES fire, so "
            "drop the filter rather than the trigger. Declaration vs outcome: the "
            "trigger always runs implicitly without sharing and cannot declare "
            "otherwise, so Trigger.new can include records the running user cannot "
            "see; but SOQL/SOSL/DML in the body run in user mode unless system mode "
            "is specified (apiVersion 67.0+ in .trigger-meta.xml, not the org "
            "release). User mode overrides that without-sharing context. "
            "WITH SYSTEM_MODE / AccessLevel.SYSTEM_MODE opts out (FLS/CRUD skipped, "
            "sharing falls back to without-sharing). Set the access mode explicitly."
        )
        issues.append(
            f"{path}: Apex trigger on Task/Event/EmailMessage filters by "
            f"ActivitySource='EAC', which is not a real filter value. {remedy}"
        )
    return issues


def check_activity_metric_retirement(
    path: Path, content: str, legacy_eac: bool = False
) -> list[str]:
    """Flag references to the retiring Activity Metrics / A360 reporting layer.

    Salesforce Help: "Search your Apex, flows, and validation rules for references
    to Activity Metrics fields, for example, the ActivityMetric object." The fields
    return null before the retirement date and nothing throws, so a seeded @isTest
    suite stays green while production silently scores every contact zero.

    Test files are exempt, matching check_dml_activity_metric_in_production. This
    skill's own checklist requires test classes to seed ActivityMetric in @isTest
    rather than depend on sandbox data, so flagging that seeding would have the
    checker contradict the skill. The production read the seeding exists to support
    is flagged on its own file, which is where the migration work actually is.
    """
    issues: list[str] = []
    if _IS_TEST_ANNOTATION.search(content):
        return issues

    match = _ACTIVITY_METRIC_REFERENCE.search(content)
    if match:
        line_no = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_no}: references ActivityMetric, which retires in "
            f"{RETIREMENT_RELEASE}. Activity Metrics fields no longer populate and "
            f"return null values before then — this code degrades silently rather "
            f"than failing. Recreate the reporting on Task and EmailMessage grouped "
            f"by Account or Opportunity, and persist computed scores to a custom field."
        )

    match = _A360_RETIRING_OBJECTS.search(content)
    if match:
        line_no = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_no}: references '{match.group(1)}', an A360 reporting "
            f"object retiring in {RETIREMENT_RELEASE} along with its report types. "
            f"Existing reports using these objects stop returning data. Migrate to "
            f"standard Activity records (Task / EmailMessage)."
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

def check_einstein_activity_capture_api(
    manifest_dir: Path, legacy_eac: bool = False
) -> list[str]:
    """Return a list of issue strings found across all Apex files in manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _find_apex_files(manifest_dir)
    if not apex_files:
        return issues  # no Apex files — not an error

    checkers = [
        partial(check_task_event_email_for_eac, legacy_eac=legacy_eac),
        partial(check_trigger_eac_source_filter, legacy_eac=legacy_eac),
        partial(check_activity_metric_retirement, legacy_eac=legacy_eac),
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
            "references to the retiring Activity Metrics and A360 reporting layer, "
            "bogus ActivitySource='EAC' filters, DML against read-only objects, "
            "missing date filters, and sharing violations."
        ),
        epilog=(
            "Assumes the org runs Sync Email as Salesforce Activity, where captured "
            "email is a standard Task/EmailMessage record. Pass --legacy-eac for orgs "
            "still on the external store. Activity Metrics, the Activities Dashboard, "
            f"Recommended Connections and A360 Reports retire in {RETIREMENT_RELEASE}."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata to scan (default: current directory).",
    )
    parser.add_argument(
        "--legacy-eac",
        action="store_true",
        help=(
            "Org is on legacy Einstein Activity Capture (external store), not Sync "
            "Email as Salesforce Activity. Enables the zero-row checks for SOQL "
            "against Task/Event/EmailMessage, which are correct patterns otherwise."
        ),
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_einstein_activity_capture_api(manifest_dir, legacy_eac=args.legacy_eac)

    if not issues:
        print("No EAC anti-patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
