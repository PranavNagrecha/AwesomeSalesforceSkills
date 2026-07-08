#!/usr/bin/env python3
"""Checker for SOQL outer-join / null-semantics footguns.

Scans Apex (`.cls`, `.trigger`, `.apex`) and standalone `.soql` files for SOQL
`WHERE` comparisons whose null semantics commonly surprise practitioners, as
documented in the SOQL and SOSL Reference:

  1. A parent field tested for null through a relationship
     (e.g. `WHERE Contact.LastName = null`). Relationship queries behave like an
     outer join, so the row is returned even when the parent does not exist —
     this over-selects when you meant "records whose lookup is empty". Filter the
     foreign-key Id field instead (e.g. `WHERE ContactId = null`).

  2. A Boolean field compared to null (e.g. `WHERE IsActive = null`). Boolean
     fields are never null, so `= null` is evaluated as `= false` and `!= null`
     as `= true`. Compare to an explicit `true` / `false`.

Stdlib only — no pip dependencies.

Usage:
    python3 check_soql_outer_join_null_semantics.py [--path DIR_OR_FILE]

Exit code 0 = no issues, 1 = issues found (or bad input path).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCANNED_SUFFIXES = {".cls", ".trigger", ".apex", ".soql"}

# Inline Apex SOQL: [SELECT ... ]  (subqueries use parentheses, not brackets,
# so a no-inner-bracket body is a safe match for typical queries).
INLINE_SOQL = re.compile(r"\[\s*(SELECT\b[^\[\]]*)\]", re.IGNORECASE | re.DOTALL)
# String-literal SOQL passed to Database.query('SELECT ...') and friends.
STRING_SOQL = re.compile(r"'(\s*SELECT\b(?:[^'\\]|\\.)*)'", re.IGNORECASE | re.DOTALL)
# A `<operand> (=|!=|<>) null` comparison. Operand may be dotted (relationship).
NULL_CMP = re.compile(
    r"([A-Za-z_][A-Za-z0-9_.]*)\s*(=|!=|<>)\s*null\b", re.IGNORECASE
)

# Conservative Boolean-field name heuristic (kept tight to avoid false alarms —
# e.g. it must NOT flag foreign keys like `UserId`).
BOOL_PREFIX = re.compile(r"^(Is|Has|Can|Allow|Enable|Show|Are)[A-Z0-9]")
KNOWN_BOOL_FIELDS = {
    "IsActive",
    "IsClosed",
    "IsWon",
    "IsDeleted",
    "IsConverted",
    "IsLocked",
    "IsEscalated",
    "IsPrivate",
    "Active__c",
    "Enabled__c",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Flag SOQL relationship/Boolean null-checks with surprising "
            "outer-join semantics."
        ),
    )
    parser.add_argument(
        "--path",
        default=".",
        help="File or directory to scan (default: current directory).",
    )
    return parser.parse_args()


def _looks_boolean(field: str) -> bool:
    return field in KNOWN_BOOL_FIELDS or bool(BOOL_PREFIX.match(field))


def _iter_soql_spans(text: str, is_soql_file: bool):
    """Yield (abs_start_offset, query_text) spans of SOQL within the file text."""
    if is_soql_file:
        yield 0, text
        return
    for match in INLINE_SOQL.finditer(text):
        yield match.start(1), match.group(1)
    for match in STRING_SOQL.finditer(text):
        yield match.start(1), match.group(1)


def _line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_text(rel_name: str, text: str, is_soql_file: bool) -> list[str]:
    issues: list[str] = []
    for span_start, query in _iter_soql_spans(text, is_soql_file):
        for cmp_match in NULL_CMP.finditer(query):
            operand, op = cmp_match.group(1), cmp_match.group(2)
            line = _line_of(text, span_start + cmp_match.start())
            loc = f"{rel_name}:{line}"
            if "." in operand:
                if op == "=":
                    issues.append(
                        f"{loc}: `{operand} {op} null` tests a parent field through a "
                        f"relationship (outer join) — the row is returned even when the "
                        f"parent does not exist, so this over-selects. To select rows "
                        f"whose lookup is empty, filter the foreign-key Id field instead "
                        f"(e.g. `AccountId = null`)."
                    )
                else:
                    issues.append(
                        f"{loc}: `{operand} {op} null` relies on relationship traversal "
                        f"to express 'has a parent value'. Prefer filtering the "
                        f"foreign-key Id (e.g. `AccountId != null`) so the intent doesn't "
                        f"depend on outer-join semantics."
                    )
            elif _looks_boolean(operand):
                issues.append(
                    f"{loc}: `{operand} {op} null` compares a Boolean field to null — "
                    f"Boolean fields are never null, so `= null` is evaluated as "
                    f"`= false` and `!= null` as `= true`. Compare to an explicit "
                    f"`true` / `false` instead."
                )
    return issues


def _iter_files(root: Path):
    if root.is_file():
        if root.suffix.lower() in SCANNED_SUFFIXES:
            yield root
        return
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in SCANNED_SUFFIXES:
            yield path


def check(root: Path) -> list[str]:
    if not root.exists():
        return [f"Path not found: {root}"]
    issues: list[str] = []
    scanned = 0
    for path in _iter_files(root):
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:  # pragma: no cover - defensive
            issues.append(f"{path}: could not read ({exc})")
            continue
        rel = str(path)
        issues.extend(check_text(rel, text, path.suffix.lower() == ".soql"))
    if scanned == 0:
        return [
            f"No {'/'.join(sorted(SCANNED_SUFFIXES))} files found under {root} "
            f"— nothing to check."
        ]
    return issues


def main() -> int:
    args = parse_args()
    issues = check(Path(args.path))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
