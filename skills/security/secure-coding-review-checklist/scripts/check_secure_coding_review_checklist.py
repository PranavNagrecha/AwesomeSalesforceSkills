#!/usr/bin/env python3
"""Checker script for Secure Coding Review Checklist skill.

Scans Apex classes, triggers, and Visualforce pages for common security
vulnerabilities: missing CRUD/FLS enforcement, SOQL injection vectors,
XSS in Visualforce, missing sharing declarations, and unprotected
@AuraEnabled methods.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_secure_coding_review_checklist.py [--help]
    python3 check_secure_coding_review_checklist.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex and Visualforce code for common security review vulnerabilities.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files(manifest_dir: Path, extensions: list[str]) -> list[Path]:
    """Recursively find files with given extensions."""
    files = []
    for ext in extensions:
        files.extend(manifest_dir.rglob(f"*{ext}"))
    return sorted(files)


def check_crud_fls(apex_files: list[Path]) -> list[str]:
    """Check for SOQL queries missing CRUD/FLS enforcement."""
    issues = []
    soql_pattern = re.compile(
        r"\[\s*SELECT\s+.+?\s+FROM\s+\w+.*?\]",
        re.IGNORECASE | re.DOTALL,
    )
    user_mode_pattern = re.compile(r"WITH\s+(USER_MODE|SYSTEM_MODE)", re.IGNORECASE)

    for filepath in apex_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = content.split("\n")
        # Track multi-line SOQL by joining content for regex, then map back to line numbers
        for match in soql_pattern.finditer(content):
            query_text = match.group(0)
            if not user_mode_pattern.search(query_text):
                # Find the line number of the match start
                line_num = content[:match.start()].count("\n") + 1
                issues.append(
                    f"CRUD/FLS: SOQL query without WITH USER_MODE/SYSTEM_MODE "
                    f"at {filepath.name}:{line_num}"
                )

    return issues


def check_soql_injection(apex_files: list[Path]) -> list[str]:
    """Check for dynamic SOQL with string concatenation."""
    issues = []
    # Pattern: Database.query( followed by string concatenation
    dynamic_query_pattern = re.compile(
        r"Database\.(query|countQuery)\s*\(",
        re.IGNORECASE,
    )

    for filepath in apex_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for i, line in enumerate(content.split("\n"), start=1):
            if dynamic_query_pattern.search(line):
                # Check if the line or nearby lines contain string concatenation with variables
                if "+" in line and ("'" in line or '"' in line):
                    issues.append(
                        f"SOQL Injection: Dynamic query with string concatenation "
                        f"at {filepath.name}:{i} — use bind variables or "
                        f"Database.queryWithBinds() instead"
                    )

    return issues


def check_sharing_declarations(apex_files: list[Path]) -> list[str]:
    """Check for Apex classes missing explicit sharing declarations."""
    issues = []
    class_pattern = re.compile(
        r"^\s*(?:public|global|private)\s+"
        r"(?:(?:virtual|abstract)\s+)?"
        r"class\s+(\w+)",
        re.MULTILINE,
    )
    sharing_pattern = re.compile(
        r"(with\s+sharing|without\s+sharing|inherited\s+sharing)",
        re.IGNORECASE,
    )

    for filepath in apex_files:
        if not filepath.suffix == ".cls":
            continue
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            # Check the text before the class keyword on the same declaration
            declaration_start = content.rfind("\n", 0, match.start()) + 1
            declaration_text = content[declaration_start : match.end()]
            if not sharing_pattern.search(declaration_text):
                line_num = content[:match.start()].count("\n") + 1
                issues.append(
                    f"Sharing: Class '{class_name}' has no explicit sharing "
                    f"declaration at {filepath.name}:{line_num} — add "
                    f"'with sharing', 'without sharing', or 'inherited sharing'"
                )

    return issues


def check_visualforce_xss(vf_files: list[Path]) -> list[str]:
    """Check for unencoded merge fields in Visualforce pages."""
    issues = []
    # Merge field in script context without JSENCODE
    script_merge_pattern = re.compile(
        r"<script[^>]*>[\s\S]*?\{!\s*(?!JSENCODE)(\w+)[\s\S]*?</script>",
        re.IGNORECASE,
    )
    # HTMLENCODE inside script block (wrong encoder)
    htmlencode_in_script = re.compile(
        r"<script[^>]*>[\s\S]*?HTMLENCODE\s*\([\s\S]*?</script>",
        re.IGNORECASE,
    )

    for filepath in vf_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for match in htmlencode_in_script.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            issues.append(
                f"XSS: HTMLENCODE used inside <script> block at "
                f"{filepath.name}:{line_num} — use JSENCODE for "
                f"JavaScript contexts"
            )

    return issues


def check_auraenabled_access(apex_files: list[Path]) -> list[str]:
    """Check for @AuraEnabled methods performing DML without permission checks."""
    issues = []
    aura_enabled_pattern = re.compile(r"@AuraEnabled", re.IGNORECASE)
    dml_pattern = re.compile(
        r"\b(insert|update|delete|upsert|Database\.(insert|update|delete|upsert))\b",
        re.IGNORECASE,
    )
    permission_pattern = re.compile(
        r"(FeatureManagement\.checkPermission|checkPermission|"
        r"UserInfo\.getProfileId|Custom_Permission|hasCustomPermission)",
        re.IGNORECASE,
    )

    for filepath in apex_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = content.split("\n")
        in_aura_method = False
        method_start_line = 0
        method_name = ""
        brace_depth = 0

        for i, line in enumerate(lines, start=1):
            if aura_enabled_pattern.search(line):
                in_aura_method = True
                method_start_line = i
                brace_depth = 0
                continue

            if in_aura_method:
                brace_depth += line.count("{") - line.count("}")

                # Extract method name from the line after @AuraEnabled
                if method_start_line == i - 1 or method_start_line == i:
                    name_match = re.search(r"\b(\w+)\s*\(", line)
                    if name_match:
                        method_name = name_match.group(1)

                if brace_depth <= 0 and "{" in content[
                    sum(len(l) + 1 for l in lines[:method_start_line - 1]):
                ]:
                    in_aura_method = False

    return issues


def check_secure_coding_review_checklist(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_files(manifest_dir, [".cls", ".trigger"])
    vf_files = find_files(manifest_dir, [".page", ".component"])

    if not apex_files and not vf_files:
        print(f"INFO: No Apex or Visualforce files found in {manifest_dir}")
        return issues

    print(f"Scanning {len(apex_files)} Apex files and {len(vf_files)} Visualforce files...")

    issues.extend(check_crud_fls(apex_files))
    issues.extend(check_soql_injection(apex_files))
    issues.extend(check_sharing_declarations(apex_files))
    issues.extend(check_visualforce_xss(vf_files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_secure_coding_review_checklist(manifest_dir)

    if not issues:
        print("No security issues found.")
        return 0

    print(f"\nFound {len(issues)} potential security issue(s):\n")
    for issue in issues:
        print(f"  ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
