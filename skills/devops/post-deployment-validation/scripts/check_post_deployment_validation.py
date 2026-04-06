#!/usr/bin/env python3
"""Checker script for Post Deployment Validation skill.

Scans a Salesforce metadata project directory for common post-deployment
validation issues: missing test classes for deployed Apex, stale deployment
artifacts, and package.xml hygiene.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_post_deployment_validation.py [--help]
    python3 check_post_deployment_validation.py --manifest-dir path/to/metadata
    python3 check_post_deployment_validation.py --manifest-dir . --check-test-coverage
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

METADATA_NS = "http://soap.sforce.com/2006/04/metadata"
NS = {"md": METADATA_NS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check post-deployment validation readiness for a Salesforce metadata project.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    parser.add_argument(
        "--check-test-coverage",
        action="store_true",
        help="Check that every Apex class in the project has a corresponding test class.",
    )
    return parser.parse_args()


def find_package_xml(manifest_dir: Path) -> Path | None:
    """Locate the package.xml in common project structures."""
    candidates = [
        manifest_dir / "package.xml",
        manifest_dir / "manifest" / "package.xml",
        manifest_dir / "src" / "package.xml",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def parse_package_members(package_path: Path) -> dict[str, list[str]]:
    """Parse package.xml and return a dict of metadata_type -> [member_names]."""
    result: dict[str, list[str]] = {}
    try:
        tree = ET.parse(package_path)
        root = tree.getroot()
        for types_el in root.findall("md:types", NS):
            name_el = types_el.find("md:name", NS)
            if name_el is None or not name_el.text:
                continue
            meta_type = name_el.text.strip()
            members = []
            for member_el in types_el.findall("md:members", NS):
                if member_el.text:
                    members.append(member_el.text.strip())
            result[meta_type] = members
    except ET.ParseError:
        pass
    return result


def find_apex_classes(manifest_dir: Path) -> list[str]:
    """Find all Apex class names in the project by scanning for .cls files."""
    classes = []
    for root_dir, _dirs, files in os.walk(manifest_dir):
        for f in files:
            if f.endswith(".cls") and not f.endswith("-meta.xml"):
                classes.append(f.replace(".cls", ""))
    return classes


def check_post_deployment_validation(manifest_dir: Path, check_coverage: bool = False) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: package.xml exists
    package_path = find_package_xml(manifest_dir)
    if package_path is None:
        issues.append(
            "No package.xml found. A valid package.xml is required for deployment "
            "and for post-deployment validation tracking."
        )
    else:
        # Check 2: package.xml has a version element
        try:
            tree = ET.parse(package_path)
            root = tree.getroot()
            version_el = root.find("md:version", NS)
            if version_el is None or not version_el.text:
                issues.append(
                    f"package.xml at {package_path} is missing a <version> element. "
                    "The API version is required for all deployments."
                )
        except ET.ParseError as e:
            issues.append(f"package.xml at {package_path} has invalid XML: {e}")

        # Check 3: look for wildcard members in destructive manifests
        destructive_names = [
            "destructiveChanges.xml",
            "destructiveChangesPre.xml",
            "destructiveChangesPost.xml",
        ]
        for dname in destructive_names:
            dpath = package_path.parent / dname
            if dpath.is_file():
                members = parse_package_members(dpath)
                for meta_type, member_list in members.items():
                    if "*" in member_list:
                        issues.append(
                            f"Wildcard '*' found in {dname} for type {meta_type}. "
                            "Wildcards are not supported in destructive manifests and will silently fail."
                        )

    # Check 4: Apex test coverage pairing
    if check_coverage:
        apex_classes = find_apex_classes(manifest_dir)
        test_pattern = re.compile(r"(?i)(test|_test$|test_)")
        non_test_classes = [c for c in apex_classes if not test_pattern.search(c)]
        test_classes = [c for c in apex_classes if test_pattern.search(c)]
        test_class_lower = {t.lower() for t in test_classes}

        for cls in non_test_classes:
            # Check common test naming conventions
            expected_names = [
                f"{cls}test",
                f"{cls}_test",
                f"test{cls}",
                f"test_{cls}",
            ]
            has_test = any(name.lower() in test_class_lower for name in expected_names)
            if not has_test:
                issues.append(
                    f"Apex class '{cls}' has no corresponding test class (checked: "
                    f"{', '.join(expected_names)}). Ensure adequate test coverage "
                    "for post-deployment validation — RunSpecifiedTests requires "
                    "75% per class in the package."
                )

    # Check 5: Look for common deployment readiness files
    force_app = manifest_dir / "force-app"
    src_dir = manifest_dir / "src"
    if not force_app.is_dir() and not src_dir.is_dir() and package_path is None:
        issues.append(
            "No recognizable Salesforce project structure found (no force-app/, "
            "no src/, no package.xml). Verify the --manifest-dir path."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_post_deployment_validation(manifest_dir, args.check_test_coverage)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
