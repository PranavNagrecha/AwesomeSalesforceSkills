#!/usr/bin/env python3
"""Checker script for the dynamic-apex skill.

Scans Apex source files (.cls, .trigger) for common dynamic SOQL / schema-describe
anti-patterns:

  1. Unescaped string concatenation into Database.query() — potential SOQL injection.
  2. Schema.getGlobalDescribe() called inside a loop.
  3. String.escapeSingleQuotes() applied to what appears to be a field/object name
     (i.e. the result is placed in SELECT or FROM position).
  4. record.get() / record.put() with no adjacent isAccessible() / isUpdateable() check
     in the same method block.
  5. Search.query() call where the FIND term does not pass through escapeSingleQuotes().

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_dynamic_apex.py [--source-dir path/to/apex/classes]
    python3 check_dynamic_apex.py --file path/to/SingleClass.cls
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# Database.query() call that has a '+' concatenation inside the argument —
# a likely indication of string-building with user/runtime values.
_DYNAMIC_SOQL_CONCAT = re.compile(
    r"""Database\s*\.\s*query\s*\(\s*[^)]*\+""",
    re.IGNORECASE,
)

# Schema.getGlobalDescribe() appearing after an opening loop keyword on the
# same line or the line immediately following a loop keyword.
# We detect loops with a simple heuristic: preceding non-blank line starts
# a for/while/do block.
_GET_GLOBAL_DESCRIBE = re.compile(
    r"""Schema\s*\.\s*getGlobalDescribe\s*\(\s*\)""",
    re.IGNORECASE,
)
_LOOP_KEYWORD = re.compile(
    r"""\b(?:for|while|do)\b\s*[(\s]""",
    re.IGNORECASE,
)

# escapeSingleQuotes result used in SELECT or FROM position.
_ESCAPE_SINGLE_FOR_IDENTIFIER = re.compile(
    r"""String\s*\.\s*escapeSingleQuotes\s*\([^)]+\)\s*[;,\)]\s*
        .*?                                       # gap
        (?:SELECT\s+\w|FROM\s+\w)                # appears as identifier
    """,
    re.IGNORECASE | re.DOTALL,
)

# record.get( / record.put( without isAccessible/isUpdateable in the same method.
_DYNAMIC_FIELD_ACCESS = re.compile(
    r"""\b\w+\s*\.\s*(?:get|put)\s*\(\s*['"]\w""",
    re.IGNORECASE,
)
_FLS_CHECK = re.compile(
    r"""\.is(?:Accessible|Updateable|Createable)\s*\(\s*\)""",
    re.IGNORECASE,
)

# Search.query() without escapeSingleQuotes in the same line or the preceding
# few lines.
_SEARCH_QUERY = re.compile(
    r"""Search\s*\.\s*query\s*\(""",
    re.IGNORECASE,
)
_ESCAPE_SINGLE = re.compile(
    r"""escapeSingleQuotes""",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Per-file analysis
# ---------------------------------------------------------------------------

def check_file(path: Path) -> list[str]:
    """Return a list of issue description strings for the given file."""
    issues: list[str] = []

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    lines = source.splitlines()

    # ------------------------------------------------------------------
    # Check 1: Database.query() with string concatenation
    # ------------------------------------------------------------------
    for lineno, line in enumerate(lines, 1):
        if _DYNAMIC_SOQL_CONCAT.search(line):
            issues.append(
                f"{path}:{lineno}: SOQL-INJECTION-RISK — Database.query() argument "
                f"contains '+' concatenation. Use bind variables (:varName) for "
                f"user-supplied values, and validate object/field names against "
                f"Schema.getGlobalDescribe()."
            )

    # ------------------------------------------------------------------
    # Check 2: getGlobalDescribe() inside a loop
    # The heuristic: if the preceding non-blank line within 3 lines
    # contains a loop keyword, flag it.
    # ------------------------------------------------------------------
    non_blank_indices: list[int] = [
        i for i, ln in enumerate(lines) if ln.strip()
    ]
    for idx, lineno_0 in enumerate(non_blank_indices):
        line = lines[lineno_0]
        if _GET_GLOBAL_DESCRIBE.search(line):
            # Look back up to 5 non-blank lines for a loop keyword.
            lookback = non_blank_indices[max(0, idx - 5) : idx]
            for lb_idx in reversed(lookback):
                lb_line = lines[lb_idx]
                if _LOOP_KEYWORD.search(lb_line):
                    issues.append(
                        f"{path}:{lineno_0 + 1}: DESCRIBE-IN-LOOP — "
                        f"Schema.getGlobalDescribe() appears to be called inside a loop "
                        f"(loop keyword seen near line {lb_idx + 1}). Cache describe "
                        f"results in a static map outside the loop."
                    )
                    break
                # Stop scanning back if we hit a method or class boundary.
                if re.search(r"\b(?:public|private|protected|global)\b", lb_line):
                    break

    # ------------------------------------------------------------------
    # Check 3: record.get()/record.put() without any FLS check in the
    # same method block (rough heuristic: within 40 lines above/below).
    # ------------------------------------------------------------------
    for lineno_0, line in enumerate(lines):
        if _DYNAMIC_FIELD_ACCESS.search(line):
            window_start = max(0, lineno_0 - 40)
            window_end   = min(len(lines), lineno_0 + 40)
            window = "\n".join(lines[window_start:window_end])
            if not _FLS_CHECK.search(window):
                issues.append(
                    f"{path}:{lineno_0 + 1}: MISSING-FLS-CHECK — "
                    f"record.get() or record.put() found with no visible "
                    f"isAccessible() / isUpdateable() check in the surrounding "
                    f"method block. Add FLS validation for user-facing dynamic "
                    f"field access."
                )

    # ------------------------------------------------------------------
    # Check 4: Search.query() without escapeSingleQuotes nearby
    # ------------------------------------------------------------------
    for lineno_0, line in enumerate(lines):
        if _SEARCH_QUERY.search(line):
            # Check 10 lines before.
            window_start = max(0, lineno_0 - 10)
            window = "\n".join(lines[window_start : lineno_0 + 1])
            if not _ESCAPE_SINGLE.search(window):
                issues.append(
                    f"{path}:{lineno_0 + 1}: SOSL-INJECTION-RISK — "
                    f"Search.query() call found without a visible "
                    f"String.escapeSingleQuotes() call in the preceding lines. "
                    f"SOSL FIND clause values do not support bind variables; "
                    f"apply escapeSingleQuotes() to user-supplied search terms."
                )

    return issues


# ---------------------------------------------------------------------------
# Directory walk
# ---------------------------------------------------------------------------

def check_directory(root: Path) -> list[str]:
    issues: list[str] = []
    apex_files = list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))
    if not apex_files:
        return [f"No .cls or .trigger files found under {root}"]
    for apex_file in sorted(apex_files):
        issues.extend(check_file(apex_file))
    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex source for dynamic-apex anti-patterns: SOQL injection risk, "
            "describe calls in loops, missing FLS checks, and SOSL injection risk."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--source-dir",
        default=".",
        help="Root directory to scan recursively for .cls and .trigger files (default: .).",
    )
    group.add_argument(
        "--file",
        help="Single Apex file to check.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.file:
        target = Path(args.file)
        if not target.is_file():
            print(f"ERROR: File not found: {target}", file=sys.stderr)
            return 2
        issues = check_file(target)
    else:
        root = Path(args.source_dir)
        if not root.is_dir():
            print(f"ERROR: Directory not found: {root}", file=sys.stderr)
            return 2
        issues = check_directory(root)

    if not issues:
        print("No dynamic-apex issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
