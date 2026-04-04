#!/usr/bin/env python3
"""Checker script for SOQL Fundamentals skill.

Scans Apex source files for common SOQL anti-patterns:
  1. SOQL queries inside for-loops (Governor limit violation)
  2. SELECT without WHERE clause on large objects (non-selective queries)
  3. Missing LIMIT on unrestricted queries

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_soql_fundamentals.py [--help]
    python3 check_soql_fundamentals.py --manifest-dir path/to/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# SOQL patterns
SOQL_INLINE = re.compile(r"\[\s*SELECT\s", re.IGNORECASE)
FOR_LOOP = re.compile(r"\bfor\s*\(", re.IGNORECASE)
SOQL_NO_WHERE = re.compile(r"\[\s*SELECT\s[^\]]+FROM\s+\w+[^\]]*\]", re.IGNORECASE | re.DOTALL)
SOQL_HAS_WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)
SOQL_HAS_LIMIT = re.compile(r"\bLIMIT\b", re.IGNORECASE)
SOQL_IN_FOR = re.compile(r"for\s*\([^)]*\)\s*\{[^}]*\[\s*SELECT\s", re.IGNORECASE | re.DOTALL)


def check_file(apex_file: Path) -> list[str]:
    """Check a single Apex file for SOQL anti-patterns."""
    issues: list[str] = []
    try:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{apex_file}: cannot read file — {exc}"]

    lines = content.splitlines()

    # Track for-loop depth to detect SOQL inside loops
    brace_depth = 0
    in_for_loop_depth: list[int] = []
    soql_in_for_found = False

    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Track for-loop start
        if FOR_LOOP.search(stripped):
            in_for_loop_depth.append(brace_depth)

        # Track brace depth
        brace_depth += stripped.count("{") - stripped.count("}")

        # Clean up completed for-loops
        in_for_loop_depth = [d for d in in_for_loop_depth if d < brace_depth]

        # Check for inline SOQL inside a for-loop
        if SOQL_INLINE.search(stripped) and in_for_loop_depth and not soql_in_for_found:
            issues.append(
                f"{apex_file.name}:{lineno}: SOQL query inside a for-loop detected. "
                "Move SOQL outside the loop and use a Map for lookups to avoid hitting "
                "the 100-query-per-transaction governor limit."
            )
            soql_in_for_found = True  # Report once per file to avoid noise

    # Check for unrestricted SELECT (no WHERE, no LIMIT) — simple line-level scan
    # Find all inline SOQL blocks (simplified: lines with [ SELECT ... ])
    for lineno, line in enumerate(lines, start=1):
        if SOQL_INLINE.search(line):
            # Look for a SOQL block starting on this line
            # Collect the full block until closing ]
            block_start = lineno
            block = []
            depth = 0
            for bline in lines[lineno - 1:]:
                block.append(bline)
                depth += bline.count("[") - bline.count("]")
                if depth <= 0:
                    break
            block_text = " ".join(block)

            has_where = SOQL_HAS_WHERE.search(block_text)
            has_limit = SOQL_HAS_LIMIT.search(block_text)

            if not has_where and not has_limit:
                issues.append(
                    f"{apex_file.name}:{block_start}: SOQL query has no WHERE clause and no LIMIT. "
                    "An unrestricted query can return up to 50,000 rows and exhaust the transaction "
                    "row budget. Add a WHERE clause or LIMIT."
                )

    return issues


def check_soql_fundamentals(manifest_dir: Path) -> list[str]:
    """Scan all Apex class files in manifest_dir for SOQL anti-patterns."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = list(manifest_dir.rglob("*.cls"))
    if not apex_files:
        # Not an error — directory may contain only metadata XML
        return issues

    for apex_file in sorted(apex_files):
        issues.extend(check_file(apex_file))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex class files for common SOQL anti-patterns: "
            "SOQL in for-loops, missing WHERE, missing LIMIT."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Apex .cls files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_soql_fundamentals(manifest_dir)

    if not issues:
        print("No SOQL anti-patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
