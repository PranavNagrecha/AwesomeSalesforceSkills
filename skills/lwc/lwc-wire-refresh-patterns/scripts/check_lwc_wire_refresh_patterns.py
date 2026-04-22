#!/usr/bin/env python3
"""Checker for LWC Wire Refresh Patterns skill.

Scans LWC JS for:
- refreshApex on .data instead of the raw wired value
- Import of deprecated getRecordNotifyChange
- refreshApex without return/await

Usage:
    python3 check_lwc_wire_refresh_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REFRESH_DATA = re.compile(r"refreshApex\(\s*[\w.]+\.data\b")
DEPRECATED_NOTIFY = re.compile(r"getRecordNotifyChange")
REFRESH_FIRE_FORGET = re.compile(
    r"^\s*refreshApex\(", re.MULTILINE
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check wire-refresh anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_lwc(root: Path) -> list[str]:
    issues: list[str] = []
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return issues
    for comp in lwc_dir.iterdir():
        if not comp.is_dir():
            continue
        for path in comp.glob("*.js"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for m in REFRESH_DATA.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: refreshApex on .data; pass raw wired value"
                )
            for m in DEPRECATED_NOTIFY.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: getRecordNotifyChange is deprecated; use RefreshEvent or notifyRecordUpdateAvailable"
                )
            for m in REFRESH_FIRE_FORGET.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: refreshApex without return/await (fire-and-forget)"
                )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_lwc(root)
    if not issues:
        print("No wire-refresh anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
