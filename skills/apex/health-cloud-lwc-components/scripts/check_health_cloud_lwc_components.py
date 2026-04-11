#!/usr/bin/env python3
"""Checker script for Health Cloud LWC Components skill.

Checks org metadata for common Health Cloud LWC component issues:
- Apex controller FLS enforcement for clinical objects
- TimelineObjectDefinition metadata presence
- Custom Account fields used for clinical data (anti-pattern)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_lwc_components.py [--help]
    python3 check_health_cloud_lwc_components.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Health Cloud LWC component code for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


CLINICAL_OBJECTS = [
    "HealthCondition",
    "ClinicalEncounter",
    "PatientMedication",
    "CareObservation",
    "EhrPatientMedication",
    "ClinicalServiceRequest",
]


def check_apex_fls_enforcement(manifest_dir: Path) -> list[str]:
    """Check Apex classes querying clinical objects for FLS enforcement."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8")
        if "@AuraEnabled" not in content:
            continue

        for clinical_obj in CLINICAL_OBJECTS:
            if f"FROM {clinical_obj}" in content or f"FROM {clinical_obj}\n" in content:
                if "WITH SECURITY_ENFORCED" not in content and "isAccessible" not in content:
                    issues.append(
                        f"{cls_file.name}: @AuraEnabled method queries {clinical_obj} without "
                        "WITH SECURITY_ENFORCED or FLS check. "
                        "Clinical data (PHI) requires FLS enforcement in all Apex controllers. "
                        "Add WITH SECURITY_ENFORCED to the SOQL query."
                    )
                    break
    return issues


def check_timeline_object_definitions(manifest_dir: Path) -> list[str]:
    """Check for TimelineObjectDefinition metadata."""
    issues: list[str] = []
    tod_dir = manifest_dir / "timelineObjectDefinitions"
    if not tod_dir.exists():
        issues.append(
            "No timelineObjectDefinitions/ directory found. "
            "If custom objects should appear in the Industries Timeline, "
            "create TimelineObjectDefinition metadata records in Setup."
        )
    return issues


def check_account_clinical_summary_fields(manifest_dir: Path) -> list[str]:
    """Check for custom Account fields that appear to store clinical data."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    account_fields_dir = objects_dir / "Account" / "fields"
    if not account_fields_dir.exists():
        return issues

    clinical_field_patterns = [
        "condition", "diagnosis", "medication", "encounter", "clinical",
        "lab_result", "a1c", "hba1c", "procedure"
    ]

    for field_file in account_fields_dir.glob("*.field-meta.xml"):
        field_name_lower = field_file.stem.lower()
        for pattern in clinical_field_patterns:
            if pattern in field_name_lower:
                issues.append(
                    f"Account.{field_file.stem}: Custom Account field name suggests clinical data storage. "
                    "Health Cloud clinical UI components (PatientCard, Timeline) query clinical standard objects, "
                    "not Account fields. Custom Account fields are invisible to clinical components. "
                    "Store clinical data on HealthCondition, PatientMedication, etc. instead."
                )
                break
    return issues


def check_health_cloud_lwc_components(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_fls_enforcement(manifest_dir))
    issues.extend(check_timeline_object_definitions(manifest_dir))
    issues.extend(check_account_clinical_summary_fields(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_health_cloud_lwc_components(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
