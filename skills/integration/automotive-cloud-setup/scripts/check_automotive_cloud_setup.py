#!/usr/bin/env python3
"""Checker script for Automotive Cloud Setup skill.

Scans force-app/ style metadata for patterns the skill warns about. Every rule is
a heuristic from SKILL.md; the object/field premises are UNVERIFIED (2026-10-20,
the corpus has no Automotive Cloud Developer Guide), so every heuristic finding is
a WARN to review; a field file that does not parse is an ERROR (exit 1):

- custom Vehicle__c / VehicleDefinition__c / Appraisal__c / Fleet__c objects
- per-VIN state fields on VehicleDefinition, build-spec fields on Vehicle
  (field files live in objects/<Object>/fields/<Field>.field-meta.xml)
- Apex that filters dealer Accounts by ParentId
- Apex that assigns ActionableEventOrchestration.Status and updates it

Exit codes: a missing directory is an ERROR (exit 1); WARN findings exit 0 unless
--strict; a directory with no metadata or code files prints one WARN and exits 0.
Stdlib only.

Usage:
    python3 check_automotive_cloud_setup.py [--manifest-dir force-app] [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PER_VIN_TOKENS = {"mileage", "currentowner", "lastservice", "registration", "odometer", "vin"}
BUILD_SPEC_TOKENS = {"msrp", "trim", "bodystyle", "fueltype", "drivetrain", "horsepower", "modelyear"}
SHADOWED = {"vehicle__c", "vehicledefinition__c", "appraisal__c", "fleet__c"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Automotive Cloud Setup metadata for common issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata (default: .).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return parser.parse_args()


def tokens(name: str) -> set[str]:
    """Lower-cased word tokens of an API name: 'Current_Owner__c' -> {current, owner, currentowner}."""
    base = re.sub(r"__c$", "", name)
    words = [w.lower() for w in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", base.replace("_", " "))]
    joined = {"".join(words[i:i + 2]) for i in range(len(words) - 1)}
    return set(words) | joined | {"".join(words)}


def full_name(root: ET.Element) -> str:
    for child in root:
        if child.tag.rsplit("}", 1)[-1] == "fullName" and child.text:
            return child.text.strip()
    return ""


def scan(manifest_dir: Path) -> tuple[int, list[str], list[str]]:
    issues: list[str] = []
    errors: list[str] = []
    seen = 0
    for obj in sorted(manifest_dir.rglob("*.object-meta.xml")) + sorted(manifest_dir.rglob("*.object")):
        seen += 1
        name = obj.name.split(".")[0].lower()
        if name in SHADOWED:
            issues.append(f"{obj}: custom object '{name}' may shadow an Automotive Cloud standard object; audit Object Manager first (premise UNVERIFIED).")
    for field in sorted(manifest_dir.rglob("*.field-meta.xml")):
        seen += 1
        owner = field.parent.parent.name.lower() if field.parent.name == "fields" else field.parent.name.lower()
        if owner not in {"vehicledefinition", "vehicle"}:
            continue
        try:
            fname = full_name(ET.parse(field).getroot()) or field.name.split(".")[0]
        except ET.ParseError:
            errors.append(f"{field}: field metadata does not parse")
            continue
        hints = PER_VIN_TOKENS if owner == "vehicledefinition" else BUILD_SPEC_TOKENS
        hit = sorted(tokens(fname) & hints)
        if hit:
            where = "per-VIN state belongs on Vehicle" if owner == "vehicledefinition" else "a build spec belongs on VehicleDefinition"
            issues.append(f"{field}: field '{fname}' on {owner} looks misplaced ({hit[0]}); {where} (premise UNVERIFIED).")
    parent_re = re.compile(r"Account.*ParentId\s*=", re.IGNORECASE)
    aeo_status_re = re.compile(r"ActionableEventOrchestration[^;]*\.Status\s*=", re.IGNORECASE)
    for code in sorted(manifest_dir.rglob("*.cls")) + sorted(manifest_dir.rglob("*.trigger")):
        seen += 1
        text = code.read_text(encoding="utf-8", errors="ignore")
        if "Dealer" in text and parent_re.search(text):
            issues.append(f"{code}: filters Account.ParentId in a dealer context; multi-franchise dealers need AccountAccountRelation (premise UNVERIFIED).")
        if aeo_status_re.search(text) and "update " in text.lower():
            issues.append(f"{code}: assigns ActionableEventOrchestration.Status and updates it; the skill says to use orchestration actions (premise UNVERIFIED).")
    return seen, issues, errors


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)
    seen, issues, errors = scan(manifest_dir)
    for err in errors:
        print(f"ERROR: {err}")
    if not seen:
        print(f"WARN: no object, field, Apex class or trigger files under {manifest_dir}; nothing to check")
        return 0
    if not issues and not errors:
        print("No Automotive Cloud anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}")
    return 1 if errors or (args.strict and issues) else 0


if __name__ == "__main__":
    sys.exit(main())
