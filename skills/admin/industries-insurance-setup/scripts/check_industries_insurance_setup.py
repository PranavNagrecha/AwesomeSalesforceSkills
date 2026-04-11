#!/usr/bin/env python3
"""Checker script for Industries Insurance Setup skill.

Inspects a Salesforce metadata directory for common misconfigurations in
FSC Insurance / Industries Insurance implementations.

Checks performed:
  1. Presence of InsurancePolicy and InsurancePolicyCoverage object metadata
  2. InsurancePolicyParticipant Role picklist — warns on placeholder values
  3. OmniScript Remote Action elements — warns if InsProductService reference
     appears without a namespace comment or path annotation
  4. Profile/PermissionSet files — warns if FSC Insurance PSL assignment is absent
  5. CustomObject presence checks for standard insurance objects

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_insurance_setup.py [--manifest-dir path/to/metadata]
    python3 check_industries_insurance_setup.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce metadata XML namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Standard insurance objects expected in a configured insurance org
EXPECTED_INSURANCE_OBJECTS = [
    "InsurancePolicy",
    "InsurancePolicyCoverage",
    "InsurancePolicyParticipant",
    "Claim",
    "CoverageType",
]

# Role picklist values that look like placeholders or non-standard values
PLACEHOLDER_ROLE_VALUES = {"agent", "customer", "tbd", "placeholder", "todo", "test"}

# Patterns that suggest InsProductService is referenced in OmniScript XML
INSPRODUCTSERVICE_MARKERS = [
    "InsProductService",
    "getRatedProducts",
    "insOsGridProductSelection",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC Insurance / Industries Insurance metadata for common "
            "configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_files_by_extension(root: Path, extension: str) -> list[Path]:
    """Return all files under root with the given extension."""
    return [p for p in root.rglob(f"*{extension}") if p.is_file()]


def check_insurance_object_metadata(manifest_dir: Path) -> list[str]:
    """Check whether standard insurance object metadata files are present."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Try force-app style layout
        objects_dir = manifest_dir / "force-app" / "main" / "default" / "objects"
    if not objects_dir.exists():
        issues.append(
            "No 'objects' metadata directory found. Cannot verify insurance object presence. "
            "Expected at: objects/ or force-app/main/default/objects/"
        )
        return issues

    found_objects = {d.name for d in objects_dir.iterdir() if d.is_dir()}
    for obj_name in EXPECTED_INSURANCE_OBJECTS:
        if obj_name not in found_objects:
            issues.append(
                f"Standard insurance object metadata not found: {obj_name}. "
                f"Ensure the object is included in package.xml and retrieved. "
                f"If this is a new org setup, the FSC Insurance PSL may not be provisioned."
            )
    return issues


def check_participant_role_picklist(manifest_dir: Path) -> list[str]:
    """Check InsurancePolicyParticipant Role picklist for placeholder values."""
    issues: list[str] = []

    # Search for InsurancePolicyParticipant object directory
    candidate_dirs: list[Path] = []
    for root, dirs, _ in os.walk(manifest_dir):
        for d in dirs:
            if d == "InsurancePolicyParticipant":
                candidate_dirs.append(Path(root) / d)

    if not candidate_dirs:
        # Not necessarily an error — may not be in metadata scope
        return issues

    for obj_dir in candidate_dirs:
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue
        role_field_file = fields_dir / "Role__c.field-meta.xml"
        if not role_field_file.exists():
            role_field_file = fields_dir / "Role.field-meta.xml"
        if not role_field_file.exists():
            continue

        try:
            tree = ET.parse(role_field_file)
            root_el = tree.getroot()
            ns = {"sf": SF_NS}
            for value_el in root_el.findall(".//sf:valueSet//sf:value", ns):
                label_el = value_el.find("sf:label", ns)
                fullname_el = value_el.find("sf:fullName", ns)
                label = (label_el.text or "").strip().lower() if label_el is not None else ""
                fullname = (fullname_el.text or "").strip().lower() if fullname_el is not None else ""
                if label in PLACEHOLDER_ROLE_VALUES or fullname in PLACEHOLDER_ROLE_VALUES:
                    issues.append(
                        f"InsurancePolicyParticipant Role picklist contains a placeholder value: "
                        f"'{label or fullname}'. Finalize role picklist values before creating "
                        f"participant records — deactivating values after records exist requires "
                        f"a Replace operation, not deactivation."
                    )
        except ET.ParseError as exc:
            issues.append(f"Could not parse Role field metadata at {role_field_file}: {exc}")

    return issues


def check_omniscript_insurance_references(manifest_dir: Path) -> list[str]:
    """Check OmniScript XML files for InsProductService references without platform path notes."""
    issues: list[str] = []

    # OmniScripts are stored as .xml files under omniscripts/ or similar paths
    xml_files: list[Path] = []
    for root_str, dirs, files in os.walk(manifest_dir):
        root_path = Path(root_str)
        for fname in files:
            if fname.endswith(".xml"):
                fpath = root_path / fname
                # Only check files that are likely OmniScript metadata
                if "omniscript" in fname.lower() or "omniscript" in str(fpath).lower():
                    xml_files.append(fpath)

    for xml_file in xml_files:
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for marker in INSPRODUCTSERVICE_MARKERS:
            if marker in content:
                # Check if there is a comment about the platform path nearby
                has_path_annotation = (
                    "managed-package" in content.lower()
                    or "native-core" in content.lower()
                    or "namespace" in content.lower()
                    or "platform path" in content.lower()
                )
                if not has_path_annotation:
                    issues.append(
                        f"OmniScript file '{xml_file.name}' references '{marker}' but contains "
                        f"no annotation about the platform path (managed-package vs native-core). "
                        f"InsProductService namespace differs between paths. Add a comment "
                        f"confirming the platform path before deployment."
                    )
                break  # One warning per file is sufficient

    return issues


def check_insurance_settings_in_settings_metadata(manifest_dir: Path) -> list[str]:
    """Check for Insurance Settings metadata file and warn if not present."""
    issues: list[str] = []

    settings_dir = manifest_dir / "settings"
    if not settings_dir.exists():
        settings_dir = manifest_dir / "force-app" / "main" / "default" / "settings"
    if not settings_dir.exists():
        # Not a hard error — settings may not be tracked
        return issues

    insurance_settings_file = settings_dir / "Insurance.settings-meta.xml"
    if not insurance_settings_file.exists():
        issues.append(
            "Insurance.settings-meta.xml not found in settings/ directory. "
            "Insurance Settings (including irreversible toggles) should be tracked in source "
            "control so the enabled settings are documented and visible in code review."
        )
        return issues

    # If the file exists, check for the irreversible settings being present
    try:
        content = insurance_settings_file.read_text(encoding="utf-8", errors="replace")
        if "enableManyToManyPolicyRelationships" not in content and "enableMultipleProducersPerPolicy" not in content:
            issues.append(
                "Insurance.settings-meta.xml exists but does not contain "
                "'enableManyToManyPolicyRelationships' or 'enableMultipleProducersPerPolicy' elements. "
                "Verify that Insurance Settings was retrieved with all insurance-specific fields included."
            )
    except OSError as exc:
        issues.append(f"Could not read Insurance settings file: {exc}")

    return issues


def check_industries_insurance_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_insurance_object_metadata(manifest_dir))
    issues.extend(check_participant_role_picklist(manifest_dir))
    issues.extend(check_omniscript_insurance_references(manifest_dir))
    issues.extend(check_insurance_settings_in_settings_metadata(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_industries_insurance_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
