#!/usr/bin/env python3
"""Checker script for Automotive Cloud Setup skill.

Scans force-app/ metadata for common Automotive Cloud anti-patterns:

- Custom Vehicle__c / VehicleDefinition__c objects (suggest standard objects)
- Misplaced fields (per-VIN state on VehicleDefinition, build specs on Vehicle)
- ParentId-based dealer hierarchy (suggest AccountAccountRelation)
- Direct DML on ActionableEventOrchestration.Status

Stdlib only.

Usage:
    python3 check_automotive_cloud_setup.py [--manifest-dir force-app]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PER_VIN_FIELD_HINTS = {"mileage", "currentowner", "lastservice", "registration", "odometer", "vin"}
BUILD_SPEC_FIELD_HINTS = {"msrp", "trim", "bodystyle", "fueltype", "drivetrain", "horsepower", "modelyear"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Automotive Cloud Setup metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _custom_objects(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.rglob("*.object-meta.xml")) + list(manifest_dir.rglob("*.object"))


def _custom_fields(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.rglob("*.field-meta.xml"))


def _apex_classes(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))


def check_automotive_cloud_setup(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: custom Vehicle__c / VehicleDefinition__c objects shadowing standard objects
    for obj_path in _custom_objects(manifest_dir):
        name = obj_path.stem.split(".")[0].lower()
        if name in {"vehicle__c", "vehicledefinition__c", "appraisal__c", "warrantyterm__c", "fleet__c"}:
            standard = name.replace("__c", "").replace("_", "")
            issues.append(
                f"{obj_path}: Custom object '{name}' shadows the Automotive Cloud standard "
                f"object '{standard}'. Audit Object Manager for the standard object before building "
                "custom equivalents."
            )

    # Check 2: misplaced fields on VehicleDefinition / Vehicle
    for field_path in _custom_fields(manifest_dir):
        parent = field_path.parent.name.lower()
        if parent not in {"vehicledefinition", "vehicle"}:
            continue
        try:
            tree = ET.parse(field_path)
        except ET.ParseError:
            continue
        root = tree.getroot()
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        full_name_el = root.find("sf:fullName", ns) or root.find("fullName")
        if full_name_el is None or not full_name_el.text:
            continue
        field_lower = full_name_el.text.lower()
        if parent == "vehicledefinition":
            for hint in PER_VIN_FIELD_HINTS:
                if hint in field_lower:
                    issues.append(
                        f"{field_path}: Field '{full_name_el.text}' on VehicleDefinition looks like "
                        "per-VIN state — belongs on Vehicle, not the model template."
                    )
                    break
        elif parent == "vehicle":
            for hint in BUILD_SPEC_FIELD_HINTS:
                if hint in field_lower:
                    issues.append(
                        f"{field_path}: Field '{full_name_el.text}' on Vehicle looks like a build "
                        "spec — belongs on VehicleDefinition, not the per-VIN record."
                    )
                    break

    # Check 3: Apex / Flow filtering Account.ParentId for dealer-OEM hierarchy
    parent_re = re.compile(r"Account.*ParentId\s*=", re.IGNORECASE)
    direct_dml_re = re.compile(
        r"\bupdate\s+\w+\s*;.*ActionableEventOrchestration", re.IGNORECASE | re.DOTALL
    )
    aeo_status_re = re.compile(r"ActionableEventOrchestration[^;]*\.Status\s*=", re.IGNORECASE)

    for code_path in _apex_classes(manifest_dir):
        try:
            text = code_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Dealer" in text and parent_re.search(text):
            issues.append(
                f"{code_path}: Filters Account.ParentId in dealer context — multi-franchise "
                "dealers require AccountAccountRelation, not single-valued ParentId."
            )
        if aeo_status_re.search(text) and "update " in text.lower():
            issues.append(
                f"{code_path}: Direct assignment to ActionableEventOrchestration.Status detected. "
                "Drive state through orchestration invocable actions, not DML."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_automotive_cloud_setup(manifest_dir)

    if not issues:
        print("No Automotive Cloud anti-patterns detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
