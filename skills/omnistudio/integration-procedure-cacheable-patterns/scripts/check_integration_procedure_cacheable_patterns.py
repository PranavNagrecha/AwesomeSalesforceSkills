#!/usr/bin/env python3
"""Heuristic checker for IP cache design documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "cache key",
    "partition",
    "ttl",
    "invalidation",
    "fallback",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect IP cache design docs.",
    )
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "org-wide" not in text and "session" not in text:
        issues.append(f"{path}: no partition type (org-wide/session) specified")

    if "version" not in text:
        issues.append(f"{path}: key version / prefix not documented — invalidation risk")

    if "hit ratio" not in text and "hit rate" not in text:
        issues.append(f"{path}: no hit ratio monitoring mentioned")

    if "fallback" in text and "live fetch" not in text and "accelerator" not in text:
        issues.append(f"{path}: fallback present but live-fetch path not described")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No design docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Cache design docs look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
