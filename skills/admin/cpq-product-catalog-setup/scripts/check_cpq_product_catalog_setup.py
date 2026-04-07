#!/usr/bin/env python3
"""Checker script for CPQ Product Catalog Setup skill.

Validates Salesforce CPQ product catalog metadata exported as XML or JSON from
a Salesforce org. Checks for common configuration issues in product bundles,
product options, product rules, and configuration attributes.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_product_catalog_setup.py [--help]
    python3 check_cpq_product_catalog_setup.py --manifest-dir path/to/metadata
    python3 check_cpq_product_catalog_setup.py --manifest-dir . --verbose
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce CPQ product catalog configuration for common issues. "
            "Scans metadata directory for CPQ product rule, product option, and "
            "configuration attribute records exported as JSON or XML."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata export (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational messages in addition to warnings.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json_records(path: Path) -> list[dict]:
    """Load a list of records from a JSON file (handles top-level list or {records: [...]} wrapper)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("records", "data", "results"):
                if key in data and isinstance(data[key], list):
                    return data[key]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def _find_json_files(manifest_dir: Path, pattern: str) -> list[Path]:
    return sorted(manifest_dir.rglob(pattern))


# ---------------------------------------------------------------------------
# Check: Product Rules must have unique, non-zero sequence numbers
# ---------------------------------------------------------------------------

def check_product_rule_sequences(manifest_dir: Path, verbose: bool) -> list[str]:
    """Detect duplicate or missing sequence numbers on SBQQ__ProductRule__c records."""
    issues: list[str] = []
    rules_files = _find_json_files(manifest_dir, "*ProductRule*.json")
    if not rules_files and verbose:
        print("INFO: No SBQQ__ProductRule__c JSON files found — skipping sequence check.")
        return issues

    seen_sequences: dict[str, list[str]] = {}
    rules_without_sequence: list[str] = []

    for path in rules_files:
        records = _load_json_records(path)
        for record in records:
            name = record.get("Name") or record.get("SBQQ__ProductRule__c") or "<unnamed>"
            seq = record.get("SBQQ__Sequence__c")
            if seq is None:
                rules_without_sequence.append(name)
            else:
                seq_str = str(seq)
                seen_sequences.setdefault(seq_str, []).append(name)

    for name in rules_without_sequence:
        issues.append(
            f"Product Rule '{name}' has no SBQQ__Sequence__c value. "
            "Rules without a sequence number have undefined evaluation order."
        )

    for seq, names in seen_sequences.items():
        if len(names) > 1:
            issues.append(
                f"Duplicate SBQQ__Sequence__c value '{seq}' found on Product Rules: "
                f"{', '.join(names)}. Duplicate sequences produce undefined evaluation order."
            )

    return issues


# ---------------------------------------------------------------------------
# Check: Product Options must have Required or Selected set explicitly
# ---------------------------------------------------------------------------

def check_product_option_fields(manifest_dir: Path, verbose: bool) -> list[str]:
    """Detect Product Options missing key configuration fields."""
    issues: list[str] = []
    option_files = _find_json_files(manifest_dir, "*ProductOption*.json")
    if not option_files and verbose:
        print("INFO: No SBQQ__ProductOption__c JSON files found — skipping option field check.")
        return issues

    for path in option_files:
        records = _load_json_records(path)
        for record in records:
            name = record.get("Name") or "<unnamed>"
            sku = record.get("SBQQ__OptionalSKU__c") or record.get("SBQQ__OptionalSKU__r", {}).get("Name", "<unknown>")

            # Required flag missing
            if "SBQQ__Required__c" not in record:
                issues.append(
                    f"Product Option '{name}' (SKU: {sku}) is missing SBQQ__Required__c. "
                    "Defaulting to false — confirm this is intentional."
                )

            # No feature assigned
            if not record.get("SBQQ__Feature__c") and not record.get("SBQQ__Feature__r"):
                issues.append(
                    f"Product Option '{name}' (SKU: {sku}) has no Feature assigned. "
                    "Unfeaturized options appear in the configurator without grouping, "
                    "which degrades rep UX for bundles with more than a few options."
                )

            # Check min/max consistency
            min_qty = record.get("SBQQ__MinQuantity__c")
            max_qty = record.get("SBQQ__MaxQuantity__c")
            if min_qty is not None and max_qty is not None:
                try:
                    if float(min_qty) > float(max_qty):
                        issues.append(
                            f"Product Option '{name}' (SKU: {sku}) has MinQuantity ({min_qty}) "
                            f"greater than MaxQuantity ({max_qty}). This configuration will "
                            "prevent the configurator from saving."
                        )
                except (ValueError, TypeError):
                    pass

    return issues


# ---------------------------------------------------------------------------
# Check: Configuration Attributes must be scoped to a bundle product
# ---------------------------------------------------------------------------

def check_configuration_attributes(manifest_dir: Path, verbose: bool) -> list[str]:
    """Detect Configuration Attributes missing a bundle product scope."""
    issues: list[str] = []
    attr_files = _find_json_files(manifest_dir, "*ConfigurationAttribute*.json")
    if not attr_files and verbose:
        print("INFO: No SBQQ__ConfigurationAttribute__c JSON files found — skipping attribute check.")
        return issues

    for path in attr_files:
        records = _load_json_records(path)
        for record in records:
            name = record.get("Name") or "<unnamed>"
            configured_sku = record.get("SBQQ__ConfiguredSKU__c") or record.get("SBQQ__ConfiguredSKU__r")
            if not configured_sku:
                issues.append(
                    f"Configuration Attribute '{name}' is missing SBQQ__ConfiguredSKU__c. "
                    "Configuration Attributes must be scoped to a specific bundle product — "
                    "an unscoped attribute will not appear in the configurator."
                )

            column = record.get("SBQQ__Column__c")
            if not column:
                issues.append(
                    f"Configuration Attribute '{name}' is missing SBQQ__Column__c (the mapped field). "
                    "Without a mapped field, the attribute cannot drive Product Rule conditions."
                )

    return issues


# ---------------------------------------------------------------------------
# Check: Product Rules must have at least one Condition record
# ---------------------------------------------------------------------------

def check_product_rule_conditions(manifest_dir: Path, verbose: bool) -> list[str]:
    """Detect Product Rules that have no associated Condition (ErrorCondition) records."""
    issues: list[str] = []
    condition_files = _find_json_files(manifest_dir, "*ErrorCondition*.json")
    rule_files = _find_json_files(manifest_dir, "*ProductRule*.json")

    if not rule_files:
        return issues

    # Collect rule IDs that have at least one condition
    rule_ids_with_conditions: set[str] = set()
    for path in condition_files:
        records = _load_json_records(path)
        for record in records:
            rule_id = record.get("SBQQ__Rule__c")
            if rule_id:
                rule_ids_with_conditions.add(rule_id)

    for path in rule_files:
        records = _load_json_records(path)
        for record in records:
            rule_id = record.get("Id") or record.get("id")
            rule_name = record.get("Name") or "<unnamed>"
            # Only warn if we have condition files to compare against (avoid false positives
            # when the export does not include ErrorCondition records at all)
            if condition_files and rule_id and rule_id not in rule_ids_with_conditions:
                issues.append(
                    f"Product Rule '{rule_name}' (Id: {rule_id}) has no associated "
                    "SBQQ__ErrorCondition__c records. A rule without conditions will never fire."
                )

    return issues


# ---------------------------------------------------------------------------
# Check: Nesting depth heuristic from ProductOption types
# ---------------------------------------------------------------------------

def check_bundle_nesting_depth(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn if Product Options of type 'Bundle' are detected — flags potential deep nesting."""
    issues: list[str] = []
    option_files = _find_json_files(manifest_dir, "*ProductOption*.json")
    if not option_files:
        return issues

    nested_bundle_options: list[str] = []
    for path in option_files:
        records = _load_json_records(path)
        for record in records:
            if record.get("SBQQ__Type__c") == "Bundle":
                name = record.get("Name") or "<unnamed>"
                nested_bundle_options.append(name)

    if nested_bundle_options:
        issues.append(
            f"Found {len(nested_bundle_options)} Product Option(s) with Type='Bundle', indicating "
            f"nested bundle structure: {', '.join(nested_bundle_options[:5])}{'...' if len(nested_bundle_options) > 5 else ''}. "
            "Verify nesting depth is 2 levels or fewer. Deep nesting (3–4 levels) significantly "
            "increases CPQ configurator load time."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_cpq_catalog(manifest_dir: Path, verbose: bool) -> list[str]:
    """Run all CPQ product catalog checks and return a combined list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    checks = [
        ("Product Rule Sequences", check_product_rule_sequences),
        ("Product Option Fields", check_product_option_fields),
        ("Configuration Attributes", check_configuration_attributes),
        ("Product Rule Conditions", check_product_rule_conditions),
        ("Bundle Nesting Depth", check_bundle_nesting_depth),
    ]

    for check_name, check_fn in checks:
        if verbose:
            print(f"Running check: {check_name}...")
        found = check_fn(manifest_dir, verbose)
        issues.extend(found)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cpq_catalog(manifest_dir, args.verbose)

    if not issues:
        print("No CPQ product catalog issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
