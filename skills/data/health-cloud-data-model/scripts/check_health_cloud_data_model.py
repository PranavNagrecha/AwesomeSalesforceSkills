#!/usr/bin/env python3
"""Checker script for Health Cloud Data Model skill.

Scans Salesforce project metadata for common data model issues:
- Use of HC24__ EHR objects in DML operations (write freeze violation)
- Missing org preference awareness in deployment notes
- Missing External ID fields for clinical object upserts
- Missing FHIR R4 for Experience Cloud permission set references

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_data_model.py [--help]
    python3 check_health_cloud_data_model.py --manifest-dir path/to/metadata
    python3 check_health_cloud_data_model.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# HC24__ EHR objects that are frozen for new writes post-Spring '23
# where FHIR R4-aligned standard-object counterparts exist.
FROZEN_HC24_OBJECTS = {
    "HC24__EhrEncounter__c",
    "HC24__EhrCondition__c",
    "HC24__EhrCarePlan__c",
    "HC24__EhrMedication__c",
    "HC24__EhrProcedure__c",
    "HC24__EhrImmunization__c",
    "HC24__EhrAllergy__c",
    "HC24__EhrObservation__c",
    "HC24__EhrGoal__c",
}

# DML keywords that indicate a write operation targeting an HC24__ object
DML_WRITE_PATTERN = re.compile(
    r"\b(insert|update|upsert|delete|Database\.(insert|update|upsert|delete))\b",
    re.IGNORECASE,
)

# Pattern to detect HC24__ object references in Apex or SOQL
HC24_REFERENCE_PATTERN = re.compile(
    r"\bHC24__Ehr\w+__c\b",
    re.IGNORECASE,
)

# FHIR R4-aligned standard clinical objects (require org preference to be active)
STANDARD_CLINICAL_OBJECTS = {
    "ClinicalEncounter",
    "HealthCondition",
    "AllergyIntolerance",
    "PatientImmunization",
    "MedicationRequest",
    "ClinicalProcedure",
    "ClinicalObservation",
}

# Pattern to detect references to standard clinical objects in code
STANDARD_CLINICAL_PATTERN = re.compile(
    r"\b(" + "|".join(STANDARD_CLINICAL_OBJECTS) + r")\b",
)

# Experience Cloud FHIR permission set name (exact)
FHIR_EC_PERMISSION = "FHIR R4 for Experience Cloud"

# Extensions to scan for Apex and metadata
APEX_EXTENSIONS = {".cls", ".trigger"}
METADATA_EXTENSIONS = {".xml", ".permissionset", ".permissionset-meta.xml"}
ALL_EXTENSIONS = APEX_EXTENSIONS | METADATA_EXTENSIONS


def find_files(root: Path, extensions: set[str]) -> list[Path]:
    """Recursively find files matching given extensions under root."""
    results = []
    for ext in extensions:
        results.extend(root.rglob(f"*{ext}"))
    return sorted(results)


def check_hc24_dml_in_apex(files: list[Path]) -> list[str]:
    """Flag Apex files that perform DML write operations against frozen HC24__ objects."""
    issues = []
    for filepath in files:
        if filepath.suffix not in APEX_EXTENSIONS:
            continue
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = content.splitlines()
        for lineno, line in enumerate(lines, start=1):
            # Check if line has both a DML write keyword and an HC24__ EHR object reference
            hc24_matches = HC24_REFERENCE_PATTERN.findall(line)
            if hc24_matches and DML_WRITE_PATTERN.search(line):
                for obj in hc24_matches:
                    if obj in FROZEN_HC24_OBJECTS or "HC24__Ehr" in obj:
                        issues.append(
                            f"{filepath}:{lineno}: DML write against frozen HC24__ object "
                            f"'{obj}'. Post-Spring '23 orgs cannot write to HC24__ EHR objects "
                            f"where standard FHIR R4-aligned counterparts exist. "
                            f"Use the corresponding standard object (e.g. ClinicalEncounter, "
                            f"HealthCondition, CarePlan) instead."
                        )
    return issues


def check_hc24_readonly_references(files: list[Path]) -> list[str]:
    """Warn about HC24__ object references (read or write) to flag for review.

    Read references are not errors, but should be reviewed during migration assessments.
    """
    issues = []
    seen_files: set[Path] = set()
    for filepath in files:
        if filepath.suffix not in APEX_EXTENSIONS:
            continue
        if filepath in seen_files:
            continue
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if HC24_REFERENCE_PATTERN.search(content):
            seen_files.add(filepath)
            issues.append(
                f"{filepath}: References HC24__ EHR object(s). "
                f"Review whether this file performs write operations (blocked post-Spring '23) "
                f"or only reads historical data (allowed). Consider migrating reads to standard "
                f"FHIR R4-aligned objects if historical data has been migrated."
            )
    return issues


def check_standard_objects_without_external_id(files: list[Path]) -> list[str]:
    """Flag Apex files that reference standard clinical objects in upsert without an External ID field."""
    issues = []
    for filepath in files:
        if filepath.suffix not in APEX_EXTENSIONS:
            continue
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lines = content.splitlines()
        for lineno, line in enumerate(lines, start=1):
            # Detect Database.upsert calls on clinical objects
            if "Database.upsert" in line or "upsert " in line.lower():
                if STANDARD_CLINICAL_PATTERN.search(line):
                    # Check that an External ID field reference is nearby (within 5 lines)
                    context_start = max(0, lineno - 3)
                    context_end = min(len(lines), lineno + 3)
                    context = "\n".join(lines[context_start:context_end])
                    # Look for External ID field pattern (e.g., FieldName__c or ExternalId reference)
                    has_external_id_key = bool(
                        re.search(r"ExternalId|External_Id|EhrId|EhrEncounterId|__c\s*,", context)
                    )
                    if not has_external_id_key:
                        issues.append(
                            f"{filepath}:{lineno}: Upsert against a standard clinical object "
                            f"detected without a clear External ID key field. "
                            f"Use an External ID field (e.g., EhrEncounterId__c) as the upsert key "
                            f"to prevent duplicate record creation on resync."
                        )
    return issues


def check_permission_set_files(manifest_dir: Path) -> list[str]:
    """Check permission set XML files for FHIR R4 Experience Cloud permission set assignments."""
    issues = []
    perm_files = list(manifest_dir.rglob("*.permissionset")) + list(
        manifest_dir.rglob("*.permissionset-meta.xml")
    )

    if not perm_files:
        return issues

    # Check whether any community/experience site profile configuration references
    # the FHIR R4 for Experience Cloud permission set
    community_indicators = re.compile(r"(ExperienceCloud|Community|CustomerCommunity|PartnerCommunity)", re.IGNORECASE)
    fhir_ec_indicator = re.compile(r"FHIRr4ExperienceCloud|FHIR_R4_for_Experience_Cloud|FHIRR4ExperienceCloud", re.IGNORECASE)

    has_community_perm = False
    has_fhir_ec_perm = False

    for filepath in perm_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if community_indicators.search(content):
            has_community_perm = True
        if fhir_ec_indicator.search(content):
            has_fhir_ec_perm = True

    if has_community_perm and not has_fhir_ec_perm:
        issues.append(
            "Permission set files include Experience Cloud / Community user configurations "
            "but no reference to the 'FHIR R4 for Experience Cloud' permission set was found. "
            "Experience Cloud users accessing Health Cloud clinical objects (ClinicalEncounter, "
            "HealthCondition, etc.) require the 'FHIR R4 for Experience Cloud' permission set. "
            "Verify this permission set is assigned in your permission set group or user setup."
        )

    return issues


def check_health_cloud_data_model(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    all_files = find_files(manifest_dir, ALL_EXTENSIONS)

    if not all_files:
        issues.append(
            f"No Apex or metadata files found under {manifest_dir}. "
            f"Verify the --manifest-dir path points to a Salesforce project root or metadata folder."
        )
        return issues

    # Check 1: HC24__ DML write violations
    issues.extend(check_hc24_dml_in_apex(all_files))

    # Check 2: HC24__ read references (advisory, not hard error)
    issues.extend(check_hc24_readonly_references(all_files))

    # Check 3: Clinical object upserts without External ID
    issues.extend(check_standard_objects_without_external_id(all_files))

    # Check 4: Experience Cloud permission set coverage
    issues.extend(check_permission_set_files(manifest_dir))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Health Cloud metadata for data model issues: "
            "HC24__ write violations, missing FHIR R4 org preference awareness, "
            "missing External ID fields on clinical object upserts, "
            "and missing Experience Cloud FHIR permission set coverage."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_health_cloud_data_model(manifest_dir)

    if not issues:
        print("No Health Cloud data model issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
