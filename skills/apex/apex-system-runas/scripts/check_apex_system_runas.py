#!/usr/bin/env python3
"""Checker for Apex System.runAs skill.

Scans Apex for:
- System.runAs outside test context
- Profile-name-based User queries in tests (unstable across orgs)

Usage:
    python3 check_apex_system_runas.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


RUNAS = re.compile(r"System\.runAs\s*\(", re.IGNORECASE)
TEST_CONTEXT = re.compile(r"@IsTest|testMethod", re.IGNORECASE)
PROFILE_NAME_QUERY = re.compile(
    r"\[SELECT[^\]]*FROM\s+User[^\]]*WHERE[^\]]*Profile\.Name\s*=",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check apex-system-runas anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if RUNAS.search(text) and not TEST_CONTEXT.search(text):
            issues.append(
                f"{path.relative_to(root)}: System.runAs used outside test context — only legal in @IsTest classes"
            )

        if TEST_CONTEXT.search(text):
            for m in PROFILE_NAME_QUERY.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: test queries User by Profile.Name — unstable across orgs; create a fresh User fixture"
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
        print("No runAs anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
