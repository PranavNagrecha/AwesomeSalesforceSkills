#!/usr/bin/env python3
"""Checker script for Commerce Checkout Flow Design skill.

Validates Salesforce metadata for common checkout design anti-patterns.
Uses stdlib only — no pip dependencies.

Checks performed:
  1. Detects checkout Flow metadata in LWR-style store configurations
     (Flow files with checkout-related names alongside LWR site metadata)
  2. Warns when a guest checkout Flow is present but CartDeliveryGroup
     email/phone field references are absent from the Flow XML
  3. Warns when a checkout Flow has a BillingAddress screen element
     without explicit WebCart billing field assignment logic
  4. Warns when a checkout Flow references both Extension Point metadata
     and Flow Builder steps in the same manifest (mutually exclusive surfaces)
  5. Warns when payment-related Flow screens exist without any reference
     to tokenization or payment component integration

Usage:
    python3 check_commerce_checkout_flow_design.py [--help]
    python3 check_commerce_checkout_flow_design.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"

# Substrings in a Flow file name that suggest it is a checkout flow
CHECKOUT_FLOW_HINTS = ("checkout", "Checkout", "CartCheckout", "cart_checkout")

# LWR site indicator file patterns
LWR_SITE_HINTS = ("lwrStore", "LWRStore", "b2c_lite_store", "b2c_store", "lwr_store")

# Extension Point configuration file patterns
EXTENSION_POINT_HINTS = ("checkoutExtension", "CheckoutExtension", "CartExtension")

# Fields that indicate guest checkout email/phone collection
GUEST_REQUIRED_FIELDS = (
    "CartDeliveryGroup.Email",
    "CartDeliveryGroup.Phone",
    "{!CartDeliveryGroup.Email}",
    "{!CartDeliveryGroup.Phone}",
    "Email",  # loose match for field mappings in Flow variables
)

# Billing fields that must be explicitly set on WebCart
BILLING_FIELDS = (
    "BillingStreet",
    "BillingCity",
    "BillingPostalCode",
    "BillingState",
    "BillingCountry",
)

# Tokenization keywords that should appear near payment screens
TOKENIZATION_HINTS = (
    "token",
    "Token",
    "paymentToken",
    "PaymentToken",
    "stripe",
    "Stripe",
    "adyen",
    "Adyen",
    "braintree",
    "Braintree",
)


def find_flow_files(manifest_dir: Path) -> list[Path]:
    """Return all .flow-meta.xml files under manifest_dir."""
    return list(manifest_dir.rglob("*.flow-meta.xml"))


def find_site_files(manifest_dir: Path) -> list[Path]:
    """Return all .site-meta.xml and ExperienceBundle files under manifest_dir."""
    sites = list(manifest_dir.rglob("*.site-meta.xml"))
    sites += list(manifest_dir.rglob("*.json"))  # ExperienceBundle config files
    return sites


def is_checkout_flow(flow_path: Path) -> bool:
    """Return True if the file name suggests it is a checkout flow."""
    return any(hint in flow_path.name for hint in CHECKOUT_FLOW_HINTS)


def flow_xml_text(flow_path: Path) -> str:
    """Return the raw text content of a Flow file, or empty string on error."""
    try:
        return flow_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def check_lwr_store_has_checkout_flow(manifest_dir: Path) -> list[str]:
    """Warn if both LWR site indicators and checkout Flow files are present.

    On LWR stores, checkout Flows in Experience Builder have no effect.
    Their presence likely indicates a misconfiguration or design error.
    """
    issues: list[str] = []
    flow_files = [f for f in find_flow_files(manifest_dir) if is_checkout_flow(f)]
    if not flow_files:
        return issues

    site_files = find_site_files(manifest_dir)
    site_texts = []
    for sf in site_files:
        try:
            site_texts.append(sf.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass

    lwr_detected = any(
        hint in text for text in site_texts for hint in LWR_SITE_HINTS
    )
    if lwr_detected:
        for ff in flow_files:
            issues.append(
                f"Checkout Flow '{ff.name}' exists alongside LWR store configuration. "
                "Flow Builder checkout has no effect on LWR stores. "
                "LWR stores use Managed Checkout via Extension Points in Commerce Setup. "
                "Verify whether this Flow is intentional or a design error."
            )
    return issues


def check_guest_checkout_missing_email_phone(manifest_dir: Path) -> list[str]:
    """Warn if a checkout Flow lacks CartDeliveryGroup email/phone field references.

    Guest checkout requires explicit email and phone collection. Without these,
    the resulting Order Contact record is created with null values (silent failure).
    """
    issues: list[str] = []
    flow_files = [f for f in find_flow_files(manifest_dir) if is_checkout_flow(f)]

    for flow_path in flow_files:
        text = flow_xml_text(flow_path)
        if not text:
            continue
        # Look for any reference to guest buyer handling
        if "guest" not in text.lower() and "Guest" not in text:
            continue
        # Check for CartDeliveryGroup email/phone field references
        has_email = any(hint in text for hint in ("CartDeliveryGroup.Email", "deliveryGroup", "EmailAddress"))
        has_phone = any(hint in text for hint in ("CartDeliveryGroup.Phone", "PhoneNumber", "MobilePhone"))
        if not has_email:
            issues.append(
                f"Checkout Flow '{flow_path.name}' appears to handle guest checkout "
                "but does not reference CartDeliveryGroup.Email. "
                "Guest buyers have no session email — it must be explicitly collected "
                "and written to CartDeliveryGroup.Email or the Order Contact will be null."
            )
        if not has_phone:
            issues.append(
                f"Checkout Flow '{flow_path.name}' appears to handle guest checkout "
                "but does not reference CartDeliveryGroup.Phone. "
                "Guest buyers have no session phone — it must be explicitly collected "
                "and written to CartDeliveryGroup.Phone or the Order Contact will be null."
            )
    return issues


def check_billing_address_mapping(manifest_dir: Path) -> list[str]:
    """Warn if a checkout Flow lacks explicit WebCart billing field assignments.

    Salesforce Commerce does not automatically copy shipping address to billing address.
    Missing WebCart billing fields produce a null billing contact on OrderSummary.
    """
    issues: list[str] = []
    flow_files = [f for f in find_flow_files(manifest_dir) if is_checkout_flow(f)]

    for flow_path in flow_files:
        text = flow_xml_text(flow_path)
        if not text:
            continue
        # Only check flows that reference billing address UI (likely have billing step)
        if "billing" not in text.lower():
            continue
        missing_billing = [field for field in BILLING_FIELDS if field not in text]
        if missing_billing:
            issues.append(
                f"Checkout Flow '{flow_path.name}' references billing address UI "
                f"but does not assign all required WebCart billing fields. "
                f"Missing assignments for: {', '.join(missing_billing)}. "
                "Salesforce does not auto-copy shipping address to WebCart billing fields. "
                "Missing fields produce a null billing contact on OrderSummary (silent failure)."
            )
    return issues


def check_mixed_lwr_aura_surfaces(manifest_dir: Path) -> list[str]:
    """Warn if both Extension Point and checkout Flow metadata appear in same manifest.

    LWR Managed Checkout uses Extension Points exclusively.
    Aura Flow Builder checkout uses Flow exclusively.
    Having both in the same deployment suggests a design error.
    """
    issues: list[str] = []
    flow_files = [f for f in find_flow_files(manifest_dir) if is_checkout_flow(f)]
    if not flow_files:
        return issues

    all_files = list(manifest_dir.rglob("*"))
    all_texts = []
    for fp in all_files:
        if fp.is_file() and fp.suffix in (".xml", ".json", ".yaml", ".cls"):
            try:
                all_texts.append(fp.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass

    has_extension_points = any(
        hint in text for text in all_texts for hint in EXTENSION_POINT_HINTS
    )
    if has_extension_points:
        issues.append(
            "Both checkout Flow files and Extension Point configuration detected in manifest. "
            "LWR Managed Checkout (Extension Points) and Aura Flow Builder checkout are mutually exclusive. "
            "If this is an LWR store, checkout Flows have no effect. "
            "If this is an Aura store, Extension Point classes have no effect. "
            "Confirm store template type and remove the unused surface's configuration."
        )
    return issues


def check_payment_screens_missing_tokenization(manifest_dir: Path) -> list[str]:
    """Warn if checkout Flows include payment screens without tokenization references.

    Salesforce Commerce requires client-side tokenization for card payment.
    Raw card data must never enter Salesforce infrastructure (PCI-DSS).
    """
    issues: list[str] = []
    flow_files = [f for f in find_flow_files(manifest_dir) if is_checkout_flow(f)]

    for flow_path in flow_files:
        text = flow_xml_text(flow_path)
        if not text:
            continue
        # Look for payment-related screen elements
        has_payment_screen = any(
            kw in text
            for kw in ("payment", "Payment", "creditCard", "CreditCard", "cardNumber", "CardNumber")
        )
        if not has_payment_screen:
            continue
        has_tokenization = any(hint in text for hint in TOKENIZATION_HINTS)
        if not has_tokenization:
            issues.append(
                f"Checkout Flow '{flow_path.name}' includes payment-related screen elements "
                "but does not reference a tokenization library (Stripe, Adyen, Braintree, etc.). "
                "Raw card data must never enter Salesforce — PCI-DSS requires client-side tokenization "
                "before any data reaches the Salesforce platform. "
                "Verify that the payment screen uses an embedded gateway component that tokenizes "
                "card data client-side and only passes a token to the CartCheckoutSession."
            )
    return issues


def check_commerce_checkout_flow_design(manifest_dir: Path) -> list[str]:
    """Run all checkout design checks and return a combined list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_lwr_store_has_checkout_flow(manifest_dir))
    issues.extend(check_guest_checkout_missing_email_phone(manifest_dir))
    issues.extend(check_billing_address_mapping(manifest_dir))
    issues.extend(check_mixed_lwr_aura_surfaces(manifest_dir))
    issues.extend(check_payment_screens_missing_tokenization(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Commerce checkout design anti-patterns. "
            "Validates LWR vs Aura surface separation, guest checkout field requirements, "
            "billing address mapping, and payment tokenization requirements."
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
    issues = check_commerce_checkout_flow_design(manifest_dir)

    if not issues:
        print("No checkout design issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
