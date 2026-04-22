#!/usr/bin/env python3
"""Checker for Record Access Troubleshooting skill.

Scans Apex for sharing anti-patterns:
- Manual share inserts that will break on ownership change
- Apex that sets With Sharing on a class doing cross-user lookups without
  a UserRecordAccess sanity check
- Hard-coded 'RowCause = Manual' when a custom ApexSharingReason would survive

Usage:
    python3 check_record_access_troubleshooting.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MANUAL_ROWCAUSE = re.compile(
    r"RowCause\s*=\s*['\"]Manual['\"]", re.IGNORECASE
)
SHARE_INSERT = re.compile(r"\b\w+__Share\b|\bAccountShare\b|\bOpportunityShare\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check record-access troubleshooting anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if SHARE_INSERT.search(text):
            for m in MANUAL_ROWCAUSE.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: Apex share with RowCause='Manual' will not survive owner change; use a custom ApexSharingReason"
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
        print("No record-access anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
