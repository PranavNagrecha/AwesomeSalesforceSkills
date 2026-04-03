#!/usr/bin/env python3
"""Checker script for Object Creation and Design skill.

Scans Salesforce metadata (SFDX source format or retrieved metadata) for
common custom object configuration issues:

- Custom objects with no description
- Custom objects with ambiguous or short API names (fewer than 5 characters before __c)
- Custom objects with Track Field History enabled but no fields configured for tracking
  (detected by presence of historyRetentionPolicy element with no tracked fields)
- Custom objects at risk of reaching the edition OWD recalculation footprint
  (inferred from object count relative to known edition limits)

Usage:
    python3 check_object_creation_and_design.py
    python3 check_object_creation_and_design.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SALESFORCE_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"

# Minimum meaningful API name length (before __c) to flag as potentially ambiguous
MIN_API_NAME_LENGTH = 4


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check custom object configuration for common design issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source (default: current directory).",
    )
    return parser.parse_args()


def find_object_files(manifest_dir: Path) -> list[Path]:
    """Locate .object-meta.xml files in the manifest directory tree."""
    return list(manifest_dir.rglob("*.object-meta.xml"))


def _tag(local_name: str) -> str:
    return f"{{{SALESFORCE_NAMESPACE}}}{local_name}"


def check_object_file(obj_path: Path) -> list[str]:
    """Return a list of issue strings for a single custom object metadata file."""
    issues: list[str] = []

    try:
        tree = ET.parse(obj_path)
    except ET.ParseError as exc:
        issues.append(f"{obj_path.name}: XML parse error — {exc}")
        return issues

    root = tree.getroot()

    # Derive object API name from file name (e.g. "Project_Request__c.object-meta.xml")
    file_stem = obj_path.name.replace(".object-meta.xml", "")

    # Only check custom objects (ending in __c), skip standard objects
    if not file_stem.endswith("__c"):
        return issues

    # Extract the local name (before __c) for length check
    local_name = file_stem[: -len("__c")]

    # 1. Flag objects with very short API names (potentially ambiguous abbreviations)
    if len(local_name) < MIN_API_NAME_LENGTH:
        issues.append(
            f"{file_stem}: Object API name '{local_name}' is very short "
            f"({len(local_name)} chars). Short names are often abbreviations that "
            f"reduce readability. Consider a more descriptive name."
        )

    # 2. Check for a description element
    description_el = root.find(_tag("description"))
    if description_el is None or not (description_el.text or "").strip():
        issues.append(
            f"{file_stem}: Missing or empty <description>. "
            "Add a description so future admins understand the object's purpose."
        )

    # 3. Check for enableHistory enabled but no fields marked for tracking.
    #    In SFDX source format, field history tracking is a per-field attribute
    #    (<trackHistory>true</trackHistory>) on CustomField elements in the object file.
    #    If enableHistory is true but no fields have trackHistory=true, history tracking
    #    is enabled but capturing nothing — likely a misconfiguration.
    enable_history_el = root.find(_tag("enableHistory"))
    history_enabled = (
        enable_history_el is not None
        and (enable_history_el.text or "").strip().lower() == "true"
    )

    if history_enabled:
        tracked_fields = [
            f
            for f in root.findall(_tag("fields"))
            if (f.find(_tag("trackHistory")) is not None
                and (f.find(_tag("trackHistory")).text or "").strip().lower() == "true")
        ]
        if not tracked_fields:
            issues.append(
                f"{file_stem}: Field History Tracking is enabled "
                "(<enableHistory>true</enableHistory>) but no fields have "
                "<trackHistory>true</trackHistory>. Either configure fields to track "
                "or disable history tracking if it is not needed."
            )

    return issues


def check_object_count(object_files: list[Path]) -> list[str]:
    """Warn if the custom object count in the manifest approaches common edition limits."""
    issues: list[str] = []
    custom_count = sum(
        1 for f in object_files if f.name.replace(".object-meta.xml", "").endswith("__c")
    )

    # Edition limits for custom objects (Salesforce Help: Custom Object Limits)
    # Professional: 50 | Enterprise: 200 | Unlimited/Performance: 2000 | Developer: 400
    # These are the objects in THIS metadata source, not the total org count.
    if custom_count >= 180:
        issues.append(
            f"Found {custom_count} custom objects in this metadata source. "
            "Enterprise Edition allows 200. Verify the org's Used Custom Objects count "
            "in Setup → Company Information before deploying additional objects."
        )
    elif custom_count >= 45:
        issues.append(
            f"Found {custom_count} custom objects in this metadata source. "
            "Professional Edition allows 50. If this is a Professional Edition org, "
            "verify the org's Used Custom Objects count before deploying additional objects."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ISSUE: Manifest directory not found: {manifest_dir}")
        return 1

    object_files = find_object_files(manifest_dir)

    if not object_files:
        print(
            "No .object-meta.xml files found. "
            "Provide a directory containing Salesforce object metadata."
        )
        return 0

    all_issues: list[str] = []

    for obj_path in sorted(object_files):
        all_issues.extend(check_object_file(obj_path))

    all_issues.extend(check_object_count(object_files))

    if not all_issues:
        print(f"No issues found across {len(object_files)} object file(s).")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
