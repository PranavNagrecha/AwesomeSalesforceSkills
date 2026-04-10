#!/usr/bin/env python3
"""Checker script for Marketing Cloud Data Views skill.

Validates SQL query files intended for Marketing Cloud Automation Studio
data view access. Checks for common structural mistakes documented in
references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_cloud_data_views.py [--help]
    python3 check_marketing_cloud_data_views.py --manifest-dir path/to/sql/files
    python3 check_marketing_cloud_data_views.py --sql "SELECT ... INTO ... FROM _Sent ..."
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Known Marketing Cloud system data views (underscore-prefixed)
# ---------------------------------------------------------------------------
SYSTEM_DATA_VIEWS = {
    "_Sent", "_Open", "_Click", "_Bounce", "_Subscribers",
    "_Job", "_Complaint", "_SMSLog", "_UndeliveredSMS",
}

# Event-type data views that require date scoping and composite join keys
EVENT_DATA_VIEWS = {
    "_Sent", "_Open", "_Click", "_Bounce", "_Complaint", "_SMSLog",
}

# Invalid date functions (MySQL/PostgreSQL/ANSI) that fail in MC T-SQL
INVALID_DATE_FUNCTIONS = re.compile(
    r"\b(NOW\s*\(\s*\)|DATE_SUB\s*\(|SYSDATE\s*\(\s*\)|CURRENT_DATE|DATE_TRUNC\s*\(|INTERVAL\s+'\d+)",
    re.IGNORECASE,
)

# Correct T-SQL date anchor
VALID_DATE_FUNC = re.compile(r"\bGETDATE\s*\(\s*\)", re.IGNORECASE)
DATEADD_FUNC = re.compile(r"\bDATEADD\s*\(", re.IGNORECASE)

# Detect SELECT INTO pattern (required for MC SQL)
SELECT_INTO_PATTERN = re.compile(
    r"\bSELECT\b.+?\bINTO\b\s+\w",
    re.IGNORECASE | re.DOTALL,
)

# Detect INSERT INTO (invalid in MC)
INSERT_INTO_PATTERN = re.compile(r"\bINSERT\s+INTO\b", re.IGNORECASE)

# Detect use of system data views
DATA_VIEW_REFS = re.compile(
    r"\b(" + "|".join(re.escape(v) for v in SYSTEM_DATA_VIEWS) + r")\b",
    re.IGNORECASE,
)

# Detect JOINs between event data views
EVENT_VIEW_JOIN = re.compile(
    r"\bJOIN\s+(" + "|".join(re.escape(v) for v in EVENT_DATA_VIEWS) + r")\b",
    re.IGNORECASE,
)

# Detect presence of JobID in ON clause (simple heuristic)
JOBID_IN_JOIN = re.compile(r"\bJobID\b", re.IGNORECASE)

# Detect EventDate filter in WHERE clause
EVENTDATE_WHERE = re.compile(r"\bEventDate\b.+?\bDATEADD\b", re.IGNORECASE | re.DOTALL)

# Detect suspicious long date ranges (> 180 days)
LONG_DATEADD = re.compile(
    r"\bDATEADD\s*\(\s*(?:DAY|DD|D)\s*,\s*-(\d+)\s*,",
    re.IGNORECASE,
)
YEAR_DATEADD = re.compile(
    r"\bDATEADD\s*\(\s*(?:YEAR|YY|YYYY)\s*,\s*-(\d+)\s*,",
    re.IGNORECASE,
)

# Detect CTE (WITH clause) — not supported in MC
CTE_PATTERN = re.compile(r"^\s*WITH\s+\w+\s+AS\s*\(", re.IGNORECASE | re.MULTILINE)

# Detect window functions — not supported in MC
WINDOW_FUNC = re.compile(r"\bROW_NUMBER\s*\(\s*\)\s*OVER\b|\bRANK\s*\(\s*\)\s*OVER\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_select_into_required(sql: str) -> list[str]:
    """Every MC query must use SELECT INTO, not bare SELECT or INSERT INTO."""
    issues = []
    has_data_view = DATA_VIEW_REFS.search(sql)
    if not has_data_view:
        return issues
    if INSERT_INTO_PATTERN.search(sql):
        issues.append(
            "INSERT INTO detected: Marketing Cloud SQL uses SELECT ... INTO <target_DE> syntax, "
            "not INSERT INTO ... SELECT. Rewrite using SELECT INTO."
        )
    if not SELECT_INTO_PATTERN.search(sql):
        issues.append(
            "No SELECT INTO detected: Marketing Cloud SQL Query Activities require "
            "SELECT <columns> INTO <TargetDE> FROM <source>. Bare SELECT statements are not valid."
        )
    return issues


def check_date_functions(sql: str) -> list[str]:
    """Flag non-T-SQL date functions that fail in Marketing Cloud."""
    issues = []
    matches = INVALID_DATE_FUNCTIONS.findall(sql)
    if matches:
        issues.append(
            f"Non-T-SQL date function(s) detected: {set(matches)}. "
            "Marketing Cloud uses T-SQL: GETDATE(), DATEADD(), DATEDIFF(), CONVERT(). "
            "Remove NOW(), DATE_SUB(), SYSDATE(), CURRENT_DATE, DATE_TRUNC()."
        )
    return issues


def check_event_view_date_scope(sql: str) -> list[str]:
    """Warn if an event data view is queried without a date WHERE clause."""
    issues = []
    event_views_used = [v for v in EVENT_DATA_VIEWS if re.search(r"\b" + re.escape(v) + r"\b", sql, re.IGNORECASE)]
    if not event_views_used:
        return issues
    if not EVENTDATE_WHERE.search(sql) and not VALID_DATE_FUNC.search(sql):
        issues.append(
            f"Event data view(s) referenced ({', '.join(event_views_used)}) without a "
            "date-scoped WHERE clause. System data views retain only ~6 months of data. "
            "Add WHERE EventDate >= DATEADD(DAY, -N, GETDATE()) to avoid full-table scans "
            "and timeout failures."
        )
    return issues


def check_retention_window(sql: str) -> list[str]:
    """Flag DATEADD patterns that exceed the ~6-month (180-day) retention window."""
    issues = []
    for match in LONG_DATEADD.finditer(sql):
        days = int(match.group(1))
        if days > 180:
            issues.append(
                f"DATEADD with -{days} days detected: Marketing Cloud engagement data views "
                "retain only approximately 180 days (~6 months) of data. Queries spanning longer "
                "windows return incomplete results without error."
            )
    for match in YEAR_DATEADD.finditer(sql):
        years = int(match.group(1))
        if years >= 1:
            issues.append(
                f"DATEADD with -{years} year(s) detected: Marketing Cloud engagement data views "
                "retain only ~6 months of data. This query will silently return incomplete results."
            )
    return issues


def check_cross_view_join_keys(sql: str) -> list[str]:
    """Warn if a JOIN between event data views does not include JobID."""
    issues = []
    if not EVENT_VIEW_JOIN.search(sql):
        return issues
    # Count how many event data views are referenced (source + join targets)
    event_view_count = sum(
        1 for v in EVENT_DATA_VIEWS
        if re.search(r"\b" + re.escape(v) + r"\b", sql, re.IGNORECASE)
    )
    if event_view_count >= 2 and not JOBID_IN_JOIN.search(sql):
        issues.append(
            "JOIN between two event data views detected without JobID in the query. "
            "Joins between _Sent, _Open, _Click, _Bounce etc. must use "
            "JobID + SubscriberKey as the composite key to avoid Cartesian fan-out. "
            "Example: ON s.JobID = c.JobID AND s.SubscriberKey = c.SubscriberKey"
        )
    return issues


def check_unsupported_features(sql: str) -> list[str]:
    """Detect SQL features not supported in Marketing Cloud T-SQL."""
    issues = []
    if CTE_PATTERN.search(sql):
        issues.append(
            "WITH (CTE) clause detected: Common Table Expressions are not supported "
            "in Marketing Cloud SQL Query Activities. Refactor using subqueries or "
            "intermediate Data Extensions."
        )
    if WINDOW_FUNC.search(sql):
        issues.append(
            "Window function (ROW_NUMBER() OVER or RANK() OVER) detected: "
            "Window functions are not supported in Marketing Cloud SQL. "
            "Use GROUP BY with MAX() / MIN() or stage results to an intermediate DE "
            "for deduplication."
        )
    return issues


# ---------------------------------------------------------------------------
# File-level scanner
# ---------------------------------------------------------------------------

def check_sql_file(path: Path) -> list[str]:
    """Read a .sql file and run all checks. Returns list of issue strings."""
    try:
        sql = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"Could not read file {path}: {exc}"]

    if not DATA_VIEW_REFS.search(sql):
        return []  # Not a data view query — skip

    issues: list[str] = []
    for checker in [
        check_select_into_required,
        check_date_functions,
        check_event_view_date_scope,
        check_retention_window,
        check_cross_view_join_keys,
        check_unsupported_features,
    ]:
        issues.extend(checker(sql))

    return [f"[{path}] {issue}" for issue in issues]


def check_sql_string(sql: str) -> list[str]:
    """Run all checks on an inline SQL string. Returns list of issue strings."""
    issues: list[str] = []
    for checker in [
        check_select_into_required,
        check_date_functions,
        check_event_view_date_scope,
        check_retention_window,
        check_cross_view_join_keys,
        check_unsupported_features,
    ]:
        issues.extend(checker(sql))
    return issues


# ---------------------------------------------------------------------------
# Directory scanner
# ---------------------------------------------------------------------------

def check_marketing_cloud_data_views(manifest_dir: Path) -> list[str]:
    """Scan manifest_dir for .sql files referencing data views and return issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    sql_files = list(manifest_dir.rglob("*.sql"))
    if not sql_files:
        return []  # No SQL files — nothing to check

    for sql_file in sql_files:
        issues.extend(check_sql_file(sql_file))

    return issues


# ---------------------------------------------------------------------------
# Argument parsing and main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Marketing Cloud SQL queries that reference system data views. "
            "Checks for missing SELECT INTO, invalid date functions, missing date scoping, "
            "excessive retention window, missing composite join keys, and unsupported features."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for .sql files (default: current directory).",
    )
    parser.add_argument(
        "--sql",
        default=None,
        help="Inline SQL string to check (skips file scanning).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.sql:
        issues = check_sql_string(args.sql)
    else:
        manifest_dir = Path(args.manifest_dir)
        issues = check_marketing_cloud_data_views(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
