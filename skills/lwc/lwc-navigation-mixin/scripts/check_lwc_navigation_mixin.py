#!/usr/bin/env python3
"""Checker for LWC NavigationMixin skill.

Scans LWC JS for:
- window.location / window.open navigation
- NavigationMixin import without class extension
- GenerateUrl usage without await/then

Usage:
    python3 check_lwc_navigation_mixin.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


WINDOW_NAV = re.compile(r"window\.(location\.href|open)\s*[=(]")
IMPORT_MIXIN = re.compile(r"import\s*\{\s*NavigationMixin\s*\}\s*from")
EXTENDS_MIXIN = re.compile(r"extends\s+NavigationMixin\s*\(")
GENERATE_URL_NO_AWAIT = re.compile(
    r"(?<!await\s)(?<!\.\s)this\[NavigationMixin\.GenerateUrl\]\([^)]*\)\s*(?:;|[^.])"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check NavigationMixin anti-patterns.")
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

            for m in WINDOW_NAV.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: window.{m.group(1)} navigation; use NavigationMixin"
                )

            if IMPORT_MIXIN.search(text) and not EXTENDS_MIXIN.search(text):
                issues.append(
                    f"{path.relative_to(root)}: imports NavigationMixin without class extension"
                )

            for m in GENERATE_URL_NO_AWAIT.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: GenerateUrl used without await or .then"
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
        print("No NavigationMixin anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
