#!/usr/bin/env python3
"""Checker script for Report Performance Tuning skill.

Parses Salesforce Report, ReportType and Dashboard metadata (retrieved via
sf CLI or Metadata API) and flags the performance anti-patterns documented
in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_report_performance_tuning.py [--help]
    python3 check_report_performance_tuning.py --manifest-dir path/to/metadata [--strict]

Files scanned (recursively): *.report-meta.xml, *.reportType-meta.xml,
*.dashboard-meta.xml (and the .report / .reportType / .dashboard forms).

Severity (Metadata API Developer Guide 264 unless noted):
  ERROR  a file that does not parse as XML
  ERROR  a Report missing a Required field: name, reportType (api_meta L106776, L106795)
  ERROR  a ReportType missing a Required field: baseObject, deployed, label
         (api_meta L108421, L108453, L108475)
  WARN   no selective filter: no filter/criteriaItems on a date / owner / record
         type column, no timeFrameFilter (L107791-107801), and a scope that is
         absent or starts with "All" (scope values e.g. MyAccounts / AllAccounts,
         L106822-106829)
  WARN   100 or more columns (detail columns + summaries + custom summary
         formulas) — the REST API error text refuses a report that is not
         "fewer than 100 columns" (Reports and Dashboards REST API 262, Report
         Error Codes), though the limits say "up to 100" (apexdev 264 L33681)
  WARN   more than 20 field filters / 3 cross filters / 5 custom summary
         formulas (50 for joined) — report-builder allocations that are
         Help-only (UNVERIFIED 2026-10-21)
  WARN   a custom report type joining 4 objects (the documented maximum,
         L108487) or using an outer join (L108493-108495)
  WARN   a joined report (check every block has a selective filter)
  WARN   a dashboard with more than 20 components (Help-only guidance,
         UNVERIFIED) or dashboardType SpecifiedUser (every viewer sees the
         running user's data, L50170-50174)

Exit codes: ERROR findings and a missing --manifest-dir exit 1; WARN findings
exit 0 unless --strict; an empty directory prints one WARN and exits 0.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"

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

MAX_REPORT_COLUMNS = 100
MAX_FIELD_FILTERS = 20
MAX_CROSS_FILTERS = 3
MAX_REPORT_FORMULAS = 5
MAX_JOINED_REPORT_FORMULAS = 50
MAX_CRT_OBJECTS = 4
DASHBOARD_COMPONENT_WARN_THRESHOLD = 20

REPORT_SUFFIXES = (".report-meta.xml", ".report")
REPORT_TYPE_SUFFIXES = (".reportType-meta.xml", ".reportType")
DASHBOARD_SUFFIXES = (".dashboard-meta.xml", ".dashboard")


def _tag(name: str) -> str:
    return f"{{{_NS}}}{name}"


def _files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and p.name.endswith(suffixes))


def _stem(path: Path, suffixes: tuple[str, ...]) -> str:
    for s in suffixes:
        if path.name.endswith(s):
            return path.name[: -len(s)]
    return path.stem


def _top_text(root: ET.Element, name: str) -> str:
    elem = root.find(_tag(name))
    return (elem.text or "").strip() if elem is not None else ""


def _iter_filter_items(root: ET.Element):
    """Field filters live under filter/criteriaItems; crossFilters reuse the
    criteriaItems name for subfilters, so the search is scoped to <filter>."""
    for filt in root.iter(_tag("filter")):
        yield from filt.findall(_tag("criteriaItems"))


def _has_selective_filter(root: ET.Element) -> bool:
    for criteria in _iter_filter_items(root):
        column = (criteria.findtext(_tag("column"), default="") or "").upper()
        if column.split(".")[-1] in SELECTIVE_FILTER_FIELDS:
            return True
    tff = root.find(_tag("timeFrameFilter"))
    if tff is not None:
        interval = (tff.findtext(_tag("interval"), default="") or "").strip().upper()
        has_dates = bool(tff.findtext(_tag("startDate")) or tff.findtext(_tag("endDate")))
        if interval and (interval != "INTERVAL_CUSTOM" or has_dates):
            return True
    scope = _top_text(root, "scope").lower()
    if scope and not scope.startswith("all") and scope != "organization":
        return True
    return False


def _count_columns(root: ET.Element) -> int:
    """Detail columns + summaries (aggregateTypes) + custom summary formulas (aggregates)."""
    return (
        len(list(root.iter(_tag("columns"))))
        + len(list(root.iter(_tag("aggregateTypes"))))
        + len(list(root.iter(_tag("aggregates"))))
    )


def check_reports(manifest_dir: Path, errors: list[str], warns: list[str]) -> None:
    for path in _files(manifest_dir, REPORT_SUFFIXES):
        name = _stem(path, REPORT_SUFFIXES)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            errors.append(f"{name}: XML parse error — {exc}")
            continue
        for required in ("name", "reportType"):
            if not _top_text(root, required):
                errors.append(f"{name}: Required Report field <{required}> is missing or empty")
        fmt = _top_text(root, "format").upper()

        if not _has_selective_filter(root):
            warns.append(
                f"{name}: no selective filter (date/owner/record type criteria, timeFrameFilter, or an "
                f"owner scope). Without a selective indexed filter the optimizer performs a full scan."
            )
        column_count = _count_columns(root)
        if column_count >= MAX_REPORT_COLUMNS:
            warns.append(
                f"{name}: ~{column_count} columns (detail columns + summaries + custom summary formulas). "
                f"The REST API error text reads 'Only a report with fewer than {MAX_REPORT_COLUMNS} columns can be "
                f"run' (the limits page says 'up to {MAX_REPORT_COLUMNS}'); stay at {MAX_REPORT_COLUMNS - 1} or fewer."
            )
        filter_count = len(list(_iter_filter_items(root)))
        if filter_count > MAX_FIELD_FILTERS:
            warns.append(
                f"{name}: {filter_count} field filters — over the {MAX_FIELD_FILTERS} report-builder "
                f"allocation Help gives (UNVERIFIED)."
            )
        cross_count = len(list(root.iter(_tag("crossFilters"))))
        if cross_count > MAX_CROSS_FILTERS:
            warns.append(
                f"{name}: {cross_count} cross filters — over the {MAX_CROSS_FILTERS} per report Help gives "
                f"(UNVERIFIED)."
            )
        formula_cap = MAX_JOINED_REPORT_FORMULAS if fmt == "JOINED" else MAX_REPORT_FORMULAS
        formula_count = len(list(root.iter(_tag("aggregates"))))
        if formula_count > formula_cap:
            warns.append(
                f"{name}: {formula_count} custom summary formulas — over the {formula_cap} Help gives for "
                f"this format (UNVERIFIED)."
            )
        if fmt == "JOINED":
            warns.append(f"{name}: joined report — confirm every block has a selective filter.")


def _join_depth(elem: ET.Element) -> int:
    depth = 0
    node = elem.find(_tag("join"))
    while node is not None:
        depth += 1
        node = node.find(_tag("join"))
    return depth


def check_report_types(manifest_dir: Path, errors: list[str], warns: list[str]) -> None:
    for path in _files(manifest_dir, REPORT_TYPE_SUFFIXES):
        name = _stem(path, REPORT_TYPE_SUFFIXES)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            errors.append(f"{name}: XML parse error — {exc}")
            continue
        for required in ("baseObject", "deployed", "label"):
            if not _top_text(root, required):
                errors.append(f"{name}: Required ReportType field <{required}> is missing or empty")
        objects = 1 + _join_depth(root)
        if objects >= MAX_CRT_OBJECTS:
            warns.append(
                f"{name}: custom report type joins {objects} objects (the documented maximum is "
                f"{MAX_CRT_OBJECTS}); remove objects that contribute no displayed fields."
            )
        if any((j.findtext(_tag("outerJoin")) or "").strip().lower() == "true" for j in root.iter(_tag("join"))):
            warns.append(
                f"{name}: outer join ('with or without') — it returns rows with no match in the joined "
                f"object; use an inner join unless those rows are required."
            )


def check_dashboards(manifest_dir: Path, errors: list[str], warns: list[str]) -> None:
    for path in _files(manifest_dir, DASHBOARD_SUFFIXES):
        name = _stem(path, DASHBOARD_SUFFIXES)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            errors.append(f"{name}: XML parse error — {exc}")
            continue
        components = list(root.iter(_tag("dashboardGridComponents"))) or list(root.iter(_tag("components")))
        if len(components) > DASHBOARD_COMPONENT_WARN_THRESHOLD:
            warns.append(
                f"{name}: {len(components)} components (Help-only guidance of "
                f"{DASHBOARD_COMPONENT_WARN_THRESHOLD}, UNVERIFIED); consider splitting the dashboard."
            )
        if _top_text(root, "dashboardType") == "SpecifiedUser":
            warns.append(
                f"{name}: dashboardType SpecifiedUser — every viewer sees data at the running user's "
                f"access level; confirm that scope is intended."
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce report, report type and dashboard metadata for performance anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (searched recursively). Default: current directory.",
    )
    parser.add_argument("--strict", action="store_true", help="Exit 1 when any WARN is reported.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        return 1
    if not any(_files(manifest_dir, s) for s in (REPORT_SUFFIXES, REPORT_TYPE_SUFFIXES, DASHBOARD_SUFFIXES)):
        print(f"WARN: no report, report type or dashboard metadata under {manifest_dir}; nothing was checked.")
        return 0

    errors: list[str] = []
    warns: list[str] = []
    check_reports(manifest_dir, errors, warns)
    check_report_types(manifest_dir, errors, warns)
    check_dashboards(manifest_dir, errors, warns)

    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if not errors and not warns:
        print("No performance issues found in report or dashboard metadata.")
    if errors:
        return 1
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
