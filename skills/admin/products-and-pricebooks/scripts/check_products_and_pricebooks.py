#!/usr/bin/env python3
"""Checker script for Products and Pricebooks skill.

Scans a Salesforce metadata directory for common configuration issues
related to Product2, Pricebook2, PricebookEntry, and Product Schedules.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_products_and_pricebooks.py [--help]
    python3 check_products_and_pricebooks.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Products and Pricebooks configuration for common issues. "
            "Scans XML metadata files in a Salesforce project directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_apex_hardcoded_standard_pricebook_id(manifest_dir: Path) -> list[str]:
    """Detect Apex classes and test classes that hardcode the Standard Pricebook ID."""
    issues: list[str] = []
    apex_dirs = [
        manifest_dir / "classes",
        manifest_dir / "triggers",
    ]

    # Standard Pricebook IDs always start with '01s' (15 or 18 char)
    hardcoded_pattern = re.compile(r"['\"]01s[A-Za-z0-9]{12,15}['\"]")

    for apex_dir in apex_dirs:
        if not apex_dir.exists():
            continue
        for apex_file in sorted(apex_dir.glob("*.cls")):
            content = apex_file.read_text(encoding="utf-8", errors="replace")
            if hardcoded_pattern.search(content):
                issues.append(
                    f"POTENTIAL ISSUE [{apex_file.name}]: Possible hardcoded "
                    "Standard Pricebook ID detected (string starting with '01s'). "
                    "Use Test.getStandardPricebookId() in test classes and a SOQL "
                    "query or Custom Metadata reference in non-test Apex instead of "
                    "a hardcoded record ID."
                )
    return issues


def check_product_schedules_settings(manifest_dir: Path) -> list[str]:
    """Check if Product Schedules Settings are referenced in any object or settings config."""
    issues: list[str] = []
    settings_dir = manifest_dir / "settings"
    if not settings_dir.exists():
        return issues

    product_settings_file = settings_dir / "Product.settings-meta.xml"
    if not product_settings_file.exists():
        return issues

    content = product_settings_file.read_text(encoding="utf-8", errors="replace")
    has_revenue = "<enableRevenueSchedules>true</enableRevenueSchedules>" in content
    has_quantity = "<enableQuantitySchedules>true</enableQuantitySchedules>" in content

    if not has_revenue and not has_quantity:
        issues.append(
            "INFO [Product.settings-meta.xml]: Neither Revenue Schedules nor "
            "Quantity Schedules appear to be enabled. If product-level scheduling "
            "(installment payments or phased delivery) is required, enable them in "
            "Setup > Products > Product Schedules Settings and re-deploy."
        )
    return issues


def check_pricebook_flow_assignment(manifest_dir: Path) -> list[str]:
    """Check for Flows that set Pricebook2Id on Opportunity."""
    issues: list[str] = []
    flow_dir = manifest_dir / "flows"
    if not flow_dir.exists():
        return issues

    pricebook_assignment_found = False
    for flow_file in sorted(flow_dir.glob("*.flow-meta.xml")):
        content = flow_file.read_text(encoding="utf-8", errors="replace")
        if "Pricebook2Id" in content and "<object>Opportunity</object>" in content:
            pricebook_assignment_found = True
            break

    if not pricebook_assignment_found:
        issues.append(
            "INFO: No Flow detected that sets Pricebook2Id on Opportunity. "
            "If the org uses multiple Pricebooks, consider automating Pricebook "
            "assignment on Opportunity creation (e.g., based on Account type or "
            "segment field) to prevent reps from selecting the wrong Pricebook."
        )
    return issues


def check_product_object_fls(manifest_dir: Path) -> list[str]:
    """Warn if Product2, Pricebook2, or PricebookEntry FLS is not visible in any profile."""
    issues: list[str] = []
    profiles_dir = manifest_dir / "profiles"
    if not profiles_dir.exists():
        return issues

    required_objects = {"Product2", "Pricebook2", "PricebookEntry"}
    objects_checked: set[str] = set()

    for profile_file in sorted(profiles_dir.glob("*.profile-meta.xml")):
        if "Admin" in profile_file.name or "System" in profile_file.name:
            continue  # skip admin profiles — focus on sales user profiles
        content = profile_file.read_text(encoding="utf-8", errors="replace")
        for obj in required_objects:
            if obj in content:
                objects_checked.add(obj)

    missing = required_objects - objects_checked
    if missing:
        issues.append(
            f"REVIEW: The following objects have no explicit FLS or CRUD grant "
            f"in non-admin profiles: {', '.join(sorted(missing))}. "
            "Sales reps who cannot read Pricebook2 or PricebookEntry records will "
            "see an empty product picker on Opportunities. Verify visibility grants "
            "for sales user profiles."
        )
    return issues


def check_validation_rules_on_opportunity_line_items(manifest_dir: Path) -> list[str]:
    """Flag validation rules on OpportunityLineItem referencing pricebook-sensitive fields."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    oli_dir = objects_dir / "OpportunityLineItem"
    if not oli_dir.exists():
        return issues

    val_dir = oli_dir / "validationRules"
    if not val_dir.exists():
        return issues

    pricebook_fields = {
        "PricebookEntryId", "UnitPrice", "ListPrice",
        "TotalPrice", "Quantity", "Product2Id",
    }

    for xml_file in sorted(val_dir.glob("*.validationRule-meta.xml")):
        content = xml_file.read_text(encoding="utf-8", errors="replace")
        for field in pricebook_fields:
            if field in content:
                issues.append(
                    f"REVIEW [{xml_file.name}]: Validation rule on OpportunityLineItem "
                    f"references '{field}', which is set by Pricebook/product selection. "
                    "Ensure this rule does not block product addition when the "
                    "Pricebook is switched or when the product is added via API/integration."
                )
                break

    return issues


def check_cpq_and_standard_pricebook_coexistence(manifest_dir: Path) -> list[str]:
    """Warn if CPQ metadata is present alongside standard product-catalog customizations."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    cpq_objects = list(objects_dir.glob("SBQQ__*"))
    if not cpq_objects:
        return issues

    standard_product_customizations = list(
        (objects_dir / "Product2").glob("**/*.field-meta.xml")
        if (objects_dir / "Product2").exists() else []
    )
    standard_pbe_customizations = list(
        (objects_dir / "PricebookEntry").glob("**/*.field-meta.xml")
        if (objects_dir / "PricebookEntry").exists() else []
    )

    if standard_product_customizations or standard_pbe_customizations:
        issues.append(
            "INFO: CPQ (SBQQ) metadata detected alongside custom fields on Product2 "
            "or PricebookEntry. Confirm whether these standard-object customizations "
            "are intended for use with CPQ or standard Pricebooks — some CPQ features "
            "bypass standard PricebookEntry pricing entirely. Verify that customizations "
            "apply to the correct quoting path."
        )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_products_and_pricebooks(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_hardcoded_standard_pricebook_id(manifest_dir))
    issues.extend(check_product_schedules_settings(manifest_dir))
    issues.extend(check_pricebook_flow_assignment(manifest_dir))
    issues.extend(check_product_object_fls(manifest_dir))
    issues.extend(check_validation_rules_on_opportunity_line_items(manifest_dir))
    issues.extend(check_cpq_and_standard_pricebook_coexistence(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_products_and_pricebooks(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
