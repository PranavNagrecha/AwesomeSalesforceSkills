#!/usr/bin/env python3
"""Checker script for Household Model Configuration skill.

Checks Salesforce metadata exports for common FSC household model
configuration issues: missing Rollups__c picklist values, ACR field
presence in page layouts, and namespace consistency.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_household_model_configuration.py [--help]
    python3 check_household_model_configuration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Required Rollups__c picklist values for FSC household rollups.
# Orgs provisioned before certain FSC releases may be missing these.
# ---------------------------------------------------------------------------
REQUIRED_ROLLUP_VALUES = {
    "FinancialAccount",
    "Opportunity",
    "Case",
    "InsurancePolicy",
}

# FSC ACR fields that must exist in the org for household model to work.
# Managed-package orgs use the FinServ__ namespace.
FSC_ACR_FIELDS = [
    "FinServ__PrimaryGroup__c",
    "FinServ__Primary__c",
    "FinServ__IncludeInGroup__c",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC Household Model Configuration metadata for common issues. "
            "Expects a Salesforce metadata directory (e.g., from sfdx force:source:retrieve)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def extract_xml_text(element: ET.Element, tag: str, ns: str = "") -> str | None:
    """Return text of the first matching child element, or None."""
    ns_prefix = f"{{{ns}}}" if ns else ""
    child = element.find(f"{ns_prefix}{tag}")
    return child.text if child is not None else None


# ---------------------------------------------------------------------------
# Check: Rollups__c picklist values on Account
# ---------------------------------------------------------------------------

def check_rollups_picklist(manifest_dir: Path) -> list[str]:
    """Check that required Rollups__c picklist values exist on Account."""
    issues: list[str] = []

    # Look for Account.field-meta.xml for Rollups__c or CustomField metadata
    # Standard path: objects/Account/fields/Rollups__c.field-meta.xml
    rollups_field_paths = (
        list(manifest_dir.rglob("Rollups__c.field-meta.xml"))
        + list(manifest_dir.rglob("Rollups__c-meta.xml"))
    )

    if not rollups_field_paths:
        issues.append(
            "Rollups__c field metadata not found in manifest. "
            "Cannot verify picklist values — retrieve Account field metadata and re-run. "
            "Missing Rollups__c values are the most common cause of silent rollup failures in existing orgs."
        )
        return issues

    for field_path in rollups_field_paths:
        try:
            tree = ET.parse(field_path)
            root = element = tree.getroot()
            # Strip namespace if present
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag[1:root.tag.index("}")]

            # Collect existing picklist values
            existing_values: set[str] = set()
            for pv in root.iter(f"{{{ns}}}fullName" if ns else "fullName"):
                if pv.text:
                    existing_values.add(pv.text.strip())

            missing = REQUIRED_ROLLUP_VALUES - existing_values
            if missing:
                issues.append(
                    f"Rollups__c picklist ({field_path.name}) is missing values for: "
                    f"{sorted(missing)}. "
                    "Household rollups for these object types will silently produce no data. "
                    "Add missing values via Setup > Object Manager > Account > Fields > Rollups__c > Values."
                )
        except ET.ParseError as exc:
            issues.append(f"Could not parse {field_path}: {exc}")

    return issues


# ---------------------------------------------------------------------------
# Check: FSC ACR custom fields exist in org metadata
# ---------------------------------------------------------------------------

def check_acr_fsc_fields(manifest_dir: Path) -> list[str]:
    """Check that the three key FSC fields exist on AccountContactRelation."""
    issues: list[str] = []

    acr_field_dir_candidates = [
        manifest_dir / "objects" / "AccountContactRelation" / "fields",
        manifest_dir / "force-app" / "main" / "default" / "objects" / "AccountContactRelation" / "fields",
    ]

    # Also search broadly
    found_dirs = [
        p.parent
        for p in manifest_dir.rglob("AccountContactRelation")
        if p.is_dir()
    ]
    acr_field_dir_candidates += [d / "fields" for d in found_dirs]

    acr_field_dirs = [d for d in acr_field_dir_candidates if d.exists()]

    if not acr_field_dirs:
        # Fall back to scanning for ACR field files by name anywhere in the manifest
        found_acr_field_files = list(manifest_dir.rglob("FinServ__*__c.field-meta.xml"))
        if found_acr_field_files:
            found_field_names = {f.stem.replace(".field-meta", "") for f in found_acr_field_files}
            for required in FSC_ACR_FIELDS:
                if required not in found_field_names:
                    issues.append(
                        f"FSC ACR field '{required}' not found in metadata. "
                        "This field is required for FSC household membership and rollup inclusion. "
                        "Confirm this is a managed-package FSC org with the FinServ__ namespace."
                    )
        else:
            issues.append(
                "AccountContactRelation field metadata not found. "
                "Cannot verify FSC ACR fields (FinServ__PrimaryGroup__c, FinServ__Primary__c, "
                "FinServ__IncludeInGroup__c). Retrieve ACR field metadata and re-run."
            )
        return issues

    for acr_field_dir in acr_field_dirs:
        existing_field_files = {f.name for f in acr_field_dir.glob("*.field-meta.xml")}
        for required_field in FSC_ACR_FIELDS:
            field_filename = f"{required_field}.field-meta.xml"
            if field_filename not in existing_field_files:
                issues.append(
                    f"ACR field '{required_field}' not found in {acr_field_dir}. "
                    "All three FSC ACR fields must be present for household membership and rollups to work."
                )

    return issues


# ---------------------------------------------------------------------------
# Check: Household record type exists on Account
# ---------------------------------------------------------------------------

def check_household_record_type(manifest_dir: Path) -> list[str]:
    """Check that a Household record type exists on Account."""
    issues: list[str] = []

    rt_paths = list(manifest_dir.rglob("*.recordType-meta.xml"))
    household_rt_found = any(
        "Household" in p.name or "household" in p.name.lower()
        for p in rt_paths
    )

    if rt_paths and not household_rt_found:
        issues.append(
            "No 'Household' record type found on Account in the metadata manifest. "
            "FSC households require an Account record type named 'Household' (or with 'Household' in the developer name). "
            "Confirm the record type is deployed and active."
        )

    return issues


# ---------------------------------------------------------------------------
# Check: Namespace consistency
# ---------------------------------------------------------------------------

def check_namespace_consistency(manifest_dir: Path) -> list[str]:
    """Warn if both FinServ__ and non-namespaced FSC field references are found.

    Mixing namespaced and non-namespaced FSC field references indicates the org
    may be migrating between managed-package FSC and Core FSC, which can cause
    runtime field resolution errors.
    """
    issues: list[str] = []

    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))
    if not apex_files:
        return issues

    has_namespace: list[str] = []
    has_no_namespace: list[str] = []

    namespace_fields = ["FinServ__PrimaryGroup__c", "FinServ__Primary__c", "FinServ__IncludeInGroup__c"]
    bare_fields = ["PrimaryGroup__c", "Primary__c", "IncludeInGroup__c"]

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
            if any(f in content for f in namespace_fields):
                has_namespace.append(str(apex_file.relative_to(manifest_dir)))
            if any(f in content for f in bare_fields):
                has_no_namespace.append(str(apex_file.relative_to(manifest_dir)))
        except OSError:
            continue

    if has_namespace and has_no_namespace:
        issues.append(
            "Namespace inconsistency: some Apex files use 'FinServ__' namespaced FSC ACR fields "
            f"({has_namespace[:3]}) and others use bare field names without namespace "
            f"({has_no_namespace[:3]}). "
            "Managed-package FSC orgs must use the FinServ__ prefix; Core FSC orgs use bare names. "
            "Mixing both will cause runtime errors. Standardize on one form."
        )

    return issues


# ---------------------------------------------------------------------------
# Main check runner
# ---------------------------------------------------------------------------

def check_household_model_configuration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues += check_rollups_picklist(manifest_dir)
    issues += check_acr_fsc_fields(manifest_dir)
    issues += check_household_record_type(manifest_dir)
    issues += check_namespace_consistency(manifest_dir)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_household_model_configuration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
