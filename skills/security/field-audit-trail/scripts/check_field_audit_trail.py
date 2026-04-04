#!/usr/bin/env python3
"""Checker script for Field Audit Trail skill.

Validates Salesforce metadata to confirm that high-sensitivity fields on key objects
have Field History Tracking enabled (prerequisite for FAT to capture data) and that
FieldAuditTrail policy configuration files are present.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_field_audit_trail.py [--manifest-dir path/to/metadata]

The manifest-dir should be the root of an SFDX or Metadata API project, e.g.:
    - SFDX: the project root (looks under force-app/main/default/)
    - Metadata API: the unpackaged/ or src/ directory

What this checker validates:
    1. Field History Tracking is enabled on high-sensitivity fields for common objects.
    2. FieldAuditTrail policy XML files exist for the same objects (if FAT is claimed).
    3. No object exceeds 20 FHT-tracked fields (standard platform limit).
    4. No object exceeds 60 FAT-tracked fields (Shield FAT platform limit).
    5. Objects with FAT configured have FHT enabled on the same fields (consistency check).
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration: high-sensitivity fields that should be tracked for compliance
# ---------------------------------------------------------------------------

# Objects and fields that commonly require long-term audit trail coverage.
# Practitioners should extend this list to match their compliance scope.
HIGH_SENSITIVITY_FIELDS: dict[str, list[str]] = {
    "Account": [
        "AnnualRevenue",
        "OwnerId",
        "Type",
        "Industry",
        "Rating",
    ],
    "Contact": [
        "OwnerId",
        "AccountId",
        "Email",
        "Phone",
        "Title",
        "Department",
    ],
    "Opportunity": [
        "Amount",
        "StageName",
        "CloseDate",
        "OwnerId",
        "Probability",
    ],
    "Case": [
        "OwnerId",
        "Status",
        "Priority",
        "Type",
        "AccountId",
    ],
    "Lead": [
        "OwnerId",
        "Status",
        "Email",
        "Phone",
        "LeadSource",
    ],
}

# Standard Field History Tracking limit per object
FHT_FIELD_LIMIT = 20
# Shield FAT limit per object
FAT_FIELD_LIMIT = 60

# Salesforce Metadata API namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# ---------------------------------------------------------------------------
# Metadata path resolution
# ---------------------------------------------------------------------------


def find_objects_dir(manifest_dir: Path) -> Path | None:
    """Locate the objects/ directory under the manifest root.

    Supports both SFDX layout (force-app/main/default/objects/) and
    Metadata API layout (objects/).
    """
    candidates = [
        manifest_dir / "force-app" / "main" / "default" / "objects",
        manifest_dir / "src" / "objects",
        manifest_dir / "unpackaged" / "objects",
        manifest_dir / "objects",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def find_field_audit_trail_dir(manifest_dir: Path) -> Path | None:
    """Locate the fieldAuditTrails/ metadata directory if present."""
    candidates = [
        manifest_dir / "force-app" / "main" / "default" / "fieldAuditTrails",
        manifest_dir / "src" / "fieldAuditTrails",
        manifest_dir / "unpackaged" / "fieldAuditTrails",
        manifest_dir / "fieldAuditTrails",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


# ---------------------------------------------------------------------------
# XML parsing helpers
# ---------------------------------------------------------------------------


def _ns(tag: str) -> str:
    return f"{{{SF_NS}}}{tag}"


def parse_object_metadata(object_xml: Path) -> dict:
    """Parse a Salesforce object metadata XML file.

    Returns a dict with:
        - tracked_fields: list of field names with trackHistory=true
        - all_fields: list of all field names defined in the file
    """
    tracked_fields: list[str] = []
    all_fields: list[str] = []

    try:
        tree = ET.parse(object_xml)
        root = tree.getroot()
    except ET.ParseError as exc:
        return {"error": str(exc), "tracked_fields": [], "all_fields": []}

    # Object-level trackHistory (older metadata format)
    track_history_el = root.find(_ns("enableHistory"))
    object_level_tracking = (
        track_history_el is not None and track_history_el.text == "true"
    )

    # Field-level trackHistory (field metadata within object XML)
    for field_el in root.findall(_ns("fields")):
        full_name_el = field_el.find(_ns("fullName"))
        track_el = field_el.find(_ns("trackHistory"))
        if full_name_el is not None:
            field_name = full_name_el.text or ""
            all_fields.append(field_name)
            if track_el is not None and track_el.text == "true":
                tracked_fields.append(field_name)

    return {
        "object_level_tracking": object_level_tracking,
        "tracked_fields": tracked_fields,
        "all_fields": all_fields,
        "error": None,
    }


def parse_field_audit_trail_policy(policy_xml: Path) -> dict:
    """Parse a FieldAuditTrail policy XML file.

    Returns a dict with:
        - object_name: the governed object
        - tracked_fields: list of fields in the FAT policy
        - retention_months: retention period if set
    """
    try:
        tree = ET.parse(policy_xml)
        root = tree.getroot()
    except ET.ParseError as exc:
        return {"error": str(exc)}

    result: dict = {"error": None, "tracked_fields": [], "retention_months": None}

    # masterLabel or fullName may indicate object
    label_el = root.find(_ns("masterLabel"))
    if label_el is not None:
        result["label"] = label_el.text

    # retentionPolicy retention period
    retention_el = root.find(_ns("retentionPolicy"))
    if retention_el is not None:
        period_el = retention_el.find(_ns("retentionPeriod"))
        if period_el is not None:
            try:
                result["retention_months"] = int(period_el.text or "0")
            except ValueError:
                pass

    # Tracked fields listed in policy
    for field_el in root.findall(_ns("fields")):
        name_el = field_el.find(_ns("fieldName"))
        if name_el is not None and name_el.text:
            result["tracked_fields"].append(name_el.text)

    return result


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def check_fht_on_sensitive_fields(
    objects_dir: Path,
) -> list[str]:
    """Check that high-sensitivity fields have Field History Tracking enabled."""
    issues: list[str] = []

    for object_name, sensitive_fields in HIGH_SENSITIVITY_FIELDS.items():
        # SFDX layout: objects/Account/Account.object-meta.xml
        sfdx_path = objects_dir / object_name / f"{object_name}.object-meta.xml"
        # Metadata API layout: objects/Account.object
        meta_path = objects_dir / f"{object_name}.object"

        object_xml: Path | None = None
        if sfdx_path.exists():
            object_xml = sfdx_path
        elif meta_path.exists():
            object_xml = meta_path

        if object_xml is None:
            # Object not present in metadata — skip (may not be deployed)
            continue

        parsed = parse_object_metadata(object_xml)
        if parsed.get("error"):
            issues.append(
                f"[{object_name}] Could not parse object metadata: {parsed['error']}"
            )
            continue

        tracked = set(parsed["tracked_fields"])
        all_fields = set(parsed["all_fields"])

        for field in sensitive_fields:
            # Only check fields that are present in the metadata file
            # (standard fields may not appear as XML elements if unmodified)
            if field in all_fields and field not in tracked:
                issues.append(
                    f"[{object_name}.{field}] Field History Tracking is NOT enabled "
                    f"on a high-sensitivity field. FAT cannot archive changes for "
                    f"fields without FHT active."
                )

        # Check FHT field count limit
        if len(tracked) > FHT_FIELD_LIMIT:
            issues.append(
                f"[{object_name}] Field History Tracking enabled on {len(tracked)} fields "
                f"— exceeds the platform limit of {FHT_FIELD_LIMIT}. "
                f"Fields beyond {FHT_FIELD_LIMIT} will not be tracked."
            )

    return issues


def check_fat_policy_files(
    objects_dir: Path,
    fat_dir: Path | None,
) -> list[str]:
    """Check FieldAuditTrail policy files for completeness and consistency."""
    issues: list[str] = []

    if fat_dir is None:
        # FAT policies directory absent — either FAT is not configured or
        # policies are managed in Setup only. Warn if high-sensitivity objects exist.
        tracked_objects = []
        for object_name in HIGH_SENSITIVITY_FIELDS:
            sfdx_path = objects_dir / object_name / f"{object_name}.object-meta.xml"
            meta_path = objects_dir / f"{object_name}.object"
            if sfdx_path.exists() or meta_path.exists():
                tracked_objects.append(object_name)
        if tracked_objects:
            issues.append(
                "No fieldAuditTrails/ metadata directory found. "
                "If Shield FAT is required for compliance, ensure FAT retention policies "
                f"are configured in Setup and consider retrieving them into source control. "
                f"Objects in scope: {', '.join(tracked_objects)}"
            )
        return issues

    policy_files = list(fat_dir.glob("*.fieldAuditTrail-meta.xml")) + list(
        fat_dir.glob("*.fieldAuditTrail")
    )

    if not policy_files:
        issues.append(
            f"fieldAuditTrails/ directory exists at {fat_dir} but contains no policy files. "
            "Add FieldAuditTrail metadata files for each object requiring long-term retention."
        )
        return issues

    for policy_file in policy_files:
        parsed = parse_field_audit_trail_policy(policy_file)
        if parsed.get("error"):
            issues.append(
                f"[FAT policy: {policy_file.name}] Could not parse: {parsed['error']}"
            )
            continue

        # Check retention period is set
        if parsed.get("retention_months") is None:
            issues.append(
                f"[FAT policy: {policy_file.name}] Retention period not found in policy XML. "
                "Always set an explicit retention period — do not rely on platform defaults."
            )
        elif parsed["retention_months"] < 18:
            issues.append(
                f"[FAT policy: {policy_file.name}] Retention period is {parsed['retention_months']} months "
                f"— shorter than the standard Field History Tracking window (18 months). "
                f"FAT adds value only for retention beyond 18 months."
            )

        # Check FAT field count
        if len(parsed["tracked_fields"]) > FAT_FIELD_LIMIT:
            issues.append(
                f"[FAT policy: {policy_file.name}] Policy defines {len(parsed['tracked_fields'])} tracked fields "
                f"— exceeds the Shield FAT limit of {FAT_FIELD_LIMIT} fields per object."
            )

    return issues


def check_fht_fat_consistency(
    objects_dir: Path,
    fat_dir: Path | None,
) -> list[str]:
    """Check that fields in FAT policies also have FHT enabled.

    FAT cannot archive changes for fields that Field History Tracking does not capture.
    """
    issues: list[str] = []

    if fat_dir is None:
        return issues

    policy_files = list(fat_dir.glob("*.fieldAuditTrail-meta.xml")) + list(
        fat_dir.glob("*.fieldAuditTrail")
    )

    for policy_file in policy_files:
        parsed_fat = parse_field_audit_trail_policy(policy_file)
        if parsed_fat.get("error") or not parsed_fat.get("tracked_fields"):
            continue

        fat_fields = set(parsed_fat["tracked_fields"])

        # Derive object name from policy file name (e.g., Account.fieldAuditTrail-meta.xml -> Account)
        object_name = policy_file.name.split(".")[0]

        sfdx_path = objects_dir / object_name / f"{object_name}.object-meta.xml"
        meta_path = objects_dir / f"{object_name}.object"

        object_xml: Path | None = None
        if sfdx_path.exists():
            object_xml = sfdx_path
        elif meta_path.exists():
            object_xml = meta_path

        if object_xml is None:
            # Cannot cross-check — object metadata not in source
            continue

        parsed_obj = parse_object_metadata(object_xml)
        if parsed_obj.get("error"):
            continue

        fht_fields = set(parsed_obj["tracked_fields"])
        all_fields = set(parsed_obj["all_fields"])

        # Fields in FAT policy that are in the object metadata but NOT in FHT
        fat_not_fht = fat_fields & all_fields - fht_fields
        if fat_not_fht:
            issues.append(
                f"[{object_name}] The following fields are in the FAT policy but do NOT "
                f"have Field History Tracking enabled. FAT will not capture changes for "
                f"these fields until FHT is also enabled: {sorted(fat_not_fht)}"
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_field_audit_trail(manifest_dir: Path) -> list[str]:
    """Run all FAT checks against the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    objects_dir = find_objects_dir(manifest_dir)
    fat_dir = find_field_audit_trail_dir(manifest_dir)

    if objects_dir is None:
        issues.append(
            f"Could not locate an objects/ directory under {manifest_dir}. "
            "Ensure this is an SFDX or Metadata API project root."
        )
        return issues

    # Run individual checks
    issues.extend(check_fht_on_sensitive_fields(objects_dir))
    issues.extend(check_fat_policy_files(objects_dir, fat_dir))
    issues.extend(check_fht_fat_consistency(objects_dir, fat_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Field Audit Trail configuration issues. "
            "Validates that high-sensitivity fields have Field History Tracking enabled "
            "(required for FAT to capture data), that FAT policy files are present, "
            "and that FHT and FAT configurations are consistent."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    print(f"Checking Field Audit Trail configuration in: {manifest_dir}")
    print()

    issues = check_field_audit_trail(manifest_dir)

    if not issues:
        print("No issues found. Field Audit Trail configuration looks correct.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"  [{i}] {issue}")
    print()
    print(
        "Resolve these issues before claiming FAT compliance coverage. "
        "See skills/security/field-audit-trail/references/gotchas.md for details."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
