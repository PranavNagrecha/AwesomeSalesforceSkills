#!/usr/bin/env python3
"""Checker script for Retry And Backoff Patterns skill.

Checks org metadata or configuration relevant to Retry And Backoff Patterns.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_retry_and_backoff_patterns.py [--help]
    python3 check_retry_and_backoff_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Retry And Backoff Patterns configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_retry_and_backoff_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # TODO: Add real checks here. Examples:
    # - Parse XML metadata files and check for prohibited patterns
    # - Count fields/objects/flows and warn against limits
    # - Detect anti-patterns described in references/gotchas.md
    issues.append("TODO: implement actual checks for Retry And Backoff Patterns")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_retry_and_backoff_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
