#!/usr/bin/env python3
"""Checker script for Industries Energy Utilities Setup skill.

Checks org metadata or configuration relevant to Energy and Utilities Cloud setup.
Validates permission set assignments, ServicePoint object presence, and common
anti-patterns described in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_energy_utilities_setup.py [--help]
    python3 check_industries_energy_utilities_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SALESFORCE_NS = "http://soap.sforce.com/2006/04/metadata"

# E&U Cloud managed package permission set names (partial match)
EU_PERMISSION_SET_KEYWORDS = [
    "EnergyUtilities",
    "Energy_Utilities",
    "Energy_and_Utilities",
    "EnergyAndUtilities",
]

# Objects required for a valid E&U Cloud setup
EU_REQUIRED_OBJECTS = [
    "ServicePoint",
    "Meter",
    "MeterReading",
    "ServiceContract",
    "RatePlan",
]

# Anti-pattern: using Asset for meter tracking instead of the Meter object
ASSET_METER_FIELD_PATTERNS = [
    "MeterType",
    "MeterSerial",
    "ReadingSchedule",
    "MeterNumber",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Energy and Utilities Cloud metadata for common setup issues. "
            "Validates object presence, permission set patterns, and anti-patterns "
            "from references/gotchas.md."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all files with the given suffix under root."""
    return list(root.rglob(f"*{suffix}"))


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on parse failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def check_eu_objects_present(manifest_dir: Path) -> list[str]:
    """Check that the required E&U Cloud object metadata files exist."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Try force-app layout
        objects_dir = manifest_dir / "force-app" / "main" / "default" / "objects"
    if not objects_dir.exists():
        issues.append(
            "Cannot locate 'objects/' directory in manifest. "
            "Skipping E&U object presence check. "
            "Ensure the metadata is retrieved with the sfdx project structure."
        )
        return issues

    found_objects = {p.name for p in objects_dir.iterdir() if p.is_dir()}
    for required_obj in EU_REQUIRED_OBJECTS:
        if required_obj not in found_objects:
            issues.append(
                f"E&U Cloud object '{required_obj}' not found in objects/ directory. "
                f"Confirm the Energy and Utilities Cloud license is installed and the "
                f"object is included in the metadata retrieval."
            )
    return issues


def check_asset_meter_antipattern(manifest_dir: Path) -> list[str]:
    """Check for custom fields on Asset that suggest it is being used for meter tracking."""
    issues: list[str] = []
    asset_dir = manifest_dir / "objects" / "Asset"
    if not asset_dir.exists():
        asset_dir = (
            manifest_dir / "force-app" / "main" / "default" / "objects" / "Asset"
        )
    if not asset_dir.exists():
        return issues  # Asset metadata not present; skip check

    fields_dir = asset_dir / "fields"
    if not fields_dir.exists():
        return issues

    for field_file in fields_dir.glob("*.field-meta.xml"):
        field_name = field_file.stem.replace(".field-meta", "")
        for pattern in ASSET_METER_FIELD_PATTERNS:
            if pattern.lower() in field_name.lower():
                issues.append(
                    f"Custom field 'Asset.{field_name}' matches meter-tracking pattern "
                    f"'{pattern}'. In E&U Cloud, metering device data should be stored "
                    f"on the Meter object, not on Asset. "
                    f"See references/gotchas.md: 'ServicePoint Is a Distinct Object'."
                )
    return issues


def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Check that at least one E&U Cloud managed package permission set is present."""
    issues: list[str] = []
    ps_files = _find_xml_files(manifest_dir, ".permissionset-meta.xml")
    if not ps_files:
        issues.append(
            "No permission set metadata found. "
            "Cannot verify E&U Cloud managed package permission sets are assigned. "
            "Confirm the metadata retrieval includes permissionsets."
        )
        return issues

    eu_ps_found = []
    for ps_file in ps_files:
        name = ps_file.stem.replace(".permissionset-meta", "")
        for keyword in EU_PERMISSION_SET_KEYWORDS:
            if keyword.lower() in name.lower():
                eu_ps_found.append(name)
                break

    if not eu_ps_found:
        issues.append(
            "No Energy and Utilities Cloud managed package permission sets found "
            "in the retrieved metadata. "
            "E&U Cloud requires managed package permission sets (not custom permission sets) "
            "for users to access industry objects. "
            "Retrieve the permission sets from the E&U Cloud managed package and verify "
            "they are assigned to the appropriate users. "
            "See references/gotchas.md: 'Managed Package Permission Sets Are Required'."
        )
    return issues


def check_service_contract_rate_plan(manifest_dir: Path) -> list[str]:
    """Check ServiceContract validation rules for RatePlan requirement."""
    issues: list[str] = []
    sc_dir = manifest_dir / "objects" / "ServiceContract"
    if not sc_dir.exists():
        sc_dir = (
            manifest_dir
            / "force-app"
            / "main"
            / "default"
            / "objects"
            / "ServiceContract"
        )
    if not sc_dir.exists():
        return issues

    validation_dir = sc_dir / "validationRules"
    if not validation_dir.exists():
        issues.append(
            "No validation rules found on ServiceContract. "
            "Consider adding a validation rule to enforce a non-null RatePlanId "
            "before a ServiceContract can be set to Active status. "
            "Without this, ServiceContracts with null RatePlan references are accepted "
            "silently, causing billing cycle failures. "
            "See references/gotchas.md: 'ServiceContract Status Remains Draft When RatePlanId Is Null'."
        )
        return issues

    rate_plan_validation_found = False
    for vr_file in validation_dir.glob("*.validationRule-meta.xml"):
        root = _parse_xml_safe(vr_file)
        if root is None:
            continue
        # Look for validation rule that references RatePlan
        error_condition = ""
        for elem in root.iter():
            if elem.tag.endswith("errorConditionFormula") and elem.text:
                error_condition = elem.text
        if "RatePlan" in error_condition:
            rate_plan_validation_found = True
            break

    if not rate_plan_validation_found:
        issues.append(
            "No validation rule on ServiceContract references RatePlan. "
            "A validation rule enforcing non-null RatePlanId (or equivalent) "
            "is recommended to prevent silent billing failures. "
            "See references/gotchas.md: 'Incomplete CIS Integration Silently Breaks Billing Cycles'."
        )
    return issues


def check_industries_energy_utilities_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_eu_objects_present(manifest_dir))
    issues.extend(check_asset_meter_antipattern(manifest_dir))
    issues.extend(check_permission_sets(manifest_dir))
    issues.extend(check_service_contract_rate_plan(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_industries_energy_utilities_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
