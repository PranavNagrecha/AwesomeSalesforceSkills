#!/usr/bin/env python3
"""Checker script for Usage-Based Pricing Setup skill.

Scans metadata for usage-based-pricing anti-patterns:
- Rating Apex without an explicit Rated/IsRated filter
- LWCs that aggregate UsageRecord directly
- Consumption Schedule edits without new effective dates

Usage:
    python3 check_usage_based_pricing_setup.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


RATED_FILTER_PAT = re.compile(r"(?i)(Is|Rated|HasBeenRated)\s*=\s*false")
USAGERECORD_SUM_PAT = re.compile(r"(?is)SELECT\s+SUM\([^)]+\)\s+FROM\s+UsageRecord")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check usage-based pricing configuration for issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_rating_classes(root: Path) -> list[str]:
    issues: list[str] = []
    classes_dir = root / "classes"
    if not classes_dir.exists():
        return issues
    for path in classes_dir.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "UsageRecord" not in text and "Usage_Record__c" not in text:
            continue
        if "Rating" not in path.stem and "Rating" not in text:
            continue
        if not RATED_FILTER_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: rating logic without explicit Rated=false filter; idempotency at risk"
            )
    return issues


def check_raw_usage_lwc(root: Path) -> list[str]:
    issues: list[str] = []
    apex_dir = root / "classes"
    if apex_dir.exists():
        for path in apex_dir.rglob("*.cls"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "AuraEnabled" in text and USAGERECORD_SUM_PAT.search(text):
                issues.append(
                    f"{path.relative_to(root)}: AuraEnabled aggregation of UsageRecord; use UsageSummary rollup"
                )
    lwc_dir = root / "lwc"
    if lwc_dir.exists():
        for path in lwc_dir.rglob("*.js"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if "UsageRecord" in text and "aggregate" in text.lower():
                issues.append(
                    f"{path.relative_to(root)}: LWC aggregates UsageRecord directly; prefer UsageSummary"
                )
    return issues


def check_consumption_schedule_edits(root: Path) -> list[str]:
    issues: list[str] = []
    schedules = root / "consumptionSchedules"
    if not schedules.exists():
        return issues
    for path in schedules.rglob("*.xml"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if "<effectiveStartDate>" not in text:
            issues.append(
                f"{path.relative_to(root)}: Consumption Schedule without explicit effective start date"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_rating_classes(manifest_dir))
    issues.extend(check_raw_usage_lwc(manifest_dir))
    issues.extend(check_consumption_schedule_edits(manifest_dir))

    if not issues:
        print("No usage-based pricing anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
