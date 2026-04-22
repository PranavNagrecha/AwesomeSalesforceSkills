#!/usr/bin/env python3
"""Checker for LWC ShowToast Patterns skill.

Scans LWC for:
- ShowToastEvent with variant 'error' but mode not sticky/pester
- ShowToastEvent with mode 'pester' but variant not error
- Raw <a> or http:// in toast message strings (should use messageData)

Usage:
    python3 check_lwc_show_toast_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SHOW_TOAST_BLOCK = re.compile(
    r"new\s+ShowToastEvent\s*\(\s*\{[^}]*\}\s*\)", re.DOTALL
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check ShowToast anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_lwc(root: Path) -> list[str]:
    issues: list[str] = []
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return issues
    for path in lwc_dir.rglob("*.js"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in SHOW_TOAST_BLOCK.finditer(text):
            block = m.group(0)
            line_no = text[: m.start()].count("\n") + 1
            variant = re.search(r"variant\s*:\s*['\"](\w+)['\"]", block)
            mode = re.search(r"mode\s*:\s*['\"](\w+)['\"]", block)
            message = re.search(r"message\s*:\s*['\"]([^'\"]+)['\"]", block)

            v = variant.group(1) if variant else None
            md = mode.group(1) if mode else None

            if v == "error" and md not in ("sticky", "pester"):
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: error toast without sticky/pester mode — user may miss it"
                )
            if md == "pester" and v != "error":
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: pester mode only valid with variant='error'"
                )
            if message and ("<a " in message.group(1) or "http://" in message.group(1) or "https://" in message.group(1)):
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: toast message contains HTML/URL; use messageData for links"
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
        print("No ShowToast anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
