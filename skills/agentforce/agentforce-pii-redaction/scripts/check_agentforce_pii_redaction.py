#!/usr/bin/env python3
"""Heuristic checker for PII redaction registers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "classification",
    "input-side detection",
    "output-side pass",
    "audit",
    "sign-off",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect PII redaction registers.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "regulated" not in text:
        issues.append(f"{path}: regulated class not referenced")

    if "ssn" not in text and "national" not in text:
        issues.append(f"{path}: no national-id category addressed")

    if "trust layer" not in text and "einstein trust" not in text:
        issues.append(f"{path}: trust layer boundary not referenced")

    if "audit" not in text:
        issues.append(f"{path}: no audit wiring referenced")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No PII redaction docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("PII redaction register looks complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
