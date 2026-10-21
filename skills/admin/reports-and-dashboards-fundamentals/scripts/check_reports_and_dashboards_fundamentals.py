#!/usr/bin/env python3
"""Checker script for Reports and Dashboards Fundamentals skill.

Scans a Salesforce metadata project directory (Report and Dashboard
metadata) for the anti-patterns in this skill's gotchas.

Element names follow the Metadata API reference (api_meta 264):
Report.filter/criteriaItems/value and Report.timeFrameFilter (L106716,
L107292-107330, L107791-107805), Report.block (L106662), Report.buckets with
one `values` per bucket (L106668, L107017-107019), Report.format and rowLimit
(L106734, L106809), Dashboard.dashboardType (L50170-50186),
Dashboard.dashboardFilters (L50162).

Severity: ERROR = unparseable XML or a missing manifest path (exit 1 always).
Every other finding is WARN (exit 0 unless --strict): the block, bucket,
component and filter maxima are Salesforce Help figures that are not in the
audit corpus (UNVERIFIED 2026-10-21). An empty directory prints one WARN and
exits 0.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_reports_and_dashboards_fundamentals.py --manifest-dir path/to/metadata
    python3 check_reports_and_dashboards_fundamentals.py --manifest-dir path --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

NS = "{http://soap.sforce.com/2006/04/metadata}"
ABSOLUTE_DATE = re.compile(r"\b(19|20)\d{2}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")
REPORT_GLOBS = ("*.report-meta.xml", "*.report")
DASHBOARD_GLOBS = ("*.dashboard-meta.xml", "*.dashboard")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Report and Dashboard metadata for hard-coded dates, "
        "static running users, Help-only limits and folderless assets.",
    )
    parser.add_argument("--manifest-dir", default=".",
                        help="Root directory of the Salesforce metadata (default: .).")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 on WARN findings as well as ERROR findings.")
    return parser.parse_args()


def _files(root: Path, globs: tuple) -> list:
    found = set()
    for pattern in globs:
        found.update(p for p in root.rglob(pattern) if p.is_file())
    return sorted(found)


def _folderless(path: Path, top: str) -> bool:
    """MDAPI/SFDX keep each report or dashboard in <top>/<Folder>/<file>."""
    return path.parent.name == top


def check_report(path: Path, root) -> list:
    out = []
    for item in root.iter(f"{NS}criteriaItems"):
        value = item.find(f"{NS}value")
        if value is not None and value.text and ABSOLUTE_DATE.search(value.text):
            out.append(("WARN", f"{path}: hard-coded date filter '{value.text.strip()}'. "
                        "Use a relative period instead, e.g. a timeFrameFilter interval such as "
                        "INTERVAL_CURRENT (current fiscal quarter, api_meta 264 L107861)."))
    for tff in root.iter(f"{NS}timeFrameFilter"):
        interval = tff.find(f"{NS}interval")
        fixed = any((tff.findtext(f"{NS}{tag}") or "").strip() for tag in ("startDate", "endDate"))
        if interval is not None and (interval.text or "").strip() == "INTERVAL_CUSTOM" and fixed:
            # The guide's own samples use INTERVAL_CUSTOM with no dates (api_meta 264
            # L108188-108191 sample); only fixed start/end dates go stale.
            out.append(("WARN", f"{path}: timeFrameFilter uses INTERVAL_CUSTOM with fixed "
                        "start/end dates (api_meta 264 L107798-107805); it will go stale."))
    blocks = [b for b in root if b.tag == f"{NS}block"]
    if len(blocks) > 5:
        out.append(("WARN", f"{path}: joined report has {len(blocks)} blocks; Help gives a "
                    "maximum of 5 (UNVERIFIED 2026-10-21)."))
    for bucket in root.iter(f"{NS}buckets"):
        values = bucket.findall(f"{NS}values")
        if len(values) > 20:
            source = bucket.findtext(f"{NS}sourceColumnName", "unknown field")
            out.append(("WARN", f"{path}: bucket on '{source}' has {len(values)} buckets; Help "
                        "gives a maximum of 20 (UNVERIFIED 2026-10-21)."))
    fmt = root.findtext(f"{NS}format", "").strip()
    if fmt == "Tabular" and not root.findtext(f"{NS}rowLimit", "").strip():
        out.append(("WARN", f"{path}: Tabular report with no rowLimit. Help says a tabular "
                    "source needs a row limit for dashboard use (UNVERIFIED 2026-10-21)."))
    if _folderless(path, "reports") and not root.findtext(f"{NS}folderName", "").strip():
        out.append(("WARN", f"{path}: report is not inside a report folder; place it under "
                    "reports/<SharedFolder>/."))
    return out


def check_dashboard(path: Path, root) -> list:
    out = []
    dtype = root.findtext(f"{NS}dashboardType", "").strip()
    running = root.findtext(f"{NS}runningUser", "").strip()
    if dtype in ("", "SpecifiedUser") and running:
        out.append(("WARN", f"{path}: static dashboard running as '{running}'. With "
                    "SpecifiedUser every viewer sees that user's access (api_meta 264 "
                    "L50172-50175); confirm this is approved or use LoggedInUser."))
    components = len(list(root.iter(f"{NS}dashboardGridComponents"))) or len(
        [c for s in ("leftSection", "middleSection", "rightSection")
         for sec in root.findall(f"{NS}{s}") for c in sec.findall(f"{NS}components")])
    if components > 20:
        out.append(("WARN", f"{path}: {components} components; Help gives a maximum of 20 "
                    "source reports per dashboard (UNVERIFIED 2026-10-21)."))
    filters = root.findall(f"{NS}dashboardFilters")
    if len(filters) > 3:
        out.append(("WARN", f"{path}: {len(filters)} dashboard filters; Help gives a "
                    "maximum of 3 (UNVERIFIED 2026-10-21)."))
    if _folderless(path, "dashboards"):
        out.append(("WARN", f"{path}: dashboard is not inside a dashboard folder."))
    return out


def run(manifest_dir: Path) -> list:
    if not manifest_dir.is_dir():
        return [("ERROR", f"manifest directory not found: {manifest_dir}")]
    reports = _files(manifest_dir, REPORT_GLOBS)
    dashboards = _files(manifest_dir, DASHBOARD_GLOBS)
    if not reports and not dashboards:
        return [("WARN", f"{manifest_dir}: no Report or Dashboard metadata found.")]
    findings = []
    for path, checker in [(p, check_report) for p in reports] + [(p, check_dashboard) for p in dashboards]:
        try:
            root = ElementTree.parse(path).getroot()
        except ElementTree.ParseError as exc:
            findings.append(("ERROR", f"{path}: not parseable as XML: {exc}"))
            continue
        findings.extend(checker(path, root))
    return findings


def main() -> int:
    args = parse_args()
    findings = run(Path(args.manifest_dir))
    for level, message in findings:
        print(f"{level}: {message}")
    errors = sum(1 for level, _ in findings if level == "ERROR")
    warns = sum(1 for level, _ in findings if level == "WARN")
    print(f"{errors} error(s), {warns} warning(s).")
    if errors:
        return 1
    if warns and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
