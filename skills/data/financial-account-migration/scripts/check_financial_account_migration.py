#!/usr/bin/env python3
"""Checker script for Financial Account Migration skill.

Validates a Salesforce metadata export directory for common FSC financial
account migration issues:
  - Insert-order issues inferred from object manifest presence
  - RBL custom setting configuration in CustomSettings metadata
  - FinancialSecurity prerequisite presence

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_financial_account_migration.py [--help]
    python3 check_financial_account_migration.py --manifest-dir path/to/metadata
    python3 check_financial_account_migration.py --csv-dir path/to/load/csvs
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC financial account migration configuration and data files "
            "for common issues: RBL settings, insert-order violations, and "
            "FinancialSecurity prerequisite gaps."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of a Salesforce metadata export (unpackaged/ or force-app/).",
    )
    parser.add_argument(
        "--csv-dir",
        default=None,
        help="Directory containing ETL load CSV files named after their target objects.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Checks: metadata
# ---------------------------------------------------------------------------

def check_rbl_custom_setting(manifest_dir: Path) -> list[str]:
    """Look for WealthAppConfig custom setting metadata and warn if RBL is enabled."""
    issues: list[str] = []

    # Custom settings in metadata are stored as CustomMetadata or CustomSettings
    # The managed-package setting appears as FinServ__WealthAppConfig__c
    # Check common locations: customSettings/, objects/, settings/
    search_patterns = [
        "**/*WealthAppConfig*",
        "**/*wealthappconfig*",
    ]
    found_files: list[Path] = []
    for pattern in search_patterns:
        found_files.extend(manifest_dir.glob(pattern))

    if not found_files:
        issues.append(
            "WealthAppConfig custom setting metadata not found in manifest. "
            "Cannot verify EnableRollupSummary state. "
            "Confirm FinServ__EnableRollupSummary__c is set to false for the ETL user "
            "before loading FinancialHolding or FinancialAccountTransaction records."
        )
        return issues

    for f in found_files:
        content = f.read_text(errors="replace").lower()
        if "enablerollupsummary" in content and "true" in content:
            issues.append(
                f"Potential RBL enabled in {f}: 'EnableRollupSummary' appears set to true. "
                "Disable for the ETL user before bulk loading holdings or transactions "
                "to prevent UNABLE_TO_LOCK_ROW errors."
            )

    return issues


def check_financial_security_objects(manifest_dir: Path) -> list[str]:
    """Check whether FinancialSecurity object metadata is present in the manifest."""
    issues: list[str] = []

    security_patterns = [
        "**/*FinancialSecurity*",
        "**/*FinServ__FinancialSecurity*",
    ]
    found: list[Path] = []
    for pattern in security_patterns:
        found.extend(manifest_dir.glob(pattern))

    if not found:
        issues.append(
            "No FinancialSecurity object metadata found in manifest. "
            "FinancialSecurity records must exist in the target org before loading "
            "FinancialHolding records. Verify that your migration plan includes a "
            "FinancialSecurity pre-load step."
        )

    return issues


# ---------------------------------------------------------------------------
# Checks: CSV load files
# ---------------------------------------------------------------------------

# Correct partial order: each key must be loaded before each value in its list
REQUIRED_ORDER: dict[str, list[str]] = {
    "FinancialSecurity": ["FinancialHolding"],
    "FinancialAccount": ["FinancialAccountRole", "FinancialHolding", "FinancialAccountTransaction"],
    "FinancialAccountRole": ["FinancialHolding", "FinancialAccountTransaction"],
    "FinancialHolding": ["FinancialAccountTransaction"],
    "Account": ["FinancialAccount", "FinancialHolding"],
}

# Normalize filenames to canonical object names
OBJECT_NAME_MAP: dict[str, str] = {
    "financialaccount": "FinancialAccount",
    "financialaccountrole": "FinancialAccountRole",
    "financialholding": "FinancialHolding",
    "financialaccounttransaction": "FinancialAccountTransaction",
    "financialsecurity": "FinancialSecurity",
    "financialaccountbalance": "FinancialAccountBalance",
    "account": "Account",
    # managed-package aliases
    "finserv__financialaccount__c": "FinancialAccount",
    "finserv__financialaccountrole__c": "FinancialAccountRole",
    "finserv__financialholding__c": "FinancialHolding",
    "finserv__financialaccounttransaction__c": "FinancialAccountTransaction",
    "finserv__financialsecurity__c": "FinancialSecurity",
}


def _canonicalize(stem: str) -> str | None:
    """Map a CSV file stem to a canonical object name, or None if unrecognised."""
    normalized = stem.lower().replace("-", "_").replace(" ", "_")
    return OBJECT_NAME_MAP.get(normalized)


def check_csv_insert_order(csv_dir: Path) -> list[str]:
    """Warn if CSV load file naming suggests missing or misordered objects."""
    issues: list[str] = []

    csv_files = sorted(csv_dir.glob("*.csv"))
    if not csv_files:
        issues.append(f"No CSV files found in {csv_dir}. Nothing to validate.")
        return issues

    present_objects: set[str] = set()
    for f in csv_files:
        canonical = _canonicalize(f.stem)
        if canonical:
            present_objects.add(canonical)

    # Check prerequisite coverage
    if "FinancialHolding" in present_objects and "FinancialSecurity" not in present_objects:
        issues.append(
            "CSV directory contains a FinancialHolding load file but no FinancialSecurity "
            "load file. FinancialSecurity records must be loaded before FinancialHolding. "
            "Add a FinancialSecurity CSV or confirm those records already exist in the target org."
        )

    if "FinancialHolding" in present_objects and "FinancialAccount" not in present_objects:
        issues.append(
            "CSV directory contains a FinancialHolding load file but no FinancialAccount "
            "load file. FinancialAccount records must be loaded before FinancialHolding."
        )

    if "FinancialAccountTransaction" in present_objects and "FinancialAccount" not in present_objects:
        issues.append(
            "CSV directory contains a FinancialAccountTransaction load file but no "
            "FinancialAccount load file. FinancialAccount records must be loaded first."
        )

    if "FinancialHolding" in present_objects and "FinancialAccountRole" not in present_objects:
        issues.append(
            "CSV directory contains a FinancialHolding load file but no FinancialAccountRole "
            "load file. Load at minimum the Primary Owner role before FinancialHolding to avoid "
            "household rollup gaps after migration."
        )

    return issues


def check_csv_balance_fields(csv_dir: Path) -> list[str]:
    """Check FinancialAccount CSV for balance field patterns and warn on model mismatch risk."""
    issues: list[str] = []

    fa_csvs = list(csv_dir.glob("*[Ff]inancial[Aa]ccount*.csv"))
    # Filter out role, holding, transaction, balance files
    fa_csvs = [
        f for f in fa_csvs
        if not any(
            x in f.stem.lower()
            for x in ("role", "holding", "transaction", "balance")
        )
    ]

    for fa_csv in fa_csvs:
        try:
            with fa_csv.open(newline="", errors="replace") as fh:
                reader = csv.reader(fh)
                headers = [h.strip() for h in next(reader, [])]
        except (OSError, StopIteration):
            continue

        header_lower = [h.lower() for h in headers]

        # Managed-package balance field present in a file that may target Core FSC
        if "finserv__balance__c" in header_lower:
            issues.append(
                f"{fa_csv.name}: contains 'FinServ__Balance__c' column — this is the "
                "managed-package balance field. If targeting a Core FSC org (API v61.0+), "
                "balance history should be loaded as FinancialAccountBalance child records instead."
            )

        # Check if a Balance column exists without a corresponding FinancialAccountBalance file
        balance_cols = [h for h in header_lower if "balance" in h]
        balance_file_present = bool(list(csv_dir.glob("*[Ff]inancial[Aa]ccount[Bb]alance*.csv")))
        if balance_cols and not balance_file_present:
            issues.append(
                f"{fa_csv.name}: balance column(s) detected ({', '.join(balance_cols)}) "
                "but no FinancialAccountBalance CSV found. "
                "For Core FSC orgs, load FinancialAccountBalance child records to preserve "
                "balance history. For managed-package orgs this is expected behavior."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_financial_account_migration(
    manifest_dir: Path | None,
    csv_dir: Path | None,
) -> list[str]:
    """Return a list of issue strings found across metadata and CSV inputs."""
    issues: list[str] = []

    if manifest_dir is not None:
        if not manifest_dir.exists():
            issues.append(f"Manifest directory not found: {manifest_dir}")
        else:
            issues.extend(check_rbl_custom_setting(manifest_dir))
            issues.extend(check_financial_security_objects(manifest_dir))

    if csv_dir is not None:
        if not csv_dir.exists():
            issues.append(f"CSV directory not found: {csv_dir}")
        else:
            issues.extend(check_csv_insert_order(csv_dir))
            issues.extend(check_csv_balance_fields(csv_dir))

    if manifest_dir is None and csv_dir is None:
        issues.append(
            "No inputs provided. Pass --manifest-dir and/or --csv-dir. "
            "Run with --help for usage."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir) if args.manifest_dir else None
    csv_dir = Path(args.csv_dir) if args.csv_dir else None

    issues = check_financial_account_migration(manifest_dir, csv_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
