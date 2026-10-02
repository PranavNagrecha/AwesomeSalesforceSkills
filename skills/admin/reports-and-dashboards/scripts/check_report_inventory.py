#!/usr/bin/env python3
"""Audit report and dashboard inventory exports and source metadata for governance risks.

Two modes:

* ``--manifest-dir <dir>`` walks a source-format tree (``force-app/main/default``) and checks the
  ``*.report-meta.xml``, ``*.dashboard-meta.xml`` and ``*.reportFolder-meta.xml`` /
  ``*.dashboardFolder-meta.xml`` files this skill produces. A folder file named
  ``<name>-meta.xml`` (no ``.reportFolder`` / ``.dashboardFolder`` type token) is also recognised
  as a folder as long as its root element is ``<ReportFolder>`` or ``<DashboardFolder>`` -- an org
  accepts that filename shape on deploy (proven live, `reports/MOCK-DEPLOY-M5.md`), so the checker
  parses the root instead of trusting the suffix alone.
* Positional paths still accept CSV inventory exports (Setup -> Reports list view export) and
  individual metadata files, for auditing an existing estate.

Both modes can be combined. Output is JSON on stdout: ``{"score", "findings", "summary"}``.

Report-body checks added 2026-09-12, all findings proven live in a `sf project deploy start
--dry-run` against the case-onboarding M5-S01 build (`reports/MOCK-DEPLOY-M5.md`, API 67.0). None
of these thresholds or names is stated in the Metadata API Developer Guide -- each is
UNVERIFIED-in-the-guide / proven-live-only, cited as such at the point of use:

* RPT-DESC-01 (ERROR)  a ``Report`` ``<description>`` over 255 characters --
  ``Value too long for field: Description maximum length is:255``.
* RPT-DESC-02 (INFO)   a ``<description>`` of 235+ characters -- headroom only, never affects
  the exit code, even under ``--strict``.
* RPT-TYPE-01 (WARN)   ``<reportType>`` matches a name proven invalid live (``Cases`` ->
  ``invalid report type``; use ``CaseList``). Extend the list only with a value proven the same
  way -- never guessed.
* RPT-GRP-01 (ERROR)   a field is both a ``groupingsDown``/``groupingsAcross`` entry and a
  ``columns`` entry -- ``You can't include groupings in the selected columns list: <field>``.
* RPT-COL-01 (INFO)    a ``criteriaItems``/``columns`` code that is not one of this report's own
  grouping fields and not in a small set of codes this project has confirmed live for the
  standard ``CaseList`` report type. Report column codes are report-type-specific (this skill's
  own rule: retrieve a working report on the same report type and copy its codes) and cannot be
  verified offline in general, so this is advisory, not a guess at right-or-wrong.

Dashboard-body check added 2026-10-02, proven live in a validate-only deploy to org `sfskills-dev`
(northwind-sales M4-S02, `reports/MOCK-DEPLOY-M4.md` run 1). The guide never marks the field
required, so this one is also proven-live-only:

* RPT-DASH-SORT-01 (HIGH)  a chart dashboard component (``componentType`` contains Chart, Bar,
  Column, Line, Pie, Donut, Funnel or Scatter -- see CHART_COMPONENT_TOKENS) with no ``<sortBy>``
  -- ``Chart dashboard components require the sortBy attribute``. Metric, Table, Gauge and the
  other non-chart types never fire.

Exit codes (``--strict`` promotes WARN-tier findings; INFO-tier findings never gate the exit
code, with or without ``--strict``):
  0 -- no ERROR/CRITICAL/HIGH-tier finding (and no MEDIUM/WARN-tier finding under ``--strict``)
  1 -- at least one ERROR/CRITICAL/HIGH-tier finding, or at least one MEDIUM/WARN-tier finding
       under ``--strict``, or the supplied ``--manifest-dir`` does not exist
A manifest dir (or path set) that exists but contains nothing to scan is not a failure -- it
exits 0 with zero findings.

Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path


CSV_SUFFIX = ".csv"
METADATA_SUFFIXES = (".dashboard-meta.xml", ".report-meta.xml")
FOLDER_SUFFIXES = (".reportFolder-meta.xml", ".dashboardFolder-meta.xml")
REPORT_TYPE_SUFFIX = ".reportType-meta.xml"
# Every typed "-meta.xml" suffix this checker already recognises by name. A bare "<name>-meta.xml"
# folder file (see is_bare_folder_meta) is only ever a file that does NOT end in one of these.
KNOWN_TYPED_META_SUFFIXES = METADATA_SUFFIXES + FOLDER_SUFFIXES + (REPORT_TYPE_SUFFIX,)
SEVERITY_WEIGHTS = {
    "CRITICAL": 20,
    "ERROR": 20,
    "HIGH": 10,
    "WARN": 10,
    "MEDIUM": 5,
    "LOW": 1,
    "REVIEW": 0,
    "INFO": 0,
}

# Exit-code tiers. ERROR-tier always fails the run; WARN-tier only fails under --strict;
# everything else (LOW, REVIEW, INFO) is advisory and never gates the exit code. CRITICAL/HIGH
# are the pre-existing severities this checker used before the RPT-* rules below were added
# (unparseable XML, a --manifest-dir that doesn't exist) and are kept at ERROR-tier since they
# are already hard, deploy-breaking conditions. MEDIUM findings (private folder, SpecifiedUser
# dashboard, Public folder, ...) are governance flags meant for review, not deploy blockers, so
# they sit at WARN-tier.
ERROR_EXIT_TIER = {"CRITICAL", "ERROR", "HIGH"}
WARN_EXIT_TIER = {"MEDIUM", "WARN"}

# RPT-DESC-01 / RPT-DESC-02. Not documented in the Metadata API Developer Guide's Report field
# table (grep of api_meta.txt for "Report" + "description" turns up no Limit: clause) -- proven
# live instead: `sf project deploy start --dry-run` against the case-onboarding M5-S01 build
# rejected a Report with `Value too long for field: Description maximum length is:255`
# (reports/MOCK-DEPLOY-M5.md, F-49). 235 is headroom advisory only, chosen the same way the
# admin/custom-permissions and admin/object-creation-and-design checkers pick a headroom
# threshold below their own documented ceilings.
RPT_DESC_MAX_LEN = 255
RPT_DESC_WARN_LEN = 235

# RPT-TYPE-01. Standard report type API names proven invalid by the same live dry-run --
# `reportType` `Cases` was rejected with `invalid report type`; `CaseList` was accepted
# (reports/MOCK-DEPLOY-M5.md, F-50). Not stated anywhere in the Metadata API Developer Guide.
# Extend this dict only with a value proven the same way -- never guessed by analogy.
KNOWN_INVALID_REPORT_TYPES = {
    "Cases": "CaseList",
}

# RPT-COL-01. Report column codes this project has confirmed live on the standard `CaseList`
# report type only (reports/MOCK-DEPLOY-M5.md, F-50/F-51 operator probes: `OWNER` accepted where
# `USERS.NAME` and `OWNER_NAME` were rejected; `STATUS` and `CREATED_DATE` are the filter columns
# in the same accepted report). This is NOT a claim these codes work on every report type --
# column codes are report-type-specific (see this skill's own "Retrieve before you write" rule,
# SKILL.md Recommended Workflow step 3) -- it exists only so this checker doesn't re-flag codes
# already proven for this specific report type.
KNOWN_GOOD_COLUMN_CODES = {"STATUS", "PRIORITY", "OWNER", "CREATED_DATE"}

# Report `scope` values that consider every record the running user can see, rather than a
# narrower "mine"/"my team" slice. Metadata API Developer Guide, Report.scope: valid values
# depend on the report type; the guide's own sample report uses `organization`, and the field
# description gives MyAccounts / MyTeamsAccounts / AllAccounts as the Accounts-report values.
ORG_WIDE_SCOPES = {"organization", "everything", "allaccounts"}

# RPT-DASH-SORT-01. The org refuses a chart component with no <sortBy>: "Chart dashboard
# components require the sortBy attribute" (org sfskills-dev, validate-only deploy,
# 2026-10-02T17:53Z, .sfskills/builds/northwind-sales/reports/MOCK-DEPLOY-M4.md run 1). The
# Metadata API Developer Guide (v67.0, Summer '26, DashboardComponent) describes sortBy only as
# "The sort option for the dashboard component" and never marks it required, so this is
# proven-live-only. Every chart in the guide's own Dashboard samples does carry one.
# A componentType is a chart when it contains one of these tokens (case-sensitive). Against the
# guide's DashboardComponentType enumeration that selects exactly these 21 values: Bar, BarGrouped,
# BarStacked, BarStacked100, Column, ColumnGrouped, ColumnLine, ColumnLineGrouped,
# ColumnLineStacked, ColumnLineStacked100, ColumnStacked, ColumnStacked100, Donut, Funnel, Line,
# LineCumulative, LineGrouped, LineGroupedCumulative, Pie, Scatter, ScatterGrouped. The other 10
# never fire: FlexTable, Gauge, Image, LightningWebComponent, Metric, PulseMetricCard, RichText,
# SControl, Table, VisualforcePage. "Chart" matches no value today; it is kept so a future
# *Chart value is caught instead of skipped.
CHART_COMPONENT_TOKENS = ("Chart", "Bar", "Column", "Line", "Pie", "Donut", "Funnel", "Scatter")
# Classic sections hold each component in <components> (DashboardComponentSection); the Lightning
# grid holds one in each <dashboardComponent> (DashboardGridComponent). "dashboardComponents" is
# not an element name in the guide; it is accepted so a hand-written variant is not skipped.
DASHBOARD_COMPONENT_TAGS = {"components", "dashboardComponent", "dashboardComponents"}


def is_chart_component_type(component_type: str) -> bool:
    return any(token in component_type for token in CHART_COMPONENT_TOKENS)


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, child_name: str) -> str:
    for child in element:
        if local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return ""


def first_child(element: ET.Element, *child_names: str) -> ET.Element | None:
    """Return the first direct child matching any of ``child_names``.

    Deliberately avoids ``element.find(a) or element.find(b)``: an ElementTree Element with no
    sub-elements is falsy, so the ``or`` idiom silently discards a leaf match.
    """
    wanted = set(child_names)
    for child in element:
        if local_name(child.tag) in wanted:
            return child
    return None


def descendants(element: ET.Element, name: str) -> list[ET.Element]:
    return [node for node in element.iter() if local_name(node.tag) == name]


def direct_children(element: ET.Element, name: str) -> list[ET.Element]:
    """Return every direct child matching ``name`` (unlike ``first_child``, all of them)."""
    return [child for child in element if local_name(child.tag) == name]


def is_bare_folder_meta(path: Path) -> bool:
    """True for a ``<name>-meta.xml`` file whose root element is ReportFolder/DashboardFolder.

    An org accepts a report/dashboard folder deployed under this filename shape -- no
    ``.reportFolder`` / ``.dashboardFolder`` type token at all -- proven live in the
    case-onboarding M5-S01 dry-run (`reports/MOCK-DEPLOY-M5.md`). The checker previously
    recognised folders by suffix only (FOLDER_SUFFIXES), which missed this shape entirely.
    Every already-typed "-meta.xml" suffix is excluded first so a report, dashboard or report
    type file is never re-parsed and mis-classified here.
    """
    name = path.name
    if not name.endswith("-meta.xml") or name.endswith(KNOWN_TYPED_META_SUFFIXES):
        return False
    root = parse_xml(path)
    if root is None:
        return False
    return local_name(root.tag) in ("ReportFolder", "DashboardFolder")


def in_private_folder(path: Path) -> bool:
    """True when the metadata sits in a Salesforce private report/dashboard folder.

    Only the path parts *below* the reports/ or dashboards/ directory are considered, so an
    absolute path that merely happens to contain "private" (macOS resolves /tmp to /private/tmp)
    doesn't produce a finding.
    """
    parts = [part.lower() for part in path.parts]
    for anchor in ("reports", "dashboards"):
        if anchor in parts:
            tail = parts[parts.index(anchor) + 1 :]
            if any("private" in part or part.startswith("my_personal") for part in tail):
                return True
    return False


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def parse_date(value: str) -> date | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    formats = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%m/%d/%Y %H:%M")
    for candidate in formats:
        try:
            return datetime.strptime(cleaned, candidate).date()
        except ValueError:
            continue
    return None


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and (
                    candidate.name.endswith(CSV_SUFFIX)
                    or candidate.name.endswith(METADATA_SUFFIXES)
                    or candidate.name.endswith(FOLDER_SUFFIXES)
                    or is_bare_folder_meta(candidate)
                ):
                    files.append(candidate)
        elif path.is_file() and (
            path.name.endswith(CSV_SUFFIX)
            or path.name.endswith(METADATA_SUFFIXES)
            or path.name.endswith(FOLDER_SUFFIXES)
            or is_bare_folder_meta(path)
        ):
            files.append(path)
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str, strict: bool = False) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))

    error_count = sum(1 for item in normalized if item["severity"] in ERROR_EXIT_TIER)
    warn_count = sum(1 for item in normalized if item["severity"] in WARN_EXIT_TIER)
    info_count = len(normalized) - error_count - warn_count

    # Single-line, literal-severity prints (not a variable-interpolated level) so a log grep for
    # "ERROR:" / "WARN:" / "INFO:" always finds the right line.
    if error_count:
        print(f"ERROR: {error_count} error-tier finding(s) detected; see findings above", file=sys.stderr)
    elif strict and warn_count:
        print(f"WARN: {warn_count} warn-tier finding(s) detected; failing under --strict", file=sys.stderr)
    elif warn_count:
        print(f"WARN: {warn_count} warn-tier finding(s) detected; pass --strict to fail on these", file=sys.stderr)
    elif normalized:
        print(f"INFO: {info_count} info-tier finding(s) detected; advisory only, never fails the run", file=sys.stderr)

    if error_count:
        return 1
    if strict and warn_count:
        return 1
    return 0


def lookup(row: dict[str, str], *candidates: str) -> str:
    normalized = {key.strip().lower(): value for key, value in row.items()}
    for candidate in candidates:
        value = normalized.get(candidate.lower())
        if value:
            return value
    return ""


def audit_csv(path: Path) -> list[str]:
    findings: list[str] = []
    today = date.today()

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            folder = lookup(row, "folder", "folder name", "report folder", "dashboard folder")
            item_type = lookup(row, "type", "item type").lower()
            name = lookup(row, "name", "report name", "dashboard name") or "<unnamed item>"
            running_user = lookup(row, "running user", "dashboard running user")

            if "private" in folder.lower():
                findings.append(f"MEDIUM {path}::{name}: item is in a private folder `{folder}`")

            if "dashboard" in item_type and running_user and "logged" not in running_user.lower():
                findings.append(
                    f"MEDIUM {path}::{name}: dashboard runs as specific user `{running_user}`"
                )

            last_run = parse_date(lookup(row, "last run date", "last run"))
            last_viewed = parse_date(lookup(row, "last viewed date", "last viewed"))
            last_modified = parse_date(lookup(row, "last modified date", "last modified"))

            if "dashboard" in item_type and last_viewed and (today - last_viewed).days > 60:
                findings.append(
                    f"REVIEW {path}::{name}: dashboard not viewed in {(today - last_viewed).days} days"
                )

            if "report" in item_type:
                if last_run and (today - last_run).days > 90:
                    findings.append(
                        f"REVIEW {path}::{name}: report not run in {(today - last_run).days} days"
                    )
                if last_modified and (today - last_modified).days > 180:
                    findings.append(
                        f"REVIEW {path}::{name}: report not modified in {(today - last_modified).days} days"
                    )

    return findings


def audit_metadata(path: Path) -> list[str]:
    """Audit a single metadata file supplied as a positional path.

    Delegates to the same checks the --manifest-dir walk uses, so a dashboard is judged on
    `dashboardType` rather than on the mere presence of `runningUser`. The report-type check is
    skipped here because a single file carries no view of the surrounding tree.
    """
    findings: list[str] = []

    if path.name.endswith(".dashboard-meta.xml"):
        findings.extend(check_dashboard_source(path))
    elif path.name.endswith(".report-meta.xml"):
        findings.extend(check_report_source(path, set()))
    elif path.name.endswith(FOLDER_SUFFIXES) or is_bare_folder_meta(path):
        findings.extend(check_folder_source(path))

    return findings


# ---------------------------------------------------------------------------
# Source-tree checks (--manifest-dir)
# ---------------------------------------------------------------------------


def check_report_source(path: Path, known_report_types: set[str]) -> list[str]:
    """Checks on one *.report-meta.xml file."""
    findings: list[str] = []
    root = parse_xml(path)
    if root is None:
        return [f"HIGH {path}: cannot parse report XML"]

    name = child_text(root, "name") or path.stem

    if in_private_folder(path):
        findings.append(
            f"MEDIUM {path}::{name}: report sits in a private folder - only its owner can open "
            "it, and it is lost when that user is deactivated"
        )

    # Check 1 - unbounded report. `filter/criteriaItems`, `crossFilters` and `timeFrameFilter`
    # are three independent narrowing mechanisms (Metadata API Developer Guide, Report). A report
    # with none of them reads every row the running user can see.
    filter_el = first_child(root, "filter")
    has_criteria = bool(descendants(filter_el, "criteriaItems")) if filter_el is not None else False
    has_timeframe = first_child(root, "timeFrameFilter") is not None
    has_cross_filter = first_child(root, "crossFilters") is not None
    has_row_limit = first_child(root, "rowLimit") is not None
    scope = child_text(root, "scope")

    if not (has_criteria or has_timeframe or has_cross_filter or has_row_limit):
        if scope and scope.lower() in ORG_WIDE_SCOPES:
            findings.append(
                f"LOW {path}::{name}: no filter, timeFrameFilter, crossFilters or rowLimit, and "
                f"scope is `{scope}` - this report reads the full table on every run"
            )
        else:
            findings.append(
                f"INFO {path}::{name}: no filter, timeFrameFilter, crossFilters or rowLimit - "
                "the result set is bounded only by the running user's record access"
            )

    # Check 2 - report type not present in this deployment.
    report_type = child_text(root, "reportType") or child_text(root, "reportTypeApiName")
    if report_type and known_report_types and report_type not in known_report_types:
        findings.append(
            f"REVIEW {path}::{name}: reportType `{report_type}` has no "
            f"{report_type}{REPORT_TYPE_SUFFIX} in this tree - confirm it is a standard report "
            "type, or add the ReportType to the deployment so it lands before the report"
        )

    # RPT-DESC-01 / RPT-DESC-02 - description length. Not documented in the Metadata API
    # Developer Guide's Report field table; proven live only (see module docstring, F-49).
    description = child_text(root, "description")
    if description:
        if len(description) > RPT_DESC_MAX_LEN:
            findings.append(
                f"ERROR {path}::{name}: RPT-DESC-01 description is {len(description)} chars - "
                f"proven live: `Value too long for field: Description maximum length is:255` "
                f"(reports/MOCK-DEPLOY-M5.md F-49) - the deploy will be rejected"
            )
        elif len(description) >= RPT_DESC_WARN_LEN:
            findings.append(
                f"INFO {path}::{name}: RPT-DESC-02 description is {len(description)} chars, "
                f"only {RPT_DESC_MAX_LEN - len(description)} of headroom before the "
                f"{RPT_DESC_MAX_LEN}-char limit (F-49) - never fails the run, even under --strict"
            )

    # RPT-TYPE-01 - reportType proven invalid live (F-50). Extend KNOWN_INVALID_REPORT_TYPES
    # only with a value proven the same way.
    if report_type in KNOWN_INVALID_REPORT_TYPES:
        suggestion = KNOWN_INVALID_REPORT_TYPES[report_type]
        findings.append(
            f"WARN {path}::{name}: RPT-TYPE-01 reportType `{report_type}` was rejected live "
            f"with `invalid report type` (reports/MOCK-DEPLOY-M5.md F-50) - use `{suggestion}` "
            "instead"
        )

    # RPT-GRP-01 - a field cannot be both a groupingsDown/groupingsAcross entry and a columns
    # entry. Proven live: `You can't include groupings in the selected columns list: PRIORITY`
    # (reports/MOCK-DEPLOY-M5.md F-50).
    column_fields = {
        child_text(column, "field")
        for column in direct_children(root, "columns")
        if child_text(column, "field")
    }
    grouping_fields = {
        child_text(grouping, "field")
        for grouping_tag in ("groupingsDown", "groupingsAcross")
        for grouping in direct_children(root, grouping_tag)
        if child_text(grouping, "field")
    }
    for field in sorted(column_fields & grouping_fields):
        findings.append(
            f"ERROR {path}::{name}: RPT-GRP-01 `{field}` is both a groupingsDown/"
            f"groupingsAcross field and a columns entry - proven live: `You can't include "
            f"groupings in the selected columns list: {field}` (reports/MOCK-DEPLOY-M5.md "
            "F-50) - drop it from one of the two"
        )

    # RPT-COL-01 - a criteriaItems/columns code that isn't one of this report's own grouping
    # fields and isn't in the small set of codes proven live for CaseList. Column codes are
    # report-type-specific (this skill's own "retrieve before you write" rule) and cannot be
    # verified offline in general, so this is advisory (INFO), never an ERROR or WARN.
    known_codes = grouping_fields | KNOWN_GOOD_COLUMN_CODES
    flagged_codes: set[str] = set()
    code_sources: list[tuple[str, str]] = [
        ("columns", code) for code in sorted(column_fields)  # deterministic finding order
    ]
    if filter_el is not None:
        code_sources.extend(
            ("filter/criteriaItems", child_text(item, "column"))
            for item in descendants(filter_el, "criteriaItems")
            if child_text(item, "column")
        )
    for cross_filter in direct_children(root, "crossFilters"):
        code_sources.extend(
            ("crossFilters/criteriaItems", child_text(item, "column"))
            for item in descendants(cross_filter, "criteriaItems")
            if child_text(item, "column")
        )
    for source, code in code_sources:
        if code in known_codes or code in flagged_codes:
            continue
        flagged_codes.add(code)
        findings.append(
            f"INFO {path}::{name}: RPT-COL-01 `{code}` ({source}) is not one of this report's "
            "own grouping fields or a code already confirmed for this report type - column "
            "codes are report-type-specific and cannot be verified offline; harvest it from a "
            "retrieve of a working report on the same reportType before deploying"
        )

    return findings


def check_dashboard_source(path: Path) -> list[str]:
    """Checks on one *.dashboard-meta.xml file."""
    findings: list[str] = []
    root = parse_xml(path)
    if root is None:
        return [f"HIGH {path}: cannot parse dashboard XML"]

    title = child_text(root, "title") or path.stem
    if in_private_folder(path):
        findings.append(
            f"MEDIUM {path}::{title}: dashboard sits in a private folder - only its owner can "
            "open it, and it is lost when that user is deactivated"
        )
    dashboard_type = child_text(root, "dashboardType")
    running_user = child_text(root, "runningUser")

    # Check 3 - running-user posture. `dashboardType`, not the presence of `runningUser`, is the
    # security decision (Metadata API Developer Guide, Dashboard.dashboardType). SpecifiedUser
    # shows one user's data to every viewer regardless of their own security settings.
    if dashboard_type == "SpecifiedUser":
        if running_user:
            findings.append(
                f"MEDIUM {path}::{title}: dashboardType is SpecifiedUser running as "
                f"`{running_user}` - every viewer sees that user's data, not their own"
            )
        else:
            findings.append(
                f"MEDIUM {path}::{title}: dashboardType is SpecifiedUser with no runningUser - "
                "on deploy the field is populated with the deploying user's username"
            )
    elif running_user and dashboard_type != "LoggedInUser":
        findings.append(
            f"MEDIUM {path}::{title}: runningUser `{running_user}` is set but dashboardType is "
            f"`{dashboard_type or 'unset'}` - state dashboardType explicitly"
        )

    # Every report-based component must declare a dashboardFilterColumns entry for each dashboard
    # filter it should respond to (Metadata API Developer Guide, DashboardComponent).
    filter_count = len(descendants(root, "dashboardFilters"))
    if filter_count:
        for component in descendants(root, "components"):
            if first_child(component, "report") is None:
                continue
            component_title = child_text(component, "title") or child_text(component, "header") or "<untitled>"
            declared = len(descendants(component, "dashboardFilterColumns"))
            if declared < filter_count:
                findings.append(
                    f"MEDIUM {path}::{title}: component `{component_title}` declares {declared} "
                    f"dashboardFilterColumns for {filter_count} dashboard filter(s) - the "
                    "undeclared filters render but do not affect this component"
                )

    # RPT-DASH-SORT-01 / RPT-DASH-AXIS-01 - a chart component with no <sortBy> or no <chartAxisRange> is refused live.
    # Proven live only; see CHART_COMPONENT_TOKENS for the source and the types that count.
    for component in root.iter():
        if local_name(component.tag) not in DASHBOARD_COMPONENT_TAGS:
            continue
        component_type = child_text(component, "componentType")
        if not component_type or not is_chart_component_type(component_type):
            continue
        label = child_text(component, "header") or child_text(component, "report") or "<untitled>"
        if not child_text(component, "sortBy"):
            findings.append(
                f"HIGH {path}: dashboard component '{label}' of type {component_type} has no "
                "<sortBy> \u2014 the platform refuses chart components without it (\"Chart dashboard "
                "components require the sortBy attribute\", org-verified 2026-10-02)"
            )
        # RPT-DASH-AXIS-01 - the org names the next missing attribute on the next run (northwind
        # M4 run 2): "Chart dashboard components require the chartAxisRange attribute".
        if not child_text(component, "chartAxisRange"):
            findings.append(
                f"HIGH {path}: dashboard component '{label}' of type {component_type} has no "
                "<chartAxisRange> \u2014 the platform refuses chart components without it (\"Chart "
                "dashboard components require the chartAxisRange attribute\", org-verified 2026-10-02)"
            )

    return findings


def check_folder_source(path: Path) -> list[str]:
    """Checks on one *.reportFolder-meta.xml / *.dashboardFolder-meta.xml file."""
    findings: list[str] = []
    root = parse_xml(path)
    if root is None:
        return [f"HIGH {path}: cannot parse folder XML"]

    folder_name = child_text(root, "name") or path.name.split(".")[0]
    access_type = child_text(root, "accessType")

    # Check 4 - Public folder access. Metadata API Developer Guide, Folder.accessType:
    # Public is "accessible by all users, including portal users"; PublicInternal excludes them.
    if access_type == "Public":
        findings.append(
            f"MEDIUM {path}::{folder_name}: accessType is Public - accessible by all users "
            "INCLUDING portal users. PublicInternal excludes portal users"
        )
    elif not access_type:
        findings.append(
            f"LOW {path}::{folder_name}: no accessType set - accessType is a required field on "
            "the Folder metadata type"
        )

    if access_type == "Shared" and not descendants(root, "folderShares"):
        findings.append(
            f"LOW {path}::{folder_name}: accessType is Shared but no folderShares are defined - "
            "nobody but the owner and users with administrative permissions can open it"
        )

    return findings


def audit_manifest_dir(manifest_dir: Path) -> tuple[list[str], int]:
    """Walk a source-format tree and run the metadata checks. Returns (findings, files scanned)."""
    findings: list[str] = []

    known_report_types = {
        path.name[: -len(REPORT_TYPE_SUFFIX)]
        for path in manifest_dir.rglob(f"*{REPORT_TYPE_SUFFIX}")
    }

    scanned = len(known_report_types)

    for path in sorted(manifest_dir.rglob("*.report-meta.xml")):
        scanned += 1
        findings.extend(check_report_source(path, known_report_types))

    for path in sorted(manifest_dir.rglob("*.dashboard-meta.xml")):
        scanned += 1
        findings.extend(check_dashboard_source(path))

    for suffix in FOLDER_SUFFIXES:
        for path in sorted(manifest_dir.rglob(f"*{suffix}")):
            scanned += 1
            findings.extend(check_folder_source(path))

    # Bare "<name>-meta.xml" folder files - see is_bare_folder_meta.
    for path in sorted(manifest_dir.rglob("*-meta.xml")):
        if not is_bare_folder_meta(path):
            continue
        scanned += 1
        findings.extend(check_folder_source(path))

    return findings, scanned


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan report/dashboard source metadata or inventory exports for governance risks."
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=None,
        help="Source-format directory to walk (for example force-app/main/default)",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="CSV inventory exports, individual metadata files, or directories",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN-tier findings (e.g. RPT-TYPE-01) too. INFO-tier findings never "
        "affect the exit code, with or without --strict.",
    )
    args = parser.parse_args()

    findings: list[str] = []
    scanned = 0

    if args.manifest_dir is not None:
        if not args.manifest_dir.is_dir():
            return emit_result(
                [f"ERROR {args.manifest_dir}: --manifest-dir is not a directory"],
                "Scanned 0 file(s); the supplied --manifest-dir does not exist.",
                args.strict,
            )
        manifest_findings, manifest_scanned = audit_manifest_dir(args.manifest_dir)
        findings.extend(manifest_findings)
        scanned += manifest_scanned

    if args.paths:
        files = iter_files([Path(value) for value in args.paths])
        scanned += len(files)
        for path in files:
            if path.name.endswith(CSV_SUFFIX):
                findings.extend(audit_csv(path))
            else:
                findings.extend(audit_metadata(path))

    if args.manifest_dir is None and not args.paths:
        parser.error("supply --manifest-dir, one or more paths, or both")

    if scanned == 0:
        # A manifest dir (or path set) that exists but has nothing to scan is not a failure --
        # e.g. an early milestone with no reports built yet. Only an actually-missing
        # --manifest-dir (handled above) is an ERROR.
        return emit_result(
            [],
            "Scanned 0 report/dashboard file(s); nothing matched the supplied inputs.",
            args.strict,
        )

    summary = (
        f"Scanned {scanned} report/dashboard file(s); {len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary, args.strict)


if __name__ == "__main__":
    sys.exit(main())
