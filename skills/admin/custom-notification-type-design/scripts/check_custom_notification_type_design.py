#!/usr/bin/env python3
"""Heuristic checker for Custom Notification Type design documents.

Scans markdown design docs for required sections (purpose, trigger,
channels, targeting, body, consent) and flags anti-patterns such as
classic URL deep-links, missing throttling, or multi-channel overuse.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "purpose",
    "trigger",
    "channels",
    "targeting",
    "body",
    "consent",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Custom Notification Type design docs.",
    )
    parser.add_argument(
        "--docs-dir",
        default=".",
        help="Directory containing design markdown files.",
    )
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "/lightning/r/" not in text and "deep link" in text:
        issues.append(f"{path}: deep link present but no Lightning URL pattern")

    if "throttl" not in text and "min interval" not in text and "cap" not in text:
        issues.append(f"{path}: no throttling or frequency cap described")

    channel_hits = sum(
        1
        for ch in ("bell", "desktop", "mobile", "slack")
        if f"[x] {ch}" in text or f"[x]  {ch}" in text
    )
    if channel_hits >= 3:
        issues.append(f"{path}: 3+ channels selected — confirm urgency justifies multi-channel")

    if "actionable" not in text and "outcome" not in text:
        issues.append(f"{path}: no actionable-outcome statement")

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
        print("CNT design docs look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
