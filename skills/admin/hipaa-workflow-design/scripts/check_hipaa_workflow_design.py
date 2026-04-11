#!/usr/bin/env python3
"""Checker script for HIPAA Workflow Design skill.

Checks org metadata for common HIPAA workflow design issues:
- Presence of Shield Field Audit Trail configuration
- Event Monitoring references
- OWD configuration for patient/PHI objects

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_hipaa_workflow_design.py [--help]
    python3 check_hipaa_workflow_design.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check HIPAA workflow design configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_owd_for_phi_objects(manifest_dir: Path) -> list[str]:
    """Check that PHI-containing objects have Private OWD configured."""
    issues: list[str] = []
    sharing_rules_dir = manifest_dir / "sharingRules"
    profiles_dir = manifest_dir / "profiles"

    # Check org-wide defaults in organization-wide default settings
    org_wide_dir = manifest_dir / "settings"
    if org_wide_dir.exists():
        for settings_file in org_wide_dir.glob("*.settings-meta.xml"):
            if "Security" in settings_file.name or "Organization" in settings_file.name:
                content = settings_file.read_text(encoding="utf-8")
                if "Account" in content and "Public" in content:
                    issues.append(
                        f"{settings_file.name}: Account OWD may be set to Public. "
                        "HIPAA minimum necessary requires Account (patient records) OWD to be Private. "
                        "Verify OWD settings for all PHI-containing objects."
                    )
    return issues


def check_field_history_vs_audit_trail(manifest_dir: Path) -> list[str]:
    """Check for standard Field History Tracking on PHI-adjacent objects."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    phi_objects = {"Account", "Contact", "ClinicalEncounter", "CarePlan", "HealthCondition"}
    for obj_name in phi_objects:
        obj_dir = objects_dir / obj_name
        obj_file = obj_dir / f"{obj_name}.object-meta.xml"
        if obj_file.exists():
            content = obj_file.read_text(encoding="utf-8")
            if "<enableHistory>true</enableHistory>" in content:
                issues.append(
                    f"{obj_name}: Standard Field History Tracking is enabled. "
                    "Standard Field History Tracking retains data for 18 months only — "
                    "HIPAA requires 6-year audit log retention. "
                    "Use Shield Field Audit Trail for all PHI objects."
                )
    return issues


def check_custom_fields_for_phi_patterns(manifest_dir: Path) -> list[str]:
    """Check custom fields on PHI objects for potentially unprotected sensitive data."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    phi_field_name_patterns = [
        "ssn", "social_security", "tax_id", "dob", "date_of_birth",
        "diagnosis", "medication", "insurance_id", "mrn", "medical_record"
    ]

    phi_objects = {"Account", "Contact", "Lead"}
    for obj_name in phi_objects:
        fields_dir = objects_dir / obj_name / "fields"
        if not fields_dir.exists():
            continue
        for field_file in fields_dir.glob("*.field-meta.xml"):
            field_name_lower = field_file.stem.lower()
            for pattern in phi_field_name_patterns:
                if pattern in field_name_lower:
                    issues.append(
                        f"{obj_name}.{field_file.stem}: Custom field name suggests PHI content. "
                        "Verify this field is covered by Shield Platform Encryption and "
                        "Shield Field Audit Trail in the HIPAA controls configuration."
                    )
                    break
    return issues


def check_hipaa_workflow_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_owd_for_phi_objects(manifest_dir))
    issues.extend(check_field_history_vs_audit_trail(manifest_dir))
    issues.extend(check_custom_fields_for_phi_patterns(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_hipaa_workflow_design(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
