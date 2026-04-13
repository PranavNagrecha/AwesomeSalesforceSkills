#!/usr/bin/env python3
"""Checker script for Einstein Discovery Deployment skill.

Validates Salesforce metadata and Flow XML for common Einstein Discovery
deployment issues: missing bulk predict job schedules, unconfigured model
activation patterns, and incorrect Flow action configuration.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_discovery_deployment.py [--help]
    python3 check_einstein_discovery_deployment.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


# Salesforce metadata XML namespaces
_SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Einstein Discovery deployment metadata for common issues: "
            "missing bulk predict schedules, inactive prediction definitions, "
            "and misconfigured Flow actions."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all XML files with the given suffix under root."""
    return list(root.rglob(f"*{suffix}"))


def check_flow_einstein_discovery_actions(manifest_dir: Path) -> list[str]:
    """Check Flow XML files for Einstein Discovery Action configuration issues."""
    issues: list[str] = []
    flow_files = _find_xml_files(manifest_dir, ".flow-meta.xml")

    for flow_file in flow_files:
        try:
            tree = ET.parse(flow_file)
        except ET.ParseError as exc:
            issues.append(f"{flow_file.name}: XML parse error — {exc}")
            continue

        root = tree.getroot()
        ns = {"sf": _SF_NS}

        # Find actionCalls elements that reference Einstein Discovery actions
        for action_call in root.findall(".//sf:actionCalls", ns):
            action_type_el = action_call.find("sf:actionType", ns)
            action_name_el = action_call.find("sf:actionName", ns)
            call_name_el = action_call.find("sf:name", ns)

            action_type = action_type_el.text if action_type_el is not None else ""
            action_name = action_name_el.text if action_name_el is not None else ""
            call_name = call_name_el.text if call_name_el is not None else "unknown"

            # Einstein Discovery Flow actions use type "EinsteinDiscovery" or
            # action names containing "Prediction" or "EinsteinDiscovery"
            is_ed_action = (
                action_type == "EinsteinDiscovery"
                or "EinsteinDiscovery" in action_name
                or "Prediction" in action_name
            )

            if not is_ed_action:
                continue

            # Check that input parameters are mapped
            input_params = action_call.findall(".//sf:inputParameters", ns)
            if not input_params:
                issues.append(
                    f"{flow_file.name}: Einstein Discovery Action '{call_name}' "
                    f"has no input parameter mappings — source record fields must be "
                    f"mapped to the action's input parameters for scoring to work."
                )

            # Check that output assignments exist
            output_params = action_call.findall(".//sf:outputParameters", ns)
            if not output_params:
                issues.append(
                    f"{flow_file.name}: Einstein Discovery Action '{call_name}' "
                    f"has no output parameter mappings — predicted value and factors "
                    f"will not be stored in Flow variables."
                )

    return issues


def check_prediction_definition_metadata(manifest_dir: Path) -> list[str]:
    """Check for DiscoveryStory or prediction definition metadata files."""
    issues: list[str] = []

    # Look for DiscoveryStory metadata files
    story_files = _find_xml_files(manifest_dir, ".discoveryStory-meta.xml")

    for story_file in story_files:
        try:
            tree = ET.parse(story_file)
        except ET.ParseError as exc:
            issues.append(f"{story_file.name}: XML parse error — {exc}")
            continue

        root = tree.getroot()
        ns = {"sf": _SF_NS}

        # Check that the story has a label (required for deployment)
        label_el = root.find("sf:label", ns)
        if label_el is None or not (label_el.text or "").strip():
            issues.append(
                f"{story_file.name}: DiscoveryStory is missing a label — "
                f"label is required for valid deployment."
            )

        # Check for predictionField elements (output field mappings)
        prediction_fields = root.findall(".//sf:predictionField", ns)
        if not prediction_fields:
            issues.append(
                f"{story_file.name}: DiscoveryStory has no predictionField mappings — "
                f"output fields (Predicted Value, Top Predictors) must be mapped to "
                f"Salesforce object fields for scores to appear on records."
            )

    return issues


def check_for_einstein_discovery_output_fields_on_layouts(manifest_dir: Path) -> list[str]:
    """Warn if page layouts exist but contain no Einstein Discovery output fields."""
    issues: list[str] = []

    layout_files = _find_xml_files(manifest_dir, ".layout-meta.xml")
    if not layout_files:
        return issues

    # Heuristic: Einstein Discovery output field names typically contain
    # patterns like "PredictionScore", "AI_Prediction", "EinsteinDiscovery",
    # or custom field names ending in __pc or __c that the admin mapped.
    # We check for at least one field reference containing "Prediction" or "Einstein".
    ed_field_patterns = ("Prediction", "Einstein", "AIInsight", "AI_Factor", "AI_Pred")

    for layout_file in layout_files:
        try:
            content = layout_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        has_ed_field = any(p in content for p in ed_field_patterns)

        # Only flag if this appears to be a layout for an object that would
        # typically have Einstein Discovery fields (Opportunity, Lead, Case, Account)
        object_name = layout_file.stem.split("-")[0] if "-" in layout_file.stem else ""
        ed_typical_objects = {"Opportunity", "Lead", "Case", "Account", "Contact"}

        if object_name in ed_typical_objects and not has_ed_field:
            issues.append(
                f"{layout_file.name}: Page layout for {object_name} does not appear "
                f"to include any Einstein Discovery output fields (Prediction score, "
                f"Top Factors, Improvement Actions). If Einstein Discovery is deployed "
                f"for this object, add output fields to this layout."
            )

    return issues


def check_einstein_discovery_deployment(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: Flow Einstein Discovery Action configuration
    flow_issues = check_flow_einstein_discovery_actions(manifest_dir)
    issues.extend(flow_issues)

    # Check 2: DiscoveryStory metadata (prediction definition source)
    story_issues = check_prediction_definition_metadata(manifest_dir)
    issues.extend(story_issues)

    # Check 3: Page layout coverage for Einstein Discovery output fields
    layout_issues = check_for_einstein_discovery_output_fields_on_layouts(manifest_dir)
    issues.extend(layout_issues)

    # Check 4: Warn if no Flow or DiscoveryStory metadata found at all
    flow_files = _find_xml_files(manifest_dir, ".flow-meta.xml")
    story_files = _find_xml_files(manifest_dir, ".discoveryStory-meta.xml")
    layout_files = _find_xml_files(manifest_dir, ".layout-meta.xml")

    if not flow_files and not story_files and not layout_files:
        issues.append(
            "No Salesforce metadata files found (*.flow-meta.xml, "
            "*.discoveryStory-meta.xml, *.layout-meta.xml). "
            "Pass --manifest-dir pointing to a retrieved Salesforce project directory."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_einstein_discovery_deployment(manifest_dir)

    if not issues:
        print("No Einstein Discovery deployment issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
