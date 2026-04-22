#!/usr/bin/env python3
"""Checker script for Custom Label Management skill.

Scans metadata for hard-coded user-facing strings that should be Custom Labels.

Usage:
    python3 check_custom_label_management.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ADDERROR_LITERAL = re.compile(r"\.addError\(\s*'[^']{3,}'")
LWC_PROSE = re.compile(r">\s*[A-Z][a-z]+(?:\s+[A-Za-z]+){2,}\s*<")
LABEL_IN_MAP = re.compile(r"Map<String\s*,\s*String>\s+labels\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check for hard-coded strings that should be Custom Labels.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def iter_files(root: Path, suffixes: tuple[str, ...]):
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in suffixes:
            yield path


def check_addError_literals(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_files(root, (".cls", ".trigger")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for match in ADDERROR_LITERAL.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: addError with hard-coded string; use System.Label"
            )
    return issues


def check_lwc_prose(root: Path) -> list[str]:
    issues: list[str] = []
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return issues
    for comp in lwc_dir.iterdir():
        if not comp.is_dir():
            continue
        for path in comp.glob("*.html"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if LWC_PROSE.search(text):
                issues.append(
                    f"{path.relative_to(root)}: prose text in template; consider @salesforce/label import"
                )
    return issues


def check_parallel_label_map(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_files(root, (".cls",)):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if LABEL_IN_MAP.search(text):
            issues.append(
                f"{path.relative_to(root)}: parallel Map<String,String> labels; use System.Label instead"
            )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_addError_literals(root))
    issues.extend(check_lwc_prose(root))
    issues.extend(check_parallel_label_map(root))

    if not issues:
        print("No Custom Label anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
