#!/usr/bin/env python3
"""Checker script for Multi-Currency Sales Architecture skill.

Scans Salesforce metadata for common multi-currency architecture issues:
- Roll-up summary fields on currency amounts (risky under ACM)
- Custom objects with currency fields but no conversion logic
- Missing DatedConversionRate references in Apex

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_multi_currency_sales_architecture.py [--help]
    python3 check_multi_currency_sales_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Multi-Currency Sales Architecture metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find files with the given suffix under root."""
    matches: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(suffix):
                matches.append(Path(dirpath) / fname)
    return matches


def check_rollup_currency_fields(manifest_dir: Path) -> list[str]:
    """Detect roll-up summary fields that aggregate currency amounts.

    Under ACM, these roll-ups use the static CurrencyType rate, not dated
    rates, which produces incorrect totals.
    """
    issues: list[str] = []
    ns = "{http://soap.sforce.com/2006/04/metadata}"

    for obj_file in find_files(manifest_dir, ".object-meta.xml"):
        try:
            tree = ET.parse(obj_file)
        except ET.ParseError:
            continue

        root = tree.getroot()
        for field in root.findall(f".//{ns}fields"):
            field_type = field.find(f"{ns}type")
            summarized_field = field.find(f"{ns}summarizedField")
            full_name = field.find(f"{ns}fullName")

            if field_type is not None and field_type.text == "Summary":
                if summarized_field is not None and summarized_field.text:
                    summary_target = summarized_field.text.lower()
                    currency_hints = ["amount", "price", "cost", "revenue", "value"]
                    if any(hint in summary_target for hint in currency_hints):
                        fname = full_name.text if full_name is not None else "unknown"
                        issues.append(
                            f"Roll-up summary '{fname}' in {obj_file.name} aggregates "
                            f"'{summarized_field.text}' — under ACM this uses the static "
                            f"rate, not dated rates. Consider Apex-based aggregation."
                        )
    return issues


def check_custom_currency_fields_without_conversion(manifest_dir: Path) -> list[str]:
    """Detect custom objects with currency fields but no evidence of
    DatedConversionRate usage in related Apex classes."""
    issues: list[str] = []
    ns = "{http://soap.sforce.com/2006/04/metadata}"

    # Collect custom objects that have currency fields
    custom_objects_with_currency: list[str] = []
    for obj_file in find_files(manifest_dir, ".object-meta.xml"):
        obj_name = obj_file.stem.replace("-meta", "").replace(".object", "")
        if not obj_name.endswith("__c"):
            continue

        try:
            tree = ET.parse(obj_file)
        except ET.ParseError:
            continue

        root = tree.getroot()
        for field in root.findall(f".//{ns}fields"):
            field_type = field.find(f"{ns}type")
            if field_type is not None and field_type.text == "Currency":
                custom_objects_with_currency.append(obj_name)
                break

    if not custom_objects_with_currency:
        return issues

    # Check if any Apex file references DatedConversionRate
    apex_files = find_files(manifest_dir, ".cls")
    has_dated_rate_reference = False
    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "DatedConversionRate" in content:
            has_dated_rate_reference = True
            break

    if not has_dated_rate_reference and custom_objects_with_currency:
        for obj_name in custom_objects_with_currency:
            issues.append(
                f"Custom object '{obj_name}' has Currency fields but no Apex code "
                f"references DatedConversionRate. Under ACM, custom objects use the "
                f"static rate only. Consider adding Apex-based dated conversion."
            )

    return issues


def check_hardcoded_rates_in_apex(manifest_dir: Path) -> list[str]:
    """Detect potential hardcoded exchange rates in Apex classes."""
    issues: list[str] = []
    # Pattern: variable assignments that look like exchange rates
    rate_pattern = re.compile(
        r"\b(?:rate|exchangeRate|conversionRate|fxRate)\s*=\s*[\d.]+",
        re.IGNORECASE,
    )

    for apex_file in find_files(manifest_dir, ".cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for i, line in enumerate(content.splitlines(), start=1):
            if rate_pattern.search(line):
                issues.append(
                    f"Possible hardcoded exchange rate in {apex_file.name}:{i} — "
                    f"'{line.strip()}'. Query CurrencyType or DatedConversionRate instead."
                )

    return issues


def check_multi_currency_sales_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_rollup_currency_fields(manifest_dir))
    issues.extend(check_custom_currency_fields_without_conversion(manifest_dir))
    issues.extend(check_hardcoded_rates_in_apex(manifest_dir))

    if not issues:
        return issues

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_multi_currency_sales_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
