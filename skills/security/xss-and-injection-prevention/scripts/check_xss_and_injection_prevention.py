#!/usr/bin/env python3
"""Checker script for XSS and Injection Prevention skill.

Scans Apex and Visualforce files for common XSS and injection patterns:
- Dynamic SOQL string concatenation (potential SOQL injection)
- Raw expressions in Visualforce script blocks (potential XSS)
- PageReference construction without obvious allowlist check (potential open redirect)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_xss_and_injection_prevention.py [--help]
    python3 check_xss_and_injection_prevention.py --source-dir force-app/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan Salesforce source files for XSS and injection vulnerabilities.",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


def check_soql_injection(apex_file: Path) -> list[str]:
    """Check for Database.query() with string concatenation."""
    issues: list[str] = []
    content = apex_file.read_text(encoding="utf-8", errors="replace")

    # Look for Database.query() calls with + concatenation
    lines = content.splitlines()
    in_query = False
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Simple heuristic: Database.query( with + in the argument
        if "Database.query(" in stripped and "+" in stripped:
            # Exclude lines that are obviously using bind variables
            if not re.search(r":\s*\w+", stripped):
                issues.append(
                    f"{apex_file}:{i}: Potential SOQL injection — "
                    f"Database.query() with string concatenation. "
                    f"Use bind variables (:varName) instead."
                )

    return issues


def check_vf_script_blocks(vf_file: Path) -> list[str]:
    """Check for raw {!expression} inside <script> blocks."""
    issues: list[str] = []
    content = vf_file.read_text(encoding="utf-8", errors="replace")

    # Find <script> blocks
    script_pattern = re.compile(r"<script[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE)
    for m in script_pattern.finditer(content):
        script_content = m.group(1)
        line_offset = content[: m.start()].count("\n") + 1
        # Look for {!expression} not wrapped in JSENCODE
        expr_pattern = re.compile(r"\{!\s*(?!JSENCODE\()(?!JSINHTMLENCODE\()([^}]+)\}")
        for em in expr_pattern.finditer(script_content):
            line_in_script = script_content[: em.start()].count("\n")
            issues.append(
                f"{vf_file}:{line_offset + line_in_script}: Potential XSS — "
                f"Visualforce expression '{em.group(0)}' inside <script> block "
                f"without JSENCODE(). Use {{!JSENCODE({em.group(1).strip()})}} instead."
            )

    return issues


def check_open_redirect(apex_file: Path) -> list[str]:
    """Check for new PageReference() with potentially user-controlled input."""
    issues: list[str] = []
    content = apex_file.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if "new PageReference(" in stripped:
            # Check if the argument looks like a variable (not a Page. or '/literal')
            arg_match = re.search(r"new PageReference\(\s*([^)]+)\s*\)", stripped)
            if arg_match:
                arg = arg_match.group(1).strip()
                # Skip obvious safe patterns: string literals, Page.* references
                if not arg.startswith("'") and not arg.startswith('"') and not arg.startswith("Page."):
                    issues.append(
                        f"{apex_file}:{i}: Potential open redirect — "
                        f"new PageReference({arg}) uses a variable. "
                        f"Validate the URL against an allowlist before redirecting."
                    )

    return issues


def check_xss_and_injection(source_dir: Path) -> list[str]:
    """Return a list of issue strings found in the source directory."""
    issues: list[str] = []

    if not source_dir.exists():
        issues.append(f"Source directory not found: {source_dir}")
        return issues

    # Check Apex files
    for apex_file in source_dir.rglob("*.cls"):
        issues.extend(check_soql_injection(apex_file))
        issues.extend(check_open_redirect(apex_file))

    # Check Visualforce files
    for vf_file in source_dir.rglob("*.page"):
        issues.extend(check_vf_script_blocks(vf_file))

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)
    issues = check_xss_and_injection(source_dir)

    if not issues:
        print("No XSS or injection patterns found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
