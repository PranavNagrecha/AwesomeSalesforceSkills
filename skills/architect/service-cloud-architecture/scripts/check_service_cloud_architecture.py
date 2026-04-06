#!/usr/bin/env python3
"""Checker script for Service Cloud Architecture skill.

Checks org metadata or configuration relevant to Service Cloud Architecture.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_service_cloud_architecture.py [--help]
    python3 check_service_cloud_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Service Cloud Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find files with a given suffix under root."""
    results: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(suffix):
                results.append(Path(dirpath) / fname)
    return results


def check_omnichannel_routing_configs(manifest_dir: Path) -> list[str]:
    """Check for Omni-Channel routing configuration metadata issues."""
    issues: list[str] = []

    # Look for ServiceChannel metadata
    service_channels = _find_files(manifest_dir, ".serviceChannel-meta.xml")
    if not service_channels:
        # Not necessarily an issue — may not be in the retrieved metadata
        return issues

    for sc_path in service_channels:
        try:
            tree = ET.parse(sc_path)
            root = tree.getroot()
            # Strip namespace if present
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            # Check if relatedEntityType is set
            entity_elem = root.find(f"{ns}relatedEntityType")
            if entity_elem is None or not entity_elem.text:
                issues.append(
                    f"ServiceChannel {sc_path.name} is missing relatedEntityType — "
                    "routing will not work without a target object."
                )
        except ET.ParseError:
            issues.append(f"Could not parse ServiceChannel metadata: {sc_path}")

    return issues


def check_case_record_types(manifest_dir: Path) -> list[str]:
    """Check Case object for record type and page layout completeness."""
    issues: list[str] = []

    case_object_files = _find_files(manifest_dir, "Case.object-meta.xml")
    if not case_object_files:
        return issues

    for case_path in case_object_files:
        try:
            tree = ET.parse(case_path)
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            # Check for record types
            record_types = root.findall(f"{ns}recordTypes")
            if not record_types:
                issues.append(
                    "Case object has no record types defined. Service Cloud architectures "
                    "typically need record types to separate case types (e.g., Inquiry, "
                    "Incident, Service Request)."
                )
        except ET.ParseError:
            issues.append(f"Could not parse Case object metadata: {case_path}")

    return issues


def check_knowledge_data_categories(manifest_dir: Path) -> list[str]:
    """Check for Knowledge data category group definitions."""
    issues: list[str] = []

    category_files = _find_files(manifest_dir, ".datacategorygroup-meta.xml")
    if not category_files:
        # Check if Knowledge is referenced anywhere
        knowledge_refs = _find_files(manifest_dir, "Knowledge__kav.object-meta.xml")
        if knowledge_refs:
            issues.append(
                "Knowledge object exists but no DataCategoryGroup metadata found. "
                "Knowledge articles without data categories cannot be segmented by "
                "audience (internal, partner, customer). Define data categories "
                "during the architecture phase."
            )

    return issues


def check_entitlement_processes(manifest_dir: Path) -> list[str]:
    """Check for entitlement process metadata."""
    issues: list[str] = []

    entitlement_files = _find_files(manifest_dir, ".entitlementProcess-meta.xml")
    milestone_files = _find_files(manifest_dir, ".milestoneType-meta.xml")

    if not entitlement_files and not milestone_files:
        # Not necessarily an issue — check if Entitlement object is present
        entitlement_obj = _find_files(manifest_dir, "Entitlement.object-meta.xml")
        if entitlement_obj:
            issues.append(
                "Entitlement object exists but no entitlement processes or milestone "
                "types found. SLA enforcement requires entitlement processes with "
                "defined milestones (e.g., First Response, Resolution)."
            )

    return issues


def check_console_app(manifest_dir: Path) -> list[str]:
    """Check Lightning app metadata for Service Console configuration."""
    issues: list[str] = []

    app_files = _find_files(manifest_dir, ".app-meta.xml")
    found_console = False
    for app_path in app_files:
        try:
            tree = ET.parse(app_path)
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            form_factor = root.find(f"{ns}formFactors")
            ui_type = root.find(f"{ns}uiType")

            # Check if this is a console-type app
            if ui_type is not None and ui_type.text == "Lightning":
                nav_type = root.find(f"{ns}navType")
                if nav_type is not None and nav_type.text == "Console":
                    found_console = True

                    # Check utility bar items count
                    utility_items = root.findall(f"{ns}utilityBar")
                    if not utility_items:
                        utility_items = root.findall(f".//{ns}utilityItems")
                    if len(utility_items) > 8:
                        issues.append(
                            f"Console app {app_path.stem} has {len(utility_items)} "
                            "utility bar items. Recommended maximum is 6-8 for "
                            "optimal Console performance."
                        )
        except ET.ParseError:
            issues.append(f"Could not parse app metadata: {app_path}")

    return issues


def check_service_cloud_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Run all checks
    issues.extend(check_omnichannel_routing_configs(manifest_dir))
    issues.extend(check_case_record_types(manifest_dir))
    issues.extend(check_knowledge_data_categories(manifest_dir))
    issues.extend(check_entitlement_processes(manifest_dir))
    issues.extend(check_console_app(manifest_dir))

    if not issues:
        print("All Service Cloud architecture checks passed.")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_service_cloud_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
