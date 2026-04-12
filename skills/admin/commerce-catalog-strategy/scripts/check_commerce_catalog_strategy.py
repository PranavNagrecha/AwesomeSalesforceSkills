#!/usr/bin/env python3
"""Checker script for Commerce Catalog Strategy skill.

Validates a Salesforce metadata export or SOQL CSV export for common
Commerce catalog strategy issues:
  - Searchable field count exceeding the 50-field platform limit
  - Category hierarchy depth exceeding 4 levels
  - Product catalog categories with names that suggest storefront
    vocabulary (numeric codes, abbreviations) rather than system-of-record terms
  - Missing entitlement policy records for multi-storefront orgs

Usage:
    python3 check_commerce_catalog_strategy.py --help
    python3 check_commerce_catalog_strategy.py --manifest-dir path/to/metadata
    python3 check_commerce_catalog_strategy.py --attribute-csv path/to/attributes.csv
    python3 check_commerce_catalog_strategy.py --category-csv path/to/categories.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Platform limit for searchable fields per product.
SEARCHABLE_FIELD_LIMIT = 50
# Internal warning threshold to leave a safety buffer.
SEARCHABLE_FIELD_WARNING_THRESHOLD = 45
# Maximum recommended taxonomy depth before navigation UX degrades.
MAX_TAXONOMY_DEPTH = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Commerce catalog strategy artifacts for common platform limit "
            "violations and anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata export (optional).",
    )
    parser.add_argument(
        "--attribute-csv",
        default=None,
        help=(
            "Path to a CSV export of product attributes. "
            "Expected columns: AttributeName, IsSearchable (true/false), "
            "IsFilterable (true/false). "
            "Checks searchable field count against the 50-field limit."
        ),
    )
    parser.add_argument(
        "--category-csv",
        default=None,
        help=(
            "Path to a CSV export of product catalog categories. "
            "Expected columns: CategoryName, ParentCategoryName. "
            "Checks hierarchy depth and naming patterns."
        ),
    )
    return parser.parse_args()


def check_searchable_field_count(attribute_csv_path: Path) -> list[str]:
    """Check that the searchable field count does not exceed 50.

    Reads a CSV with at minimum the columns:
        AttributeName, IsSearchable

    Returns a list of issue strings.
    """
    issues: list[str] = []

    if not attribute_csv_path.exists():
        issues.append(f"Attribute CSV not found: {attribute_csv_path}")
        return issues

    searchable_fields: list[str] = []

    try:
        with attribute_csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                issues.append(f"Attribute CSV appears empty: {attribute_csv_path}")
                return issues

            # Normalize column names for case-insensitive matching.
            normalized_fields = {col.strip().lower(): col for col in reader.fieldnames}

            searchable_col = normalized_fields.get("issearchable")
            name_col = normalized_fields.get("attributename")

            if searchable_col is None:
                issues.append(
                    "Attribute CSV is missing required column 'IsSearchable'. "
                    "Cannot validate searchable field count."
                )
                return issues

            for row in reader:
                is_searchable_raw = row.get(searchable_col, "").strip().lower()
                if is_searchable_raw in ("true", "1", "yes"):
                    attr_name = row.get(name_col, "<unknown>").strip() if name_col else "<unknown>"
                    searchable_fields.append(attr_name)

    except csv.Error as exc:
        issues.append(f"Failed to parse attribute CSV: {exc}")
        return issues

    count = len(searchable_fields)

    if count > SEARCHABLE_FIELD_LIMIT:
        issues.append(
            f"CRITICAL: Searchable field count is {count}, which exceeds the platform "
            f"limit of {SEARCHABLE_FIELD_LIMIT}. The next search index rebuild will fail "
            f"silently, causing stale or missing search results. "
            f"Reduce searchable fields by reclassifying lower-priority attributes as "
            f"filterable-only or display-only. "
            f"Over-limit fields: {', '.join(searchable_fields[SEARCHABLE_FIELD_LIMIT:])}"
        )
    elif count > SEARCHABLE_FIELD_WARNING_THRESHOLD:
        issues.append(
            f"WARNING: Searchable field count is {count} (limit: {SEARCHABLE_FIELD_LIMIT}). "
            f"Approaching the platform limit. Avoid adding new searchable attributes "
            f"without reclassifying existing ones. "
            f"Recommended internal threshold: {SEARCHABLE_FIELD_WARNING_THRESHOLD}."
        )
    else:
        print(
            f"OK: Searchable field count is {count} / {SEARCHABLE_FIELD_LIMIT} "
            f"(warning threshold: {SEARCHABLE_FIELD_WARNING_THRESHOLD})."
        )

    return issues


def check_category_hierarchy(category_csv_path: Path) -> list[str]:
    """Check product catalog category hierarchy depth and naming patterns.

    Reads a CSV with at minimum the columns:
        CategoryName, ParentCategoryName (empty string for root categories)

    Returns a list of issue strings.
    """
    issues: list[str] = []

    if not category_csv_path.exists():
        issues.append(f"Category CSV not found: {category_csv_path}")
        return issues

    # Build parent map: child_name -> parent_name
    parent_map: dict[str, str] = {}
    all_categories: list[str] = []

    try:
        with category_csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                issues.append(f"Category CSV appears empty: {category_csv_path}")
                return issues

            normalized_fields = {col.strip().lower(): col for col in reader.fieldnames}
            name_col = normalized_fields.get("categoryname")
            parent_col = normalized_fields.get("parentcategoryname")

            if name_col is None:
                issues.append(
                    "Category CSV is missing required column 'CategoryName'. "
                    "Cannot validate hierarchy depth."
                )
                return issues

            for row in reader:
                cat_name = row.get(name_col, "").strip()
                parent_name = row.get(parent_col, "").strip() if parent_col else ""
                if cat_name:
                    parent_map[cat_name] = parent_name
                    all_categories.append(cat_name)

    except csv.Error as exc:
        issues.append(f"Failed to parse category CSV: {exc}")
        return issues

    def get_depth(cat: str, depth: int = 1, visited: set[str] | None = None) -> int:
        """Recursively compute the depth of a category in the hierarchy."""
        if visited is None:
            visited = set()
        if cat in visited:
            return depth  # Cycle guard
        visited.add(cat)
        parent = parent_map.get(cat, "")
        if not parent:
            return depth
        return get_depth(parent, depth + 1, visited)

    deep_categories: list[tuple[str, int]] = []
    for cat in all_categories:
        depth = get_depth(cat)
        if depth > MAX_TAXONOMY_DEPTH:
            deep_categories.append((cat, depth))

    if deep_categories:
        deep_list = "; ".join(f"'{name}' (depth {d})" for name, d in deep_categories[:10])
        issues.append(
            f"Taxonomy depth exceeds recommended maximum of {MAX_TAXONOMY_DEPTH} levels "
            f"for {len(deep_categories)} category/categories. Deep hierarchies degrade "
            f"storefront navigation UX and increase maintenance complexity. "
            f"Consider flattening and using faceted filtering instead. "
            f"Deep categories (first 10): {deep_list}"
        )
    else:
        print(
            f"OK: Category hierarchy depth is within the recommended maximum "
            f"of {MAX_TAXONOMY_DEPTH} levels for all {len(all_categories)} categories."
        )

    # Check for naming patterns that suggest internal codes rather than
    # system-of-record vocabulary (all-caps abbreviations, numeric-heavy names).
    suspicious_names: list[str] = []
    for cat in all_categories:
        # Flag categories that are predominantly uppercase letters and digits
        # with no spaces — typical of internal code patterns (e.g., "AX-241-C").
        stripped = cat.replace("-", "").replace("_", "").replace(" ", "")
        if len(stripped) >= 4 and stripped.isupper() and any(c.isdigit() for c in stripped):
            suspicious_names.append(cat)

    if suspicious_names:
        issues.append(
            f"Possible internal-code naming detected in {len(suspicious_names)} category "
            f"name(s): {', '.join(suspicious_names[:10])}. "
            f"Product catalog category names should reflect product nature in natural "
            f"language, not internal codes. Buyers cannot search by partial code tokens "
            f"due to full-token matching constraints."
        )

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Check a Salesforce metadata directory for Commerce catalog strategy issues.

    Looks for:
    - Presence of WebStoreCatalog metadata (warns if multiple found without
      corresponding entitlement policy metadata)
    - Any Commerce-related metadata that suggests catalog configuration has
      been applied without a strategy document (heuristic check only)
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for WebStoreCatalog XML files (exported via SFDX metadata retrieve).
    web_store_catalog_files = list(manifest_dir.rglob("*WebStoreCatalog*"))
    if web_store_catalog_files:
        print(
            f"INFO: Found {len(web_store_catalog_files)} WebStoreCatalog metadata file(s). "
            f"Verify that each store has a distinct storefront catalog and that entitlement "
            f"policies are configured for product visibility isolation."
        )

    # Check for entitlement policy metadata.
    entitlement_files = list(manifest_dir.rglob("*BuyerGroup*")) + list(
        manifest_dir.rglob("*EntitlementPolicy*")
    )
    if web_store_catalog_files and not entitlement_files:
        issues.append(
            "WebStoreCatalog metadata found but no BuyerGroup or EntitlementPolicy "
            "metadata detected. Product catalog visibility is org-wide by default — "
            "products not in a storefront catalog are still accessible via direct URL. "
            "Confirm that entitlement policies have been configured for product "
            "visibility control before go-live."
        )

    if not web_store_catalog_files and not entitlement_files:
        print(
            "INFO: No Commerce catalog metadata found in manifest directory. "
            "If this is a pre-configuration strategy review, this is expected."
        )

    return issues


def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    ran_any_check = False

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_manifest_dir(manifest_dir))
        ran_any_check = True

    if args.attribute_csv:
        attribute_csv_path = Path(args.attribute_csv)
        all_issues.extend(check_searchable_field_count(attribute_csv_path))
        ran_any_check = True

    if args.category_csv:
        category_csv_path = Path(args.category_csv)
        all_issues.extend(check_category_hierarchy(category_csv_path))
        ran_any_check = True

    if not ran_any_check:
        print(
            "No input provided. Specify at least one of: "
            "--manifest-dir, --attribute-csv, --category-csv\n"
            "Run with --help for usage details."
        )
        return 0

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
