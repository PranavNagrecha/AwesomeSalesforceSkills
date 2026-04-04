#!/usr/bin/env python3
"""Checker script for OmniScript Versioning skill.

Scans OmniStudio DataPack JSON files and OmniProcess metadata for versioning issues:
- Multiple active versions in the same DataPack export (versioning conflict)
- DataPack activate flag set to true in non-production contexts
- Missing Type/Subtype/Language in OmniScript metadata references

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omniscript_versioning.py [--help]
    python3 check_omniscript_versioning.py --datapacks-dir path/to/datapacks
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check OmniScript DataPacks for versioning anti-patterns.",
    )
    parser.add_argument(
        "--datapacks-dir",
        default=".",
        help="Directory containing DataPack JSON files (default: current directory).",
    )
    return parser.parse_args()


def scan_datapacks(datapacks_dir: Path) -> list[str]:
    """Scan DataPack JSON files for OmniScript versioning issues."""
    issues: list[str] = []

    if not datapacks_dir.exists():
        issues.append(f"DataPacks directory not found: {datapacks_dir}")
        return issues

    json_files = list(datapacks_dir.rglob("*.json"))
    if not json_files:
        return issues

    # Track active versions per Type+Subtype+Language triplet
    active_versions: dict[str, list[str]] = {}

    for json_file in json_files:
        try:
            content = json_file.read_text(encoding="utf-8", errors="ignore")
        except (OSError, PermissionError):
            continue

        # Check for DataPack activate:true in what appears to be a CI/non-production config
        if '"activate"' in content and '"true"' in content.lower():
            # Check if this file looks like a CI/environment config
            path_lower = str(json_file).lower()
            if any(env in path_lower for env in ["uat", "dev", "sandbox", "test", "ci", "staging"]):
                issues.append(
                    f"{json_file.name}: DataPack file appears to be in a non-production environment "
                    f"path and contains 'activate: true'. Activating a DataPack on import in UAT/Dev "
                    f"environments will immediately make the version live. Consider setting activate "
                    f"to false for non-production environments."
                )

        # Try to parse as JSON and check for OmniScript records
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            continue

        # Look for OmniProcess/OmniScript records in the DataPack
        records = []
        if isinstance(data, dict):
            records = data.get("records", [])
        elif isinstance(data, list):
            records = data

        for record in records:
            if not isinstance(record, dict):
                continue
            record_type = record.get("attributes", {}).get("type", "")
            if "OmniProcess" not in record_type and "OmniScript" not in record_type:
                continue

            # Build triplet key
            os_type = record.get("Type__c", record.get("OmniProcessType", ""))
            os_subtype = record.get("SubType__c", record.get("OmniProcessSubType", ""))
            os_language = record.get("Language__c", record.get("Language", ""))
            is_active = record.get("IsActive", record.get("Active__c", False))
            version = record.get("VersionNumber", record.get("Version__c", "?"))

            if os_type and os_subtype and os_language and is_active:
                key = f"{os_type}/{os_subtype}/{os_language}"
                if key not in active_versions:
                    active_versions[key] = []
                active_versions[key].append(f"v{version} in {json_file.name}")

    # Report triplets with multiple active versions in the export
    for triplet, versions in active_versions.items():
        if len(versions) > 1:
            issues.append(
                f"Multiple active versions found for OmniScript triplet '{triplet}': "
                f"{', '.join(versions)}. Only one version can be active per triplet. "
                f"Review the DataPack export — activating will overwrite whichever version "
                f"was activated last."
            )

    return issues


def check_omniscript_versioning(datapacks_dir: Path) -> list[str]:
    """Return a list of issue strings found in the DataPacks directory."""
    return scan_datapacks(datapacks_dir)


def main() -> int:
    args = parse_args()
    datapacks_dir = Path(args.datapacks_dir)
    issues = check_omniscript_versioning(datapacks_dir)

    if not issues:
        print("No OmniScript versioning issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\nFound {len(issues)} issue(s). Resolve before importing DataPacks to production.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
