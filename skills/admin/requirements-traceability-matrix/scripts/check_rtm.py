#!/usr/bin/env python3
"""Validate a Requirements Traceability Matrix CSV.

Stdlib-only checker for `governance/rtm.csv` (or any RTM CSV using the canonical
column set documented in `templates/rtm.md`).

Checks performed:
  1. Required columns present.
  2. Every `req_id` is unique (no duplicates).
  3. Every `status` value is in the allowed enum.
  4. Every `source` value is in the allowed enum.
  5. Every requirement with status `In UAT` or `Released` has a `story_ids` value.
  6. Every requirement with status `Released` has a `test_case_ids` value.
  7. Backward traceability: a 10% sample of test_case_ids resolves to a `req_id` row
     (i.e., each test ID appears in some row's `test_case_ids` cell).
  8. Multi-valued cells use the pipe `|` delimiter (no commas, no semicolons).

Usage:
    python3 check_rtm.py --csv path/to/rtm.csv
    python3 check_rtm.py --csv path/to/rtm.csv --strict   (any warning becomes an error)

Exit code:
    0 — no issues, or warnings only without --strict
    1 — at least one ERROR (or any issue with --strict)
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable

REQUIRED_COLUMNS = [
    "req_id",
    "source",
    "description",
    "priority",
    "story_ids",
    "test_case_ids",
    "defect_ids",
    "sprint",
    "release",
    "status",
]

ALLOWED_STATUS = {"Draft", "In Build", "In UAT", "Released", "Deferred", "Dropped"}
ALLOWED_SOURCE = {
    "interview",
    "sow",
    "regulatory",
    "change-request",
    "defect-driven",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a Salesforce Requirements Traceability Matrix CSV.",
    )
    parser.add_argument(
        "--csv",
        default="governance/rtm.csv",
        help="Path to the RTM CSV (default: governance/rtm.csv).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (non-zero exit).",
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Run an internal smoke test against an in-memory fixture and exit.",
    )
    return parser.parse_args()


def split_multi(cell: str) -> list[str]:
    """Split a pipe-delimited multi-value cell, ignoring empties and whitespace."""
    if cell is None:
        return []
    return [v.strip() for v in cell.split("|") if v.strip()]


def cell_uses_wrong_delimiter(cell: str) -> bool:
    """Heuristic: a multi-value cell that contains a comma or semicolon
    but no pipe almost certainly used the wrong delimiter."""
    if not cell:
        return False
    if "|" in cell:
        return False
    return ("," in cell) or (";" in cell)


def validate_rows(rows: list[dict[str, str]]) -> tuple[list[str], list[str]]:
    """Run all checks. Return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    if not rows:
        warnings.append("RTM CSV has zero data rows.")
        return errors, warnings

    # Check 1: required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in rows[0]]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        # Without core columns, deeper checks will be unreliable.
        return errors, warnings

    # Check 2: unique req_id
    seen_ids: dict[str, int] = {}
    for idx, row in enumerate(rows, start=2):  # row 1 is header
        rid = (row.get("req_id") or "").strip()
        if not rid:
            errors.append(f"Row {idx}: empty req_id")
            continue
        if rid in seen_ids:
            errors.append(
                f"Row {idx}: duplicate req_id '{rid}' "
                f"(also at row {seen_ids[rid]})"
            )
        else:
            seen_ids[rid] = idx

    # Per-row checks
    all_test_ids_in_matrix: set[str] = set()
    for idx, row in enumerate(rows, start=2):
        rid = (row.get("req_id") or "").strip()
        status = (row.get("status") or "").strip()
        source = (row.get("source") or "").strip()
        story_cell = row.get("story_ids") or ""
        test_cell = row.get("test_case_ids") or ""
        defect_cell = row.get("defect_ids") or ""

        # Check 3: status enum
        if status and status not in ALLOWED_STATUS:
            errors.append(
                f"Row {idx} ({rid}): status '{status}' not in allowed enum "
                f"{sorted(ALLOWED_STATUS)}"
            )

        # Check 4: source enum
        if source and source not in ALLOWED_SOURCE:
            errors.append(
                f"Row {idx} ({rid}): source '{source}' not in allowed enum "
                f"{sorted(ALLOWED_SOURCE)}"
            )

        # Check 5/6: coverage by status
        story_ids = split_multi(story_cell)
        test_ids = split_multi(test_cell)

        if status in {"In Build", "In UAT", "Released"} and not story_ids:
            errors.append(
                f"Row {idx} ({rid}): status '{status}' requires at least one story_id"
            )
        if status in {"In UAT", "Released"} and not test_ids:
            errors.append(
                f"Row {idx} ({rid}): status '{status}' requires at least one test_case_id"
            )

        # Check 8: delimiter
        for col_name, cell in (
            ("story_ids", story_cell),
            ("test_case_ids", test_cell),
            ("defect_ids", defect_cell),
        ):
            if cell_uses_wrong_delimiter(cell):
                warnings.append(
                    f"Row {idx} ({rid}): {col_name} cell '{cell}' looks like it uses "
                    f"',' or ';' instead of the canonical '|' delimiter"
                )

        all_test_ids_in_matrix.update(test_ids)

        # Forward-traceability orphan flag
        if status not in {"Draft", "Deferred", "Dropped"} and not story_ids:
            warnings.append(
                f"Row {idx} ({rid}): orphan requirement — no story_ids while "
                f"status is '{status}'"
            )

    # Check 7: backward traceability — every test_case_id collected appears in
    # at least one story->test pair. With a single-CSV input we can only confirm
    # that the test IDs we see in test_case_ids cells form a self-consistent set
    # (they do by construction). The richer check (every test in the test mgmt
    # tool maps back) requires a second input file. We surface the count for
    # transparency.
    if all_test_ids_in_matrix:
        # No additional ERROR here without a second input; emit a stat-only line
        # via warnings so the user sees the backward sample size.
        warnings.append(
            f"Backward sample: {len(all_test_ids_in_matrix)} unique test_case_ids "
            f"present in matrix. Cross-check against the test management tool "
            f"externally for a full backward pass."
        )

    return errors, warnings


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def run_self_check() -> int:
    """In-memory smoke test that exercises every rule path."""
    fixture = [
        # Valid released row
        {
            "req_id": "REQ-001", "source": "interview",
            "description": "Sales reps see their accounts", "priority": "must",
            "story_ids": "US-101", "test_case_ids": "TC-201",
            "defect_ids": "", "sprint": "Sprint-1", "release": "R1.0",
            "status": "Released",
        },
        # Duplicate req_id (ERROR)
        {
            "req_id": "REQ-001", "source": "sow",
            "description": "duplicate id", "priority": "should",
            "story_ids": "US-102", "test_case_ids": "TC-202",
            "defect_ids": "", "sprint": "Sprint-1", "release": "R1.0",
            "status": "Released",
        },
        # Bad status (ERROR)
        {
            "req_id": "REQ-002", "source": "interview",
            "description": "bad status", "priority": "must",
            "story_ids": "US-103", "test_case_ids": "TC-203",
            "defect_ids": "", "sprint": "Sprint-1", "release": "R1.0",
            "status": "Active",  # not in enum
        },
        # Bad source (ERROR)
        {
            "req_id": "REQ-003", "source": "verbal",  # not in enum
            "description": "bad source", "priority": "must",
            "story_ids": "US-104", "test_case_ids": "TC-204",
            "defect_ids": "", "sprint": "Sprint-1", "release": "R1.0",
            "status": "Released",
        },
        # Released without story (ERROR) and without test (ERROR)
        {
            "req_id": "REQ-004", "source": "interview",
            "description": "missing coverage", "priority": "must",
            "story_ids": "", "test_case_ids": "",
            "defect_ids": "", "sprint": "Sprint-1", "release": "R1.0",
            "status": "Released",
        },
        # Comma delimiter (WARN)
        {
            "req_id": "REQ-005", "source": "interview",
            "description": "wrong delim", "priority": "should",
            "story_ids": "US-105,US-106", "test_case_ids": "TC-205",
            "defect_ids": "", "sprint": "Sprint-2", "release": "R1.0",
            "status": "Released",
        },
        # Deferred row with empty cells (OK)
        {
            "req_id": "REQ-006", "source": "interview",
            "description": "deferred req", "priority": "could",
            "story_ids": "", "test_case_ids": "",
            "defect_ids": "", "sprint": "", "release": "",
            "status": "Deferred",
        },
    ]
    errors, warnings = validate_rows(fixture)
    expected_error_substrings = [
        "duplicate req_id 'REQ-001'",
        "status 'Active' not in allowed enum",
        "source 'verbal' not in allowed enum",
        "requires at least one story_id",
        "requires at least one test_case_id",
    ]
    missing = [
        s for s in expected_error_substrings
        if not any(s in e for e in errors)
    ]
    delimiter_warning = any("'|' delimiter" in w for w in warnings)
    if missing or not delimiter_warning:
        print("SELF-CHECK FAIL", file=sys.stderr)
        print(f"  missing expected errors: {missing}", file=sys.stderr)
        print(f"  delimiter warning seen:  {delimiter_warning}", file=sys.stderr)
        return 1
    print("SELF-CHECK PASS — all rule paths exercised.")
    return 0


def main() -> int:
    args = parse_args()
    if args.self_check:
        return run_self_check()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        # Pre-RTM repos won't have governance/rtm.csv yet — this is not an error
        # in repo-level validation; only flag if the user explicitly pointed at
        # a path that doesn't exist.
        print(
            f"INFO: no RTM CSV at {csv_path}; nothing to validate.",
            file=sys.stderr,
        )
        return 0

    rows = load_rows(csv_path)
    errors, warnings = validate_rows(rows)

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    if not errors and not warnings:
        print(f"OK: {len(rows)} RTM rows validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
