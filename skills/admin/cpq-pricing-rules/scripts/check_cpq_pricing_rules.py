#!/usr/bin/env python3
"""Checker script for CPQ Pricing Rules skill.

Validates Salesforce CPQ pricing configuration metadata for common issues:
  - Duplicate Evaluation Order values across active Price Rules
  - Price Rules missing Conditions or Actions
  - Block Price records on products that also have Discount Schedules (double-discount risk)
  - Contracted Price records missing Account or Product references
  - Price Action targets that sit high in the waterfall (early fields that get overwritten)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_pricing_rules.py [--help]
    python3 check_cpq_pricing_rules.py --manifest-dir path/to/metadata
    python3 check_cpq_pricing_rules.py --csv-dir path/to/exported/csv/files

The checker works in two modes:
  1. Metadata XML mode (--manifest-dir): Scans Salesforce DX or MDAPI metadata files
     for CPQ custom object records exported as XML.
  2. CSV mode (--csv-dir): Scans CSV exports of CPQ objects (e.g., from Data Loader).
     Expected files: PriceRule.csv, PriceCondition.csv, PriceAction.csv,
                     DiscountSchedule.csv, BlockPrice.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from collections import defaultdict
from xml.etree import ElementTree

# CPQ API names used as checks
WATERFALL_EARLY_FIELDS = {
    "SBQQ__ListPrice__c",
    "SBQQ__RegularPrice__c",
    "SBQQ__CustomerPrice__c",
}
SAFE_FINAL_PRICE_FIELDS = {
    "SBQQ__SpecialPrice__c",
    "SBQQ__NetPrice__c",
    "SBQQ__Discount__c",
    "SBQQ__AdditionalDiscount__c",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce CPQ pricing configuration for common issues. "
            "Scans metadata XML or CSV exports for duplicate evaluation orders, "
            "missing conditions/actions, double-discount risks, and unsafe price action targets."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata (MDAPI or SFDX format).",
    )
    parser.add_argument(
        "--csv-dir",
        default=None,
        help="Directory containing CSV exports: PriceRule.csv, PriceCondition.csv, "
             "PriceAction.csv, DiscountSchedule.csv, BlockPrice.csv",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# XML metadata helpers
# ---------------------------------------------------------------------------

def _xml_field(root: ElementTree.Element, tag: str, ns: str = "") -> str:
    """Return text of first matching tag, or empty string."""
    ns_prefix = f"{{{ns}}}" if ns else ""
    el = root.find(f".//{ns_prefix}{tag}")
    return (el.text or "").strip() if el is not None else ""


def load_xml_records(metadata_dir: Path, object_name: str) -> list[dict]:
    """Load custom object records from MDAPI-style XML under metadata_dir."""
    records: list[dict] = []
    search_patterns = [
        f"**/{object_name}/*.xml",
        f"**/{object_name}/**/*.xml",
    ]
    found_files: list[Path] = []
    for pattern in search_patterns:
        found_files.extend(metadata_dir.glob(pattern))

    for xml_file in found_files:
        try:
            tree = ElementTree.parse(xml_file)
            root = tree.getroot()
            # Extract namespace if present
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0].lstrip("{")
            record: dict = {"_file": str(xml_file)}
            for child in root:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                record[tag] = (child.text or "").strip()
            records.append(record)
        except ElementTree.ParseError:
            pass  # skip malformed files
    return records


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def load_csv(csv_path: Path) -> list[dict]:
    """Load a CSV file and return list of row dicts. Returns empty list if file missing."""
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_duplicate_evaluation_orders(price_rules: list[dict]) -> list[str]:
    """Detect active Price Rules sharing the same Evaluation Order value."""
    issues: list[str] = []
    order_map: dict[str, list[str]] = defaultdict(list)
    for rule in price_rules:
        active = rule.get("SBQQ__Active__c", rule.get("Active", "true"))
        if str(active).lower() in ("false", "0"):
            continue
        order = rule.get("SBQQ__EvaluationOrder__c", rule.get("EvaluationOrder", ""))
        name = rule.get("Name", rule.get("_file", "unknown"))
        if order:
            order_map[order].append(name)
    for order, names in order_map.items():
        if len(names) > 1:
            issues.append(
                f"DUPLICATE EVALUATION ORDER {order}: Price Rules {names} share the same "
                f"Evaluation Order. CPQ execution sequence is undefined. Assign unique values."
            )
    return issues


def check_rules_missing_conditions_or_actions(
    price_rules: list[dict],
    conditions: list[dict],
    actions: list[dict],
) -> list[str]:
    """Detect active Price Rules that have no Conditions or no Actions."""
    issues: list[str] = []

    condition_rule_ids: set[str] = set()
    for cond in conditions:
        rid = cond.get("SBQQ__Rule__c", cond.get("Rule", ""))
        if rid:
            condition_rule_ids.add(rid)

    action_rule_ids: set[str] = set()
    for action in actions:
        rid = action.get("SBQQ__Rule__c", action.get("Rule", ""))
        if rid:
            action_rule_ids.add(rid)

    for rule in price_rules:
        active = rule.get("SBQQ__Active__c", rule.get("Active", "true"))
        if str(active).lower() in ("false", "0"):
            continue
        rule_id = rule.get("Id", rule.get("_file", ""))
        name = rule.get("Name", rule_id or "unknown")

        # If we have no relational data (flat CSV without IDs), skip relational checks
        if not rule_id or not (condition_rule_ids or action_rule_ids):
            continue

        if rule_id not in condition_rule_ids:
            issues.append(
                f"MISSING CONDITIONS: Price Rule '{name}' (Id: {rule_id}) has no "
                f"Price Condition records. Rule will never fire."
            )
        if rule_id not in action_rule_ids:
            issues.append(
                f"MISSING ACTIONS: Price Rule '{name}' (Id: {rule_id}) has no "
                f"Price Action records. Rule fires but does not change any field."
            )
    return issues


def check_unsafe_price_action_targets(actions: list[dict]) -> list[str]:
    """Warn when Price Actions target fields that sit early in the CPQ price waterfall."""
    issues: list[str] = []
    for action in actions:
        target = action.get("SBQQ__TargetField__c", action.get("TargetField", ""))
        rule_id = action.get("SBQQ__Rule__c", action.get("Rule", "unknown"))
        name = action.get("Name", f"action on rule {rule_id}")
        if target in WATERFALL_EARLY_FIELDS:
            issues.append(
                f"UNSAFE ACTION TARGET: Price Action '{name}' targets '{target}', which sits "
                f"early in the CPQ price waterfall and may be overwritten by later stages. "
                f"Consider targeting SBQQ__SpecialPrice__c or SBQQ__Discount__c instead."
            )
    return issues


def check_block_price_products_with_discount_schedules(
    block_prices: list[dict],
    products: list[dict],
) -> list[str]:
    """Detect products that have both Block Price records and a Discount Schedule (double-discount risk)."""
    issues: list[str] = []
    if not block_prices or not products:
        return issues

    # Build set of product IDs with block prices
    block_product_ids: set[str] = set()
    for bp in block_prices:
        pid = bp.get("SBQQ__Product__c", bp.get("Product", ""))
        if pid:
            block_product_ids.add(pid)

    for product in products:
        pid = product.get("Id", "")
        name = product.get("Name", pid or "unknown")
        discount_schedule = product.get(
            "SBQQ__DiscountSchedule__c",
            product.get("DiscountSchedule", ""),
        )
        if pid in block_product_ids and discount_schedule:
            issues.append(
                f"DOUBLE-DISCOUNT RISK: Product '{name}' (Id: {pid}) has both Block Price "
                f"records and a Discount Schedule ('{discount_schedule}'). Both apply during "
                f"the CPQ price waterfall, producing an unintended combined discount. "
                f"Remove the Discount Schedule from block-priced products unless stacking is intentional."
            )
    return issues


def check_contracted_prices_missing_account_or_product(
    contracted_prices: list[dict],
) -> list[str]:
    """Detect Contracted Price records missing required Account or Product reference."""
    issues: list[str] = []
    for cp in contracted_prices:
        account = cp.get("SBQQ__Account__c", cp.get("Account", ""))
        product = cp.get("SBQQ__Product__c", cp.get("Product", ""))
        name = cp.get("Name", cp.get("Id", "unknown"))
        if not account:
            issues.append(
                f"CONTRACTED PRICE MISSING ACCOUNT: Record '{name}' has no Account reference. "
                f"It will not match any quote and will never apply."
            )
        if not product:
            issues.append(
                f"CONTRACTED PRICE MISSING PRODUCT: Record '{name}' has no Product reference. "
                f"It will not match any quote line and will never apply."
            )
    return issues


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_checks_from_csv(csv_dir: Path) -> list[str]:
    """Run all checks using CSV exports from csv_dir."""
    issues: list[str] = []

    price_rules = load_csv(csv_dir / "PriceRule.csv")
    conditions = load_csv(csv_dir / "PriceCondition.csv")
    actions = load_csv(csv_dir / "PriceAction.csv")
    block_prices = load_csv(csv_dir / "BlockPrice.csv")
    contracted_prices = load_csv(csv_dir / "ContractedPrice.csv")
    products = load_csv(csv_dir / "Product2.csv")

    if not any([price_rules, conditions, actions, block_prices, contracted_prices]):
        issues.append(
            f"No CPQ pricing CSV files found in '{csv_dir}'. "
            f"Expected: PriceRule.csv, PriceCondition.csv, PriceAction.csv, "
            f"BlockPrice.csv, ContractedPrice.csv"
        )
        return issues

    if price_rules:
        issues.extend(check_duplicate_evaluation_orders(price_rules))
        issues.extend(check_rules_missing_conditions_or_actions(price_rules, conditions, actions))
    if actions:
        issues.extend(check_unsafe_price_action_targets(actions))
    if block_prices:
        issues.extend(check_block_price_products_with_discount_schedules(block_prices, products))
    if contracted_prices:
        issues.extend(check_contracted_prices_missing_account_or_product(contracted_prices))

    return issues


def run_checks_from_metadata(manifest_dir: Path) -> list[str]:
    """Run checks against MDAPI/SFDX metadata XML in manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    price_rules = load_xml_records(manifest_dir, "SBQQ__PriceRule__c")
    conditions = load_xml_records(manifest_dir, "SBQQ__PriceCondition__c")
    actions = load_xml_records(manifest_dir, "SBQQ__PriceAction__c")
    block_prices = load_xml_records(manifest_dir, "SBQQ__BlockPrice__c")
    contracted_prices = load_xml_records(manifest_dir, "SBQQ__ContractedPrice__c")
    products = load_xml_records(manifest_dir, "Product2")

    if price_rules:
        issues.extend(check_duplicate_evaluation_orders(price_rules))
        issues.extend(check_rules_missing_conditions_or_actions(price_rules, conditions, actions))
    if actions:
        issues.extend(check_unsafe_price_action_targets(actions))
    if block_prices:
        issues.extend(check_block_price_products_with_discount_schedules(block_prices, products))
    if contracted_prices:
        issues.extend(check_contracted_prices_missing_account_or_product(contracted_prices))

    if not any([price_rules, conditions, actions, block_prices, contracted_prices]):
        issues.append(
            "No CPQ pricing metadata found in manifest directory. "
            "Ensure metadata is exported with SBQQ__ object types included, "
            "or use --csv-dir with Data Loader CSV exports."
        )

    return issues


def main() -> int:
    args = parse_args()

    if args.csv_dir:
        issues = run_checks_from_csv(Path(args.csv_dir))
    elif args.manifest_dir:
        issues = run_checks_from_metadata(Path(args.manifest_dir))
    else:
        # Default: try current directory as manifest
        issues = run_checks_from_metadata(Path("."))

    if not issues:
        print("No CPQ pricing issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
