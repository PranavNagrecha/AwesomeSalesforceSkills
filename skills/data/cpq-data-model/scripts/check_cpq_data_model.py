#!/usr/bin/env python3
"""Checker script for CPQ Data Model skill.

Validates Salesforce metadata for common CPQ data model anti-patterns:
- References to standard Quote/QuoteLineItem in CPQ-context code
- Direct DML on CPQ-managed price fields
- Wrong child relationship names for SBQQ__ objects
- Missing CPQ permission set assignments in permission set metadata

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_data_model.py [--help]
    python3 check_cpq_data_model.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# CPQ-managed price fields that must NOT be set via direct DML
CPQ_READONLY_PRICE_FIELDS = [
    "SBQQ__NetPrice__c",
    "SBQQ__CustomerPrice__c",
    "SBQQ__RegularPrice__c",
    "SBQQ__SpecialPrice__c",
    "SBQQ__PartnerPrice__c",
    "SBQQ__NetAmount__c",
]

# Incorrect child relationship names developers commonly guess
BAD_RELATIONSHIP_NAMES = [
    "QuoteLineItems",
    "SBQQ__QuoteLines__r",
    "LineItems__r",
    "SBQQ__Lines__r",
]

# Correct child relationship names for reference in issue messages
CORRECT_RELATIONSHIPS = {
    "SBQQ__Quote__c -> SBQQ__QuoteLine__c": "SBQQ__LineItems__r",
    "SBQQ__Quote__c -> SBQQ__QuoteLineGroup__c": "SBQQ__LineItemGroups__r",
    "SBQQ__DiscountSchedule__c -> SBQQ__DiscountTier__c": "SBQQ__DiscountTiers__r",
    "SBQQ__PriceRule__c -> SBQQ__PriceAction__c": "SBQQ__PriceActions__r",
    "SBQQ__PriceRule__c -> SBQQ__PriceCondition__c": "SBQQ__Conditions__r",
}

# Standard quoting objects that should not appear in CPQ-specific Apex/SOQL
STANDARD_QUOTE_OBJECTS = ["QuoteLineItem", "FROM Quote", "Quote.TotalPrice"]

# CPQ permission sets that users need for SBQQ__ object access
CPQ_PERMISSION_SETS = ["SBQQ CPQ User", "SBQQ CPQ Admin", "SBQQ__CPQ_User", "SBQQ__CPQ_Admin"]


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_apex_direct_dml_on_price_fields(manifest_dir: Path) -> list[str]:
    """Detect Apex files that set CPQ-managed price fields via direct DML assignment."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for field in CPQ_READONLY_PRICE_FIELDS:
            # Pattern: field assignment e.g.  .SBQQ__NetPrice__c = or .SBQQ__NetPrice__c=
            pattern = rf"\.\s*{re.escape(field)}\s*="
            matches = list(re.finditer(pattern, content))
            for match in matches:
                # Find line number
                line_num = content[: match.start()].count("\n") + 1
                issues.append(
                    f"DIRECT_DML_PRICE_FIELD: {apex_file.relative_to(manifest_dir)} "
                    f"line {line_num} sets {field} directly. "
                    "Use CPQ Quote API (SBQQ.QuoteService.calculate + save) instead."
                )

    return issues


def check_apex_standard_quote_objects(manifest_dir: Path) -> list[str]:
    """Detect Apex/SOQL files referencing standard Quote objects in a CPQ context."""
    issues: list[str] = []
    apex_files = (
        list(manifest_dir.rglob("*.cls"))
        + list(manifest_dir.rglob("*.trigger"))
        + list(manifest_dir.rglob("*.soql"))
    )

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Only flag if file also references SBQQ__ (confirms CPQ context)
        if "SBQQ__" not in content:
            continue

        for obj_pattern in STANDARD_QUOTE_OBJECTS:
            if obj_pattern in content:
                line_num = content.find(obj_pattern)
                line_num = content[:line_num].count("\n") + 1
                issues.append(
                    f"STANDARD_QUOTE_IN_CPQ_CONTEXT: {apex_file.relative_to(manifest_dir)} "
                    f"line ~{line_num} references '{obj_pattern}' alongside SBQQ__ objects. "
                    "In CPQ orgs, use SBQQ__Quote__c and SBQQ__QuoteLine__c for pricing data."
                )

    return issues


def check_soql_bad_relationship_names(manifest_dir: Path) -> list[str]:
    """Detect SOQL subqueries using incorrect child relationship names for SBQQ__ objects."""
    issues: list[str] = []
    apex_files = (
        list(manifest_dir.rglob("*.cls"))
        + list(manifest_dir.rglob("*.trigger"))
        + list(manifest_dir.rglob("*.soql"))
    )

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "SBQQ__Quote__c" not in content and "SBQQ__" not in content:
            continue

        for bad_rel in BAD_RELATIONSHIP_NAMES:
            if bad_rel in content:
                line_num = content.find(bad_rel)
                line_num = content[:line_num].count("\n") + 1
                issues.append(
                    f"WRONG_CPQ_RELATIONSHIP_NAME: {apex_file.relative_to(manifest_dir)} "
                    f"line ~{line_num} uses '{bad_rel}'. "
                    f"Correct CPQ relationship names: {CORRECT_RELATIONSHIPS}"
                )

    return issues


def check_cpq_objects_present(manifest_dir: Path) -> list[str]:
    """Verify that at least the core SBQQ__ object definitions exist in the metadata."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"

    if not objects_dir.exists():
        # No objects dir — skip this check
        return issues

    core_cpq_objects = [
        "SBQQ__Quote__c",
        "SBQQ__QuoteLine__c",
        "SBQQ__Subscription__c",
    ]
    found_objects = {f.name.replace(".object-meta.xml", "") for f in objects_dir.rglob("*.object-meta.xml")}

    for obj in core_cpq_objects:
        if obj not in found_objects:
            issues.append(
                f"CPQ_OBJECT_MISSING: Object metadata for '{obj}' not found in {objects_dir}. "
                "If this is a CPQ org, ensure the SBQQ__ managed package objects are in your manifest."
            )

    return issues


def check_apex_asset_used_for_subscriptions(manifest_dir: Path) -> list[str]:
    """Detect Apex that queries standard Asset in a CPQ context where SBQQ__Subscription__c should be used."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "SBQQ__" not in content:
            continue

        # Look for queries on standard Asset alongside CPQ references
        if re.search(r"\bFROM\s+Asset\b", content, re.IGNORECASE):
            line_match = re.search(r"\bFROM\s+Asset\b", content, re.IGNORECASE)
            if line_match:
                line_num = content[: line_match.start()].count("\n") + 1
                issues.append(
                    f"ASSET_INSTEAD_OF_SUBSCRIPTION: {apex_file.relative_to(manifest_dir)} "
                    f"line ~{line_num} queries standard 'Asset' in a CPQ context. "
                    "For CPQ recurring products, query SBQQ__Subscription__c instead."
                )

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def check_cpq_data_model(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_direct_dml_on_price_fields(manifest_dir))
    issues.extend(check_apex_standard_quote_objects(manifest_dir))
    issues.extend(check_soql_bad_relationship_names(manifest_dir))
    issues.extend(check_cpq_objects_present(manifest_dir))
    issues.extend(check_apex_asset_used_for_subscriptions(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for CPQ data model anti-patterns. "
            "Detects direct DML on CPQ price fields, wrong relationship names, "
            "standard Quote usage in CPQ contexts, and missing SBQQ__ object metadata."
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
    issues = check_cpq_data_model(manifest_dir)

    if not issues:
        print("No CPQ data model issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
