#!/usr/bin/env python3
"""Checker script for SOQL Query Optimization skill.

Scans Apex source files (.cls, .trigger) for common SOQL anti-patterns:
  1. Leading wildcard LIKE patterns (LIKE '%...) — prevents index usage, no workaround
  2. NULL/empty checks on non-standard fields (WHERE Field__c = null / != null / != '')
  3. OR conditions in SOQL WHERE clauses — may bypass indexes if fields are non-indexed
  4. SOQL queries without a LIMIT clause — risky on large objects
  5. Formula field note — static analysis cannot detect formula fields; flagged as manual check

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_soql_query_optimization.py [--manifest-dir path/to/src]
    python3 check_soql_query_optimization.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Leading wildcard LIKE: LIKE '%something or LIKE "%something
LEADING_WILDCARD_RE = re.compile(
    r"""LIKE\s+['"][%]""",
    re.IGNORECASE,
)

# NULL / empty checks on custom fields (field name ends with __c or __r)
# Matches: WHERE Custom__c = null, != null, = '', != ''
NULL_CHECK_CUSTOM_RE = re.compile(
    r"""\bWHERE\b[^'"]*?\b(\w+__[cr])\s*(?:!=|=)\s*(?:null|''|"")""",
    re.IGNORECASE,
)

# OR inside a SOQL WHERE clause (within a string literal that looks like SOQL)
# Simplified: find string literals containing WHERE ... OR ...
SOQL_OR_RE = re.compile(
    r"""(?:SELECT\s+\S+.*?WHERE\s+.*?\bOR\b)""",
    re.IGNORECASE | re.DOTALL,
)

# SOQL query without LIMIT — look for SELECT...FROM...WHERE without LIMIT
# Catches both static SOQL in [ ] and dynamic SOQL in string literals
SOQL_NO_LIMIT_RE = re.compile(
    r"""\[?\s*SELECT\b(?:(?!LIMIT).)*?\bFROM\b(?:(?!LIMIT|\]|;).)*?(?:\]|;)""",
    re.IGNORECASE | re.DOTALL,
)

# Inline SOQL blocks (in square brackets): [SELECT ... FROM ... WHERE ...]
INLINE_SOQL_RE = re.compile(
    r"""\[\s*SELECT\b.*?\]""",
    re.IGNORECASE | re.DOTALL,
)

# Database.query( string ) dynamic SOQL calls
DYNAMIC_SOQL_RE = re.compile(
    r"""Database\.query\s*\(""",
    re.IGNORECASE,
)

# FIELDS(ALL) or FIELDS(STANDARD) — expensive on large objects
FIELDS_ALL_RE = re.compile(
    r"""\bFIELDS\s*\(\s*(?:ALL|STANDARD|CUSTOM)\s*\)""",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File scanning
# ---------------------------------------------------------------------------

def find_apex_files(root: Path) -> list[Path]:
    """Return all .cls and .trigger files under root."""
    apex_files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        apex_files.extend(root.rglob(ext))
    return sorted(apex_files)


def check_file(path: Path) -> list[str]:
    """Return a list of issue strings found in a single file."""
    issues: list[str] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: Could not read file — {exc}"]

    lines = source.splitlines()

    for line_num, line in enumerate(lines, start=1):
        location = f"{path}:{line_num}"

        # 1. Leading wildcard LIKE
        if LEADING_WILDCARD_RE.search(line):
            issues.append(
                f"{location}: LEADING WILDCARD — `LIKE '%...` prevents index usage. "
                "No index workaround exists. Switch to SOSL for full-text search or "
                "use a trailing wildcard (`LIKE 'value%`) if prefix match is sufficient."
            )

        # 2. NULL/empty checks on custom fields
        if NULL_CHECK_CUSTOM_RE.search(line):
            issues.append(
                f"{location}: NULL FILTER ON CUSTOM FIELD — `WHERE custom__c = null` "
                "or `!= null` is not served by default custom indexes (index tables "
                "exclude null rows). Request a null-inclusive custom index from "
                "Salesforce Support if this filter is needed on a large object."
            )

        # 3. OR conditions — flag for manual review
        stripped = line.strip()
        if re.search(r'\bOR\b', stripped, re.IGNORECASE) and re.search(
            r'\bWHERE\b', stripped, re.IGNORECASE
        ):
            issues.append(
                f"{location}: OR CONDITION IN WHERE — All fields in an OR clause "
                "must be individually indexed and selective for any index to be used. "
                "Consider decomposing into multiple queries if fields lack custom indexes."
            )

        # 4. FIELDS(ALL/STANDARD/CUSTOM)
        if FIELDS_ALL_RE.search(line):
            issues.append(
                f"{location}: FIELDS() KEYWORD — FIELDS(ALL), FIELDS(STANDARD), or "
                "FIELDS(CUSTOM) queries all fields on an object. This is expensive on "
                "large objects and should be replaced with an explicit field list."
            )

    # 5. Inline SOQL without LIMIT
    for match in INLINE_SOQL_RE.finditer(source):
        soql_block = match.group(0)
        if not re.search(r'\bLIMIT\b', soql_block, re.IGNORECASE):
            # Find approximate line number
            start_line = source[: match.start()].count("\n") + 1
            issues.append(
                f"{path}:{start_line}: MISSING LIMIT — Inline SOQL query has no LIMIT "
                "clause. On objects with large data volumes, unlimited result sets "
                "can cause heap or timeout issues. Add LIMIT or use OFFSET pagination."
            )

    # 6. Dynamic SOQL usage note
    if DYNAMIC_SOQL_RE.search(source):
        first_match = DYNAMIC_SOQL_RE.search(source)
        start_line = source[: first_match.start()].count("\n") + 1
        issues.append(
            f"{path}:{start_line}: DYNAMIC SOQL DETECTED — `Database.query()` is used. "
            "Verify that the WHERE clause in the dynamic query uses indexed fields. "
            "The same selectivity rules apply to dynamic and static SOQL."
        )

    return issues


# ---------------------------------------------------------------------------
# Manual check reminders
# ---------------------------------------------------------------------------

MANUAL_CHECKS = [
    "MANUAL CHECK: Formula fields in WHERE clauses cannot be detected statically. "
    "Search for any SOQL WHERE clause filters that reference formula field API names "
    "(fields whose definitions use formulas in Setup). Formula fields are not indexable.",
    "MANUAL CHECK: Run the Query Plan tool (Developer Console > Debug > Open Query Plan) "
    "on your slowest queries against large objects. Cost > 1.0 indicates a full-table scan.",
    "MANUAL CHECK: Verify that custom indexed fields have selectivity < 10% or < 333,333 "
    "matching records for the filter values used. Run GROUP BY aggregate queries to confirm.",
]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Apex files for SOQL anti-patterns that cause query timeouts and "
            "non-selective queries on large Salesforce objects."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for .cls and .trigger files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    apex_files = find_apex_files(manifest_dir)

    if not apex_files:
        print(f"No .cls or .trigger files found under: {manifest_dir}")
        print("Nothing to check.")
        return 0

    all_issues: list[str] = []
    for apex_file in apex_files:
        all_issues.extend(check_file(apex_file))

    # Print automated findings
    if all_issues:
        print(f"Found {len(all_issues)} issue(s) in {len(apex_files)} file(s):\n")
        for issue in all_issues:
            print(f"ISSUE: {issue}\n")
    else:
        print(f"No automated issues found in {len(apex_files)} file(s).")

    # Always print manual check reminders
    print("\n--- Manual checks required (cannot be detected statically) ---")
    for reminder in MANUAL_CHECKS:
        print(f"  {reminder}")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
