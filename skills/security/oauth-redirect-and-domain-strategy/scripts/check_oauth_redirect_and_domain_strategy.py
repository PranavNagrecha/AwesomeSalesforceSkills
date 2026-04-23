#!/usr/bin/env python3
"""Heuristic checker for OAuth redirect / domain strategy plans."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "connected apps",
    "my domain",
    "enhanced domains",
    "monitoring",
    "sign-off",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect OAuth redirect plans.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "http://" in text and "https://" not in text:
        issues.append(f"{path}: HTTP callback referenced — require HTTPS")

    if "wildcard" in text and "not supported" not in text and "no wildcards" not in text:
        issues.append(f"{path}: wildcard callback referenced — not supported")

    if "redirect_uri_mismatch" not in text:
        issues.append(f"{path}: no mismatch monitoring mentioned")

    if "sandbox" not in text:
        issues.append(f"{path}: sandbox strategy not addressed")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No OAuth redirect docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("OAuth redirect / domain plan looks complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
