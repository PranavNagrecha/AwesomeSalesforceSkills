#!/usr/bin/env python3
"""Checker script for Commerce Pricing and Promotions skill.

Scans a Salesforce metadata directory for common pricing and promotions
configuration issues: missing PromotionsCartCalculator in checkout flows,
stale active promotions, and pricebook assignment patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_pricing_and_promotions.py [--help]
    python3 check_commerce_pricing_and_promotions.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROMOTIONS_CALCULATOR_ELEMENT = "PromotionsCartCalculator"
# These substrings in a flow file name suggest it is a checkout flow.
CHECKOUT_FLOW_NAME_HINTS = ("checkout", "Checkout", "CartCheckout", "cart_checkout")
SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tag(local: str) -> str:
    """Return a namespaced tag string for Salesforce metadata XML."""
    return f"{{{SF_NAMESPACE}}}{local}"


def _find_flow_files(manifest_dir: Path) -> list[Path]:
    """Return all .flow-meta.xml files under manifest_dir."""
    return list(manifest_dir.rglob("*.flow-meta.xml"))


def _is_checkout_flow(flow_path: Path) -> bool:
    """Heuristic: does the file name suggest a checkout flow?"""
    name = flow_path.name
    return any(hint in name for hint in CHECKOUT_FLOW_NAME_HINTS)


def _flow_has_promotions_calculator(flow_path: Path) -> bool:
    """Return True if the flow XML contains a PromotionsCartCalculator element."""
    try:
        tree = ET.parse(flow_path)
    except ET.ParseError:
        return False  # malformed XML — caller will report separately
    root = tree.getroot()
    # Check any element with a <name> child equal to PromotionsCartCalculator
    for elem in root.iter():
        name_elem = elem.find(_tag("name"))
        if name_elem is not None and name_elem.text == PROMOTIONS_CALCULATOR_ELEMENT:
            return True
        # Also check elementType attribute pattern used in newer metadata format
        elem_type = elem.find(_tag("elementType"))
        if elem_type is not None and PROMOTIONS_CALCULATOR_ELEMENT in (elem_type.text or ""):
            return True
    return False


def _flow_is_active(flow_path: Path) -> bool:
    """Return True if the flow metadata declares status = Active."""
    try:
        tree = ET.parse(flow_path)
    except ET.ParseError:
        return False
    root = tree.getroot()
    status = root.find(_tag("status"))
    return status is not None and (status.text or "").strip().lower() == "active"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_checkout_flows_have_promotions_calculator(manifest_dir: Path) -> list[str]:
    """Warn if any active checkout flow is missing the PromotionsCartCalculator element."""
    issues: list[str] = []
    flow_files = _find_flow_files(manifest_dir)
    if not flow_files:
        return issues  # no flows found — skip silently

    checkout_flows = [f for f in flow_files if _is_checkout_flow(f)]
    if not checkout_flows:
        return issues  # no checkout flows detected — skip silently

    for flow_path in checkout_flows:
        if not _flow_is_active(flow_path):
            continue  # only check active flows
        if not _flow_has_promotions_calculator(flow_path):
            issues.append(
                f"Active checkout flow '{flow_path.name}' does not contain a "
                f"'{PROMOTIONS_CALCULATOR_ELEMENT}' element. Promotions will not "
                f"fire at checkout without this subflow. "
                f"(File: {flow_path})"
            )
    return issues


def check_for_stale_promotion_xml(manifest_dir: Path) -> list[str]:
    """Warn if Promotion metadata files are found with IsActive=true but no EndDate.

    Commerce orgs accumulate active promotions that consume evaluation slots
    (max 50 automatic + 50 manual per checkout call). Promotions without an
    end date are never automatically retired.
    """
    issues: list[str] = []
    # Promotion objects in metadata are typically exported as records or
    # custom metadata; check for any XML files with 'Promotion' in the name.
    promotion_files = list(manifest_dir.rglob("*Promotion*.xml"))
    promotion_files += list(manifest_dir.rglob("*promotion*.xml"))

    for pfile in promotion_files:
        try:
            tree = ET.parse(pfile)
        except ET.ParseError:
            issues.append(f"Could not parse XML file: {pfile}")
            continue
        root = tree.getroot()
        is_active = root.find(_tag("isActive")) or root.find("isActive")
        end_date = root.find(_tag("endDate")) or root.find("endDate")
        if is_active is not None and (is_active.text or "").strip().lower() == "true":
            if end_date is None or not (end_date.text or "").strip():
                issues.append(
                    f"Promotion file '{pfile.name}' has IsActive=true but no EndDate set. "
                    f"Promotions without an end date accumulate indefinitely and can push "
                    f"important promotions past the 50-per-call evaluation limit. "
                    f"(File: {pfile})"
                )
    return issues


def check_pricebook_limit_warnings(manifest_dir: Path) -> list[str]:
    """Warn if WebStorePricebook or BuyerGroupPricebook XML files indicate
    counts that may approach platform limits.

    Limits:
      - WebStorePricebook: max 5 per store
      - BuyerGroupPricebook: max 50 per BuyerGroup, max 100 BuyerGroups per pricebook
      - Evaluation limit: 25 pricebooks per resolution call (silent exclusion)
    """
    issues: list[str] = []
    wsb_files = list(manifest_dir.rglob("*WebStorePricebook*.xml"))
    bgp_files = list(manifest_dir.rglob("*BuyerGroupPricebook*.xml"))

    if len(wsb_files) > 4:
        issues.append(
            f"Found {len(wsb_files)} WebStorePricebook metadata files. "
            f"The platform hard limit is 5 per store. Review and remove unused assignments "
            f"before adding new ones. (Found in: {manifest_dir})"
        )

    if len(bgp_files) > 40:
        issues.append(
            f"Found {len(bgp_files)} BuyerGroupPricebook metadata files. "
            f"If these span a small number of BuyerGroups, individual groups may be "
            f"approaching the 50-pricebook-per-BuyerGroup limit. Also verify that no "
            f"buyer can see more than 25 pricebooks (silent exclusion above 25). "
            f"(Found in: {manifest_dir})"
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Commerce pricing and promotions metadata for common configuration issues.\n"
            "\n"
            "Checks performed:\n"
            "  1. Active checkout flows missing the PromotionsCartCalculator subflow element\n"
            "  2. Promotion records with IsActive=true but no EndDate (accumulation risk)\n"
            "  3. WebStorePricebook / BuyerGroupPricebook counts approaching platform limits\n"
            "\n"
            "All checks use stdlib XML parsing only — no pip dependencies required."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_commerce_pricing_and_promotions(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_checkout_flows_have_promotions_calculator(manifest_dir))
    issues.extend(check_for_stale_promotion_xml(manifest_dir))
    issues.extend(check_pricebook_limit_warnings(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_commerce_pricing_and_promotions(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
