#!/usr/bin/env python3
"""Checker script for Commerce Payment Integration skill.

Scans Salesforce Apex source files in a metadata directory for common
anti-patterns documented in references/gotchas.md and
references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_payment_integration.py [--help]
    python3 check_commerce_payment_integration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Raw card data parameter names in Apex methods / variables
_RAW_CARD_DATA_PARAMS = re.compile(
    r"\b(cardNumber|card_number|cvv|cvc|expiryDate|expiry_date|panNumber|pan)\b",
    re.IGNORECASE,
)

# Hardcoded HTTP endpoint in setEndpoint() — should use callout: scheme
_HARDCODED_ENDPOINT = re.compile(
    r'setEndpoint\s*\(\s*["\']https?://',
    re.IGNORECASE,
)

# Hardcoded Authorization header value in setHeader()
_HARDCODED_AUTH_HEADER = re.compile(
    r'setHeader\s*\(\s*["\']Authorization["\']',
    re.IGNORECASE,
)

# Legacy CartPaymentAuthorize interface — wrong for LWR stores
_LEGACY_INTERFACE = re.compile(
    r"implements\s+sfdc_checkout\.CartPaymentAuthorize",
    re.IGNORECASE,
)

# Missing setSalesforceResultCodeInfo — check if a file has a CommercePayments
# response set without the required result code info call.  We detect files
# that construct a response object but never call setSalesforceResultCodeInfo.
_RESPONSE_CONSTRUCTOR = re.compile(
    r"new\s+CommercePayments\.(AuthorizationResponse|CaptureResponse"
    r"|ReferencedRefundResponse|AuthorizationReversalResponse"
    r"|PostAuthorizationResponse|PaymentMethodTokenizationResponse)\s*\(\s*\)",
    re.IGNORECASE,
)
_RESULT_CODE_CALL = re.compile(
    r"setSalesforceResultCodeInfo\s*\(",
    re.IGNORECASE,
)

# Check all six RequestType enum values are referenced
_ALL_REQUEST_TYPES = [
    "RequestType.Tokenize",
    "RequestType.Authorization",
    "RequestType.PostAuthorization",
    "RequestType.Capture",
    "RequestType.ReferencedRefund",
    "RequestType.AuthorizationReversal",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apex_files(manifest_dir: Path) -> list[Path]:
    """Return all .cls files under manifest_dir."""
    return list(manifest_dir.rglob("*.cls"))


def _check_file_for_raw_card_data(path: Path, content: str) -> list[str]:
    issues: list[str] = []
    for match in _RAW_CARD_DATA_PARAMS.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_no}: POSSIBLE raw card data parameter '{match.group()}' "
            f"— card data must never pass through Apex. Use provider-hosted "
            f"capture component and tokenization instead."
        )
    return issues


def _check_file_for_hardcoded_endpoint(path: Path, content: str) -> list[str]:
    issues: list[str] = []
    for match in _HARDCODED_ENDPOINT.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_no}: Hardcoded HTTPS endpoint in setEndpoint(). "
            f"Use 'callout:<NamedCredentialName>/...' instead."
        )
    return issues


def _check_file_for_hardcoded_auth_header(path: Path, content: str) -> list[str]:
    issues: list[str] = []
    for match in _HARDCODED_AUTH_HEADER.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_no}: Manual 'Authorization' header in setHeader(). "
            f"Store credentials in a Named Credential — Salesforce injects the "
            f"header automatically."
        )
    return issues


def _check_file_for_legacy_interface(path: Path, content: str) -> list[str]:
    issues: list[str] = []
    for match in _LEGACY_INTERFACE.finditer(content):
        line_no = content[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_no}: 'implements sfdc_checkout.CartPaymentAuthorize' "
            f"found. This legacy interface is only invoked for Aura-based B2B "
            f"checkout. For LWR-based B2B/D2C stores use "
            f"CommercePayments.PaymentGatewayAdapter instead."
        )
    return issues


def _check_file_for_missing_result_code(path: Path, content: str) -> list[str]:
    """Warn if a file constructs a CommercePayments response but never calls
    setSalesforceResultCodeInfo."""
    issues: list[str] = []
    if _RESPONSE_CONSTRUCTOR.search(content) and not _RESULT_CODE_CALL.search(content):
        issues.append(
            f"{path}: CommercePayments response object constructed but "
            f"setSalesforceResultCodeInfo() not found in this file. Every "
            f"response must map to a SalesforceResultCodes value so Commerce "
            f"order management can determine the next order state."
        )
    return issues


def _check_adapter_request_type_coverage(path: Path, content: str) -> list[str]:
    """Warn if a file implements PaymentGatewayAdapter but does not reference
    all six RequestType values."""
    issues: list[str] = []
    if "PaymentGatewayAdapter" not in content:
        return issues
    missing = [rt for rt in _ALL_REQUEST_TYPES if rt not in content]
    if missing:
        issues.append(
            f"{path}: PaymentGatewayAdapter found but these RequestType values "
            f"are not referenced: {', '.join(missing)}. All six must be handled "
            f"in processRequest to avoid silent checkout failures."
        )
    return issues


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------


def check_commerce_payment_integration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = _apex_files(manifest_dir)

    if not apex_files:
        # No Apex found — nothing to check, not an error
        return issues

    for apex_path in apex_files:
        try:
            content = apex_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            issues.append(f"{apex_path}: Could not read file — {exc}")
            continue

        issues.extend(_check_file_for_raw_card_data(apex_path, content))
        issues.extend(_check_file_for_hardcoded_endpoint(apex_path, content))
        issues.extend(_check_file_for_hardcoded_auth_header(apex_path, content))
        issues.extend(_check_file_for_legacy_interface(apex_path, content))
        issues.extend(_check_file_for_missing_result_code(apex_path, content))
        issues.extend(_check_adapter_request_type_coverage(apex_path, content))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex metadata for Commerce payment integration anti-patterns: "
            "raw card data, hardcoded credentials, legacy interface usage, "
            "missing SalesforceResultCodes mapping, and incomplete RequestType coverage."
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
    issues = check_commerce_payment_integration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
