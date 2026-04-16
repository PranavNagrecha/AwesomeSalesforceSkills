#!/usr/bin/env python3
"""Checker script for Gift History Import skill.

Validates a gift migration plan or staging CSV for common NPSP BDI import issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_gift_history_import.py --staging-csv <path/to/DataImport_staging.csv>
    python3 check_gift_history_import.py --manifest-dir <path>

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

import argparse
import csv
import sys
from pathlib import Path


# Required columns for a valid NPSP DataImport__c staging CSV (subset of key fields)
REQUIRED_COLUMNS = [
    "npsp__Contact1_Firstname__c",
    "npsp__Contact1_Lastname__c",
    "npsp__Donation_Amount__c",
    "npsp__Donation_Date__c",
]

# Columns that signal GAU allocation intent
GAU_AMOUNT_COLS = [f"npsp__GAU_Allocation_{i}_Amount__c" for i in range(1, 6)]
GAU_PERCENT_COLS = [f"npsp__GAU_Allocation_{i}_Percent__c" for i in range(1, 6)]
GAU_NAME_COLS = [f"npsp__GAU_Allocation_{i}_GAU__c" for i in range(1, 6)]

# Forbidden: direct Opportunity-level columns that indicate bypassing BDI
DIRECT_OPP_COLUMNS = ["StageName", "OwnerId", "AccountId"]


def check_staging_csv(csv_path: Path) -> list[str]:
    """Validate DataImport__c staging CSV for common BDI import issues."""
    issues = []

    if not csv_path.exists():
        return [f"ERROR: Staging CSV not found: {csv_path}"]

    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            headers = reader.fieldnames or []
    except Exception as exc:
        return [f"ERROR: Could not read CSV: {exc}"]

    # Check for direct Opportunity columns (signals bypassing BDI)
    direct_cols_found = [c for c in DIRECT_OPP_COLUMNS if c in headers]
    if direct_cols_found:
        issues.append(
            f"ERROR: CSV appears to be formatted for direct Opportunity insert, not DataImport__c staging. "
            f"Found Opportunity-only columns: {direct_cols_found}. "
            f"NPSP gift imports must use npsp__DataImport__c, not Opportunity directly."
        )

    # Check required staging columns
    missing = [c for c in REQUIRED_COLUMNS if c not in headers]
    if missing:
        issues.append(
            f"WARN: Staging CSV is missing recommended DataImport__c columns: {missing}. "
            f"Contact matching and gift amount/date are required for BDI processing."
        )

    # Check for mixed GAU amount vs percent in the same row
    for i, row in enumerate(rows, start=2):
        has_amount = any(row.get(c, "").strip() for c in GAU_AMOUNT_COLS)
        has_percent = any(row.get(c, "").strip() for c in GAU_PERCENT_COLS)
        if has_amount and has_percent:
            issues.append(
                f"WARN: Row {i} mixes GAU allocation amounts and percentages. "
                f"BDI does not support mixed split types in the same row. "
                f"Standardize to amount-only or percent-only per row."
            )

    # Check GAU name present when GAU amount/percent specified
    for i, row in enumerate(rows, start=2):
        for idx in range(1, 6):
            amt = row.get(f"npsp__GAU_Allocation_{idx}_Amount__c", "").strip()
            pct = row.get(f"npsp__GAU_Allocation_{idx}_Percent__c", "").strip()
            name = row.get(f"npsp__GAU_Allocation_{idx}_GAU__c", "").strip()
            if (amt or pct) and not name:
                issues.append(
                    f"WARN: Row {i} has GAU Allocation {idx} amount/percent set but no GAU name. "
                    f"BDI requires the GAU record name or ID to create the allocation."
                )
                break  # one warning per row is sufficient

    # Volume check
    if len(rows) > 50000:
        issues.append(
            f"ERROR: CSV contains {len(rows)} rows, exceeding the BDI limit of 50,000 per batch. "
            f"Split into chunks of ≤50,000 rows and process each chunk separately."
        )

    if not issues:
        print(f"OK: {csv_path.name} — {len(rows)} rows look structurally valid for BDI staging.")

    return issues


def check_manifest_for_direct_opp_inserts(manifest_dir: Path) -> list[str]:
    """Scan data plan or deploy scripts for direct Opportunity inserts that bypass BDI."""
    issues = []
    for apex_file in list(manifest_dir.glob("**/*.cls")) + list(manifest_dir.glob("**/*.trigger")):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "insert opp" in content.lower() or "Database.insert(opp" in content:
            if "DataImport" not in content and "BDI" not in content:
                issues.append(
                    f"WARN: {apex_file.name} inserts Opportunity records without referencing "
                    f"DataImport__c or BDI. For NPSP gift creation, use BDI batch via DataImport__c "
                    f"or the NPSP API (npe01.OpportunityContactRoles, npsp.BDI_DataImport) to "
                    f"ensure OCRs and payment records are created."
                )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate NPSP gift history import plan.")
    parser.add_argument("--staging-csv", type=Path, help="DataImport__c staging CSV to validate")
    parser.add_argument("--manifest-dir", type=Path, default=None,
                        help="Metadata directory to scan for direct Opportunity inserts")
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.staging_csv:
        all_issues.extend(check_staging_csv(args.staging_csv))

    if args.manifest_dir and args.manifest_dir.exists():
        all_issues.extend(check_manifest_for_direct_opp_inserts(args.manifest_dir))

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    if not args.staging_csv and not args.manifest_dir:
        print("INFO: No input provided. Use --staging-csv or --manifest-dir.")
        return 0

    print("OK: No gift import issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
