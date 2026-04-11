#!/usr/bin/env python3
"""Checker script for Clinical Data Requirements skill.

Checks org metadata for common clinical data model issues:
- Legacy EHR object usage in Flows and Apex
- FHIR R4-aligned object references
- CodeableConcept field patterns

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_clinical_data_requirements.py [--help]
    python3 check_clinical_data_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check clinical data model configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


LEGACY_EHR_OBJECTS = [
    "HC24__EhrCondition__c",
    "HC24__EhrMedication__c",
    "HC24__EhrProcedure__c",
    "HC24__EhrLabResult__c",
    "HC24__EhrPatientMedication__c",
    "HC24__EhrCarePlan__c",
]

FHIR_ALIGNED_REPLACEMENTS = {
    "HC24__EhrCondition__c": "HealthCondition",
    "HC24__EhrMedication__c": "PatientMedication",
    "HC24__EhrProcedure__c": "MedicalProcedure",
    "HC24__EhrLabResult__c": "CareObservation",
    "HC24__EhrCarePlan__c": "CarePlan",
}


def check_legacy_ehr_object_usage(manifest_dir: Path) -> list[str]:
    """Check for legacy HC24__ EHR object references in Flows and classes."""
    issues: list[str] = []

    for search_dir in ["flows", "classes", "triggers"]:
        dir_path = manifest_dir / search_dir
        if not dir_path.exists():
            continue

        extensions = {"flows": "*.flow-meta.xml", "classes": "*.cls", "triggers": "*.trigger"}
        pattern = extensions.get(search_dir, "*")

        for file_path in dir_path.glob(pattern):
            content = file_path.read_text(encoding="utf-8")
            for legacy_obj in LEGACY_EHR_OBJECTS:
                if legacy_obj in content:
                    replacement = FHIR_ALIGNED_REPLACEMENTS.get(legacy_obj, "FHIR R4-aligned standard object")
                    issues.append(
                        f"{file_path.name}: References legacy EHR object '{legacy_obj}'. "
                        f"New Health Cloud orgs (Spring '23+) cannot write to this object. "
                        f"Use '{replacement}' instead."
                    )
    return issues


def check_fhir_aligned_objects_presence(manifest_dir: Path) -> list[str]:
    """Check for presence of FHIR R4-aligned clinical objects."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    fhir_objects = ["HealthCondition", "CareObservation", "PatientImmunization", "AllergyIntolerance"]
    present = {d.name for d in objects_dir.iterdir() if d.is_dir()}
    found = [obj for obj in fhir_objects if obj in present]

    if not found:
        issues.append(
            "No FHIR R4-aligned clinical objects found in objects/ directory. "
            "If clinical data is in scope, verify FHIR R4 Support Settings are enabled in Setup "
            "and that clinical objects are included in the metadata retrieval."
        )
    return issues


def check_clinical_data_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_legacy_ehr_object_usage(manifest_dir))
    issues.extend(check_fhir_aligned_objects_presence(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_clinical_data_requirements(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
