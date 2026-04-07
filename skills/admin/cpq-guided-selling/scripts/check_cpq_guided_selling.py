#!/usr/bin/env python3
"""Checker script for CPQ Guided Selling skill.

Validates Salesforce CPQ Guided Selling configuration metadata for common issues:
  - Quote Process records with SBQQ__GuidedProductSelection__c != true
  - ProcessInput records with SBQQ__SearchField__c pointing to a custom field (ending in __c)
    that does NOT have a matching API-name field on SBQQ__ProcessInput__c in the metadata
  - ProcessInput records missing SBQQ__SearchField__c entirely
  - ProcessInput records with SBQQ__Order__c values that are duplicated within a Quote Process
  - Product2 records with null/empty values on fields referenced by ProcessInput SearchField

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_guided_selling.py [--help]
    python3 check_cpq_guided_selling.py --manifest-dir path/to/metadata
    python3 check_cpq_guided_selling.py --csv-dir path/to/exported/csv/files

The checker works in two modes:
  1. Metadata XML mode (--manifest-dir): Scans Salesforce DX or MDAPI metadata files
     for CPQ custom object records exported as XML.
  2. CSV mode (--csv-dir): Scans CSV exports of CPQ objects (e.g., from Data Loader).
     Expected files: QuoteProcess.csv, ProcessInput.csv, Product2.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce CPQ Guided Selling configuration for common issues. "
            "Scans metadata XML or CSV exports for missing mirror fields, missing "
            "GuidedProductSelection flag, duplicate ProcessInput order values, "
            "and products with null classification field values."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata (MDAPI or SFDX format).",
    )
    parser.add_argument(
        "--csv-dir",
        default=None,
        help="Directory containing CSV exports: QuoteProcess.csv, ProcessInput.csv, Product2.csv",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# XML metadata helpers
# ---------------------------------------------------------------------------

def load_xml_records(metadata_dir: Path, object_name: str) -> list[dict]:
    """Load custom object records from MDAPI-style XML under metadata_dir."""
    records: list[dict] = []
    search_patterns = [
        f"**/{object_name}/*.xml",
        f"**/{object_name}/**/*.xml",
    ]
    found_files: list[Path] = []
    for pattern in search_patterns:
        found_files.extend(metadata_dir.glob(pattern))

    for xml_file in found_files:
        try:
            tree = ElementTree.parse(xml_file)
            root = tree.getroot()
            record: dict = {"_file": str(xml_file)}
            for child in root:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                record[tag] = (child.text or "").strip()
            records.append(record)
        except ElementTree.ParseError:
            pass  # skip malformed files
    return records


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def load_csv(csv_path: Path) -> list[dict]:
    """Load a CSV file and return list of row dicts. Returns empty list if file missing."""
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def collect_field_api_names_from_csv(process_inputs: list[dict]) -> set[str]:
    """
    Collect all column names present in the ProcessInput CSV export.
    These represent actual fields on SBQQ__ProcessInput__c in the org.
    """
    if not process_inputs:
        return set()
    # DictReader keys from the first row represent the org's field API names
    return set(process_inputs[0].keys())


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_quote_process_guided_selection_flag(quote_processes: list[dict]) -> list[str]:
    """Detect Quote Process records where GuidedProductSelection is not true."""
    issues: list[str] = []
    for qp in quote_processes:
        flag = qp.get(
            "SBQQ__GuidedProductSelection__c",
            qp.get("GuidedProductSelection", ""),
        )
        name = qp.get("Name", qp.get("_file", "unknown"))
        if str(flag).lower() not in ("true", "1"):
            issues.append(
                f"GUIDED SELECTION DISABLED: Quote Process '{name}' has "
                f"SBQQ__GuidedProductSelection__c = '{flag}' (must be true). "
                f"The guided selling wizard will not launch for quotes using this process."
            )
    return issues


def check_process_inputs_missing_search_field(process_inputs: list[dict]) -> list[str]:
    """Detect ProcessInput records with no SBQQ__SearchField__c value."""
    issues: list[str] = []
    for pi in process_inputs:
        active = pi.get("SBQQ__Active__c", pi.get("Active", "true"))
        if str(active).lower() in ("false", "0"):
            continue
        search_field = pi.get("SBQQ__SearchField__c", pi.get("SearchField", "")).strip()
        name = pi.get("Name", pi.get("_file", "unknown"))
        if not search_field:
            issues.append(
                f"MISSING SEARCH FIELD: ProcessInput '{name}' has no SBQQ__SearchField__c value. "
                f"This question will not filter any products — all products will pass this input."
            )
    return issues


def check_mirror_fields_for_custom_search_fields(
    process_inputs: list[dict],
    process_input_field_names: set[str],
) -> list[str]:
    """
    Detect ProcessInput records whose SBQQ__SearchField__c references a custom field
    (ending in __c) that does not appear in the known field set for SBQQ__ProcessInput__c.

    Note: This check requires knowledge of what fields exist on SBQQ__ProcessInput__c.
    In CSV mode, the CSV column headers represent actual org fields.
    In XML mode, we can only check against fields found in the exported records.
    If process_input_field_names is empty, this check is skipped.
    """
    issues: list[str] = []
    if not process_input_field_names:
        return issues

    for pi in process_inputs:
        active = pi.get("SBQQ__Active__c", pi.get("Active", "true"))
        if str(active).lower() in ("false", "0"):
            continue
        search_field = pi.get("SBQQ__SearchField__c", pi.get("SearchField", "")).strip()
        name = pi.get("Name", pi.get("_file", "unknown"))

        # Only check custom fields (standard fields like 'Family' don't need mirror fields)
        if not search_field or not search_field.endswith("__c"):
            continue

        if search_field not in process_input_field_names:
            issues.append(
                f"MISSING MIRROR FIELD: ProcessInput '{name}' has "
                f"SBQQ__SearchField__c = '{search_field}', but this custom field does not "
                f"appear to exist on SBQQ__ProcessInput__c. "
                f"Without this mirror field, CPQ cannot store the rep's answer at runtime "
                f"and this question will silently return all products. "
                f"Create a field named '{search_field}' on SBQQ__ProcessInput__c with a "
                f"compatible data type."
            )
    return issues


def check_duplicate_process_input_order(process_inputs: list[dict]) -> list[str]:
    """Detect active ProcessInput records within the same Quote Process sharing the same order value."""
    issues: list[str] = []
    # Group by parent Quote Process
    process_map: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for pi in process_inputs:
        active = pi.get("SBQQ__Active__c", pi.get("Active", "true"))
        if str(active).lower() in ("false", "0"):
            continue
        parent = pi.get("SBQQ__QuoteProcess__c", pi.get("QuoteProcess", "unknown"))
        order = pi.get("SBQQ__Order__c", pi.get("Order", ""))
        name = pi.get("Name", pi.get("_file", "unknown"))
        if order:
            process_map[parent].append((order, name))

    for parent, entries in process_map.items():
        order_to_names: dict[str, list[str]] = defaultdict(list)
        for order, name in entries:
            order_to_names[order].append(name)
        for order, names in order_to_names.items():
            if len(names) > 1:
                issues.append(
                    f"DUPLICATE ORDER VALUE {order} on Quote Process '{parent}': "
                    f"ProcessInput records {names} share the same order. "
                    f"Display sequence is undefined. Assign unique SBQQ__Order__c values."
                )
    return issues


def check_product2_null_classification_fields(
    products: list[dict],
    search_fields: set[str],
) -> list[str]:
    """
    Detect Product2 records with null values on fields used as ProcessInput SearchField targets.
    Products with null values will never appear in guided selling results when equals operator is used.
    """
    issues: list[str] = []
    if not search_fields or not products:
        return issues

    for product in products:
        pid = product.get("Id", product.get("_file", "unknown"))
        name = product.get("Name", pid)
        for field in search_fields:
            value = product.get(field, "").strip()
            if not value:
                issues.append(
                    f"NULL CLASSIFICATION FIELD: Product '{name}' has no value for '{field}'. "
                    f"This product will be excluded from guided selling results when the "
                    f"'{field}' question uses the 'equals' operator. "
                    f"Populate this field or use a non-equals operator for optional matching."
                )
    return issues


# ---------------------------------------------------------------------------
# Collect all custom search field API names from active ProcessInputs
# ---------------------------------------------------------------------------

def collect_active_search_fields(process_inputs: list[dict]) -> set[str]:
    """Return the set of SBQQ__SearchField__c values from active ProcessInput records."""
    fields: set[str] = set()
    for pi in process_inputs:
        active = pi.get("SBQQ__Active__c", pi.get("Active", "true"))
        if str(active).lower() in ("false", "0"):
            continue
        search_field = pi.get("SBQQ__SearchField__c", pi.get("SearchField", "")).strip()
        if search_field:
            fields.add(search_field)
    return fields


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_checks_from_csv(csv_dir: Path) -> list[str]:
    """Run all checks using CSV exports from csv_dir."""
    issues: list[str] = []

    quote_processes = load_csv(csv_dir / "QuoteProcess.csv")
    process_inputs = load_csv(csv_dir / "ProcessInput.csv")
    products = load_csv(csv_dir / "Product2.csv")

    if not any([quote_processes, process_inputs]):
        issues.append(
            f"No CPQ Guided Selling CSV files found in '{csv_dir}'. "
            f"Expected: QuoteProcess.csv, ProcessInput.csv, and optionally Product2.csv"
        )
        return issues

    # In CSV mode, column headers of ProcessInput.csv represent actual org fields
    process_input_field_names = collect_field_api_names_from_csv(process_inputs)

    if quote_processes:
        issues.extend(check_quote_process_guided_selection_flag(quote_processes))

    if process_inputs:
        issues.extend(check_process_inputs_missing_search_field(process_inputs))
        issues.extend(
            check_mirror_fields_for_custom_search_fields(
                process_inputs, process_input_field_names
            )
        )
        issues.extend(check_duplicate_process_input_order(process_inputs))

    if products:
        active_search_fields = collect_active_search_fields(process_inputs)
        issues.extend(
            check_product2_null_classification_fields(products, active_search_fields)
        )

    return issues


def run_checks_from_metadata(manifest_dir: Path) -> list[str]:
    """Run checks against MDAPI/SFDX metadata XML in manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    quote_processes = load_xml_records(manifest_dir, "SBQQ__QuoteProcess__c")
    process_inputs = load_xml_records(manifest_dir, "SBQQ__ProcessInput__c")
    products = load_xml_records(manifest_dir, "Product2")

    if not any([quote_processes, process_inputs]):
        issues.append(
            "No CPQ Guided Selling metadata found in manifest directory. "
            "Ensure metadata is exported with SBQQ__QuoteProcess__c and "
            "SBQQ__ProcessInput__c object types included, or use --csv-dir with "
            "Data Loader CSV exports."
        )
        return issues

    # In XML mode, collect all field names seen across all ProcessInput records
    # This is an approximation — use CSV mode for reliable mirror field checking
    process_input_field_names: set[str] = set()
    for pi in process_inputs:
        process_input_field_names.update(pi.keys())

    if quote_processes:
        issues.extend(check_quote_process_guided_selection_flag(quote_processes))

    if process_inputs:
        issues.extend(check_process_inputs_missing_search_field(process_inputs))
        issues.extend(
            check_mirror_fields_for_custom_search_fields(
                process_inputs, process_input_field_names
            )
        )
        issues.extend(check_duplicate_process_input_order(process_inputs))

    if products:
        active_search_fields = collect_active_search_fields(process_inputs)
        issues.extend(
            check_product2_null_classification_fields(products, active_search_fields)
        )

    return issues


def main() -> int:
    args = parse_args()

    if args.csv_dir:
        issues = run_checks_from_csv(Path(args.csv_dir))
    elif args.manifest_dir:
        issues = run_checks_from_metadata(Path(args.manifest_dir))
    else:
        # Default: try current directory as manifest
        issues = run_checks_from_metadata(Path("."))

    if not issues:
        print("No CPQ Guided Selling issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
