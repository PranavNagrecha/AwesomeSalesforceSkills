#!/usr/bin/env python3
"""Heuristic checker for FlexCard composition plan documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "context",
    "card inventory",
    "event contract",
    "actions",
    "datasource caching",
    "sign-off",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect FlexCard composition plans.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "event" not in text:
        issues.append(f"{path}: no event contract mentioned")

    if "datasource" not in text and "data source" not in text:
        issues.append(f"{path}: no datasource mentioned")

    if "form factor" not in text and "desktop" not in text:
        issues.append(f"{path}: no form-factor preview plan")

    if "hardcoded" in text and "url" in text:
        issues.append(f"{path}: references hardcoded URL — use Navigate action")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No FlexCard composition docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("FlexCard composition plan looks complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
