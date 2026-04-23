#!/usr/bin/env python3
"""Heuristic checker for Calculation Procedure / Matrix design documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "matrix",
    "inputs",
    "outputs",
    "lookup strategy",
    "fallback row",
    "review checklist",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect calculation matrix docs.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "version" not in text:
        issues.append(f"{path}: no matrix version declared")

    if "effective" not in text:
        issues.append(f"{path}: no effective-date window documented")

    if "overlap" not in text:
        issues.append(f"{path}: overlap check not mentioned")

    if "fallback" not in text and "wildcard" not in text:
        issues.append(f"{path}: no fallback / wildcard row mentioned")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No calculation matrix docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Calculation matrix design docs look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
