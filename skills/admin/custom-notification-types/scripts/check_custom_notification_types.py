#!/usr/bin/env python3
"""Checker for Custom Notification Types skill.

Scans Apex for:
- Hard-coded Notification Type IDs
- setTitle/setBody with literals over character limits
- send() calls without apparent chunking

Usage:
    python3 check_custom_notification_types.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HARDCODED_TYPE_ID = re.compile(r"setNotificationTypeId\(\s*'0ML[A-Za-z0-9]{12,15}'")
SET_TITLE_LITERAL = re.compile(r"setTitle\(\s*'([^']{65,})'")
SET_BODY_LITERAL = re.compile(r"setBody\(\s*'([^']{751,})'")
BARE_SEND = re.compile(r"\.send\(\s*new\s+Set<String>\s*\(\s*(\w+)\s*\)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Custom Notification Type anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in HARDCODED_TYPE_ID.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: hard-coded Notification Type ID; resolve by DeveloperName"
            )

        for m in SET_TITLE_LITERAL.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: setTitle literal over 64 chars ({len(m.group(1))} chars)"
            )

        for m in SET_BODY_LITERAL.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: setBody literal over 750 chars ({len(m.group(1))} chars)"
            )

        for m in BARE_SEND.finditer(text):
            var = m.group(1)
            if not re.search(rf"{var}\.size\(\)\s*<=\s*500|{var}\.subList|chunk", text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: send() without visible 500-recipient chunking"
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
        print("No Custom Notification anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
