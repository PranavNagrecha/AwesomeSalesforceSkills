#!/usr/bin/env python3
"""Checker script for Managed Package Development skill.

Validates 1GP managed package development artifacts for common issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_managed_package_development.py --manifest-dir <path>

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

import argparse
import re
import sys
from pathlib import Path


def check_postinstall_dml_size(path: Path) -> list[str]:
    """Warn if PostInstall scripts contain large DML operations."""
    issues = []
    postinstall_pattern = re.compile(r"InstallHandler|onInstall", re.IGNORECASE)
    large_dml_pattern = re.compile(r"insert\s+\[|Database\.insert\(", re.IGNORECASE)
    queueable_pattern = re.compile(r"System\.enqueueJob|Queueable", re.IGNORECASE)

    for apex_file in list(path.glob("**/*.cls")):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if postinstall_pattern.search(content) and large_dml_pattern.search(content):
            if not queueable_pattern.search(content):
                issues.append(
                    f"WARN: {apex_file.name} appears to be a PostInstall script with direct DML inserts "
                    f"but no Queueable pattern. PostInstall scripts run in the subscriber org under governor limits. "
                    f"Large DML operations should be offloaded to a Queueable: System.enqueueJob(new SetupQueueable())."
                )
    return issues


def check_cli_1gp_reference(path: Path) -> list[str]:
    """Warn if plan documents or scripts reference sf package version create for 1GP."""
    issues = []
    cli_pattern = re.compile(r"sf package version create|sfdx force:package:version:create", re.IGNORECASE)

    for doc_file in list(path.glob("**/*.md")) + list(path.glob("**/*.sh")) + list(path.glob("**/*.txt")):
        try:
            content = doc_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if cli_pattern.search(content):
            # Only warn if the doc also mentions 1GP context
            if "1GP" in content or "first-generation" in content.lower() or "packaging org" in content.lower():
                issues.append(
                    f"WARN: {doc_file.name} references 'sf package version create' in a 1GP context. "
                    f"This CLI command is for second-generation (2GP) packages only. "
                    f"1GP packages are uploaded via Setup > Package Manager > Upload or Tooling API."
                )
    return issues


def check_namespace_change_claim(path: Path) -> list[str]:
    """Warn if documentation claims namespace can be changed after release."""
    issues = []
    namespace_change_patterns = [
        re.compile(r"change.+namespace|rename.+namespace|update.+namespace.+prefix", re.IGNORECASE),
    ]

    for doc_file in list(path.glob("**/*.md")) + list(path.glob("**/*.txt")):
        try:
            content = doc_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in namespace_change_patterns:
            if pattern.search(content):
                issues.append(
                    f"WARN: {doc_file.name} suggests that a namespace prefix can be changed or renamed. "
                    f"Namespace prefixes are permanent after registration and cannot be changed, transferred, "
                    f"or reused. Rebranding requires creating a new package with a new namespace."
                )
                break
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate 1GP managed package development artifacts."
    )
    parser.add_argument("--manifest-dir", type=Path, default=Path("."),
                        help="Directory to scan for Apex, scripts, and documentation")
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.manifest_dir.exists():
        all_issues.extend(check_postinstall_dml_size(args.manifest_dir))
        all_issues.extend(check_cli_1gp_reference(args.manifest_dir))
        all_issues.extend(check_namespace_change_claim(args.manifest_dir))
    else:
        all_issues.append(f"ERROR: Directory not found: {args.manifest_dir}")

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    print("OK: No 1GP managed package development issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
