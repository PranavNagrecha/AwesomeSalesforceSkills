#!/usr/bin/env python3
"""Checker script for Billing Schedule Setup skill.

Inspects a Salesforce metadata directory for common Salesforce Billing
(blng__ namespace) configuration issues. Uses stdlib only — no pip dependencies.

Checks performed:
  1. Detects custom fields or objects with 'RevenueSchedule' names in
     non-blng namespaces (likely conflation with native revenue schedules).
  2. Warns if flows reference blng__BillingSchedule__c DML create operations
     (manually creating billing schedule records is unsupported).
  3. Detects flows or process builders that write blng__BillingPolicy__c
     only to Order records without also writing to Account records.
  4. Scans Apex classes for direct blng__BillingSchedule__c insert statements.
  5. Checks for InvoiceRun records or flow steps that set TargetDate to a
     relative date formula that would produce yesterday rather than today.

Usage:
    python3 check_billing_schedule_setup.py [--help]
    python3 check_billing_schedule_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Salesforce Billing "
            "(blng__ namespace) billing schedule configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_native_revenue_schedule_confusion(manifest_dir: Path) -> list[str]:
    """Detect custom fields or objects named with 'RevenueSchedule' that are
    not in the blng__ namespace — these suggest conflation with native Salesforce
    revenue schedule functionality, which does not integrate with Billing."""
    issues: list[str] = []
    # Look for CustomField and CustomObject metadata files
    patterns = ["**/*.field-meta.xml", "**/*.object-meta.xml", "**/*.flow-meta.xml"]
    suspect_pattern = re.compile(
        r"(?i)revenue.?schedule",
        re.IGNORECASE,
    )
    blng_pattern = re.compile(r"blng__", re.IGNORECASE)

    for glob_pattern in patterns:
        for path in manifest_dir.rglob(glob_pattern.lstrip("**/")):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(content.splitlines(), start=1):
                if suspect_pattern.search(line) and not blng_pattern.search(line):
                    # Exclude lines that are comments or XML declarations
                    stripped = line.strip()
                    if stripped.startswith("<!--") or stripped.startswith("<?"):
                        continue
                    issues.append(
                        f"{path.relative_to(manifest_dir)}:{lineno} — "
                        f"Reference to 'RevenueSchedule' without blng__ namespace. "
                        f"Verify this is not conflating native OpportunityLineItem "
                        f"revenue schedules with blng__RevenueSchedule__c. "
                        f"Line: {stripped[:120]}"
                    )
    return issues


def check_billing_schedule_dml_in_apex(manifest_dir: Path) -> list[str]:
    """Detect Apex classes that directly insert blng__BillingSchedule__c records.
    Billing schedule records must be created by the Order activation trigger,
    not by direct DML — Invoice Runs will silently skip manually created records."""
    issues: list[str] = []
    apex_dir = manifest_dir
    insert_pattern = re.compile(
        r"\binsert\b[^;]*blng__BillingSchedule__c",
        re.IGNORECASE | re.DOTALL,
    )
    for path in apex_dir.rglob("*.cls"):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if insert_pattern.search(content):
            issues.append(
                f"{path.relative_to(manifest_dir)} — "
                f"Apex class appears to insert blng__BillingSchedule__c records directly. "
                f"Billing schedule records must be auto-created by the Order activation "
                f"trigger (managed package). Manually inserted records are skipped by "
                f"Invoice Runs. Consider reactivating the Order instead."
            )
    return issues


def check_flow_billing_schedule_create(manifest_dir: Path) -> list[str]:
    """Detect Flow metadata that creates (not updates) blng__BillingSchedule__c records.
    Flows creating these records bypass the managed package trigger and produce
    invoice-ineligible records."""
    issues: list[str] = []
    # Flow metadata is XML; look for recordCreate elements referencing the object
    create_pattern = re.compile(
        r"<object>blng__BillingSchedule__c</object>",
        re.IGNORECASE,
    )
    record_create_block = re.compile(
        r"<recordCreates>.*?blng__BillingSchedule__c.*?</recordCreates>",
        re.IGNORECASE | re.DOTALL,
    )
    for path in manifest_dir.rglob("*.flow-meta.xml"):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if record_create_block.search(content) or (
            create_pattern.search(content)
            and "<recordCreates>" in content
        ):
            issues.append(
                f"{path.relative_to(manifest_dir)} — "
                f"Flow appears to create blng__BillingSchedule__c records. "
                f"Billing schedule records must be created by the Order activation "
                f"trigger (managed package). Flow-created records are silently skipped "
                f"by Invoice Runs."
            )
    return issues


def check_billing_policy_on_order_only(manifest_dir: Path) -> list[str]:
    """Detect flows or triggers that write blng__BillingPolicy__c to Order records
    without evidence of also writing it to Account records. The Invoice Run engine
    reads Billing Policy from Account, not from Order."""
    issues: list[str] = []
    order_billing_policy_pattern = re.compile(
        r"blng__BillingPolicy__c.*?Order|Order.*?blng__BillingPolicy__c",
        re.IGNORECASE | re.DOTALL,
    )
    account_billing_policy_pattern = re.compile(
        r"blng__BillingPolicy__c.*?Account|Account.*?blng__BillingPolicy__c",
        re.IGNORECASE | re.DOTALL,
    )
    for path in list(manifest_dir.rglob("*.flow-meta.xml")) + list(manifest_dir.rglob("*.cls")):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if order_billing_policy_pattern.search(content) and not account_billing_policy_pattern.search(content):
            issues.append(
                f"{path.relative_to(manifest_dir)} — "
                f"File references blng__BillingPolicy__c on Order but not on Account. "
                f"The Invoice Run engine reads Billing Policy from Account.blng__BillingPolicy__c. "
                f"Verify that Account is also updated, or this will produce zero invoices."
            )
    return issues


def check_apex_invoice_run_target_date(manifest_dir: Path) -> list[str]:
    """Detect Apex patterns that set blng__TargetDate__c to Date.today() - 1
    (yesterday), which excludes same-day billing schedule items from Invoice Runs."""
    issues: list[str] = []
    yesterday_pattern = re.compile(
        r"blng__TargetDate__c\s*=\s*Date\.today\(\)\s*-\s*1",
        re.IGNORECASE,
    )
    for path in manifest_dir.rglob("*.cls"):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            if yesterday_pattern.search(line):
                issues.append(
                    f"{path.relative_to(manifest_dir)}:{lineno} — "
                    f"blng__TargetDate__c is set to Date.today() - 1 (yesterday). "
                    f"Invoice Runs use TargetDate as a hard cutoff: items scheduled "
                    f"for today will be excluded. Use Date.today() to include today's items."
                )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_billing_schedule_setup(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_native_revenue_schedule_confusion(manifest_dir))
    issues.extend(check_billing_schedule_dml_in_apex(manifest_dir))
    issues.extend(check_flow_billing_schedule_create(manifest_dir))
    issues.extend(check_billing_policy_on_order_only(manifest_dir))
    issues.extend(check_apex_invoice_run_target_date(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_billing_schedule_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
