#!/usr/bin/env python3
"""Checker script for Soft Credits and Matching Gifts (NPSP) skill.

Checks Salesforce metadata exports or SOQL query result CSV files for common
misconfiguration patterns in NPSP soft credit and matching gift setup.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_soft_credits_and_matching.py [--help]
    python3 check_soft_credits_and_matching.py --manifest-dir path/to/metadata
    python3 check_soft_credits_and_matching.py --manifest-dir . --ocr-csv ocr_export.csv --psc-csv psc_export.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check NPSP soft credit and matching gift configuration for common issues.\n"
            "Accepts optional CSV exports of OpportunityContactRole and "
            "npsp__Partial_Soft_Credit__c records."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--ocr-csv",
        default=None,
        help=(
            "Path to a CSV export of OpportunityContactRole records. "
            "Expected columns: Id, OpportunityId, ContactId, Role, IsPrimary."
        ),
    )
    parser.add_argument(
        "--psc-csv",
        default=None,
        help=(
            "Path to a CSV export of npsp__Partial_Soft_Credit__c records. "
            "Expected columns: Id, npsp__Opportunity__c, npsp__Contact__c, "
            "npsp__Amount__c, npsp__Contact_Role_ID__c."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a CSV file and return a list of row dicts. Returns [] on error."""
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# Checks against OCR CSV
# ---------------------------------------------------------------------------

KNOWN_SOFT_CREDIT_ROLES = {
    "Soft Credit",
    "Household Member",
    "Matched Donor",
    "Influencer",
    "Solicitor",
}


def check_duplicate_ocrs(rows: list[dict[str, str]]) -> list[str]:
    """Detect duplicate (OpportunityId, ContactId, Role) combinations."""
    issues: list[str] = []
    key_counter: Counter = Counter()
    for row in rows:
        opp = row.get("OpportunityId", "").strip()
        contact = row.get("ContactId", "").strip()
        role = row.get("Role", "").strip()
        if opp and contact and role and role in KNOWN_SOFT_CREDIT_ROLES:
            key_counter[(opp, contact, role)] += 1

    for (opp, contact, role), count in key_counter.items():
        if count > 1:
            issues.append(
                f"Duplicate OCR detected: OpportunityId={opp}, ContactId={contact}, "
                f"Role='{role}' appears {count} times. "
                "This inflates soft credit rollup totals — remove duplicate records."
            )
    return issues


def check_matched_donor_duplicates(rows: list[dict[str, str]]) -> list[str]:
    """Flag more than one 'Matched Donor' OCR for the same contact on the same opportunity.
    This is the known Find Matched Gifts duplicate-record platform bug.
    """
    issues: list[str] = []
    matched_donor_rows = [
        r for r in rows if r.get("Role", "").strip() == "Matched Donor"
    ]
    key_counter: Counter = Counter()
    for row in matched_donor_rows:
        opp = row.get("OpportunityId", "").strip()
        contact = row.get("ContactId", "").strip()
        if opp and contact:
            key_counter[(opp, contact)] += 1

    for (opp, contact), count in key_counter.items():
        if count > 1:
            issues.append(
                f"[KNOWN BUG] Duplicate 'Matched Donor' OCR: OpportunityId={opp}, "
                f"ContactId={contact} has {count} Matched Donor OCRs. "
                "Likely caused by running Find Matched Gifts multiple times. "
                "Delete duplicate OCRs and corresponding Partial_Soft_Credit__c records, "
                "then retrigger rollup recalculation."
            )
    return issues


# ---------------------------------------------------------------------------
# Checks against Partial_Soft_Credit__c CSV
# ---------------------------------------------------------------------------

def check_psc_missing_ocr_id(rows: list[dict[str, str]]) -> list[str]:
    """Detect Partial_Soft_Credit__c records with null npsp__Contact_Role_ID__c.
    These records are silently ignored by NPSP rollup calculations.
    """
    issues: list[str] = []
    for row in rows:
        psc_id = row.get("Id", "?").strip()
        ocr_id = row.get("npsp__Contact_Role_ID__c", "").strip()
        if not ocr_id:
            opp = row.get("npsp__Opportunity__c", "?").strip()
            contact = row.get("npsp__Contact__c", "?").strip()
            amount = row.get("npsp__Amount__c", "?").strip()
            issues.append(
                f"Partial_Soft_Credit__c Id={psc_id} (Opp={opp}, Contact={contact}, "
                f"Amount={amount}) is missing npsp__Contact_Role_ID__c. "
                "NPSP will ignore this record during rollup calculations and use the "
                "full opportunity amount instead. Populate npsp__Contact_Role_ID__c "
                "with the corresponding OCR record Id."
            )
    return issues


def check_psc_zero_amount(rows: list[dict[str, str]]) -> list[str]:
    """Flag Partial_Soft_Credit__c records with $0 or negative amounts."""
    issues: list[str] = []
    for row in rows:
        psc_id = row.get("Id", "?").strip()
        amount_str = row.get("npsp__Amount__c", "").strip()
        if amount_str:
            try:
                amount = float(amount_str)
                if amount <= 0:
                    issues.append(
                        f"Partial_Soft_Credit__c Id={psc_id} has Amount={amount_str}. "
                        "Zero or negative partial credit amounts produce incorrect rollup totals. "
                        "Verify the intended amount and correct or delete this record."
                    )
            except ValueError:
                pass  # non-numeric amount — skip
    return issues


# ---------------------------------------------------------------------------
# Metadata directory checks
# ---------------------------------------------------------------------------

def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Light structural checks on a Salesforce metadata directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for presence of NPSP custom object metadata if this is a full project
    npsp_objects_dir = manifest_dir / "objects"
    if npsp_objects_dir.exists():
        npsp_markers = [
            "npsp__Partial_Soft_Credit__c.object-meta.xml",
        ]
        for marker in npsp_markers:
            marker_path = npsp_objects_dir / marker
            if not marker_path.exists():
                # Not necessarily an error — just informational
                issues.append(
                    f"INFO: {marker} not found under {npsp_objects_dir}. "
                    "If this org uses NPSP soft credits, confirm the NPSP managed package "
                    "is installed and the object metadata is included in the project."
                )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_all_checks(
    manifest_dir: Path,
    ocr_csv: Path | None,
    psc_csv: Path | None,
) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    # Manifest directory checks
    issues.extend(check_manifest_dir(manifest_dir))

    # OCR CSV checks
    if ocr_csv is not None:
        ocr_rows = _read_csv(ocr_csv)
        if not ocr_rows:
            issues.append(
                f"OCR CSV not found or empty: {ocr_csv}. "
                "Skipping OCR-based checks."
            )
        else:
            issues.extend(check_duplicate_ocrs(ocr_rows))
            issues.extend(check_matched_donor_duplicates(ocr_rows))

    # Partial_Soft_Credit__c CSV checks
    if psc_csv is not None:
        psc_rows = _read_csv(psc_csv)
        if not psc_rows:
            issues.append(
                f"Partial_Soft_Credit__c CSV not found or empty: {psc_csv}. "
                "Skipping PSC-based checks."
            )
        else:
            issues.extend(check_psc_missing_ocr_id(psc_rows))
            issues.extend(check_psc_zero_amount(psc_rows))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    ocr_csv = Path(args.ocr_csv) if args.ocr_csv else None
    psc_csv = Path(args.psc_csv) if args.psc_csv else None

    issues = run_all_checks(manifest_dir, ocr_csv, psc_csv)

    info_issues = [i for i in issues if i.startswith("INFO:")]
    warn_issues = [i for i in issues if not i.startswith("INFO:")]

    for issue in info_issues:
        print(issue)

    if not warn_issues:
        print("No issues found.")
        return 0

    for issue in warn_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
