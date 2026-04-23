#!/usr/bin/env python3
"""Heuristic checker for OmniScript session design documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "store",
    "state schema",
    "save cadence",
    "resume url",
    "concurrency",
    "retention",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect OmniScript session design docs.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "expiry" not in text and "expires" not in text:
        issues.append(f"{path}: no expiry policy")

    if "version" not in text:
        issues.append(f"{path}: no version field for concurrency")

    if "token" not in text and "jwt" not in text:
        issues.append(f"{path}: resume URL token not specified")

    if "encrypt" not in text and "tokeniz" not in text and "pii" in text:
        issues.append(f"{path}: PII referenced but no encryption / tokenization plan")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No design docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Session design docs look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
