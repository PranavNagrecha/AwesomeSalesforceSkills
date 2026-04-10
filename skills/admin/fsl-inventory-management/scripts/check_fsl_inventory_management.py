#!/usr/bin/env python3
"""Checker script for FSL Inventory Management skill.

Checks Salesforce metadata for common FSL inventory configuration issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_inventory_management.py [--help]
    python3 check_fsl_inventory_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSL Inventory Management configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_product_item_transaction_dml(manifest_dir: Path) -> list[str]:
    """Warn if Apex classes contain DML against ProductItemTransaction.

    Direct insert/update/delete of ProductItemTransaction corrupts QuantityOnHand.
    """
    issues: list[str] = []
    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        return issues

    danger_patterns = [
        "insert productitemtransaction",
        "update productitemtransaction",
        "delete productitemtransaction",
        "upsert productitemtransaction",
    ]

    for apex_file in apex_dir.glob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
        for pattern in danger_patterns:
            if pattern in content:
                issues.append(
                    f"[CRITICAL] {apex_file.name}: contains '{pattern}' — "
                    "direct DML on ProductItemTransaction corrupts QuantityOnHand. "
                    "Use adjusting ProductTransfer records instead."
                )

    return issues


def check_quantity_on_hand_direct_write(manifest_dir: Path) -> list[str]:
    """Warn if Apex classes directly assign QuantityOnHand on ProductItem."""
    issues: list[str] = []
    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        return issues

    # Look for assignments like .QuantityOnHand = or .QuantityOnHand=
    import re
    pattern = re.compile(r"\.quantityonhand\s*=", re.IGNORECASE)

    for apex_file in apex_dir.glob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if pattern.search(content):
            issues.append(
                f"[CRITICAL] {apex_file.name}: directly assigns QuantityOnHand — "
                "this field is platform-managed on ProductItem. "
                "Use ProductTransfer (Received) or ProductConsumed to change stock levels."
            )

    return issues


def check_flow_quantity_on_hand_write(manifest_dir: Path) -> list[str]:
    """Warn if Flow metadata updates QuantityOnHand directly on ProductItem."""
    issues: list[str] = []
    flow_dir = manifest_dir / "flows"
    if not flow_dir.exists():
        return issues

    ns = "http://soap.sforce.com/2006/04/metadata"

    for flow_file in flow_dir.glob("*.flow-meta.xml"):
        try:
            tree = ET.parse(flow_file)
        except ET.ParseError:
            continue

        root = tree.getroot()
        # Look for recordUpdates targeting ProductItem with QuantityOnHand field
        for record_update in root.findall(f".//{{{ns}}}recordUpdates"):
            object_el = record_update.find(f"{{{ns}}}object")
            if object_el is None or object_el.text != "ProductItem":
                continue
            for field_el in record_update.findall(f".//{{{ns}}}field"):
                if field_el.text == "QuantityOnHand":
                    issues.append(
                        f"[CRITICAL] {flow_file.name}: Flow updates QuantityOnHand on ProductItem — "
                        "this field is platform-managed. Use ProductTransfer (Received) to adjust stock."
                    )
                    break

    return issues


def check_flow_product_item_transaction_dml(manifest_dir: Path) -> list[str]:
    """Warn if Flow metadata creates/updates/deletes ProductItemTransaction records."""
    issues: list[str] = []
    flow_dir = manifest_dir / "flows"
    if not flow_dir.exists():
        return issues

    ns = "http://soap.sforce.com/2006/04/metadata"
    dml_tags = ["recordCreates", "recordUpdates", "recordDeletes"]

    for flow_file in flow_dir.glob("*.flow-meta.xml"):
        try:
            tree = ET.parse(flow_file)
        except ET.ParseError:
            continue

        root = tree.getroot()
        for tag in dml_tags:
            for el in root.findall(f".//{{{ns}}}{tag}"):
                object_el = el.find(f"{{{ns}}}object")
                if object_el is not None and object_el.text == "ProductItemTransaction":
                    issues.append(
                        f"[CRITICAL] {flow_file.name}: Flow performs '{tag}' on ProductItemTransaction — "
                        "these records are auto-generated and must not be modified via DML."
                    )

    return issues


def check_missing_official_sources_in_skill(manifest_dir: Path) -> list[str]:
    """Verify the skill package has at least one official URL in well-architected.md."""
    issues: list[str] = []
    # Resolve relative to the script location if manifest_dir is the skill root
    wa_file = manifest_dir / "references" / "well-architected.md"
    if not wa_file.exists():
        # Not a skill package root — skip silently
        return issues

    content = wa_file.read_text(encoding="utf-8", errors="replace")
    if "https://developer.salesforce.com" not in content and "https://help.salesforce.com" not in content:
        issues.append(
            f"[WARN] references/well-architected.md has no official Salesforce URLs under 'Official Sources Used'. "
            "Add at least one developer.salesforce.com or help.salesforce.com reference."
        )
    return issues


def check_apex_product_consumed_pattern(manifest_dir: Path) -> list[str]:
    """Warn if Apex creates ProductTransfer to record parts usage instead of ProductConsumed."""
    issues: list[str] = []
    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        return issues

    import re
    # Heuristic: ProductTransfer insert near 'consumed' or 'workorder' in the same file
    # that does NOT also reference ProductConsumed — likely wrong pattern
    transfer_pattern = re.compile(r"new\s+ProductTransfer\b", re.IGNORECASE)
    consumed_pattern = re.compile(r"ProductConsumed\b", re.IGNORECASE)
    workorder_context = re.compile(r"WorkOrder", re.IGNORECASE)

    for apex_file in apex_dir.glob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        has_transfer = transfer_pattern.search(content)
        has_consumed = consumed_pattern.search(content)
        has_wo_context = workorder_context.search(content)

        if has_transfer and has_wo_context and not has_consumed:
            issues.append(
                f"[WARN] {apex_file.name}: creates ProductTransfer in a Work Order context without ProductConsumed — "
                "verify that parts usage on Work Orders is recorded via ProductConsumed, "
                "not ProductTransfer. ProductTransfer is for location-to-location stock movement."
            )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_fsl_inventory_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_product_item_transaction_dml(manifest_dir))
    issues.extend(check_quantity_on_hand_direct_write(manifest_dir))
    issues.extend(check_flow_quantity_on_hand_write(manifest_dir))
    issues.extend(check_flow_product_item_transaction_dml(manifest_dir))
    issues.extend(check_missing_official_sources_in_skill(manifest_dir))
    issues.extend(check_apex_product_consumed_pattern(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_inventory_management(manifest_dir)

    if not issues:
        print("No FSL inventory management issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    critical_count = sum(1 for i in issues if "[CRITICAL]" in i)
    warn_count = len(issues) - critical_count
    print(
        f"\nSummary: {critical_count} critical issue(s), {warn_count} warning(s).",
        file=sys.stderr,
    )

    return 1


if __name__ == "__main__":
    sys.exit(main())
