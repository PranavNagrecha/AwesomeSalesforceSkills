#!/usr/bin/env python3
"""Checker script for Reports and Dashboards Fundamentals skill.

Scans a Salesforce metadata project directory for common report and dashboard
anti-patterns described in this skill's gotchas and well-architected references.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_reports_and_dashboards_fundamentals.py [--help]
    python3 check_reports_and_dashboards_fundamentals.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Reports and Dashboards issues: "
            "hard-coded date filters, static dashboard running users, joined report "
            "block limits, and missing folder assignments."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

SALESFORCE_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    return f"{{{SALESFORCE_NS}}}{local}"


def _parse_xml(path: Path) -> ElementTree.Element | None:
    try:
        return ElementTree.parse(path).getroot()
    except ElementTree.ParseError:
        return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

ABSOLUTE_DATE_PATTERN = re.compile(
    r"\b(19|20)\d{2}[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b"
)

RELATIVE_DATE_KEYWORDS = {
    "TODAY", "YESTERDAY", "TOMORROW", "LAST_N_DAYS", "NEXT_N_DAYS",
    "THIS_WEEK", "LAST_WEEK", "NEXT_WEEK", "THIS_MONTH", "LAST_MONTH",
    "NEXT_MONTH", "THIS_QUARTER", "LAST_QUARTER", "NEXT_QUARTER",
    "THIS_YEAR", "LAST_YEAR", "NEXT_YEAR", "LAST_N_QUARTERS",
    "NEXT_N_QUARTERS", "LAST_N_MONTHS", "NEXT_N_MONTHS",
}


def check_reports(manifest_dir: Path) -> list[str]:
    """Scan *.report-meta.xml files for common issues."""
    issues: list[str] = []
    report_dir = manifest_dir / "reports"
    if not report_dir.exists():
        # Try force-app style paths
        for candidate in manifest_dir.rglob("*.report-meta.xml"):
            issues.extend(_check_single_report(candidate))
        return issues

    for report_file in report_dir.rglob("*.report-meta.xml"):
        issues.extend(_check_single_report(report_file))

    return issues


def _check_single_report(report_file: Path) -> list[str]:
    issues: list[str] = []
    root = _parse_xml(report_file)
    if root is None:
        return [f"Cannot parse report XML: {report_file}"]

    rel_path = str(report_file)

    # Check 1: Hard-coded absolute date filters
    filter_elements = root.findall(f".//{_tag('filter')}")
    for f_el in filter_elements:
        value_el = f_el.find(_tag("value"))
        if value_el is not None and value_el.text:
            val = value_el.text.strip()
            if ABSOLUTE_DATE_PATTERN.search(val):
                issues.append(
                    f"[REPORT] Hard-coded absolute date filter '{val}' in {rel_path}. "
                    "Use a relative date range (e.g., THIS_QUARTER, LAST_N_DAYS:30) "
                    "so the report stays current without manual updates."
                )

    # Check 2: Joined report block count
    blocks = root.findall(f".//{_tag('block')}")
    if len(blocks) > 5:
        issues.append(
            f"[REPORT] Joined report in {rel_path} has {len(blocks)} blocks "
            "(maximum is 5). Reduce the number of blocks or split into separate reports."
        )

    # Check 3: Bucket field value count per bucket
    bucket_fields = root.findall(f".//{_tag('bucketField')}")
    for bf in bucket_fields:
        values = bf.findall(f".//{_tag('sourceColumnName')}")
        bucket_values = bf.findall(f".//{_tag('value')}")
        if len(bucket_values) > 20:
            source = bf.findtext(_tag("sourceColumnName"), "unknown field")
            issues.append(
                f"[REPORT] Bucket field on '{source}' in {rel_path} has "
                f"{len(bucket_values)} bucket values (maximum is 20). "
                "Consolidate bucket ranges."
            )

    # Check 4: Tabular report used without a row limit (potential dashboard incompatibility)
    report_format_el = root.find(_tag("reportType"))
    format_el = root.find(_tag("format"))
    if format_el is not None and format_el.text == "Tabular":
        row_limit_el = root.find(f".//{_tag('rowLimit')}")
        if row_limit_el is None or not row_limit_el.text:
            issues.append(
                f"[REPORT] Tabular report in {rel_path} has no row limit set. "
                "Tabular reports without a row limit cannot drive Metric or Chart "
                "dashboard components. Add a row limit if this report is used in a dashboard."
            )

    return issues


def check_dashboards(manifest_dir: Path) -> list[str]:
    """Scan *.dashboard-meta.xml files for common issues."""
    issues: list[str] = []

    dashboard_files = list(manifest_dir.rglob("*.dashboard-meta.xml"))
    if not dashboard_files:
        return issues

    for dash_file in dashboard_files:
        issues.extend(_check_single_dashboard(dash_file))

    return issues


def _check_single_dashboard(dash_file: Path) -> list[str]:
    issues: list[str] = []
    root = _parse_xml(dash_file)
    if root is None:
        return [f"Cannot parse dashboard XML: {dash_file}"]

    rel_path = str(dash_file)

    # Check 1: Running user set to a specific named user (static dashboard risk)
    running_user_el = root.find(_tag("runningUser"))
    dashboard_type_el = root.find(_tag("dashboardType"))
    dashboard_type = dashboard_type_el.text if dashboard_type_el is not None else ""

    if running_user_el is not None and running_user_el.text:
        running_user = running_user_el.text.strip()
        if running_user and dashboard_type != "LoggedInUser":
            issues.append(
                f"[DASHBOARD] Static running user '{running_user}' in {rel_path}. "
                "All dashboard viewers see this user's data regardless of their own "
                "sharing access. Verify this is intentional. Consider 'Run as logged-in user' "
                "(dynamic dashboard) to enforce per-viewer record-level security."
            )

    # Check 2: More than 20 components
    components = root.findall(f".//{_tag('dashboardGridLayout')}")
    # Try alternative tag for components
    component_tags = root.findall(f".//{_tag('dashboardGridComponent')}")
    if not component_tags:
        component_tags = root.findall(f".//{_tag('components')}")

    if len(component_tags) > 20:
        issues.append(
            f"[DASHBOARD] {rel_path} has {len(component_tags)} components. "
            "Salesforce supports a maximum of 20 source reports per dashboard. "
            "Review and consolidate components."
        )

    # Check 3: Dashboard filters — more than 3
    dashboard_filters = root.findall(f".//{_tag('dashboardFilters')}")
    if len(dashboard_filters) > 3:
        issues.append(
            f"[DASHBOARD] {rel_path} defines {len(dashboard_filters)} dashboard filters. "
            "Salesforce supports a maximum of 3 filters per dashboard."
        )

    return issues


def check_folder_assignments(manifest_dir: Path) -> list[str]:
    """Warn about reports or dashboards that appear to be in a user's private folder.

    Private folders in metadata deployments are uncommon, but a missing or
    empty <folder> element on a Report or Dashboard metadata record can indicate
    it will land in My Personal Custom Reports / My Personal Dashboards.
    """
    issues: list[str] = []

    for report_file in manifest_dir.rglob("*.report-meta.xml"):
        root = _parse_xml(report_file)
        if root is None:
            continue
        folder_el = root.find(_tag("folder"))
        if folder_el is None or not (folder_el.text or "").strip():
            issues.append(
                f"[REPORT] No folder assignment found in {report_file}. "
                "Reports without a folder assignment may land in a private folder. "
                "Assign to a shared folder so team members can access it."
            )

    for dash_file in manifest_dir.rglob("*.dashboard-meta.xml"):
        root = _parse_xml(dash_file)
        if root is None:
            continue
        folder_el = root.find(_tag("folder"))
        if folder_el is None or not (folder_el.text or "").strip():
            issues.append(
                f"[DASHBOARD] No folder assignment found in {dash_file}. "
                "Assign to a shared folder so viewers can access the dashboard."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_reports_and_dashboards_fundamentals(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_reports(manifest_dir))
    issues.extend(check_dashboards(manifest_dir))
    issues.extend(check_folder_assignments(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_reports_and_dashboards_fundamentals(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
