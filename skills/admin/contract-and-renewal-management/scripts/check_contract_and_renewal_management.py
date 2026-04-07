#!/usr/bin/env python3
"""Checker script for Contract and Renewal Management skill.

Checks Salesforce CPQ metadata for common contract and renewal configuration issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_contract_and_renewal_management.py [--help]
    python3 check_contract_and_renewal_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CPQ Contract and Renewal Management configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file, returning None on any parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def check_subscription_fields_on_product(manifest_dir: Path) -> list[str]:
    """Check Product2 custom fields for SBQQ__SubscriptionPricing__c and SBQQ__SubscriptionType__c.

    These fields must exist for CPQ contract creation to generate SBQQ__Subscription__c records.
    """
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    # Look for Product2 object directory or file
    product2_dir = objects_dir / "Product2"
    if not product2_dir.exists():
        return issues

    fields_dir = product2_dir / "fields"
    if not fields_dir.exists():
        return issues

    existing_field_names = {f.stem for f in fields_dir.glob("*.field-meta.xml")}

    required_cpq_fields = {
        "SBQQ__SubscriptionPricing__c",
        "SBQQ__SubscriptionType__c",
    }
    missing = required_cpq_fields - existing_field_names
    for field in sorted(missing):
        issues.append(
            f"Product2 is missing CPQ field {field}. "
            "Without this field, CPQ contract creation will not generate SBQQ__Subscription__c records. "
            "Ensure the Salesforce CPQ managed package is installed."
        )

    return issues


def check_contract_object_for_cpq_fields(manifest_dir: Path) -> list[str]:
    """Check Contract object for key CPQ fields needed for renewal and amendment."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    contract_dir = objects_dir / "Contract"
    if not contract_dir.exists():
        return issues

    fields_dir = contract_dir / "fields"
    if not fields_dir.exists():
        return issues

    existing_field_names = {f.stem for f in fields_dir.glob("*.field-meta.xml")}

    key_cpq_contract_fields = {
        "SBQQ__DefaultRenewalTerm__c",
        "SBQQ__RenewedContract__c",
        "SBQQ__RenewalQuoted__c",
    }
    missing = key_cpq_contract_fields - existing_field_names
    for field in sorted(missing):
        issues.append(
            f"Contract object is missing CPQ field {field}. "
            "This field is required for CPQ renewal lifecycle management. "
            "Ensure the Salesforce CPQ managed package is installed and deployed."
        )

    return issues


def check_subscription_object_exists(manifest_dir: Path) -> list[str]:
    """Check that SBQQ__Subscription__c object metadata is present."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    subscription_dir = objects_dir / "SBQQ__Subscription__c"
    # Also accept a flat .object-meta.xml file
    subscription_file = objects_dir / "SBQQ__Subscription__c.object-meta.xml"

    if not subscription_dir.exists() and not subscription_file.exists():
        issues.append(
            "SBQQ__Subscription__c object metadata not found in the manifest. "
            "This object is the core of CPQ contract management. "
            "Ensure the Salesforce CPQ managed package metadata is included in your retrieval."
        )

    return issues


def check_flows_for_direct_subscription_edits(manifest_dir: Path) -> list[str]:
    """Scan Flow metadata for record updates targeting SBQQ__Subscription__c directly.

    Direct updates to SBQQ__Subscription__c outside of the CPQ amendment flow
    corrupt the contract lifecycle and break renewal generation.
    """
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        root = _parse_xml_safe(flow_file)
        if root is None:
            continue

        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        # Look for recordUpdates or recordCreates targeting SBQQ__Subscription__c
        for record_update in root.findall(".//recordUpdates", ns) or root.findall(".//recordUpdates"):
            object_elem = record_update.find("object") or record_update.find(
                "{http://soap.sforce.com/2006/04/metadata}object"
            )
            if object_elem is not None and object_elem.text == "SBQQ__Subscription__c":
                issues.append(
                    f"Flow '{flow_file.stem}' contains a Record Update targeting SBQQ__Subscription__c directly. "
                    "Direct updates to CPQ Subscription records bypass amendment proration, "
                    "co-termination, and approval logic. Use the CPQ Amendment flow instead."
                )

    return issues


def check_apex_for_direct_subscription_edits(manifest_dir: Path) -> list[str]:
    """Scan Apex classes for DML on SBQQ__Subscription__c outside of test classes."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    suspicious_patterns = [
        "update sub",
        "update subscription",
        "Database.update(sub",
        "Database.update(subscription",
    ]

    for apex_file in classes_dir.glob("*.cls"):
        # Skip test classes
        content = apex_file.read_text(encoding="utf-8", errors="replace")
        if "@isTest" in content or "testMethod" in content.lower():
            continue

        content_lower = content.lower()
        if "sbqq__subscription__c" in content_lower:
            for pattern in suspicious_patterns:
                if pattern.lower() in content_lower:
                    issues.append(
                        f"Apex class '{apex_file.stem}' may be directly updating SBQQ__Subscription__c records "
                        f"(found pattern: '{pattern}'). "
                        "Direct DML on CPQ Subscription records outside of the CPQ amendment flow "
                        "can corrupt contract and renewal state. Review and refactor to use the amendment API."
                    )
                    break  # One issue per file is enough

    return issues


def check_contract_and_renewal_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_subscription_fields_on_product(manifest_dir))
    issues.extend(check_contract_object_for_cpq_fields(manifest_dir))
    issues.extend(check_subscription_object_exists(manifest_dir))
    issues.extend(check_flows_for_direct_subscription_edits(manifest_dir))
    issues.extend(check_apex_for_direct_subscription_edits(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_contract_and_renewal_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
