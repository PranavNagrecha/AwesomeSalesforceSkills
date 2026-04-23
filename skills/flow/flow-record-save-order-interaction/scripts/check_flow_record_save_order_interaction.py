#!/usr/bin/env python3
"""Heuristic checker for save-order documentation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED = (
    "system validation",
    "before-save flow",
    "before trigger",
    "duplicate rule",
    "validation rule",
    "after trigger",
    "after-save flow",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect save-order maps.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for required in REQUIRED:
        if required not in text:
            issues.append(f"{path}: missing '{required}' row")

    if "recursion" not in text:
        issues.append(f"{path}: recursion chain not documented")

    if "workflow" in text and "flow" in text and "duplicate field ownership" not in text:
        issues.append(
            f"{path}: workflow + flow mentioned — duplicate-field-ownership check missing"
        )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No save-order docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Save-order docs look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
