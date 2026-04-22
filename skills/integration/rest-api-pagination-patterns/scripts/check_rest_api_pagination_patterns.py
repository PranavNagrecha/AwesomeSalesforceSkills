#!/usr/bin/env python3
"""Checker for REST API Pagination Patterns skill.

Scans Apex for:
- Pagination while-loops without an iteration safety cap
- HTTP callouts inside triggers
- Absence of rate-limit header handling near callout loops

Usage:
    python3 check_rest_api_pagination_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


HTTP_SEND_IN_WHILE = re.compile(
    r"while\s*\([^)]*\)\s*\{[^}]*http\.send", re.DOTALL | re.IGNORECASE
)
PAGINATION_LOOP = re.compile(r"while\s*\([^)]*\)\s*\{", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check REST pagination anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    # Triggers doing HTTP pagination
    for path in root.rglob("*.trigger"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if HTTP_SEND_IN_WHILE.search(text):
            issues.append(
                f"{path.relative_to(root)}: HTTP pagination inside trigger; move to Queueable"
            )

    # Classes: paginating loops without safety cap
    for path in root.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in HTTP_SEND_IN_WHILE.finditer(text):
            # Inspect 800 chars around the loop for counter/max pattern
            window = text[max(0, m.start() - 200) : m.end() + 400]
            if not re.search(r"(max_?pages|safety|iter|counter|\+\+\s*<|\d+\s*pages)", window, re.IGNORECASE):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: pagination loop without safety iteration cap"
                )

        # Callouts without rate-limit header references in class
        if "http.send" in text.lower() and "X-RateLimit" not in text and "Retry-After" not in text:
            # only warn once per file if obvious pagination loop present
            if HTTP_SEND_IN_WHILE.search(text):
                issues.append(
                    f"{path.relative_to(root)}: pagination class does not inspect rate-limit headers"
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
        print("No REST pagination anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
