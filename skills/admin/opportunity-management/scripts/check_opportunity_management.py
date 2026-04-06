#!/usr/bin/env python3
"""Checker script for Opportunity Management skill.

Validates Salesforce metadata for common opportunity management configuration
issues: stage picklist integrity, sales process assignments, splits prerequisites,
and forecast category correctness.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_opportunity_management.py [--help]
    python3 check_opportunity_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Platform-fixed ForecastCategoryName values — cannot be renamed
VALID_FORECAST_CATEGORIES = {"Pipeline", "Best Case", "Commit", "Closed", "Omitted"}

# Salesforce metadata namespace used in XML files
SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Opportunity Management configuration and metadata for common issues. "
            "Validates stage picklist values, sales process assignments, and forecast "
            "category integrity."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _tag(name: str) -> str:
    """Return a namespaced XML tag string."""
    return f"{{{SF_NS}}}{name}"


def _find_text(element: ET.Element, tag: str) -> str:
    """Return text of a child element, or empty string if missing."""
    child = element.find(_tag(tag))
    return child.text.strip() if child is not None and child.text else ""


def check_opportunity_stage_metadata(manifest_dir: Path) -> list[str]:
    """Parse StandardValueSet or GlobalValueSet XML for Opportunity Stage values.

    Checks:
    - ForecastCategoryName is one of the five fixed platform values
    - Stages with IsWon=true also have IsClosed=true
    - Stages with ForecastCategoryName=Closed also have IsClosed=true
    - At least one stage with IsWon=true exists
    - At least one stage with IsClosed=true and IsWon=false exists (Closed Lost)
    """
    issues: list[str] = []

    # Look in both standardValueSets/ and globalValueSets/ directories
    candidate_paths = [
        manifest_dir / "standardValueSets" / "OpportunityStage.standardValueSet-meta.xml",
        manifest_dir / "globalValueSets" / "OpportunityStage.globalValueSet-meta.xml",
    ]

    stage_file: Path | None = None
    for path in candidate_paths:
        if path.exists():
            stage_file = path
            break

    if stage_file is None:
        # Not finding the file is advisory — the org may not have deployed this metadata
        return []

    try:
        tree = ET.parse(stage_file)
        root = tree.getroot()
    except ET.ParseError as exc:
        issues.append(f"Could not parse stage metadata file {stage_file}: {exc}")
        return issues

    won_stages: list[str] = []
    closed_lost_stages: list[str] = []

    # Handle both StandardValueSet and GlobalValueSet shapes
    value_tag = _tag("standardValue") if "standardValueSet" in stage_file.name else _tag("customValue")
    all_values = root.findall(f".//{value_tag}")

    if not all_values:
        # Fall back: try both tag names
        all_values = root.findall(f".//{_tag('standardValue')}") or root.findall(f".//{_tag('customValue')}")

    for value_element in all_values:
        label = _find_text(value_element, "fullName") or _find_text(value_element, "label")
        is_active_text = _find_text(value_element, "isActive")
        is_active = is_active_text.lower() != "false"

        if not is_active:
            continue  # Skip inactive stages

        forecast_category = _find_text(value_element, "forecastCategory")
        is_won_text = _find_text(value_element, "won")
        is_closed_text = _find_text(value_element, "closed")

        is_won = is_won_text.lower() == "true" if is_won_text else False
        is_closed = is_closed_text.lower() == "true" if is_closed_text else False

        if not label:
            continue

        # Check: ForecastCategoryName must be one of the five fixed platform values
        if forecast_category and forecast_category not in VALID_FORECAST_CATEGORIES:
            issues.append(
                f"Stage '{label}': ForecastCategoryName '{forecast_category}' is not a valid "
                f"platform value. Must be one of: {', '.join(sorted(VALID_FORECAST_CATEGORIES))}."
            )

        # Check: IsWon=true requires IsClosed=true
        if is_won and not is_closed:
            issues.append(
                f"Stage '{label}': IsWon=true but IsClosed=false. "
                "A Won stage must also be Closed."
            )

        # Check: ForecastCategory=Closed requires IsClosed=true
        if forecast_category == "Closed" and not is_closed:
            issues.append(
                f"Stage '{label}': ForecastCategoryName=Closed but IsClosed=false. "
                "Stages mapped to 'Closed' forecast category must have IsClosed=true."
            )

        # Check: ForecastCategory=Omitted stages should be closed (IsWon=false, IsClosed=true) or
        # document the intent — advisory only
        if forecast_category == "Omitted" and is_won:
            issues.append(
                f"Stage '{label}': ForecastCategoryName=Omitted but IsWon=true. "
                "Won stages are typically mapped to 'Closed', not 'Omitted'. "
                "Verify this is intentional."
            )

        if is_won:
            won_stages.append(label)
        if is_closed and not is_won:
            closed_lost_stages.append(label)

    # Check: org must have at least one Won stage
    if all_values and not won_stages:
        issues.append(
            "No active Opportunity Stage with IsWon=true found. "
            "At least one Won stage is required for closed-won reporting."
        )

    # Check: org must have at least one Closed Lost stage
    if all_values and not closed_lost_stages:
        issues.append(
            "No active Opportunity Stage with IsClosed=true and IsWon=false found. "
            "At least one Closed Lost stage is required for pipeline health reporting."
        )

    return issues


def check_record_type_sales_process(manifest_dir: Path) -> list[str]:
    """Check Opportunity Record Type metadata for missing Sales Process assignments.

    Each Opportunity Record Type should reference a Sales Process.
    """
    issues: list[str] = []

    record_types_dir = manifest_dir / "objects" / "Opportunity" / "recordTypes"
    if not record_types_dir.exists():
        return []

    for rt_file in sorted(record_types_dir.glob("*.recordType-meta.xml")):
        try:
            tree = ET.parse(rt_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"Could not parse record type file {rt_file.name}: {exc}")
            continue

        rt_name = rt_file.stem.replace(".recordType-meta", "")
        is_active_text = _find_text(root, "active")
        is_active = is_active_text.lower() != "false" if is_active_text else True

        if not is_active:
            continue

        business_process = _find_text(root, "businessProcess")
        if not business_process:
            issues.append(
                f"Opportunity Record Type '{rt_name}' is active but has no "
                "Sales Process (businessProcess) assigned. "
                "Every active Opportunity Record Type should reference a Sales Process."
            )

    return issues


def check_splits_team_selling_order(manifest_dir: Path) -> list[str]:
    """Advisory check: warn if OpportunitySplits metadata is present without evidence
    of Opportunity Teams being enabled. Uses Settings metadata if available."""
    issues: list[str] = []

    # Check for OpportunitySplitType metadata — presence implies splits were enabled
    split_types_dir = manifest_dir / "opportunitySplitTypes"
    splits_enabled = split_types_dir.exists() and any(split_types_dir.glob("*.opportunitySplitType-meta.xml"))

    # Check for OpportunitySettings metadata
    settings_dir = manifest_dir / "settings"
    opportunity_settings_file = settings_dir / "Opportunity.settings-meta.xml"

    if splits_enabled and opportunity_settings_file.exists():
        try:
            tree = ET.parse(opportunity_settings_file)
            root = tree.getroot()
            team_selling_text = _find_text(root, "enableOpportunityTeam")
            if team_selling_text.lower() == "false":
                issues.append(
                    "OpportunitySplitType metadata is present but "
                    "Opportunity.settings enableOpportunityTeam is set to false. "
                    "Team Selling must be enabled before Opportunity Splits. "
                    "Verify the settings deployment order."
                )
        except ET.ParseError as exc:
            issues.append(f"Could not parse Opportunity.settings metadata: {exc}")

    return issues


def check_forecast_type_limits(manifest_dir: Path) -> list[str]:
    """Advisory check: warn if more than 4 custom forecast types are defined.

    The default org limit for custom forecast types is 4. Exceeding this requires
    a Support case to raise the limit to 7.
    """
    issues: list[str] = []

    forecast_types_dir = manifest_dir / "forecastingTypes"
    if not forecast_types_dir.exists():
        return []

    type_files = list(forecast_types_dir.glob("*.forecastingType-meta.xml"))
    if len(type_files) > 4:
        issues.append(
            f"Found {len(type_files)} custom forecast types. "
            "The default org limit is 4 custom forecast types. "
            "If this exceeds your org's limit, open a Salesforce Support case to raise it to 7."
        )

    return issues


def check_opportunity_management(manifest_dir: Path) -> list[str]:
    """Run all opportunity management checks. Return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_opportunity_stage_metadata(manifest_dir))
    issues.extend(check_record_type_sales_process(manifest_dir))
    issues.extend(check_splits_team_selling_order(manifest_dir))
    issues.extend(check_forecast_type_limits(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_opportunity_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
