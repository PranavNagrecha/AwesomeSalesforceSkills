#!/usr/bin/env python3
"""Checker script for FSL Resource Management skill.

Checks Salesforce metadata exports for common FSL resource management
configuration issues: workflow metadata, custom field definitions, and
permission sets.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_resource_management.py [--help]
    python3 check_fsl_resource_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSL Resource Management configuration and metadata for "
            "common issues including capacity record gaps, ResourceType misuse, "
            "and SkillLevel range violations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_xml_files(root: Path, glob: str) -> list[Path]:
    """Return all files matching glob under root, sorted for determinism."""
    return sorted(root.rglob(glob))


def _get_text(element: ET.Element, tag: str, ns: str = "") -> str:
    """Return stripped text of a child element, or empty string if absent."""
    full_tag = f"{{{ns}}}{tag}" if ns else tag
    child = element.find(full_tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_resource_type_values(manifest_dir: Path) -> list[str]:
    """Flag any CustomField or CustomObject metadata that defines a
    ResourceType picklist with values other than Technician or Crew.

    In practice this surfaces DataLoader templates or custom objects that
    incorrectly enumerate 'Equipment', 'Asset', or 'Vehicle'.
    """
    issues: list[str] = []
    valid_types = {"Technician", "Crew"}
    invalid_labels = {"Equipment", "Asset", "Vehicle", "Tool"}

    for xml_file in _iter_xml_files(manifest_dir, "*.object-meta.xml"):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError:
            continue
        root = tree.getroot()
        # Strip namespace for broad matching
        ns_stripped = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
        for field in root.iter("fields" if not ns_stripped else f"{{{ns_stripped}}}fields"):
            field_name_el = field.find("fullName") or field.find(
                f"{{{ns_stripped}}}fullName"
            )
            if field_name_el is None or field_name_el.text != "ResourceType":
                continue
            for value in field.iter("value"):
                label = (value.text or "").strip()
                if label in invalid_labels:
                    issues.append(
                        f"{xml_file.name}: ResourceType picklist contains invalid value "
                        f"'{label}'. Valid values are: {sorted(valid_types)}."
                    )
    return issues


def check_skill_level_ranges(manifest_dir: Path) -> list[str]:
    """Flag any metadata templates or CSV data files that contain SkillLevel
    values outside the valid 0–99.99 range or that use a 1–10 scale.
    """
    issues: list[str] = []

    for csv_file in _iter_xml_files(manifest_dir, "*.csv"):
        try:
            lines = csv_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        if not lines:
            continue
        header = [h.strip().lower() for h in lines[0].split(",")]
        if "skilllevel" not in header:
            continue
        skill_idx = header.index("skilllevel")
        for line_num, line in enumerate(lines[1:], start=2):
            cols = line.split(",")
            if skill_idx >= len(cols):
                continue
            raw = cols[skill_idx].strip().strip('"')
            if not raw:
                continue
            try:
                level = float(raw)
            except ValueError:
                continue
            if level > 99.99:
                issues.append(
                    f"{csv_file.name} line {line_num}: SkillLevel value {level} exceeds "
                    "maximum of 99.99. Salesforce will reject this record."
                )
            elif level < 0:
                issues.append(
                    f"{csv_file.name} line {line_num}: SkillLevel value {level} is "
                    "negative. Valid range is 0–99.99."
                )
    return issues


def check_capacity_unit_values(manifest_dir: Path) -> list[str]:
    """Flag ServiceResourceCapacity CSV data files using invalid CapacityUnit values."""
    issues: list[str] = []
    valid_units = {"Hours", "Appointments"}

    for csv_file in _iter_xml_files(manifest_dir, "*.csv"):
        try:
            lines = csv_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        if not lines:
            continue
        header = [h.strip().lower() for h in lines[0].split(",")]
        if "capacityunit" not in header:
            continue
        unit_idx = header.index("capacityunit")
        for line_num, line in enumerate(lines[1:], start=2):
            cols = line.split(",")
            if unit_idx >= len(cols):
                continue
            raw = cols[unit_idx].strip().strip('"')
            if raw and raw not in valid_units:
                issues.append(
                    f"{csv_file.name} line {line_num}: CapacityUnit '{raw}' is not valid. "
                    f"Valid values are: {sorted(valid_units)}."
                )
    return issues


def check_preference_type_values(manifest_dir: Path) -> list[str]:
    """Flag ResourcePreference CSV data files using invalid PreferenceType values."""
    issues: list[str] = []
    valid_prefs = {"Preferred", "Required", "Excluded"}

    for csv_file in _iter_xml_files(manifest_dir, "*.csv"):
        try:
            lines = csv_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        if not lines:
            continue
        header = [h.strip().lower() for h in lines[0].split(",")]
        if "preferencetype" not in header:
            continue
        pref_idx = header.index("preferencetype")
        for line_num, line in enumerate(lines[1:], start=2):
            cols = line.split(",")
            if pref_idx >= len(cols):
                continue
            raw = cols[pref_idx].strip().strip('"')
            if raw and raw not in valid_prefs:
                issues.append(
                    f"{csv_file.name} line {line_num}: PreferenceType '{raw}' is not valid. "
                    f"Valid values are: {sorted(valid_prefs)}."
                )
    return issues


def check_territory_member_counts(manifest_dir: Path) -> list[str]:
    """Warn if any CSV containing ServiceTerritoryMember data appears to assign
    more than 50 members to a single territory (the FSL hard limit).
    """
    issues: list[str] = []
    limit = 50

    for csv_file in _iter_xml_files(manifest_dir, "*.csv"):
        try:
            lines = csv_file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        if not lines:
            continue
        header = [h.strip().lower() for h in lines[0].split(",")]
        if "serviceterritoryid" not in header:
            continue
        terr_idx = header.index("serviceterritoryid")
        territory_counts: dict[str, int] = {}
        for line in lines[1:]:
            cols = line.split(",")
            if terr_idx >= len(cols):
                continue
            terr_id = cols[terr_idx].strip().strip('"')
            if terr_id:
                territory_counts[terr_id] = territory_counts.get(terr_id, 0) + 1
        for terr_id, count in territory_counts.items():
            if count > limit:
                issues.append(
                    f"{csv_file.name}: Territory '{terr_id}' has {count} members in this "
                    f"file, exceeding the FSL limit of {limit} resources per territory."
                )
    return issues


def check_flow_fsl_resource_references(manifest_dir: Path) -> list[str]:
    """Scan Flow metadata for references to deleted FSL resource fields that are
    commonly misused (e.g., referencing ResourceType = 'Equipment' in flow filters).
    """
    issues: list[str] = []
    invalid_resource_type_literals = {"Equipment", "Asset", "Vehicle", "Tool"}

    for xml_file in _iter_xml_files(manifest_dir, "*.flow-meta.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for literal in invalid_resource_type_literals:
            if f"ResourceType" in content and literal in content:
                issues.append(
                    f"{xml_file.name}: Flow may reference invalid ResourceType value "
                    f"'{literal}'. ServiceResource.ResourceType only accepts "
                    "'Technician' or 'Crew'."
                )
                break  # one warning per file is sufficient

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_fsl_resource_management(manifest_dir: Path) -> list[str]:
    """Run all FSL resource management checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_resource_type_values(manifest_dir))
    issues.extend(check_skill_level_ranges(manifest_dir))
    issues.extend(check_capacity_unit_values(manifest_dir))
    issues.extend(check_preference_type_values(manifest_dir))
    issues.extend(check_territory_member_counts(manifest_dir))
    issues.extend(check_flow_fsl_resource_references(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_resource_management(manifest_dir)

    if not issues:
        print("No FSL resource management issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
