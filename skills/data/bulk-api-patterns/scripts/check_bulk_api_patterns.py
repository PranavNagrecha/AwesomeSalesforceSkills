#!/usr/bin/env python3
"""Checker script for Bulk API Patterns skill.

Scans Salesforce source files (Apex classes, triggers, and JS/Python integration
scripts) for common Bulk API 2.0 implementation mistakes:

1. Bulk API 2.0 ingest references without all three result endpoint calls
   (failedResults, unprocessedRecords, successfulResults).
2. Bulk API 2.0 ingest references without an UploadComplete signal.
3. Query job pagination that uses falsy/None check instead of string equality
   for the Sforce-Locator "null" sentinel value.
4. Legacy Bulk API v1 session ID authentication used in v2.0 context
   (X-SFDC-Session header in files that also reference v2.0 endpoints).
5. Multipart job creation followed by a redundant UploadComplete PATCH in
   the same file (indicates the pipeline does not branch on initial job state).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_bulk_api_patterns.py [--help]
    python3 check_bulk_api_patterns.py --manifest-dir path/to/source
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Bulk API 2.0 ingest endpoint references
BULK_INGEST_V2_PATTERN = re.compile(
    r"jobs/ingest|/jobs/ingest/",
    re.IGNORECASE,
)

# Bulk API 2.0 query endpoint references
BULK_QUERY_V2_PATTERN = re.compile(
    r"jobs/query",
    re.IGNORECASE,
)

# Result endpoint retrieval — ingest
FAILED_RESULTS_PATTERN = re.compile(
    r"failedResults|failed[_\-]results|getFailedResults",
    re.IGNORECASE,
)

UNPROCESSED_PATTERN = re.compile(
    r"unprocessedRecords|unprocessed[_\-]records|getUnprocessedRecords",
    re.IGNORECASE,
)

SUCCESSFUL_RESULTS_PATTERN = re.compile(
    r"successfulResults|successful[_\-]results|getSuccessfulResults",
    re.IGNORECASE,
)

# UploadComplete signal
UPLOAD_COMPLETE_PATTERN = re.compile(
    r"UploadComplete|uploadComplete|upload_complete",
    re.IGNORECASE,
)

# Multipart job creation — Content-Type multipart or multipart boundary in same file
MULTIPART_CREATION_PATTERN = re.compile(
    r"multipart/form-data|multipart\.form|boundary=",
    re.IGNORECASE,
)

# Sforce-Locator None/falsy check (anti-pattern — should be string equality to "null")
# Catches: `if not locator`, `if locator is None`, `if locator == None`, `if locator == ""`
LOCATOR_FALSY_CHECK_PATTERN = re.compile(
    r"Sforce-Locator|sforce.locator|sforce_locator",
    re.IGNORECASE,
)

LOCATOR_STRING_NULL_PATTERN = re.compile(
    r"""(locator\s*==\s*["']null["'])|(["']null["']\s*==\s*locator)""",
    re.IGNORECASE,
)

LOCATOR_NONE_PATTERN = re.compile(
    r"""locator\s+(is\s+None|==\s*None|==\s*[""]["'])"""
    r"""|if\s+not\s+\w*locator\w*""",
    re.IGNORECASE,
)

# Legacy Bulk API v1 session ID header used alongside v2.0 endpoints
V1_SESSION_HEADER_PATTERN = re.compile(
    r"X-SFDC-Session",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

SOURCE_EXTENSIONS = {".cls", ".trigger", ".js", ".py", ".ts"}


def find_source_files(manifest_dir: Path) -> list[Path]:
    """Return all source files under manifest_dir."""
    files: list[Path] = []
    for ext in SOURCE_EXTENSIONS:
        files.extend(manifest_dir.rglob(f"*{ext}"))
    return sorted(files)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_ingest_result_completeness(files: list[Path]) -> list[str]:
    """
    For every file referencing Bulk API 2.0 ingest endpoints, verify it also
    references all three result endpoints (failedResults, unprocessedRecords,
    successfulResults) and an UploadComplete signal.

    Missing any result endpoint is a data-loss risk.
    Missing UploadComplete means the job never starts.
    """
    issues: list[str] = []

    for path in files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not BULK_INGEST_V2_PATTERN.search(content):
            continue  # File does not reference Bulk API 2.0 ingest — skip

        rel = path.name
        has_failed = FAILED_RESULTS_PATTERN.search(content) is not None
        has_unprocessed = UNPROCESSED_PATTERN.search(content) is not None
        has_successful = SUCCESSFUL_RESULTS_PATTERN.search(content) is not None
        has_upload_complete = UPLOAD_COMPLETE_PATTERN.search(content) is not None
        uses_multipart = MULTIPART_CREATION_PATTERN.search(content) is not None

        if not has_failed:
            issues.append(
                f"{rel}: References Bulk API 2.0 ingest but does not call failedResults. "
                "Failed records are silently lost. "
                "Retrieve GET .../failedResults/ after every job reaches a terminal state."
            )

        if not has_unprocessed:
            issues.append(
                f"{rel}: References Bulk API 2.0 ingest but does not call unprocessedRecords. "
                "Records from timed-out batches appear here, not in failedResults. "
                "Retrieve GET .../unprocessedRecords/ after every job."
            )

        if not has_successful:
            issues.append(
                f"{rel}: References Bulk API 2.0 ingest but does not call successfulResults. "
                "Without successfulResults, the integrity check "
                "(successful + failed + unprocessed == total uploaded) cannot be performed."
            )

        # Only warn about missing UploadComplete if multipart creation is NOT present.
        # Multipart jobs auto-complete the upload step.
        if not has_upload_complete and not uses_multipart:
            issues.append(
                f"{rel}: References Bulk API 2.0 ingest but no UploadComplete signal found. "
                "A standard ingest job remains in Open state indefinitely without "
                "PATCH {{state: UploadComplete}}. The job will never start processing."
            )

        # Warn if both multipart creation AND UploadComplete PATCH are present.
        # This likely means the pipeline sends a redundant PATCH after multipart creation.
        if uses_multipart and has_upload_complete:
            issues.append(
                f"{rel}: Contains both multipart job creation and an UploadComplete signal. "
                "Multipart jobs auto-transition to UploadComplete on creation. "
                "Sending a redundant PATCH to an already-UploadComplete job will return an error. "
                "Branch the pipeline on the initial job state to skip the PATCH for multipart jobs."
            )

    return issues


def check_query_locator_sentinel(files: list[Path]) -> list[str]:
    """
    For every file referencing Sforce-Locator, verify that the pagination
    termination check uses string equality to the literal "null" value, not
    a None/falsy check.

    Using None/falsy check fails to terminate pagination because Sforce-Locator
    is always present and always returns a string (either a locator or "null").
    """
    issues: list[str] = []

    for path in files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not LOCATOR_FALSY_CHECK_PATTERN.search(content):
            continue  # File does not reference Sforce-Locator — skip

        rel = path.name
        has_string_null_check = LOCATOR_STRING_NULL_PATTERN.search(content) is not None
        has_none_check = LOCATOR_NONE_PATTERN.search(content) is not None

        if has_none_check and not has_string_null_check:
            issues.append(
                f"{rel}: References Sforce-Locator but uses a None/falsy check to detect "
                "the last page. The Sforce-Locator header always returns a string — "
                "the last-page sentinel is the literal string \"null\", not Python None. "
                "Use string equality: `if locator == \"null\": break`."
            )

    return issues


def check_v1_session_header_in_v2_context(files: list[Path]) -> list[str]:
    """
    Warn when a file uses the legacy Bulk API v1 X-SFDC-Session authentication
    header alongside Bulk API 2.0 endpoint patterns.

    Bulk API 2.0 uses OAuth 2.0 bearer tokens, not session IDs.
    Mixing v1 auth with v2.0 endpoints will result in authentication failures.
    """
    issues: list[str] = []

    for path in files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        uses_v1_auth = V1_SESSION_HEADER_PATTERN.search(content) is not None
        uses_v2_ingest = BULK_INGEST_V2_PATTERN.search(content) is not None
        uses_v2_query = BULK_QUERY_V2_PATTERN.search(content) is not None

        if uses_v1_auth and (uses_v2_ingest or uses_v2_query):
            issues.append(
                f"{path.name}: Uses X-SFDC-Session header (Bulk API v1 authentication) "
                "alongside Bulk API 2.0 endpoint patterns (/jobs/ingest or /jobs/query). "
                "Bulk API 2.0 requires OAuth 2.0 bearer token authentication. "
                "Replace X-SFDC-Session with Authorization: Bearer {{token}}."
            )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce source files for common Bulk API 2.0 implementation mistakes.\n\n"
            "Checks performed:\n"
            "  1. Ingest job references without all three result endpoints\n"
            "  2. Ingest job references without UploadComplete signal\n"
            "  3. Multipart job creation with redundant UploadComplete PATCH\n"
            "  4. Query job Sforce-Locator checked with None/falsy instead of string equality\n"
            "  5. Legacy v1 X-SFDC-Session auth used with v2.0 endpoints\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing source files to scan (default: current directory).",
    )
    return parser.parse_args()


def run_checks(manifest_dir: Path) -> list[str]:
    """Run all checks and return a flat list of issue strings."""
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    files = find_source_files(manifest_dir)

    if not files:
        return [
            f"No source files ({', '.join(sorted(SOURCE_EXTENSIONS))}) found "
            f"under {manifest_dir}. "
            "Point --manifest-dir at a directory containing integration source files."
        ]

    issues: list[str] = []
    issues.extend(check_ingest_result_completeness(files))
    issues.extend(check_query_locator_sentinel(files))
    issues.extend(check_v1_session_header_in_v2_context(files))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = run_checks(manifest_dir)

    if not issues:
        print("No Bulk API pattern issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
