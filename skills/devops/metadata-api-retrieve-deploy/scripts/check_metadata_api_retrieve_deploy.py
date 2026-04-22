#!/usr/bin/env python3
"""Checker for Metadata API Retrieve / Deploy skill.

Scans a project for manifest and CI anti-patterns:
- package.xml wildcards in a CI-looking repo
- Deploy scripts using --ignore-errors or --test-level NoTestRun
- Username/password CLI auth in CI scripts

Usage:
    python3 check_metadata_api_retrieve_deploy.py [--manifest-dir path/to/project]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


WILDCARD = re.compile(r"<members>\s*\*\s*</members>", re.IGNORECASE)
IGNORE_ERRORS = re.compile(r"--ignore-errors\b")
NO_TEST_RUN = re.compile(r"--test-level\s+NoTestRun", re.IGNORECASE)
PASSWORD_LOGIN = re.compile(
    r"sf\s+org\s+login\b[^\n]*--password\b|sfdx\s+force:auth:[^\n]*--password",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Metadata API deploy anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory to scan.")
    return parser.parse_args()


def check_manifests(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("package.xml"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in WILDCARD.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            issues.append(
                f"{path.relative_to(root)}:{line_no}: wildcard <members>*</members>; use explicit members for CI"
            )
    return issues


def check_scripts(root: Path) -> list[str]:
    issues: list[str] = []
    for pattern in ("*.sh", "*.yml", "*.yaml", "*.ps1"):
        for path in root.rglob(pattern):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if IGNORE_ERRORS.search(text):
                issues.append(
                    f"{path.relative_to(root)}: uses --ignore-errors; risks partial deploy state"
                )
            for m in NO_TEST_RUN.finditer(text):
                line_no = text[: m.start()].count("\n") + 1
                issues.append(
                    f"{path.relative_to(root)}:{line_no}: --test-level NoTestRun invalid for production"
                )
            if PASSWORD_LOGIN.search(text):
                issues.append(
                    f"{path.relative_to(root)}: password-based sf login; prefer JWT bearer flow"
                )
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues = check_manifests(root) + check_scripts(root)
    if not issues:
        print("No Metadata API deploy anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
