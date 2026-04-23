#!/usr/bin/env python3
"""Heuristic checker for flow activation checklists."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "flow",
    "diff",
    "caller audit",
    "paused interviews",
    "rollback",
    "cleanup",
    "sign-off",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect flow activation checklists.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "paused" not in text:
        issues.append(f"{path}: paused interviews not addressed")

    if "rollback" not in text:
        issues.append(f"{path}: rollback path not defined")

    if "breaking" not in text:
        issues.append(f"{path}: breaking-change classification missing")

    if "redeploy" in text and "not" not in text and "rollback" in text:
        issues.append(f"{path}: rollback via redeploy flagged — prefer activate-prior")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No flow activation docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Flow activation checklist looks complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
