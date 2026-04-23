#!/usr/bin/env python3
"""Heuristic checker for Agentforce agent handoff design documents.

Scans markdown handoff-design documents for the minimum required sections
(triggers, context package, destinations, user-facing message) and flags
common omissions surfaced in `references/llm-anti-patterns.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "triggers",
    "context package",
    "destinations",
)

RECOMMENDED_SECTIONS = (
    "hand-back",
    "sign-off",
)

TRIGGER_CATEGORIES = (
    "user-initiated",
    "confidence",
    "scope",
    "policy",
    "authorization",
    "technical",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect handoff-design documents for required sections.",
    )
    parser.add_argument(
        "--docs-dir",
        default=".",
        help="Directory containing handoff design markdown files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat recommended-section omissions as failures too.",
    )
    return parser.parse_args()


def check_file(path: Path, strict: bool) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    missing_trigger_cats = [c for c in TRIGGER_CATEGORIES if c not in text]
    if len(missing_trigger_cats) > 2:
        issues.append(
            f"{path}: only "
            f"{len(TRIGGER_CATEGORIES) - len(missing_trigger_cats)}/6 trigger "
            f"categories referenced — missing: {', '.join(missing_trigger_cats)}"
        )

    if "user message" not in text and "user-facing" not in text:
        issues.append(f"{path}: no user-facing handoff message defined (silent transfer risk)")

    if "fallback" not in text:
        issues.append(f"{path}: no presence-aware fallback referenced (queue-empty risk)")

    if strict:
        for section in RECOMMENDED_SECTIONS:
            if section not in text:
                issues.append(f"{path}: missing recommended section '{section}'")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No markdown handoff docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path, args.strict))

    if not all_issues:
        print("Handoff design documents look complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
