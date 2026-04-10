#!/usr/bin/env python3
"""Checker script for Revenue Recognition Requirements skill.

Inspects a Salesforce metadata directory for common Salesforce Billing (blng__ namespace)
revenue recognition configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_revenue_recognition_requirements.py [--help]
    python3 check_revenue_recognition_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_files(manifest_dir: Path, *glob_patterns: str):
    """Yield (path, text) for all files matching the given glob patterns."""
    for pattern in glob_patterns:
        for path in manifest_dir.rglob(pattern.lstrip("**/")):
            try:
                yield path, path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_native_revenue_schedule_confusion(manifest_dir: Path) -> list[str]:
    """Detect references to standard OpportunityLineItemSchedule in Billing contexts.

    The standard Salesforce Revenue Schedules feature (OpportunityLineItemSchedule)
    is completely separate from blng__RevenueSchedule__c. Apex or Flow that
    queries OpportunityLineItemSchedule in a Salesforce Billing org for revenue
    recognition purposes is almost certainly an anti-pattern.
    """
    issues: list[str] = []
    patterns = ["**/*.cls", "**/*.trigger", "**/*.flow-meta.xml", "**/*.js"]
    opportunitylineschedule_pattern = re.compile(
        r"OpportunityLineItemSchedule", re.IGNORECASE
    )
    billing_context_pattern = re.compile(
        r"blng__|RevenueRecognition|FinancePeriod|RevenueSchedule", re.IGNORECASE
    )

    for path, text in _iter_files(manifest_dir, *patterns):
        if opportunitylineschedule_pattern.search(text) and billing_context_pattern.search(text):
            issues.append(
                f"{path}: References OpportunityLineItemSchedule alongside blng__ objects. "
                "Standard Salesforce Revenue Schedules (OpportunityLineItemSchedule) are "
                "unrelated to blng__RevenueSchedule__c. Do not use them together for "
                "ASC 606 revenue recognition in a Salesforce Billing org."
            )

    return issues


def check_revenue_transaction_direct_edits(manifest_dir: Path) -> list[str]:
    """Detect Apex or Flow that directly updates blng__RevenueTransaction__c fields.

    Revenue Transaction records are system-managed GL events. Direct field updates
    via DML or Flow bypass engine consistency checks and corrupt GL integrity.
    """
    issues: list[str] = []
    patterns = ["**/*.cls", "**/*.trigger", "**/*.flow-meta.xml"]

    # Pattern: DML update on RevenueTransaction OR field assignment on __c
    update_pattern = re.compile(
        r"update\s+\w*[Rr]evenue[Tt]ransaction|"
        r"blng__RevenueTransaction__c\s*\.\s*blng__Amount__c\s*=|"
        r"blng__RevenueTransaction__c\s*\.\s*blng__FinancePeriod__c\s*=",
        re.IGNORECASE,
    )

    for path, text in _iter_files(manifest_dir, *patterns):
        if update_pattern.search(text):
            issues.append(
                f"{path}: Detected potential direct update to blng__RevenueTransaction__c. "
                "Revenue Transaction records are system-managed. Direct edits corrupt GL "
                "integrity. Fix the root cause (wrong rule, wrong Finance Period, wrong SSP) "
                "and re-trigger schedule generation instead."
            )

    return issues


def check_revenue_schedule_direct_edits(manifest_dir: Path) -> list[str]:
    """Detect Apex or Flow that directly updates blng__RevenueSchedule__c amounts.

    Revenue Schedule records are system-managed. Direct amount edits produce
    inconsistencies between the schedule total and its child transaction records.
    """
    issues: list[str] = []
    patterns = ["**/*.cls", "**/*.trigger", "**/*.flow-meta.xml"]

    amount_write_pattern = re.compile(
        r"blng__RevenueSchedule__c\s*\.\s*blng__TotalAmount__c\s*=|"
        r"blng__RevenueSchedule__c\s*\.\s*blng__RecognizedAmount__c\s*=",
        re.IGNORECASE,
    )

    for path, text in _iter_files(manifest_dir, *patterns):
        if amount_write_pattern.search(text):
            issues.append(
                f"{path}: Detected potential direct write to blng__RevenueSchedule__c amount "
                "fields (blng__TotalAmount__c or blng__RecognizedAmount__c). These are "
                "system-managed fields. Direct writes corrupt GL reconciliation. Close the "
                "schedule and re-generate it through the Salesforce Billing process instead."
            )

    return issues


def check_revenue_recognition_rule_on_wrong_object(manifest_dir: Path) -> list[str]:
    """Detect Revenue Recognition Rule being set on Order or OrderProduct instead of Product2.

    blng__RevenueRecognitionRule__c must be set on Product2. Setting it on Order
    or OrderProduct records does not drive revenue schedule generation.
    """
    issues: list[str] = []
    patterns = ["**/*.cls", "**/*.trigger", "**/*.flow-meta.xml"]

    # Look for assignment of RevenueRecognitionRule on an Order or OrderProduct variable
    wrong_object_pattern = re.compile(
        r"(Order|OrderProduct|blng__Order__c|OrderItem)\s*\.\s*blng__RevenueRecognitionRule__c\s*=",
        re.IGNORECASE,
    )

    for path, text in _iter_files(manifest_dir, *patterns):
        if wrong_object_pattern.search(text):
            issues.append(
                f"{path}: Detected blng__RevenueRecognitionRule__c being set on an Order or "
                "OrderProduct record. This field must be configured on Product2 — the Billing "
                "engine reads the rule from Product2 at Order activation time. Setting it on "
                "Order or OrderProduct has no effect on revenue schedule generation."
            )

    return issues


def check_missing_finance_period_guard(manifest_dir: Path) -> list[str]:
    """Detect Order activation patterns that lack a Finance Period pre-check.

    Activating an Order without verifying Finance Periods causes silent schedule
    generation failure. Automation that sets Order Status = Activated should
    query blng__FinancePeriod__c first.
    """
    issues: list[str] = []
    patterns = ["**/*.cls", "**/*.trigger", "**/*.flow-meta.xml"]

    activate_pattern = re.compile(
        r"Status\s*=\s*['\"]Activated['\"]|blng__Status__c\s*=\s*['\"]Activated['\"]",
        re.IGNORECASE,
    )
    finance_period_check = re.compile(
        r"blng__FinancePeriod__c",
        re.IGNORECASE,
    )

    for path, text in _iter_files(manifest_dir, *patterns):
        if activate_pattern.search(text) and not finance_period_check.search(text):
            issues.append(
                f"{path}: Found Order activation (Status = Activated) without a "
                "blng__FinancePeriod__c query. If this automation activates Orders in a "
                "revenue-recognition-enabled Billing org, missing Finance Periods will cause "
                "blng__RevenueSchedule__c to silently not generate. Add a Finance Period "
                "existence check before activating."
            )

    return issues


def check_equal_distribution_on_subscription_products(manifest_dir: Path) -> list[str]:
    """Detect Revenue Recognition Rules using Equal Distribution in a subscription context.

    Equal Distribution splits revenue evenly across Finance Periods regardless of period
    length. For subscriptions with variable start/end dates, this mis-states revenue
    in partial months. Daily Proration is the ASC 606-correct default.
    """
    issues: list[str] = []
    patterns = ["**/*.cls", "**/*.trigger", "**/*.xml"]

    equal_distribution_pattern = re.compile(
        r"blng__DistributionMethod__c\s*=\s*['\"]Equal Distribution['\"]",
        re.IGNORECASE,
    )
    subscription_context = re.compile(
        r"subscription|Recurring|blng__RecognitionTreatment__c\s*=\s*['\"]Rateable['\"]",
        re.IGNORECASE,
    )

    for path, text in _iter_files(manifest_dir, *patterns):
        if equal_distribution_pattern.search(text) and subscription_context.search(text):
            issues.append(
                f"{path}: Detected Equal Distribution method in a subscription or Rateable "
                "recognition context. Equal Distribution does not prorate partial months. "
                "For ASC 606-compliant subscription revenue, use Daily Proration to correctly "
                "handle service periods that start or end mid-month."
            )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path) -> list[str]:
    """Run all checks and aggregate results."""
    all_issues: list[str] = []

    checks = [
        check_native_revenue_schedule_confusion,
        check_revenue_transaction_direct_edits,
        check_revenue_schedule_direct_edits,
        check_revenue_recognition_rule_on_wrong_object,
        check_missing_finance_period_guard,
        check_equal_distribution_on_subscription_products,
    ]

    for check_fn in checks:
        all_issues.extend(check_fn(manifest_dir))

    return all_issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Salesforce Billing revenue recognition "
            "configuration issues (blng__ namespace). "
            "Uses stdlib only — no pip dependencies."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    issues = run_all_checks(manifest_dir)

    if not issues:
        print("No revenue recognition issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
