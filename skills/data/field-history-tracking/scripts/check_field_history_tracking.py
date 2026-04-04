#!/usr/bin/env python3
"""Checker script for Field History Tracking skill.

Analyzes a Salesforce metadata directory for common field history tracking
configuration issues: objects with history enabled but no fields selected,
fields exceeding the 20-per-object limit, and ineligible field types
(formula, roll-up summary, auto-number) marked for tracking.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_field_history_tracking.py [--help]
    python3 check_field_history_tracking.py --manifest-dir path/to/force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Standard Field History Tracking limit per object
FHT_FIELD_LIMIT = 20

# Field types ineligible for history tracking
INELIGIBLE_FIELD_TYPES = {
    "Formula",
    "Summary",       # roll-up summary
    "AutoNumber",
    "Text",          # Long Text Area is not trackable; plain Text is fine, but flag as advisory
}

# Types confirmed ineligible (hard failures)
HARD_INELIGIBLE_TYPES = {"Formula", "Summary", "AutoNumber"}

SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


def _ns(tag: str) -> str:
    return f"{{{SF_NAMESPACE}}}{tag}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Field History Tracking configuration issues. "
            "Looks for objects with history enabled, counts tracked fields per object, "
            "and flags ineligible field types marked for tracking."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata source tree (default: current directory). "
             "Expects an 'objects/' subdirectory in SFDX source format.",
    )
    return parser.parse_args()


def find_object_metadata(objects_dir: Path) -> list[Path]:
    """Return all .object-meta.xml files under objects_dir."""
    return list(objects_dir.glob("**/*.object-meta.xml"))


def find_field_metadata(objects_dir: Path) -> list[Path]:
    """Return all .field-meta.xml files under objects_dir."""
    return list(objects_dir.glob("**/fields/*.field-meta.xml"))


def get_text(element: ET.Element, tag: str) -> str | None:
    child = element.find(_ns(tag))
    if child is not None and child.text:
        return child.text.strip()
    return None


def check_object_history_enabled(obj_file: Path) -> bool | None:
    """Return True if enableHistory is true, False if false, None if tag absent."""
    try:
        tree = ET.parse(obj_file)
        root = tree.getroot()
        enable = get_text(root, "enableHistory")
        if enable is None:
            return None
        return enable.lower() == "true"
    except ET.ParseError:
        return None


def check_field_track_history(field_file: Path) -> tuple[bool, str | None]:
    """Return (track_history_enabled, field_type) from a field metadata file."""
    try:
        tree = ET.parse(field_file)
        root = tree.getroot()
        track = get_text(root, "trackHistory")
        field_type = get_text(root, "type")
        track_enabled = (track is not None and track.lower() == "true")
        return track_enabled, field_type
    except ET.ParseError:
        return False, None


def check_field_history_tracking(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Try one level up (sometimes source root contains objects/ directly)
        alt = manifest_dir.parent / "objects"
        if alt.exists():
            objects_dir = alt
        else:
            issues.append(
                f"No 'objects/' directory found under {manifest_dir}. "
                "Run this checker from the Salesforce source root "
                "(e.g., force-app/main/default)."
            )
            return issues

    # --- Check 1: Objects with history enabled but zero tracked fields ---
    obj_files = find_object_metadata(objects_dir)
    history_enabled_objects: set[str] = set()

    for obj_file in obj_files:
        enabled = check_object_history_enabled(obj_file)
        if enabled is True:
            obj_name = obj_file.parent.name  # directory name = object API name
            history_enabled_objects.add(obj_name)

    # --- Check 2: Count tracked fields per object and detect ineligible types ---
    field_files = find_field_metadata(objects_dir)

    # object_name -> list of (field_file_name, field_type)
    tracked_fields_by_object: dict[str, list[tuple[str, str | None]]] = {}

    for field_file in field_files:
        track_enabled, field_type = check_field_track_history(field_file)
        if not track_enabled:
            continue

        # Infer object name from path: objects/<ObjectName>/fields/<FieldName>.field-meta.xml
        parts = field_file.parts
        try:
            obj_idx = parts.index("objects") + 1  # type: ignore[arg-type]
            obj_name = parts[obj_idx]
        except (ValueError, IndexError):
            obj_name = "unknown"

        field_name = field_file.stem.replace(".field-meta", "")
        tracked_fields_by_object.setdefault(obj_name, []).append((field_name, field_type))

        # Flag ineligible field types
        if field_type in HARD_INELIGIBLE_TYPES:
            issues.append(
                f"[{obj_name}] Field '{field_name}' has trackHistory=true but its type "
                f"'{field_type}' is ineligible for Field History Tracking. "
                "Salesforce will not track this field — remove trackHistory or change the field type."
            )

    # Check per-object field count against 20-field limit
    for obj_name, fields in tracked_fields_by_object.items():
        count = len(fields)
        if count > FHT_FIELD_LIMIT:
            field_names = ", ".join(f for f, _ in fields)
            issues.append(
                f"[{obj_name}] {count} fields are marked trackHistory=true, "
                f"exceeding the platform limit of {FHT_FIELD_LIMIT}. "
                f"Tracked fields: {field_names}. "
                "Reduce to 20 or fewer, or license Shield Field Audit Trail for up to 60."
            )
        elif count == FHT_FIELD_LIMIT:
            issues.append(
                f"[{obj_name}] WARNING: Exactly {FHT_FIELD_LIMIT} fields tracked — "
                "at the limit. No additional fields can be enabled without removing one first."
            )

    # Check for objects with history enabled but no tracked fields
    for obj_name in history_enabled_objects:
        if obj_name not in tracked_fields_by_object:
            issues.append(
                f"[{obj_name}] Object has enableHistory=true but no fields have "
                "trackHistory=true. Enable tracking on at least one field, "
                "or disable object-level history if it is no longer needed."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_field_history_tracking(manifest_dir)

    if not issues:
        print("No field history tracking issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
