#!/usr/bin/env python3
"""Audit report and dashboard inventory exports and source metadata for governance risks.

Two modes:

* ``--manifest-dir <dir>`` walks a source-format tree (``force-app/main/default``) and checks the
  ``*.report-meta.xml``, ``*.dashboard-meta.xml`` and ``*.reportFolder-meta.xml`` /
  ``*.dashboardFolder-meta.xml`` files this skill produces.
* Positional paths still accept CSV inventory exports (Setup -> Reports list view export) and
  individual metadata files, for auditing an existing estate.

Both modes can be combined. Output is JSON on stdout: ``{"score", "findings", "summary"}``.
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
SEVERITY_WEIGHTS = {
    "CRITICAL": 20,
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 1,
    "REVIEW": 0,
    "INFO": 0,
}

# Report `scope` values that consider every record the running user can see, rather than a
# narrower "mine"/"my team" slice. Metadata API Developer Guide, Report.scope: valid values
# depend on the report type; the guide's own sample report uses `organization`, and the field
# description gives MyAccounts / MyTeamsAccounts / AllAccounts as the Accounts-report values.
ORG_WIDE_SCOPES = {"organization", "everything", "allaccounts"}


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
                ):
                    files.append(candidate)
        elif path.is_file() and (
            path.name.endswith(CSV_SUFFIX)
            or path.name.endswith(METADATA_SUFFIXES)
            or path.name.endswith(FOLDER_SUFFIXES)
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


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


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
    elif path.name.endswith(FOLDER_SUFFIXES):
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
    args = parser.parse_args()

    findings: list[str] = []
    scanned = 0

    if args.manifest_dir is not None:
        if not args.manifest_dir.is_dir():
            return emit_result(
                [f"HIGH {args.manifest_dir}: --manifest-dir is not a directory"],
                "Scanned 0 file(s); the supplied --manifest-dir does not exist.",
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
        return emit_result(
            ["HIGH no report/dashboard metadata or CSV exports found"],
            "Scanned 0 report/dashboard file(s); nothing matched the supplied inputs.",
        )

    summary = (
        f"Scanned {scanned} report/dashboard file(s); {len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
