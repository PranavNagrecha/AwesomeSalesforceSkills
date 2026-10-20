#!/usr/bin/env python3
"""Checker script for XSS and Injection Prevention skill.

Scans Apex and Visualforce files for common XSS and injection patterns:
- Dynamic SOQL string concatenation (potential SOQL injection; the guide's
  first defense is a static query with a bind, apexdev 264 L13661-13662)
- Raw expressions in Visualforce script blocks (potential XSS; expressions
  outside a component are not escaped, apexdev 264 L13480-13483)
- escape="false" tags whose value is not wrapped in an encoding function
  (apexdev 264 L13449-13452; the guide's safe form wraps HTMLENCODE, L13518)
- PageReference construction without obvious allowlist check (potential open redirect)

Every finding is a heuristic WARN. Exit codes:
  0 - no findings, or WARN findings only (one WARN for an empty directory)
  1 - ERROR (directory missing), or any WARN with --strict

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_xss_and_injection_prevention.py [--help]
    python3 check_xss_and_injection_prevention.py --manifest-dir force-app/ [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_ENCODED = re.compile(r"\{!\s*(HTMLENCODE|JSENCODE|JSINHTMLENCODE|URLENCODE)\(", re.IGNORECASE)
_ESCAPE_FALSE_TAG = re.compile(r"<apex:\w+\b[^>]*\bescape\s*=\s*[\"']false[\"'][^>]*>", re.IGNORECASE | re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan Salesforce source files for XSS and injection vulnerabilities.",
    )
    parser.add_argument(
        "--manifest-dir", "--source-dir",
        dest="manifest_dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    parser.add_argument("--strict", action="store_true", help="Exit 1 on any WARN finding.")
    return parser.parse_args()


def check_soql_injection(apex_file: Path) -> list[str]:
    """Check for Database.query() with string concatenation."""
    issues: list[str] = []
    content = apex_file.read_text(encoding="utf-8", errors="replace")

    for i, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        # Simple heuristic: Database.query( with + in the argument
        if "Database.query(" in stripped and "+" in stripped:
            # Exclude lines that are obviously using bind variables
            if not re.search(r":\s*\w+", stripped):
                issues.append(
                    f"{apex_file}:{i}: Potential SOQL injection — "
                    f"Database.query() with string concatenation. "
                    f"Use a static query or bind variables (:varName) instead."
                )

    return issues


def check_vf_script_blocks(vf_file: Path) -> list[str]:
    """Check for raw {!expression} inside <script> blocks."""
    issues: list[str] = []
    content = vf_file.read_text(encoding="utf-8", errors="replace")

    script_pattern = re.compile(r"<script[^>]*>(.*?)</script>", re.DOTALL | re.IGNORECASE)
    expr_pattern = re.compile(r"\{!\s*(?!JSENCODE\()(?!JSINHTMLENCODE\()([^}]+)\}")
    for m in script_pattern.finditer(content):
        script_content = m.group(1)
        line_offset = content[: m.start()].count("\n") + 1
        for em in expr_pattern.finditer(script_content):
            line_in_script = script_content[: em.start()].count("\n")
            issues.append(
                f"{vf_file}:{line_offset + line_in_script}: Potential XSS — "
                f"Visualforce expression '{em.group(0)}' inside <script> block "
                f"without JSENCODE(). Use {{!JSENCODE({em.group(1).strip()})}} instead."
            )

    return issues


def check_vf_escape_false(vf_file: Path) -> list[str]:
    """Flag escape="false" tags whose merge expressions are not wrapped in an encoding function."""
    issues: list[str] = []
    content = vf_file.read_text(encoding="utf-8", errors="replace")
    for m in _ESCAPE_FALSE_TAG.finditer(content):
        tag = m.group(0)
        if "{!" in tag and tag.count("{!") > len(_ENCODED.findall(tag)):
            line = content[: m.start()].count("\n") + 1
            issues.append(
                f"{vf_file}:{line}: Potential XSS — escape=\"false\" output is unfiltered; "
                f"wrap the value in HTMLENCODE() or keep default escaping."
            )
    return issues


def check_open_redirect(apex_file: Path) -> list[str]:
    """Check for new PageReference() with potentially user-controlled input."""
    issues: list[str] = []
    content = apex_file.read_text(encoding="utf-8", errors="replace")

    for i, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if "new PageReference(" in stripped:
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
    """Return a list of WARN strings found in the source directory."""
    issues: list[str] = []
    apex_files = list(source_dir.rglob("*.cls"))
    vf_files = list(source_dir.rglob("*.page")) + list(source_dir.rglob("*.component"))
    if not apex_files and not vf_files:
        return [f"{source_dir} holds no .cls, .page or .component files — nothing to check."]

    for apex_file in apex_files:
        issues.extend(check_soql_injection(apex_file))
        issues.extend(check_open_redirect(apex_file))

    for vf_file in vf_files:
        issues.extend(check_vf_script_blocks(vf_file))
        issues.extend(check_vf_escape_false(vf_file))

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.manifest_dir)
    if not source_dir.is_dir():
        print(f"ERROR: directory not found: {source_dir}")
        sys.exit(1)

    issues = check_xss_and_injection(source_dir)
    if not issues:
        print("No XSS or injection patterns found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}")

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
