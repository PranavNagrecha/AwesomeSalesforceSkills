#!/usr/bin/env python3
"""Heuristic checker for flow post-commit plan documents.

Scans markdown plan docs for required sections (work, durability,
mechanism, idempotency, logging) and flags omissions from
`references/llm-anti-patterns.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "work to run post-commit",
    "durability",
    "chosen mechanism",
    "idempotency",
    "logging",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect flow post-commit plan docs.",
    )
    parser.add_argument(
        "--docs-dir",
        default=".",
        help="Directory containing plan markdown files.",
    )
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "scheduled path" not in text and "platform event" not in text and "queueable" not in text:
        issues.append(f"{path}: no mechanism (scheduled path/platform event/queueable) named")

    if "idempot" not in text:
        issues.append(f"{path}: no idempotency discussion")

    if "retry" not in text and "replay" not in text:
        issues.append(f"{path}: no retry or replay plan documented")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No plan docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Plan docs look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
