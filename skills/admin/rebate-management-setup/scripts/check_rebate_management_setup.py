#!/usr/bin/env python3
"""Checker script for Rebate Management Setup skill.

Scans metadata for Rebate Management anti-patterns:
- Scheduled Apex named like hand-rolled accrual calculators
- Rebate_Program__c records implied to be oversized (by counting benefit files)
- Partner-facing LWCs that query Rebate_Accrual__c directly

Usage:
    python3 check_rebate_management_setup.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ACCRUAL_CLASS_PAT = re.compile(
    r"(?i)(rebate_?accrual|calculate_?rebate|nightly_?rebate|partner_?rebate_?calc)"
)
RAW_ACCRUAL_QUERY_PAT = re.compile(
    r"(?is)SELECT.*FROM\s+Rebate_Accrual__c"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Rebate Management configuration for common issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_accrual_classes(root: Path) -> list[str]:
    issues: list[str] = []
    classes_dir = root / "classes"
    if not classes_dir.exists():
        return issues
    for path in classes_dir.rglob("*.cls"):
        if ACCRUAL_CLASS_PAT.search(path.stem):
            issues.append(
                f"{path.relative_to(root)}: likely hand-rolled accrual logic; use shipped Rebate Calculation"
            )
    return issues


def check_lwc_raw_accrual_query(root: Path) -> list[str]:
    issues: list[str] = []
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return issues
    for path in lwc_dir.rglob("*.js"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Rebate_Accrual__c" in text and ("@wire" in text or "SOQL" in text.upper()):
            issues.append(
                f"{path.relative_to(root)}: partner-facing LWC likely queries raw accruals; use snapshot data"
            )
    apex_dir = root / "classes"
    if apex_dir.exists():
        for path in apex_dir.rglob("*.cls"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if RAW_ACCRUAL_QUERY_PAT.search(text) and "AuraEnabled" in text:
                issues.append(
                    f"{path.relative_to(root)}: AuraEnabled query against Rebate_Accrual__c; use snapshot"
                )
    return issues


def check_oversized_program(root: Path) -> list[str]:
    issues: list[str] = []
    records_dir = root / "records" / "Rebate_Program__c"
    if not records_dir.exists():
        return issues
    benefit_counts: dict[str, int] = {}
    benefits_dir = root / "records" / "Benefit__c"
    if benefits_dir.exists():
        for bf in benefits_dir.glob("*.json"):
            try:
                text = bf.read_text(encoding="utf-8")
            except OSError:
                continue
            m = re.search(r"Rebate_Program__c[\"']?\s*:\s*[\"']([^\"']+)", text)
            if m:
                benefit_counts[m.group(1)] = benefit_counts.get(m.group(1), 0) + 1
    for program, count in benefit_counts.items():
        if count >= 100:
            issues.append(
                f"Rebate_Program__c {program} has {count} Benefits; consider splitting into multiple programs"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_accrual_classes(manifest_dir))
    issues.extend(check_lwc_raw_accrual_query(manifest_dir))
    issues.extend(check_oversized_program(manifest_dir))

    if not issues:
        print("No Rebate Management anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
