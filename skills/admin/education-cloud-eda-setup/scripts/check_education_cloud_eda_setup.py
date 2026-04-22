#!/usr/bin/env python3
"""Checker script for Education Cloud EDA Setup skill.

Scans a Salesforce metadata manifest for EDA anti-patterns:
- Shadow custom objects like Student__c / Applicant__c
- Grade fields on Course_Offering__c instead of Course_Connection__c
- Scheduled Apex that deletes Course_Connection__c records

Usage:
    python3 check_education_cloud_eda_setup.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SHADOW_OBJECTS = {"Student__c", "Applicant__c", "Pupil__c", "Learner__c"}

GRADE_FIELD_PAT = re.compile(
    r"(?i)<fullName>(grade|final_?grade|mark|score)__c</fullName>"
)

DELETE_CC_PAT = re.compile(
    r"(?i)delete\s+.*Course_Connection__c|DML\s*delete\s+.*Course_Connection__c"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check EDA configuration for common issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_shadow_objects(root: Path) -> list[str]:
    issues: list[str] = []
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return issues
    for child in objects_dir.iterdir():
        if child.is_dir() and child.name in SHADOW_OBJECTS:
            issues.append(
                f"Custom object {child.name} shadows EDA contact-centric model; use Contact + Affiliation instead"
            )
    return issues


def check_grade_on_offering(root: Path) -> list[str]:
    issues: list[str] = []
    offering_dir = root / "objects" / "Course_Offering__c"
    if not offering_dir.exists():
        return issues
    for field_file in offering_dir.rglob("*.field-meta.xml"):
        try:
            text = field_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if GRADE_FIELD_PAT.search(text):
            issues.append(
                f"{field_file.relative_to(root)}: grade/mark field on Course_Offering__c; grades belong on Course_Connection__c"
            )
    return issues


def check_course_connection_deletes(root: Path) -> list[str]:
    issues: list[str] = []
    for sub in ("classes", "triggers", "flows"):
        base = root / sub
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if DELETE_CC_PAT.search(text):
                issues.append(
                    f"{path.relative_to(root)}: deletes Course_Connection__c; enrollment history must be preserved"
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
    issues.extend(check_grade_on_offering(manifest_dir))
    issues.extend(check_course_connection_deletes(manifest_dir))

    if not issues:
        print("No EDA anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
