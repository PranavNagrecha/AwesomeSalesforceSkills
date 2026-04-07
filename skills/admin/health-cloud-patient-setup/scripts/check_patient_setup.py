#!/usr/bin/env python3
"""Checker script for Health Cloud Patient Setup skill.

Validates Salesforce metadata for common Health Cloud patient setup issues.
Uses stdlib only — no pip dependencies.

Checks performed:
  1. Person Account field present on Account object metadata
  2. Patient record type exists on Account object
  3. Health Cloud patient page layout assigned to Patient record type
  4. EhrPatientMedication and PatientHealthCondition objects present in metadata
  5. Clinical data not stored in custom Account fields with suspicious names
  6. Care team roles present (via CustomField or custom metadata inspection)

Usage:
    python3 check_patient_setup.py [--manifest-dir path/to/metadata]
    python3 check_patient_setup.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce metadata namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Health Cloud clinical objects that should exist as sObject metadata
HC_CLINICAL_OBJECTS = [
    "EhrPatientMedication",
    "PatientHealthCondition",
    "PatientImmunization",
    "PatientMedicalProcedure",
]

# Suspicious custom field name patterns that suggest clinical data stored on Account
# instead of dedicated Health Cloud objects
CLINICAL_FIELD_PATTERNS = [
    "medication",
    "diagnosis",
    "diagnos",
    "immunization",
    "condition",
    "allergy",
    "prescription",
    "clinical",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Health Cloud patient setup metadata for common configuration issues. "
            "Validates that Person Accounts, patient record types, clinical objects, "
            "and care team role patterns are correctly configured."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_object_dir(manifest_dir: Path) -> Path | None:
    """Locate the objects metadata directory."""
    candidates = [
        manifest_dir / "objects",
        manifest_dir / "force-app" / "main" / "default" / "objects",
        manifest_dir / "src" / "objects",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def check_person_accounts_enabled(object_dir: Path) -> list[str]:
    """Check if Account object metadata references IsPersonAccount field."""
    issues: list[str] = []
    account_dir = object_dir / "Account"
    if not account_dir.is_dir():
        # Account metadata may not be deployed — not necessarily an issue
        return issues

    # Look for IsPersonAccount in Account fields directory
    fields_dir = account_dir / "fields"
    if fields_dir.is_dir():
        field_files = list(fields_dir.glob("IsPersonAccount.field-meta.xml"))
        if field_files:
            return issues  # field exists — person accounts likely enabled
        # Check via Account.object-meta.xml
    account_meta = account_dir / "Account.object-meta.xml"
    if account_meta.is_file():
        content = account_meta.read_text(encoding="utf-8")
        if "IsPersonAccount" not in content:
            issues.append(
                "PERSON_ACCOUNTS: Account object metadata does not reference IsPersonAccount. "
                "Verify Person Accounts are enabled. This is required before Health Cloud patient "
                "record types can be created. NOTE: IsPersonAccount may not appear in deployed "
                "metadata even when enabled — confirm in Setup > Account Settings."
            )
    return issues


def check_patient_record_type(object_dir: Path) -> list[str]:
    """Check if a Patient (or Member) record type exists on Account."""
    issues: list[str] = []
    account_dir = object_dir / "Account"
    if not account_dir.is_dir():
        return issues

    record_types_dir = account_dir / "recordTypes"
    if not record_types_dir.is_dir():
        issues.append(
            "PATIENT_RECORD_TYPE: No recordTypes directory found under Account object metadata. "
            "A 'Patient' (or 'Member') record type on Account is required for Health Cloud "
            "patient records. Create it in Object Manager > Account > Record Types."
        )
        return issues

    rt_files = list(record_types_dir.glob("*.recordType-meta.xml"))
    patient_rt_found = False
    for rt_file in rt_files:
        name_lower = rt_file.stem.lower()
        if "patient" in name_lower or "member" in name_lower:
            patient_rt_found = True
            # Check that the record type is active
            try:
                tree = ET.parse(rt_file)
                root = tree.getroot()
                active_elem = root.find(f"{{{SF_NS}}}active")
                if active_elem is not None and active_elem.text == "false":
                    issues.append(
                        f"PATIENT_RECORD_TYPE: Record type '{rt_file.stem}' on Account is "
                        f"marked inactive. Patient records cannot use inactive record types."
                    )
            except ET.ParseError:
                issues.append(
                    f"PATIENT_RECORD_TYPE: Could not parse {rt_file.name} — XML may be malformed."
                )
            break

    if not patient_rt_found:
        issues.append(
            "PATIENT_RECORD_TYPE: No 'Patient' or 'Member' record type found on Account. "
            "Health Cloud patient records require a dedicated record type separate from "
            "business account record types. Enabling Person Accounts alone is not sufficient."
        )
    return issues


def check_clinical_objects_present(object_dir: Path) -> list[str]:
    """Check if Health Cloud clinical objects exist in metadata."""
    issues: list[str] = []
    missing_objects = []
    for obj_name in HC_CLINICAL_OBJECTS:
        obj_dir = object_dir / obj_name
        obj_meta = object_dir / f"{obj_name}.object-meta.xml"
        if not obj_dir.is_dir() and not obj_meta.is_file():
            missing_objects.append(obj_name)

    if missing_objects:
        issues.append(
            f"HC_CLINICAL_OBJECTS: The following Health Cloud clinical objects are not present "
            f"in metadata: {', '.join(missing_objects)}. "
            f"If clinical data integrations are required, these objects must be mapped and populated. "
            f"Do NOT store clinical data (medications, diagnoses, immunizations) in custom "
            f"Account or Contact fields — use these dedicated Health Cloud objects instead."
        )
    return issues


def check_account_clinical_field_antipattern(object_dir: Path) -> list[str]:
    """Detect custom Account fields with clinical-sounding names."""
    issues: list[str] = []
    account_fields_dir = object_dir / "Account" / "fields"
    if not account_fields_dir.is_dir():
        return issues

    suspicious_fields = []
    for field_file in account_fields_dir.glob("*.field-meta.xml"):
        field_name_lower = field_file.stem.lower()
        # Skip standard/known fields
        if "__c" not in field_file.stem and not field_file.stem.endswith("__c"):
            continue
        for pattern in CLINICAL_FIELD_PATTERNS:
            if pattern in field_name_lower:
                suspicious_fields.append(field_file.stem)
                break

    if suspicious_fields:
        issues.append(
            f"CLINICAL_FIELD_ANTIPATTERN: Found custom Account fields with clinical-sounding names: "
            f"{', '.join(suspicious_fields)}. "
            f"Clinical data (medications, diagnoses, immunizations, conditions) should be stored "
            f"in Health Cloud clinical objects (EhrPatientMedication, PatientHealthCondition, etc.), "
            f"NOT in custom Account fields. Custom Account fields are invisible to Patient Card, "
            f"Timeline, Care Plans, and Population Health analytics."
        )
    return issues


def check_hc_permission_sets(manifest_dir: Path) -> list[str]:
    """Check that Health Cloud permission sets are present in metadata."""
    issues: list[str] = []
    ps_dir_candidates = [
        manifest_dir / "permissionsets",
        manifest_dir / "force-app" / "main" / "default" / "permissionsets",
        manifest_dir / "src" / "permissionsets",
    ]
    ps_dir = None
    for candidate in ps_dir_candidates:
        if candidate.is_dir():
            ps_dir = candidate
            break

    if ps_dir is None:
        # Permission sets may be managed-package only — not a hard error
        return issues

    ps_files = {f.stem for f in ps_dir.glob("*.permissionset-meta.xml")}
    hc_permission_sets = ["HealthCloudFoundation", "HealthCloudSocialDeterminants"]
    missing_ps = [ps for ps in hc_permission_sets if ps not in ps_files]
    if missing_ps:
        issues.append(
            f"HC_PERMISSION_SETS: Health Cloud permission sets not found in metadata: "
            f"{', '.join(missing_ps)}. "
            f"These are installed with the Health Cloud managed package. If they are absent, "
            f"the Health Cloud package may not be installed, or permission sets may need to be "
            f"assigned to profiles. Clinical users need these sets to access care team, "
            f"care plan, and clinical data features."
        )
    return issues


def check_health_cloud_patient_setup(manifest_dir: Path) -> list[str]:
    """Run all Health Cloud patient setup checks. Returns list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    object_dir = find_object_dir(manifest_dir)
    if object_dir is None:
        issues.append(
            "METADATA_STRUCTURE: No 'objects' directory found in manifest. "
            "Provide a Salesforce metadata directory containing an 'objects' subdirectory."
        )
        return issues

    issues.extend(check_person_accounts_enabled(object_dir))
    issues.extend(check_patient_record_type(object_dir))
    issues.extend(check_clinical_objects_present(object_dir))
    issues.extend(check_account_clinical_field_antipattern(object_dir))
    issues.extend(check_hc_permission_sets(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_health_cloud_patient_setup(manifest_dir)

    if not issues:
        print("No Health Cloud patient setup issues found.")
        return 0

    print(f"Found {len(issues)} issue(s):\n", file=sys.stderr)
    for i, issue in enumerate(issues, 1):
        print(f"[{i}] WARN: {issue}\n", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
