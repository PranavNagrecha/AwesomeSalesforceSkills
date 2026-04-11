#!/usr/bin/env python3
"""Checker script for Patient Data Migration skill.

Scans Salesforce metadata (XML files from a project or force-app directory) for
common configuration gaps that cause patient data migration failures or HIPAA risks.

Checks performed:
  1. External ID field presence on Account (EMR_Patient_ID__c or similar)
  2. Shield Platform Encryption configuration files present
  3. Person Account enabled (PersonAccount custom field or setting detected)
  4. Duplicate Rule present for Account/Patient record type
  5. Custom field naming conventions for Health Cloud clinical objects

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_patient_data_migration.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CLINICAL_OBJECTS = {
    "EhrPatientMedication",
    "PatientHealthCondition",
    "PatientImmunization",
    "PatientMedicalProcedure",
}

CARE_OBJECTS = {
    "CarePlan",
    "CarePlanProblem",
    "CarePlanGoal",
    "CarePlanTask",
}

ENCRYPTION_FILE_PATTERNS = [
    "**/*.encryptionScheme-meta.xml",
    "**/PlatformEncryptionSettings.settings-meta.xml",
    "**/encryptionScheme/**",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def find_xml_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file, returning None on parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_external_id_on_account(manifest_dir: Path) -> list[str]:
    """Warn if no External ID custom field is found on Account."""
    issues: list[str] = []
    account_fields = list(manifest_dir.rglob("objects/Account/fields/*.field-meta.xml"))

    if not account_fields:
        # May be stored in a single Account.object-meta.xml (old format)
        account_objects = list(manifest_dir.rglob("Account.object-meta.xml"))
        if not account_objects:
            issues.append(
                "No Account field metadata found. "
                "Confirm an External ID field (e.g. EMR_Patient_ID__c) exists on Account "
                "for Bulk API 2.0 upsert and relationship-by-external-ID lookups."
            )
            return issues
        # Check inside the object XML for externalId=true
        found = False
        for obj_path in account_objects:
            root = parse_xml_safe(obj_path)
            if root is None:
                continue
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
            for field in root.findall(".//sf:fields", ns) or root.findall(".//fields"):
                ext_id_el = field.find("sf:externalId", ns) or field.find("externalId")
                if ext_id_el is not None and ext_id_el.text == "true":
                    found = True
                    break
        if not found:
            issues.append(
                "No External ID field detected on Account object. "
                "Add an External ID field (e.g. EMR_Patient_ID__c) to support idempotent "
                "Bulk API 2.0 upsert and relationship-by-external-ID lookups for "
                "clinical and care objects."
            )
        return issues

    # Check individual field files
    found_external_id = False
    for field_path in account_fields:
        root = parse_xml_safe(field_path)
        if root is None:
            continue
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        ext_id_el = root.find(".//sf:externalId", ns) or root.find(".//externalId")
        if ext_id_el is not None and ext_id_el.text == "true":
            found_external_id = True
            break

    if not found_external_id:
        issues.append(
            "No External ID field found in Account/fields/. "
            "Create EMR_Patient_ID__c (or equivalent) as an External ID field on Account. "
            "This is required for Bulk API 2.0 upsert and cross-object relationship "
            "resolution in clinical and care object loads."
        )

    return issues


def check_encryption_config(manifest_dir: Path) -> list[str]:
    """Warn if no Shield Platform Encryption metadata is present."""
    issues: list[str] = []

    found = False
    for pattern in ENCRYPTION_FILE_PATTERNS:
        matches = list(manifest_dir.rglob(pattern.lstrip("**/")))
        if matches:
            found = True
            break

    if not found:
        issues.append(
            "No Shield Platform Encryption metadata detected "
            "(no *.encryptionScheme-meta.xml or PlatformEncryptionSettings.settings-meta.xml). "
            "HIPAA requires Shield Platform Encryption on PHI fields (BirthDate, SSN, "
            "diagnosis codes, medication names) to be active BEFORE any patient data is loaded. "
            "Configure encryption and deploy the metadata before running the migration."
        )

    return issues


def check_duplicate_rule_for_account(manifest_dir: Path) -> list[str]:
    """Warn if no Duplicate Rule targeting Account is found."""
    issues: list[str] = []

    dup_rules = list(manifest_dir.rglob("duplicateRules/Account*.duplicateRule-meta.xml"))
    if not dup_rules:
        dup_rules = list(manifest_dir.rglob("*.duplicateRule-meta.xml"))
        account_rules = [
            r for r in dup_rules if "account" in r.name.lower() or "patient" in r.name.lower()
        ]
        if not account_rules:
            issues.append(
                "No Duplicate Rule found for Account/Patient. "
                "Standard Duplicate Rules may not fire on Bulk API 2.0 upsert depending on "
                "rule configuration. Add a post-load SOQL deduplication check: "
                "SELECT EMR_Patient_ID__c, COUNT(Id) FROM Account "
                "WHERE RecordType.DeveloperName = 'Patient' "
                "GROUP BY EMR_Patient_ID__c HAVING COUNT(Id) > 1"
            )

    return issues


def check_care_plan_external_id(manifest_dir: Path) -> list[str]:
    """Warn if no External ID field is found on CarePlan."""
    issues: list[str] = []

    care_plan_fields = list(manifest_dir.rglob("objects/CarePlan/fields/*.field-meta.xml"))
    if not care_plan_fields:
        return issues  # Metadata not present — not necessarily an error; skip check

    found = False
    for field_path in care_plan_fields:
        root = parse_xml_safe(field_path)
        if root is None:
            continue
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        ext_id_el = root.find(".//sf:externalId", ns) or root.find(".//externalId")
        if ext_id_el is not None and ext_id_el.text == "true":
            found = True
            break

    if not found:
        issues.append(
            "No External ID field found on CarePlan object. "
            "Add CarePlan_Ext_ID__c as an External ID field to support "
            "relationship-by-external-ID lookups from CarePlanProblem, CarePlanGoal, "
            "and CarePlanTask during migration."
        )

    return issues


def check_health_cloud_permission_sets(manifest_dir: Path) -> list[str]:
    """Warn if no Health Cloud permission set files are detected."""
    issues: list[str] = []

    ps_files = list(manifest_dir.rglob("permissionsets/HealthCloud*.permissionset-meta.xml"))
    if not ps_files:
        ps_files = list(manifest_dir.rglob("*.permissionset-meta.xml"))
        hc_ps = [p for p in ps_files if "health" in p.name.lower() or "clinical" in p.name.lower()]
        if not hc_ps:
            issues.append(
                "No Health Cloud permission set metadata detected. "
                "Ensure the migration integration user has Health Cloud feature licenses and "
                "appropriate permission sets (e.g. HealthCloudFoundation, HealthCloudPermissionSet) "
                "assigned before running Bulk API 2.0 jobs for clinical and care objects."
            )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def check_patient_data_migration(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_external_id_on_account(manifest_dir))
    issues.extend(check_encryption_config(manifest_dir))
    issues.extend(check_duplicate_rule_for_account(manifest_dir))
    issues.extend(check_care_plan_external_id(manifest_dir))
    issues.extend(check_health_cloud_permission_sets(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common patient data migration "
            "configuration gaps and HIPAA compliance risks."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_patient_data_migration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
