#!/usr/bin/env python3
"""Checker script for NPSP API and Integration skill.

Checks Apex metadata for NPSP integration anti-patterns: direct Opportunity/OppPayment
inserts that bypass BDI, correct BDI DataImport usage, and ERD API patterns.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_npsp_api_and_integration.py [--help]
    python3 check_npsp_api_and_integration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check NPSP API and Integration Apex patterns for common anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files_recursive(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def check_direct_opportunity_insert(manifest_dir: Path, issues: list[str]) -> None:
    """Check for direct Opportunity insert in Apex files (anti-pattern — should use BDI)."""
    apex_files = find_files_recursive(manifest_dir, "*.cls")

    # Patterns that suggest direct DML on Opportunity without BDI
    # Match: insert new Opportunity(...), insert opp, insert opps, Database.insert(opp...)
    direct_insert_pattern = re.compile(
        r"\binsert\s+(?:new\s+)?Opportunity\b"
        r"|\binsert\s+\w*[Oo]pp(?:ortunity)?\b"
        r"|\bDatabase\.insert\s*\(\s*\w*[Oo]pp(?:ortunity)?\b",
        re.MULTILINE,
    )
    # BDI marker — if the file also references DataImport, it's probably fine (it may be BDI itself)
    bdi_pattern = re.compile(r"npsp__DataImport__c|BDI_DataImport|DataImport__c", re.IGNORECASE)
    # Exclude NPSP package classes (managed package files)
    npsp_class_pattern = re.compile(r"//\s*@npsp|namespace\s+npsp", re.IGNORECASE)

    flagged: list[str] = []
    for apex_file in apex_files:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        # Skip files that are part of the BDI framework itself or test utilities
        if bdi_pattern.search(content):
            continue
        if npsp_class_pattern.search(content):
            continue
        if direct_insert_pattern.search(content):
            # Check if this looks like gift-related context
            gift_context = re.search(
                r"gift|donation|donor|payment|contribution|pledge",
                content,
                re.IGNORECASE,
            )
            if gift_context:
                flagged.append(apex_file.name)

    if flagged:
        issues.append(
            f"Apex class(es) {flagged} contain direct Opportunity insert(s) in what appears to be "
            "a gift processing context. Direct Opportunity inserts bypass the NPSP BDI pipeline, "
            "silently skipping: GAU allocations, soft credit (Opportunity Contact Role) creation, "
            "household Account rollup recalculation (npo02__ CRLP), and Salesforce Elevate payment linkage. "
            "All gift integrations must route through npsp__DataImport__c staging records and invoke "
            "BDI_DataImport_API.processDataImportRecords()."
        )
    else:
        if apex_files:
            print("  OK: No direct gift-context Opportunity inserts detected in Apex files.")


def check_bdi_data_import_usage(manifest_dir: Path, issues: list[str]) -> None:
    """Check for npsp__DataImport__c references in Apex (correct BDI pattern)."""
    apex_files = find_files_recursive(manifest_dir, "*.cls")

    bdi_staging_pattern = re.compile(r"npsp__DataImport__c", re.IGNORECASE)
    bdi_api_pattern = re.compile(r"BDI_DataImport_API|BDI_DataImport_BATCH", re.IGNORECASE)

    has_staging = False
    has_api_call = False
    staging_without_api: list[str] = []

    for apex_file in apex_files:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        file_has_staging = bool(bdi_staging_pattern.search(content))
        file_has_api = bool(bdi_api_pattern.search(content))

        if file_has_staging:
            has_staging = True
        if file_has_api:
            has_api_call = True

        # Flag files that create DataImport records but never call the API
        if file_has_staging and not file_has_api:
            # Check if this looks like it inserts DataImport records (not just queries them)
            if re.search(r"\binsert\s+\w*[Dd]ata[Ii]mport\b|\binsert\s+new\s+npsp__DataImport__c", content):
                staging_without_api.append(apex_file.name)

    if has_staging:
        print("  OK: npsp__DataImport__c references found — BDI staging pattern in use.")
    else:
        # Only warn about missing BDI if there are Apex files to check
        if apex_files:
            issues.append(
                "No npsp__DataImport__c references found in Apex files. "
                "If this codebase includes gift processing integration logic, all gift data must be "
                "routed through npsp__DataImport__c staging records before BDI processing. "
                "Confirm that gift integrations use the BDI DataImport staging pattern and not "
                "direct Opportunity DML."
            )

    if staging_without_api:
        issues.append(
            f"Apex class(es) {staging_without_api} insert npsp__DataImport__c records but do not call "
            "BDI_DataImport_API.processDataImportRecords(). "
            "DataImport staging records that are inserted without invoking BDI processing will sit "
            "unprocessed in the org until the nightly BDI batch runs (or never, if batch is not scheduled). "
            "Call BDI_DataImport_API.processDataImportRecords() explicitly, or confirm the NPSP "
            "Data Import batch is scheduled to run at an acceptable frequency."
        )
    elif has_staging and has_api_call:
        print("  OK: BDI API invocation (BDI_DataImport_API) found alongside DataImport staging.")


def check_erd_recurring_donation_references(manifest_dir: Path, issues: list[str]) -> None:
    """Check for npe03__Recurring_Donation__c references (ERD API)."""
    apex_files = find_files_recursive(manifest_dir, "*.cls")

    erd_pattern = re.compile(
        r"npe03__Recurring_Donation__c|RD2_ApiService|npe03__.*Recurring|Recurring_Donation",
        re.IGNORECASE,
    )
    installment_schedule_pattern = re.compile(
        r"RD2_ApiService\.getInstallments|RD2_ApiService\.getSchedules",
        re.IGNORECASE,
    )

    has_erd_refs = False
    uses_rd2_api = False

    for apex_file in apex_files:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        if erd_pattern.search(content):
            has_erd_refs = True
        if installment_schedule_pattern.search(content):
            uses_rd2_api = True

    if has_erd_refs:
        print("  OK: npe03__Recurring_Donation__c / ERD references found in Apex.")
        if uses_rd2_api:
            print("  OK: RD2_ApiService (Schedules or Installments API) in use.")
    else:
        # Only an issue if the manifest has NPSP signals
        all_files = find_files_recursive(manifest_dir, "*.cls") + find_files_recursive(manifest_dir, "*.object-meta.xml")
        all_content = " ".join(f.read_text(encoding="utf-8", errors="replace") for f in all_files[:50])
        if "npsp__" in all_content or "npe01__" in all_content:
            # NPSP present but no ERD references — informational only
            print(
                "  INFO: NPSP namespace detected but no npe03__Recurring_Donation__c or RD2_ApiService "
                "references found. If recurring donation integration is in scope, use RD2_ApiService "
                "for schedule and installment retrieval."
            )


def check_direct_opp_payment_insert(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if any Apex does a direct DML insert into npe01__OppPayment__c (bypasses payment processing)."""
    apex_files = find_files_recursive(manifest_dir, "*.cls")

    # Match direct insert into OppPayment
    opp_payment_insert_pattern = re.compile(
        r"\binsert\s+(?:new\s+)?npe01__OppPayment__c\b"
        r"|\binsert\s+\w*[Pp]ayment\b"
        r"|\bDatabase\.insert\s*\(\s*\w*[Pp]ayment\b",
        re.MULTILINE,
    )
    # Exclude files that are clearly BDI or payment processing framework themselves
    bdi_or_framework = re.compile(
        r"class\s+BDI_|class\s+PMT_|class\s+npe01__",
        re.IGNORECASE,
    )

    flagged: list[str] = []
    for apex_file in apex_files:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        if bdi_or_framework.search(content):
            continue
        if opp_payment_insert_pattern.search(content):
            # Check for npe01__OppPayment__c to confirm NPSP context
            if "npe01__OppPayment__c" in content or "OppPayment" in content:
                flagged.append(apex_file.name)

    if flagged:
        issues.append(
            f"Apex class(es) {flagged} appear to perform direct DML insert into npe01__OppPayment__c. "
            "Direct inserts into OppPayment__c bypass NPSP's payment processing logic, which manages "
            "payment scheduling, payment status transitions, and Salesforce Elevate payment ID linkage. "
            "Payment records should be created by NPSP automatically when an Opportunity is processed "
            "through BDI or through NPSP's npe01 trigger framework. "
            "If a payment record must be created programmatically, use the BDI DataImport "
            "npsp__Payment_Method__c field and route through BDI_DataImport_API instead."
        )
    else:
        if apex_files:
            print("  OK: No direct npe01__OppPayment__c insert patterns detected.")


def check_npsp_api_and_integration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    print(f"Checking NPSP API and Integration in: {manifest_dir.resolve()}")

    check_direct_opportunity_insert(manifest_dir, issues)
    check_bdi_data_import_usage(manifest_dir, issues)
    check_erd_recurring_donation_references(manifest_dir, issues)
    check_direct_opp_payment_insert(manifest_dir, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_npsp_api_and_integration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:", file=sys.stderr)
    for issue in issues:
        print(f"\nWARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
