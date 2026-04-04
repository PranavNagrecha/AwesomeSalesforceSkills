#!/usr/bin/env python3
"""Checker script for Data Storage Management skill.

Analyzes Salesforce org metadata to surface storage management issues:
- Objects with Long Text Area or Rich Text Area fields (potential data storage inflation)
- Attachment usage (prefer ContentDocument migration)
- Field History Tracking enabled on high-volume-risk objects
- ContentDocument / ContentVersion patterns

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_storage_management.py --help
    python3 check_data_storage_management.py --manifest-dir path/to/metadata
    python3 check_data_storage_management.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SALESFORCE_NS = "http://soap.sforce.com/2006/04/metadata"

# Field types that can inflate data storage beyond the 2 KB average
LARGE_FIELD_TYPES = {"LongTextArea", "Html", "Textarea", "EncryptedText"}

# Field types that are not storage-concerning
SMALL_FIELD_TYPES = {
    "Text", "Number", "Checkbox", "Date", "DateTime", "Email",
    "Phone", "Url", "Picklist", "MultiselectPicklist", "Reference",
    "Currency", "Double", "Integer", "Percent",
}

# Objects where field history tracking creates high-volume history records
HIGH_VOLUME_RISK_OBJECTS = {
    "Opportunity", "Case", "Lead", "Contact", "Account",
    "Order", "Contract", "Task", "Event",
}

# Maximum recommended Long Text Area fields per object before flagging
MAX_LARGE_TEXT_FIELDS = 5

# Maximum field length (chars) before flagging as extra-large
EXTRA_LARGE_FIELD_THRESHOLD = 65536  # 64K chars — half the platform max


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def _tag(local: str) -> str:
    """Return a namespaced tag string for Salesforce metadata XML."""
    return f"{{{SALESFORCE_NS}}}{local}"


def _find_text(element: ET.Element, local_tag: str, default: str = "") -> str:
    child = element.find(_tag(local_tag))
    return child.text.strip() if child is not None and child.text else default


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_custom_objects(manifest_dir: Path) -> list[str]:
    """Inspect CustomObject XML files for storage anti-patterns."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"

    if not objects_dir.exists():
        # Try sfdx project layout: objects/<ObjectName>/<ObjectName>.object-meta.xml
        objects_dir = manifest_dir
        xml_files = list(manifest_dir.rglob("*.object-meta.xml"))
        if not xml_files:
            # No objects to check
            return issues
    else:
        xml_files = list(objects_dir.rglob("*.object-meta.xml")) + list(
            objects_dir.glob("*.object")
        )

    for xml_file in xml_files:
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"XML parse error in {xml_file.name}: {exc}")
            continue

        root = tree.getroot()
        object_name = xml_file.stem.replace(".object-meta", "").replace(".object", "")

        # Count large text fields on this object
        large_text_fields: list[tuple[str, str, int]] = []
        history_tracking_fields: list[str] = []

        for field_el in root.findall(_tag("fields")):
            field_name = _find_text(field_el, "fullName")
            field_type = _find_text(field_el, "type")
            length_text = _find_text(field_el, "length")
            track_history = _find_text(field_el, "trackHistory", "false").lower()

            if field_type in LARGE_FIELD_TYPES:
                length = int(length_text) if length_text.isdigit() else 0
                large_text_fields.append((field_name, field_type, length))

            if track_history == "true":
                history_tracking_fields.append(field_name)

        if len(large_text_fields) > MAX_LARGE_TEXT_FIELDS:
            issues.append(
                f"{object_name}: has {len(large_text_fields)} large text/rich text fields "
                f"({', '.join(f[0] for f in large_text_fields[:3])}...). "
                f"More than {MAX_LARGE_TEXT_FIELDS} large text fields can significantly inflate "
                f"data storage beyond the 2 KB average per record."
            )

        for field_name, field_type, length in large_text_fields:
            if length >= EXTRA_LARGE_FIELD_THRESHOLD:
                issues.append(
                    f"{object_name}.{field_name}: {field_type} field with length {length} chars "
                    f"(>={EXTRA_LARGE_FIELD_THRESHOLD}). Extra-large text fields on high-volume "
                    f"objects can cause severe data storage inflation. "
                    f"Consider whether this content could be stored as a ContentDocument instead."
                )

        if history_tracking_fields and object_name in HIGH_VOLUME_RISK_OBJECTS:
            issues.append(
                f"{object_name}: field history tracking enabled on "
                f"{len(history_tracking_fields)} field(s) "
                f"({', '.join(history_tracking_fields[:5])}). "
                f"High-volume objects with tracking generate large numbers of history records "
                f"that count toward data storage. Disable tracking on low-value fields or "
                f"evaluate Field Audit Trail."
            )

    return issues


def check_for_attachment_usage(manifest_dir: Path) -> list[str]:
    """Detect Apex classes that reference the Attachment sObject in DML."""
    issues: list[str] = []
    apex_dir = manifest_dir / "classes"

    if not apex_dir.exists():
        apex_files = list(manifest_dir.rglob("*.cls"))
    else:
        apex_files = list(apex_dir.glob("*.cls"))

    attachment_files: list[str] = []
    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Look for Attachment DML patterns (insert new Attachment, new Attachment())
        lower = content.lower()
        if "new attachment(" in lower or "insert attachment" in lower or "attachment att" in lower:
            attachment_files.append(apex_file.name)

    if attachment_files:
        issues.append(
            f"Apex classes reference the Attachment sObject in DML "
            f"({', '.join(attachment_files[:5])}{'...' if len(attachment_files) > 5 else ''}). "
            f"Attachments are legacy and create binary duplicates per parent record. "
            f"Migrate to ContentVersion + ContentDocumentLink to enable deduplication "
            f"and sharing without duplicating file storage."
        )

    return issues


def check_content_document_links(manifest_dir: Path) -> list[str]:
    """Check for Apex code that creates ContentDocumentLink with overly broad Visibility."""
    issues: list[str] = []
    apex_dir = manifest_dir / "classes"

    if not apex_dir.exists():
        apex_files = list(manifest_dir.rglob("*.cls"))
    else:
        apex_files = list(apex_dir.glob("*.cls"))

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Detect AllUsers visibility on ContentDocumentLink — potential security exposure
        if "contentdocumentlink" in content.lower() and "'allusers'" in content.lower():
            issues.append(
                f"{apex_file.name}: ContentDocumentLink created with Visibility = 'AllUsers'. "
                f"Verify this is intentional — 'AllUsers' exposes the file to all internal users "
                f"regardless of record sharing. Use 'InternalUsers' or 'SharedUsers' if "
                f"restricted access is needed."
            )

    return issues


def check_storage_monitoring(manifest_dir: Path) -> list[str]:
    """Look for signs of storage monitoring setup (Limits API calls, scheduled jobs)."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls"))

    has_limits_check = False
    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "datastoragemb" in content.lower() or "filestoragemb" in content.lower():
            has_limits_check = True
            break

    if apex_files and not has_limits_check:
        issues.append(
            "No Apex code found that references DataStorageMB or FileStorageMB from the "
            "Limits API. Consider implementing automated storage monitoring that alerts "
            "when remaining storage drops below 25% of allocation. "
            "Salesforce built-in alerts (75%/90%/100%) are a lagging safety net, "
            "not a proactive monitoring strategy."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_data_storage_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_custom_objects(manifest_dir))
    issues.extend(check_for_attachment_usage(manifest_dir))
    issues.extend(check_content_document_links(manifest_dir))
    issues.extend(check_storage_monitoring(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for data storage management issues: "
            "large text fields, Attachment usage, ContentDocumentLink security, "
            "field history tracking on high-volume objects, and monitoring gaps."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_storage_management(manifest_dir)

    if not issues:
        print("No storage management issues found.")
        return 0

    print(f"Found {len(issues)} storage management issue(s):\n")
    for i, issue in enumerate(issues, start=1):
        print(f"ISSUE {i}: {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
