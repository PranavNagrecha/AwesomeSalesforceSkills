#!/usr/bin/env python3
"""Checker script for Integration Pattern Selection skill.

Checks org metadata or configuration relevant to Integration Pattern Selection.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_integration_pattern_selection.py [--help]
    python3 check_integration_pattern_selection.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Integration Pattern Selection configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_apex_callouts(file_path: Path) -> list[str]:
    """Check Apex class files for synchronous callout anti-patterns."""
    import re

    issues: list[str] = []
    content = file_path.read_text(encoding="utf-8", errors="ignore")

    # Check for multiple sequential callouts (hub-and-spoke anti-pattern)
    callout_count = len(re.findall(r'Http\(\)\.send\(|Http\.send\(|callout\s*=\s*true', content, re.IGNORECASE))
    if callout_count >= 3:
        issues.append(
            f"{file_path.name}: Multiple sequential HTTP callouts detected ({callout_count} found). "
            "Multiple sequential callouts to different systems suggest hub-and-spoke orchestration in Apex. "
            "Per Salesforce Integration Patterns guidance, multi-system orchestration should live in middleware."
        )

    # Check for callout in trigger context with no future/async annotation
    if re.search(r'@isTest', content, re.IGNORECASE):
        return issues  # Skip test classes

    if re.search(r'trigger\s+\w+\s+on', content, re.IGNORECASE) and re.search(r'Http\(\)', content):
        issues.append(
            f"{file_path.name}: Apex trigger appears to contain HTTP callouts. "
            "Callouts in trigger context require @future or Queueable Apex to avoid mixed DML/callout errors. "
            "Consider whether the Fire-and-Forget pattern (Platform Event) is more appropriate."
        )

    return issues


def check_integration_pattern_selection(manifest_dir: Path) -> list[str]:
    """Check Apex code for integration pattern anti-patterns."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan Apex class and trigger files
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))
    for apex_file in apex_files:
        issues.extend(check_apex_callouts(apex_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_integration_pattern_selection(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
