#!/usr/bin/env python3
"""Checker for SOQL FOR VIEW / FOR REFERENCE misuse in Apex source.

Scans a source tree of Apex classes (`*.cls`) and triggers (`*.trigger`) for the
optional `FOR VIEW` and `FOR REFERENCE` SOQL clauses and reports the misuse
patterns documented in references/gotchas.md and references/llm-anti-patterns.md:

  * clause used in a context with no viewing user (trigger / Batchable /
    Schedulable / Queueable) — the docs say to use it "only when you are sure
    that the retrieved records will definitely be viewed by the logged-in user";
  * clause on an unbounded query (no LIMIT and no `WHERE Id` filter) — floods
    Recent Items / search auto-complete;
  * clause on an aggregate query (COUNT() / GROUP BY) — no records to "view";
  * both clauses in one query — the reference shows them only individually and
    the grammar is an alternation `{FOR VIEW | FOR REFERENCE}`.

Stdlib only — no pip dependencies. Exit code 0 = no issues, 1 = issues found.

Usage:
    python3 check_soql_for_view_and_for_reference.py [--manifest-dir path]
    python3 check_soql_for_view_and_for_reference.py --manifest-dir force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# The clause itself (word-bounded, case-insensitive; Apex/SOQL are case-insensitive).
CLAUSE_RE = re.compile(r"\bFOR\s+(VIEW|REFERENCE)\b", re.IGNORECASE)
SELECT_RE = re.compile(r"\bSELECT\b", re.IGNORECASE)
LIMIT_RE = re.compile(r"\bLIMIT\b", re.IGNORECASE)
# A bounded, by-Id filter such as `WHERE Id = :recordId` or `WHERE Id IN :ids`.
WHERE_ID_RE = re.compile(r"\bWHERE\b[^\]';]*\bId\b\s*(=|\bIN\b)", re.IGNORECASE)
AGGREGATE_RE = re.compile(r"\bCOUNT\s*\(|\bGROUP\s+BY\b", re.IGNORECASE)
FOR_VIEW_RE = re.compile(r"\bFOR\s+VIEW\b", re.IGNORECASE)
FOR_REFERENCE_RE = re.compile(r"\bFOR\s+REFERENCE\b", re.IGNORECASE)
# Class-wide async / no-viewing-user contexts.
ASYNC_CONTEXT_RE = re.compile(
    r"implements[^{;]*\b(Database\.Batchable|Schedulable|Queueable)\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex source for SOQL FOR VIEW / FOR REFERENCE misuse.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source metadata (scans *.cls and *.trigger beneath it).",
    )
    return parser.parse_args()


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _query_context(text: str, clause_start: int, clause_end: int) -> str:
    """Return the query text from the nearest preceding SELECT to the clause end."""
    select_starts = [m.start() for m in SELECT_RE.finditer(text, 0, clause_start)]
    start = select_starts[-1] if select_starts else max(0, clause_start - 400)
    return text[start:clause_end]


def _file_context_note(text: str, suffix: str) -> str | None:
    """Return a short label if the whole file is a no-viewing-user context."""
    if suffix == ".trigger":
        return "trigger"
    if ASYNC_CONTEXT_RE.search(text):
        return "async class (Batchable/Schedulable/Queueable)"
    return None


def check_file(path: Path, issues: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: could not read file ({exc})")
        return

    matches = list(CLAUSE_RE.finditer(text))
    if not matches:
        return

    context_note = _file_context_note(text, path.suffix.lower())
    seen_queries: set[int] = set()

    for match in matches:
        line = _line_of(text, match.start())
        loc = f"{path}:{line}"
        clause = match.group(0).upper()

        query = _query_context(text, match.start(), match.end())
        # De-duplicate: a single query carrying both clauses reports its
        # combined/aggregate/unbounded findings once, keyed by the SELECT start.
        query_key = match.start() - len(query)

        if context_note is not None:
            issues.append(
                f"{loc}: `{clause}` used in a {context_note} — no logged-in user is viewing "
                f"these records; the clause incorrectly updates usage information. Remove it here."
            )

        if query_key not in seen_queries:
            seen_queries.add(query_key)

            has_both = bool(FOR_VIEW_RE.search(query)) and bool(FOR_REFERENCE_RE.search(query))
            if has_both:
                issues.append(
                    f"{loc}: query uses BOTH FOR VIEW and FOR REFERENCE — the reference shows them "
                    f"only individually (grammar is an alternation). Use one clause per query."
                )

            if AGGREGATE_RE.search(query):
                issues.append(
                    f"{loc}: `{clause}` on an aggregate query (COUNT()/GROUP BY) — there are no "
                    f"individual records to mark viewed. Remove the clause."
                )

            if not LIMIT_RE.search(query) and not WHERE_ID_RE.search(query):
                issues.append(
                    f"{loc}: `{clause}` on an unbounded query (no LIMIT and no `WHERE Id` filter) — "
                    f"this stamps recency on every returned record and pollutes Recent Items. "
                    f"Bound the query to the record(s) the user is viewing."
                )


def check(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    if manifest_dir.is_file():
        files = [manifest_dir]
    else:
        files = sorted(
            p
            for p in manifest_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in {".cls", ".trigger", ".apex"}
        )

    if not files:
        return [f"No Apex source (*.cls / *.trigger) found under {manifest_dir} — nothing to check."]

    for path in files:
        check_file(path, issues)
    return issues


def main() -> int:
    args = parse_args()
    issues = check(Path(args.manifest_dir))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
