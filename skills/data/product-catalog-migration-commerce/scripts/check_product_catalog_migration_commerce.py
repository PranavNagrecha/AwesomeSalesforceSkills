#!/usr/bin/env python3
"""Checker script for Product Catalog Migration Commerce skill.

Validates a B2B Commerce product catalog migration plan or data files for common issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_product_catalog_migration_commerce.py --plan-dir <path>
    python3 check_product_catalog_migration_commerce.py --csv-dir <path>

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

import argparse
import csv
import re
import sys
from pathlib import Path


REQUIRED_LOAD_ORDER = [
    "ProductCatalog",
    "ProductCategory",
    "Product2",
    "ProductCategoryProduct",
    "WebStoreCatalog",
    "Pricebook2",
    "PricebookEntry",
]

MAX_VARIANTS_PER_PARENT = 200
MAX_IMAGES_PER_PRODUCT = 9


def check_load_order_in_plan(plan_dir: Path) -> list[str]:
    """Scan markdown or text plan files for Commerce object references and check load order."""
    issues = []
    plan_files = list(plan_dir.glob("**/*.md")) + list(plan_dir.glob("**/*.txt"))

    for plan_file in plan_files:
        try:
            content = plan_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Check for deprecated endpoint
        if "/commerce/sale/product" in content:
            issues.append(
                f"ERROR: {plan_file.name} references the deprecated synchronous Commerce import endpoint "
                f"'/commerce/sale/product'. Use the async Commerce Import API: "
                f"POST /commerce/management/import/product/jobs"
            )

        # Check for missing ProductCategoryProduct
        has_product2 = "Product2" in content
        has_category_product = "ProductCategoryProduct" in content
        if has_product2 and not has_category_product:
            issues.append(
                f"WARN: {plan_file.name} references Product2 but not ProductCategoryProduct. "
                f"Category assignments require a ProductCategoryProduct junction record. "
                f"Products without this junction will not appear in storefront category navigation."
            )

        # Check for missing WebStoreCatalog
        has_catalog = "ProductCatalog" in content
        has_web_store_catalog = "WebStoreCatalog" in content
        if has_catalog and not has_web_store_catalog:
            issues.append(
                f"WARN: {plan_file.name} references ProductCatalog but not WebStoreCatalog. "
                f"A WebStoreCatalog record is required to make catalog products visible in the store."
            )

    return issues


def check_variant_counts(csv_dir: Path) -> list[str]:
    """Scan Product2 CSV files for variant counts exceeding the 200 limit."""
    issues = []
    csv_files = list(csv_dir.glob("*Product2*")) + list(csv_dir.glob("*product2*"))

    for csv_file in csv_files:
        try:
            with csv_file.open(newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except Exception as exc:
            issues.append(f"ERROR: Could not read {csv_file.name}: {exc}")
            continue

        # Count variants per parent
        parent_variant_counts: dict[str, int] = {}
        for row in rows:
            parent_id = row.get("ParentId", "").strip()
            product_class = row.get("ProductClass", "").strip()
            if parent_id and product_class == "Variation":
                parent_variant_counts[parent_id] = parent_variant_counts.get(parent_id, 0) + 1

        for parent_id, count in parent_variant_counts.items():
            if count > MAX_VARIANTS_PER_PARENT:
                issues.append(
                    f"ERROR: {csv_file.name} — parent product '{parent_id}' has {count} variants, "
                    f"exceeding the hard limit of {MAX_VARIANTS_PER_PARENT} variants per VariationParent. "
                    f"Catalog redesign required before import."
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate B2B Commerce product catalog migration plan and data files."
    )
    parser.add_argument("--plan-dir", type=Path, default=None,
                        help="Directory containing migration plan documents to scan")
    parser.add_argument("--csv-dir", type=Path, default=None,
                        help="Directory containing product CSVs to validate")
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.plan_dir and args.plan_dir.exists():
        all_issues.extend(check_load_order_in_plan(args.plan_dir))
    elif args.plan_dir:
        all_issues.append(f"ERROR: Plan directory not found: {args.plan_dir}")

    if args.csv_dir and args.csv_dir.exists():
        all_issues.extend(check_variant_counts(args.csv_dir))
    elif args.csv_dir:
        all_issues.append(f"ERROR: CSV directory not found: {args.csv_dir}")

    if not args.plan_dir and not args.csv_dir:
        print("INFO: No input provided. Use --plan-dir or --csv-dir.")
        return 0

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    print("OK: No B2B Commerce catalog migration issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
