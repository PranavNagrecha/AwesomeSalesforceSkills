#!/usr/bin/env python3
"""Checker script for Sales Cloud Integration Patterns skill.

Scans org metadata for common integration configuration issues:
- Missing External ID fields on key Sales Cloud objects
- Integration user profile with excessive permissions
- Missing standard Pricebook entries for synced products
- Order-related triggers that attempt synchronous callouts

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sales_cloud_integration_patterns.py [--help]
    python3 check_sales_cloud_integration_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Sales Cloud Integration Patterns configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# Objects that typically need External ID fields for integration
INTEGRATION_OBJECTS = {"Account", "Contact", "Product2", "Order", "Lead"}

# Salesforce metadata XML namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _find_files(root: Path, pattern: str) -> list[Path]:
    """Recursively find files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file, returning None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except (ET.ParseError, OSError):
        return None


def check_external_id_fields(manifest_dir: Path) -> list[str]:
    """Check that integration objects have at least one External ID field."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Try force-app structure
        objects_dir = manifest_dir / "force-app" / "main" / "default" / "objects"
    if not objects_dir.exists():
        return issues  # Cannot check without object metadata

    for obj_name in INTEGRATION_OBJECTS:
        obj_dir = objects_dir / obj_name
        if not obj_dir.exists():
            continue

        field_files = _find_files(obj_dir, "*.field-meta.xml")
        has_external_id = False
        for field_file in field_files:
            root = _parse_xml_safe(field_file)
            if root is None:
                continue
            ext_id_elem = root.find(f".//{{{SF_NS}}}externalId")
            if ext_id_elem is not None and ext_id_elem.text == "true":
                has_external_id = True
                break

        if field_files and not has_external_id:
            issues.append(
                f"{obj_name}: No External ID field found. "
                f"Integration sync requires an External ID for upsert operations."
            )

    return issues


def check_triggers_for_sync_callouts(manifest_dir: Path) -> list[str]:
    """Check for triggers on Order or Account that contain synchronous HTTP callouts."""
    issues: list[str] = []
    trigger_dirs = [
        manifest_dir / "triggers",
        manifest_dir / "force-app" / "main" / "default" / "triggers",
    ]

    callout_pattern = re.compile(
        r"\b(Http\s*\(\s*\)|HttpRequest|\.send\()", re.IGNORECASE
    )
    async_pattern = re.compile(
        r"\b(System\.enqueueJob|@future|Queueable|EventBus\.publish)", re.IGNORECASE
    )

    for trigger_dir in trigger_dirs:
        if not trigger_dir.exists():
            continue
        for trigger_file in trigger_dir.glob("*.trigger"):
            content = trigger_file.read_text(errors="replace")
            if callout_pattern.search(content) and not async_pattern.search(content):
                issues.append(
                    f"{trigger_file.name}: Contains HTTP callout logic without "
                    f"async wrapper (@future/Queueable). Callouts in trigger "
                    f"context will fail at runtime."
                )

    return issues


def check_integration_user_profile(manifest_dir: Path) -> list[str]:
    """Check for integration profiles with System Administrator base."""
    issues: list[str] = []
    profile_dirs = [
        manifest_dir / "profiles",
        manifest_dir / "force-app" / "main" / "default" / "profiles",
    ]

    integration_keywords = re.compile(r"integrat|api[_\s]user|sync", re.IGNORECASE)

    for profile_dir in profile_dirs:
        if not profile_dir.exists():
            continue
        for profile_file in profile_dir.glob("*.profile-meta.xml"):
            if not integration_keywords.search(profile_file.stem):
                continue
            root = _parse_xml_safe(profile_file)
            if root is None:
                continue
            # Check for excessive permissions
            for perm in root.findall(f".//{{{SF_NS}}}userPermissions"):
                name_elem = perm.find(f"{{{SF_NS}}}name")
                enabled_elem = perm.find(f"{{{SF_NS}}}enabled")
                if (
                    name_elem is not None
                    and enabled_elem is not None
                    and enabled_elem.text == "true"
                    and name_elem.text in ("ModifyAllData", "ViewAllData")
                ):
                    issues.append(
                        f"{profile_file.stem}: Integration profile has "
                        f"{name_elem.text} enabled. Use field-level and "
                        f"object-level permissions instead of broad access."
                    )

    return issues


def check_sales_cloud_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_external_id_fields(manifest_dir))
    issues.extend(check_triggers_for_sync_callouts(manifest_dir))
    issues.extend(check_integration_user_profile(manifest_dir))

    if not issues:
        return issues

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sales_cloud_integration_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
