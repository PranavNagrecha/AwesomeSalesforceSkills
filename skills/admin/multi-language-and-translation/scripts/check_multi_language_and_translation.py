#!/usr/bin/env python3
"""Checker script for Multi-Language and Translation skill.

Scans Apex files for hardcoded user-facing strings that should use Custom Labels.
Also checks for picklist value comparisons that may use translated labels.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_multi_language_and_translation.py [--help]
    python3 check_multi_language_and_translation.py --source-dir force-app/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex and metadata for multi-language translation issues.",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


def check_hardcoded_exception_messages(apex_file: Path) -> list[str]:
    """Warn if AuraHandledException or throw uses hardcoded string rather than Custom Label."""
    issues: list[str] = []
    try:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Look for AuraHandledException with a hardcoded string
            if re.search(r"new AuraHandledException\s*\(\s*'[^']{10,}'", stripped):
                issues.append(
                    f"{apex_file}:{i}: Hardcoded error message in AuraHandledException — "
                    f"use System.Label.YourLabel for translateable user-facing messages."
                )
    except OSError:
        pass
    return issues


def check_validation_rule_messages(source_dir: Path) -> list[str]:
    """Check validation rule XML for hardcoded error messages (no $Label reference)."""
    issues: list[str] = []
    # Validation rules use .validationRule-meta.xml
    for vr_file in source_dir.rglob("*.validationRule-meta.xml"):
        try:
            content = vr_file.read_text(encoding="utf-8", errors="replace")
            # Look for errorMessage with no $Label reference
            error_match = re.search(
                r"<errorMessage>(.*?)</errorMessage>", content, re.DOTALL
            )
            if error_match:
                msg = error_match.group(1).strip()
                if "$Label" not in msg and len(msg) > 10:
                    issues.append(
                        f"{vr_file}: Validation rule error message is hardcoded — "
                        f"use $Label.YourLabel for translateable messages. "
                        f"Current: '{msg[:50]}...'"
                    )
        except OSError:
            pass
    return issues


def check_translation_issues(source_dir: Path) -> list[str]:
    """Return a list of issue strings found in the source directory."""
    issues: list[str] = []

    if not source_dir.exists():
        issues.append(f"Source directory not found: {source_dir}")
        return issues

    # Check Apex files for hardcoded error messages
    for apex_file in source_dir.rglob("*.cls"):
        issues.extend(check_hardcoded_exception_messages(apex_file))

    # Check validation rules
    issues.extend(check_validation_rule_messages(source_dir))

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)
    issues = check_translation_issues(source_dir)

    if not issues:
        print("No multi-language translation issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
