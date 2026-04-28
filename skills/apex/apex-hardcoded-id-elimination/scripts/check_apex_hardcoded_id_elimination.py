#!/usr/bin/env python3
"""Checker for hardcoded Salesforce record IDs in Apex source.

Scans `.cls` files for three classes of issues:

  P0 -- A Salesforce-ID literal (15-char or 18-char) appearing in a
        non-test Apex class. Test classes (file ends in `_Test.cls` or
        contains `@isTest` near the class declaration) are exempted.

  P1 -- A `[SELECT Id FROM Profile WHERE Name = ...]` or similar
        per-call lookup that does not appear inside a static cache
        initializer (heuristic: not preceded within 30 lines by a
        `static` Map declaration).

  P2 -- A variable whose name ends with `Id` or `IDs` declared with the
        `String` type, which opens the 15/18-char comparison bug.

Exit code:
  0  -- no P0 / P1 findings
  1  -- one or more P0 / P1 findings (P2 reported but does not fail)

Stdlib only. No pip dependencies.

Usage:
    python3 check_apex_hardcoded_id_elimination.py --src path/to/classes
    python3 check_apex_hardcoded_id_elimination.py            # uses .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

# 15-char or 18-char Salesforce ID, surrounded by single or double quotes.
# Conservative: require the literal to be quoted to avoid hitting URL fragments
# or random alphanumerics in comments.
ID_LITERAL = re.compile(r"""(['"])([a-zA-Z0-9]{15}|[a-zA-Z0-9]{18})\1""")

# `[SELECT Id FROM Profile WHERE Name = ...]` and the Group/UserRole variants.
NAME_LOOKUP_SOQL = re.compile(
    r"\[\s*SELECT\s+Id\s+FROM\s+(Profile|Group|UserRole|Queue)\s+WHERE\s+(Name|DeveloperName)\s*=",
    re.IGNORECASE,
)

# `String someId = ...` or `String someIDs = ...`.
STRING_ID_VAR = re.compile(
    r"\bString\s+(\w+(?:Id|IDs|Ids))\s*[=;,)]",
)

# Heuristic: detect that a SOQL line lives inside (or directly under) a
# static Map cache initializer.
STATIC_MAP_DECL = re.compile(
    r"\bstatic\b[^;]*\bMap\s*<\s*String\s*,\s*Id\s*>",
    re.IGNORECASE,
)

CLASS_DECL = re.compile(r"\bclass\s+(\w+)", re.IGNORECASE)


def is_test_file(path: Path, contents: str) -> bool:
    """Heuristic: file is a test class if name ends with _Test.cls or
    `@isTest` annotation appears within 5 lines of a `class` declaration."""
    if path.name.lower().endswith("_test.cls"):
        return True
    lines = contents.splitlines()
    for idx, line in enumerate(lines):
        if CLASS_DECL.search(line):
            window_start = max(0, idx - 5)
            window = "\n".join(lines[window_start : idx + 1])
            if re.search(r"@\s*istest\b", window, re.IGNORECASE):
                return True
            break
    return False


def strip_comments(src: str) -> str:
    """Drop `//` line comments and `/* ... */` block comments so we don't
    flag IDs that appear only in commented-out examples."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.DOTALL)
    src = re.sub(r"//[^\n]*", "", src)
    return src


def scan_file(path: Path) -> Tuple[List[str], List[str], List[str]]:
    """Return (p0_issues, p1_issues, p2_issues) for one .cls file."""
    p0: List[str] = []
    p1: List[str] = []
    p2: List[str] = []

    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ([f"{path}: cannot read file ({exc})"], [], [])

    is_test = is_test_file(path, raw)
    code = strip_comments(raw)
    lines = code.splitlines()

    for line_no, line in enumerate(lines, start=1):
        # P0: Salesforce ID literal in non-test code.
        if not is_test:
            for match in ID_LITERAL.finditer(line):
                literal = match.group(2)
                p0.append(
                    f"{path}:{line_no}: P0 hardcoded Salesforce ID literal "
                    f"'{literal}' (use Schema describe / SOQL by DeveloperName / Custom Metadata)"
                )

        # P1: Name-based ID SOQL outside a static cache.
        if NAME_LOOKUP_SOQL.search(line):
            window_start = max(0, line_no - 30)
            window = "\n".join(lines[window_start:line_no])
            if not STATIC_MAP_DECL.search(window):
                p1.append(
                    f"{path}:{line_no}: P1 name-based ID SOQL not in a static "
                    f"Map<String, Id> cache (wrap in a cached helper)"
                )

        # P2: String-typed variable holding an ID.
        for match in STRING_ID_VAR.finditer(line):
            name = match.group(1)
            p2.append(
                f"{path}:{line_no}: P2 variable '{name}' declared String "
                f"(should be Id to avoid 15/18-char comparison failures)"
            )

    return (p0, p1, p2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan Apex .cls files for hardcoded Salesforce IDs and related anti-patterns.",
    )
    parser.add_argument(
        "--src",
        default=".",
        help="Root directory to scan recursively for .cls files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.src)

    if not root.exists():
        print(f"ERROR: source directory not found: {root}", file=sys.stderr)
        return 2

    cls_files = sorted(root.rglob("*.cls"))
    if not cls_files:
        print(f"No .cls files found under {root}.")
        return 0

    all_p0: List[str] = []
    all_p1: List[str] = []
    all_p2: List[str] = []

    for path in cls_files:
        p0, p1, p2 = scan_file(path)
        all_p0.extend(p0)
        all_p1.extend(p1)
        all_p2.extend(p2)

    if all_p0:
        print("=== P0 findings (hardcoded Salesforce IDs) ===")
        for issue in all_p0:
            print(issue)
    if all_p1:
        print("=== P1 findings (uncached name-based ID SOQL) ===")
        for issue in all_p1:
            print(issue)
    if all_p2:
        print("=== P2 findings (String-typed ID variables) ===")
        for issue in all_p2:
            print(issue)

    if not (all_p0 or all_p1 or all_p2):
        print(f"OK: scanned {len(cls_files)} Apex class(es); no findings.")
        return 0

    summary = (
        f"Summary: {len(all_p0)} P0, {len(all_p1)} P1, {len(all_p2)} P2 "
        f"across {len(cls_files)} file(s)."
    )
    print(summary, file=sys.stderr)

    if all_p0 or all_p1:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
