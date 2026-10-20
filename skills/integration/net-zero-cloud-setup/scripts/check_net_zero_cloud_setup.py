#!/usr/bin/env python3
"""Checker script for Net Zero Cloud Setup skill.

Scans force-app/ style metadata and scratch org definition files. Every heuristic
finding is a WARN to review (the corpus has no Net Zero Cloud Developer Guide, so
the object-level premises are UNVERIFIED, 2026-10-20); a scratch-def.json that
does not parse is an ERROR (exit 1):

- custom Carbon_Footprint__c / Emission_Factor__c style objects
- Apex triggers on activity-data objects that do carbon calculation
- Apex that assigns a calculated CO2 field on a ...CrbnFtprnt object and updates
- a scratch org definition with industriesSettings.enableSCCarbonAccounting true
  but without enableSustainabilityCloud, or without a SustainabilityApp /
  SustainabilityCloud feature (the documented example sets both: sfdx 264
  L9206-9218; IndustriesSettings flags: meta 264 L123200-123272)

A disclosure-pack rule was removed: no "disclosure pack" metadata type exists
in the corpus (the grounded feature is the Disclosure and Compliance Hub flag
enableGnrcDisclsFrmwrk, meta 264 L123160-123163).

Exit codes: a missing directory is an ERROR (exit 1); WARN findings exit 0 unless
--strict; a directory with nothing to scan prints one WARN and exits 0.
Stdlib only.

Usage:
    python3 check_net_zero_cloud_setup.py [--manifest-dir force-app] [--strict]
"""

from __future__ import annotations

import argparse
import json
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
CRBN_FTPRNT_OBJECTS = ("StnryAssetCrbnFtprnt", "VehicleAssetCrbnFtprnt", "Scope3CrbnFtprnt", "StnryAssetCrbnFtprntItm")
CALCULATION_TRIGGER_TARGETS = ("StnryAssetEnrgyUse", "Scope3PcmtItem", "VehicleAssetCrbnFtprnt")
NZC_FEATURES = {"SustainabilityApp", "SustainabilityCloud"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Net Zero Cloud Setup metadata for common issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata (default: .).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return parser.parse_args()


def check_scratch_def(path: Path, errors: list[str]) -> list[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: scratch org definition does not parse ({exc})")
        return []
    if not isinstance(data, dict):
        return []
    ind = (data.get("settings") or {}).get("industriesSettings") or {}
    if not isinstance(ind, dict) or not ind.get("enableSCCarbonAccounting"):
        return []
    out = []
    if not ind.get("enableSustainabilityCloud"):
        out.append(f"{path}: enableSCCarbonAccounting is on but enableSustainabilityCloud is not; the documented example sets both")
    if not NZC_FEATURES & set(data.get("features") or []):
        out.append(f"{path}: no SustainabilityApp or SustainabilityCloud scratch org feature; the permission set licenses come from it")
    return out


def scan(manifest_dir: Path, errors: list[str]) -> tuple[int, list[str]]:
    issues: list[str] = []
    seen = 0
    for obj in sorted(manifest_dir.rglob("*.object-meta.xml")) + sorted(manifest_dir.rglob("*.object")):
        seen += 1
        name = obj.name.split(".")[0].lower()
        if name in SHADOW_OBJECTS:
            issues.append(f"{obj}: custom object '{name}' may shadow Net Zero Cloud '{SHADOW_OBJECTS[name]}'; use the standard objects when licensed (premise UNVERIFIED)")
    calc_re = re.compile(r"\b(calculate|compute|multiply)\b.*\bCO2", re.IGNORECASE | re.DOTALL)
    for code in sorted(manifest_dir.rglob("*.trigger")):
        seen += 1
        text = code.read_text(encoding="utf-8", errors="ignore")
        for target in CALCULATION_TRIGGER_TARGETS:
            if re.search(rf"\btrigger\s+\w+\s+on\s+{target}\b", text) and (calc_re.search(text) or "TotalCO2" in text):
                issues.append(f"{code}: Apex trigger on {target} performs carbon calculation; the skill says to use a DPE definition (premise UNVERIFIED)")
    update_re = re.compile(r"\bupdate\s+\w+\s*;", re.IGNORECASE)
    for code in sorted(manifest_dir.rglob("*.cls")) + sorted(manifest_dir.rglob("*.trigger")):
        seen += 1
        text = code.read_text(encoding="utf-8", errors="ignore")
        for obj in CRBN_FTPRNT_OBJECTS:
            if re.search(rf"{obj}[^;]*\.\w*CO2\w*\s*=", text, re.IGNORECASE) and update_re.search(text):
                issues.append(f"{code}: assigns a calculated CO2 field on {obj} and runs DML; correct at the activity-data or factor layer instead (premise UNVERIFIED)")
                break
    for sd in sorted(manifest_dir.rglob("*scratch-def.json")):
        seen += 1
        issues.extend(check_scratch_def(sd, errors))
    return seen, issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)
    errors: list[str] = []
    seen, issues = scan(manifest_dir, errors)
    for err in errors:
        print(f"ERROR: {err}")
    if not seen:
        print(f"WARN: no object, Apex or scratch-org definition files under {manifest_dir}; nothing to check")
        return 0
    if not issues and not errors:
        print("No Net Zero Cloud anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}")
    return 1 if errors or (args.strict and issues) else 0


if __name__ == "__main__":
    sys.exit(main())
