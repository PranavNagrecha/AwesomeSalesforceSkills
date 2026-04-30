#!/usr/bin/env python3
"""Static checker for SOQL ORDER BY clauses in Apex source.

Scans `force-app/.../classes/*.cls` and `*.trigger` files for SOQL queries
with ORDER BY clauses and flags:

- ORDER BY clauses lacking an explicit NULLS FIRST/LAST keyword pair
- ORDER BY clauses without an `Id` (or other tiebreaker) at the end
- OFFSET values above 500 (cursor pagination strongly preferred)

Stdlib only. Heuristic regex.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ORDER_BY = re.compile(r"ORDER\s+BY\s+([^\]]+?)(?=\s+LIMIT\b|\s*\]|$)", re.IGNORECASE | re.DOTALL)
OFFSET_VAL = re.compile(r"OFFSET\s+(\d+)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lint SOQL ORDER BY clauses for null/tiebreaker hygiene.")
    p.add_argument("--manifest-dir", default=".", help="Project root.")
    return p.parse_args()


def source_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        out.extend((root / "force-app").rglob(ext))
    return out


def check_clause(clause: str) -> list[str]:
    issues: list[str] = []
    norm = clause.upper()
    if "NULLS FIRST" not in norm and "NULLS LAST" not in norm:
        issues.append("ORDER BY without explicit NULLS FIRST/LAST")
    last_segment = clause.strip().rstrip(",").split(",")[-1].strip().upper()
    if not last_segment.startswith("ID"):
        issues.append("ORDER BY does not end with `Id` tiebreaker")
    return issues


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return issues

    for m in ORDER_BY.finditer(text):
        for problem in check_clause(m.group(1)):
            issues.append(f"{path}: {problem} — clause `{m.group(1).strip()[:80]}`")

    for m in OFFSET_VAL.finditer(text):
        n = int(m.group(1))
        if n > 500:
            issues.append(f"{path}: OFFSET {n} — switch to cursor pagination (cap is 2000)")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not (root / "force-app").exists():
        print(f"ERROR: no force-app/ directory under {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for f in source_files(root):
        issues.extend(check_file(f))

    if not issues:
        print("[soql-null-ordering-patterns] no issues found")
        return 0
    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
