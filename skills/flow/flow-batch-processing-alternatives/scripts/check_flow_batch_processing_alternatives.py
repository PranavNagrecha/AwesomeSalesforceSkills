#!/usr/bin/env python3
"""Heuristic checker for flow batch strategy documents.

Scans markdown strategy docs for required sections (workload, measured
limits, decision, implementation) and flags omissions listed in
`references/llm-anti-patterns.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "workload",
    "measured limits",
    "decision",
    "implementation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect flow batch strategy docs.",
    )
    parser.add_argument(
        "--docs-dir",
        default=".",
        help="Directory containing strategy markdown files.",
    )
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "retry" not in text:
        issues.append(f"{path}: no retry strategy mentioned — partial-failure risk")

    if "chunk" not in text and "batch" not in text:
        issues.append(f"{path}: neither chunking nor batch sizing documented")

    if "monitor" not in text and "alert" not in text:
        issues.append(f"{path}: no monitoring or alert plan")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No strategy docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Strategy docs look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
