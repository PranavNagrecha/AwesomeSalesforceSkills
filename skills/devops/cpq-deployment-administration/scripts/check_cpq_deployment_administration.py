#!/usr/bin/env python3
"""Checker script for CPQ Deployment Administration skill.

Checks a Salesforce metadata directory for common CPQ deployment anti-patterns:
- SBQQ objects incorrectly included in metadata deploy scope
- Missing external ID fields on SBQQ objects
- Potentially dangerous ordering in deployment scripts or plan files

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_deployment_administration.py [--help]
    python3 check_cpq_deployment_administration.py --manifest-dir path/to/metadata
    python3 check_cpq_deployment_administration.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# SBQQ objects that are sObject data records — cannot be deployed via Metadata API
SBQQ_DATA_OBJECTS = {
    "SBQQ__PriceRule__c",
    "SBQQ__PriceAction__c",
    "SBQQ__PriceCondition__c",
    "SBQQ__ProductRule__c",
    "SBQQ__ProductAction__c",
    "SBQQ__ErrorCondition__c",
    "SBQQ__OptionConstraint__c",
    "SBQQ__QuoteTemplate__c",
    "SBQQ__TemplateSection__c",
    "SBQQ__TemplateContent__c",
    "SBQQ__CustomClass__c",
    "SBQQ__ConfigurationRule__c",
    "SBQQ__SummaryVariable__c",
}

# Required parent-before-child ordering for CPQ data migration
CPQ_DEPLOY_ORDER = [
    "Product2",
    "Pricebook2",
    "PricebookEntry",
    "SBQQ__ProductRule__c",
    "SBQQ__PriceRule__c",
    "SBQQ__PriceCondition__c",
    "SBQQ__PriceAction__c",
    "SBQQ__OptionConstraint__c",
    "SBQQ__QuoteTemplate__c",
    "SBQQ__TemplateSection__c",
    "SBQQ__TemplateContent__c",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata directory for CPQ deployment anti-patterns. "
            "Detects SBQQ data objects incorrectly treated as metadata, missing external ID "
            "field definitions, and incorrect CPQ object ordering in migration plan files."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def check_package_xml_for_sbqq_records(manifest_dir: Path) -> list[str]:
    """Detect if a package.xml includes SBQQ data objects as CustomObject members.

    SBQQ data objects should NOT be in a metadata deploy package — they are sObject records.
    A package.xml that includes them will deploy only the schema, not any configuration data.
    """
    issues: list[str] = []
    package_xml = manifest_dir / "package.xml"
    if not package_xml.exists():
        # Try common alternative paths
        candidates = list(manifest_dir.rglob("package.xml"))
        if not candidates:
            return issues
        package_xml = candidates[0]

    try:
        tree = ET.parse(package_xml)
        root = tree.getroot()
        # Handle namespace
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        for type_elem in root.findall(f"{ns}types"):
            name_elem = type_elem.find(f"{ns}name")
            if name_elem is None or name_elem.text != "CustomObject":
                continue
            for member in type_elem.findall(f"{ns}members"):
                if member.text and member.text in SBQQ_DATA_OBJECTS:
                    issues.append(
                        f"ANTI-PATTERN: '{member.text}' found in package.xml as a CustomObject member. "
                        f"CPQ configuration objects are data records, not metadata. "
                        f"This deploy will copy the schema only — zero CPQ configuration records will move. "
                        f"Use Prodly, SFDMU, or a data loader instead."
                    )
    except ET.ParseError as exc:
        issues.append(f"Could not parse package.xml: {exc}")

    return issues


def check_external_id_fields_on_sbqq_objects(manifest_dir: Path) -> list[str]:
    """Warn if SBQQ objects exist in the metadata but lack a custom external ID field.

    External ID fields are required for upsert-based CPQ data migration.
    """
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Try force-app/main/default/objects or similar
        candidates = list(manifest_dir.rglob("objects"))
        candidates = [c for c in candidates if c.is_dir()]
        if not candidates:
            return issues
        objects_dir = candidates[0]

    for sbqq_obj in SBQQ_DATA_OBJECTS:
        obj_dir = objects_dir / sbqq_obj
        if not obj_dir.exists():
            continue  # Object not in this metadata set — skip

        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            issues.append(
                f"WARN: '{sbqq_obj}' is present in metadata but has no 'fields' subdirectory. "
                f"Ensure a custom External ID text field (e.g. CPQ_External_Id__c) is defined "
                f"and deployed to both source and target orgs before data migration."
            )
            continue

        # Check for at least one field with externalId = true
        has_external_id = False
        for field_file in fields_dir.glob("*.field-meta.xml"):
            try:
                tree = ET.parse(field_file)
                root = tree.getroot()
                ns = ""
                if root.tag.startswith("{"):
                    ns = root.tag.split("}")[0] + "}"
                ext_id_elem = root.find(f"{ns}externalId")
                if ext_id_elem is not None and ext_id_elem.text == "true":
                    has_external_id = True
                    break
            except ET.ParseError:
                continue

        if not has_external_id:
            issues.append(
                f"WARN: '{sbqq_obj}' has no External ID field defined in its metadata. "
                f"Add a custom text field marked as 'External ID' (e.g. CPQ_External_Id__c) "
                f"to enable idempotent upsert-based CPQ data migration."
            )

    return issues


def check_sfdmu_plan_ordering(manifest_dir: Path) -> list[str]:
    """Check SFDMU export plan JSON files for incorrect CPQ object ordering."""
    issues: list[str] = []

    plan_files = list(manifest_dir.rglob("*.json"))
    plan_files += list(manifest_dir.rglob("exportPlan.json"))

    for plan_file in plan_files:
        try:
            with plan_file.open() as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        # SFDMU plan files have an "objects" or top-level list structure
        objects_list: list = []
        if isinstance(data, list):
            objects_list = data
        elif isinstance(data, dict) and "objects" in data:
            objects_list = data["objects"]
        else:
            continue

        # Extract object names from query fields
        found_cpq_objects: list[str] = []
        for entry in objects_list:
            if not isinstance(entry, dict):
                continue
            query = entry.get("query", "")
            for obj in CPQ_DEPLOY_ORDER:
                if obj.upper() in query.upper() and obj not in found_cpq_objects:
                    found_cpq_objects.append(obj)

        # Check ordering: Price Actions must come after Price Rules
        if "SBQQ__PriceAction__c" in found_cpq_objects and "SBQQ__PriceRule__c" in found_cpq_objects:
            action_idx = found_cpq_objects.index("SBQQ__PriceAction__c")
            rule_idx = found_cpq_objects.index("SBQQ__PriceRule__c")
            if action_idx < rule_idx:
                issues.append(
                    f"ORDERING ERROR in {plan_file.name}: "
                    f"'SBQQ__PriceAction__c' appears before 'SBQQ__PriceRule__c'. "
                    f"Price Actions depend on their parent Price Rule. "
                    f"Import SBQQ__PriceRule__c first."
                )

        # Check ordering: Template children must come after template header
        if "SBQQ__TemplateSection__c" in found_cpq_objects and "SBQQ__QuoteTemplate__c" in found_cpq_objects:
            section_idx = found_cpq_objects.index("SBQQ__TemplateSection__c")
            template_idx = found_cpq_objects.index("SBQQ__QuoteTemplate__c")
            if section_idx < template_idx:
                issues.append(
                    f"ORDERING ERROR in {plan_file.name}: "
                    f"'SBQQ__TemplateSection__c' appears before 'SBQQ__QuoteTemplate__c'. "
                    f"Template sections depend on their parent Quote Template. "
                    f"Import SBQQ__QuoteTemplate__c first."
                )

    return issues


def check_hardcoded_salesforce_ids_in_scripts(manifest_dir: Path) -> list[str]:
    """Detect hardcoded Salesforce Record IDs in shell scripts or CSV files in the manifest.

    Hardcoded IDs are org-specific and will fail when used in a different org.
    """
    issues: list[str] = []
    # Salesforce IDs: 15-char or 18-char alphanumeric starting with known key prefixes
    # This heuristic targets SBQQ-prefixed or generic object ID patterns in script files
    id_pattern = re.compile(r"\b[a-zA-Z0-9]{15,18}\b")
    sbqq_id_prefix_pattern = re.compile(r"'[a-zA-Z0-9]{15,18}'|\"[a-zA-Z0-9]{15,18}\"")

    for script_file in list(manifest_dir.rglob("*.sh")) + list(manifest_dir.rglob("*.bat")):
        try:
            content = script_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Look for lines that contain SBQQ object names and also match ID-like strings
        for lineno, line in enumerate(content.splitlines(), start=1):
            if any(obj in line for obj in SBQQ_DATA_OBJECTS):
                matches = sbqq_id_prefix_pattern.findall(line)
                for match in matches:
                    inner = match.strip("'\"")
                    if len(inner) in (15, 18) and inner.isalnum():
                        issues.append(
                            f"POTENTIAL HARDCODED ORG ID in {script_file.name}:{lineno}: "
                            f"'{inner}' looks like a Salesforce Record ID used with a CPQ object. "
                            f"Record IDs are org-specific. Use External ID fields for cross-org migration instead."
                        )

    return issues


def check_cpq_deployment_administration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_package_xml_for_sbqq_records(manifest_dir))
    issues.extend(check_external_id_fields_on_sbqq_objects(manifest_dir))
    issues.extend(check_sfdmu_plan_ordering(manifest_dir))
    issues.extend(check_hardcoded_salesforce_ids_in_scripts(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cpq_deployment_administration(manifest_dir)

    if not issues:
        print("No CPQ deployment administration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
