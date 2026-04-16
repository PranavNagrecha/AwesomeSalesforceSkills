#!/usr/bin/env python3
"""Checker script for Revenue Lifecycle Management skill.

Checks org metadata or configuration relevant to Revenue Lifecycle Management.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_revenue_lifecycle_management.py [--help]
    python3 check_revenue_lifecycle_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Revenue Lifecycle Management configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_revenue_lifecycle_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for use of legacy Salesforce Billing managed package objects in code
    code_files = (
        list(manifest_dir.rglob("*.cls")) +
        list(manifest_dir.rglob("*.py")) +
        list(manifest_dir.rglob("*.soql"))
    )
    for code_file in code_files:
        try:
            text = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect legacy blng__ namespace usage
        if "blng__" in text or "blng__BillingSchedule" in text:
            issues.append(
                f"{code_file}: Uses legacy Salesforce Billing managed package objects (blng__*) — "
                "If this is a native Revenue Cloud (RLM) org, use standard objects: "
                "BillingSchedule, Invoice, Payment, FinanceTransaction."
            )
        # Detect FinanceTransaction DML
        if "FinanceTransaction" in text and any(
            kw in text for kw in ["insert ", "update ", "upsert "]
        ):
            issues.append(
                f"{code_file}: Possible DML on FinanceTransaction detected — "
                "FinanceTransaction is read-only (system-generated). DML will throw an exception."
            )

    # Check Flow XML for Slack actions in before-save context (shared check)
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))
    for flow_file in flow_files:
        try:
            text = flow_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect before-save flows with callout-like actions
        if "triggerType>Before_Save" in text and "actionType>apex" in text:
            issues.append(
                f"{flow_file}: Before-save record-triggered Flow with Apex action detected — "
                "Callouts (including external system integrations) cannot run in before-save context."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_revenue_lifecycle_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
