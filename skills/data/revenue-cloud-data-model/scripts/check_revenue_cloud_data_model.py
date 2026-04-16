#!/usr/bin/env python3
"""Checker script for Revenue Cloud Data Model skill.

Checks org metadata or configuration relevant to Revenue Cloud Data Model.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_revenue_cloud_data_model.py [--help]
    python3 check_revenue_cloud_data_model.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Revenue Cloud Data Model configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_revenue_cloud_data_model(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for legacy Salesforce Billing managed package object usage
    code_files = (
        list(manifest_dir.rglob("*.cls")) +
        list(manifest_dir.rglob("*.soql")) +
        list(manifest_dir.rglob("*.py"))
    )
    for code_file in code_files:
        try:
            text = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect blng__ namespace usage
        legacy_objects = ["blng__BillingSchedule__c", "blng__Invoice__c", "blng__Payment__c"]
        for obj in legacy_objects:
            if obj in text:
                issues.append(
                    f"{code_file}: Uses legacy Salesforce Billing object '{obj}' — "
                    "Native Revenue Cloud (RLM) uses standard objects: "
                    "BillingSchedule, Invoice, Payment. Confirm which product is in use."
                )
        # Detect FinanceTransaction DML
        if "FinanceTransaction" in text:
            for dml_kw in ["insert ", "update ", "upsert ", "delete "]:
                if dml_kw in text and "FinanceTransaction" in text:
                    lines = text.split("\n")
                    for i, line in enumerate(lines):
                        if "FinanceTransaction" in line and dml_kw.strip() in lines[max(0, i-3):i+3]:
                            issues.append(
                                f"{code_file}: DML near FinanceTransaction — "
                                "FinanceTransaction is read-only (system-generated). "
                                "Use SELECT only."
                            )
                            break
                    break
        # Detect LIMIT 1 queries on BillingSchedule (amendment history gap)
        if "BillingSchedule" in text and "LIMIT 1" in text.upper():
            issues.append(
                f"{code_file}: LIMIT 1 on BillingSchedule query — "
                "For amended assets, multiple BillingSchedule records exist per OrderItem. "
                "LIMIT 1 misses amendment history. Aggregate all records instead."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_revenue_cloud_data_model(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
