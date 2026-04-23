#!/usr/bin/env python3
"""Heuristic checker for Decision review docs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = ("outcomes", "checks", "default")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect decision review docs.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing '{section}'")

    if "null-safe" not in text and "null safe" not in text:
        issues.append(f"{path}: null-safety column missing")

    if "api value" not in text:
        issues.append(f"{path}: pick-list API-value check missing")

    if "nesting" not in text and "depth" not in text:
        issues.append(f"{path}: depth/nesting check missing")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No decision review docs found.")
        return 0

    issues: list[str] = []
    for path in targets:
        issues.extend(check_file(path))

    if not issues:
        print("Decision reviews look complete.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
