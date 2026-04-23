#!/usr/bin/env python3
"""Heuristic checker for IP restriction / relaxation plan documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "profile login ip",
    "org trusted ip",
    "connected app ip",
    "breakglass",
    "sign-off",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect IP restriction / relaxation plans.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "admin" in text and "lock" in text and "not" not in text and "do not" not in text:
        issues.append(f"{path}: appears to lock admin profile — prefer MFA + alerting")

    if "runbook" not in text:
        issues.append(f"{path}: no breakglass runbook referenced")

    if "review" not in text:
        issues.append(f"{path}: no review cadence for trusted ranges")

    if "partner" not in text and "integration" not in text:
        issues.append(f"{path}: partner / integration IPs not addressed")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No IP plan docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("IP restriction / relaxation plan looks complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
