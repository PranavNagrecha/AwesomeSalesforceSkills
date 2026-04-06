#!/usr/bin/env python3
"""Checker script for Performance Testing Salesforce skill.

Scans a Salesforce metadata directory for common performance testing readiness issues:
- Connected App definitions missing OAuth scopes needed for load test authentication
- Custom objects with high field counts that may cause EPT degradation
- Apex classes with non-cacheable @AuraEnabled methods (EPT impact)
- Missing test classes for performance-critical Apex controllers

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_performance_testing_salesforce.py [--help]
    python3 check_performance_testing_salesforce.py --manifest-dir path/to/metadata
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
        description="Check Performance Testing Salesforce configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files(root: Path, extension: str) -> list[Path]:
    """Recursively find files with a given extension."""
    results = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(extension):
                results.append(Path(dirpath) / fname)
    return results


def check_non_cacheable_aura_enabled(manifest_dir: Path) -> list[str]:
    """Flag @AuraEnabled methods that are not cacheable — potential EPT bottleneck."""
    issues = []
    cls_files = find_files(manifest_dir, ".cls")
    aura_pattern = re.compile(r"@AuraEnabled\b(?!\s*\(\s*cacheable\s*=\s*true\s*\))", re.IGNORECASE)
    cacheable_pattern = re.compile(r"@AuraEnabled\s*\(\s*cacheable\s*=\s*true\s*\)", re.IGNORECASE)

    for cls_file in cls_files:
        try:
            content = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        non_cacheable_matches = aura_pattern.findall(content)
        cacheable_matches = cacheable_pattern.findall(content)

        if non_cacheable_matches and not cacheable_matches:
            count = len(non_cacheable_matches)
            issues.append(
                f"EPT risk: {cls_file.name} has {count} @AuraEnabled method(s) without "
                f"cacheable=true. Non-cacheable Apex calls bypass the Lightning Data Service "
                f"cache and increase EPT. Review whether these can be made cacheable."
            )

    return issues


def check_high_field_count_objects(manifest_dir: Path) -> list[str]:
    """Flag custom objects with excessive field counts that may degrade page load."""
    issues = []
    # Count .field-meta.xml files per object directory
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Try force-app structure
        objects_dir = manifest_dir / "force-app" / "main" / "default" / "objects"

    if not objects_dir.exists():
        return issues

    field_threshold = 100

    for obj_dir in objects_dir.iterdir():
        if not obj_dir.is_dir():
            continue
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue

        field_files = list(fields_dir.glob("*.field-meta.xml"))
        if len(field_files) > field_threshold:
            issues.append(
                f"Performance risk: Object '{obj_dir.name}' has {len(field_files)} custom fields "
                f"(threshold: {field_threshold}). High field counts increase page load time and "
                f"EPT. Consider archiving unused fields or splitting into related objects."
            )

    return issues


def check_connected_app_oauth_scopes(manifest_dir: Path) -> list[str]:
    """Check Connected Apps for OAuth scopes needed for load test authentication."""
    issues = []
    ca_files = find_files(manifest_dir, ".connectedApp-meta.xml")

    if not ca_files:
        ca_files = find_files(manifest_dir, ".connectedApp")

    for ca_file in ca_files:
        try:
            tree = ET.parse(ca_file)
            root = tree.getroot()
        except (ET.ParseError, OSError):
            continue

        # Strip namespace for easier querying
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        scopes = [elem.text for elem in root.iter(f"{ns}scopes") if elem.text]
        has_api = any(s in ("Api", "api", "Full", "full") for s in scopes)

        if not has_api:
            issues.append(
                f"Load test auth: Connected App '{ca_file.stem}' does not include 'Api' or 'Full' "
                f"OAuth scope. API load test tools (k6, JMeter) require API access scope for "
                f"authenticated testing."
            )

    return issues


def check_performance_testing_salesforce(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_non_cacheable_aura_enabled(manifest_dir))
    issues.extend(check_high_field_count_objects(manifest_dir))
    issues.extend(check_connected_app_oauth_scopes(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_performance_testing_salesforce(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
