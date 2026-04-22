#!/usr/bin/env python3
"""Checker for Apex Custom Permissions Check skill.

Scans Apex for:
- Profile-name-based authorization
- Hardcoded user-Id bypass
- FeatureManagement.checkPermission inside loops

Usage:
    python3 check_apex_custom_permissions_check.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROFILE_NAME = re.compile(r"Profile\.Name\s*==")
HARDCODED_USERID = re.compile(r"UserInfo\.getUserId\s*\(\s*\)\s*==\s*'005[A-Za-z0-9]{12,15}'")
CHECK_IN_LOOP = re.compile(
    r"for\s*\([^)]*\)\s*\{[^}]*FeatureManagement\.checkPermission", re.DOTALL
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Custom Permission anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in PROFILE_NAME.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: Profile.Name equality check; use Custom Permission"
            )

        for m in HARDCODED_USERID.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: hardcoded user Id bypass; use Custom Permission"
            )

        for m in CHECK_IN_LOOP.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: FeatureManagement.checkPermission inside loop; hoist above"
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
        print("No Custom Permission anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
