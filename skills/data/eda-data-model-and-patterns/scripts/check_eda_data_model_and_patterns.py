#!/usr/bin/env python3
"""Checker script for EDA Data Model and Patterns skill.

Scans metadata for EDA modeling anti-patterns:
- Shadow Student__c / Faculty__c / Guardian__c objects
- Guardian_* / Parent_* fields on Contact
- Apex/Flow with hard-coded Term__c IDs
- Course_Connection__c with only one record type

Usage:
    python3 check_eda_data_model_and_patterns.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SHADOW_OBJECTS = {"Student__c", "Faculty__c", "Guardian__c", "Alumnus__c", "Enrollment__c"}
GUARDIAN_FIELD_PAT = re.compile(r"^(Guardian|Parent)_.*__c\.field-meta\.xml$")
HARDCODED_ID_PAT = re.compile(r"['\"]001\w{12,15}['\"]|['\"]a0\w{13,15}['\"]")
TERM_REF_PAT = re.compile(r"Term__c")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check EDA data-model hygiene.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_shadow_objects(root: Path) -> list[str]:
    issues: list[str] = []
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return issues
    for obj in SHADOW_OBJECTS:
        if (objects_dir / obj).exists():
            issues.append(f"objects/{obj}: shadow EDA object; use Contact + Affiliation__c instead")
    return issues


def check_guardian_fields(root: Path) -> list[str]:
    issues: list[str] = []
    contact_dir = root / "objects" / "Contact" / "fields"
    if not contact_dir.exists():
        return issues
    for field in contact_dir.glob("*.field-meta.xml"):
        if GUARDIAN_FIELD_PAT.match(field.name):
            issues.append(
                f"{field.relative_to(root)}: Guardian/Parent field on Contact; use Relationship__c"
            )
    return issues


def check_hardcoded_terms(root: Path) -> list[str]:
    issues: list[str] = []
    for sub in ("classes", "triggers", "flows"):
        d = root / sub
        if not d.exists():
            continue
        ext = "*.cls" if sub != "flows" else "*.flow-meta.xml"
        for path in d.rglob(ext):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if TERM_REF_PAT.search(text) and HARDCODED_ID_PAT.search(text):
                issues.append(
                    f"{path.relative_to(root)}: hard-coded Salesforce ID near Term__c reference"
                )
    return issues


def check_course_connection_record_types(root: Path) -> list[str]:
    issues: list[str] = []
    cc_dir = root / "objects" / "hed__Course_Enrollment__c" / "recordTypes"
    alt = root / "objects" / "Course_Connection__c" / "recordTypes"
    for candidate in (cc_dir, alt):
        if candidate.exists():
            record_types = list(candidate.glob("*.recordType-meta.xml"))
            if len(record_types) <= 1:
                issues.append(
                    f"{candidate.relative_to(root)}: Course_Connection with ≤1 record type; differentiate Student vs Faculty"
                )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_shadow_objects(manifest_dir))
    issues.extend(check_guardian_fields(manifest_dir))
    issues.extend(check_hardcoded_terms(manifest_dir))
    issues.extend(check_course_connection_record_types(manifest_dir))

    if not issues:
        print("No EDA data-model issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
