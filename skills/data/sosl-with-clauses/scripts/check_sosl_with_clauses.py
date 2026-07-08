#!/usr/bin/env python3
"""Linter for SOSL WITH clauses.

Checks a SOSL FIND statement (or every FIND statement found in a source tree)
for the mistakes documented in references/gotchas.md and
references/llm-anti-patterns.md:

  * WITH clauses out of the fixed canonical order
  * WITH SNIPPET target_length outside the 50-1,000 range
  * WITH SPELL_CORRECTION value that is not true/false
  * DATA CATEGORY specifiers joined with OR / AND NOT (only AND is allowed)
  * WITH DATA CATEGORY without a RETURNING clause / without WHERE PublishStatus
  * SNIPPET / HIGHLIGHT expected on a wildcard (*, ?) search term

Stdlib only -- no pip dependencies. Best-effort static lint, not a full parser.

Usage:
    python3 check_sosl_with_clauses.py --query "FIND {x} RETURNING Account WITH HIGHLIGHT"
    python3 check_sosl_with_clauses.py --file path/to/query.sosl
    python3 check_sosl_with_clauses.py --manifest-dir force-app   # scan *.cls/*.trigger/*.apex/*.sosl

Exit code 0 = no issues, 1 = issues found (or a usage error).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Canonical order of the WITH clauses (SOSL Syntax reference).
CANONICAL_ORDER = [
    "DIVISIONFILTER",
    "DATA CATEGORY",
    "SNIPPET",
    "NETWORK",
    "PRICEBOOKID",
    "METADATA",
    "HIGHLIGHT",
    "SPELL_CORRECTION",
]
_ORDER_INDEX = {name: i for i, name in enumerate(CANONICAL_ORDER)}

SNIPPET_MIN, SNIPPET_MAX = 50, 1000
SOURCE_SUFFIXES = {".cls", ".trigger", ".apex", ".sosl", ".txt"}

# Match a WITH <clause-keyword>. DATA CATEGORY has an internal space.
_WITH_CLAUSE_RE = re.compile(
    r"\bWITH\s+(DIVISIONFILTER|DATA\s+CATEGORY|SNIPPET|NETWORK|PRICEBOOKID|"
    r"METADATA|HIGHLIGHT|SPELL_CORRECTION)\b",
    re.IGNORECASE,
)
_SNIPPET_LEN_RE = re.compile(
    r"\bWITH\s+SNIPPET\s*\(\s*target_length\s*=\s*(\d+)\s*\)", re.IGNORECASE
)
_SNIPPET_BARE_RE = re.compile(r"\bWITH\s+SNIPPET\b", re.IGNORECASE)
_SPELL_RE = re.compile(r"\bWITH\s+SPELL_CORRECTION\s*=\s*([A-Za-z0-9_]+)", re.IGNORECASE)
_FIND_TERM_RE = re.compile(r"\bFIND\s*(?:\{([^}]*)\}|'([^']*)'|:\s*\w+)", re.IGNORECASE)
# Pull individual SOSL statements out of a larger source file.
_STATEMENT_RE = re.compile(r"\bFIND\b.*?(?:\]|;|\Z)", re.IGNORECASE | re.DOTALL)


def _normalize(keyword: str) -> str:
    return re.sub(r"\s+", " ", keyword).strip().upper()


def _clause_order_issues(query: str) -> list[str]:
    issues: list[str] = []
    seen = [(_normalize(m.group(1)), m.start()) for m in _WITH_CLAUSE_RE.finditer(query)]
    last_idx = -1
    last_name = None
    for name, _pos in seen:
        idx = _ORDER_INDEX[name]
        if idx <= last_idx:
            issues.append(
                f"WITH {name} appears after WITH {last_name} but the fixed SOSL clause "
                f"order is: {', '.join(CANONICAL_ORDER)}"
            )
        last_idx = idx
        last_name = name
    return issues


def _snippet_issues(query: str) -> list[str]:
    issues: list[str] = []
    for m in _SNIPPET_LEN_RE.finditer(query):
        n = int(m.group(1))
        if not (SNIPPET_MIN <= n <= SNIPPET_MAX):
            issues.append(
                f"WITH SNIPPET target_length={n} is outside the valid {SNIPPET_MIN}-"
                f"{SNIPPET_MAX} range; an invalid value silently defaults to ~300"
            )
    return issues


def _spell_correction_issues(query: str) -> list[str]:
    issues: list[str] = []
    for m in _SPELL_RE.finditer(query):
        val = m.group(1).lower()
        if val not in ("true", "false"):
            issues.append(
                f"WITH SPELL_CORRECTION = {m.group(1)} is invalid; it accepts only "
                f"true or false (defaults to true)"
            )
    return issues


def _data_category_issues(query: str) -> list[str]:
    issues: list[str] = []
    dc = re.search(r"\bWITH\s+DATA\s+CATEGORY\b", query, re.IGNORECASE)
    if not dc:
        return issues
    if not re.search(r"\bRETURNING\b", query, re.IGNORECASE):
        issues.append(
            "WITH DATA CATEGORY requires a RETURNING clause naming the object to search"
        )
    if not re.search(r"\bPublishStatus\b", query, re.IGNORECASE):
        issues.append(
            "WITH DATA CATEGORY requires a WHERE filter on PublishStatus "
            "(e.g. WHERE PublishStatus='online')"
        )
    # Only AND may join multiple category specifiers.
    tail = query[dc.end():]
    tail = re.split(r"\bWITH\b|\bLIMIT\b|\bUPDATE\b", tail, maxsplit=1, flags=re.IGNORECASE)[0]
    if re.search(r"\bOR\b", tail, re.IGNORECASE) or re.search(r"\bAND\s+NOT\b", tail, re.IGNORECASE):
        issues.append(
            "WITH DATA CATEGORY specifiers may be joined only with AND; OR and AND NOT "
            "are not supported"
        )
    return issues


def _wildcard_shaping_issues(query: str) -> list[str]:
    issues: list[str] = []
    term_match = _FIND_TERM_RE.search(query)
    term = ""
    if term_match:
        term = term_match.group(1) or term_match.group(2) or ""
    if not term:
        return issues
    if "*" in term or "?" in term:
        if _SNIPPET_BARE_RE.search(query):
            issues.append(
                "FIND term contains a wildcard (*/?) with WITH SNIPPET; snippets are not "
                "generated for wildcard search terms"
            )
        if re.search(r"\bWITH\s+HIGHLIGHT\b", query, re.IGNORECASE):
            issues.append(
                "FIND term contains a wildcard (*/?) with WITH HIGHLIGHT; wildcard terms "
                "are not highlighted"
            )
    return issues


def lint_sosl(query: str) -> list[str]:
    """Return a list of issue strings for a single SOSL statement."""
    query = query.strip()
    if not query:
        return []
    issues: list[str] = []
    issues.extend(_clause_order_issues(query))
    issues.extend(_snippet_issues(query))
    issues.extend(_spell_correction_issues(query))
    issues.extend(_data_category_issues(query))
    issues.extend(_wildcard_shaping_issues(query))
    return issues


def _iter_statements(text: str):
    for m in _STATEMENT_RE.finditer(text):
        stmt = m.group(0)
        # Only bother with statements that actually use a WITH clause.
        if _WITH_CLAUSE_RE.search(stmt):
            yield stmt


def _lint_text(text: str, label: str) -> list[str]:
    issues: list[str] = []
    for stmt in _iter_statements(text):
        for issue in lint_sosl(stmt):
            issues.append(f"{label}: {issue}")
    return issues


def _lint_file(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: could not read ({exc})"]
    return _lint_text(text, str(path))


def _lint_manifest(root: Path) -> list[str]:
    if not root.exists():
        return [f"Manifest directory not found: {root}"]
    issues: list[str] = []
    scanned = 0
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES:
            scanned += 1
            issues.extend(_lint_file(path))
    if scanned == 0:
        return [f"No SOSL-bearing source files ({', '.join(sorted(SOURCE_SUFFIXES))}) under {root}"]
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint SOSL WITH clauses for order, range, and object/version rules.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--query", help="A single SOSL FIND statement to lint.")
    group.add_argument("--file", help="Path to a file containing one or more SOSL statements.")
    group.add_argument(
        "--manifest-dir",
        help="Root directory to scan for SOSL in *.cls/*.trigger/*.apex/*.sosl/*.txt files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.query:
        issues = [f"--query: {i}" for i in lint_sosl(args.query)]
    elif args.file:
        issues = _lint_file(Path(args.file))
    elif args.manifest_dir:
        issues = _lint_manifest(Path(args.manifest_dir))
    else:
        # Default: read a query from stdin if piped, else show usage.
        if not sys.stdin.isatty():
            data = sys.stdin.read()
            issues = [f"stdin: {i}" for i in lint_sosl(data)]
        else:
            print(
                "Provide --query, --file, --manifest-dir, or pipe a SOSL statement on stdin.",
                file=sys.stderr,
            )
            return 1

    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
