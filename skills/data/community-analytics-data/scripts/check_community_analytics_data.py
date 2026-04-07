#!/usr/bin/env python3
"""Checker script for Community Analytics Data skill.

Inspects Salesforce metadata in a sfdx/mdapi project directory for common
Experience Cloud analytics configuration issues described in this skill.

Uses stdlib only — no pip dependencies.

Checks performed:
  1. Detects ExperienceBundle metadata and warns if GA4 Measurement ID is absent.
  2. Warns if NetworkActivityAudit is referenced in a report without a date filter
     (query without time scoping risks hitting retention gaps or large row counts).
  3. Detects custom report types that do NOT include NetworkActivityAudit or
     NetworkUserHistoryMonthly when the report type name suggests community analytics.
  4. Warns if a ReportType referencing Network objects is missing child relationships
     (common sign of an incomplete Custom Report Type setup).

Usage:
    python3 check_community_analytics_data.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import sys
import os
import re
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, suffix: str) -> list[Path]:
    """Walk root and return all files with the given suffix."""
    results: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(suffix):
                results.append(Path(dirpath) / fname)
    return results


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_experience_bundle_ga4(manifest_dir: Path) -> list[str]:
    """Warn if ExperienceBundle site configuration files lack a GA4 Measurement ID."""
    issues: list[str] = []
    # ExperienceBundles live under experienceBundle/<site>/config/<site>.json
    # or experiences/<site>.site in mdapi format
    site_configs = find_files(manifest_dir, ".site")
    experience_jsons: list[Path] = []

    # sfdx format: experienceBundle/**/config/*.json
    bundle_root = manifest_dir / "experienceBundle"
    if bundle_root.is_dir():
        experience_jsons = list(bundle_root.rglob("*.json"))

    checked = False

    # Check mdapi .site metadata files
    for site_file in site_configs:
        checked = True
        content = read_text(site_file)
        if "googleAnalyticsTrackingId" not in content and "measurementId" not in content.lower():
            issues.append(
                f"Experience Cloud site metadata '{site_file.name}' has no GA4 Measurement ID "
                f"configured. If GA4 integration is required, add the Measurement ID under "
                f"Administration > Advanced > Google Analytics, then republish the site. "
                f"(File: {site_file})"
            )

    # Check sfdx ExperienceBundle JSON config files
    ga4_pattern = re.compile(r'(googleAnalyticsTrackingId|measurementId)', re.IGNORECASE)
    for json_file in experience_jsons:
        if "config" in json_file.parts:
            checked = True
            content = read_text(json_file)
            if not ga4_pattern.search(content):
                issues.append(
                    f"ExperienceBundle config '{json_file.name}' has no GA4 Measurement ID. "
                    f"If GA4 tracking is required, configure it in site Administration and republish. "
                    f"(File: {json_file})"
                )

    return issues


def check_report_network_activity_audit_date_filter(manifest_dir: Path) -> list[str]:
    """Warn if a report references NetworkActivityAudit but has no date filter.

    Unscoped queries against NetworkActivityAudit can be slow for active orgs
    and may return unexpected empty results near the 12-month retention boundary.
    """
    issues: list[str] = []
    report_files = find_files(manifest_dir, ".report")
    report_files += find_files(manifest_dir, "-meta.xml")  # sfdx reports

    for report_file in report_files:
        content = read_text(report_file)
        if "NetworkActivityAudit" not in content:
            continue
        # Look for a date filter — common XML field names in report metadata
        has_date_filter = bool(re.search(
            r'<(dateFilter|dateColumn|standardDateFilter|dateFilterColumn)>',
            content,
            re.IGNORECASE,
        ))
        if not has_date_filter:
            issues.append(
                f"Report '{report_file.name}' references NetworkActivityAudit but has no "
                f"date filter. NetworkActivityAudit retains only a rolling 12-month window. "
                f"Add a date filter to scope the query and avoid unexpected empty results "
                f"near the retention boundary. (File: {report_file})"
            )

    return issues


def check_report_type_community_completeness(manifest_dir: Path) -> list[str]:
    """Warn if a ReportType with 'community' or 'network' in its name lacks
    NetworkActivityAudit or NetworkUserHistoryMonthly as a related object."""
    issues: list[str] = []
    report_type_files = find_files(manifest_dir, ".reportType")

    community_pattern = re.compile(r'(community|network|experience)', re.IGNORECASE)
    analytics_objects = {"NetworkActivityAudit", "NetworkUserHistoryMonthly"}

    for rt_file in report_type_files:
        if not community_pattern.search(rt_file.stem):
            continue
        content = read_text(rt_file)
        has_analytics_object = any(obj in content for obj in analytics_objects)
        if not has_analytics_object:
            issues.append(
                f"Custom Report Type '{rt_file.stem}' appears to be community-related but does "
                f"not include NetworkActivityAudit or NetworkUserHistoryMonthly as a related "
                f"object. If this report type is intended for member engagement reporting, add "
                f"the appropriate child object relationship. (File: {rt_file})"
            )

    return issues


def check_report_type_missing_child_relationships(manifest_dir: Path) -> list[str]:
    """Warn if a community-related ReportType has no child sections defined,
    which is a common sign of an incomplete Custom Report Type."""
    issues: list[str] = []
    report_type_files = find_files(manifest_dir, ".reportType")

    community_pattern = re.compile(r'(community|network|NetworkActivity)', re.IGNORECASE)

    for rt_file in report_type_files:
        content = read_text(rt_file)
        if not community_pattern.search(content):
            continue
        # ReportType XML includes <sections> for child object relationships
        has_sections = "<sections>" in content
        if not has_sections:
            issues.append(
                f"Custom Report Type '{rt_file.stem}' appears community-related but has no "
                f"<sections> element, suggesting no child object relationships are defined. "
                f"A Custom Report Type on Networks needs a child relationship to "
                f"NetworkActivityAudit or NetworkUserHistoryMonthly to expose engagement data. "
                f"(File: {rt_file})"
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_community_analytics_data(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_experience_bundle_ga4(manifest_dir))
    issues.extend(check_report_network_activity_audit_date_filter(manifest_dir))
    issues.extend(check_report_type_community_completeness(manifest_dir))
    issues.extend(check_report_type_missing_child_relationships(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Experience Cloud analytics "
            "configuration issues (GA4 setup, NetworkActivityAudit date filters, "
            "Custom Report Type completeness)."
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
    manifest_dir = Path(args.manifest_dir)
    issues = check_community_analytics_data(manifest_dir)

    if not issues:
        print("No community analytics issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
