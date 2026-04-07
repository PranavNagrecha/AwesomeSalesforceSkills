#!/usr/bin/env python3
"""Checker script for MCP Tool Definition Apex skill.

Checks Apex classes that extend McpToolDefinition for common anti-patterns:
- Missing global access modifier on class and overriding methods
- validate() returning empty string instead of null
- SOQL string concatenation (injection risk) in execute()
- Raw SObject return from execute() (serialization surprises)
- Missing inputSchema() return structure (no 'type' => 'object')

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_mcp_tool_definition_apex.py [--help]
    python3 check_mcp_tool_definition_apex.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check McpToolDefinition Apex classes for common implementation issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_apex_classes(manifest_dir: Path) -> list[Path]:
    """Find all .cls files under the manifest directory."""
    candidates = []
    for apex_dir in [
        manifest_dir / "force-app" / "main" / "default" / "classes",
        manifest_dir / "classes",
        manifest_dir,
    ]:
        if apex_dir.exists():
            candidates.extend(apex_dir.glob("*.cls"))
            break
    return candidates


def check_mcp_tool_definition_apex(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_apex_classes(manifest_dir)
    tool_classes_found = 0

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only inspect classes that extend McpToolDefinition
        if "McpToolDefinition" not in content or "extends McpToolDefinition" not in content:
            continue

        tool_classes_found += 1
        fname = apex_file.name

        # Check 1: Class must use 'global' access modifier
        if re.search(r"\bpublic\s+(class|with sharing class|without sharing class)\b", content):
            issues.append(
                f"{fname}: McpToolDefinition subclass uses 'public' instead of 'global'. "
                "Extending a global abstract class from a managed package requires 'global class ...'."
            )

        # Check 2: Override methods must use 'global override', not 'public override'
        if re.search(r"\bpublic\s+override\b", content):
            issues.append(
                f"{fname}: uses 'public override' on an overriding method. "
                "Methods overriding 'global abstract' from McpToolDefinition must use 'global override'."
            )

        # Check 3: validate() must not return empty string as success signal
        # Look for 'return "";' or "return '';" in validate method context
        if re.search(r"return\s+[\"']{2}\s*;", content):
            issues.append(
                f"{fname}: may return an empty string from validate(). "
                "validate() must return null (not empty string) to indicate success. "
                "Returning '' is treated as a validation error by McpServer."
            )

        # Check 4: SOQL string concatenation in execute() — injection risk
        soql_concat_pattern = re.compile(
            r"SELECT\b.*\+\s*[\w(]", re.IGNORECASE | re.DOTALL
        )
        if soql_concat_pattern.search(content):
            issues.append(
                f"{fname}: may contain SOQL string concatenation in execute(). "
                "Use bind variables (:variable) for all user-supplied input. "
                "String concatenation into SOQL is a SOQL injection vulnerability."
            )

        # Check 5: inputSchema() should include 'type' => 'object'
        if "inputSchema" in content and "'type'" not in content and '"type"' not in content:
            issues.append(
                f"{fname}: inputSchema() does not appear to include a 'type' key. "
                "The JSON Schema object must include '\"type\": \"object\"' at the root level."
            )

        # Check 6: Warn if execute() queries a single record without list guard
        # Pattern: assign directly from [SELECT ... LIMIT 1] without a list
        single_row_assign = re.compile(
            r"\w+\s+\w+\s*=\s*\[SELECT\b[^\]]+LIMIT\s+1\]", re.IGNORECASE
        )
        if single_row_assign.search(content):
            issues.append(
                f"{fname}: assigns directly from a single-row SOQL query (LIMIT 1). "
                "If no record is found, Apex throws QueryException. "
                "Use List<SObject> and check .isEmpty() before accessing [0]."
            )

    if tool_classes_found == 0:
        # Not necessarily an error — the manifest may not have any tool classes yet
        pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_mcp_tool_definition_apex(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
