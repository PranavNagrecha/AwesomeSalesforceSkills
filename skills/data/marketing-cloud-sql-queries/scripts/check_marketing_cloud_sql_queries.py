#!/usr/bin/env python3
"""Checker script for Marketing Cloud SQL Queries skill.

Statically analyzes SQL query text for common Marketing Cloud Query Activity
anti-patterns documented in references/llm-anti-patterns.md and references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_cloud_sql_queries.py --sql "SELECT ... INTO ..."
    python3 check_marketing_cloud_sql_queries.py --sql-file path/to/query.sql
    python3 check_marketing_cloud_sql_queries.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Detection rules
# ---------------------------------------------------------------------------

# Each rule is (rule_id, description, regex_pattern, case_insensitive)
# A match means an issue is found.
_RULES: list[tuple[str, str, str, bool]] = [
    (
        "MC-SQL-001",
        "Non-T-SQL date function detected (NOW, SYSDATE, DATE_SUB, DATE_FORMAT, CURDATE). "
        "Use GETDATE(), DATEADD(), DATEDIFF(), or CONVERT() instead.",
        r"\b(NOW\s*\(|SYSDATE\s*\(|DATE_SUB\s*\(|DATE_FORMAT\s*\(|CURDATE\s*\()\b",
        True,
    ),
    (
        "MC-SQL-002",
        "INSERT INTO ... SELECT detected. Marketing Cloud Query Activities require "
        "SELECT ... INTO <target_de> syntax exclusively.",
        r"\bINSERT\s+INTO\b",
        True,
    ),
    (
        "MC-SQL-003",
        "Window function detected (ROW_NUMBER, RANK, DENSE_RANK, LEAD, LAG, NTILE, OVER). "
        "Window functions are not supported in Marketing Cloud SQL. "
        "Use GROUP BY with aggregate functions instead.",
        r"\b(ROW_NUMBER|RANK|DENSE_RANK|LEAD|LAG|NTILE|FIRST_VALUE|LAST_VALUE)\s*\(",
        True,
    ),
    (
        "MC-SQL-003b",
        "OVER clause detected (implies window function). Not supported in Marketing Cloud SQL.",
        r"\bOVER\s*\(",
        True,
    ),
    (
        "MC-SQL-004",
        "CTE (WITH clause) detected. Common Table Expressions are not supported in "
        "Marketing Cloud Query Activities. Decompose into separate Query Activities "
        "writing to intermediate Data Extensions instead.",
        r"^\s*WITH\s+\w+\s+AS\s*\(",
        True,
    ),
    (
        "MC-SQL-005",
        "Temp table reference detected (#table_name). Temp tables are not supported "
        "in Marketing Cloud Query Activities. Use a real Data Extension as staging.",
        r"#\w+",
        False,
    ),
    (
        "MC-SQL-006",
        "INTERVAL keyword detected. This is MySQL/PostgreSQL syntax. "
        "Use DATEADD(DAY, -N, GETDATE()) in Marketing Cloud SQL.",
        r"\bINTERVAL\b",
        True,
    ),
    (
        "MC-SQL-007",
        "Stored procedure syntax detected (CREATE PROCEDURE or EXEC). "
        "Stored procedures are not supported in Marketing Cloud Query Activities.",
        r"\b(CREATE\s+PROCEDURE|CREATE\s+PROC|EXEC\s+\w+)\b",
        True,
    ),
    (
        "MC-SQL-008",
        "NULL equality check detected (= NULL or <> NULL). "
        "Use IS NULL or IS NOT NULL instead — '= NULL' always evaluates to false in SQL.",
        r"[<>=!]\s*NULL\b",
        True,
    ),
    (
        "MC-SQL-009",
        "SELECT * detected. Enumerating all columns from a system data view is "
        "a performance risk and breaks if view schema changes. "
        "List only required columns explicitly.",
        r"\bSELECT\s+\*",
        True,
    ),
]

# Warnings (non-fatal suggestions)
_WARNINGS: list[tuple[str, str, str, bool]] = [
    (
        "MC-SQL-W001",
        "No date range filter detected on a system data view (_Sent, _Open, _Click, _Bounce, _Job). "
        "System data views retain ~6 months of data. An unbounded query will cause a full-table "
        "scan that likely exceeds the 30-minute timeout on high-volume accounts. "
        "Add: WHERE EventDate >= DATEADD(DAY, -N, GETDATE())",
        r"\b_(Sent|Open|Click|Bounce|Job)\b",
        True,
    ),
    (
        "MC-SQL-W002",
        "System data view join detected. Ensure the join uses JobID + SubscriberKey as the "
        "composite key, not EmailAddress alone. Joining on EmailAddress causes fan-out.",
        r"\bJOIN\s+_(Sent|Open|Click|Bounce|Job)\b|\b_(Sent|Open|Click|Bounce|Job)\b.{0,200}JOIN\b",
        True,
    ),
]


def _check_date_scope(sql: str) -> list[str]:
    """Warn if a system data view is referenced but no EventDate WHERE clause is present."""
    issues: list[str] = []
    sdv_pattern = re.compile(r"\b_(Sent|Open|Click|Bounce|Job)\b", re.IGNORECASE)
    date_filter_pattern = re.compile(r"\bEventDate\b.{0,60}DATEADD|DATEADD.{0,60}\bEventDate\b", re.IGNORECASE | re.DOTALL)

    if sdv_pattern.search(sql) and not date_filter_pattern.search(sql):
        issues.append(
            "MC-SQL-W001: System data view referenced without an EventDate date-range filter. "
            "Add WHERE EventDate >= DATEADD(DAY, -N, GETDATE()) to prevent full-table scans "
            "and respect the ~6-month retention window."
        )
    return issues


def check_sql(sql: str) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) lists for the given SQL text."""
    errors: list[str] = []
    warnings: list[str] = []

    for rule_id, description, pattern, case_insensitive in _RULES:
        flags = re.IGNORECASE | re.MULTILINE if case_insensitive else re.MULTILINE
        if re.search(pattern, sql, flags):
            errors.append(f"{rule_id}: {description}")

    # Date scope check (custom logic)
    warnings.extend(_check_date_scope(sql))

    # Join key check
    sdv_join_pattern = re.compile(
        r"\b_(Sent|Open|Click|Bounce|Job)\b", re.IGNORECASE
    )
    email_join_pattern = re.compile(r"EmailAddress\s*=", re.IGNORECASE)
    subscriber_key_pattern = re.compile(r"SubscriberKey\s*=", re.IGNORECASE)

    if sdv_join_pattern.search(sql) and email_join_pattern.search(sql) and not subscriber_key_pattern.search(sql):
        warnings.append(
            "MC-SQL-W002: System data view join appears to use EmailAddress without SubscriberKey. "
            "Use JobID + SubscriberKey as the composite join key to avoid fan-out from "
            "email addresses that map to multiple SubscriberKey values."
        )

    return errors, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Marketing Cloud SQL Query Activity statements for common anti-patterns. "
            "Validates T-SQL dialect compliance, date scope, join key correctness, and "
            "unsupported syntax (window functions, CTEs, temp tables, stored procedures)."
        ),
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--sql",
        help="SQL query text to check (pass as a quoted string).",
    )
    group.add_argument(
        "--sql-file",
        help="Path to a .sql file to check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.sql:
        sql_text = args.sql
        source_label = "<inline>"
    else:
        sql_path = Path(args.sql_file)
        if not sql_path.exists():
            print(f"ERROR: SQL file not found: {sql_path}", file=sys.stderr)
            return 2
        sql_text = sql_path.read_text(encoding="utf-8")
        source_label = str(sql_path)

    errors, warnings = check_sql(sql_text)

    if not errors and not warnings:
        print(f"OK: No issues found in {source_label}")
        return 0

    exit_code = 0

    for warning in warnings:
        print(f"WARN [{source_label}]: {warning}", file=sys.stderr)

    for error in errors:
        print(f"ERROR [{source_label}]: {error}", file=sys.stderr)
        exit_code = 1

    if exit_code == 0 and warnings:
        print(f"OK (with warnings): {source_label} — review WARN messages above.", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
