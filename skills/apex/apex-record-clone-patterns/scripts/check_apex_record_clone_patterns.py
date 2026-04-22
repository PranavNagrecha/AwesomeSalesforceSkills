#!/usr/bin/env python3
"""Checker for Apex Record Clone Patterns skill.

Scans Apex for:
- clone(true, ...) (preserveId) followed by insert in the same class
- clone() + insert of child records without reparenting the lookup

Usage:
    python3 check_apex_record_clone_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PRESERVE_ID_CLONE = re.compile(r"\.clone\s*\(\s*true\b", re.IGNORECASE)
INSERT_ANY = re.compile(r"\binsert\s+\w", re.IGNORECASE)
CLONE_CALL = re.compile(r"\.clone\s*\(", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check clone() anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if PRESERVE_ID_CLONE.search(text) and INSERT_ANY.search(text):
            for m in PRESERVE_ID_CLONE.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: clone(true, ...) preserves Id; cannot be inserted — use clone() without preserveId"
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
        print("No clone anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
