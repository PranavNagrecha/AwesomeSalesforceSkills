#!/usr/bin/env python3
"""Checker script for Nonprofit Cloud vs NPSP Migration skill.

Scans a repo for migration-hygiene issues:
- Data-loader configs touching NPSP Opportunity without disabling triggers
- Both NPSP and Nonprofit Cloud objects present with no domain boundary docs
- Migration scripts that copy NPSP fields directly without a mapping doc

Usage:
    python3 check_nonprofit_cloud_vs_npsp_migration.py [--manifest-dir path/to/metadata] [--docs-dir path/to/docs]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


NPSP_OBJECT_HINTS = ("npsp__", "npo02__", "npe01__", "npe03__", "npe4__", "npe5__")
NONPROFIT_CLOUD_OBJECT_HINTS = ("Gift__c", "GiftCommitment", "ProgramEngagement", "PersonEducation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check nonprofit migration hygiene.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    parser.add_argument("--docs-dir", default="docs", help="Directory with migration docs.")
    return parser.parse_args()


def detect_npsp_usage(root: Path) -> bool:
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return False
    for obj_dir in objects_dir.iterdir():
        if obj_dir.is_dir() and any(obj_dir.name.startswith(h) for h in NPSP_OBJECT_HINTS):
            return True
    return False


def detect_nonprofit_cloud_usage(root: Path) -> bool:
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return False
    for obj_dir in objects_dir.iterdir():
        if obj_dir.is_dir() and any(hint in obj_dir.name for hint in NONPROFIT_CLOUD_OBJECT_HINTS):
            return True
    return False


def check_boundary_doc(docs_dir: Path) -> bool:
    if not docs_dir.exists():
        return False
    for path in docs_dir.rglob("*.md"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if "npsp" in text and "nonprofit cloud" in text and "boundary" in text:
            return True
    return False


def check_loader_triggers(root: Path) -> list[str]:
    issues: list[str] = []
    for pattern in ("*.sdl", "process-conf.xml", "*.yaml", "*.yml"):
        for path in root.rglob(pattern):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if re.search(r"(?i)(npsp__|Opportunity).*insert", text) and "Trigger_Handler" not in text:
                issues.append(
                    f"{path}: loader config touches NPSP Opportunity but no mention of Trigger_Handler gating"
                )
    return issues


def check_migration_script_mapping(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("migrate*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(hint in text for hint in NPSP_OBJECT_HINTS) and "mapping" not in text.lower():
            issues.append(
                f"{path}: migration script references NPSP objects with no mapping doc reference"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    docs_dir = Path(args.docs_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    has_npsp = detect_npsp_usage(manifest_dir)
    has_nc = detect_nonprofit_cloud_usage(manifest_dir)
    if has_npsp and has_nc and not check_boundary_doc(docs_dir):
        issues.append(
            "both NPSP and Nonprofit Cloud objects present but no boundary doc found in docs/"
        )
    issues.extend(check_loader_triggers(manifest_dir))
    issues.extend(check_migration_script_mapping(manifest_dir))

    if not issues:
        print("No nonprofit migration hygiene issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
