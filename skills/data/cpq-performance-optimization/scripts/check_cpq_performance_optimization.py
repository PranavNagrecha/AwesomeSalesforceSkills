#!/usr/bin/env python3
"""Checker script for CPQ Performance Optimization skill.

Scans Salesforce metadata in a local directory for common CPQ performance
anti-patterns:
  - SBQQ__Code__c content approaching or exceeding the 131,072-char limit
  - QCP field declaration arrays that appear empty or very large (>25 fields)
  - Large Quote Mode not configured in CPQ package settings XML

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_performance_optimization.py [--manifest-dir PATH]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Hard limit documented in CPQ help: Long Text Area max for SBQQ__Code__c
SBQQ_CODE_HARD_LIMIT = 131_072
SBQQ_CODE_WARN_THRESHOLD = 100_000

# Heuristic: declaration arrays over this size are likely over-declared
QCP_FIELD_DECLARATION_WARN_COUNT = 25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CPQ performance optimization configuration and metadata "
            "for common anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_sbqq_custom_script_size(manifest_dir: Path) -> list[str]:
    """Warn if any SBQQ__CustomScript__c data file contains large inline code."""
    issues: list[str] = []

    # Look for exported object data files (data export CSVs or XML records)
    # Common patterns: CustomScript.json, CustomScript.xml, or *CustomScript*.xml
    for pattern in [
        "**/*CustomScript*.xml",
        "**/*CustomScript*.json",
        "**/*SBQQ__CustomScript*.xml",
        "**/*SBQQ__CustomScript*.json",
    ]:
        for path in manifest_dir.glob(pattern):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            # Look for SBQQ__Code__c content in the file
            # Works for both XML and JSON exports
            code_marker_xml = "<SBQQ__Code__c>"
            code_marker_json = '"SBQQ__Code__c"'

            if code_marker_xml in content:
                start = content.index(code_marker_xml) + len(code_marker_xml)
                end = content.find("</SBQQ__Code__c>", start)
                if end != -1:
                    code_length = end - start
                    if code_length >= SBQQ_CODE_HARD_LIMIT:
                        issues.append(
                            f"{path}: SBQQ__Code__c content is {code_length:,} characters "
                            f"which meets or exceeds the hard limit of "
                            f"{SBQQ_CODE_HARD_LIMIT:,}. Migrate to Static Resource "
                            f"+ eval() bootstrap architecture."
                        )
                    elif code_length >= SBQQ_CODE_WARN_THRESHOLD:
                        issues.append(
                            f"{path}: SBQQ__Code__c content is {code_length:,} characters "
                            f"(warning threshold: {SBQQ_CODE_WARN_THRESHOLD:,}). "
                            f"Plan Static Resource migration before the next plugin update."
                        )

            elif code_marker_json in content:
                # Rough heuristic for JSON: measure content between the key and next key
                start = content.index(code_marker_json) + len(code_marker_json)
                # Find the value start (after colon and optional space/quote)
                colon_pos = content.find(":", start)
                if colon_pos != -1:
                    value_start = colon_pos + 1
                    # Estimate: find the next top-level comma or closing brace
                    # This is approximate — use as a heuristic only
                    code_snippet = content[value_start : value_start + SBQQ_CODE_HARD_LIMIT + 1000]
                    code_length = len(code_snippet.strip().strip('"'))
                    if code_length >= SBQQ_CODE_HARD_LIMIT:
                        issues.append(
                            f"{path}: SBQQ__Code__c JSON value appears to exceed "
                            f"{SBQQ_CODE_HARD_LIMIT:,} characters. Verify and consider "
                            f"Static Resource migration."
                        )

    return issues


def check_qcp_field_declarations(manifest_dir: Path) -> list[str]:
    """Warn if QCP JavaScript files have suspiciously large field declaration arrays."""
    issues: list[str] = []

    js_patterns = [
        "**/*QuoteCalculator*.js",
        "**/*qcp*.js",
        "**/*QCP*.js",
        "**/*plugin*.js",
    ]

    for pattern in js_patterns:
        for path in manifest_dir.glob(pattern):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            # Look for fieldsToCalculate or lineFieldsToCalculate functions
            for fn_name in ("fieldsToCalculate", "lineFieldsToCalculate"):
                if fn_name not in content:
                    continue

                fn_pos = content.index(fn_name)
                # Extract a window of text after the function name to find the return array
                window = content[fn_pos : fn_pos + 2000]

                # Count string entries in the array (rough heuristic: count quoted items)
                import re
                bracket_match = re.search(r"\[([^\]]*)\]", window)
                if bracket_match:
                    array_content = bracket_match.group(1)
                    field_entries = [
                        f.strip().strip("'\"")
                        for f in array_content.split(",")
                        if f.strip().strip("'\"")
                    ]
                    count = len(field_entries)
                    if count > QCP_FIELD_DECLARATION_WARN_COUNT:
                        issues.append(
                            f"{path}: {fn_name}() declares {count} fields "
                            f"(>{QCP_FIELD_DECLARATION_WARN_COUNT} heuristic threshold). "
                            f"Review for over-declaration — undeclared fields cause silent "
                            f"null reads; over-declared fields inflate the calculation payload."
                        )
                    elif count == 0:
                        issues.append(
                            f"{path}: {fn_name}() appears to return an empty array. "
                            f"Verify the plugin does not read any fields — if it does, "
                            f"those fields must be declared here."
                        )

    return issues


def check_cpq_settings_xml(manifest_dir: Path) -> list[str]:
    """Check CPQ Package Settings XML for Large Quote Mode configuration."""
    issues: list[str] = []

    # CPQ package settings may appear in CustomSettings or InstalledPackageVersionSetting
    settings_patterns = [
        "**/*SBQQ__Preferences__c*.xml",
        "**/*CPQSettings*.xml",
        "**/settings/SBQQ*.xml",
    ]

    found_settings = False
    for pattern in settings_patterns:
        for path in manifest_dir.glob(pattern):
            found_settings = True
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            # Look for Large Quote Mode field
            if "LargeQuote" not in content and "largeQuote" not in content:
                issues.append(
                    f"{path}: CPQ settings file does not appear to configure Large Quote "
                    f"Mode (SBQQ__LargeQuote fields not found). If quotes exceed 150 lines, "
                    f"Large Quote Mode should be explicitly configured."
                )

    return issues


def check_cpq_performance_optimization(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sbqq_custom_script_size(manifest_dir))
    issues.extend(check_qcp_field_declarations(manifest_dir))
    issues.extend(check_cpq_settings_xml(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cpq_performance_optimization(manifest_dir)

    if not issues:
        print("No CPQ performance optimization issues detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
