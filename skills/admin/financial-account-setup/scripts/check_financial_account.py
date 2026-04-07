#!/usr/bin/env python3
"""Checker script for FSC Financial Account Setup skill.

Validates exported Salesforce metadata for common FSC financial account
configuration issues: namespace consistency, required picklist values,
record type completeness, and held-away account flag presence.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_financial_account.py [--help]
    python3 check_financial_account.py --manifest-dir path/to/metadata
    python3 check_financial_account.py --manifest-dir . --namespace FinServ
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Core FSC picklist values — at minimum one retirement and one brokerage type
# should be present. Production orgs will have more, but these signal that
# the picklist has been meaningfully configured.
REQUIRED_FINANCIAL_ACCOUNT_TYPES = {
    "retirement": [
        "401k",
        "403b",
        "Traditional IRA",
        "Roth IRA",
        "Individual IRA",
        "SEP IRA",
        "SIMPLE IRA",
    ],
    "brokerage": [
        "Individual Brokerage",
        "Joint Brokerage",
        "Brokerage",
    ],
    "deposit": [
        "Checking",
        "Savings",
        "Money Market",
        "CD",
        "Certificate of Deposit",
    ],
}

# Required role values on the FinancialAccountRole picklist
REQUIRED_ROLE_VALUES = [
    "Primary Owner",
    "Joint Owner",
    "Beneficiary",
]

# Namespace prefixes — managed-package uses FinServ__, Core FSC uses none
MANAGED_PACKAGE_NAMESPACE = "FinServ"
CORE_FSC_OBJECT_NAME = "FinancialAccount"
MANAGED_PKG_OBJECT_NAME = "FinServ__FinancialAccount__c"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_xml_files(directory: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under directory."""
    return sorted(directory.rglob(pattern))


def _parse_xml(path: Path) -> ET.Element | None:
    """Parse an XML file, returning the root element or None on error."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError as exc:
        return None


def _strip_namespace(tag: str) -> str:
    """Remove {namespace} prefix from an XML tag if present."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _get_text(element: ET.Element, tag: str) -> str:
    """Return text of the first child element matching tag, or empty string."""
    child = element.find(tag)
    if child is None:
        # Try namespace-stripped search
        for c in element:
            if _strip_namespace(c.tag) == tag:
                return (c.text or "").strip()
        return ""
    return (child.text or "").strip()


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_namespace_consistency(manifest_dir: Path, namespace: str) -> list[str]:
    """Flag Apex files and metadata XML that mix namespace and no-namespace references."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        has_namespaced_object = MANAGED_PKG_OBJECT_NAME in content
        has_core_fsc_object = CORE_FSC_OBJECT_NAME in content and MANAGED_PKG_OBJECT_NAME not in content

        if has_namespaced_object and has_core_fsc_object:
            issues.append(
                f"NAMESPACE_MISMATCH in {apex_file.name}: file references both "
                f"'{MANAGED_PKG_OBJECT_NAME}' (managed-package) and bare "
                f"'{CORE_FSC_OBJECT_NAME}' (Core FSC). Standardize on one model."
            )

        # Check for field references without namespace when object uses namespace
        if has_namespaced_object:
            # Common naked field names that should have FinServ__ prefix in managed-package orgs
            naked_fields = [".Balance__c", ".PrimaryOwner__c", ".FinancialAccountType__c"]
            for field in naked_fields:
                if field in content:
                    issues.append(
                        f"POSSIBLE_NAMESPACE_ERROR in {apex_file.name}: found field reference "
                        f"'{field}' which may be missing the '{namespace}__' prefix in a "
                        f"managed-package org. Expected: '{namespace}__{field.lstrip('.')}'."
                    )

    return issues


def check_financial_account_type_picklist(manifest_dir: Path, namespace: str) -> list[str]:
    """Verify FinancialAccountType picklist contains at least one value per required category."""
    issues: list[str] = []

    # Look for the FinancialAccount object metadata file
    object_files = (
        list(manifest_dir.rglob(f"{namespace}__FinancialAccount__c.object-meta.xml"))
        + list(manifest_dir.rglob("FinancialAccount.object-meta.xml"))
        + list(manifest_dir.rglob(f"{namespace}__FinancialAccount__c.object"))
        + list(manifest_dir.rglob("FinancialAccount.object"))
    )

    if not object_files:
        # No object file found — cannot validate, but not necessarily an error
        return issues

    for object_file in object_files:
        root = _parse_xml(object_file)
        if root is None:
            issues.append(f"XML_PARSE_ERROR: Could not parse {object_file.name}")
            continue

        # Collect all picklist values defined in the object metadata
        found_values: set[str] = set()
        for field_elem in root.iter():
            if _strip_namespace(field_elem.tag) in ("CustomField", "fields"):
                field_name = _get_text(field_elem, "fullName") or _get_text(field_elem, "name")
                if "FinancialAccountType" in field_name or "financialAccountType" in field_name.lower():
                    for value_elem in field_elem.iter():
                        if _strip_namespace(value_elem.tag) == "value":
                            v = _get_text(value_elem, "fullName") or (value_elem.text or "").strip()
                            if v:
                                found_values.add(v)

        if not found_values:
            # Field not found inline — check separate field metadata
            field_files = (
                list(manifest_dir.rglob(f"*{namespace}__FinancialAccountType__c.field-meta.xml"))
                + list(manifest_dir.rglob("*FinancialAccountType.field-meta.xml"))
            )
            for ff in field_files:
                ff_root = _parse_xml(ff)
                if ff_root is None:
                    continue
                for ve in ff_root.iter():
                    if _strip_namespace(ve.tag) == "value":
                        v = _get_text(ve, "fullName") or (ve.text or "").strip()
                        if v:
                            found_values.add(v)

        # Check each required category has at least one matching value
        for category, expected_values in REQUIRED_FINANCIAL_ACCOUNT_TYPES.items():
            matches = [v for v in found_values if v in expected_values]
            if not matches:
                issues.append(
                    f"MISSING_ACCOUNT_TYPE_CATEGORY: No '{category}' account type value found in "
                    f"FinancialAccountType picklist. Expected at least one of: {expected_values}. "
                    f"Found values: {sorted(found_values) if found_values else 'none detected'}."
                )

    return issues


def check_financial_account_role_picklist(manifest_dir: Path, namespace: str) -> list[str]:
    """Verify the Role picklist on FinancialAccountRole includes required values."""
    issues: list[str] = []

    role_object_files = (
        list(manifest_dir.rglob(f"{namespace}__FinancialAccountRole__c.object-meta.xml"))
        + list(manifest_dir.rglob("FinancialAccountRole.object-meta.xml"))
        + list(manifest_dir.rglob(f"{namespace}__FinancialAccountRole__c.object"))
        + list(manifest_dir.rglob("FinancialAccountRole.object"))
    )

    field_files = (
        list(manifest_dir.rglob(f"*{namespace}__Role__c.field-meta.xml"))
        + list(manifest_dir.rglob("*Role.field-meta.xml"))
    )

    found_role_values: set[str] = set()

    for source_file in role_object_files + field_files:
        root = _parse_xml(source_file)
        if root is None:
            continue
        for elem in root.iter():
            if _strip_namespace(elem.tag) == "value":
                v = _get_text(elem, "fullName") or (elem.text or "").strip()
                if v:
                    found_role_values.add(v)

    if role_object_files or field_files:
        for required_role in REQUIRED_ROLE_VALUES:
            if required_role not in found_role_values:
                issues.append(
                    f"MISSING_ROLE_VALUE: Required role value '{required_role}' not found in "
                    f"FinancialAccountRole Role picklist. "
                    f"Found: {sorted(found_role_values) if found_role_values else 'none detected'}."
                )

    return issues


def check_held_away_field_presence(manifest_dir: Path, namespace: str) -> list[str]:
    """Check whether a held-away indicator field exists on FinancialAccount."""
    issues: list[str] = []

    # Look for HeldAway field in object or field metadata
    held_away_patterns = [
        f"*{namespace}__HeldAway__c.field-meta.xml",
        "*HeldAway.field-meta.xml",
        "*held_away*.field-meta.xml",
    ]

    found = False
    for pattern in held_away_patterns:
        if list(manifest_dir.rglob(pattern)):
            found = True
            break

    # Also check inside object files
    if not found:
        object_files = (
            list(manifest_dir.rglob(f"{namespace}__FinancialAccount__c.object-meta.xml"))
            + list(manifest_dir.rglob("FinancialAccount.object-meta.xml"))
        )
        for obj_file in object_files:
            try:
                content = obj_file.read_text(encoding="utf-8", errors="ignore")
                if "HeldAway" in content or "held_away" in content.lower():
                    found = True
                    break
            except OSError:
                continue

    if not found:
        # Informational — not all orgs need held-away accounts
        issues.append(
            "INFO_HELD_AWAY_FIELD: No HeldAway indicator field detected on FinancialAccount. "
            "If held-away accounts (externally held assets) are in scope, add a "
            f"'{namespace}__HeldAway__c' (Boolean) field and implement validation rules to "
            "prevent unauthorized balance edits on held-away records."
        )

    return issues


def check_record_types_present(manifest_dir: Path, namespace: str) -> list[str]:
    """Check that at least one record type exists for FinancialAccount."""
    issues: list[str] = []

    record_type_files = (
        list(manifest_dir.rglob(f"{namespace}__FinancialAccount__c.*.recordType-meta.xml"))
        + list(manifest_dir.rglob("FinancialAccount.*.recordType-meta.xml"))
    )

    # Also check for record type definitions inside the object file
    object_files = (
        list(manifest_dir.rglob(f"{namespace}__FinancialAccount__c.object-meta.xml"))
        + list(manifest_dir.rglob("FinancialAccount.object-meta.xml"))
    )
    found_in_object = False
    for obj_file in object_files:
        try:
            content = obj_file.read_text(encoding="utf-8", errors="ignore")
            if "<recordTypes>" in content or "recordType" in content.lower():
                found_in_object = True
                break
        except OSError:
            continue

    if not record_type_files and not found_in_object:
        issues.append(
            "MISSING_RECORD_TYPES: No record type metadata found for FinancialAccount. "
            "FSC best practice requires separate record types per account category "
            "(retirement, brokerage, deposit, insurance, education savings) to control "
            "page layouts and field visibility per account type."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_financial_account(manifest_dir: Path, namespace: str = MANAGED_PACKAGE_NAMESPACE) -> list[str]:
    """Run all FSC financial account configuration checks.

    Args:
        manifest_dir: Root directory of the exported Salesforce metadata.
        namespace: FSC namespace prefix. 'FinServ' for managed-package orgs;
                   empty string '' for Core FSC orgs.

    Returns:
        List of issue strings. Empty list means no issues detected.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"MANIFEST_NOT_FOUND: Directory does not exist: {manifest_dir}")
        return issues

    issues.extend(check_namespace_consistency(manifest_dir, namespace))
    issues.extend(check_financial_account_type_picklist(manifest_dir, namespace))
    issues.extend(check_financial_account_role_picklist(manifest_dir, namespace))
    issues.extend(check_held_away_field_presence(manifest_dir, namespace))
    issues.extend(check_record_types_present(manifest_dir, namespace))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC Financial Account configuration metadata for common setup issues. "
            "Validates namespace consistency, required picklist values, record type presence, "
            "and held-away account field configuration."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the exported Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--namespace",
        default=MANAGED_PACKAGE_NAMESPACE,
        help=(
            f"FSC namespace prefix (default: '{MANAGED_PACKAGE_NAMESPACE}' for managed-package orgs). "
            "Use empty string '' for Core FSC orgs (Winter '23+)."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    namespace = args.namespace

    print(f"Checking FSC financial account configuration in: {manifest_dir}")
    print(f"Namespace prefix: '{namespace}' ({'managed-package' if namespace else 'Core FSC'})")
    print()

    issues = check_financial_account(manifest_dir, namespace)

    info_issues = [i for i in issues if i.startswith("INFO_")]
    warn_issues = [i for i in issues if not i.startswith("INFO_")]

    if warn_issues:
        print("Issues found:", file=sys.stderr)
        for issue in warn_issues:
            print(f"  WARN: {issue}", file=sys.stderr)
        print(file=sys.stderr)

    if info_issues:
        print("Informational notes:")
        for note in info_issues:
            print(f"  INFO: {note}")
        print()

    if not warn_issues:
        print("No blocking issues found.")
        if info_issues:
            print("Review informational notes above.")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
