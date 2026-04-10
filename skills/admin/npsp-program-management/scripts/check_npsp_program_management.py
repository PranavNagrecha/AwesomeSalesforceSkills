#!/usr/bin/env python3
"""Checker script for NPSP Program Management Module (PMM) skill.

Checks Salesforce metadata for common PMM configuration issues:
- Validation rules on ServiceDelivery__c (required-field enforcement)
- Bulk Service Delivery field set presence
- PMM object presence (basic namespace check via CustomObject metadata)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_npsp_program_management.py [--help]
    python3 check_npsp_program_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check PMM (Program Management Module) configuration and metadata "
            "for common issues. Pass a Salesforce metadata project root."
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

def find_xml_files(root: Path, glob_pattern: str) -> list[Path]:
    return sorted(root.rglob(glob_pattern))


def read_xml(path: Path) -> ET.Element | None:
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag string."""
    return tag.split("}")[-1] if "}" in tag else tag


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_service_delivery_validation_rules(manifest_dir: Path) -> list[str]:
    """Warn if ServiceDelivery__c has no validation rules at all.

    Admins frequently rely on the field-set Required flag instead of
    validation rules, which does not enforce saves in the bulk action.
    """
    issues: list[str] = []

    # Metadata API stores validation rules inside the object XML or as
    # individual ValidationRule metadata files depending on the project format.
    # Check both locations.

    # 1. Check for standalone ValidationRule metadata files under the PMM namespace.
    vr_files = find_xml_files(manifest_dir, "pmdm__ServiceDelivery__c.*.validationRule-meta.xml")
    vr_files += find_xml_files(manifest_dir, "ServiceDelivery__c.*.validationRule-meta.xml")

    # 2. Check for validation rules embedded in the object XML.
    obj_files = find_xml_files(manifest_dir, "pmdm__ServiceDelivery__c.object-meta.xml")
    obj_files += find_xml_files(manifest_dir, "ServiceDelivery__c.object-meta.xml")

    has_vr = bool(vr_files)

    if not has_vr:
        for obj_path in obj_files:
            root_el = read_xml(obj_path)
            if root_el is None:
                continue
            for child in root_el:
                if strip_ns(child.tag) == "validationRules":
                    has_vr = True
                    break

    if not has_vr and (obj_files or vr_files):
        issues.append(
            "No validation rules found on ServiceDelivery__c. "
            "The PMM Bulk Service Delivery field-set 'Required' flag does NOT enforce saves. "
            "Add validation rules for any field that must be required (e.g., Quantity, Delivery Date)."
        )

    return issues


def check_bulk_service_delivery_fieldset(manifest_dir: Path) -> list[str]:
    """Check that the Bulk_Service_Deliveries_Fields field set file exists.

    Cannot validate field order from metadata alone (field set XML does not
    expose the display order reliably across API versions), but we can
    confirm the field set is present and remind the reviewer to check order manually.
    """
    issues: list[str] = []

    fieldset_files = find_xml_files(
        manifest_dir, "Bulk_Service_Deliveries_Fields.fieldSet-meta.xml"
    )

    if not fieldset_files:
        # Only warn if PMM objects appear to be in scope.
        pmm_objects = find_xml_files(manifest_dir, "pmdm__ServiceDelivery__c.object-meta.xml")
        pmm_objects += find_xml_files(manifest_dir, "pmdm__ProgramEngagement__c.object-meta.xml")
        if pmm_objects:
            issues.append(
                "Bulk_Service_Deliveries_Fields field set metadata not found in manifest. "
                "If this org uses PMM Bulk Service Deliveries, confirm the field set exists in the org "
                "and that field order is: (1) Client, (2) Program Engagement, (3) Service."
            )
    else:
        issues.append(
            "MANUAL CHECK REQUIRED: Bulk_Service_Deliveries_Fields field set found. "
            "Verify in Setup that field order is: (1) Client, (2) Program Engagement, (3) Service. "
            "Incorrect order breaks cascading lookup filtering silently."
        )

    return issues


def check_pmm_namespace_objects_present(manifest_dir: Path) -> list[str]:
    """Verify that at least some pmdm__ namespace objects are in the manifest.

    If none are present, warn that the manifest may not include PMM objects,
    so this checker cannot fully validate PMM configuration.
    """
    issues: list[str] = []

    pmm_files = find_xml_files(manifest_dir, "pmdm__*.object-meta.xml")
    pmm_files += find_xml_files(manifest_dir, "pmdm__*.field-meta.xml")

    if not pmm_files:
        issues.append(
            "No pmdm__ namespace metadata found in manifest directory. "
            "PMM checks cannot run. Ensure the metadata manifest includes PMM objects "
            "(pmdm__ServiceDelivery__c, pmdm__ProgramEngagement__c, etc.) before running this checker."
        )

    return issues


def check_orphan_service_records(manifest_dir: Path) -> list[str]:
    """Check for Service__c validation rules that enforce the Program__c lookup.

    Without a validation rule, Service__c records can be created without a
    parent Program__c, making them unusable in bulk service delivery.
    """
    issues: list[str] = []

    service_obj_files = find_xml_files(manifest_dir, "pmdm__Service__c.object-meta.xml")
    service_obj_files += find_xml_files(manifest_dir, "Service__c.object-meta.xml")
    service_vr_files = find_xml_files(manifest_dir, "pmdm__Service__c.*.validationRule-meta.xml")
    service_vr_files += find_xml_files(manifest_dir, "Service__c.*.validationRule-meta.xml")

    has_service_vr = bool(service_vr_files)
    if not has_service_vr:
        for obj_path in service_obj_files:
            root_el = read_xml(obj_path)
            if root_el is None:
                continue
            for child in root_el:
                if strip_ns(child.tag) == "validationRules":
                    has_service_vr = True
                    break

    if service_obj_files and not has_service_vr:
        issues.append(
            "No validation rules found on Service__c (pmdm__Service__c). "
            "Consider adding a validation rule to require pmdm__Program__c to be non-blank, "
            "preventing orphaned Service records that cannot be used in Bulk Service Delivery."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_npsp_program_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_pmm_namespace_objects_present(manifest_dir))

    # Only run detailed checks if namespace objects are present.
    pmm_present = not any("pmdm__ namespace metadata not found" in i for i in issues)
    if pmm_present:
        issues.extend(check_service_delivery_validation_rules(manifest_dir))
        issues.extend(check_bulk_service_delivery_fieldset(manifest_dir))
        issues.extend(check_orphan_service_records(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_npsp_program_management(manifest_dir)

    if not issues:
        print("No PMM configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
