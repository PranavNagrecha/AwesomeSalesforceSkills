#!/usr/bin/env python3
"""Checker script for Manufacturing Cloud Setup skill.

Scans force-app/ metadata for common Manufacturing Cloud anti-patterns:

- Custom SalesAgreement__c / Sales_Agreement__c objects shadowing standard SalesAgreement
- Custom Rebate_Payout__c / Rebate__c objects shadowing native Rebate Management
- Apex batch classes that calculate rebates instead of using the native engine
- Flows / Apex creating OrderItem without populating SalesAgreementId
- Multi-period Opportunity custom Term__c field (suggests SalesAgreement)

Stdlib only.

Usage:
    python3 check_manufacturing_cloud_setup.py [--manifest-dir force-app]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SHADOW_OBJECT_HINTS = {
    "salesagreement__c": "SalesAgreement",
    "sales_agreement__c": "SalesAgreement",
    "rebate__c": "RebateProgram",
    "rebate_payout__c": "ProgramRebatePayout",
    "rebate_program__c": "RebateProgram",
    "account_product_forecast__c": "AccountProductForecast",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Manufacturing Cloud Setup metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _custom_objects(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.rglob("*.object-meta.xml")) + list(manifest_dir.rglob("*.object"))


def _custom_fields(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.rglob("*.field-meta.xml"))


def _apex_classes(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))


def _flows(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.rglob("*.flow-meta.xml"))


def check_manufacturing_cloud_setup(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: shadow objects for standard Manufacturing Cloud entities
    for obj_path in _custom_objects(manifest_dir):
        name = obj_path.stem.split(".")[0].lower()
        if name in SHADOW_OBJECT_HINTS:
            issues.append(
                f"{obj_path}: Custom object '{name}' shadows the Manufacturing Cloud standard "
                f"object '{SHADOW_OBJECT_HINTS[name]}'. Audit Object Manager for the standard "
                "object before building custom equivalents."
            )

    # Check 2: Term__c on Opportunity (suggests Sales Agreement modeling on wrong object)
    for field_path in _custom_fields(manifest_dir):
        if field_path.parent.name.lower() != "opportunity":
            continue
        try:
            text = field_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if re.search(r"<fullName>(Term|Contract_Term|Agreement_Term)__c</fullName>", text):
            issues.append(
                f"{field_path}: Custom multi-period field on Opportunity. Multi-period demand "
                "commitments belong on SalesAgreement, not Opportunity."
            )

    # Check 3: Apex classes calculating rebates without using native engine
    rebate_calc_re = re.compile(r"\b(rebate|payout)\b.*\b(calculate|compute|process)\b", re.IGNORECASE)
    for code_path in _apex_classes(manifest_dir):
        try:
            text = code_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if (
            "implements Database.Batchable" in text
            and rebate_calc_re.search(text)
            and "RebateProgram" not in text
            and "ProgramRebatePayout" not in text
        ):
            issues.append(
                f"{code_path}: Batch class appears to calculate rebates without referencing native "
                "RebateProgram / ProgramRebatePayout objects. Evaluate native Rebate Management."
            )

    # Check 4: Code creating OrderItem without setting SalesAgreementId
    orderitem_create_re = re.compile(r"\bnew\s+OrderItem\s*\(", re.IGNORECASE)
    for code_path in _apex_classes(manifest_dir):
        try:
            text = code_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if orderitem_create_re.search(text) and "SalesAgreementId" not in text:
            issues.append(
                f"{code_path}: Creates OrderItem without populating SalesAgreementId. Actuals "
                "will not reconcile to active Sales Agreements unless the lookup is set."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_manufacturing_cloud_setup(manifest_dir)

    if not issues:
        print("No Manufacturing Cloud anti-patterns detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
