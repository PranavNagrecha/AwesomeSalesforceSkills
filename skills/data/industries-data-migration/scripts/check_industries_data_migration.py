#!/usr/bin/env python3
"""Checker script for Industries Data Migration skill.

Validates a migration load plan CSV or directory of CSVs against common
Industries data migration anti-patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_data_migration.py --help
    python3 check_industries_data_migration.py --plan-csv migration_plan.csv
    python3 check_industries_data_migration.py --load-dir path/to/load_files/
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Object hierarchy definitions
# ---------------------------------------------------------------------------

INSURANCE_LOAD_ORDER = [
    "account",
    "personaccount",
    "insurancepolicy",
    "insurancepolicyparticipant",
    "insurancepolicyasset",
    "insurancepolicycoverage",
    "insurancepolicytransaction",
    "billingstatement",
]

EU_LOAD_ORDER = [
    "account",
    "premise",
    "servicepoint",
    "serviceaccount",
]

# Objects that must have their own external ID field (not just Account)
REQUIRES_OWN_EXTERNAL_ID = {
    "insurancepolicy",
    "insurancepolicyasset",
    "insurancepolicycoverage",
    "insurancepolicytransaction",
    "billingstatement",
    "premise",
    "servicepoint",
    "serviceaccount",
}

# Known parent relationships: child -> required parent (object name, lowercase)
PARENT_REQUIREMENTS: dict[str, list[str]] = {
    "insurancepolicy": ["account"],
    "insurancepolicyparticipant": ["insurancepolicy"],
    "insurancepolicyasset": ["insurancepolicy"],
    "insurancepolicycoverage": ["insurancepolicy"],
    "insurancepolicytransaction": ["insurancepolicy"],
    "billingstatement": ["insurancepolicy"],
    "premise": ["account"],
    "servicepoint": ["premise"],
    "serviceaccount": ["account", "servicepoint"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check an Industries data migration plan for common anti-patterns "
            "including incorrect load order, missing external ID fields, and "
            "missing parent references."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--plan-csv",
        metavar="PATH",
        help=(
            "Path to a migration plan CSV with columns: "
            "'tier' (integer), 'object' (Salesforce API name), "
            "'external_id_field' (optional), 'parent_ref_field' (optional)."
        ),
    )
    group.add_argument(
        "--load-dir",
        metavar="PATH",
        help=(
            "Directory containing CSV load files. File names must start with the "
            "Salesforce object API name (e.g. 'InsurancePolicy_load.csv'). "
            "The checker inspects column headers for external ID fields."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Check: load order
# ---------------------------------------------------------------------------

def check_load_order(objects_in_order: list[str]) -> list[str]:
    """Verify that no child object appears before its required parent."""
    issues: list[str] = []
    seen: set[str] = set()

    for obj in objects_in_order:
        obj_lower = obj.lower()
        parents = PARENT_REQUIREMENTS.get(obj_lower, [])
        for parent in parents:
            if parent not in seen:
                issues.append(
                    f"Load order violation: '{obj}' appears before its required parent "
                    f"'{parent}'. '{parent}' must be loaded and confirmed before '{obj}'."
                )
        seen.add(obj_lower)

    return issues


# ---------------------------------------------------------------------------
# Check: external ID field coverage
# ---------------------------------------------------------------------------

def check_external_id_coverage(
    objects_in_scope: list[str],
    external_id_fields: dict[str, str],
) -> list[str]:
    """Warn if any intermediate object lacks its own external ID field."""
    issues: list[str] = []

    for obj in objects_in_scope:
        obj_lower = obj.lower()
        if obj_lower in REQUIRES_OWN_EXTERNAL_ID:
            field = external_id_fields.get(obj_lower, "").strip()
            if not field:
                issues.append(
                    f"Missing external ID field: '{obj}' is an intermediate object that "
                    f"must have its own external ID field (not just Account). "
                    f"Create a custom Text field with 'External ID' checked on {obj}."
                )

    return issues


# ---------------------------------------------------------------------------
# Check: parent reference fields in load files
# ---------------------------------------------------------------------------

def check_load_file_columns(load_dir: Path) -> list[str]:
    """
    Inspect CSV load file headers and warn about common column anti-patterns.
    Only checks headers — does not read data rows (avoids large file reads).
    """
    issues: list[str] = []

    csv_files = list(load_dir.glob("*.csv"))
    if not csv_files:
        issues.append(f"No CSV files found in load directory: {load_dir}")
        return issues

    for csv_path in csv_files:
        obj_name = csv_path.name.split("_")[0].lower()

        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                try:
                    headers = [h.lower().strip() for h in next(reader)]
                except StopIteration:
                    issues.append(f"{csv_path.name}: file is empty or has no header row.")
                    continue
        except OSError as e:
            issues.append(f"{csv_path.name}: cannot read file — {e}")
            continue

        # Check for anti-pattern: using AccountId external ID as parent ref
        # for objects that do not directly reference Account
        indirect_account_children = {
            "insurancepolicycoverage",
            "insurancepolicytransaction",
            "billingstatement",
            "servicepoint",
        }
        if obj_name in indirect_account_children:
            account_ref_columns = [h for h in headers if "account" in h and "external" in h]
            if account_ref_columns:
                issues.append(
                    f"{csv_path.name} ({obj_name}): column(s) {account_ref_columns} suggest "
                    f"Account external ID is used as a parent reference. "
                    f"'{obj_name}' does not reference Account directly — "
                    f"use the intermediate parent's external ID field instead."
                )

        # Check that objects requiring own external ID have one in their header
        if obj_name in REQUIRES_OWN_EXTERNAL_ID:
            has_external_id_col = any(
                "external_id" in h or "ext_id" in h or h.endswith("__c") and "external" in h
                for h in headers
            )
            if not has_external_id_col:
                issues.append(
                    f"{csv_path.name} ({obj_name}): no external ID column detected in headers. "
                    f"Add the object's own external ID field (e.g. Policy_External_ID__c) "
                    f"to make the load re-runnable via upsert."
                )

    return issues


# ---------------------------------------------------------------------------
# Check: plan CSV
# ---------------------------------------------------------------------------

def check_plan_csv(plan_path: Path) -> list[str]:
    """Parse and check a migration plan CSV file."""
    issues: list[str] = []

    if not plan_path.exists():
        return [f"Migration plan file not found: {plan_path}"]

    rows: list[dict[str, str]] = []
    try:
        with open(plan_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return [f"{plan_path.name}: file is empty or missing headers."]
            required_cols = {"tier", "object"}
            missing = required_cols - {c.lower() for c in reader.fieldnames}
            if missing:
                return [
                    f"{plan_path.name}: missing required columns: {missing}. "
                    f"Expected columns: tier, object, external_id_field (optional), "
                    f"parent_ref_field (optional)."
                ]
            rows = list(reader)
    except OSError as e:
        return [f"{plan_path.name}: cannot read file — {e}"]

    if not rows:
        return [f"{plan_path.name}: plan file has no data rows."]

    # Sort by tier and extract object order
    try:
        rows_sorted = sorted(rows, key=lambda r: int(r.get("tier", "0")))
    except ValueError:
        issues.append(f"{plan_path.name}: 'tier' column contains non-integer values.")
        rows_sorted = rows

    objects_in_order = [r.get("object", "").strip() for r in rows_sorted if r.get("object")]
    external_id_fields = {
        r.get("object", "").lower().strip(): r.get("external_id_field", "").strip()
        for r in rows_sorted
        if r.get("object")
    }

    issues.extend(check_load_order(objects_in_order))
    issues.extend(check_external_id_coverage(objects_in_order, external_id_fields))

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.plan_csv:
        plan_path = Path(args.plan_csv)
        issues = check_plan_csv(plan_path)

    elif args.load_dir:
        load_dir = Path(args.load_dir)
        if not load_dir.exists():
            print(f"WARN: Load directory not found: {load_dir}", file=sys.stderr)
            return 1
        issues = check_load_file_columns(load_dir)

    else:
        print(
            "No input provided. Use --plan-csv or --load-dir. Run with --help for usage.",
            file=sys.stderr,
        )
        return 1

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
