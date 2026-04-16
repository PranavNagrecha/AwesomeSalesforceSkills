#!/usr/bin/env python3
"""Checker script for Loyalty Management Setup skill.

Checks org metadata or configuration relevant to Loyalty Management Setup.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_loyalty_management_setup.py [--help]
    python3 check_loyalty_management_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Loyalty Management Setup configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_loyalty_management_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check SOQL/Apex files for non-qualifying currency used in tier queries
    code_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.soql"))
    for code_file in code_files:
        try:
            text = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect queries on LoyaltyMemberCurrency without CurrencyType filter
        if "LoyaltyMemberCurrency" in text and "CurrencyType" not in text:
            issues.append(
                f"{code_file}: Queries LoyaltyMemberCurrency without filtering on CurrencyType — "
                "Ensure qualifying vs. non-qualifying currencies are explicitly distinguished."
            )

    # Check for DPE-related metadata
    dpe_files = list(manifest_dir.rglob("*.dataProcessingEngine-meta.xml"))
    if not dpe_files:
        # Check if any loyalty-related flow or custom metadata suggests DPE should exist
        flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))
        has_loyalty_flow = any(
            "loyalty" in f.name.lower() or "tier" in f.name.lower()
            for f in flow_files
        )
        if has_loyalty_flow:
            issues.append(
                "No Data Processing Engine (DPE) metadata found but loyalty/tier flows detected — "
                "Loyalty tier processing requires DPE batch jobs (Reset Qualifying Points, "
                "Aggregate/Expire Fixed Non-Qualifying Points) to be activated and scheduled."
            )

    # Check Experience Cloud site metadata for multiple loyalty program associations
    site_files = list(manifest_dir.rglob("*.network-meta.xml"))
    loyalty_sites = []
    for site_file in site_files:
        try:
            text = site_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "LoyaltyMemberPortal" in text or "loyalty" in text.lower():
            loyalty_sites.append(site_file.name)
    if len(loyalty_sites) > 1:
        issues.append(
            f"Multiple Experience Cloud sites with loyalty configuration found: {loyalty_sites} — "
            "Each Experience Cloud site can be associated with only one loyalty program."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_loyalty_management_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
