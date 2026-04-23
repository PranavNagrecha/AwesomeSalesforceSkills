#!/usr/bin/env python3
"""Heuristic checker for Agentforce test plan documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "coverage matrix",
    "golden prompt",
    "adversarial",
    "metrics dashboard",
    "sign-off",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect Agentforce test plans.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "jailbreak" not in text:
        issues.append(f"{path}: no jailbreak adversarial bucket")

    if "pii" not in text:
        issues.append(f"{path}: PII handling not referenced")

    if "routing" not in text:
        issues.append(f"{path}: no routing tests mentioned")

    if "owner" not in text:
        issues.append(f"{path}: no owner assigned for eval suite")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No Agentforce test plan docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Agentforce test plan looks complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
