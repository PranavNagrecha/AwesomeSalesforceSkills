#!/usr/bin/env python3
"""Heuristic checker for ADR files."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "status",
    "context",
    "decision",
    "consequences",
    "alternatives considered",
    "date",
    "deciders",
)

TITLE_RE = re.compile(r"^#\s+ADR-\d{4}:\s+.+", re.MULTILINE)
ALT_RE = re.compile(r"(?:Alternative|###)\s+[A-Za-z0-9]+.*\n.*?(why rejected)", re.IGNORECASE | re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan ADR files.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()

    if not TITLE_RE.search(text):
        issues.append(f"{path}: title does not match 'ADR-XXXX: ...'")

    for section in REQUIRED_SECTIONS:
        if section not in lower:
            issues.append(f"{path}: missing section '{section}'")

    # At least two rejected alternatives.
    if lower.count("why rejected") < 2 and lower.count("rejected:") < 2:
        issues.append(f"{path}: fewer than 2 alternatives considered")

    if "negative" not in lower and "tradeoff" not in lower and "trade-off" not in lower:
        issues.append(f"{path}: consequences lacks a negative / tradeoff")

    if "superseded" in lower and "adr-" not in lower:
        issues.append(f"{path}: superseded status missing forward ADR link")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: not found: {root}")
        return 1

    targets = [p for p in root.rglob("*.md") if p.name.lower().startswith("adr") or re.match(r"\d{4}-", p.name)]
    if not targets:
        targets = list(root.rglob("*.md"))
    if not targets:
        print("No ADR files found.")
        return 0

    issues: list[str] = []
    for path in targets:
        issues.extend(check_file(path))

    if not issues:
        print("ADR files look complete.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
