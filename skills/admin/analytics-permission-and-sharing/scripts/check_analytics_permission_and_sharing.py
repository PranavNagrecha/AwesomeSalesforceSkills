#!/usr/bin/env python3
"""Checker script for Analytics Permission and Sharing skill.

Validates CRM Analytics security configuration metadata for common issues including:
- Missing security predicates on datasets
- Blank backup predicates when sharing inheritance is used
- Predicate string length exceeding the 5,000-character platform limit
- References to likely-incorrect column name casing in predicates
- App sharing metadata sanity checks

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_permission_and_sharing.py [--help]
    python3 check_analytics_permission_and_sharing.py --manifest-dir path/to/metadata
    python3 check_analytics_permission_and_sharing.py --predicate "'OwnerId' == \\"\\$User.Id\\""
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Platform limit for security predicate SAQL string length (characters)
PREDICATE_MAX_LENGTH = 5000

# Objects supported by sharing inheritance
SHARING_INHERITANCE_SUPPORTED_OBJECTS = {
    "Account",
    "Case",
    "Contact",
    "Lead",
    "Opportunity",
}

# Common incorrect column name patterns (lowercase field API names used as predicate columns)
LIKELY_WRONG_CASING_PATTERNS = [
    "ownerid",
    "accountid",
    "contactid",
    "caseid",
    "leadid",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics permission and sharing configuration for common issues. "
            "Scans .json metadata files in the manifest directory for dataset security settings."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or Analytics JSON exports (default: current directory).",
    )
    parser.add_argument(
        "--predicate",
        default=None,
        help="A single security predicate string to validate (length, casing patterns).",
    )
    return parser.parse_args()


def check_predicate_string(predicate: str, dataset_name: str = "<unknown>") -> list[str]:
    """Validate a single security predicate string. Returns a list of issue strings."""
    issues: list[str] = []

    if not predicate or predicate.strip() == "":
        issues.append(
            f"Dataset '{dataset_name}': security predicate is blank. "
            "If sharing inheritance is enabled, a blank backup predicate grants all-visible access "
            "to users with 3,000+ source records. Set backup predicate to 'false' to deny those users."
        )
        return issues

    if len(predicate) > PREDICATE_MAX_LENGTH:
        issues.append(
            f"Dataset '{dataset_name}': security predicate is {len(predicate)} characters, "
            f"exceeding the {PREDICATE_MAX_LENGTH}-character platform limit. "
            "The predicate may be silently truncated. Refactor using a data-driven join approach."
        )

    predicate_lower = predicate.lower()
    for wrong_name in LIKELY_WRONG_CASING_PATTERNS:
        # Look for the pattern inside single quotes (predicate column reference)
        if f"'{wrong_name}'" in predicate_lower:
            # Check if the exact same string with original casing is NOT present
            # (i.e., the predicate uses lowercase when the column is likely mixed-case)
            if f"'{wrong_name}'" in predicate and wrong_name not in predicate:
                # The lowercase version matches but the correct-case version is absent
                issues.append(
                    f"Dataset '{dataset_name}': predicate may reference column '{wrong_name}' in all-lowercase. "
                    "CRM Analytics predicate column names are case-sensitive. "
                    "Verify the exact column name from the dataset schema (e.g., 'OwnerId' not 'ownerid')."
                )

    return issues


def check_dataset_json(file_path: Path) -> list[str]:
    """Check a dataset JSON metadata file for security configuration issues."""
    issues: list[str] = []
    dataset_name = file_path.stem

    try:
        with file_path.open() as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        issues.append(f"Dataset '{dataset_name}': could not parse JSON — {exc}")
        return issues

    # Check for security section existence
    security = data.get("security") or data.get("securityPredicate") or data.get("rowLevelSecurity")

    if security is None:
        issues.append(
            f"Dataset '{dataset_name}': no security configuration found in metadata. "
            "Datasets without a security predicate or sharing inheritance grant all licensed users "
            "access to all rows by default. If this is intentional, document it explicitly."
        )
        return issues

    # Sharing inheritance checks
    predicate_type = security.get("predicateType") or security.get("type") or ""
    if predicate_type.lower() in ("sharinginheritance", "sharing_inheritance", "sharing"):
        sf_object = security.get("inheritedObject") or security.get("salesforceObject") or ""
        if sf_object and sf_object not in SHARING_INHERITANCE_SUPPORTED_OBJECTS:
            issues.append(
                f"Dataset '{dataset_name}': sharing inheritance references object '{sf_object}', "
                f"which is not in the supported list: {sorted(SHARING_INHERITANCE_SUPPORTED_OBJECTS)}. "
                "Sharing inheritance only works for Account, Case, Contact, Lead, and Opportunity. "
                "Use a security predicate instead for this object."
            )

        backup_predicate = security.get("backupPredicate") or security.get("fallbackPredicate") or ""
        if not backup_predicate or backup_predicate.strip() == "":
            issues.append(
                f"Dataset '{dataset_name}': sharing inheritance is configured but backup predicate is blank. "
                "Users with access to 3,000 or more source records bypass sharing inheritance and fall back "
                "to the backup predicate. A blank backup predicate grants those users all-row access. "
                "Set backup predicate to 'false'."
            )
        else:
            issues.extend(check_predicate_string(backup_predicate, dataset_name + " (backup predicate)"))

    # Regular predicate checks
    predicate_text = security.get("predicate") or security.get("saqlPredicate") or ""
    if predicate_text:
        issues.extend(check_predicate_string(predicate_text, dataset_name))

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Scan a directory for Analytics metadata JSON files and check each one."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for dataset JSON files — common patterns in SFDX and Analytics metadata exports
    dataset_files = list(manifest_dir.rglob("*.json"))

    if not dataset_files:
        issues.append(
            f"No JSON files found under '{manifest_dir}'. "
            "To use this checker, point --manifest-dir at a directory containing Analytics "
            "dataset metadata JSON files (e.g., exported via sfdx force:analytics:dataset:list)."
        )
        return issues

    checked = 0
    for f in dataset_files:
        # Skip package.json, node_modules, registry artifacts, etc.
        if any(skip in f.parts for skip in ("node_modules", "registry", "vector_index", ".git")):
            continue
        if f.name.startswith("."):
            continue
        file_issues = check_dataset_json(f)
        if file_issues:
            issues.extend(file_issues)
        checked += 1

    if checked == 0:
        issues.append(
            "No dataset metadata JSON files were scanned (all found files were skipped). "
            "Ensure the manifest directory contains Analytics dataset configuration exports."
        )

    return issues


def main() -> int:
    args = parse_args()

    all_issues: list[str] = []

    # Validate a standalone predicate string if provided
    if args.predicate:
        predicate_issues = check_predicate_string(args.predicate, "<provided predicate>")
        all_issues.extend(predicate_issues)

    # Validate the manifest directory
    manifest_dir = Path(args.manifest_dir)
    all_issues.extend(check_manifest_dir(manifest_dir))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
