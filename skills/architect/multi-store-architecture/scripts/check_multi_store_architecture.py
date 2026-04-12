#!/usr/bin/env python3
"""Checker script for Multi-Store Architecture skill.

Validates Salesforce metadata for common multi-store architecture issues:
- Multiple WebStoreCatalog records for the same WebStore
- Missing entitlement policies per WebStore
- Catalog-per-store anti-pattern (multiple ProductCatalog records in small orgs)
- Missing multi-currency configuration when multiple WebStores are present
- WebStore language field not set

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_multi_store_architecture.py [--help]
    python3 check_multi_store_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common multi-store architecture issues. "
            "Validates WebStoreCatalog assignments, entitlement policies, and multi-currency setup."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output issues as JSON array instead of plain text.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checkers
# ---------------------------------------------------------------------------


def check_web_store_catalog_multiplicity(manifest_dir: Path) -> list[str]:
    """Detect WebStore records with multiple WebStoreCatalog assignments.

    A WebStore can have at most one active storefront catalog. Multiple
    WebStoreCatalog records for the same WebStore produce a validation error
    in Salesforce Commerce and indicate the separate-catalog-per-buyer-group
    anti-pattern.
    """
    issues: list[str] = []

    # Look for WebStoreCatalog metadata files (objects or data export format)
    # Supports both SFDX metadata format (.object-meta.xml) and data export CSVs
    catalog_files = list(manifest_dir.rglob("WebStoreCatalog*.xml"))
    catalog_files += list(manifest_dir.rglob("WebStoreCatalog*.json"))

    if not catalog_files:
        return issues  # Nothing to check; metadata not present

    store_to_catalogs: dict[str, list[str]] = defaultdict(list)

    for f in catalog_files:
        try:
            if f.suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                records = data if isinstance(data, list) else data.get("records", [])
                for rec in records:
                    store_id = rec.get("WebStoreId", "")
                    catalog_id = rec.get("ProductCatalogId", rec.get("CatalogId", ""))
                    if store_id:
                        store_to_catalogs[store_id].append(catalog_id or f.name)
            elif f.suffix == ".xml":
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
                store_id = (
                    root.findtext("sf:WebStoreId", namespaces=ns)
                    or root.findtext("WebStoreId")
                    or ""
                )
                catalog_id = (
                    root.findtext("sf:ProductCatalogId", namespaces=ns)
                    or root.findtext("ProductCatalogId")
                    or f.stem
                )
                if store_id:
                    store_to_catalogs[store_id].append(catalog_id)
        except Exception:
            # Parsing failures do not block the rest of the check
            pass

    for store_id, catalogs in store_to_catalogs.items():
        if len(catalogs) > 1:
            issues.append(
                f"WebStore '{store_id}' has {len(catalogs)} WebStoreCatalog records "
                f"({', '.join(catalogs)}). A WebStore supports at most one active storefront "
                f"catalog. Use entitlement policies for buyer-group-level product visibility."
            )

    return issues


def check_product_catalog_count(manifest_dir: Path) -> list[str]:
    """Warn when multiple ProductCatalog records exist without justification.

    Multiple product catalogs are the anti-pattern for multi-store deployments
    where stores share the same product universe. This check flags the presence
    of more than two product catalog records, which suggests a per-store catalog
    pattern. (Two is sometimes legitimate: one for org-based, one for search.)
    """
    issues: list[str] = []

    catalog_files = list(manifest_dir.rglob("ProductCatalog*.xml"))
    catalog_files += list(manifest_dir.rglob("ProductCatalog*.json"))

    catalog_names: list[str] = []

    for f in catalog_files:
        try:
            if f.suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                records = data if isinstance(data, list) else data.get("records", [])
                for rec in records:
                    name = rec.get("Name", f.stem)
                    catalog_names.append(name)
            elif f.suffix == ".xml":
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
                name = (
                    root.findtext("sf:Name", namespaces=ns)
                    or root.findtext("Name")
                    or f.stem
                )
                catalog_names.append(name)
        except Exception:
            pass

    if len(catalog_names) > 2:
        issues.append(
            f"Found {len(catalog_names)} ProductCatalog records "
            f"({', '.join(catalog_names[:5])}{'...' if len(catalog_names) > 5 else ''}). "
            f"The recommended pattern for multi-store deployments is a single shared "
            f"ProductCatalog. Multiple catalogs are only justified when stores sell "
            f"genuinely disjoint product universes. Verify this is intentional."
        )

    return issues


def check_web_store_language_field(manifest_dir: Path) -> list[str]:
    """Detect WebStore records without a Language field set.

    The WebStore.Language field controls the default locale for the storefront.
    In multi-store deployments with locale-specific stores, this field must be
    set explicitly. Missing language configuration means the store falls back to
    the org default locale, which breaks locale-specific product display.
    """
    issues: list[str] = []

    store_files = list(manifest_dir.rglob("WebStore*.xml"))
    store_files += list(manifest_dir.rglob("WebStore*.json"))

    if not store_files:
        return issues

    for f in store_files:
        try:
            if f.suffix == ".json":
                data = json.loads(f.read_text(encoding="utf-8"))
                records = data if isinstance(data, list) else data.get("records", [])
                for rec in records:
                    name = rec.get("Name", f.stem)
                    language = rec.get("Language", "")
                    if not language:
                        issues.append(
                            f"WebStore '{name}' has no Language field set. "
                            f"Set WebStore.Language to the store's primary locale "
                            f"(e.g., 'en_US', 'de', 'fr') to ensure correct locale-specific "
                            f"product display and storefront translations."
                        )
            elif f.suffix == ".xml":
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
                name = (
                    root.findtext("sf:Name", namespaces=ns)
                    or root.findtext("Name")
                    or f.stem
                )
                language = (
                    root.findtext("sf:Language", namespaces=ns)
                    or root.findtext("Language")
                    or ""
                )
                if not language:
                    issues.append(
                        f"WebStore '{name}' has no Language field set. "
                        f"Set WebStore.Language to the store's primary locale "
                        f"to ensure correct locale-specific product display."
                    )
        except Exception:
            pass

    return issues


def check_currency_configuration(manifest_dir: Path) -> list[str]:
    """Warn if multiple WebStore records exist but currency configuration is not present.

    When multiple WebStores are found in the metadata, org-level multi-currency
    should be enabled. This check looks for CurrencyType metadata files as a
    proxy for multi-currency enablement. Absence of CurrencyType metadata in a
    multi-store deployment may indicate multi-currency was not enabled.
    """
    issues: list[str] = []

    store_files = list(manifest_dir.rglob("WebStore*.xml"))
    store_files += list(manifest_dir.rglob("WebStore*.json"))

    if len(store_files) < 2:
        return issues  # Single store — multi-currency may not be needed

    currency_files = list(manifest_dir.rglob("*.currency-meta.xml"))
    currency_files += list(manifest_dir.rglob("CurrencyType*.xml"))
    currency_files += list(manifest_dir.rglob("currencies.json"))

    if not currency_files:
        issues.append(
            f"Found {len(store_files)} WebStore records but no CurrencyType metadata. "
            f"For multi-store deployments that serve different regions, org-level "
            f"multi-currency must be enabled before price books and carts are created. "
            f"Verify whether multi-currency is enabled in Setup > Company Information > Currencies."
        )

    return issues


def check_entitlement_policy_coverage(manifest_dir: Path) -> list[str]:
    """Warn if WebStore records exist with no associated entitlement policies.

    Sharing a product catalog across multiple WebStores does not enforce product
    isolation between stores. Each WebStore must have at least one entitlement
    policy configured. This check looks for CommerceEntitlementPolicy metadata
    files and warns if none exist when WebStore records are present.
    """
    issues: list[str] = []

    store_files = list(manifest_dir.rglob("WebStore*.xml"))
    store_files += list(manifest_dir.rglob("WebStore*.json"))

    if not store_files:
        return issues

    entitlement_files = list(manifest_dir.rglob("CommerceEntitlementPolicy*.xml"))
    entitlement_files += list(manifest_dir.rglob("CommerceEntitlementPolicy*.json"))
    entitlement_files += list(manifest_dir.rglob("EntitlementPolicy*.xml"))

    if store_files and not entitlement_files:
        issues.append(
            f"Found {len(store_files)} WebStore record(s) but no CommerceEntitlementPolicy "
            f"metadata. Sharing a product catalog across WebStores does not restrict product "
            f"access between stores — entitlement policies are required for each store to "
            f"control which products are visible and orderable by which buyers. "
            f"Add CommerceEntitlementPolicy records for each WebStore."
        )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def check_multi_store_architecture(manifest_dir: Path) -> list[str]:
    """Run all multi-store architecture checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_web_store_catalog_multiplicity(manifest_dir))
    issues.extend(check_product_catalog_count(manifest_dir))
    issues.extend(check_web_store_language_field(manifest_dir))
    issues.extend(check_currency_configuration(manifest_dir))
    issues.extend(check_entitlement_policy_coverage(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_multi_store_architecture(manifest_dir)

    if args.json:
        print(json.dumps(issues, indent=2))
        return 1 if issues else 0

    if not issues:
        print("No multi-store architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
