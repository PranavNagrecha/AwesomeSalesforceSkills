#!/usr/bin/env python3
"""Checker script for Commerce Product Catalog skill.

Checks Salesforce metadata and SOQL export CSV files for common
Commerce Product Catalog configuration issues:
  - Missing WebStoreCatalog records (store not linked to a catalog)
  - Multiple WebStoreCatalog records for the same WebStore (constraint violation risk)
  - ProductCategoryProduct records referencing inactive Product2 records
  - CommerceEntitlementProduct records with no corresponding ProductCategoryProduct (entitlement
    but no category assignment — product is accessible but not browseable)
  - Products assigned to more than a threshold number of entitlement policies (approaching the
    2,000 buyer group search index cap)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_product_catalog.py [--help]
    python3 check_commerce_product_catalog.py --manifest-dir path/to/metadata
    python3 check_commerce_product_catalog.py --csv-dir path/to/soql/exports
    python3 check_commerce_product_catalog.py --entitlement-cap 1800

Input modes:
    --manifest-dir  Root directory containing Salesforce metadata XML (e.g., sfdx project).
                    The checker looks for *WebStore*, *ProductCatalog*, and related XML files.
    --csv-dir       Directory containing SOQL export CSV files named after their object
                    (e.g., WebStoreCatalog.csv, ProductCategoryProduct.csv,
                    CommerceEntitlementProduct.csv, Product2.csv).

At least one of --manifest-dir or --csv-dir must point to an existing location with readable files.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set


# ── constants ──────────────────────────────────────────────────────────────────

DEFAULT_ENTITLEMENT_CAP = 1800  # warn below the hard 2,000 limit to give headroom
REQUIRED_CSV_NAMES = [
    "WebStoreCatalog",
    "ProductCategoryProduct",
    "CommerceEntitlementProduct",
    "Product2",
]


# ── argument parsing ───────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check B2B/B2C Commerce product catalog configuration for common issues. "
            "Reads SOQL export CSVs or scans Salesforce metadata XML."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata / sfdx project.",
    )
    parser.add_argument(
        "--csv-dir",
        default=None,
        help=(
            "Directory containing SOQL export CSV files "
            "(WebStoreCatalog.csv, ProductCategoryProduct.csv, etc.)."
        ),
    )
    parser.add_argument(
        "--entitlement-cap",
        type=int,
        default=DEFAULT_ENTITLEMENT_CAP,
        help=(
            f"Warn when a product is assigned to this many or more entitlement policies "
            f"(default: {DEFAULT_ENTITLEMENT_CAP}; hard platform limit is 2,000)."
        ),
    )
    return parser.parse_args()


# ── CSV helpers ────────────────────────────────────────────────────────────────

def read_csv(path: Path) -> List[Dict[str, str]]:
    """Read a CSV file and return rows as a list of dicts. Returns [] if file not found."""
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def normalise(value: Optional[str]) -> str:
    return (value or "").strip()


# ── check functions ────────────────────────────────────────────────────────────

def check_web_store_catalog(rows: List[Dict[str, str]]) -> List[str]:
    """
    Check WebStoreCatalog rows for:
      1. Zero records (store not linked to any catalog)
      2. Multiple records for the same WebStoreId (platform constraint violation)
    """
    issues: List[str] = []

    if not rows:
        issues.append(
            "WebStoreCatalog: no records found. "
            "The store must be linked to exactly one ProductCatalog via WebStoreCatalog."
        )
        return issues

    store_counts: Dict[str, int] = defaultdict(int)
    for row in rows:
        store_id = normalise(row.get("WebStoreId") or row.get("webstoreid") or "")
        if store_id:
            store_counts[store_id] += 1

    for store_id, count in store_counts.items():
        if count > 1:
            issues.append(
                f"WebStoreCatalog: WebStoreId {store_id!r} has {count} WebStoreCatalog records. "
                "The platform allows only one ProductCatalog per store. "
                "Delete the extra record(s) to avoid undefined behavior."
            )

    return issues


def check_inactive_products_in_categories(
    product_category_rows: List[Dict[str, str]],
    product_rows: List[Dict[str, str]],
) -> List[str]:
    """
    Warn when ProductCategoryProduct references a Product2 with IsActive = false.
    Inactive products are excluded from storefront browsing after the next index rebuild.
    """
    issues: List[str] = []

    inactive_ids: Set[str] = set()
    for row in product_rows:
        pid = normalise(row.get("Id") or row.get("id") or "")
        active = normalise(row.get("IsActive") or row.get("isactive") or "true").lower()
        if pid and active in ("false", "0", "no"):
            inactive_ids.add(pid)

    if not inactive_ids:
        return issues

    for row in product_category_rows:
        prod_id = normalise(row.get("ProductId") or row.get("productid") or "")
        cat_id = normalise(row.get("ProductCategoryId") or row.get("productcategoryid") or "")
        if prod_id in inactive_ids:
            issues.append(
                f"ProductCategoryProduct: Product2 {prod_id!r} is inactive but is still assigned "
                f"to category {cat_id!r}. Inactive products are hidden from storefront buyers. "
                "Remove the category assignment or reactivate the product."
            )

    return issues


def check_entitlement_without_category(
    entitlement_rows: List[Dict[str, str]],
    product_category_rows: List[Dict[str, str]],
) -> List[str]:
    """
    Warn when a product has CommerceEntitlementProduct records but no ProductCategoryProduct record.
    Such products are buyer-accessible via direct URL / API but are not browseable by category.
    """
    issues: List[str] = []

    categorised_products: Set[str] = {
        normalise(row.get("ProductId") or row.get("productid") or "")
        for row in product_category_rows
        if normalise(row.get("ProductId") or row.get("productid") or "")
    }

    entitled_products: Set[str] = {
        normalise(row.get("ProductId") or row.get("productid") or "")
        for row in entitlement_rows
        if normalise(row.get("ProductId") or row.get("productid") or "")
    }

    for prod_id in entitled_products - categorised_products:
        issues.append(
            f"CommerceEntitlementProduct: Product2 {prod_id!r} is granted via an entitlement "
            "policy but has no ProductCategoryProduct record. "
            "The product can be purchased via direct link but buyers cannot browse to it by category."
        )

    return issues


def check_entitlement_policy_count(
    entitlement_rows: List[Dict[str, str]],
    cap: int,
) -> List[str]:
    """
    Warn when a product is assigned to >= cap entitlement policies.
    The hard platform limit is 2,000; exceeding it silently excludes the product from search.
    """
    issues: List[str] = []

    policy_count_per_product: Dict[str, Set[str]] = defaultdict(set)
    for row in entitlement_rows:
        prod_id = normalise(row.get("ProductId") or row.get("productid") or "")
        policy_id = normalise(
            row.get("CommerceEntitlementPolicyId")
            or row.get("commerceentitlementpolicyid")
            or row.get("PolicyId")
            or row.get("policyid")
            or ""
        )
        if prod_id and policy_id:
            policy_count_per_product[prod_id].add(policy_id)

    for prod_id, policies in policy_count_per_product.items():
        count = len(policies)
        if count >= cap:
            issues.append(
                f"CommerceEntitlementProduct: Product2 {prod_id!r} is assigned to {count} "
                f"entitlement policies (warning threshold: {cap}; hard search index limit: 2,000). "
                "Products assigned to more than 2,000 buyer groups are silently excluded from "
                "storefront search results for excess groups. Consolidate buyer groups."
            )

    return issues


def check_manifest_dir(manifest_dir: Path) -> List[str]:
    """
    Scan a Salesforce metadata directory for WebStore and ProductCatalog related XML files
    and report any that are missing.
    """
    issues: List[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    xml_files = list(manifest_dir.rglob("*.xml"))
    if not xml_files:
        issues.append(
            f"No XML metadata files found under {manifest_dir}. "
            "Ensure --manifest-dir points to an sfdx or metadata API project root."
        )
        return issues

    found_names = {f.stem.lower() for f in xml_files}

    # Check for expected Commerce-related metadata file stems
    expected_stems = {
        "webstore": "WebStore configuration",
        "webstorecatalog": "WebStoreCatalog junction",
        "productcatalog": "ProductCatalog definition",
    }
    for stem, description in expected_stems.items():
        if not any(stem in name for name in found_names):
            issues.append(
                f"Metadata: No XML file found matching '{stem}' ({description}). "
                "If this project manages Commerce configuration, the file may be missing from source."
            )

    return issues


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    args = parse_args()

    if not args.manifest_dir and not args.csv_dir:
        print(
            "ERROR: Specify at least one of --manifest-dir or --csv-dir.",
            file=sys.stderr,
        )
        return 2

    all_issues: List[str] = []

    # ── CSV-based checks ───────────────────────────────────────────────────────
    if args.csv_dir:
        csv_dir = Path(args.csv_dir)
        if not csv_dir.exists():
            all_issues.append(f"CSV directory not found: {csv_dir}")
        else:
            web_store_catalog_rows = read_csv(csv_dir / "WebStoreCatalog.csv")
            product_category_rows = read_csv(csv_dir / "ProductCategoryProduct.csv")
            entitlement_rows = read_csv(csv_dir / "CommerceEntitlementProduct.csv")
            product_rows = read_csv(csv_dir / "Product2.csv")

            all_issues.extend(check_web_store_catalog(web_store_catalog_rows))
            all_issues.extend(
                check_inactive_products_in_categories(product_category_rows, product_rows)
            )
            all_issues.extend(
                check_entitlement_without_category(entitlement_rows, product_category_rows)
            )
            all_issues.extend(
                check_entitlement_policy_count(entitlement_rows, args.entitlement_cap)
            )

    # ── Metadata XML checks ────────────────────────────────────────────────────
    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_manifest_dir(manifest_dir))

    # ── Report ─────────────────────────────────────────────────────────────────
    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
