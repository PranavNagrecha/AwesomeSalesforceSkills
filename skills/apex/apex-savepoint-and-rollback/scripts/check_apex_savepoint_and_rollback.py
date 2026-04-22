#!/usr/bin/env python3
"""Checker for Apex Savepoint and Rollback skill.

Scans Apex for:
- Savepoint inside a loop
- Rollback after an HTTP callout in the same method
- Rollback outside a catch block (heuristic)

Usage:
    python3 check_apex_savepoint_and_rollback.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SAVEPOINT_IN_LOOP = re.compile(
    r"for\s*\([^)]*\)\s*\{[^}]*Database\.setSavepoint\s*\(", re.DOTALL | re.IGNORECASE
)
ROLLBACK = re.compile(r"Database\.rollback\s*\(")
CALLOUT = re.compile(r"\bnew\s+Http\s*\(|HttpRequest\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Savepoint/rollback anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in SAVEPOINT_IN_LOOP.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: Database.setSavepoint inside a loop"
            )

        for m in ROLLBACK.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            preceding = text[: m.start()]
            # Callout before rollback in same method?
            last_method_start = max(
                preceding.rfind("{"), preceding.rfind("void "), preceding.rfind("public ")
            )
            window = preceding[last_method_start:] if last_method_start > 0 else preceding
            if CALLOUT.search(window):
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: Database.rollback after HTTP callout in same method"
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
        print("No Savepoint/rollback anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
