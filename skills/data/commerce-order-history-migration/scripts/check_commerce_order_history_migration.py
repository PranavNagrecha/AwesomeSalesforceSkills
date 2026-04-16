#!/usr/bin/env python3
"""Checker script for Commerce Order History Migration skill.

Validates migration plan documents and Apex code for common Order Management migration issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_commerce_order_history_migration.py --manifest-dir <path>

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

import argparse
import re
import sys
from pathlib import Path


def check_order_summary_dml(path: Path) -> list[str]:
    """Scan Apex files for direct DML inserts to OrderSummary."""
    issues = []
    for apex_file in list(path.glob("**/*.cls")) + list(path.glob("**/*.trigger")):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Look for insert statements targeting OrderSummary
        if re.search(r"insert\s+\w*[Oo]rder[Ss]ummary", content) or \
           re.search(r"Database\.insert\(\w*[Oo]rder[Ss]ummary", content):
            if "ConnectAPI" not in content:
                issues.append(
                    f"ERROR: {apex_file.name} appears to insert OrderSummary via direct DML. "
                    f"OrderSummary must be created via ConnectAPI.OrderSummary.createOrderSummary() "
                    f"or the 'Create Order Summary' Flow core action — not via insert DML or Bulk API."
                )
    return issues


def check_lifecycle_type(path: Path) -> list[str]:
    """Warn if ConnectAPI OrderSummary creation does not set LifeCycleType."""
    issues = []
    for apex_file in list(path.glob("**/*.cls")):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "createOrderSummary" in content or "OrderSummaryInputRepresentation" in content:
            if "LifeCycleType" not in content and "lifecycleType" not in content:
                issues.append(
                    f"WARN: {apex_file.name} calls ConnectAPI OrderSummary creation but does not "
                    f"explicitly set LifeCycleType. Historical orders require LifeCycleType = UNMANAGED. "
                    f"The default (MANAGED) enables refund/cancel actions on historical records."
                )
    return issues


def check_load_sequence_in_plan(path: Path) -> list[str]:
    """Check migration plan documents for missing OrderDeliveryGroup in load sequence."""
    issues = []
    for plan_file in list(path.glob("**/*.md")) + list(path.glob("**/*.txt")):
        try:
            content = plan_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        has_order_item = "OrderItem" in content
        has_delivery_group = "OrderDeliveryGroup" in content
        if has_order_item and not has_delivery_group:
            issues.append(
                f"WARN: {plan_file.name} references OrderItem but not OrderDeliveryGroup. "
                f"Order Management requires OrderDeliveryGroup as an intermediate object between "
                f"Order and OrderItem. Skipping it will cause FIELD_INTEGRITY_EXCEPTION at insert time."
            )

        has_order_summary = "OrderSummary" in content
        has_connectapi = "ConnectAPI" in content or "Connect API" in content or "Flow core action" in content
        if has_order_summary and not has_connectapi:
            issues.append(
                f"WARN: {plan_file.name} references OrderSummary but not ConnectAPI or Flow core action. "
                f"OrderSummary cannot be created via direct DML. Use ConnectAPI.OrderSummary.createOrderSummary() "
                f"or the 'Create Order Summary' Flow core action."
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Order Management historical order migration plan and code."
    )
    parser.add_argument("--manifest-dir", type=Path, default=Path("."),
                        help="Directory containing Apex files and plan documents to scan")
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.manifest_dir.exists():
        all_issues.extend(check_order_summary_dml(args.manifest_dir))
        all_issues.extend(check_lifecycle_type(args.manifest_dir))
        all_issues.extend(check_load_sequence_in_plan(args.manifest_dir))
    else:
        all_issues.append(f"ERROR: Directory not found: {args.manifest_dir}")

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    print("OK: No Order Management migration issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
