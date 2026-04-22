#!/usr/bin/env python3
"""Checker script for Industries Public Sector Setup skill.

Scans a Salesforce metadata manifest for PSS anti-patterns:
- Custom objects that shadow shipped PSS objects
- Flow/Apex classes whose names look like hand-rolled eligibility
- OWDs set to Public Read/Write on PSS-sensitive objects

Usage:
    python3 check_industries_public_sector_setup.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PSS_SHIPPED_OBJECTS = {
    "LicenseApplication",
    "BenefitDisbursement",
    "IndividualApplication",
    "RegulatoryCode",
    "BusinessLicense",
    "Authorization",
}

ELIGIBILITY_NAME_PAT = re.compile(
    r"(?i)(evaluate_?eligibility|benefit_?qualification|eligibility_?check|qualify_?applicant)"
)

SENSITIVE_OWD_OBJECTS = {
    "Case",
    "LicenseApplication",
    "BenefitDisbursement",
    "IndividualApplication",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check PSS configuration for common issues.")
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_shadow_custom_objects(root: Path) -> list[str]:
    issues: list[str] = []
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return issues
    for child in objects_dir.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if not name.endswith("__c"):
            continue
        base = name[:-3].replace("_", "")
        for shipped in PSS_SHIPPED_OBJECTS:
            if base.lower() == shipped.lower():
                issues.append(
                    f"Custom object {name} shadows shipped PSS object {shipped}; extend the shipped object instead"
                )
    return issues


def check_hardcoded_eligibility(root: Path) -> list[str]:
    issues: list[str] = []
    for pattern in ("classes", "flows"):
        sub = root / pattern
        if not sub.exists():
            continue
        for path in sub.rglob("*"):
            if not path.is_file():
                continue
            if ELIGIBILITY_NAME_PAT.search(path.stem):
                issues.append(
                    f"{path.relative_to(root)} looks like hand-rolled eligibility; prefer Business Rules Engine expression sets"
                )
    return issues


def check_owd_public_on_sensitive(root: Path) -> list[str]:
    issues: list[str] = []
    sharing_settings = root / "settings" / "Sharing.settings-meta.xml"
    if not sharing_settings.exists():
        return issues
    try:
        text = sharing_settings.read_text(encoding="utf-8")
    except OSError:
        return issues
    for obj in SENSITIVE_OWD_OBJECTS:
        if re.search(rf"<object>{obj}</object>\s*<defaultExternalAccess>Read(Write)?</defaultExternalAccess>", text):
            issues.append(f"OWD external access for {obj} is Public; PSS expects Private with criteria-based sharing")
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_shadow_custom_objects(manifest_dir))
    issues.extend(check_hardcoded_eligibility(manifest_dir))
    issues.extend(check_owd_public_on_sensitive(manifest_dir))

    if not issues:
        print("No PSS anti-patterns detected.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
