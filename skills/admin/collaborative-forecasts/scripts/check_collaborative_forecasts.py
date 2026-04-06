#!/usr/bin/env python3
"""Checker script for Collaborative Forecasts skill.

Checks Salesforce metadata files for common Collaborative Forecasts configuration issues.
Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_collaborative_forecasts.py [--help]
    python3 check_collaborative_forecasts.py --manifest-dir path/to/metadata
    python3 check_collaborative_forecasts.py --manifest-dir force-app/main/default

Checks performed:
  1. ForecastingSettings presence -- warns if no ForecastingSettings metadata found
  2. Active Forecast Type count -- warns if more than 4 Forecast Types are active
  3. Stage-to-category mapping for Omitted -- flags common revenue stages mapped to Omitted
  4. ForecastingQuota CSV files -- flags quota load CSVs missing ForecastingTypeId column
  5. Rollup method documentation -- flags Forecast Types with no rollupType element
"""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_ACTIVE_FORECAST_TYPES = 4

# Forecast category values that exclude opportunities from all rollups
OMIT_CATEGORY_VALUES = {"omitted", "omit"}

# Common stage names that are almost always revenue-generating
# and should not be mapped to Omitted
LIKELY_REVENUE_STAGES = {
    "prospecting",
    "qualification",
    "needs analysis",
    "value proposition",
    "id. decision makers",
    "perception analysis",
    "proposal/price quote",
    "negotiation/review",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from a tag name."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def get_text(element: ET.Element, child_tag: str) -> str:
    """Return text content of a direct child element, or empty string."""
    for child in element:
        if strip_ns(child.tag) == child_tag:
            return (child.text or "").strip()
    return ""


def iter_children(element: ET.Element, child_tag: str):
    """Yield all direct child elements with the given tag (namespace-stripped)."""
    for child in element:
        if strip_ns(child.tag) == child_tag:
            yield child


def find_forecasting_settings(root: Path) -> list[Path]:
    """Return ForecastingSettings metadata files under root."""
    return (
        find_files(root, "ForecastingSettings.settings")
        + find_files(root, "ForecastingSettings.settings-meta.xml")
    )


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_forecasting_settings_present(manifest_dir: Path) -> list[str]:
    """Warn if no ForecastingSettings metadata file is found in the manifest."""
    issues: list[str] = []
    settings_files = find_forecasting_settings(manifest_dir)
    if not settings_files:
        issues.append(
            "No ForecastingSettings metadata file found "
            "(ForecastingSettings.settings or ForecastingSettings.settings-meta.xml). "
            "Collaborative Forecasts configuration is not captured in this metadata deployment. "
            "If Collaborative Forecasts is configured in this org, add ForecastingSettings "
            "to your package.xml and retrieve it to ensure forecast configuration is source-tracked."
        )
    return issues


def check_active_forecast_type_count(manifest_dir: Path) -> list[str]:
    """Warn if more than 4 Forecast Types are configured as active in ForecastingSettings."""
    issues: list[str] = []
    settings_files = find_forecasting_settings(manifest_dir)

    for sf in settings_files:
        root = parse_xml_safe(sf)
        if root is None:
            continue

        active_types: list[str] = []
        for forecast_type in iter_children(root, "forecastingTypeSettings"):
            active_str = get_text(forecast_type, "active").lower()
            if active_str == "true":
                name = (
                    get_text(forecast_type, "developerName")
                    or get_text(forecast_type, "name")
                    or "<unnamed>"
                )
                active_types.append(name)

        if len(active_types) > MAX_ACTIVE_FORECAST_TYPES:
            issues.append(
                f"More than {MAX_ACTIVE_FORECAST_TYPES} active Forecast Types found in "
                f"{sf.name}: {active_types}. "
                f"Salesforce allows a maximum of {MAX_ACTIVE_FORECAST_TYPES} active Forecast Types "
                "by default. Additional types require a Salesforce Support case to raise the limit. "
                "Review active types and deactivate any that are no longer in use."
            )

    return issues


def check_omitted_stage_mapping(manifest_dir: Path) -> list[str]:
    """Flag opportunity stages that appear revenue-generating but are mapped to Omitted."""
    issues: list[str] = []
    settings_files = find_forecasting_settings(manifest_dir)

    for sf in settings_files:
        root = parse_xml_safe(sf)
        if root is None:
            continue

        for stage_map in iter_children(root, "opportunityListFieldsLabelMappings"):
            stage_name = get_text(stage_map, "field")
            category = get_text(stage_map, "label").lower()
            if category in OMIT_CATEGORY_VALUES:
                if stage_name.lower() in LIKELY_REVENUE_STAGES:
                    issues.append(
                        f"Opportunity stage '{stage_name}' is mapped to Omitted in {sf.name}. "
                        "This stage name typically represents active pipeline revenue. "
                        "Omitted stages are excluded from ALL forecast rollups including Pipeline. "
                        "Verify this mapping is intentional -- if the stage has open opportunities, "
                        "they are completely invisible in every Collaborative Forecast view."
                    )

    return issues


def check_rollup_method_documentation(manifest_dir: Path) -> list[str]:
    """Flag active Forecast Types with no rollupType element set."""
    issues: list[str] = []
    settings_files = find_forecasting_settings(manifest_dir)

    for sf in settings_files:
        root = parse_xml_safe(sf)
        if root is None:
            continue

        for forecast_type in iter_children(root, "forecastingTypeSettings"):
            active_str = get_text(forecast_type, "active").lower()
            if active_str != "true":
                continue
            name = (
                get_text(forecast_type, "developerName")
                or get_text(forecast_type, "name")
                or "<unnamed>"
            )
            rollup_method = get_text(forecast_type, "rollupType")

            if not rollup_method:
                issues.append(
                    f"Active Forecast Type '{name}' in {sf.name} has no rollupType element. "
                    "Confirm whether this type uses cumulative or single-category rollup. "
                    "Rollup method cannot be changed after adjustments exist without "
                    "permanently deleting all adjustment data."
                )

    return issues


def check_quota_csv_missing_forecast_type(manifest_dir: Path) -> list[str]:
    """Flag CSV files that appear to be quota loads but are missing ForecastingTypeId column."""
    issues: list[str] = []

    csv_files = find_files(manifest_dir, "*.csv")
    quota_csv_candidates = [
        f for f in csv_files
        if "quota" in f.name.lower() or "forecastingquota" in f.name.lower()
    ]

    for csv_file in quota_csv_candidates:
        try:
            with csv_file.open(newline="", encoding="utf-8-sig") as fh:
                reader = csv.DictReader(fh)
                fieldnames = [
                    (f.lower() if f else "") for f in (reader.fieldnames or [])
                ]

            has_forecast_type = any(
                "forecastingtypeid" in col or "forecastingtype" in col
                for col in fieldnames
            )
            if not has_forecast_type:
                issues.append(
                    f"Quota CSV file '{csv_file.name}' does not contain a ForecastingTypeId column. "
                    "ForecastingQuota records require ForecastingTypeId to associate the quota with "
                    "a specific Forecast Type. Without it, quota records may load successfully "
                    "but will not display attainment on the Forecasts page. "
                    "Add a ForecastingTypeId column and populate it with the correct Forecast Type ID. "
                    "Retrieve the correct ID via: SELECT Id, Name FROM ForecastingType"
                )
        except (OSError, csv.Error):
            pass

    return issues


def check_no_forecast_metadata(manifest_dir: Path) -> list[str]:
    """Informational: note if no forecast-related metadata or data files are found."""
    issues: list[str] = []
    forecast_files = (
        find_forecasting_settings(manifest_dir)
        + find_files(manifest_dir, "*quota*.csv")
        + find_files(manifest_dir, "*Quota*.csv")
    )
    if not forecast_files:
        issues.append(
            "No Collaborative Forecasts metadata or quota data files found in the manifest directory. "
            "If Collaborative Forecasts is not part of this deployment, this check can be ignored. "
            "If it should be included, retrieve ForecastingSettings metadata and include any "
            "quota load CSV files in the manifest directory."
        )
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    all_issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    all_issues.extend(check_no_forecast_metadata(manifest_dir))
    all_issues.extend(check_forecasting_settings_present(manifest_dir))
    all_issues.extend(check_active_forecast_type_count(manifest_dir))
    all_issues.extend(check_omitted_stage_mapping(manifest_dir))
    all_issues.extend(check_rollup_method_documentation(manifest_dir))
    all_issues.extend(check_quota_csv_missing_forecast_type(manifest_dir))

    return all_issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Collaborative Forecasts metadata and quota data for common issues. "
            "Point --manifest-dir at the root of your Salesforce metadata project or "
            "the force-app/main/default directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    print(f"Checking Collaborative Forecasts metadata in: {manifest_dir}\n")

    issues = run_all_checks(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}\n")

    print(f"{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
