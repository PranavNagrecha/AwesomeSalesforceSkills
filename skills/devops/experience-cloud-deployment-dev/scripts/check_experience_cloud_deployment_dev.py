#!/usr/bin/env python3
"""Checker script for Experience Cloud Deployment Dev skill.

Validates a Salesforce project directory for common Experience Cloud deployment issues:
- Detects ExperienceBundle components missing ExperienceBundleSettings
- Detects DigitalExperienceBundle components used with too-low API version
- Detects package.xml files that include ExperienceBundle without Network metadata
- Detects whether ExperienceBundleSettings has enableExperienceBundle set to true
- Warns when no CMS content migration documentation is present alongside site bundles

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_deployment_dev.py [--help]
    python3 check_experience_cloud_deployment_dev.py --manifest-dir path/to/metadata
    python3 check_experience_cloud_deployment_dev.py --manifest-dir . --package-xml package.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


EXPERIENCE_BUNDLE_MIN_API = 46
DIGITAL_EXPERIENCE_BUNDLE_MIN_API = 58

# Salesforce Metadata API XML namespace
META_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce project for common Experience Cloud deployment issues. "
            "Validates ExperienceBundleSettings, Network metadata pairing, API version, "
            "and deployment order prerequisites."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    parser.add_argument(
        "--package-xml",
        default=None,
        help="Path to a package.xml manifest to analyze (optional).",
    )
    return parser.parse_args()


def find_experience_bundle_dirs(manifest_dir: Path) -> list[Path]:
    """Find all ExperienceBundle site directories (Aura-based sites)."""
    experiences_dir = manifest_dir / "force-app" / "main" / "default" / "experiences"
    if not experiences_dir.exists():
        # Try flat structure
        experiences_dir = manifest_dir / "experiences"
    if not experiences_dir.exists():
        return []
    return [p for p in experiences_dir.iterdir() if p.is_dir()]


def find_digital_experience_bundle_dirs(manifest_dir: Path) -> list[Path]:
    """Find all DigitalExperienceBundle site directories (enhanced LWR sites)."""
    digital_dir = manifest_dir / "force-app" / "main" / "default" / "digitalExperiences" / "site"
    if not digital_dir.exists():
        digital_dir = manifest_dir / "digitalExperiences" / "site"
    if not digital_dir.exists():
        return []
    return [p for p in digital_dir.iterdir() if p.is_dir()]


def find_experience_bundle_settings(manifest_dir: Path) -> Path | None:
    """Find the ExperienceBundleSettings settings metadata file."""
    candidates = [
        manifest_dir / "force-app" / "main" / "default" / "settings" / "ExperienceBundleSettings.settings-meta.xml",
        manifest_dir / "settings" / "ExperienceBundleSettings.settings-meta.xml",
        manifest_dir / "ExperienceBundleSettings.settings-meta.xml",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def check_experience_bundle_settings_enabled(settings_file: Path) -> bool:
    """Return True if enableExperienceBundle is set to true in the settings file."""
    try:
        tree = ET.parse(settings_file)
        root = tree.getroot()
        # Handle namespaced XML
        tag = f"{{{META_NS}}}enableExperienceBundle"
        for elem in root.iter(tag):
            return elem.text and elem.text.strip().lower() == "true"
        # Try without namespace
        for elem in root.iter("enableExperienceBundle"):
            return elem.text and elem.text.strip().lower() == "true"
    except ET.ParseError:
        pass
    return False


def get_sfdx_api_version(manifest_dir: Path) -> int | None:
    """Read sourceApiVersion from sfdx-project.json if present."""
    import json
    sfdx_project = manifest_dir / "sfdx-project.json"
    if not sfdx_project.exists():
        return None
    try:
        with open(sfdx_project) as f:
            data = json.load(f)
        version_str = data.get("sourceApiVersion", "")
        if version_str:
            return int(float(version_str))
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    return None


def parse_package_xml(package_xml_path: Path) -> dict[str, list[str]]:
    """Parse a package.xml and return a dict of {TypeName: [member, ...]}."""
    result: dict[str, list[str]] = {}
    try:
        tree = ET.parse(package_xml_path)
        root = tree.getroot()
        ns = META_NS
        for types_elem in root.findall(f"{{{ns}}}types"):
            name_elem = types_elem.find(f"{{{ns}}}name")
            if name_elem is None or not name_elem.text:
                continue
            type_name = name_elem.text.strip()
            members = [
                m.text.strip()
                for m in types_elem.findall(f"{{{ns}}}members")
                if m.text
            ]
            result[type_name] = members
    except ET.ParseError:
        pass
    return result


def check_package_xml_for_issues(package_xml_path: Path) -> list[str]:
    """Check a package.xml for Experience Cloud deployment issues."""
    issues: list[str] = []
    components = parse_package_xml(package_xml_path)

    has_experience_bundle = "ExperienceBundle" in components
    has_digital_experience_bundle = "DigitalExperienceBundle" in components
    has_network = "Network" in components
    has_experience_bundle_settings = (
        "Settings" in components
        and "ExperienceBundleSettings" in components.get("Settings", [])
    )

    if has_experience_bundle and not has_experience_bundle_settings:
        issues.append(
            f"{package_xml_path.name}: ExperienceBundle is present but "
            "Settings:ExperienceBundleSettings is missing. Retrieve/deploy of "
            "ExperienceBundle will silently return empty results if this setting "
            "is not enabled in the org."
        )

    if has_experience_bundle and not has_network:
        eb_sites = components.get("ExperienceBundle", [])
        issues.append(
            f"{package_xml_path.name}: ExperienceBundle member(s) {eb_sites} are present "
            "but Network metadata is missing. Deploying ExperienceBundle without the "
            "corresponding Network record creates an orphaned site bundle."
        )

    if has_digital_experience_bundle and not has_network:
        deb_sites = components.get("DigitalExperienceBundle", [])
        issues.append(
            f"{package_xml_path.name}: DigitalExperienceBundle member(s) {deb_sites} are present "
            "but Network metadata is missing. Always include the Network record alongside "
            "the site bundle."
        )

    if has_experience_bundle and has_digital_experience_bundle:
        issues.append(
            f"{package_xml_path.name}: Both ExperienceBundle and DigitalExperienceBundle are "
            "present in the same package.xml. These types serve different site runtimes "
            "(Aura vs. enhanced LWR). Confirm whether both are intentional or if one "
            "is incorrect."
        )

    return issues


def check_experience_cloud_deployment_dev(manifest_dir: Path, package_xml: Path | None = None) -> list[str]:
    """Return a list of issue strings found in the project directory.

    Each returned string describes a concrete, actionable problem.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: ExperienceBundle present but ExperienceBundleSettings missing
    eb_dirs = find_experience_bundle_dirs(manifest_dir)
    deb_dirs = find_digital_experience_bundle_dirs(manifest_dir)
    settings_file = find_experience_bundle_settings(manifest_dir)

    if eb_dirs and not settings_file:
        site_names = [d.name for d in eb_dirs]
        issues.append(
            f"ExperienceBundle site directories found {site_names} but "
            "ExperienceBundleSettings.settings-meta.xml is not present in this project. "
            "Without this settings file, retrieve/deploy of ExperienceBundle will silently "
            "return empty results if ExperienceBundleSettings is not already enabled in the target org. "
            "Add Settings:ExperienceBundleSettings to your package.xml and project."
        )

    # Check 2: ExperienceBundleSettings present but enableExperienceBundle is false
    if settings_file:
        if not check_experience_bundle_settings_enabled(settings_file):
            issues.append(
                f"ExperienceBundleSettings found at {settings_file} but "
                "<enableExperienceBundle> is not set to 'true'. "
                "Deploying this file will disable ExperienceBundle in the target org. "
                "Set <enableExperienceBundle>true</enableExperienceBundle>."
            )

    # Check 3: API version too low for DigitalExperienceBundle
    if deb_dirs:
        api_version = get_sfdx_api_version(manifest_dir)
        if api_version is not None and api_version < DIGITAL_EXPERIENCE_BUNDLE_MIN_API:
            issues.append(
                f"DigitalExperienceBundle directories found but sfdx-project.json "
                f"sourceApiVersion is {api_version}.0, which is below the minimum "
                f"required API version {DIGITAL_EXPERIENCE_BUNDLE_MIN_API}.0. "
                "Update sourceApiVersion to 58.0 or higher."
            )

    # Check 4: Analyze package.xml if provided
    if package_xml is not None and package_xml.exists():
        pkg_issues = check_package_xml_for_issues(package_xml)
        issues.extend(pkg_issues)
    else:
        # Search for package.xml files in common locations
        for candidate_name in ["package.xml", "manifest/package.xml"]:
            candidate = manifest_dir / candidate_name
            if candidate.exists():
                pkg_issues = check_package_xml_for_issues(candidate)
                issues.extend(pkg_issues)
                break

    # Check 5: Warn about CMS content gap if site bundles are present
    if eb_dirs or deb_dirs:
        site_count = len(eb_dirs) + len(deb_dirs)
        # Check if there's any documented CMS migration plan nearby
        runbook_indicators = list(manifest_dir.rglob("cms*migration*")) + list(manifest_dir.rglob("*cms*runbook*"))
        if not runbook_indicators:
            issues.append(
                f"INFO: {site_count} Experience Cloud site bundle(s) found. "
                "CMS Managed Content (from CMS Workspaces) is NOT included in ExperienceBundle "
                "or DigitalExperienceBundle and cannot be deployed via sf CLI. "
                "If the site uses CMS Workspace content, plan a separate CMS export/import or "
                "Managed Content REST API migration. A successful deploy (exit 0) does not guarantee "
                "CMS content will be present in the target org."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    package_xml = Path(args.package_xml) if args.package_xml else None

    issues = check_experience_cloud_deployment_dev(manifest_dir, package_xml)

    if not issues:
        print("No Experience Cloud deployment issues found.")
        return 0

    exit_code = 0
    for issue in issues:
        if issue.startswith("INFO:"):
            print(f"INFO: {issue[5:].strip()}")
        else:
            print(f"WARN: {issue}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
