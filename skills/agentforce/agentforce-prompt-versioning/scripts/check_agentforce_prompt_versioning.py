#!/usr/bin/env python3
"""Heuristic checker for prompt change entries."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "prompt",
    "motivation",
    "rollout plan",
    "metrics to watch",
    "rollback plan",
    "sign-off",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect prompt change entries.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "version" not in text:
        issues.append(f"{path}: no version declared")

    if "rollback" not in text:
        issues.append(f"{path}: no rollback plan")

    if "metric" not in text:
        issues.append(f"{path}: no metrics watched during rollout")

    if "goldens" not in text and "golden" not in text:
        issues.append(f"{path}: no golden-set regeneration note")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No prompt change entries found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Prompt change entries look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
