#!/usr/bin/env python3
"""Heuristic checker for Event Relay configuration documents.

Scans markdown relay-config docs for required sections (channel, aws,
salesforce, consumer contract, ops) and flags common omissions such as
missing external id, missing watermark, and non-idempotent consumers.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "channel",
    "aws side",
    "salesforce side",
    "consumer contract",
    "ops",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Event Relay configuration docs.",
    )
    parser.add_argument(
        "--docs-dir",
        default=".",
        help="Directory containing relay config markdown files.",
    )
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "external id" not in text:
        issues.append(f"{path}: no external id on IAM role — confused deputy risk")

    if "idempot" not in text:
        issues.append(f"{path}: consumer idempotency not documented")

    if "high-volume" not in text and "cdc" not in text:
        issues.append(f"{path}: channel type (High-Volume PE / CDC) not specified")

    if "replay" not in text:
        issues.append(f"{path}: no replay / watermark strategy")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No config docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Relay config docs look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
