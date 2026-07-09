#!/usr/bin/env python3
"""Checker for the SOQL String Escaping and Reserved Characters skill.

Validates backslash escape sequences inside SOQL single-quoted string literals
against the fixed rule set in the SOQL and SOSL Reference:

  - The escape character is the backslash (\\).
  - Valid sequences: \\n \\r \\t \\b \\f (case-insensitive), \\" \\' \\\\,
    \\uXXXX (four hex digits), and the LIKE-only \\_ and \\%.
  - Any backslash used in any other context is a hard query error.
  - \\_ and \\% are valid ONLY inside a LIKE expression.

It reports:
  P0  invalid-escape       backslash followed by a char with no defined sequence
  P0  bad-unicode          \\u not followed by exactly four hex digits
  P1  like-escape-outside  \\_ or \\% used where the preceding operator is not LIKE

Scope note: this scans *raw SOQL text* — .soql files or a --query string, where
the SOQL escape table applies directly. Do NOT point it at Apex .cls sources: a
dynamic query built as an Apex String has a second (Apex) escaping layer, so its
raw source uses different escaping and would produce false positives. For unsafe
dynamic-SOQL construction in Apex, use the apex-dynamic-soql-binding-safety
skill's checker instead.

Stdlib only. Exits 1 if any issue is found.

Usage:
    python3 check_soql_string_escaping_and_reserved_characters.py --query "SELECT Id FROM Account WHERE Name = 'Bob\\'s BBQ'"
    python3 check_soql_string_escaping_and_reserved_characters.py --manifest-dir path/to/soql
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

# Letter escapes (case-insensitive) plus the quote/backslash escapes.
_ALWAYS_VALID = set("nNrRtTbBfF") | set("\"'\\")
_HEX_DIGITS = set("0123456789abcdefABCDEF")
_LIKE_ONLY = set("_%")

Issue = Tuple[int, int, str, str, str]  # (line, col, severity, code, message)


def _line_col(text: str, index: int) -> Tuple[int, int]:
    """1-based (line, column) for an absolute character index."""
    line = text.count("\n", 0, index) + 1
    last_nl = text.rfind("\n", 0, index)
    col = index - last_nl  # if no newline, last_nl == -1 -> col == index + 1
    return line, col


def _preceding_word(text: str, quote_index: int) -> str:
    """Return the alphabetic word immediately before the opening quote (upper-cased)."""
    i = quote_index - 1
    while i >= 0 and text[i].isspace():
        i -= 1
    end = i + 1
    while i >= 0 and text[i].isalpha():
        i -= 1
    return text[i + 1:end].upper()


def scan_soql(text: str) -> List[Issue]:
    """Scan one SOQL string for escape-sequence issues."""
    issues: List[Issue] = []
    n = len(text)
    i = 0
    in_literal = False
    like_context = False

    while i < n:
        ch = text[i]

        if not in_literal:
            if ch == "'":
                in_literal = True
                like_context = _preceding_word(text, i) == "LIKE"
            i += 1
            continue

        # Inside a single-quoted literal.
        if ch == "\\":
            if i + 1 >= n:
                line, col = _line_col(text, i)
                issues.append((line, col, "P0", "invalid-escape",
                               "Dangling backslash at end of literal — not a valid SOQL escape."))
                i += 1
                continue

            nxt = text[i + 1]

            if nxt in _ALWAYS_VALID:
                i += 2
                continue

            if nxt in ("u", "U"):
                hexpart = text[i + 2:i + 6]
                if len(hexpart) == 4 and all(c in _HEX_DIGITS for c in hexpart):
                    i += 6
                else:
                    line, col = _line_col(text, i)
                    issues.append((line, col, "P0", "bad-unicode",
                                   r"\u must be followed by exactly four hex digits (\uXXXX)."))
                    i += 2
                continue

            if nxt in _LIKE_ONLY:
                if not like_context:
                    line, col = _line_col(text, i)
                    issues.append((line, col, "P1", "like-escape-outside",
                                   f"\\{nxt} is a LIKE-only escape; used outside a LIKE expression "
                                   f"it is a query error. In a non-LIKE filter, '{nxt}' needs no escape."))
                i += 2
                continue

            # Any other backslash context is a hard error.
            line, col = _line_col(text, i)
            issues.append((line, col, "P0", "invalid-escape",
                           f"\\{nxt} is not a defined SOQL escape sequence — the query will error. "
                           f"Use \\\\ for a literal backslash."))
            i += 2
            continue

        if ch == "'":
            in_literal = False
            like_context = False

        i += 1

    if in_literal:
        # Unterminated literal is worth surfacing too.
        line, col = _line_col(text, n - 1 if n else 0)
        issues.append((line, col, "P0", "unterminated-literal",
                       "Unterminated string literal — an unescaped single quote must be \\'."))

    return issues


def find_soql_files(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.soql"))


def report(source: str, issues: List[Issue]) -> Tuple[int, int]:
    p0 = p1 = 0
    for line, col, severity, code, msg in issues:
        if severity == "P0":
            p0 += 1
        else:
            p1 += 1
        print(f"{severity} [{code}] {source}:{line}:{col}: {msg}", file=sys.stderr)
    return p0, p1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate SOQL string-literal escape sequences and LIKE-only escapes.",
    )
    parser.add_argument(
        "--query",
        help="A single SOQL string to validate.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for *.soql files (default: current directory). "
             "Ignored when --query is given.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    total_p0 = total_p1 = 0
    scanned = 0

    if args.query is not None:
        scanned = 1
        p0, p1 = report("<--query>", scan_soql(args.query))
        total_p0 += p0
        total_p1 += p1
    else:
        root = Path(args.manifest_dir)
        if not root.exists():
            print(f"ERROR: directory not found: {root}", file=sys.stderr)
            return 1
        files = find_soql_files(root)
        if not files:
            print(f"No .soql files found under {root}. "
                  f"(Use --query to validate a SOQL string directly.)")
            return 0
        for f in files:
            scanned += 1
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                print(f"P1 [io-error] {f}:0:0: cannot read file: {exc}", file=sys.stderr)
                total_p1 += 1
                continue
            p0, p1 = report(str(f), scan_soql(text))
            total_p0 += p0
            total_p1 += p1

    print(f"\nScanned {scanned} SOQL source(s). P0 issues: {total_p0}. P1 issues: {total_p1}.")
    if not total_p0 and not total_p1:
        print("No escaping issues found.")
    return 1 if (total_p0 or total_p1) else 0


if __name__ == "__main__":
    sys.exit(main())
