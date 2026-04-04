#!/usr/bin/env python3
"""Checker script for Custom Index Requests skill.

Scans Salesforce custom field metadata for index-related anti-patterns:
- Custom fields marked as External ID that appear to be non-unique filter fields
  (field names suggest categories, statuses, types — not external system keys)
- Very wide objects (100+ fields) that may benefit from skinny table analysis

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_custom_index_requests.py [--help]
    python3 check_custom_index_requests.py --metadata-dir path/to/force-app/main/default/objects
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce custom field metadata for index anti-patterns.",
    )
    parser.add_argument(
        "--metadata-dir",
        default=".",
        help="Directory containing Salesforce object/field metadata (default: current directory).",
    )
    return parser.parse_args()


# Field names suggesting categorical/status values — not unique external IDs
CATEGORICAL_INDICATORS = [
    "status", "type", "category", "segment", "region", "tier", "level",
    "priority", "source", "channel", "stage", "phase", "group", "class",
]


def scan_field_metadata(metadata_dir: Path) -> list[str]:
    """Scan custom field XML files for index anti-patterns."""
    issues: list[str] = []

    if not metadata_dir.exists():
        issues.append(f"Metadata directory not found: {metadata_dir}")
        return issues

    field_files = list(metadata_dir.rglob("*.field-meta.xml"))
    if not field_files:
        return issues

    # Track field count per object for skinny table recommendation
    object_field_counts: dict[str, int] = {}

    for field_file in field_files:
        try:
            content = field_file.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue

        # Count fields per object
        object_name = field_file.parent.parent.name
        object_field_counts[object_name] = object_field_counts.get(object_name, 0) + 1

        # Parse XML to check externalId flag
        try:
            tree = ET.parse(field_file)
            root = tree.getroot()
        except ET.ParseError:
            continue

        # Handle namespace
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        external_id_elem = root.find(f"{ns}externalId")
        unique_elem = root.find(f"{ns}unique")

        is_external_id = external_id_elem is not None and external_id_elem.text == "true"
        is_unique = unique_elem is not None and unique_elem.text == "true"

        if is_external_id and not is_unique:
            # External ID without Unique is unusual but possible
            pass

        if is_external_id:
            field_name_lower = field_file.stem.lower().replace(".field-meta", "")
            for indicator in CATEGORICAL_INDICATORS:
                if indicator in field_name_lower:
                    issues.append(
                        f"{object_name}.{field_file.stem}: Field '{field_file.stem}' is marked "
                        f"as External ID (creates a unique index). The field name suggests it may "
                        f"be a categorical/status field with duplicate values. External ID enforces "
                        f"uniqueness — if this field is not a unique external system key, upsert "
                        f"operations will fail on duplicate values. Use a non-unique custom index "
                        f"(via Support case) for non-unique filter fields."
                    )
                    break

    # Check for wide objects (100+ fields) — skinny table candidates
    for obj_name, count in object_field_counts.items():
        if count >= 100:
            issues.append(
                f"Object '{obj_name}' has {count} custom field metadata files. Wide objects "
                f"(100+ fields) may benefit from a Salesforce Support request for a skinny table "
                f"if high-frequency read queries always access the same small field subset. "
                f"Review Query Plan output for this object before requesting."
            )

    return issues


def check_custom_index_requests(metadata_dir: Path) -> list[str]:
    """Return a list of issue strings."""
    return scan_field_metadata(metadata_dir)


def main() -> int:
    args = parse_args()
    metadata_dir = Path(args.metadata_dir)
    issues = check_custom_index_requests(metadata_dir)

    if not issues:
        print("No custom index anti-patterns found in field metadata.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\nFound {len(issues)} issue(s). Review before filing a Support case.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
