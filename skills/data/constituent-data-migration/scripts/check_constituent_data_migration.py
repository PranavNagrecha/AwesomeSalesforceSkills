#!/usr/bin/env python3
"""Checker script for Constituent Data Migration skill.

Validates a CSV file intended for NPSP constituent migration by checking
for common structural errors before the file is loaded into npsp__DataImport__c.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_constituent_data_migration.py --csv path/to/staging.csv
    python3 check_constituent_data_migration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Required Contact1 fields for every row in a staging CSV
REQUIRED_CONTACT1_FIELDS = [
    "npsp__Contact1_Firstname__c",
    "npsp__Contact1_Lastname__c",
]

# Fields that indicate the practitioner is trying to target Contact directly
# instead of the NPSP staging object — a critical anti-pattern
DIRECT_CONTACT_FIELD_INDICATORS = [
    "FirstName",
    "LastName",
    "MailingStreet",
    "MailingCity",
    "MailingState",
    "MailingPostalCode",
]

# Expected NPSP staging field prefixes
NPSP_STAGING_FIELD_PREFIXES = [
    "npsp__Contact1",
    "npsp__Contact2",
    "npsp__HH_",
    "npsp__Donation",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a constituent migration CSV for NPSP Data Import staging issues. "
            "Validates field naming, required fields, and household pairing rules."
        ),
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Path to the staging CSV file to validate (npsp__DataImport__c format).",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce metadata (scans for CSV files if --csv not provided).",
    )
    return parser.parse_args()


def check_csv_structure(csv_path: Path) -> list[str]:
    """Validate the structure and content of an npsp__DataImport__c staging CSV."""
    issues: list[str] = []

    if not csv_path.exists():
        issues.append(f"CSV file not found: {csv_path}")
        return issues

    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames or []
            rows = list(reader)
    except Exception as exc:
        issues.append(f"Could not read CSV file {csv_path}: {exc}")
        return issues

    if not headers:
        issues.append(f"{csv_path}: CSV has no headers.")
        return issues

    # Check 1: Detect direct Contact field names (anti-pattern: targeting Contact sObject)
    direct_contact_headers = [h for h in headers if h in DIRECT_CONTACT_FIELD_INDICATORS]
    if direct_contact_headers:
        issues.append(
            f"{csv_path}: Detected standard Contact field names {direct_contact_headers}. "
            "This CSV appears to target the Contact sObject directly. "
            "NPSP constituent migration MUST use npsp__DataImport__c staging fields "
            "(e.g., npsp__Contact1_Firstname__c). "
            "Loading directly to Contact bypasses NPSP triggers and corrupts the Household Account model."
        )

    # Check 2: Confirm NPSP staging fields are present
    has_npsp_fields = any(
        any(h.startswith(prefix) for prefix in NPSP_STAGING_FIELD_PREFIXES)
        for h in headers
    )
    if not has_npsp_fields and not direct_contact_headers:
        issues.append(
            f"{csv_path}: No NPSP staging field prefixes detected "
            f"(expected fields starting with {NPSP_STAGING_FIELD_PREFIXES}). "
            "Confirm this CSV is mapped to npsp__DataImport__c fields."
        )

    # Check 3: Required Contact1 fields must be present as headers
    for required_field in REQUIRED_CONTACT1_FIELDS:
        if required_field not in headers:
            issues.append(
                f"{csv_path}: Missing required header '{required_field}'. "
                "Every npsp__DataImport__c staging row requires Contact1 first and last name."
            )

    # Check 4: Per-row validation
    contact2_fields = [h for h in headers if h.startswith("npsp__Contact2")]
    for i, row in enumerate(rows, start=2):  # start=2: row 1 is header
        # Check 4a: Contact1 first and last name must not be blank
        c1_first = row.get("npsp__Contact1_Firstname__c", "").strip()
        c1_last = row.get("npsp__Contact1_Lastname__c", "").strip()

        if not c1_first or not c1_last:
            # Check if Contact2 data is present on this row
            has_c2_data = any(
                row.get(f, "").strip() for f in contact2_fields
            )
            if has_c2_data:
                issues.append(
                    f"{csv_path} row {i}: Contact2 fields are populated but "
                    "Contact1 first/last name is blank. "
                    "NPSP will skip this row entirely — Contact2 will not be imported. "
                    "Ensure Contact1 fields are always populated when using household pairs."
                )
            elif not c1_first or not c1_last:
                issues.append(
                    f"{csv_path} row {i}: Contact1 first name or last name is blank. "
                    "NPSP requires both fields to process the row."
                )

    return issues


def check_manifest_for_csvs(manifest_dir: Path) -> list[str]:
    """Scan a metadata directory for any CSV files and validate them."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    csv_files = list(manifest_dir.rglob("*.csv"))
    if not csv_files:
        issues.append(
            f"No CSV files found in {manifest_dir}. "
            "If you are validating a staging CSV, use --csv path/to/file.csv."
        )
        return issues

    for csv_file in csv_files:
        issues.extend(check_csv_structure(csv_file))

    return issues


def main() -> int:
    args = parse_args()

    issues: list[str] = []

    if args.csv:
        issues = check_csv_structure(Path(args.csv))
    elif args.manifest_dir:
        issues = check_manifest_for_csvs(Path(args.manifest_dir))
    else:
        # No arguments — print usage guidance
        print(
            "constituent-data-migration checker\n"
            "\nUsage:\n"
            "  python3 check_constituent_data_migration.py --csv path/to/staging.csv\n"
            "  python3 check_constituent_data_migration.py --manifest-dir path/to/metadata\n"
            "\nThis checker validates NPSP constituent migration staging CSVs for:\n"
            "  - Direct Contact field names (anti-pattern: must use npsp__DataImport__c fields)\n"
            "  - Missing required Contact1 fields\n"
            "  - Rows where Contact2 is populated but Contact1 is blank (silent skip risk)\n"
        )
        return 0

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
