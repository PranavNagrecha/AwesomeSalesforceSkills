#!/usr/bin/env python3
"""Checker script for Pricing Model Design skill.

Validates Salesforce CPQ pricing model configuration for common design issues:
  - Products with SBQQ__PricingMethod__c = 'Block' that also have a Discount Schedule
    (double-discount risk)
  - Block Price records with gaps or overlapping ranges per product/pricebook combination
  - Products with SBQQ__PricingMethod__c = 'Cost Plus Markup' that lack SBQQ__Cost__c
  - Discount Schedules with no Discount Tier records
  - Products with SBQQ__PricingMethod__c = 'Percent of Total' missing SBQQ__PercentOfTotalBase__c

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_pricing_model_design.py [--help]
    python3 check_pricing_model_design.py --csv-dir path/to/exported/csv/files
    python3 check_pricing_model_design.py --manifest-dir path/to/metadata

CSV mode expects:
    Product2.csv          — exported Product2 records including SBQQ__ pricing fields
    BlockPrice.csv        — exported SBQQ__BlockPrice__c records
    DiscountSchedule.csv  — exported SBQQ__DiscountSchedule__c records
    DiscountTier.csv      — exported SBQQ__DiscountTier__c records

Metadata mode scans SFDX/MDAPI XML for the same objects.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce CPQ pricing model design for common issues. "
            "Detects Block Pricing + Discount Schedule conflicts, Block Price range "
            "gaps/overlaps, Cost Plus Markup products missing cost, and "
            "Discount Schedules without tiers."
        ),
    )
    parser.add_argument(
        "--csv-dir",
        default=None,
        help=(
            "Directory containing CSV exports: Product2.csv, BlockPrice.csv, "
            "DiscountSchedule.csv, DiscountTier.csv"
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce DX or MDAPI metadata XML.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def load_csv(csv_path: Path) -> list[dict]:
    """Load a CSV file and return list of row dicts. Returns empty list if file is missing."""
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def load_xml_records(metadata_dir: Path, object_name: str) -> list[dict]:
    """Load records from MDAPI/SFDX XML under metadata_dir for the given CPQ object."""
    records: list[dict] = []
    for xml_file in metadata_dir.glob(f"**/{object_name}/*.xml"):
        try:
            tree = ElementTree.parse(xml_file)
            root = tree.getroot()
            record: dict = {"_file": str(xml_file)}
            for child in root:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                record[tag] = (child.text or "").strip()
            records.append(record)
        except ElementTree.ParseError:
            pass
    return records


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_block_priced_products_with_discount_schedule(
    products: list[dict],
) -> list[str]:
    """Detect products with Block Pricing Method AND an attached Discount Schedule.

    Both mechanisms apply during the CPQ price waterfall, causing unintended double-discounting.
    """
    issues: list[str] = []
    for product in products:
        pricing_method = product.get(
            "SBQQ__PricingMethod__c", product.get("PricingMethod", "")
        )
        discount_schedule = product.get(
            "SBQQ__DiscountSchedule__c", product.get("DiscountSchedule", "")
        )
        name = product.get("Name", product.get("_file", "unknown"))
        if pricing_method == "Block" and discount_schedule:
            issues.append(
                f"DOUBLE-DISCOUNT RISK: Product '{name}' has PricingMethod='Block' AND "
                f"a Discount Schedule ('{discount_schedule}') attached. Both apply during "
                f"the CPQ price waterfall. The Discount Schedule will reduce the block price "
                f"by its tier percentage. Remove the Discount Schedule unless stacking is "
                f"explicitly documented."
            )
    return issues


def check_block_price_range_integrity(block_prices: list[dict]) -> list[str]:
    """Detect gaps and overlaps in Block Price records per product/pricebook combination.

    Gaps cause CPQ to fall back to list price for quantities in the gap.
    Overlaps cause undefined tier-matching behavior.
    """
    issues: list[str] = []

    # Group records by product + pricebook
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for bp in block_prices:
        product_id = bp.get("SBQQ__Product__c", bp.get("Product", ""))
        pricebook_id = bp.get("SBQQ__Pricebook__c", bp.get("Pricebook", ""))
        key = (product_id, pricebook_id)
        groups[key].append(bp)

    for (product_id, pricebook_id), records in groups.items():
        group_label = f"Product '{product_id}' / Pricebook '{pricebook_id}'"

        # Parse and sort by lower bound
        parsed: list[tuple[float, float, dict]] = []
        for rec in records:
            try:
                lower = float(rec.get("SBQQ__LowerBound__c", rec.get("LowerBound", "0")) or 0)
                upper = float(rec.get("SBQQ__UpperBound__c", rec.get("UpperBound", "0")) or 0)
                parsed.append((lower, upper, rec))
            except (ValueError, TypeError):
                name = rec.get("Name", rec.get("_file", "unknown"))
                issues.append(
                    f"INVALID BLOCK PRICE BOUNDS: Record '{name}' for {group_label} "
                    f"has non-numeric LowerBound or UpperBound."
                )

        parsed.sort(key=lambda t: t[0])

        for i, (lower, upper, rec) in enumerate(parsed):
            name = rec.get("Name", rec.get("_file", f"record {i}"))

            # Check that lower <= upper
            if lower > upper:
                issues.append(
                    f"INVERTED RANGE: Block Price record '{name}' for {group_label} "
                    f"has LowerBound ({lower}) > UpperBound ({upper})."
                )
                continue

            if i > 0:
                prev_lower, prev_upper, prev_rec = parsed[i - 1]
                prev_name = prev_rec.get("Name", prev_rec.get("_file", f"record {i-1}"))

                # Check for overlap: current lower <= previous upper
                if lower <= prev_upper:
                    issues.append(
                        f"OVERLAPPING RANGES: Block Price records '{prev_name}' "
                        f"(upper={prev_upper}) and '{name}' (lower={lower}) for "
                        f"{group_label} overlap. CPQ tier-matching is undefined for "
                        f"quantities in the overlapping range."
                    )

                # Check for gap: current lower > previous upper + 1
                elif lower > prev_upper + 1:
                    issues.append(
                        f"RANGE GAP: Block Price records '{prev_name}' (upper={prev_upper}) "
                        f"and '{name}' (lower={lower}) for {group_label} leave a gap at "
                        f"quantities {int(prev_upper + 1)}–{int(lower - 1)}. CPQ falls back "
                        f"to list price for quantities in this gap."
                    )

    return issues


def check_cost_plus_markup_products_missing_cost(products: list[dict]) -> list[str]:
    """Detect Cost Plus Markup products that do not have SBQQ__Cost__c populated.

    Without a cost, the markup calculation produces $0 net price.
    """
    issues: list[str] = []
    for product in products:
        pricing_method = product.get(
            "SBQQ__PricingMethod__c", product.get("PricingMethod", "")
        )
        cost = product.get("SBQQ__Cost__c", product.get("Cost", ""))
        name = product.get("Name", product.get("_file", "unknown"))
        if pricing_method == "Cost Plus Markup" and not cost:
            issues.append(
                f"MISSING COST: Product '{name}' has PricingMethod='Cost Plus Markup' "
                f"but SBQQ__Cost__c is empty or zero. The CPQ engine will compute the "
                f"net price as markup-of-zero, producing $0. Populate SBQQ__Cost__c "
                f"before attaching this product to a quote."
            )
    return issues


def check_discount_schedules_without_tiers(
    schedules: list[dict],
    tiers: list[dict],
) -> list[str]:
    """Detect Discount Schedule records that have no associated Discount Tier records.

    A Discount Schedule with no tiers has no effect during CPQ calculation — it silently
    applies a 0% discount to all quantities.
    """
    issues: list[str] = []
    if not schedules:
        return issues

    # Build set of schedule IDs that have at least one tier
    schedule_ids_with_tiers: set[str] = set()
    for tier in tiers:
        schedule_id = tier.get(
            "SBQQ__Schedule__c", tier.get("Schedule", "")
        )
        if schedule_id:
            schedule_ids_with_tiers.add(schedule_id)

    for schedule in schedules:
        schedule_id = schedule.get("Id", "")
        name = schedule.get("Name", schedule.get("_file", "unknown"))
        # Only perform relational check when IDs are available
        if schedule_id and schedule_ids_with_tiers and schedule_id not in schedule_ids_with_tiers:
            issues.append(
                f"DISCOUNT SCHEDULE HAS NO TIERS: Discount Schedule '{name}' "
                f"(Id: {schedule_id}) has no SBQQ__DiscountTier__c records. "
                f"The schedule will silently apply 0% discount to all quantities. "
                f"Create at least one Discount Tier or remove the schedule from products."
            )

    return issues


def check_percent_of_total_missing_base(products: list[dict]) -> list[str]:
    """Detect Percent of Total products missing SBQQ__PercentOfTotalBase__c.

    Without a base, CPQ cannot determine which lines to sum — results are unpredictable.
    """
    issues: list[str] = []
    for product in products:
        pricing_method = product.get(
            "SBQQ__PricingMethod__c", product.get("PricingMethod", "")
        )
        base = product.get(
            "SBQQ__PercentOfTotalBase__c", product.get("PercentOfTotalBase", "")
        )
        name = product.get("Name", product.get("_file", "unknown"))
        if pricing_method == "Percent of Total" and not base:
            issues.append(
                f"MISSING PERCENT OF TOTAL BASE: Product '{name}' has "
                f"PricingMethod='Percent of Total' but SBQQ__PercentOfTotalBase__c "
                f"is empty. Set this field to 'Regular', 'All', or a product category "
                f"value to specify which quote lines are included in the pricing base."
            )
    return issues


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_checks_from_csv(csv_dir: Path) -> list[str]:
    """Run all checks from CSV exports in csv_dir."""
    issues: list[str] = []

    products = load_csv(csv_dir / "Product2.csv")
    block_prices = load_csv(csv_dir / "BlockPrice.csv")
    schedules = load_csv(csv_dir / "DiscountSchedule.csv")
    tiers = load_csv(csv_dir / "DiscountTier.csv")

    if not any([products, block_prices, schedules]):
        issues.append(
            f"No CPQ pricing model CSV files found in '{csv_dir}'. "
            f"Expected: Product2.csv, BlockPrice.csv, DiscountSchedule.csv, DiscountTier.csv"
        )
        return issues

    if products:
        issues.extend(check_block_priced_products_with_discount_schedule(products))
        issues.extend(check_cost_plus_markup_products_missing_cost(products))
        issues.extend(check_percent_of_total_missing_base(products))

    if block_prices:
        issues.extend(check_block_price_range_integrity(block_prices))

    if schedules:
        issues.extend(check_discount_schedules_without_tiers(schedules, tiers))

    return issues


def run_checks_from_metadata(manifest_dir: Path) -> list[str]:
    """Run all checks from MDAPI/SFDX XML metadata in manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    products = load_xml_records(manifest_dir, "Product2")
    block_prices = load_xml_records(manifest_dir, "SBQQ__BlockPrice__c")
    schedules = load_xml_records(manifest_dir, "SBQQ__DiscountSchedule__c")
    tiers = load_xml_records(manifest_dir, "SBQQ__DiscountTier__c")

    if not any([products, block_prices, schedules]):
        issues.append(
            "No CPQ pricing model metadata found in manifest directory. "
            "Ensure Product2, SBQQ__BlockPrice__c, SBQQ__DiscountSchedule__c, and "
            "SBQQ__DiscountTier__c are included in the metadata export, or use "
            "--csv-dir with Data Loader CSV exports."
        )
        return issues

    if products:
        issues.extend(check_block_priced_products_with_discount_schedule(products))
        issues.extend(check_cost_plus_markup_products_missing_cost(products))
        issues.extend(check_percent_of_total_missing_base(products))

    if block_prices:
        issues.extend(check_block_price_range_integrity(block_prices))

    if schedules:
        issues.extend(check_discount_schedules_without_tiers(schedules, tiers))

    return issues


def main() -> int:
    args = parse_args()

    if args.csv_dir:
        issues = run_checks_from_csv(Path(args.csv_dir))
    elif args.manifest_dir:
        issues = run_checks_from_metadata(Path(args.manifest_dir))
    else:
        issues = run_checks_from_metadata(Path("."))

    if not issues:
        print("No CPQ pricing model design issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
