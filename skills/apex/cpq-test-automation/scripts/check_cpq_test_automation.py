#!/usr/bin/env python3
"""Checker script for CPQ Test Automation skill.

Scans Apex test classes in the given metadata directory for common CPQ test anti-patterns:

  1. Price rule assertions without a ServiceRouter call
  2. Hardcoded Pricebook IDs (01s... strings) in test classes
  3. SBQQ__Quote__c inserts missing required lookup fields
  4. Attempted mocking/stubbing of SBQQ namespace types
  5. Direct SBQQ__Contract__c inserts without ContractingService invocation

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_test_automation.py [--help]
    python3 check_cpq_test_automation.py --manifest-dir path/to/salesforce/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Detects @isTest classes or test methods for scoping
_TEST_CLASS_RE = re.compile(r"@[Ii]s[Tt]est", re.MULTILINE)

# Pricing fields that are only set by the CPQ engine (price rules, discount schedules)
_PRICING_FIELD_ASSERT_RE = re.compile(
    r"System\.(assert\w*)\s*\([^)]*SBQQ__(?:CustomerPrice|NetPrice|RegularPrice|ListPrice|"
    r"DiscountAmount|TotalPrice|GrossProfit|NetTotal)__c",
    re.IGNORECASE,
)

# ServiceRouter / QuoteCalculator invocations
_SERVICE_ROUTER_RE = re.compile(
    r"SBQQ\.(?:ServiceRouter|QuoteCalculatorPlugin)\.(?:calculate|calculateQuote)",
    re.IGNORECASE,
)

# Hardcoded 01s... Pricebook2 ID strings
_HARDCODED_PRICEBOOK_RE = re.compile(r"['\"]01s[A-Za-z0-9]{12,18}['\"]")

# SBQQ__Quote__c insert/upsert statement (simplified: looks for 'new SBQQ__Quote__c(')
_QUOTE_INSERT_RE = re.compile(r"new\s+SBQQ__Quote__c\s*\(", re.IGNORECASE)

# Required lookup fields on SBQQ__Quote__c
_ACCOUNT_FIELD_RE = re.compile(r"SBQQ__Account__c\s*=", re.IGNORECASE)
_OPP_FIELD_RE = re.compile(r"SBQQ__Opportunity__c\s*=", re.IGNORECASE)
_PRICEBOOK_FIELD_RE = re.compile(r"SBQQ__PricebookId__c\s*=", re.IGNORECASE)

# Stub/mock of SBQQ types
_SBQQ_STUB_RE = re.compile(
    r"Test\.createStub\s*\(\s*SBQQ\.|StubProvider.*SBQQ\.", re.IGNORECASE
)

# Direct SBQQ__Contract__c insert without ContractingService
_CONTRACT_INSERT_RE = re.compile(r"new\s+SBQQ__Contract__c\s*\(", re.IGNORECASE)
_CONTRACTING_SERVICE_RE = re.compile(
    r"SBQQ\.ContractingService\.contract\b", re.IGNORECASE
)

# Test.getStandardPricebookId usage
_STD_PRICEBOOK_METHOD_RE = re.compile(r"Test\.getStandardPricebookId\(\)", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def _check_file(apex_file: Path) -> list[str]:
    """Return a list of issue strings for the given Apex file."""
    issues: list[str] = []
    try:
        content = apex_file.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{apex_file}: cannot read file — {exc}")
        return issues

    # Only analyse test classes
    if not _TEST_CLASS_RE.search(content):
        return issues

    rel = str(apex_file)

    # --- Check 1: Price-field assertions without ServiceRouter ---
    has_pricing_asserts = bool(_PRICING_FIELD_ASSERT_RE.search(content))
    has_service_router = bool(_SERVICE_ROUTER_RE.search(content))
    if has_pricing_asserts and not has_service_router:
        issues.append(
            f"{rel}: CPQ pricing field assertion found without SBQQ.ServiceRouter.calculateQuote() call. "
            "Price rules are only evaluated by the CPQ calculation engine — direct DML does not fire them."
        )

    # --- Check 2: Hardcoded Pricebook2 IDs ---
    hardcoded_matches = _HARDCODED_PRICEBOOK_RE.findall(content)
    if hardcoded_matches:
        issues.append(
            f"{rel}: Hardcoded Pricebook2 ID(s) detected: {hardcoded_matches[:3]}. "
            "Use Test.getStandardPricebookId() instead — hardcoded IDs are org-specific and break in CI."
        )

    # --- Check 3: SBQQ__Quote__c inserts missing required lookups ---
    if _QUOTE_INSERT_RE.search(content):
        missing_fields = []
        if not _ACCOUNT_FIELD_RE.search(content):
            missing_fields.append("SBQQ__Account__c")
        if not _OPP_FIELD_RE.search(content):
            missing_fields.append("SBQQ__Opportunity__c")
        if not _PRICEBOOK_FIELD_RE.search(content):
            missing_fields.append("SBQQ__PricebookId__c")
        if missing_fields:
            issues.append(
                f"{rel}: SBQQ__Quote__c instantiation found but required lookup field(s) appear missing "
                f"from the file: {missing_fields}. All three (Account, Opportunity, Pricebook2) are required."
            )

    # --- Check 4: Attempted stubbing of SBQQ namespace types ---
    if _SBQQ_STUB_RE.search(content):
        issues.append(
            f"{rel}: Attempted Test.createStub() or StubProvider usage for SBQQ namespace type. "
            "Managed package types cannot be mocked via StubProvider. The CPQ package must be installed."
        )

    # --- Check 5: Direct SBQQ__Contract__c insert without ContractingService ---
    if _CONTRACT_INSERT_RE.search(content) and not _CONTRACTING_SERVICE_RE.search(content):
        issues.append(
            f"{rel}: Direct SBQQ__Contract__c instantiation found without SBQQ.ContractingService.contract() call. "
            "Direct inserts bypass the CPQ contracting engine and will not create subscription assets or renewal opportunities."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex test classes for common CPQ test automation anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project or metadata (default: current directory).",
    )
    return parser.parse_args()


def check_cpq_test_automation(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Find all Apex class files (*.cls)
    apex_files = list(manifest_dir.rglob("*.cls"))
    if not apex_files:
        # Not an error — project may have no Apex yet
        return issues

    for apex_file in apex_files:
        issues.extend(_check_file(apex_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cpq_test_automation(manifest_dir)

    if not issues:
        print("No CPQ test automation issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
