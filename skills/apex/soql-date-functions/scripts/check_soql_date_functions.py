#!/usr/bin/env python3
"""Checker for SOQL date-function usage.

Scans SOQL text for the documented mistakes in references/gotchas.md and
references/llm-anti-patterns.md:

  ISSUE (exit 1 — the query will not compile):
    * a date-function result compared to a date literal in WHERE
    * a date function in SELECT with no matching GROUP BY expression
    * a hallucinated / misspelled date-function name

  ADVISORY (printed, does not affect exit code — verify by hand):
    * FISCAL_* usage (unsupported when custom fiscal years are enabled)
    * DAY_ONLY()/HOUR_IN_DAY() usage (require a DateTime field, not a Date field)

Stdlib only — no pip dependencies.

Usage:
    python3 check_soql_date_functions.py --query "SELECT CALENDAR_YEAR(CloseDate) ..."
    python3 check_soql_date_functions.py --manifest-dir force-app/main/default
    echo "SELECT ..." | python3 check_soql_date_functions.py --stdin

With --manifest-dir it extracts inline bracketed SOQL ([ SELECT ... ]) and quoted
dynamic SOQL ('SELECT ...') from .cls/.trigger/.apex files, and the whole content of
.soql files. Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# The 13 documented SOQL date functions.
DATE_FUNCS = (
    "CALENDAR_MONTH",
    "CALENDAR_QUARTER",
    "CALENDAR_YEAR",
    "DAY_IN_MONTH",
    "DAY_IN_WEEK",
    "DAY_IN_YEAR",
    "DAY_ONLY",
    "FISCAL_MONTH",
    "FISCAL_QUARTER",
    "FISCAL_YEAR",
    "HOUR_IN_DAY",
    "WEEK_IN_MONTH",
    "WEEK_IN_YEAR",
)
FISCAL_FUNCS = {"FISCAL_MONTH", "FISCAL_QUARTER", "FISCAL_YEAR"}
DATETIME_ONLY_FUNCS = {"DAY_ONLY", "HOUR_IN_DAY"}

# Common hallucinated names -> suggested real function (or None when there is no equivalent).
BAD_FUNCS = {
    "CALENDAR_DAY": "DAY_IN_MONTH",
    "DAY_OF_WEEK": "DAY_IN_WEEK",
    "DAY_OF_MONTH": "DAY_IN_MONTH",
    "DAY_OF_YEAR": "DAY_IN_YEAR",
    "WEEK_OF_YEAR": "WEEK_IN_YEAR",
    "WEEK_OF_MONTH": "WEEK_IN_MONTH",
    "HOUR_OF_DAY": "HOUR_IN_DAY",
    "FISCAL_WEEK": None,
    "CALENDAR_WEEK": "WEEK_IN_YEAR",
}

_FUNC_ALT = "|".join(DATE_FUNCS)
_BAD_ALT = "|".join(re.escape(name) for name in BAD_FUNCS)

# A date literal: an ISO date (optionally with time) or a SOQL relative date literal.
_ISO = r"\d{4}-\d{2}-\d{2}(?:T[0-9:.+\-Z]+)?"
_REL_SIMPLE = (
    r"YESTERDAY|TODAY|TOMORROW|LAST_WEEK|THIS_WEEK|NEXT_WEEK|LAST_MONTH|THIS_MONTH|"
    r"NEXT_MONTH|LAST_90_DAYS|NEXT_90_DAYS|LAST_QUARTER|THIS_QUARTER|NEXT_QUARTER|"
    r"LAST_YEAR|THIS_YEAR|NEXT_YEAR|LAST_FISCAL_QUARTER|THIS_FISCAL_QUARTER|"
    r"NEXT_FISCAL_QUARTER|LAST_FISCAL_YEAR|THIS_FISCAL_YEAR|NEXT_FISCAL_YEAR"
)
_REL_PARAM = (
    r"(?:LAST_N_DAYS|NEXT_N_DAYS|N_DAYS_AGO|LAST_N_WEEKS|NEXT_N_WEEKS|N_WEEKS_AGO|"
    r"LAST_N_MONTHS|NEXT_N_MONTHS|N_MONTHS_AGO|LAST_N_QUARTERS|NEXT_N_QUARTERS|"
    r"N_QUARTERS_AGO|LAST_N_YEARS|NEXT_N_YEARS|N_YEARS_AGO|LAST_N_FISCAL_QUARTERS|"
    r"NEXT_N_FISCAL_QUARTERS|N_FISCAL_QUARTERS_AGO|LAST_N_FISCAL_YEARS|"
    r"NEXT_N_FISCAL_YEARS|N_FISCAL_YEARS_AGO)\s*:\s*\d+"
)
_LITERAL = rf"(?:{_ISO}|(?:{_REL_SIMPLE})\b|{_REL_PARAM})"

RE_FUNC_CALL = re.compile(rf"\b({_FUNC_ALT})\s*\(\s*([A-Za-z0-9_.]+)\s*\)", re.IGNORECASE)
RE_BAD_FUNC = re.compile(rf"\b({_BAD_ALT})\s*\(", re.IGNORECASE)
RE_LITERAL_CMP = re.compile(
    rf"\b({_FUNC_ALT})\s*\([^)]*\)\s*(=|!=|<>|<=|>=|<|>)\s*({_LITERAL})",
    re.IGNORECASE,
)

RE_SELECT = re.compile(r"\bSELECT\b(.*?)\bFROM\b", re.IGNORECASE | re.DOTALL)
RE_WHERE = re.compile(
    r"\bWHERE\b(.*?)(?:\bGROUP\s+BY\b|\bWITH\b|\bORDER\s+BY\b|\bLIMIT\b|$)",
    re.IGNORECASE | re.DOTALL,
)
RE_GROUP = re.compile(
    r"\bGROUP\s+BY\b(.*?)(?:\bHAVING\b|\bORDER\s+BY\b|\bLIMIT\b|$)",
    re.IGNORECASE | re.DOTALL,
)

# SOQL extraction from source files.
RE_BRACKET_SOQL = re.compile(r"\[\s*(SELECT\b[\s\S]*?)\]", re.IGNORECASE)
RE_QUOTED_SOQL = re.compile(r"['\"]\s*(SELECT\b[\s\S]*?)['\"]", re.IGNORECASE)
SOURCE_EXTS = {".cls", ".trigger", ".apex"}


def _funcs_in(fragment: str) -> set[tuple[str, str]]:
    """Return {(FUNC_UPPER, arg_lower)} for date functions in a query fragment."""
    return {
        (m.group(1).upper(), m.group(2).lower())
        for m in RE_FUNC_CALL.finditer(fragment or "")
    }


def check_query(query: str, source: str, issues: list[str], advisories: list[str]) -> None:
    tag = f"{source}: " if source else ""

    # 1. Hallucinated / misspelled function names.
    for m in RE_BAD_FUNC.finditer(query):
        name = m.group(1).upper()
        suggestion = BAD_FUNCS.get(name)
        hint = f" — did you mean {suggestion}()?" if suggestion else " — no such SOQL date function"
        issues.append(f"{tag}'{name}()' is not a SOQL date function{hint}")

    # 2. Date-function result compared to a date literal in WHERE.
    where_m = RE_WHERE.search(query)
    where_text = where_m.group(1) if where_m else ""
    for m in RE_LITERAL_CMP.finditer(where_text):
        func, op, literal = m.group(1).upper(), m.group(2), m.group(3).strip()
        issues.append(
            f"{tag}{func}(...) {op} {literal} compares a date-function result to a date "
            f"literal — compare to an integer instead (a date function returns a number)"
        )

    # 3. Date function in SELECT with no matching GROUP BY expression.
    select_m = RE_SELECT.search(query)
    if select_m:
        in_select = _funcs_in(select_m.group(1))
        group_m = RE_GROUP.search(query)
        in_group = _funcs_in(group_m.group(1)) if group_m else set()
        for func, arg in sorted(in_select - in_group):
            issues.append(
                f"{tag}{func}({arg}) appears in SELECT but not in GROUP BY — a date function "
                f"in SELECT must also appear, unchanged, in the GROUP BY clause"
            )

    # 4/5. Advisories for fiscal and dateTime-only functions.
    used = {func for func, _ in _funcs_in(query)}
    for func in sorted(used & FISCAL_FUNCS):
        advisories.append(
            f"{tag}{func}() is unsupported when the org has custom fiscal years enabled — "
            f"verify the org uses standard fiscal years"
        )
    datetime_only = sorted(
        (func, arg) for func, arg in _funcs_in(query) if func in DATETIME_ONLY_FUNCS
    )
    for func, arg in datetime_only:
        advisories.append(
            f"{tag}{func}({arg}) requires a DateTime field — confirm '{arg}' is a "
            f"DateTime, not a Date, field"
        )


def _extract_queries(text: str, ext: str) -> list[str]:
    if ext == ".soql":
        return [q.strip() for q in text.split(";") if "select" in q.lower()]
    queries: list[str] = []
    queries.extend(m.group(1) for m in RE_BRACKET_SOQL.finditer(text))
    queries.extend(m.group(1) for m in RE_QUOTED_SOQL.finditer(text))
    return queries


def check(manifest_dir: Path) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    advisories: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"], advisories

    files = [
        p
        for p in manifest_dir.rglob("*")
        if p.is_file() and (p.suffix in SOURCE_EXTS or p.suffix == ".soql")
    ]
    if not files:
        return (
            [f"No .cls/.trigger/.apex/.soql files found under {manifest_dir} — nothing to check."],
            advisories,
        )

    found_any = False
    for path in sorted(files):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            issues.append(f"{path}: could not read ({exc})")
            continue
        for i, query in enumerate(_extract_queries(text, path.suffix), start=1):
            found_any = True
            check_query(query, f"{path} (query {i})", issues, advisories)

    if not found_any:
        advisories.append(f"No SOQL SELECT statements found under {manifest_dir}.")
    return issues, advisories


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check SOQL date-function usage for documented compile-time mistakes.",
    )
    parser.add_argument("--manifest-dir", default=".", help="Root of a Salesforce source tree.")
    parser.add_argument("--query", help="Check a single SOQL string instead of scanning files.")
    parser.add_argument("--stdin", action="store_true", help="Read one SOQL string from stdin.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.stdin:
        source_query = sys.stdin.read()
    else:
        source_query = args.query

    if source_query is not None:
        issues: list[str] = []
        advisories: list[str] = []
        check_query(source_query, "query", issues, advisories)
    else:
        issues, advisories = check(Path(args.manifest_dir))

    for advisory in advisories:
        print(f"INFO: {advisory}")
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    if issues:
        return 1
    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
