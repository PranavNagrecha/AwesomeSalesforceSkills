#!/usr/bin/env python3
"""Checker script for billing-integration-apex skill.

Scans Salesforce Apex source files in the given directory for common
billing-integration anti-patterns documented in this skill's references.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_billing_apex.py [--help]
    python3 check_billing_apex.py --source-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# blng.TransactionAPI method calls — these require async context
_TRANSACTION_API_CALL = re.compile(
    r"\bblng\.TransactionAPI\.(generateToken|authorize|capture|charge|void|refund)\b"
)

# DML statements (simplified heuristic — covers common forms)
_DML_STATEMENT = re.compile(
    r"\b(insert|update|delete|upsert)\s+(new\s+\w|\w+\s*[;{(])",
    re.IGNORECASE,
)

# Database DML methods
_DATABASE_DML = re.compile(
    r"\bDatabase\.(insert|update|delete|upsert|merge)\s*\(",
    re.IGNORECASE,
)

# Connect REST API commerce/invoices endpoint — check API version
_COMMERCE_INVOICES_ENDPOINT = re.compile(
    r"/services/data/v(\d+(?:\.\d+)?)/commerce/invoices",
    re.IGNORECASE,
)
_MIN_API_VERSION = 63.0

# Billing sObject references WITHOUT blng__ prefix (common mistakes)
_UNNAMESPACED_BILLING_OBJECTS = re.compile(
    r"\b(?<!blng__)(Invoice__c|BillingSchedule__c|Payment__c|CreditNote__c"
    r"|InvoiceRunResult__c|PaymentGateway__c|PaymentGatewayLog__c)\b"
)

# TransactionAPI usage in a class that does NOT declare AllowsCallouts
_ALLOWS_CALLOUTS = re.compile(r"\bDatabase\.AllowsCallouts\b")
_FUTURE_CALLOUT = re.compile(r"@future\s*\(\s*callout\s*=\s*true\s*\)", re.IGNORECASE)

# billingScheduleIds array — look for list assignment without size guard
_BILLING_SCHEDULE_IDS_ASSIGNMENT = re.compile(r"billingScheduleIds", re.IGNORECASE)
_SIZE_GUARD = re.compile(r"\.size\(\)\s*(>|>=|!=|<|<=)\s*\d+|MAX|limit|chunk", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_file(path: Path) -> list[str]:
    """Return a list of issue strings for a single Apex file."""
    issues: list[str] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    lines = source.splitlines()
    has_transaction_api = bool(_TRANSACTION_API_CALL.search(source))
    has_allows_callouts = bool(_ALLOWS_CALLOUTS.search(source))
    has_future_callout = bool(_FUTURE_CALLOUT.search(source))

    # ---- Rule 1: TransactionAPI without async declaration ----
    if has_transaction_api and not has_allows_callouts and not has_future_callout:
        issues.append(
            f"{path}: blng.TransactionAPI method called but class does not implement "
            "Database.AllowsCallouts and no @future(callout=true) detected. "
            "TransactionAPI makes HTTP callouts — must run in async context."
        )

    # ---- Rule 2: TransactionAPI and DML in same file (heuristic for sync risk) ----
    if has_transaction_api:
        for i, line in enumerate(lines, start=1):
            if _TRANSACTION_API_CALL.search(line):
                # Scan the surrounding 20 lines for DML
                window_start = max(0, i - 20)
                window_end = min(len(lines), i + 20)
                window = "\n".join(lines[window_start:window_end])
                if _DML_STATEMENT.search(window) or _DATABASE_DML.search(window):
                    issues.append(
                        f"{path}:{i}: blng.TransactionAPI call near DML statements "
                        "(within 20 lines). Verify this is in an async context with no "
                        "uncommitted DML before the callout."
                    )
                    break  # one warning per file for this rule

    # ---- Rule 3: Connect REST API endpoint version check ----
    for i, line in enumerate(lines, start=1):
        for match in _COMMERCE_INVOICES_ENDPOINT.finditer(line):
            try:
                version = float(match.group(1))
            except ValueError:
                continue
            if version < _MIN_API_VERSION:
                issues.append(
                    f"{path}:{i}: commerce/invoices endpoint uses API version "
                    f"v{match.group(1)}, but requires v63.0 or later. "
                    f"Update to /services/data/v63.0/commerce/invoices."
                )

    # ---- Rule 4: Unnamespaced Billing sObject references ----
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip comment lines
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        match = _UNNAMESPACED_BILLING_OBJECTS.search(line)
        if match:
            issues.append(
                f"{path}:{i}: Possible missing blng__ namespace prefix — "
                f"found '{match.group(0)}'. Billing managed package sObjects use "
                f"'blng__{match.group(0)}' as their API name."
            )

    # ---- Rule 5: billingScheduleIds assignment without size check ----
    if _BILLING_SCHEDULE_IDS_ASSIGNMENT.search(source):
        # Look for size guard anywhere in the file
        if not _SIZE_GUARD.search(source):
            issues.append(
                f"{path}: 'billingScheduleIds' referenced but no size guard (.size() "
                "comparison, MAX constant, or 'chunk' logic) detected. "
                "The Connect REST API commerce/invoices endpoint accepts a maximum of "
                "200 billing schedule IDs per request."
            )

    return issues


def check_directory(source_dir: Path) -> list[str]:
    """Scan all .cls files under source_dir and return aggregated issues."""
    issues: list[str] = []

    if not source_dir.exists():
        return [f"Source directory not found: {source_dir}"]

    cls_files = list(source_dir.rglob("*.cls"))
    if not cls_files:
        issues.append(
            f"No .cls files found under {source_dir}. "
            "Provide the root of a Salesforce DX project or classes directory."
        )
        return issues

    for cls_file in sorted(cls_files):
        issues.extend(check_file(cls_file))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Apex classes for billing-integration-apex anti-patterns.\n\n"
            "Checks performed:\n"
            "  1. blng.TransactionAPI called without Database.AllowsCallouts or @future(callout=true)\n"
            "  2. blng.TransactionAPI call near DML (potential uncommitted-DML callout violation)\n"
            "  3. Connect REST API commerce/invoices endpoint with API version < 63.0\n"
            "  4. Billing sObject names missing the blng__ namespace prefix\n"
            "  5. billingScheduleIds used without a size guard (200-schedule limit)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory containing Apex .cls files to scan (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)
    issues = check_directory(source_dir)

    if not issues:
        print("No billing-integration-apex issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
