#!/usr/bin/env python3
"""Checker script for Commerce Checkout Configuration skill.

Validates Salesforce metadata in a project directory for common
Commerce checkout configuration issues.

Checks performed:
  - Apex classes implementing sfdc_checkout.CartPaymentAuthorize: verifies
    they contain authorizePayment and do not throw exceptions at the top level.
  - WebCart DML updates: warns when billing address fields are set via trigger
    DML rather than through a storefront component or Checkout API.
  - Guest checkout: detects if CartDeliveryGroup is referenced in any Apex
    without email/phone field assignment.
  - CartValidationOutput: warns if no Apex or LWC in the project queries
    CartValidationOutput, indicating missing error surfacing.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_checkout_configuration.py [--manifest-dir PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    """Return all files under root with any of the given suffixes."""
    result: list[Path] = []
    for suffix in suffixes:
        result.extend(root.rglob(f"*{suffix}"))
    return result


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_payment_adapter(apex_files: list[Path]) -> list[str]:
    """Detect Apex payment adapters that may throw exceptions from authorizePayment."""
    issues: list[str] = []
    adapter_pattern = re.compile(
        r"implements\s+sfdc_checkout\.CartPaymentAuthorize", re.IGNORECASE
    )
    throw_pattern = re.compile(r"\bthrow\b", re.IGNORECASE)
    return_pattern = re.compile(r"setAuthorized\s*\(", re.IGNORECASE)

    for path in apex_files:
        content = read_text(path)
        if not adapter_pattern.search(content):
            continue

        # Found a payment adapter — check for throw statements
        if throw_pattern.search(content):
            issues.append(
                f"{path}: Payment adapter contains 'throw' statement. "
                "All gateway failure paths must return setAuthorized(false) "
                "instead of throwing — exceptions leave CartCheckoutSession "
                "in an unrecoverable state. See references/gotchas.md#gotcha-3."
            )

        # Check that setAuthorized is called at all
        if not return_pattern.search(content):
            issues.append(
                f"{path}: Payment adapter does not call setAuthorized(). "
                "The CartPaymentAuthorizationResponse must call setAuthorized(true) "
                "or setAuthorized(false) before being returned."
            )

    return issues


def check_billing_address_dml(apex_files: list[Path]) -> list[str]:
    """Warn when WebCart billing fields are set in trigger Apex via DML."""
    issues: list[str] = []
    billing_field_pattern = re.compile(
        r"\bBillingStreet\b|\bBillingCity\b|\bBillingPostalCode\b"
        r"|\bBillingState\b|\bBillingCountry\b",
        re.IGNORECASE,
    )
    trigger_pattern = re.compile(r"trigger\s+\w+\s+on\s+", re.IGNORECASE)
    dml_pattern = re.compile(r"\bupdate\s+\w*[Cc]art\w*\b", re.IGNORECASE)

    for path in apex_files:
        content = read_text(path)
        if not trigger_pattern.search(content):
            continue
        if billing_field_pattern.search(content) and dml_pattern.search(content):
            issues.append(
                f"{path}: Apex trigger sets WebCart billing address fields via DML. "
                "Trigger timing relative to CartCheckoutSession order creation state "
                "is non-deterministic — the order may be created before the DML commits. "
                "Set billing fields from the storefront component or Checkout API instead. "
                "See references/gotchas.md#gotcha-1."
            )

    return issues


def check_cart_validation_output_surfacing(
    apex_files: list[Path], lwc_files: list[Path]
) -> list[str]:
    """Warn if CartValidationOutput is never queried anywhere in the project."""
    issues: list[str] = []
    cvo_pattern = re.compile(r"CartValidationOutput", re.IGNORECASE)

    all_files = apex_files + lwc_files
    found = any(cvo_pattern.search(read_text(f)) for f in all_files)

    if all_files and not found:
        issues.append(
            "No Apex class or LWC file in this project references CartValidationOutput. "
            "Checkout errors (shipping, tax, inventory, payment) are written to "
            "CartValidationOutput records — without querying them, buyers see only "
            "generic errors and support teams cannot diagnose failures. "
            "See references/gotchas.md#gotcha-5 and references/llm-anti-patterns.md#anti-pattern-5."
        )

    return issues


def check_guest_checkout_email_phone(apex_files: list[Path]) -> list[str]:
    """Detect Apex that reads CartDeliveryGroup without setting Email or Phone."""
    issues: list[str] = []
    cdg_pattern = re.compile(r"CartDeliveryGroup", re.IGNORECASE)
    email_pattern = re.compile(r"\.Email\s*=|'Email'", re.IGNORECASE)
    phone_pattern = re.compile(r"\.Phone\s*=|'Phone'", re.IGNORECASE)

    for path in apex_files:
        content = read_text(path)
        if not cdg_pattern.search(content):
            continue
        # If the file deals with CartDeliveryGroup but never sets Email or Phone,
        # flag it as a potential guest checkout gap. Only flag if it looks like
        # a checkout or address-related class (heuristic: contains 'checkout' or 'address').
        context_pattern = re.compile(r"checkout|address|delivery", re.IGNORECASE)
        if not context_pattern.search(content):
            continue
        if not email_pattern.search(content) and not phone_pattern.search(content):
            issues.append(
                f"{path}: References CartDeliveryGroup in a checkout/address context "
                "but does not set Email or Phone fields. Guest checkout requires these "
                "fields to be explicitly populated — the platform does not derive them "
                "from the unauthenticated session. See references/gotchas.md#gotcha-2."
            )

    return issues


def check_raw_card_data(apex_files: list[Path], lwc_files: list[Path]) -> list[str]:
    """Detect field or variable names suggesting raw card data handling."""
    issues: list[str] = []
    pci_pattern = re.compile(
        r"\bcardNumber\b|\bcvv\b|\bcvc\b|\bsecurityCode\b|\bcardCvc\b"
        r"|\brawCard\b|\bccNumber\b",
        re.IGNORECASE,
    )

    for path in apex_files + lwc_files:
        content = read_text(path)
        if pci_pattern.search(content):
            issues.append(
                f"{path}: Contains field or variable names associated with raw card data "
                "(cardNumber, cvv, securityCode, etc.). Raw card data must never pass "
                "through Salesforce Apex or be stored in Salesforce fields. "
                "Use client-side tokenization via the payment gateway's JavaScript SDK. "
                "See references/llm-anti-patterns.md#anti-pattern-6."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Commerce Checkout Configuration metadata and Apex for common issues. "
            "Run from the root of a Salesforce DX project or metadata directory."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or SFDX project (default: current directory).",
    )
    return parser.parse_args()


def check_commerce_checkout_configuration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_files(manifest_dir, (".cls",))
    lwc_files = find_files(manifest_dir, (".js", ".html"))

    issues.extend(check_payment_adapter(apex_files))
    issues.extend(check_billing_address_dml(apex_files))
    issues.extend(check_cart_validation_output_surfacing(apex_files, lwc_files))
    issues.extend(check_guest_checkout_email_phone(apex_files))
    issues.extend(check_raw_card_data(apex_files, lwc_files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_commerce_checkout_configuration(manifest_dir)

    if not issues:
        print("No Commerce checkout configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
