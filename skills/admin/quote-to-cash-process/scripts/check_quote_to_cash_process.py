#!/usr/bin/env python3
"""Checker script for Quote-to-Cash Process (CPQ + Revenue Cloud) skill.

Validates Salesforce metadata in a retrieved project directory for common
CPQ Q2C anti-patterns and configuration gaps.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_quote_to_cash_process.py [--help]
    python3 check_quote_to_cash_process.py --manifest-dir path/to/metadata
    python3 check_quote_to_cash_process.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, *extensions: str) -> list[Path]:
    """Recursively find files with the given extensions under root."""
    results: list[Path] = []
    for ext in extensions:
        results.extend(root.rglob(f"*{ext}"))
    return results


def _read_text(path: Path) -> str:
    """Read file text safely, returning empty string on error."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_standard_quote_references(manifest_dir: Path) -> list[str]:
    """Detect Apex and SOQL referencing standard Quote/QuoteLineItem in a CPQ org.

    In CPQ orgs, quotes live on SBQQ__Quote__c and SBQQ__QuoteLine__c.
    References to the standard Quote or QuoteLineItem objects return no CPQ data.
    """
    issues: list[str] = []
    apex_files = _find_files(manifest_dir, ".cls", ".trigger")

    # Patterns that indicate standard object usage
    patterns = [
        # FROM Quote (SOQL) — but not SBQQ__Quote__c
        (re.compile(r'\bFROM\s+Quote\b', re.IGNORECASE), "SOQL query on standard Quote object"),
        (re.compile(r'\bFROM\s+QuoteLineItem\b', re.IGNORECASE), "SOQL query on standard QuoteLineItem object"),
        # Schema.Quote (Apex describe)
        (re.compile(r'\bSchema\.Quote\b'), "Apex reference to Schema.Quote (standard object)"),
        # new Quote( — Apex DML on standard object
        (re.compile(r'\bnew\s+Quote\s*\('), "Apex DML: new Quote() targets standard object"),
        (re.compile(r'\bnew\s+QuoteLineItem\s*\('), "Apex DML: new QuoteLineItem() targets standard object"),
    ]

    for apex_file in apex_files:
        text = _read_text(apex_file)
        for pattern, description in patterns:
            if pattern.search(text):
                issues.append(
                    f"{description} found in {apex_file.relative_to(manifest_dir)} — "
                    f"use SBQQ__Quote__c / SBQQ__QuoteLine__c instead"
                )
    return issues


def check_process_instance_for_approvals(manifest_dir: Path) -> list[str]:
    """Detect Apex querying ProcessInstance/ProcessInstanceWorkitem for CPQ approval status.

    Advanced Approvals (sbaa__) does not create ProcessInstance records.
    Approval status must be read from sbaa__ApprovalRequest__c.
    """
    issues: list[str] = []
    apex_files = _find_files(manifest_dir, ".cls", ".trigger")

    pattern_pi = re.compile(r'\bFROM\s+ProcessInstance\b', re.IGNORECASE)
    pattern_piw = re.compile(r'\bFROM\s+ProcessInstanceWorkitem\b', re.IGNORECASE)

    for apex_file in apex_files:
        text = _read_text(apex_file)
        if pattern_pi.search(text) or pattern_piw.search(text):
            issues.append(
                f"ProcessInstance/ProcessInstanceWorkitem query in {apex_file.relative_to(manifest_dir)} — "
                f"this returns no records for Advanced Approvals (sbaa__) managed CPQ quotes; "
                f"query sbaa__ApprovalRequest__c instead"
            )
    return issues


def check_hardcoded_approver_ids(manifest_dir: Path) -> list[str]:
    """Detect hardcoded Salesforce User IDs in sbaa__Approver__c Apex or data files.

    sbaa__Approver__c records with hardcoded User IDs break when users are deactivated.
    Use dynamic sources: Owner.Manager field references, queues, or role hierarchy.
    """
    issues: list[str] = []
    apex_files = _find_files(manifest_dir, ".cls", ".trigger")

    # Pattern: sbaa__User__c followed (loosely) by a hardcoded 15 or 18 char Salesforce ID
    pattern = re.compile(
        r'sbaa__User__c\s*=\s*[\'"]([0-9A-Za-z]{15,18})[\'"]'
    )

    for apex_file in apex_files:
        text = _read_text(apex_file)
        matches = pattern.findall(text)
        if matches:
            issues.append(
                f"Hardcoded User ID(s) {matches} in sbaa__Approver__c.sbaa__User__c "
                f"in {apex_file.relative_to(manifest_dir)} — "
                f"use dynamic approver sources (Owner.Manager, Queue) instead"
            )
    return issues


def check_process_builder_on_sbqq(manifest_dir: Path) -> list[str]:
    """Detect Process Builder definitions targeting SBQQ__Quote__c.

    Process Builder is deprecated and its async execution can conflict with
    CPQ's synchronous trigger logic. Use Record-Triggered Flow instead.
    """
    issues: list[str] = []
    # Process Builder files are FlowDefinition metadata with processType = Workflow
    flow_files = _find_files(manifest_dir, ".flow-meta.xml", ".flow")

    pb_type_pattern = re.compile(r'<processType>Workflow</processType>', re.IGNORECASE)
    sbqq_object_pattern = re.compile(r'<object>SBQQ__Quote__c</object>', re.IGNORECASE)

    for flow_file in flow_files:
        text = _read_text(flow_file)
        if pb_type_pattern.search(text) and sbqq_object_pattern.search(text):
            issues.append(
                f"Process Builder definition targeting SBQQ__Quote__c found: "
                f"{flow_file.relative_to(manifest_dir)} — "
                f"Process Builder is deprecated; migrate to Record-Triggered Flow to avoid "
                f"CPQ trigger interaction issues"
            )
    return issues


def check_missing_contracted_guard_in_flows(manifest_dir: Path) -> list[str]:
    """Detect flows on SBQQ__Quote__c that set SBQQ__Contracted__c without a re-entry guard.

    Flows that set SBQQ__Contracted__c = true on Quote must use
    'Run Once Per Record Version' or equivalent to prevent recursion.
    """
    issues: list[str] = []
    flow_files = _find_files(manifest_dir, ".flow-meta.xml", ".flow")

    sbqq_object_pattern = re.compile(r'<object>SBQQ__Quote__c</object>', re.IGNORECASE)
    contracted_pattern = re.compile(r'SBQQ__Contracted__c', re.IGNORECASE)
    # triggerType for record-triggered flows that run repeatedly
    always_pattern = re.compile(r'<triggerType>RecordAfterSave</triggerType>', re.IGNORECASE)
    once_pattern = re.compile(r'<runAsUser>false</runAsUser>|oncePerRecord|ONCE_PER_RECORD_VERSION', re.IGNORECASE)

    for flow_file in flow_files:
        text = _read_text(flow_file)
        if (
            sbqq_object_pattern.search(text)
            and contracted_pattern.search(text)
            and always_pattern.search(text)
            and not once_pattern.search(text)
        ):
            issues.append(
                f"Flow {flow_file.relative_to(manifest_dir)} sets SBQQ__Contracted__c on "
                f"SBQQ__Quote__c without a clear run-once guard — "
                f"verify 'Run Once Per Record Version' is configured to prevent recursion "
                f"with CPQ's trigger handler"
            )
    return issues


def check_billing_rule_assignment(manifest_dir: Path) -> list[str]:
    """Heuristic: detect Product2 metadata files without blng__BillingRule__c references.

    Products without a Billing Rule assigned generate no billing schedules when ordered.
    This check is a heuristic based on custom field presence in product metadata.
    """
    issues: list[str] = []
    # Product metadata lives in objects/ or customMetadata/ depending on setup
    product_files = list(manifest_dir.rglob("Product2.object-meta.xml"))

    if not product_files:
        # No product metadata found — skip this check silently
        return issues

    for product_file in product_files:
        text = _read_text(product_file)
        if "blng__BillingRule__c" not in text:
            issues.append(
                f"Product2 object metadata {product_file.relative_to(manifest_dir)} does not "
                f"reference blng__BillingRule__c — confirm that recurring products have a "
                f"Billing Rule assigned; products without one generate no billing schedules"
            )
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def check_quote_to_cash_process(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_standard_quote_references(manifest_dir))
    issues.extend(check_process_instance_for_approvals(manifest_dir))
    issues.extend(check_hardcoded_approver_ids(manifest_dir))
    issues.extend(check_process_builder_on_sbqq(manifest_dir))
    issues.extend(check_missing_contracted_guard_in_flows(manifest_dir))
    issues.extend(check_billing_rule_assignment(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CPQ + Revenue Cloud Q2C metadata for common anti-patterns. "
            "Detects: standard Quote object usage, ProcessInstance approval queries, "
            "hardcoded approver IDs, Process Builder on SBQQ objects, "
            "and missing billing rule references."
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
    issues = check_quote_to_cash_process(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
