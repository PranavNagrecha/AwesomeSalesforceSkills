#!/usr/bin/env python3
"""Checker script for Cross-Cloud Data Deployment skill.

Scans metadata for cross-cloud hygiene issues:
- Cross-cloud key fields without External ID + Unique
- Scheduled Apex jobs polling LastModifiedDate to post to another cloud
- Lightning components reading Data Cloud on record-page load

Usage:
    python3 check_cross_cloud_data_deployment.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CROSS_CLOUD_KEY_PAT = re.compile(r"(Global_|External_|Shared_|Unified_).*_Id__c$")
POLLING_SYNC_PAT = re.compile(
    r"(?is)LastModifiedDate\s*(>=|>)\s*.{0,200}?(HttpRequest|callout|MarketingCloud|Data Cloud)"
)
DATA_CLOUD_ON_LOAD_PAT = re.compile(
    r"(?i)@wire\s*\(\s*(getDataCloudProfile|getUnifiedProfile|getDataCloudEntity)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check cross-cloud data deployment hygiene.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def iter_fields(root: Path):
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return
    for obj_dir in objects_dir.iterdir():
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue
        for field in fields_dir.glob("*.field-meta.xml"):
            yield field


def check_cross_cloud_keys(root: Path) -> list[str]:
    issues: list[str] = []
    for field in iter_fields(root):
        api_name = field.name.replace(".field-meta.xml", "")
        if not CROSS_CLOUD_KEY_PAT.search(api_name):
            continue
        try:
            text = field.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        has_external_id = re.search(r"<externalId>true</externalId>", text)
        has_unique = re.search(r"<unique>true</unique>", text)
        if not (has_external_id and has_unique):
            issues.append(
                f"{field.relative_to(root)}: cross-cloud key without External ID + Unique"
            )
    return issues


def check_polling_sync(root: Path) -> list[str]:
    issues: list[str] = []
    classes_dir = root / "classes"
    if not classes_dir.exists():
        return issues
    for path in classes_dir.rglob("*.cls"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if POLLING_SYNC_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: LastModifiedDate polling + callout; prefer CDC or Platform Events"
            )
    return issues


def check_data_cloud_on_load(root: Path) -> list[str]:
    issues: list[str] = []
    lwc_dir = root / "lwc"
    if not lwc_dir.exists():
        return issues
    for path in lwc_dir.rglob("*.js"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if DATA_CLOUD_ON_LOAD_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: Data Cloud read on record-page load; expect latency"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_cross_cloud_keys(manifest_dir))
    issues.extend(check_polling_sync(manifest_dir))
    issues.extend(check_data_cloud_on_load(manifest_dir))

    if not issues:
        print("No cross-cloud data deployment issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
