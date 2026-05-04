#!/usr/bin/env python3
"""Checker script for Net Zero Cloud Setup skill.

Scans force-app/ metadata for common Net Zero Cloud anti-patterns:

- Custom Carbon_Footprint__c / Emission_Factor__c objects (suggest standard NZC objects)
- Apex triggers on …EnrgyUse / Scope3PcmtItem that perform calculation (move to DPE)
- Direct DML against …CrbnFtprnt calculated rows
- Disclosure-pack metadata referencing multiple frameworks

Stdlib only.

Usage:
    python3 check_net_zero_cloud_setup.py [--manifest-dir force-app]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SHADOW_OBJECTS = {
    "carbon_footprint__c": "StnryAssetCrbnFtprnt / Scope3CrbnFtprnt",
    "emission_factor__c": "EmssnFctr",
    "emission_factor_set__c": "EmssnFctrSet",
    "scope_3__c": "Scope3CrbnFtprnt",
    "ghg_inventory__c": "StnryAssetCrbnFtprnt + Scope3CrbnFtprnt",
}

CRBN_FTPRNT_OBJECTS = (
    "StnryAssetCrbnFtprnt",
    "VehicleAssetCrbnFtprnt",
    "Scope3CrbnFtprnt",
    "StnryAssetCrbnFtprntItm",
)

CALCULATION_TRIGGER_TARGETS = (
    "StnryAssetEnrgyUse",
    "Scope3PcmtItem",
    "VehicleAssetCrbnFtprnt",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Net Zero Cloud Setup metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _custom_objects(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.rglob("*.object-meta.xml")) + list(manifest_dir.rglob("*.object"))


def _apex_files(manifest_dir: Path) -> list[Path]:
    return list(manifest_dir.rglob("*.cls")) + list(manifest_dir.rglob("*.trigger"))


def check_net_zero_cloud_setup(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: shadow objects for standard NZC entities
    for obj_path in _custom_objects(manifest_dir):
        name = obj_path.stem.split(".")[0].lower()
        if name in SHADOW_OBJECTS:
            issues.append(
                f"{obj_path}: Custom object '{name}' shadows the Net Zero Cloud standard "
                f"object(s) '{SHADOW_OBJECTS[name]}'. Use standard NZC objects when license is active."
            )

    # Check 2: Apex triggers on activity-data objects performing calculation
    calc_keyword_re = re.compile(r"\b(calculate|compute|multiply)\b.*\bCO2", re.IGNORECASE | re.DOTALL)
    for code_path in _apex_files(manifest_dir):
        if code_path.suffix != ".trigger":
            continue
        try:
            text = code_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for target in CALCULATION_TRIGGER_TARGETS:
            if re.search(rf"\btrigger\s+\w+\s+on\s+{target}\b", text):
                if calc_keyword_re.search(text) or "TotalCO2" in text:
                    issues.append(
                        f"{code_path}: Apex trigger on {target} performs carbon calculation. "
                        "Move calculation logic to a DPE definition; triggers undermine the "
                        "auditable batch model."
                    )

    # Check 3: direct DML against …CrbnFtprnt rows
    update_re = re.compile(r"\bupdate\s+\w+\s*;", re.IGNORECASE)
    for code_path in _apex_files(manifest_dir):
        try:
            text = code_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for obj in CRBN_FTPRNT_OBJECTS:
            field_assign_re = re.compile(rf"{obj}[^;]*\.\w*CO2\w*\s*=", re.IGNORECASE)
            if field_assign_re.search(text) and update_re.search(text):
                issues.append(
                    f"{code_path}: Assigns to a calculated CO2 field on {obj} and performs "
                    "DML. The next DPE run will overwrite the manual edit; correct at "
                    "activity-data or factor layer instead."
                )
                break

    # Check 4: disclosure-pack metadata referencing multiple frameworks (heuristic)
    pack_files = list(manifest_dir.rglob("*disclosurePack*-meta.xml")) + list(
        manifest_dir.rglob("*DisclosurePack*-meta.xml")
    )
    framework_tokens = ("CSRD", "ESRS", "TCFD", "CDP", "SBTi")
    for pack_path in pack_files:
        try:
            text = pack_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hits = [t for t in framework_tokens if t in text]
        if len(hits) > 1:
            issues.append(
                f"{pack_path}: Disclosure pack references multiple frameworks ({', '.join(hits)}). "
                "Split into one pack per framework — aggregation rules differ."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_net_zero_cloud_setup(manifest_dir)

    if not issues:
        print("No Net Zero Cloud anti-patterns detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
