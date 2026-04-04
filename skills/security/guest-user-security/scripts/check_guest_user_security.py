#!/usr/bin/env python3
"""Checker script for Guest User Security skill.

Scans Salesforce Apex source files for guest user security anti-patterns:
- Apex classes with 'without sharing' that are @AuraEnabled (guest-accessible)
- SOQL queries without WITH USER_MODE in AuraEnabled/RestResource classes
- Potential guest-facing classes missing 'with sharing' declaration

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_guest_user_security.py [--help]
    python3 check_guest_user_security.py --apex-dir path/to/force-app/main/default/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex classes for guest user security anti-patterns.",
    )
    parser.add_argument(
        "--apex-dir",
        default=".",
        help="Directory containing Apex .cls files (default: current directory).",
    )
    return parser.parse_args()


def scan_apex_files(apex_dir: Path) -> list[str]:
    """Scan Apex files for guest user security issues."""
    issues: list[str] = []

    if not apex_dir.exists():
        issues.append(f"Apex directory not found: {apex_dir}")
        return issues

    cls_files = list(apex_dir.rglob("*.cls"))
    if not cls_files:
        return issues

    for cls_file in cls_files:
        try:
            content = cls_file.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue

        # Check 1: without sharing + @AuraEnabled
        has_aura_enabled = "@AuraEnabled" in content
        has_rest_resource = "@RestResource" in content
        has_without_sharing = bool(re.search(r"\bwithout\s+sharing\b", content, re.IGNORECASE))
        has_with_sharing = bool(re.search(r"\bwith\s+sharing\b", content, re.IGNORECASE))

        if has_without_sharing and (has_aura_enabled or has_rest_resource):
            issues.append(
                f"{cls_file.name}: Class uses 'without sharing' and has @AuraEnabled or "
                f"@RestResource methods. If this class is reachable from an Experience Cloud "
                f"guest session, it will expose records ignoring OWD. Review and change to "
                f"'with sharing' unless there is a documented reason for system-mode access."
            )

        # Check 2: @AuraEnabled class without any sharing declaration
        if (has_aura_enabled or has_rest_resource) and not has_with_sharing and not has_without_sharing:
            issues.append(
                f"{cls_file.name}: Class has @AuraEnabled or @RestResource but no sharing "
                f"declaration ('with sharing' or 'without sharing'). In Apex, omitting the "
                f"sharing keyword defaults to 'without sharing' in most contexts. Add "
                f"'with sharing' explicitly for guest-accessible classes."
            )

        # Check 3: SOQL without WITH USER_MODE in AuraEnabled/RestResource classes
        if has_aura_enabled or has_rest_resource:
            soql_pattern = re.compile(r"\[SELECT\b.*?\bFROM\b", re.IGNORECASE | re.DOTALL)
            soql_matches = soql_pattern.findall(content)
            for match in soql_matches:
                if "WITH USER_MODE" not in match.upper() and "WITH SYSTEM_MODE" not in match.upper():
                    issues.append(
                        f"{cls_file.name}: SOQL query found without WITH USER_MODE in an "
                        f"@AuraEnabled/@RestResource class. Guest-accessible SOQL should use "
                        f"WITH USER_MODE to enforce field-level security and sharing in one pass."
                    )
                    break  # One warning per file

    return issues


def check_guest_user_security(apex_dir: Path) -> list[str]:
    """Return a list of issue strings found in the Apex directory."""
    return scan_apex_files(apex_dir)


def main() -> int:
    args = parse_args()
    apex_dir = Path(args.apex_dir)
    issues = check_guest_user_security(apex_dir)

    if not issues:
        print("No guest user security issues found in Apex classes.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\nFound {len(issues)} issue(s). Review each before deploying to an org with Experience Cloud guest access.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
