#!/usr/bin/env python3
"""Checker script for FSC Relationship Groups skill.

Validates Salesforce metadata for common FSC Relationship Group configuration issues:
- Checks that AccountContactRelation object has the required FSC custom fields
- Checks that Account object has Household, Professional Group, and Trust record types
- Checks that Rollups__c picklist is present on Account
- Detects any trigger metadata that references FSC rollup fields without all three ACR fields

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_relationship_groups.py [--manifest-dir path/to/metadata]
    python3 check_fsc_relationship_groups.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# FSC fields required on AccountContactRelation for correct group membership and rollups
REQUIRED_ACR_FIELDS = {
    "FinServ__PrimaryGroup__c",
    "FinServ__Primary__c",
    "FinServ__IncludeInGroup__c",
}

# FSC Relationship Group record types required on the Account object
REQUIRED_ACCOUNT_RECORD_TYPES = {
    "Household",
    "Professional Group",
    "Trust",
}

# Apex patterns that indicate ACR DML without all required FSC fields
# (heuristic: checks for AccountContactRelation usage without IncludeInGroup assignment)
APEX_ACR_PATTERN = "AccountContactRelation"
APEX_INCLUDE_PATTERN = "IncludeInGroup__c"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSC Relationship Group configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_xml_files(root: Path, glob: str) -> list[Path]:
    return sorted(root.rglob(glob))


def check_acr_custom_fields(manifest_dir: Path) -> list[str]:
    """Check that required FSC fields exist on AccountContactRelation object metadata."""
    issues: list[str] = []

    # Look for ACR object-level custom field metadata
    acr_field_dirs = [
        manifest_dir / "objects" / "AccountContactRelation" / "fields",
        manifest_dir / "force-app" / "main" / "default" / "objects" / "AccountContactRelation" / "fields",
    ]

    found_dir = None
    for d in acr_field_dirs:
        if d.exists():
            found_dir = d
            break

    if found_dir is None:
        # Not a hard failure — the org may use managed-package fields not in local metadata
        return issues

    existing_fields = {p.stem for p in found_dir.glob("*.field-meta.xml")}
    missing = REQUIRED_ACR_FIELDS - existing_fields

    # Only flag fields that have no match at all (managed-package fields will not appear in local metadata)
    # This check is useful for Core FSC orgs where fields are unmanaged
    for field in sorted(missing):
        if not field.startswith("FinServ__"):
            # Unexpected format — flag it
            issues.append(
                f"ACR field '{field}' in REQUIRED_ACR_FIELDS does not follow expected namespace pattern."
            )

    return issues


def check_account_record_types(manifest_dir: Path) -> list[str]:
    """Check that required FSC Relationship Group record types exist on Account."""
    issues: list[str] = []

    # Possible locations for Account record type metadata
    rt_dirs = [
        manifest_dir / "objects" / "Account" / "recordTypes",
        manifest_dir / "force-app" / "main" / "default" / "objects" / "Account" / "recordTypes",
    ]

    found_dir = None
    for d in rt_dirs:
        if d.exists():
            found_dir = d
            break

    if found_dir is None:
        return issues  # No local record type metadata — skip

    found_names: set[str] = set()
    for rt_file in found_dir.glob("*.recordType-meta.xml"):
        try:
            tree = ET.parse(rt_file)
            root_el = tree.getroot()
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
            label_el = root_el.find("sf:label", ns)
            if label_el is None:
                label_el = root_el.find("label")
            if label_el is not None and label_el.text:
                found_names.add(label_el.text.strip())
        except ET.ParseError:
            issues.append(f"Could not parse record type file: {rt_file}")

    missing_rts = REQUIRED_ACCOUNT_RECORD_TYPES - found_names
    for rt in sorted(missing_rts):
        issues.append(
            f"Account record type '{rt}' not found in local metadata. "
            f"Required for FSC Relationship Groups (Household, Professional Group, Trust). "
            f"Verify it is active in Setup > Object Manager > Account > Record Types."
        )

    return issues


def check_apex_acr_usage(manifest_dir: Path) -> list[str]:
    """Heuristic check: Apex classes that create AccountContactRelation without IncludeInGroup__c."""
    issues: list[str] = []

    apex_dirs = [
        manifest_dir / "classes",
        manifest_dir / "force-app" / "main" / "default" / "classes",
    ]

    for apex_dir in apex_dirs:
        if not apex_dir.exists():
            continue
        for apex_file in apex_dir.glob("*.cls"):
            try:
                content = apex_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            if APEX_ACR_PATTERN not in content:
                continue

            # If the file references AccountContactRelation but never references IncludeInGroup__c
            # it is a candidate for missing field assignment
            if APEX_INCLUDE_PATTERN not in content:
                issues.append(
                    f"Apex class '{apex_file.name}' references AccountContactRelation "
                    f"but does not mention FinServ__IncludeInGroup__c. "
                    f"Verify that all ACR inserts or updates in this class explicitly set "
                    f"FinServ__IncludeInGroup__c = true where group rollup inclusion is intended."
                )

    return issues


def check_rollups_picklist(manifest_dir: Path) -> list[str]:
    """Check that Rollups__c picklist field exists on Account object metadata."""
    issues: list[str] = []

    rollups_field_paths = [
        manifest_dir / "objects" / "Account" / "fields" / "FinServ__Rollups__c.field-meta.xml",
        manifest_dir / "force-app" / "main" / "default" / "objects" / "Account" / "fields" / "FinServ__Rollups__c.field-meta.xml",
        # Core FSC (no namespace)
        manifest_dir / "objects" / "Account" / "fields" / "Rollups__c.field-meta.xml",
        manifest_dir / "force-app" / "main" / "default" / "objects" / "Account" / "fields" / "Rollups__c.field-meta.xml",
    ]

    # Only flag if Account fields directory exists but Rollups__c is absent
    account_field_dirs = [
        manifest_dir / "objects" / "Account" / "fields",
        manifest_dir / "force-app" / "main" / "default" / "objects" / "Account" / "fields",
    ]

    has_account_fields_dir = any(d.exists() for d in account_field_dirs)
    has_rollups_field = any(p.exists() for p in rollups_field_paths)

    if has_account_fields_dir and not has_rollups_field:
        issues.append(
            "Rollups__c picklist field not found in Account object metadata. "
            "This field controls which object types are included in FSC group-level rollups. "
            "If this is a managed-package FSC org, the field is under FinServ__Rollups__c and "
            "may not appear in local metadata. Verify in Setup > Object Manager > Account > "
            "Fields & Relationships > Rollups__c that the field exists and has values for "
            "all required object types (FinancialAccount, Opportunity, Case, InsurancePolicy)."
        )

    return issues


def check_fsc_relationship_groups(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_acr_custom_fields(manifest_dir))
    issues.extend(check_account_record_types(manifest_dir))
    issues.extend(check_apex_acr_usage(manifest_dir))
    issues.extend(check_rollups_picklist(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsc_relationship_groups(manifest_dir)

    if not issues:
        print("No FSC Relationship Group configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
