#!/usr/bin/env python3
"""Checker script for B2B Commerce Store Setup skill.

Validates Salesforce metadata exported via `sf project retrieve` or
`sfdx force:source:retrieve` for common B2B Commerce store setup issues.

Checks performed:
  - Detects WebStore records missing an associated Experience Cloud site reference
  - Warns when no BuyerGroup metadata files are found
  - Detects CommerceEntitlementPolicy files with no linked product entries
  - Warns if no BuyerGroupMember-equivalent setup is detectable
  - Reports any XML metadata files that appear malformed (unparseable)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_b2b_commerce_store_setup.py [--manifest-dir path/to/metadata]
    python3 check_b2b_commerce_store_setup.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check exported Salesforce metadata for common B2B Commerce store "
            "setup issues: missing BuyerGroups, unlinked entitlement policies, "
            "and misconfigured WebStore records."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the retrieved Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_manifest_dir_exists(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
    elif not manifest_dir.is_dir():
        issues.append(f"Manifest path is not a directory: {manifest_dir}")
    return issues


def find_xml_files(manifest_dir: Path, pattern: str) -> list[Path]:
    return list(manifest_dir.rglob(pattern))


def check_webstore_files(manifest_dir: Path) -> list[str]:
    """Warn if WebStore metadata files exist but appear to lack a site association."""
    issues: list[str] = []
    webstore_files = find_xml_files(manifest_dir, "*.webStore-meta.xml")
    if not webstore_files:
        # WebStore metadata may not be retrievable in all project setups; soft warning only
        return issues

    for ws_file in webstore_files:
        try:
            tree = ET.parse(ws_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"Malformed XML in WebStore file {ws_file.name}: {exc}")
            continue

        # Look for a site or network reference; tag names vary by API version
        ns_tag = any(
            child.tag.lower().endswith(("site", "network", "experiencecloudsite"))
            for child in root.iter()
        )
        if not ns_tag:
            issues.append(
                f"WebStore file '{ws_file.name}' does not appear to reference an "
                "Experience Cloud site. Ensure the store is associated with a published "
                "site before testing buyer access."
            )

    return issues


def check_buyer_groups(manifest_dir: Path) -> list[str]:
    """Warn if no BuyerGroup records or metadata files are detected."""
    issues: list[str] = []
    # BuyerGroup can appear in custom metadata, CSV fixtures, or object records
    buyer_group_files = (
        find_xml_files(manifest_dir, "*BuyerGroup*.xml")
        + find_xml_files(manifest_dir, "*buyerGroup*.xml")
        + find_xml_files(manifest_dir, "*buyer_group*.xml")
    )
    if not buyer_group_files:
        issues.append(
            "No BuyerGroup metadata or record files detected in the manifest directory. "
            "Every B2B Commerce store requires at least one BuyerGroup linked to the "
            "WebStore via a WebStoreBuyerGroup junction record."
        )
    return issues


def check_entitlement_policies(manifest_dir: Path) -> list[str]:
    """Check CommerceEntitlementPolicy files for obvious misconfiguration."""
    issues: list[str] = []
    policy_files = (
        find_xml_files(manifest_dir, "*EntitlementPolicy*.xml")
        + find_xml_files(manifest_dir, "*entitlementPolicy*.xml")
        + find_xml_files(manifest_dir, "*entitlement_policy*.xml")
    )
    if not policy_files:
        issues.append(
            "No CommerceEntitlementPolicy metadata files detected. Buyers cannot see "
            "any products without at least one active entitlement policy linked to a "
            "BuyerGroup and containing product records."
        )
        return issues

    for policy_file in policy_files:
        try:
            tree = ET.parse(policy_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"Malformed XML in entitlement policy file {policy_file.name}: {exc}")
            continue

        # Check for at least one product or entitlement entry in the policy
        product_entries = [
            child for child in root.iter()
            if "product" in child.tag.lower() or "entitlement" in child.tag.lower()
        ]
        if not product_entries:
            issues.append(
                f"EntitlementPolicy file '{policy_file.name}' appears to contain no "
                "product entitlement entries. An empty policy will result in buyers "
                "seeing no products in the storefront."
            )

    return issues


def check_buyer_group_member_files(manifest_dir: Path) -> list[str]:
    """Soft warning if no BuyerGroupMember or BuyerAccount records are detectable."""
    issues: list[str] = []
    member_files = (
        find_xml_files(manifest_dir, "*BuyerGroupMember*.xml")
        + find_xml_files(manifest_dir, "*buyerGroupMember*.xml")
        + find_xml_files(manifest_dir, "*BuyerAccount*.xml")
        + find_xml_files(manifest_dir, "*buyerAccount*.xml")
    )
    if not member_files:
        issues.append(
            "No BuyerGroupMember or BuyerAccount record files detected. Ensure that "
            "customer Accounts have been converted to BuyerAccounts (IsBuyer=true) and "
            "that each BuyerAccount has a BuyerGroupMember record assigning it to the "
            "correct BuyerGroup."
        )
    return issues


def check_webstore_buyer_group_junction(manifest_dir: Path) -> list[str]:
    """Warn if WebStoreBuyerGroup junction files are absent."""
    issues: list[str] = []
    junction_files = (
        find_xml_files(manifest_dir, "*WebStoreBuyerGroup*.xml")
        + find_xml_files(manifest_dir, "*webStoreBuyerGroup*.xml")
    )
    if not junction_files:
        issues.append(
            "No WebStoreBuyerGroup junction record files detected. Without this "
            "junction, a BuyerGroup is not linked to any WebStore and buyers in that "
            "group will see an empty storefront regardless of entitlement configuration."
        )
    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_b2b_commerce_store_setup(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    existence_issues = check_manifest_dir_exists(manifest_dir)
    if existence_issues:
        return existence_issues

    issues.extend(check_webstore_files(manifest_dir))
    issues.extend(check_buyer_groups(manifest_dir))
    issues.extend(check_entitlement_policies(manifest_dir))
    issues.extend(check_buyer_group_member_files(manifest_dir))
    issues.extend(check_webstore_buyer_group_junction(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_b2b_commerce_store_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
