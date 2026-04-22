#!/usr/bin/env python3
"""Checker script for Consumer Goods Cloud Setup skill.

Scans a Salesforce metadata manifest for CG Cloud anti-patterns:
- Flows named like manual visit generators (should use RoutePlan)
- External vision-API callouts instead of Salesforce Image Recognition
- Account metadata with flat retail hierarchy fields but no ParentId usage

Usage:
    python3 check_consumer_goods_cloud_setup.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


VISIT_GEN_NAME_PAT = re.compile(r"(?i)(generate|create|weekly)_?visit")
EXTERNAL_VISION_PAT = re.compile(
    r"(?i)(rekognition\.amazonaws\.com|vision\.googleapis\.com|api\.cognitive\.microsoft\.com/vision)"
)
RETAILER_FIELD_PAT = re.compile(r"(?i)<fullName>(retailer_?name|banner_?name)__c</fullName>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check CG Cloud configuration for common issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_manual_visit_generators(root: Path) -> list[str]:
    issues: list[str] = []
    for sub in ("flows", "classes"):
        base = root / sub
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and VISIT_GEN_NAME_PAT.search(path.stem):
                issues.append(
                    f"{path.relative_to(root)}: looks like a manual Visit generator; prefer RoutePlan regeneration"
                )
    return issues


def check_external_vision(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.xml"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if EXTERNAL_VISION_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: external vision API referenced; prefer Salesforce Image Recognition"
            )
    return issues


def check_flat_retailer_fields(root: Path) -> list[str]:
    issues: list[str] = []
    account_dir = root / "objects" / "Account"
    if not account_dir.exists():
        return issues
    for field in account_dir.rglob("*.field-meta.xml"):
        try:
            text = field.read_text(encoding="utf-8")
        except OSError:
            continue
        if RETAILER_FIELD_PAT.search(text):
            issues.append(
                f"{field.relative_to(root)}: flat retailer/banner field on Account; prefer Account hierarchy via ParentId"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_manual_visit_generators(manifest_dir))
    issues.extend(check_external_vision(manifest_dir))
    issues.extend(check_flat_retailer_fields(manifest_dir))

    if not issues:
        print("No CG Cloud anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
