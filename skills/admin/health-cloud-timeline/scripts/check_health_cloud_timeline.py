#!/usr/bin/env python3
"""Checker script for Health Cloud Timeline skill.

Validates TimelineObjectDefinition metadata and related configuration for
common issues documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_timeline.py [--help]
    python3 check_health_cloud_timeline.py --manifest-dir path/to/metadata
    python3 check_health_cloud_timeline.py --manifest-dir path/to/metadata --categories "Medications,Encounters,Labs"
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


TIMELINE_OBJECT_DEF_SUFFIX = ".timelineObjectDefinition-meta.xml"
LEGACY_COMPONENT_NAMES = {"HealthCloud__Timeline", "HealthCloud.Timeline", "healthcloud:timeline"}
FORMULA_FIELD_SUFFIX_HINTS = ("_Formula__c", "formula", "Formula")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Health Cloud Enhanced Timeline configuration for common issues. "
            "Validates TimelineObjectDefinition metadata files and optionally checks "
            "category name consistency."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source (default: current directory).",
    )
    parser.add_argument(
        "--categories",
        default="",
        help=(
            "Comma-separated list of valid timeline category names as configured in "
            "Setup > Timeline > Categories. Used to detect category name mismatches."
        ),
    )
    return parser.parse_args()


def find_timeline_definitions(manifest_dir: Path) -> list[Path]:
    """Return all TimelineObjectDefinition metadata files under manifest_dir."""
    return list(manifest_dir.rglob(f"*{TIMELINE_OBJECT_DEF_SUFFIX}"))


def check_definition_file(def_file: Path, valid_categories: set[str]) -> list[str]:
    """Validate a single TimelineObjectDefinition XML file. Returns issue strings."""
    issues: list[str] = []
    rel = def_file.relative_to(def_file.anchor) if def_file.is_absolute() else def_file

    try:
        tree = ET.parse(def_file)
        root = tree.getroot()
    except ET.ParseError as exc:
        issues.append(f"{rel}: XML parse error — {exc}")
        return issues

    # Strip namespace from tag for comparison
    def tag(element: ET.Element) -> str:
        return element.tag.split("}")[-1] if "}" in element.tag else element.tag

    fields: dict[str, str] = {tag(child): (child.text or "").strip() for child in root}

    # Check active flag
    active_val = fields.get("active", fields.get("isActive", "")).lower()
    if active_val not in ("true",):
        issues.append(
            f"{rel}: 'active' is '{active_val}' — TimelineObjectDefinition must be set to true to appear on timeline"
        )

    # Check required fields
    for required_field in ("baseObject", "dateField", "label", "labelPlural", "nameField"):
        if not fields.get(required_field):
            issues.append(f"{rel}: Missing or empty required field '{required_field}'")

    # Check for formula field used as dateField (known anti-pattern)
    date_field = fields.get("dateField", "")
    if any(hint in date_field for hint in FORMULA_FIELD_SUFFIX_HINTS):
        issues.append(
            f"{rel}: dateField '{date_field}' looks like a formula field. "
            "Formula fields are not supported as timeline date fields — use a real date/datetime field."
        )

    # Check timelineCategory against known valid categories
    category = fields.get("timelineCategory", "")
    if valid_categories and category not in valid_categories:
        issues.append(
            f"{rel}: timelineCategory '{category}' does not match any known category. "
            f"Valid categories: {sorted(valid_categories)}. "
            "Category mismatch silently drops records from the timeline."
        )
    elif not category:
        issues.append(
            f"{rel}: 'timelineCategory' is empty — records will not appear under any filter category"
        )

    return issues


def check_for_legacy_component(manifest_dir: Path) -> list[str]:
    """Scan flexipage XML files for references to the deprecated legacy timeline component."""
    issues: list[str] = []
    flexipages = list(manifest_dir.rglob("*.flexipage-meta.xml"))
    for fp in flexipages:
        try:
            content = fp.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for legacy_name in LEGACY_COMPONENT_NAMES:
            if legacy_name.lower() in content.lower():
                rel = fp.relative_to(manifest_dir) if fp.is_relative_to(manifest_dir) else fp
                issues.append(
                    f"{rel}: references deprecated legacy timeline component '{legacy_name}'. "
                    "Migrate to the Industries Timeline component (industries:timeline) "
                    "backed by TimelineObjectDefinition metadata."
                )
                break  # one warning per file is enough
    return issues


def check_health_cloud_timeline(manifest_dir: Path, valid_categories: set[str]) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    def_files = find_timeline_definitions(manifest_dir)
    if not def_files:
        # Not necessarily an error — org may not have timeline configured yet
        issues.append(
            "No TimelineObjectDefinition files found. "
            "If the Industries Timeline component is in use, ensure "
            "*.timelineObjectDefinition-meta.xml files are included in the metadata source."
        )
    else:
        for def_file in sorted(def_files):
            issues.extend(check_definition_file(def_file, valid_categories))

    issues.extend(check_for_legacy_component(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    valid_categories: set[str] = set()
    if args.categories:
        valid_categories = {c.strip() for c in args.categories.split(",") if c.strip()}

    issues = check_health_cloud_timeline(manifest_dir, valid_categories)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
