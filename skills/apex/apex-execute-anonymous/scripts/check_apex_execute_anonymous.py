#!/usr/bin/env python3
"""Checker for Apex Execute Anonymous skill.

Scans .apex scripts for:
- SOQL without LIMIT followed by DML
- DML without a savepoint or dry-run toggle

Usage:
    python3 check_apex_execute_anonymous.py [--manifest-dir path/to/project]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SOQL = re.compile(r"\[SELECT[^\]]*\]", re.IGNORECASE | re.DOTALL)
LIMIT_CLAUSE = re.compile(r"\bLIMIT\s+\d", re.IGNORECASE)
DML = re.compile(r"\b(?:insert|update|delete|upsert)\s+\w", re.IGNORECASE)
SAVEPOINT = re.compile(r"Database\.setSavepoint\s*\(", re.IGNORECASE)
APPLY_TOGGLE = re.compile(r"\bBoolean\s+APPLY\s*=", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check anonymous-Apex anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan.")
    return parser.parse_args()


def check_scripts(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.apex"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        has_dml = bool(DML.search(text))

        # SOQL without LIMIT when DML is present
        for m in SOQL.finditer(text):
            query = m.group(0)
            if has_dml and not LIMIT_CLAUSE.search(query):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: SOQL without LIMIT in DML-mutating script; bound the record set"
                )

        if has_dml and not SAVEPOINT.search(text) and not APPLY_TOGGLE.search(text):
            issues.append(
                f"{path.relative_to(root)}: anonymous script with DML has no savepoint or dry-run toggle"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_scripts(root)
    if not issues:
        print("No anonymous-Apex anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
