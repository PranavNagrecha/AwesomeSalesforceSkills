#!/usr/bin/env python3
"""Heuristic checker for MFA enforcement plan documents."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "populations",
    "sso assertion",
    "integration users",
    "exceptions",
    "rollout comms",
    "audit",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect MFA enforcement plans.")
    parser.add_argument("--docs-dir", default=".")
    return parser.parse_args()


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"{path}: missing required section '{section}'")

    if "expires" not in text and "expiry" not in text:
        issues.append(f"{path}: exceptions lack an expiry field")

    if "authncontext" not in text and "amr" not in text:
        issues.append(f"{path}: SSO auth-context assertion not referenced")

    if "connected app" not in text and "oauth" not in text:
        issues.append(f"{path}: no integration-user OAuth migration plan")

    if "login history" not in text:
        issues.append(f"{path}: no Login History audit mentioned")

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.docs_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}")
        return 1

    targets = list(root.rglob("*.md"))
    if not targets:
        print("No MFA plan docs found.")
        return 0

    all_issues: list[str] = []
    for path in targets:
        all_issues.extend(check_file(path))

    if not all_issues:
        print("MFA enforcement plan looks complete.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
