#!/usr/bin/env python3
"""Checker script for CPQ Deployment Patterns skill.

Validates CPQ deployment plans and scripts for common data deployment issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_deployment_patterns.py --manifest-dir <path>

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

import argparse
import re
import sys
from pathlib import Path


CPQ_DATA_OBJECTS = [
    "SBQQ__PricingRule__c",
    "SBQQ__ProductRule__c",
    "SBQQ__QuoteTemplate__c",
    "SBQQ__ProductOption__c",
    "SBQQ__OptionConstraint__c",
    "SBQQ__DiscountCategory__c",
]

# Required load order for validation
CPQ_LOAD_ORDER = [
    "Pricebook2",
    "Product2",
    "PricebookEntry",
    "SBQQ__PricingRule",
    "SBQQ__ProductRule",
    "SBQQ__QuoteTemplate",
]


def check_metadata_only_deployment(path: Path) -> list[str]:
    """Warn if deployment pipelines deploy CPQ without a data step."""
    issues = []
    pipeline_files = list(path.glob("**/*.yml")) + list(path.glob("**/*.yaml")) + \
                     list(path.glob("**/*.sh")) + list(path.glob("**/*.json"))

    for pipe_file in pipeline_files:
        try:
            content = pipe_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Check if file describes a deployment pipeline with CPQ
        if "CPQ" not in content and "SBQQ" not in content:
            continue
        has_metadata_deploy = re.search(r"sf.project.deploy|sfdx.force:source:deploy|change.set", content, re.IGNORECASE)
        has_data_step = re.search(r"SFDMU|sfdmu|data.move|data.loader|DataLoader|Prodly|Copado.Data", content, re.IGNORECASE)
        if has_metadata_deploy and not has_data_step:
            issues.append(
                f"WARN: {pipe_file.name} describes a CPQ deployment with a metadata step but no data migration step. "
                f"CPQ configuration (Price Rules, Product Rules, Quote Templates) exists as data records, not metadata. "
                f"A data deployment step using SFDMU, Data Loader, or Copado Data Deploy is required."
            )
    return issues


def check_hardcoded_sf_ids_in_csv(path: Path) -> list[str]:
    """Warn if CSV files contain patterns that look like org-specific Salesforce IDs in lookup fields."""
    issues = []
    id_pattern = re.compile(r"^[0-9a-zA-Z]{15,18}$")

    for csv_file in list(path.glob("**/*.csv")):
        if "SBQQ" not in csv_file.name and "CPQ" not in csv_file.name and "Price" not in csv_file.name:
            continue
        try:
            content = csv_file.read_text(encoding="utf-8-sig", errors="ignore")
        except OSError:
            continue
        # Check for lines with patterns of org-specific IDs (look for typical Salesforce ID prefixes)
        sf_id_pattern = re.compile(r"\b0[0-9a-zA-Z]{14,17}\b")
        matches = sf_id_pattern.findall(content)
        if len(matches) > 5:  # More than a few matches suggests raw SF IDs in the data
            issues.append(
                f"WARN: {csv_file.name} appears to contain multiple raw Salesforce record IDs. "
                f"Org-specific IDs will produce INVALID_CROSS_REFERENCE_KEY errors when loaded to a target org. "
                f"Use External ID fields as cross-org matching keys instead of record IDs."
            )
    return issues


def check_sfdmu_config(path: Path) -> list[str]:
    """Validate SFDMU export.json files for CPQ deployment correctness."""
    issues = []
    sfdmu_files = list(path.glob("**/export.json")) + list(path.glob("**/sfdmu*.json"))

    for sfdmu_file in sfdmu_files:
        try:
            content = sfdmu_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "SBQQ" not in content and "CPQ" not in content:
            continue
        # Check if External IDs are mentioned
        if "externalId" not in content and "ExternalId" not in content:
            issues.append(
                f"WARN: {sfdmu_file.name} is an SFDMU config for CPQ deployment but does not specify "
                f"External ID fields. CPQ cross-org deployment requires External IDs as upsert matching keys."
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate CPQ deployment plans and pipeline scripts."
    )
    parser.add_argument("--manifest-dir", type=Path, default=Path("."),
                        help="Directory to scan for deployment pipelines, CSVs, and SFDMU config")
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.manifest_dir.exists():
        all_issues.extend(check_metadata_only_deployment(args.manifest_dir))
        all_issues.extend(check_hardcoded_sf_ids_in_csv(args.manifest_dir))
        all_issues.extend(check_sfdmu_config(args.manifest_dir))
    else:
        all_issues.append(f"ERROR: Directory not found: {args.manifest_dir}")

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    print("OK: No CPQ deployment pattern issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
