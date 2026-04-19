#!/usr/bin/env python3
"""Checker script for Apex Aggregate Queries skill.

Scans Apex source files (.cls) under a metadata directory for common
aggregate-query anti-patterns documented in references/llm-anti-patterns.md
and references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_aggregate_queries.py [--help]
    python3 check_apex_aggregate_queries.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Matches expr0 / expr1 … in get() calls — sign of missing alias
_RE_AUTO_ALIAS = re.compile(r"""ar\.get\(\s*['"]expr\d+['"]\s*\)""")

# WHERE clause containing an aggregate function — should be HAVING
_RE_WHERE_AGGREGATE = re.compile(
    r"""\bWHERE\b[^;]*?\b(SUM|COUNT|AVG|MIN|MAX)\s*\(""",
    re.IGNORECASE,
)

# GROUP BY inside a subquery — invalid in SOQL
_RE_GROUP_BY_IN_SUBQUERY = re.compile(
    r"""\(\s*SELECT\b[^)]*\bGROUP\s+BY\b""",
    re.IGNORECASE | re.DOTALL,
)

# Database.getQueryLocator with GROUP BY — pagination not supported
_RE_QUERY_LOCATOR_WITH_GROUP_BY = re.compile(
    r"""Database\s*\.\s*getQueryLocator\s*\([^)]*GROUP\s+BY""",
    re.IGNORECASE | re.DOTALL,
)

# Typed cast of AggregateResult to a concrete SObject type
_RE_TYPED_CAST_OF_AR = re.compile(
    r"""\(\s*(?!AggregateResult\b)\w+\s*\)\s*ar\b""",
)

# Direct field access on AggregateResult variable (ar.SomeField or ar.get without parens)
_RE_DIRECT_FIELD_ACCESS = re.compile(
    r"""\bar\s*\.\s*(?!get\s*\()(?!size\s*\()\w+""",
)


def _issues_in_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    def flag(pattern: re.Pattern, message: str) -> None:
        for m in pattern.finditer(src):
            line_no = src[: m.start()].count("\n") + 1
            issues.append(f"{path}:{line_no}: {message}")

    flag(
        _RE_AUTO_ALIAS,
        "Auto-assigned alias (expr0/expr1) used in ar.get() — assign explicit aliases in SOQL.",
    )
    flag(
        _RE_WHERE_AGGREGATE,
        "Aggregate function found in WHERE clause — use HAVING to filter on aggregate values.",
    )
    flag(
        _RE_GROUP_BY_IN_SUBQUERY,
        "GROUP BY inside a subquery — SOQL does not support GROUP BY in inner queries.",
    )
    flag(
        _RE_QUERY_LOCATOR_WITH_GROUP_BY,
        "Database.getQueryLocator() used with GROUP BY — aggregate queries do not support QueryMore/cursor pagination.",
    )
    flag(
        _RE_TYPED_CAST_OF_AR,
        "AggregateResult cast to a typed SObject — use ar.get('alias') and cast to the correct scalar type instead.",
    )

    return issues


def check_apex_aggregate_queries(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in Apex source files under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = list(manifest_dir.rglob("*.cls"))
    if not apex_files:
        # Not an error — project may have no Apex; return clean
        return issues

    for apex_file in sorted(apex_files):
        issues.extend(_issues_in_file(apex_file))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex source files for aggregate-query anti-patterns "
            "(missing aliases, WHERE-instead-of-HAVING, GROUP BY in subqueries, "
            "cursor pagination on aggregate queries, typed SObject casts of AggregateResult)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata to scan (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_apex_aggregate_queries(manifest_dir)

    if not issues:
        print("No aggregate-query issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
