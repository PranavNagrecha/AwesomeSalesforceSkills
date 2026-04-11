#!/usr/bin/env python3
"""Checker script for Clinical Decision Support skill.

Checks org metadata for common clinical decision support issues:
- Non-bulkified Apex triggers on clinical objects
- CareGap creation via standard DML
- ClinicalAlert trigger patterns

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_clinical_decision_support.py [--help]
    python3 check_clinical_decision_support.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check clinical decision support code for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


CLINICAL_TRIGGER_OBJECTS = [
    "CareObservation",
    "HealthCondition",
    "PatientMedication",
    "ClinicalEncounter",
    "ClinicalServiceRequest",
]


def check_caregap_dml_in_apex(manifest_dir: Path) -> list[str]:
    """Check Apex classes for standard DML on CareGap (should be ingested, not manually created)."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8")
        if "CareGap" in content and ("insert" in content.lower() or "new CareGap()" in content):
            issues.append(
                f"{cls_file.name}: Contains what appears to be CareGap insertion via standard DML. "
                "CareGap records (API v59.0+) should be ingested from external clinical rules engines "
                "via FHIR API, not created via standard Apex DML."
            )
    return issues


def check_triggers_for_bulkification(manifest_dir: Path) -> list[str]:
    """Check Apex triggers on clinical objects for non-bulkified patterns."""
    issues: list[str] = []
    triggers_dir = manifest_dir / "triggers"
    if not triggers_dir.exists():
        return issues

    for trigger_file in triggers_dir.glob("*.trigger"):
        content = trigger_file.read_text(encoding="utf-8")
        is_clinical_trigger = any(obj in content for obj in CLINICAL_TRIGGER_OBJECTS)
        if not is_clinical_trigger:
            continue

        # Check for DML inside for loop (non-bulkified pattern indicator)
        # This is a heuristic — look for 'insert' or 'update' appearing after 'for' in close proximity
        lines = content.split("\n")
        in_for_loop = False
        for_depth = 0
        for i, line in enumerate(lines):
            stripped = line.strip().lower()
            if stripped.startswith("for ") or "for(" in stripped:
                in_for_loop = True
                for_depth += 1
            if in_for_loop and (stripped.startswith("insert ") or stripped.startswith("update ")):
                if "clinicalalert" in stripped or "caregap" in stripped:
                    issues.append(
                        f"{trigger_file.name} (line {i+1}): Clinical object trigger appears to have "
                        "DML inside a loop. Triggers on clinical objects must be bulkified — "
                        "collect records first, then perform single bulk DML operations."
                    )
                    break
    return issues


def check_flows_for_caregap_creation(manifest_dir: Path) -> list[str]:
    """Check Flows for CareGap creation patterns."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        content = flow_file.read_text(encoding="utf-8")
        if "CareGap" in content and "<recordCreates>" in content:
            issues.append(
                f"{flow_file.name}: Flow appears to create CareGap records via recordCreates. "
                "CareGap records cannot be created via standard Flow DML. "
                "CareGap must be ingested from external clinical rules engines via FHIR API."
            )
    return issues


def check_clinical_decision_support(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_caregap_dml_in_apex(manifest_dir))
    issues.extend(check_triggers_for_bulkification(manifest_dir))
    issues.extend(check_flows_for_caregap_creation(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_clinical_decision_support(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
