#!/usr/bin/env python3
"""Checker script for the Apex Dynamic SOQL Binding Safety skill.

Scans Apex (.cls) sources for unsafe dynamic-SOQL patterns:

  P0 — String concatenation INSIDE a Database.query(...) call.
       Example:  Database.query('SELECT Id FROM Account WHERE Name = \\'' + name + '\\'')
       This is the canonical SOQL-injection vector.

  P1 — Database.query(varName) where the referenced query string contains
       no ':name' colon-bind tokens AND the file does not use queryWithBinds.
       Indicates a query built without binds.

  P1 — String.escapeSingleQuotes used immediately upstream of a Database.query
       string concatenation. Indicates a "false sense of security" pattern —
       escaping is not a substitute for binding.

Stdlib only. Exits 1 if any P0 or P1 issue is found.

Usage:
    python3 check_apex_dynamic_soql_binding_safety.py [--manifest-dir DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

# P0: '+' concatenation inside Database.query(...) — argument starts with a
# string literal (allowing \' escapes) and concatenates a token before the
# closing paren.
P0_CONCAT_INSIDE_QUERY = re.compile(
    r"Database\.query\s*\(\s*'(?:\\.|[^'\\])*'\s*\+",
    re.IGNORECASE,
)
# Also catch the reverse: Database.query(varName + 'literal')
P0_CONCAT_INSIDE_QUERY_REV = re.compile(
    r"Database\.query\s*\(\s*[A-Za-z_][A-Za-z0-9_]*\s*\+",
    re.IGNORECASE,
)

# P1: Database.query(soqlVar) where soqlVar's assignment has no :bind token
P1_QUERY_VAR = re.compile(
    r"Database\.query\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
    re.IGNORECASE,
)
P1_BIND_TOKEN = re.compile(r":[A-Za-z_][A-Za-z0-9_]*")
P1_USES_QUERY_WITH_BINDS = re.compile(r"Database\.queryWithBinds\s*\(", re.IGNORECASE)

# P1: escapeSingleQuotes immediately followed by concatenation into Database.query
P1_ESCAPE_THEN_QUERY = re.compile(
    r"String\.escapeSingleQuotes[^;]{0,200}?Database\.query",
    re.IGNORECASE | re.DOTALL,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan Apex .cls files for unsafe dynamic SOQL patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Apex classes (default: current directory).",
    )
    return parser.parse_args()


def find_apex_files(root: Path) -> List[Path]:
    if not root.exists():
        return []
    return sorted(root.rglob("*.cls"))


def assignment_has_bind(source: str, var_name: str) -> bool:
    """Return True if any assignment to `var_name` in `source` contains a :bind token."""
    pattern = re.compile(
        rf"\b(?:String\s+)?{re.escape(var_name)}\s*(?:=|\+=)\s*([^;]+);",
        re.IGNORECASE,
    )
    matches = pattern.findall(source)
    if not matches:
        # No visible assignment — assume worst case (P1 will fire from caller logic).
        return False
    return any(P1_BIND_TOKEN.search(rhs) for rhs in matches)


def scan_file(path: Path) -> List[Tuple[str, str, int, str]]:
    """Return list of (severity, rule, line_number, message) tuples."""
    issues: List[Tuple[str, str, int, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [("P1", "io_error", 0, f"Cannot read {path}: {exc}")]

    lines = text.splitlines()
    uses_qwb = bool(P1_USES_QUERY_WITH_BINDS.search(text))

    for idx, line in enumerate(lines, start=1):
        # Skip single-line comments
        stripped = line.strip()
        if stripped.startswith("//"):
            continue

        if P0_CONCAT_INSIDE_QUERY.search(line) or P0_CONCAT_INSIDE_QUERY_REV.search(line):
            issues.append(
                (
                    "P0",
                    "concat_inside_query",
                    idx,
                    "String concatenation inside Database.query(...) — SOQL-injection vector. "
                    "Use Database.queryWithBinds with a bind map.",
                )
            )

        m = P1_QUERY_VAR.search(line)
        if m:
            var_name = m.group(1)
            # If file does not use queryWithBinds, AND the assignment has no bind, flag it.
            if not uses_qwb and not assignment_has_bind(text, var_name):
                issues.append(
                    (
                        "P1",
                        "query_var_no_bind",
                        idx,
                        f"Database.query({var_name}) — referenced query has no ':bind' "
                        f"tokens and file does not use Database.queryWithBinds. "
                        f"Confirm the query is fully static or migrate to queryWithBinds.",
                    )
                )

    # Multi-line: escapeSingleQuotes then Database.query within ~200 chars
    for match in P1_ESCAPE_THEN_QUERY.finditer(text):
        # Approximate line number from match offset
        line_no = text.count("\n", 0, match.start()) + 1
        issues.append(
            (
                "P1",
                "escape_then_query",
                line_no,
                "String.escapeSingleQuotes used immediately before Database.query — "
                "escaping is NOT a substitute for binding. Use Database.queryWithBinds.",
            )
        )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists():
        print(f"ERROR: manifest directory not found: {root}", file=sys.stderr)
        return 1

    files = find_apex_files(root)
    if not files:
        print(f"No .cls files found under {root}.")
        return 0

    total_p0 = 0
    total_p1 = 0
    for f in files:
        for severity, rule, line_no, msg in scan_file(f):
            if severity == "P0":
                total_p0 += 1
            else:
                total_p1 += 1
            print(f"{severity} [{rule}] {f}:{line_no}: {msg}", file=sys.stderr)

    print(
        f"\nScanned {len(files)} file(s). P0 issues: {total_p0}. P1 issues: {total_p1}."
    )
    if total_p0 > 0 or total_p1 > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
