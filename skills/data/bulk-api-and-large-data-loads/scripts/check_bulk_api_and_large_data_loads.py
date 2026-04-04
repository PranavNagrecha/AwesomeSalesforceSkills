#!/usr/bin/env python3
"""Checker script for Bulk API and Large Data Loads skill.

Scans Salesforce metadata (Apex classes, triggers, and Aura/LWC components)
for common Bulk API integration mistakes:

1. Code that references Bulk API endpoints but does not call failedResults.
2. Code that references Bulk API endpoints but does not call unprocessedRecords.
3. Apex that calls Database.insert/update/delete with allOrNone=true on large
   collections (suggests synchronous bulk anti-pattern rather than Bulk API).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_bulk_api_and_large_data_loads.py [--help]
    python3 check_bulk_api_and_large_data_loads.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Detects references to Bulk API 2.0 ingest endpoint in source files
BULK_INGEST_PATTERN = re.compile(
    r"jobs/ingest|bulkApi|BulkApi|bulk_api|/jobs/query",
    re.IGNORECASE,
)

# Detects retrieval of failed results
FAILED_RESULTS_PATTERN = re.compile(
    r"failedResults|failed[_\-]results|getFailedResults",
    re.IGNORECASE,
)

# Detects retrieval of unprocessed records
UNPROCESSED_PATTERN = re.compile(
    r"unprocessedRecords|unprocessed[_\-]records|getUnprocessedRecords",
    re.IGNORECASE,
)

# Detects UploadComplete signal
UPLOAD_COMPLETE_PATTERN = re.compile(
    r"UploadComplete|uploadComplete|upload_complete",
    re.IGNORECASE,
)

# Detects large synchronous DML — allOrNone=true with a list argument
# This is a heuristic: Database.insert(recordList, true) style
SYNC_BULK_DML_PATTERN = re.compile(
    r"Database\.(insert|update|delete|upsert)\s*\(\s*\w+\s*,\s*true\s*\)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

APEX_EXTENSIONS = {".cls", ".trigger"}
JS_EXTENSIONS = {".js"}
ALL_EXTENSIONS = APEX_EXTENSIONS | JS_EXTENSIONS


def find_source_files(manifest_dir: Path) -> list[Path]:
    """Return all Apex and JS source files under manifest_dir."""
    files: list[Path] = []
    for ext in ALL_EXTENSIONS:
        files.extend(manifest_dir.rglob(f"*{ext}"))
    return sorted(files)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_bulk_api_result_retrieval(files: list[Path]) -> list[str]:
    """
    For every file that references Bulk API ingest/query endpoints, verify it
    also references failedResults AND unprocessedRecords endpoints.

    Missing either is a data-loss risk: records silently dropped without
    surfacing an error to the caller.
    """
    issues: list[str] = []

    for path in files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not BULK_INGEST_PATTERN.search(content):
            continue  # File does not reference Bulk API — skip

        rel = path.name
        has_failed = FAILED_RESULTS_PATTERN.search(content) is not None
        has_unprocessed = UNPROCESSED_PATTERN.search(content) is not None
        has_upload_complete = UPLOAD_COMPLETE_PATTERN.search(content) is not None

        if not has_failed:
            issues.append(
                f"{rel}: References Bulk API but does not call failedResults. "
                "Failed records will be silently lost. "
                "Retrieve GET .../failedResults/ after every job reaches JobComplete."
            )

        if not has_unprocessed:
            issues.append(
                f"{rel}: References Bulk API but does not call unprocessedRecords. "
                "Batch-timeout records appear here, not in failedResults. "
                "Retrieve GET .../unprocessedRecords/ after every job."
            )

        if not has_upload_complete:
            issues.append(
                f"{rel}: References Bulk API ingest but no UploadComplete signal found. "
                "Jobs remain in Open state indefinitely without PATCH {{state: UploadComplete}}. "
                "The job will never start processing without this call."
            )

    return issues


def check_synchronous_bulk_dml(files: list[Path]) -> list[str]:
    """
    Detect Apex that uses Database.insert/update/delete with allOrNone=true
    on what appears to be a collection variable. For small volumes this is
    fine, but it surfaces as a candidate for Bulk API 2.0 review when the
    collection size is unknown at compile time.

    This is advisory, not a hard error.
    """
    issues: list[str] = []

    apex_files = [f for f in files if f.suffix in APEX_EXTENSIONS]

    for path in apex_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        matches = SYNC_BULK_DML_PATTERN.findall(content)
        if matches:
            ops = ", ".join(set(m.lower() for m in matches))
            issues.append(
                f"{path.name}: Contains synchronous Database.{ops}(list, allOrNone=true). "
                "If the list can exceed 2,000 records at runtime, consider Bulk API 2.0 "
                "to avoid governor limit exposure and improve throughput."
            )

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Bulk API integration mistakes.\n\n"
            "Checks performed:\n"
            "  1. Bulk API references without failedResults retrieval\n"
            "  2. Bulk API references without unprocessedRecords retrieval\n"
            "  3. Bulk API references without UploadComplete signal\n"
            "  4. Synchronous DML on collections (advisory)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def run_checks(manifest_dir: Path) -> list[str]:
    """Run all checks and return a flat list of issue strings."""
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    files = find_source_files(manifest_dir)

    if not files:
        return [
            f"No Apex (.cls, .trigger) or JS (.js) files found under {manifest_dir}. "
            "Point --manifest-dir at a directory containing source files to check."
        ]

    issues: list[str] = []
    issues.extend(check_bulk_api_result_retrieval(files))
    issues.extend(check_synchronous_bulk_dml(files))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = run_checks(manifest_dir)

    if not issues:
        print("No Bulk API issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
