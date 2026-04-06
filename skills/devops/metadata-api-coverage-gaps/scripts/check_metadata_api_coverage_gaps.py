#!/usr/bin/env python3
"""Checker script for Metadata API Coverage Gaps skill.

Scans a Salesforce project directory for common coverage-gap risks:
- package.xml entries for known-problematic metadata types
- Missing .forceignore entries for commonly unsupported types
- sourceApiVersion consistency in sfdx-project.json

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_metadata_api_coverage_gaps.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Metadata types with known persistent coverage gaps (as of API v60+).
# This list is intentionally conservative -- only types with well-documented,
# long-standing gaps are included.  Practitioners should always cross-reference
# the Metadata Coverage Report for the definitive, version-specific answer.
KNOWN_GAP_TYPES: dict[str, str] = {
    "ForecastingSettings": "Partial support; deployment often fails depending on target org forecasting config. Use release runbook.",
    "OrgPreferenceSettings": "Several fields removed in API v48+. Deprecated fields cause deploy failures on newer orgs.",
    "EmailServicesFunction": "Not source-tracked. Changes in Setup UI will not appear in sf project retrieve.",
    "LiveAgentSettings": "Partial support; some sub-elements are silently ignored during deployment.",
    "SocialCustomerServiceSettings": "Limited support; requires manual Setup configuration in most cases.",
    "EinsteinAnalyticsSettings": "Partial support; dashboard and lens deployment may silently skip components.",
}

# Types that are commonly source-tracking blind spots
SOURCE_TRACKING_GAPS: set[str] = {
    "EmailServicesFunction",
    "PermissionSetAssignment",
    "CaseSettings",
    "LiveAgentSettings",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a Salesforce project for metadata API coverage gap risks.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


def find_package_xml_types(manifest_dir: Path) -> list[tuple[str, Path]]:
    """Parse all package.xml files and return (type_name, file_path) tuples."""
    found: list[tuple[str, Path]] = []
    for pkg_file in manifest_dir.rglob("package.xml"):
        try:
            tree = ET.parse(pkg_file)  # noqa: S314
            root = tree.getroot()
            # Handle namespace in Metadata API package.xml
            ns = ""
            match = re.match(r"\{(.+)\}", root.tag)
            if match:
                ns = f"{{{match.group(1)}}}"
            for types_elem in root.findall(f"{ns}types"):
                name_elem = types_elem.find(f"{ns}name")
                if name_elem is not None and name_elem.text:
                    found.append((name_elem.text.strip(), pkg_file))
        except ET.ParseError:
            pass
    return found


def check_forceignore(manifest_dir: Path) -> set[str]:
    """Return the set of patterns in .forceignore, if it exists."""
    fi_path = manifest_dir / ".forceignore"
    if not fi_path.exists():
        return set()
    patterns: set[str] = set()
    for line in fi_path.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            patterns.add(stripped)
    return patterns


def check_source_api_version(manifest_dir: Path) -> list[str]:
    """Check sfdx-project.json for sourceApiVersion consistency."""
    issues: list[str] = []
    proj_file = manifest_dir / "sfdx-project.json"
    if not proj_file.exists():
        return issues
    try:
        proj = json.loads(proj_file.read_text())
    except (json.JSONDecodeError, OSError):
        issues.append(f"Could not parse {proj_file}")
        return issues

    version = proj.get("sourceApiVersion")
    if not version:
        issues.append(
            "WARN: sfdx-project.json does not set sourceApiVersion. "
            "Team members may use different API versions, causing inconsistent "
            "metadata type support. Set sourceApiVersion explicitly."
        )
    return issues


def check_metadata_api_coverage_gaps(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Project directory not found: {manifest_dir}")
        return issues

    # 1. Check sourceApiVersion
    issues.extend(check_source_api_version(manifest_dir))

    # 2. Scan package.xml files for known-gap types
    pkg_types = find_package_xml_types(manifest_dir)
    for type_name, pkg_path in pkg_types:
        if type_name in KNOWN_GAP_TYPES:
            issues.append(
                f"WARN: {pkg_path} includes '{type_name}' which has known coverage gaps. "
                f"{KNOWN_GAP_TYPES[type_name]}"
            )

    # 3. Check .forceignore for common unsupported types
    forceignore_patterns = check_forceignore(manifest_dir)
    fi_exists = (manifest_dir / ".forceignore").exists()
    if not fi_exists and pkg_types:
        issues.append(
            "INFO: No .forceignore file found. Consider adding one to exclude "
            "unsupported metadata types from source tracking and deployment."
        )

    # 4. Check for source-tracking-blind metadata in sfdx-project package directories
    proj_file = manifest_dir / "sfdx-project.json"
    if proj_file.exists():
        try:
            proj = json.loads(proj_file.read_text())
            pkg_dirs = proj.get("packageDirectories", [])
            for pkg_dir in pkg_dirs:
                pkg_path_str = pkg_dir.get("path", "")
                pkg_path = manifest_dir / pkg_path_str
                if pkg_path.exists():
                    for gap_type in SOURCE_TRACKING_GAPS:
                        # Look for directories or files matching the gap type name
                        matches = list(pkg_path.rglob(f"*{gap_type}*"))
                        if matches:
                            issues.append(
                                f"INFO: Package directory '{pkg_path_str}' contains "
                                f"'{gap_type}' components which are not fully source-tracked. "
                                f"Add explicit retrieve steps to your workflow."
                            )
        except (json.JSONDecodeError, OSError):
            pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_metadata_api_coverage_gaps(manifest_dir)

    if not issues:
        print("No metadata coverage gap risks detected.")
        return 0

    for issue in issues:
        print(f"  {issue}")

    warn_count = sum(1 for i in issues if i.startswith("WARN"))
    info_count = sum(1 for i in issues if i.startswith("INFO"))
    print(f"\nSummary: {warn_count} warnings, {info_count} informational notes.")
    return 1 if warn_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
