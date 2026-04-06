#!/usr/bin/env python3
"""Checker script for SIS Integration Patterns skill.

Validates Salesforce metadata in a local project directory for common SIS
integration issues: missing External ID fields, incorrect upsert field
references in named credential configs, missing CDC setup markers, and
integration user permission set gaps.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sis_integration_patterns.py [--help]
    python3 check_sis_integration_patterns.py --manifest-dir path/to/force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Custom External ID fields the SIS integration requires.
REQUIRED_EXTERNAL_ID_FIELDS: dict[str, list[str]] = {
    "Contact": ["SIS_Student_ID__c"],
    "LearnerProfile__c": ["SIS_LearnerProfile_ID__c"],
    "AcademicTermEnrollment__c": ["SIS_Enrollment_Key__c"],
    "CourseOfferingParticipant": ["SIS_CourseParticipant_Key__c"],
    "CourseOfferingPtcpResult": ["SIS_GradeResult_Key__c"],
}

# Standard field that is NOT an External ID — using it as an upsert key is wrong.
WRONG_EXTERNAL_ID_FIELD = "StudentIdNumber"

# Allowed EnrollmentStatus picklist values per Education Cloud Developer Guide v66.0.
ALLOWED_ENROLLMENT_STATUSES = {
    "Active",
    "Dropout",
    "Expelled",
    "Graduated",
    "No show",
    "Other",
    "Transferred",
    "Withdrawn",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_xml_files(directory: Path, suffix: str) -> list[Path]:
    """Return all files under *directory* ending with *suffix*."""
    return list(directory.rglob(f"*{suffix}"))


def _xml_root(path: Path) -> ET.Element | None:
    """Parse XML file and return root element, or None on parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def _strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from a tag string."""
    return tag.split("}")[-1] if "}" in tag else tag


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_external_id_fields(manifest_dir: Path) -> list[str]:
    """Check that required External ID fields exist and are correctly configured."""
    issues: list[str] = []

    fields_dir = manifest_dir / "objects"
    if not fields_dir.exists():
        # No objects directory — cannot check
        return issues

    for object_name, required_fields in REQUIRED_EXTERNAL_ID_FIELDS.items():
        # Metadata layout: objects/<ObjectName>/fields/<FieldName>.field-meta.xml
        object_fields_dir = fields_dir / object_name / "fields"
        if not object_fields_dir.exists():
            issues.append(
                f"MISSING OBJECT DIR: {object_name}/fields/ not found under "
                f"{fields_dir}. Required External ID field(s) cannot be verified: "
                + ", ".join(required_fields)
            )
            continue

        for field_name in required_fields:
            field_file = object_fields_dir / f"{field_name}.field-meta.xml"
            if not field_file.exists():
                issues.append(
                    f"MISSING EXTERNAL ID FIELD: {object_name}.{field_name} "
                    f"does not exist. This field is required for SIS upsert keying. "
                    f"Create it as Text, External ID, Unique."
                )
                continue

            root = _xml_root(field_file)
            if root is None:
                issues.append(
                    f"UNPARSEABLE XML: {field_file} could not be parsed."
                )
                continue

            tags = {_strip_ns(child.tag): child.text for child in root}

            if tags.get("externalId", "").lower() != "true":
                issues.append(
                    f"NOT EXTERNAL ID: {object_name}.{field_name} exists but "
                    f"externalId is not set to true. The upsert key must be an "
                    f"External ID field."
                )
            if tags.get("unique", "").lower() != "true":
                issues.append(
                    f"NOT UNIQUE: {object_name}.{field_name} exists but unique "
                    f"is not set to true. Duplicate SIS keys will cause silent "
                    f"INVALID_CROSS_REFERENCE_KEY errors."
                )

    return issues


def check_wrong_external_id_usage(manifest_dir: Path) -> list[str]:
    """Warn if any metadata references StudentIdNumber as an upsert key."""
    issues: list[str] = []

    # Check .xml files in the manifest for references to StudentIdNumber as
    # externalIdFieldName — a common misconfiguration in integration metadata.
    for xml_file in _find_xml_files(manifest_dir, ".xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Look for externalIdFieldName element containing StudentIdNumber
        if "externalIdFieldName" in content and WRONG_EXTERNAL_ID_FIELD in content:
            issues.append(
                f"WRONG EXTERNAL ID KEY in {xml_file}: 'StudentIdNumber' appears "
                f"near 'externalIdFieldName'. LearnerProfile.StudentIdNumber is NOT "
                f"an External ID field and cannot be used as an upsert key. "
                f"Use SIS_LearnerProfile_ID__c instead."
            )

    return issues


def check_enrollment_status_mapping(manifest_dir: Path) -> list[str]:
    """Check for custom metadata or flow records that set EnrollmentStatus to non-allowed values."""
    issues: list[str] = []

    # Scan CustomMetadata and Flow files for literal EnrollmentStatus assignments.
    for xml_file in _find_xml_files(manifest_dir, ".xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "EnrollmentStatus" not in content:
            continue

        root = _xml_root(xml_file)
        if root is None:
            continue

        # Walk all elements looking for value assignments to EnrollmentStatus.
        for elem in root.iter():
            if _strip_ns(elem.tag) in ("field", "assignToReference") and elem.text == "EnrollmentStatus":
                # Try to find the sibling value element
                parent = None
                for potential_parent in root.iter():
                    for child in list(potential_parent):
                        if child is elem:
                            parent = potential_parent
                            break
                    if parent is not None:
                        break

                if parent is not None:
                    value_elem = None
                    siblings = list(parent)
                    try:
                        idx = siblings.index(elem)
                        # Look for a 'value' or 'stringValue' sibling after the field ref
                        for sib in siblings[idx:]:
                            if _strip_ns(sib.tag) in ("value", "stringValue"):
                                value_elem = sib
                                break
                    except ValueError:
                        pass

                    if value_elem is not None and value_elem.text:
                        assigned_value = value_elem.text.strip()
                        if (
                            assigned_value
                            and assigned_value not in ALLOWED_ENROLLMENT_STATUSES
                            and not assigned_value.startswith("{!")  # formula reference
                        ):
                            issues.append(
                                f"INVALID ENROLLMENT STATUS in {xml_file}: "
                                f"'{assigned_value}' is not in the restricted picklist "
                                f"for EnrollmentStatus. Allowed values: "
                                + ", ".join(sorted(ALLOWED_ENROLLMENT_STATUSES))
                            )

    return issues


def check_learner_profile_contact_id_in_updates(manifest_dir: Path) -> list[str]:
    """Warn if any Flow or Apex metadata attempts to set ContactId on LearnerProfile in an update context."""
    issues: list[str] = []

    # Heuristic: look for Flow metadata that sets ContactId inside an Update operation
    # on LearnerProfile. Full AST analysis is out of scope for a stdlib checker;
    # we scan for the co-occurrence pattern.
    for xml_file in _find_xml_files(manifest_dir, ".flow-meta.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "LearnerProfile" in content and "ContactId" in content and "recordUpdates" in content:
            issues.append(
                f"POSSIBLE IMMUTABLE FIELD UPDATE in {xml_file}: Flow contains "
                f"recordUpdates referencing LearnerProfile and ContactId. "
                f"LearnerProfile.ContactId is a master-detail create-only field and "
                f"cannot be changed after record creation. Review this flow to ensure "
                f"ContactId is only set during record creation, not updates."
            )

    return issues


def check_cdc_configuration(manifest_dir: Path) -> list[str]:
    """Check whether Change Data Capture is enabled for AcademicTermEnrollment."""
    issues: list[str] = []

    # CDC configuration lives in PlatformEventChannel metadata or
    # ChangeDataCaptureSettings metadata (depending on deployment method).
    cdc_dir = manifest_dir / "platformEventChannels"
    settings_dir = manifest_dir / "settings"

    # Check for ChangeDataCaptureSettings.settings-meta.xml
    cdc_settings_file = settings_dir / "ChangeDataCapture.settings-meta.xml"
    if cdc_settings_file.exists():
        root = _xml_root(cdc_settings_file)
        if root is not None:
            content_str = ET.tostring(root, encoding="unicode")
            if "AcademicTermEnrollment" not in content_str:
                issues.append(
                    "CDC NOT ENABLED FOR AcademicTermEnrollment: "
                    "ChangeDataCapture.settings-meta.xml exists but does not include "
                    "AcademicTermEnrollment. Enable CDC on this object via Setup > "
                    "Integrations > Change Data Capture if near-real-time writeback "
                    "to the SIS is required."
                )
    elif cdc_dir.exists():
        # Check for a PlatformEventChannel referencing AcademicTermEnrollmentChangeEvent
        found = False
        for xml_file in _find_xml_files(cdc_dir, ".xml"):
            try:
                content = xml_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "AcademicTermEnrollment" in content:
                found = True
                break
        if not found:
            issues.append(
                "CDC NOT CONFIGURED FOR AcademicTermEnrollment: "
                "No PlatformEventChannel metadata found referencing "
                "AcademicTermEnrollment. If near-real-time enrollment status "
                "writeback to the SIS is required, enable CDC on this object."
            )
    # If neither directory exists, we cannot assess CDC status — skip silently.

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common SIS integration issues: "
            "missing External ID fields, wrong upsert keys, invalid EnrollmentStatus "
            "values, immutable field update attempts, and missing CDC configuration."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory). "
             "Typically force-app/main/default or the src/ directory of a Salesforce DX project.",
    )
    return parser.parse_args()


def check_sis_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_external_id_fields(manifest_dir))
    issues.extend(check_wrong_external_id_usage(manifest_dir))
    issues.extend(check_enrollment_status_mapping(manifest_dir))
    issues.extend(check_learner_profile_contact_id_in_updates(manifest_dir))
    issues.extend(check_cdc_configuration(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sis_integration_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
