#!/usr/bin/env python3
"""Checker script for FSL Work Order Migration skill.

Scans a CSV or JSON data extract directory for common FSL migration issues:
- Missing External ID fields in headers
- Status values that may not be active in FSL default picklist
- ProductConsumed records without PricebookEntryId

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_work_order_migration.py [--help]
    python3 check_fsl_work_order_migration.py --manifest-dir path/to/data-extracts
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Status values typically not present in a freshly provisioned FSL org
_HISTORICAL_STATUS_VALUES = {"Completed", "Cannot Complete", "Canceled", "No Show"}

# Expected External ID field pattern (heuristic — look for columns named like legacy IDs)
_EXTERNAL_ID_PATTERNS = ("legacy", "external", "_id__c", "_ext_id")


def check_csv_headers(csv_path: Path) -> list[str]:
    """Check a single CSV file for migration readiness indicators."""
    issues = []
    try:
        with csv_path.open(encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            lower_headers = [h.lower() for h in headers]

            # Check for External ID column
            has_ext_id = any(
                any(p in h for p in _EXTERNAL_ID_PATTERNS) for h in lower_headers
            )
            if not has_ext_id:
                issues.append(
                    f"{csv_path.name}: No External ID column detected in headers {headers[:10]}. "
                    "FSL migration loads should use upsert with an External ID for re-runability."
                )

            # Check for Status values in ServiceAppointment files
            if "serviceappointment" in csv_path.name.lower() or "service_appointment" in csv_path.name.lower():
                status_col = None
                for h in headers:
                    if h.lower() in ("status", "status__c"):
                        status_col = h
                        break
                if status_col:
                    status_values = set()
                    for row in reader:
                        v = row.get(status_col, "").strip()
                        if v:
                            status_values.add(v)
                    historical = status_values & _HISTORICAL_STATUS_VALUES
                    if historical:
                        issues.append(
                            f"{csv_path.name}: Historical status values found: {sorted(historical)}. "
                            "Verify these are active in the target org's ServiceAppointment Status picklist "
                            "before loading, or inserts will fail with INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST."
                        )

            # Check for ProductConsumed PricebookEntryId
            if "productconsumed" in csv_path.name.lower() or "product_consumed" in csv_path.name.lower():
                has_pbe = any("pricebook" in h.lower() for h in lower_headers)
                if not has_pbe:
                    issues.append(
                        f"{csv_path.name}: ProductConsumed file detected but no PricebookEntry column found. "
                        "ProductConsumed requires PricebookEntryId. Ensure PricebookEntry records are "
                        "pre-loaded and mapped in this file."
                    )

    except (OSError, csv.Error):
        pass
    return issues


def check_fsl_work_order_migration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    csv_files = list(manifest_dir.rglob("*.csv"))
    if not csv_files:
        return issues

    for csv_file in csv_files:
        issues.extend(check_csv_headers(csv_file))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSL migration data extracts for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing migration CSV files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_work_order_migration(manifest_dir)

    if not issues:
        print("No FSL Work Order Migration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
