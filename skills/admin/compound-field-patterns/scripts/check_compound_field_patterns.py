#!/usr/bin/env python3
"""Checker for Compound Field Patterns skill.

Scans Apex for:
- WHERE clauses filtering on compound Address fields
- DML assignment of compound fields
- Assignment of Contact.Name / Lead.Name / User.Name (read-only compounds)

Usage:
    python3 check_compound_field_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ADDR_SUFFIXES = r"(?:Billing|Shipping|Mailing|Other)Address"
WHERE_COMPOUND = re.compile(rf"\bWHERE\b[^;]*?\b{ADDR_SUFFIXES}\s*=", re.IGNORECASE)
ASSIGN_COMPOUND = re.compile(rf"\.{ADDR_SUFFIXES}\s*=", re.IGNORECASE)
ASSIGN_READONLY_NAME = re.compile(r"\b(?:Contact|Lead|User)\w*\.Name\s*=")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check compound-field anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of metadata.")
    return parser.parse_args()


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in list(root.rglob("*.cls")) + list(root.rglob("*.trigger")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for m in WHERE_COMPOUND.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: WHERE filter on compound Address; filter by components"
            )

        for m in ASSIGN_COMPOUND.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: assignment to compound Address; assign components instead"
            )

        for m in ASSIGN_READONLY_NAME.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: assignment to compound Name on standard object; assign FirstName/LastName"
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
        print("No compound-field anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
