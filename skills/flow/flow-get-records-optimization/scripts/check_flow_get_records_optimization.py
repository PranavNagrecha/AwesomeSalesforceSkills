#!/usr/bin/env python3
"""Heuristic checker for Get Records audit docs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED = (
    "inventory",
    "filter",
    "limit",
    "loop",
    "soql count",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Get Records audit.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for required in REQUIRED:
        if required not in text:
            issues.append(f"{path}: missing '{required}'")

    if "in loop" not in text and "inside a loop" not in text:
        issues.append(f"{path}: loop check missing")

    if "indexed" not in text:
        issues.append(f"{path}: indexed-filter check missing")

    if "all fields" not in text and "trim" not in text:
        issues.append(f"{path}: field-trim check missing")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No Get Records audit docs found.")
        return 0

    issues: list[str] = []
    for path in targets:
        issues.extend(check_file(path))

    if not issues:
        print("Get Records audit looks complete.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
