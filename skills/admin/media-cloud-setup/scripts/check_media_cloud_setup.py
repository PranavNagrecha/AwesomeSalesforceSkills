#!/usr/bin/env python3
"""Checker script for Media Cloud Setup skill.

Scans metadata for Media Cloud anti-patterns:
- High-volume impression-log custom objects inside Salesforce
- Hand-rolled revenue recognition Apex
- Separate per-media-type Placement objects instead of record types

Usage:
    python3 check_media_cloud_setup.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


IMPRESSION_OBJECT_PAT = re.compile(r"(?i)^(impression|ad_?event|log_?event).*__c$")
REVREC_CLASS_PAT = re.compile(r"(?i)(revrec|recognize_?revenue|monthly_?revenue|revenue_?schedule)")
PLACEMENT_OBJECT_PAT = re.compile(r"(?i)^(digital|linear|print|ooh|streaming)_?placement__c$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Media Cloud configuration for common issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_impression_objects(root: Path) -> list[str]:
    issues: list[str] = []
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return issues
    for child in objects_dir.iterdir():
        if not child.is_dir():
            continue
        if IMPRESSION_OBJECT_PAT.match(child.name):
            issues.append(
                f"Object {child.name} may store raw ad impressions inside Salesforce; aggregate upstream and load rollups"
            )
    return issues


def check_handrolled_revrec(root: Path) -> list[str]:
    issues: list[str] = []
    classes_dir = root / "classes"
    if not classes_dir.exists():
        return issues
    for path in classes_dir.rglob("*.cls"):
        if REVREC_CLASS_PAT.search(path.stem):
            issues.append(
                f"{path.relative_to(root)}: looks like hand-rolled revenue recognition; prefer Media Cloud Revenue Management"
            )
    return issues


def check_per_type_placement_objects(root: Path) -> list[str]:
    issues: list[str] = []
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return issues
    matches = []
    for child in objects_dir.iterdir():
        if child.is_dir() and PLACEMENT_OBJECT_PAT.match(child.name):
            matches.append(child.name)
    if len(matches) >= 2:
        issues.append(
            f"Multiple per-media-type Placement objects found: {', '.join(matches)}; use one Placement with record types"
        )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_impression_objects(manifest_dir))
    issues.extend(check_handrolled_revrec(manifest_dir))
    issues.extend(check_per_type_placement_objects(manifest_dir))

    if not issues:
        print("No Media Cloud anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
