#!/usr/bin/env python3
"""Checker script for Field Audit Trail skill.

Validates Salesforce object metadata to confirm that high-sensitivity fields on key
objects have Field History Tracking enabled (prerequisite for FAT to capture data) and
that Field Audit Trail retention policies use values the Metadata API documents.

Reads only metadata the Metadata API actually defines: the object-level
`historyRetentionPolicy` block (HistoryRetentionPolicy, api_meta.txt) and the field-level
`trackHistory` element. There is no separate FieldAuditTrail metadata type.

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_field_audit_trail.py [--manifest-dir path/to/metadata]

The manifest-dir should be the root of an SFDX or Metadata API project, e.g.:
    - SFDX: the project root (looks under force-app/main/default/)
    - Metadata API: the unpackaged/ or src/ directory

What this checker validates:
    1. Field History Tracking is enabled on high-sensitivity fields for common objects.
    2. No object tracks more fields than the documented limit: 20 without Field Audit
       Trail, 200 with it (security guide: "track up to 200 fields per object"; "Without
       Field Audit Trail, you can track only up to 20 fields per object"). An object is
       treated as FAT-enabled when its XML carries a historyRetentionPolicy block.
    3. At least one in-scope object carries a historyRetentionPolicy block (otherwise a
       warning that no FAT retention policy is in source control).
    4. historyRetentionPolicy blocks use values the Metadata API documents:
       archiveAfterMonths 1-18 (required), gracePeriodDays 0-10. archiveRetentionYears
       is only a reminder for manual deletion; archived data is kept until you delete it,
       so it is not range-checked here.

Exit codes: 0 = no issues, 1 = issues found.
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

# Tracked-field limit per object without Field Audit Trail (security guide 262 L4838)
FHT_FIELD_LIMIT = 20
# Tracked-field limit per object with Field Audit Trail (security guide 262 L4835-4836)
FAT_FIELD_LIMIT = 200

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
        - has_retention_policy: True when a historyRetentionPolicy block is present
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

    # Field-level trackHistory (field metadata within object XML: Metadata API layout)
    for field_el in root.findall(_ns("fields")):
        full_name_el = field_el.find(_ns("fullName"))
        track_el = field_el.find(_ns("trackHistory"))
        if full_name_el is not None:
            field_name = full_name_el.text or ""
            all_fields.append(field_name)
            if track_el is not None and track_el.text == "true":
                tracked_fields.append(field_name)

    # SFDX layout keeps each field in objects/<Object>/fields/<Field>.field-meta.xml
    fields_dir = object_xml.parent / "fields"
    if object_xml.name.endswith(".object-meta.xml") and fields_dir.is_dir():
        for field_xml in sorted(fields_dir.glob("*.field-meta.xml")):
            try:
                field_root = ET.parse(field_xml).getroot()
            except ET.ParseError:
                continue
            full_name_el = field_root.find(_ns("fullName"))
            field_name = (
                full_name_el.text
                if full_name_el is not None and full_name_el.text
                else field_xml.name.split(".")[0]
            )
            track_el = field_root.find(_ns("trackHistory"))
            all_fields.append(field_name)
            if track_el is not None and track_el.text == "true":
                tracked_fields.append(field_name)

    has_retention_policy = root.find(_ns("historyRetentionPolicy")) is not None

    return {
        "object_level_tracking": object_level_tracking,
        "tracked_fields": tracked_fields,
        "all_fields": all_fields,
        "has_retention_policy": has_retention_policy,
        "error": None,
    }


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

        # Check tracked-field count: 20 without FAT, 200 with FAT. A historyRetentionPolicy
        # block on the object is the signal that FAT is in use.
        has_policy = parsed.get("has_retention_policy", False)
        limit = FAT_FIELD_LIMIT if has_policy else FHT_FIELD_LIMIT
        if len(tracked) > limit:
            basis = "with Field Audit Trail" if has_policy else "without Field Audit Trail"
            issues.append(
                f"[{object_name}] History tracking enabled on {len(tracked)} fields "
                f"- exceeds the documented limit of {limit} per object {basis}."
            )

    return issues


def find_object_xml(objects_dir: Path, object_name: str) -> Path | None:
    """Return the object XML for object_name in SFDX or Metadata API layout."""
    sfdx_path = objects_dir / object_name / f"{object_name}.object-meta.xml"
    meta_path = objects_dir / f"{object_name}.object"
    if sfdx_path.exists():
        return sfdx_path
    if meta_path.exists():
        return meta_path
    return None


def check_retention_policy_presence(objects_dir: Path) -> list[str]:
    """Warn when no in-scope object carries a historyRetentionPolicy block.

    The Metadata API defines FAT retention policies as a historyRetentionPolicy block
    inside the object definition (api_meta HistoryRetentionPolicy).
    """
    issues: list[str] = []
    in_scope = []
    with_policy = []
    for object_name in HIGH_SENSITIVITY_FIELDS:
        candidate = find_object_xml(objects_dir, object_name)
        if candidate is None:
            continue
        in_scope.append(object_name)
        try:
            root = ET.parse(candidate).getroot()
        except ET.ParseError:
            continue
        if root.find(_ns("historyRetentionPolicy")) is not None:
            with_policy.append(object_name)
    if in_scope and not with_policy:
        issues.append(
            "No historyRetentionPolicy block found in any in-scope object definition. "
            "If Shield FAT is required for compliance, define a HistoryRetentionPolicy "
            "per object (Metadata API) and keep it in source control; the default "
            "archives after 18 months in production. "
            f"Objects in scope: {', '.join(in_scope)}"
        )
    return issues


def check_history_retention_policies(objects_dir: Path) -> list[str]:
    """Check historyRetentionPolicy blocks in object XML against the Metadata API field docs.

    archiveAfterMonths: required, 1-18. gracePeriodDays: 0-10 (api_meta HistoryRetentionPolicy).
    """
    issues: list[str] = []
    object_files = list(objects_dir.rglob("*.object-meta.xml")) + list(
        objects_dir.rglob("*.object")
    )
    for object_xml in object_files:
        try:
            root = ET.parse(object_xml).getroot()
        except ET.ParseError:
            continue
        for policy in root.findall(_ns("historyRetentionPolicy")):
            name = object_xml.name
            months_el = policy.find(_ns("archiveAfterMonths"))
            if months_el is None or not (months_el.text or "").strip():
                issues.append(
                    f"[{name}] historyRetentionPolicy has no archiveAfterMonths "
                    "(required; 1-18 months)."
                )
            else:
                try:
                    months = int(months_el.text.strip())
                except ValueError:
                    months = None
                if months is None or months < 1 or months > 18:
                    issues.append(
                        f"[{name}] archiveAfterMonths={months_el.text.strip()} is outside "
                        "the documented range of 1-18 months. It sets when history is "
                        "archived, not how long it is kept; use archiveRetentionYears "
                        "as the manual-deletion reminder."
                    )
            grace_el = policy.find(_ns("gracePeriodDays"))
            if grace_el is not None and (grace_el.text or "").strip():
                try:
                    grace = int(grace_el.text.strip())
                except ValueError:
                    grace = None
                if grace is None or grace < 0 or grace > 10:
                    issues.append(
                        f"[{name}] gracePeriodDays={grace_el.text.strip()} is outside "
                        "the documented range of 0-10 days."
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

    if objects_dir is None:
        issues.append(
            f"Could not locate an objects/ directory under {manifest_dir}. "
            "Ensure this is an SFDX or Metadata API project root."
        )
        return issues

    # Run individual checks
    issues.extend(check_fht_on_sensitive_fields(objects_dir))
    issues.extend(check_retention_policy_presence(objects_dir))
    issues.extend(check_history_retention_policies(objects_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Field Audit Trail configuration issues. "
            "Validates that high-sensitivity fields have Field History Tracking enabled "
            "(required for FAT to capture data), that tracked-field counts respect the "
            "documented limits, and that historyRetentionPolicy values are in range."
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
