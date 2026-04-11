#!/usr/bin/env python3
"""Checker script for FHIR Integration Patterns skill.

Checks org metadata for common FHIR integration issues:
- Legacy HC24__ EHR object references in integration code
- Connected App FHIR OAuth scope configuration
- Experience Cloud FHIR permission set presence

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fhir_integration_patterns.py [--help]
    python3 check_fhir_integration_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FHIR integration configuration and code for common issues.",
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
]


def check_legacy_ehr_in_classes(manifest_dir: Path) -> list[str]:
    """Check Apex classes for legacy HC24__ EHR object usage."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8")
        for legacy_obj in LEGACY_EHR_OBJECTS:
            if legacy_obj in content:
                issues.append(
                    f"{cls_file.name}: References legacy EHR object '{legacy_obj}'. "
                    "Spring '23+ orgs cannot write to this object. "
                    "Target FHIR R4-aligned standard objects instead."
                )
    return issues


def check_fhir_connected_app_scopes(manifest_dir: Path) -> list[str]:
    """Check Connected Apps for FHIR-required OAuth scopes."""
    issues: list[str] = []
    connected_apps_dir = manifest_dir / "connectedApps"
    if not connected_apps_dir.exists():
        return issues

    for app_file in connected_apps_dir.glob("*.connectedApp-meta.xml"):
        content = app_file.read_text(encoding="utf-8")
        # Check for FHIR-related naming in app
        if "fhir" in content.lower() or "healthcare" in content.lower():
            if "<oauthScope>healthcare</oauthScope>" not in content:
                issues.append(
                    f"{app_file.name}: Connected App appears FHIR-related but missing 'healthcare' scope. "
                    "FHIR Healthcare API requires both 'api' and 'healthcare' OAuth scopes."
                )
    return issues


def check_experience_cloud_fhir_perms(manifest_dir: Path) -> list[str]:
    """Check for FHIR R4 for Experience Cloud permission set."""
    issues: list[str] = []
    perm_dir = manifest_dir / "permissionsets"
    if not perm_dir.exists():
        return issues

    # Look for any Experience Cloud permission sets that don't include FHIR R4 EC perm
    exp_cloud_perms = [
        f for f in perm_dir.glob("*.permissionset-meta.xml")
        if "experiencecloud" in f.name.lower() or "community" in f.name.lower()
    ]

    fhir_ec_perm_found = any(
        "FhirR4ForExperience" in f.read_text(encoding="utf-8") or "fhir_r4_experience" in f.name.lower()
        for f in perm_dir.glob("*.permissionset-meta.xml")
    )

    if exp_cloud_perms and not fhir_ec_perm_found:
        issues.append(
            "Experience Cloud permission sets found but no 'FHIR R4 for Experience Cloud' permission set. "
            "If portal users need to view FHIR-aligned clinical data, they require the "
            "'FHIR R4 for Experience Cloud' permission set."
        )
    return issues


def check_fhir_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_legacy_ehr_in_classes(manifest_dir))
    issues.extend(check_fhir_connected_app_scopes(manifest_dir))
    issues.extend(check_experience_cloud_fhir_perms(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fhir_integration_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
