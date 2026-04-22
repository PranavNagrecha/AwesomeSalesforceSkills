#!/usr/bin/env python3
"""Checker for Apex Polymorphic SOQL skill.

Scans Apex SOQL for:
- What.<field>/Who.<field>/LinkedEntity.<field> accessing type-specific fields without TYPEOF
- Filters on What.Type or Who.Type without a selective companion filter

Usage:
    python3 check_apex_polymorphic_soql.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Heuristic: polymorphic traversal to known type-specific fields
TYPE_SPECIFIC = re.compile(
    r"\b(What|Who|LinkedEntity)\.(Industry|Amount|StageName|Company|Title|Salary__c|[A-Za-z_]+__c)\b"
)
TYPE_FILTER_ALONE = re.compile(
    r"WHERE\s+(?:What|Who|LinkedEntity)\.Type\s*=\s*'[^']+'\s*(?:LIMIT|$|\))", re.IGNORECASE
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check polymorphic-SOQL anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if "TYPEOF" not in text.upper():
            for m in TYPE_SPECIFIC.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: {m.group(1)}.{m.group(2)} without TYPEOF"
                )
                break

        for m in TYPE_FILTER_ALONE.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: filter by polymorphic Type alone is non-selective"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_apex(root)
    if not issues:
        print("No polymorphic-SOQL anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
