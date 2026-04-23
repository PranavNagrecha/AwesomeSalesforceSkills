#!/usr/bin/env python3
"""Heuristic checker for retriever-design documents.

Scans markdown retriever design docs for the minimum sections (fact
classification, retrievers, sharing enforcement, freshness, citations) and
common omissions listed in `references/llm-anti-patterns.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "fact classification",
    "retrievers",
    "sharing enforcement",
    "freshness",
    "citation",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect retriever design docs for completeness.",
    )
    parser.add_argument(
        "--docs-dir",
        default=".",
        help="Directory containing retriever design docs.",
    )
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "structured" not in text and "vector" not in text and "hybrid" not in text:
        issues.append(f"{path}: no retriever type (structured/vector/hybrid) mentioned")

    if "sla" not in text and "staleness" not in text:
        issues.append(f"{path}: no freshness SLA or staleness window documented")

    if "filter" not in text:
        issues.append(f"{path}: no retriever filter mentioned — sharing enforcement risk")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No retriever design docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Retriever design documents look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
