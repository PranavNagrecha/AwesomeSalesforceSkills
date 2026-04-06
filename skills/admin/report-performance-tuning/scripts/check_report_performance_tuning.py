#!/usr/bin/env python3
"""Checker script for Report Performance Tuning skill.

Parses Salesforce report metadata XML files (retrieved via sfdx/sf CLI or
Metadata API) and flags common performance anti-patterns documented in
references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_report_performance_tuning.py [--help]
    python3 check_report_performance_tuning.py --manifest-dir path/to/metadata

The script looks for *.report-meta.xml files under the manifest directory,
typically at: force-app/main/default/reports/**/*.report-meta.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Salesforce Metadata API namespace for report files
_NS = "http://soap.sforce.com/2006/04/metadata"

# Fields that provide high selectivity on large standard objects.
# Reports lacking at least one of these on large objects are at risk.
SELECTIVE_FILTER_FIELDS = {
    "CLOSE_DATE",
    "CREATED_DATE",
    "LAST_MODIFIED_DATE",
    "ACTIVITY_DATE",
    "SERVICE_DATE",
    "OWNER",
    "OWNERID",
    "RECORD_TYPE",
    "RECORDTYPEID",
}

# Dashboard refresh minimum is 24 hours; we flag anything less.
MIN_DASHBOARD_REFRESH_HOURS = 24

# Component count above this threshold warrants a warning.
DASHBOARD_COMPONENT_WARN_THRESHOLD = 20


# ---------------------------------------------------------------------------
# Report XML helpers
# ---------------------------------------------------------------------------

def _tag(name: str) -> str:
    """Return a namespace-qualified tag name."""
    return f"{{{_NS}}}{name}"


def _has_selective_filter(root: ET.Element) -> bool:
    """Return True if the report XML contains at least one selective filter."""
    for criteria in root.iter(_tag("reportFilterCriteria")):
        column = criteria.findtext(_tag("column"), default="").upper()
        if column in SELECTIVE_FILTER_FIELDS:
            return True
    # Also check top-level scope filter (e.g. mine, team)
    scope = root.findtext(_tag("scope"), default="").upper()
    if scope in {"MINE", "TEAM", "ROLEANDSUB", "QUEUE"}:
        return True
    return False


def _count_crt_objects(root: ET.Element) -> int:
    """Count the number of objects referenced in a custom report type."""
    type_refs = list(root.iter(_tag("reportTypeColumnItems")))
    if type_refs:
        return len(type_refs)
    # Fall back: count objectType elements
    return len(list(root.iter(_tag("objectType"))))


def _has_outer_joins(root: ET.Element) -> bool:
    """Return True if any relationship in the report uses outer join behavior."""
    for rel in root.iter(_tag("reportTypeToFieldItem")):
        join_type = rel.findtext(_tag("joinType"), default="").upper()
        if join_type in {"OUTER", "FULL_OUTER"}:
            return True
    return False


# ---------------------------------------------------------------------------
# Main checkers
# ---------------------------------------------------------------------------

def check_report_files(manifest_dir: Path) -> list[str]:
    """Scan report metadata XML files for performance anti-patterns."""
    issues: list[str] = []

    report_files = list(manifest_dir.rglob("*.report-meta.xml"))
    if not report_files:
        # Not an error — the manifest may not include reports.
        return issues

    for report_path in report_files:
        report_name = report_path.stem.replace(".report-meta", "")
        try:
            tree = ET.parse(report_path)
        except ET.ParseError as exc:
            issues.append(f"{report_name}: XML parse error — {exc}")
            continue

        root = tree.getroot()

        # Check 1: Report type
        report_type = root.findtext(_tag("reportType"), default="")
        format_ = root.findtext(_tag("format"), default="")

        # Check 2: Missing selective filter
        if not _has_selective_filter(root):
            issues.append(
                f"{report_name}: No selective filter detected (date range, owner, or "
                f"record type). Reports on large objects without selective filters "
                f"perform a full table scan and may time out. "
                f"Add a date range, Owner, or Record Type filter."
            )

        # Check 3: CRT with many objects
        # report type name is the API name of the report type; standard types
        # do not start with a namespace or custom suffix. CRT names are set by
        # the admin and do not follow a reliable pattern, but we can check
        # object count from the XML structure.
        obj_count = _count_crt_objects(root)
        if obj_count >= 4:
            issues.append(
                f"{report_name}: Report type spans {obj_count} objects. "
                f"Custom report types spanning 4+ objects add significant join "
                f"overhead on large datasets. Verify that all objects contribute "
                f"actively used fields; remove unused objects from the CRT."
            )

        # Check 4: Outer join on high-cardinality path
        if _has_outer_joins(root):
            issues.append(
                f"{report_name}: Outer join (with-or-without) detected in report type. "
                f"Outer joins on high-volume child objects can multiply row counts "
                f"unexpectedly, causing timeouts. Change to inner join unless outer "
                f"join behavior is explicitly required."
            )

        # Check 5: Joined reports have extra overhead
        if format_.upper() == "JOINED":
            issues.append(
                f"{report_name}: Joined report format detected. Joined reports run "
                f"multiple sub-reports and combine them client-side. They have higher "
                f"overhead than tabular or summary formats. Ensure all blocks have "
                f"selective filters."
            )

    return issues


def check_dashboard_files(manifest_dir: Path) -> list[str]:
    """Scan dashboard metadata XML files for performance anti-patterns."""
    issues: list[str] = []

    dashboard_files = list(manifest_dir.rglob("*.dashboard-meta.xml"))
    if not dashboard_files:
        return issues

    for dash_path in dashboard_files:
        dash_name = dash_path.stem.replace(".dashboard-meta", "")
        try:
            tree = ET.parse(dash_path)
        except ET.ParseError as exc:
            issues.append(f"{dash_name}: XML parse error — {exc}")
            continue

        root = tree.getroot()

        # Check 1: Component count
        components = list(root.iter(_tag("dashboardGridComponents")))
        if not components:
            # Try alternate element name used in older metadata format
            components = list(root.iter(_tag("components")))
        component_count = len(components)
        if component_count > DASHBOARD_COMPONENT_WARN_THRESHOLD:
            issues.append(
                f"{dash_name}: Dashboard has {component_count} components "
                f"(threshold: {DASHBOARD_COMPONENT_WARN_THRESHOLD}). Each component "
                f"runs an independent report query on refresh. Consider splitting into "
                f"multiple focused dashboards."
            )

        # Check 2: Running user — flag "run as specified user" for awareness
        running_user = root.findtext(_tag("runningUser"), default="")
        if running_user and running_user.strip():
            issues.append(
                f"{dash_name}: Dashboard runs as specified user '{running_user}'. "
                f"Verify that this sharing scope is intentional — all viewers will "
                f"see this user's data, which may be broader than intended."
            )

    return issues


def check_report_performance_tuning(manifest_dir: Path) -> list[str]:
    """Run all performance checks and return a combined issue list."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_report_files(manifest_dir))
    issues.extend(check_dashboard_files(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce report and dashboard metadata for performance "
            "anti-patterns documented in the report-performance-tuning skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory of the Salesforce metadata. "
            "The script searches recursively for *.report-meta.xml and "
            "*.dashboard-meta.xml files. "
            "Default: current directory."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_report_performance_tuning(manifest_dir)

    if not issues:
        print("No performance issues found in report or dashboard metadata.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
