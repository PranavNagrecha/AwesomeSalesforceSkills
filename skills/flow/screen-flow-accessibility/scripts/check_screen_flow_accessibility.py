#!/usr/bin/env python3
"""Heuristic checker for Screen Flow accessibility audit documents.

Scans markdown audit docs for the minimum sections (per-screen checklist,
keyboard test, screen reader test, contrast, WCAG mapping) and common
omissions from `references/llm-anti-patterns.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "per-screen checklist",
    "keyboard test",
    "screen reader test",
    "contrast",
    "wcag",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Screen Flow accessibility audit documents.",
    )
    parser.add_argument(
        "--docs-dir",
        default=".",
        help="Directory containing audit markdown files.",
    )
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "nvda" not in text and "voiceover" not in text and "jaws" not in text:
        issues.append(f"{path}: no specific screen reader named (audit untested)")

    if "placeholder" in text and "label" not in text:
        issues.append(f"{path}: placeholder used without label — WCAG 1.3.1 risk")

    if "color" in text and "4.5" not in text:
        issues.append(f"{path}: contrast ratio target (4.5:1) not documented")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No audit documents found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("Audit documents look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
