#!/usr/bin/env python3
"""Checker script for CPQ Integration with ERP skill.

Scans a Salesforce metadata directory for common CPQ-ERP integration anti-patterns:
  - Flows or triggers on quote/opportunity events instead of Order activation
  - SOQL queries against QuoteLineItem instead of SBQQ__QuoteLine__c
  - HTTP callouts inside QCP (Quote Calculator Plugin) classes
  - Missing Named Credential usage (plain Authorization headers in Apex)
  - Missing ERP writeback to Order record after callout

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_integration_with_erp.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# SOQL queries against QuoteLineItem that are likely in a CPQ context
_QUOTE_LINE_ITEM_RE = re.compile(
    r"\bFROM\s+QuoteLineItem\b", re.IGNORECASE
)

# HTTP callout inside a QCP class — detect classes that implement SBQQ plugin
# and also contain HttpRequest or Http.send
_QCP_CLASS_RE = re.compile(
    r"(SBQQ\.QuoteCalculatorPlugin|SBQQ\.QuoteCalculatorPlugin2)", re.IGNORECASE
)
_HTTP_CALLOUT_RE = re.compile(
    r"\bHttpRequest\b|\bHttp\(\)", re.IGNORECASE
)

# Plain Authorization header (not using Named Credential)
_PLAIN_AUTH_HEADER_RE = re.compile(
    r"setHeader\s*\(\s*['\"]Authorization['\"]", re.IGNORECASE
)
# Named credential callout (correct pattern)
_NAMED_CRED_RE = re.compile(
    r"callout:", re.IGNORECASE
)

# Flows: trigger on SBQQ__Quote__c.SBQQ__Status__c or Opportunity.StageName
_QUOTE_TRIGGER_RE = re.compile(
    r"SBQQ__Status__c|StageName.*Closed.Won|Closed.Won.*StageName", re.IGNORECASE
)

# Missing ERP writeback: files with Http callouts but no update back to Order
_ORDER_UPDATE_RE = re.compile(
    r"\bupdate\s+\w*(order|ord)\w*\b|\bOrder\s*\(\s*Id\s*=", re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _apex_files(manifest_dir: Path):
    return list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))


def _flow_files(manifest_dir: Path):
    return list(manifest_dir.rglob("*.flow-meta.xml")) + list(manifest_dir.rglob("*.flow"))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_quote_line_item_queries(manifest_dir: Path) -> list[str]:
    """Flag SOQL queries against QuoteLineItem in Apex files (CPQ uses SBQQ__QuoteLine__c)."""
    issues: list[str] = []
    for apex_file in _apex_files(manifest_dir):
        content = _read_text(apex_file)
        if _QUOTE_LINE_ITEM_RE.search(content):
            issues.append(
                f"{apex_file.name}: SOQL query against QuoteLineItem detected. "
                "CPQ does not populate QuoteLineItem — use SBQQ__QuoteLine__c for "
                "quote-time data or OrderItem for order-time data."
            )
    return issues


def check_qcp_callouts(manifest_dir: Path) -> list[str]:
    """Flag HTTP callouts inside QCP implementation classes."""
    issues: list[str] = []
    for apex_file in _apex_files(manifest_dir):
        content = _read_text(apex_file)
        if _QCP_CLASS_RE.search(content) and _HTTP_CALLOUT_RE.search(content):
            issues.append(
                f"{apex_file.name}: HTTP callout detected inside a QCP class "
                "(implements SBQQ.QuoteCalculatorPlugin). QCP executes in a restricted "
                "context where callouts are not permitted. Move inventory/pricing API "
                "calls to an invocable Apex action or a pre-fetch batch pattern."
            )
    return issues


def check_plain_auth_headers(manifest_dir: Path) -> list[str]:
    """Flag plain Authorization headers in Apex — credentials should use Named Credentials."""
    issues: list[str] = []
    for apex_file in _apex_files(manifest_dir):
        content = _read_text(apex_file)
        if _PLAIN_AUTH_HEADER_RE.search(content) and not _NAMED_CRED_RE.search(content):
            issues.append(
                f"{apex_file.name}: Authorization header set manually without a "
                "Named Credential endpoint (callout:). ERP credentials must be stored "
                "in Named Credentials, not in Apex code or custom settings."
            )
    return issues


def check_flow_quote_triggers(manifest_dir: Path) -> list[str]:
    """Flag Flows that trigger ERP transmission on quote/opportunity events instead of Order.Status."""
    issues: list[str] = []
    for flow_file in _flow_files(manifest_dir):
        content = _read_text(flow_file)
        # Only flag flows that also appear to involve an ERP callout or action
        if _QUOTE_TRIGGER_RE.search(content) and ("callout" in content.lower() or "erp" in content.lower()):
            issues.append(
                f"{flow_file.name}: Flow appears to trigger an ERP action on a quote "
                "or opportunity status event. The canonical ERP trigger point is "
                "Order.Status reaching the activated value, not quote close or "
                "Opportunity StageName = Closed Won."
            )
    return issues


def check_missing_erp_writeback(manifest_dir: Path) -> list[str]:
    """Warn when Apex files make HTTP callouts but show no Order writeback."""
    issues: list[str] = []
    for apex_file in _apex_files(manifest_dir):
        content = _read_text(apex_file)
        if _HTTP_CALLOUT_RE.search(content) and "Order" in content:
            # If there's a callout and Order is referenced but no writeback pattern found
            if not _ORDER_UPDATE_RE.search(content):
                issues.append(
                    f"{apex_file.name}: Apex file makes HTTP callouts and references Order "
                    "but shows no Order update after the callout. Ensure the ERP order number "
                    "or confirmation status is written back to the Salesforce Order record "
                    "for deduplication and traceability."
                )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_cpq_integration_with_erp(manifest_dir: Path) -> list[str]:
    """Run all CPQ-ERP integration checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_count = len(_apex_files(manifest_dir))
    flow_count = len(_flow_files(manifest_dir))

    if apex_count == 0 and flow_count == 0:
        issues.append(
            "No Apex (.cls, .trigger) or Flow metadata files found in manifest directory. "
            "Point --manifest-dir at the root of a Salesforce metadata deployment (e.g., force-app/main/default)."
        )
        return issues

    issues.extend(check_quote_line_item_queries(manifest_dir))
    issues.extend(check_qcp_callouts(manifest_dir))
    issues.extend(check_plain_auth_headers(manifest_dir))
    issues.extend(check_flow_quote_triggers(manifest_dir))
    issues.extend(check_missing_erp_writeback(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce CPQ-ERP integration metadata for common anti-patterns. "
            "See skills/architect/cpq-integration-with-erp/references/gotchas.md for details."
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
    issues = check_cpq_integration_with_erp(manifest_dir)

    if not issues:
        print("No CPQ-ERP integration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
