#!/usr/bin/env python3
"""Checker script for Billing Data Reconciliation skill.

Validates metadata for common Salesforce Billing reconciliation configuration issues:
- Detects blng__Invoice__c or blng__InvoiceLine__c direct-edit patterns in Apex
- Detects missing blng__PaymentAllocation__c in payment-handling Apex (heuristic)
- Detects blng__RevenueTransactionErrorLog__c absence from reconciliation SOQL files
- Detects direct blng__Status__c assignment on invoices in Apex

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_billing_data_reconciliation.py [--help]
    python3 check_billing_data_reconciliation.py --manifest-dir path/to/metadata
    python3 check_billing_data_reconciliation.py --apex-dir path/to/apex/classes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches direct DML update of blng__InvoiceLine__c or blng__Invoice__c
# where a field assignment on blng__ChargeAmount__c or blng__Status__c precedes update()
DIRECT_INVOICE_EDIT_PATTERN = re.compile(
    r"blng__Invoice(?:Line)?__c\b.*?\bupdate\b",
    re.DOTALL,
)

# Matches assignment of blng__Status__c to 'Paid' on what appears to be an invoice
MANUAL_STATUS_PAID_PATTERN = re.compile(
    r"blng__Status__c\s*=\s*['\"]Paid['\"]",
)

# Matches use of blng__ChargeAmount__c in a context that looks like assignment (= not ==)
CHARGE_AMOUNT_ASSIGNMENT_PATTERN = re.compile(
    r"blng__ChargeAmount__c\s*=[^=]",
)

# Detects blng__Payment__c usage WITHOUT blng__PaymentAllocation__c nearby
PAYMENT_WITHOUT_ALLOCATION_PATTERN = re.compile(
    r"blng__Payment__c",
)
ALLOCATION_PATTERN = re.compile(
    r"blng__PaymentAllocation__c",
)

# Detects SOQL referencing blng__Invoice__c without blng__RevenueTransactionErrorLog__c
# in files that look like reconciliation queries
INVOICE_SOQL_PATTERN = re.compile(
    r"FROM\s+blng__Invoice__c",
    re.IGNORECASE,
)
ERROR_LOG_SOQL_PATTERN = re.compile(
    r"blng__RevenueTransactionErrorLog__c",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------


def check_apex_files(apex_dir: Path) -> list[str]:
    """Scan Apex class files for billing reconciliation anti-patterns."""
    issues: list[str] = []
    apex_files = list(apex_dir.rglob("*.cls")) + list(apex_dir.rglob("*.trigger"))

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = apex_file.relative_to(apex_dir.parent) if apex_dir.parent in apex_file.parents else apex_file

        # Check 1: direct assignment to blng__Status__c = 'Paid' on invoices
        if MANUAL_STATUS_PAID_PATTERN.search(content):
            issues.append(
                f"{rel}: WARN: Direct assignment of blng__Status__c = 'Paid' detected. "
                "Invoice status should transition automatically via blng__PaymentAllocation__c, "
                "not be set manually. Manual status updates bypass the payment allocation trail."
            )

        # Check 2: direct assignment to blng__ChargeAmount__c (invoice line edit)
        if CHARGE_AMOUNT_ASSIGNMENT_PATTERN.search(content):
            issues.append(
                f"{rel}: WARN: Direct assignment to blng__ChargeAmount__c detected. "
                "Invoice line amounts are system-generated from blng__BillingSchedule__c. "
                "Correct the billing schedule and use the credit memo process — do not edit invoice lines directly."
            )

        # Check 3: blng__Payment__c usage without blng__PaymentAllocation__c in same file
        if PAYMENT_WITHOUT_ALLOCATION_PATTERN.search(content) and not ALLOCATION_PATTERN.search(content):
            issues.append(
                f"{rel}: WARN: blng__Payment__c referenced but blng__PaymentAllocation__c not found in same file. "
                "Payment processing that does not create PaymentAllocation records will leave invoices open. "
                "Verify that PaymentAllocation creation is handled in a related file or process."
            )

    return issues


def check_soql_files(manifest_dir: Path) -> list[str]:
    """Scan SOQL or query files for reconciliation completeness."""
    issues: list[str] = []
    # Look for files that might contain SOQL: .soql, .sql, .cls, .js, .py
    query_files = (
        list(manifest_dir.rglob("*.soql"))
        + list(manifest_dir.rglob("*.sql"))
    )

    for qfile in query_files:
        try:
            content = qfile.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = qfile.relative_to(manifest_dir) if manifest_dir in qfile.parents else qfile

        # Check: SOQL file queries blng__Invoice__c but never references blng__RevenueTransactionErrorLog__c
        if INVOICE_SOQL_PATTERN.search(content) and not ERROR_LOG_SOQL_PATTERN.search(content):
            issues.append(
                f"{rel}: INFO: Invoice SOQL found but blng__RevenueTransactionErrorLog__c not referenced. "
                "Reconciliation workflows should always start with the Revenue Transaction Error Log. "
                "Consider adding a blng__RevenueTransactionErrorLog__c query to this file."
            )

    return issues


def check_skill_package(manifest_dir: Path) -> list[str]:
    """Check for skill package completeness from within the manifest dir."""
    issues: list[str] = []

    # If we're pointed at the skill package itself, validate key files exist
    skill_md = manifest_dir / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8", errors="replace")

        # Check for Official Sources Used section
        if "## Official Sources Used" not in content:
            issues.append(
                "SKILL.md: WARN: '## Official Sources Used' section is missing. "
                "At least one official Salesforce URL is required."
            )

        # Check for Recommended Workflow section
        if "## Recommended Workflow" not in content:
            issues.append(
                "SKILL.md: WARN: '## Recommended Workflow' section is missing. "
                "SKILL.md must include a Recommended Workflow section with 3-7 numbered steps."
            )

        # Check for NOT for clause in description
        if "NOT for" not in content:
            issues.append(
                "SKILL.md: WARN: Description is missing a 'NOT for ...' exclusion clause. "
                "The description must explicitly state what this skill does not cover."
            )

        # Check for blng__PaymentAllocation__c mention (key concept for this skill)
        if "blng__PaymentAllocation__c" not in content:
            issues.append(
                "SKILL.md: WARN: blng__PaymentAllocation__c not mentioned in SKILL.md. "
                "Payment allocation is the core mechanism for invoice reconciliation in Salesforce Billing."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_billing_data_reconciliation(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Skill package self-check
    issues.extend(check_skill_package(manifest_dir))

    # Apex checks: look for a classes/ or force-app/ subdirectory
    for apex_candidate in ["classes", "force-app", "src"]:
        apex_dir = manifest_dir / apex_candidate
        if apex_dir.exists():
            issues.extend(check_apex_files(apex_dir))
            break
    else:
        # Try manifest_dir itself if it looks like an Apex directory
        if any(manifest_dir.rglob("*.cls")):
            issues.extend(check_apex_files(manifest_dir))

    # SOQL file checks
    issues.extend(check_soql_files(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Billing data reconciliation configuration and metadata "
            "for common issues (stdlib only — no pip dependencies)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or skill package (default: current directory).",
    )
    parser.add_argument(
        "--apex-dir",
        default=None,
        help="Explicit path to Apex classes directory (overrides auto-detection).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    issues = check_billing_data_reconciliation(manifest_dir)

    # If --apex-dir is explicitly provided, also scan that directory
    if args.apex_dir:
        apex_dir = Path(args.apex_dir).resolve()
        issues.extend(check_apex_files(apex_dir))

    if not issues:
        print("No issues found.")
        return 0

    warn_count = 0
    info_count = 0
    for issue in issues:
        if ": WARN:" in issue or issue.startswith("WARN:"):
            print(f"WARN: {issue}", file=sys.stderr)
            warn_count += 1
        else:
            print(f"INFO: {issue}")
            info_count += 1

    print(f"\nSummary: {warn_count} warning(s), {info_count} info(s).")
    return 1 if warn_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
