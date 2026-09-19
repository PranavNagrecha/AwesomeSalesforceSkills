#!/usr/bin/env python3
"""Checker for the opportunity-management skill.

Validates the metadata this skill produces -- the Opportunity stage value set,
the sales processes (``BusinessProcess``) built on top of it, the record types
that bind them, the ``PathAssistant`` records layered on those record types, and
``Opportunity.settings`` -- for the failure modes documented in
``references/gotchas.md``.

Reads both project shapes:

* MDAPI      ``objects/Opportunity.object`` with nested ``<businessProcesses>``
  and ``<recordTypes>``
* DX source  ``objects/Opportunity/businessProcesses/*.businessProcess-meta.xml``
  and ``objects/Opportunity/recordTypes/*.recordType-meta.xml``

Checks
------
ERROR  A stage's ``forecastCategory`` is not a member of the metadata
       ``ForecastCategories`` enumeration (api_meta.txt:47578-47586). The SOQL
       vocabulary is different -- ``Commit`` is ``Forecast`` in metadata -- so
       this catches values transcribed from a SOQL export (Gotcha 13).
ERROR  A stage has ``won`` true but ``closed`` false.
ERROR  Two business processes on Opportunity share a ``fullName``.
ERROR  Two ``PathAssistant`` files target the same entity + record type. Only one
       path may exist per record type per object (api_meta.txt:94496).
ERROR  A business process exposes no won stage, or no closed stage, when the
       stage value set is present in the tree to resolve the flags against.
WARN   A stage is missing ``forecastCategory`` or ``probability``.
WARN   A business process lists a value that is not in the stage value set.
WARN   An active Opportunity record type has no ``businessProcess``, or names one
       that is not in the tree.
WARN   A ``PathAssistant`` names a ``recordTypeName`` that is not in the tree.
WARN   A ``PathAssistant`` step's ``picklistValueName`` is not a value of the
       business process bound to that path's record type.
INFO   A business process could not be checked for won/closed coverage because
       the stage value set is not in the tree.
INFO   Team selling or a split-backed forecast type is present -- a reminder that
       splits enablement and split types are Setup-only and cannot ship in this
       manifest (Gotcha 11).

Stdlib only. Exits 1 when any ERROR or WARN is found; ``--strict`` also fails on
INFO.

Usage:
    python3 check_opportunity_management.py --manifest-dir force-app/main/default
    python3 check_opportunity_management.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

# api_meta.txt:47578-47586 -- the ForecastCategories enumeration accepted by the
# forecastCategory element on StandardValue / CustomValue. NOT the SOQL vocabulary.
VALID_METADATA_FORECAST_CATEGORIES = {
    "Omitted",
    "Pipeline",
    "BestCase",
    "Forecast",
    "Closed",
}

# object_reference.txt:195499-195505 -- what SOQL and the UI return instead.
# Mapped back to the metadata token so the finding can name the fix.
SOQL_TO_METADATA_CATEGORY = {
    "Best Case": "BestCase",
    "Commit": "Forecast",
    "Most Likely": None,  # readable in SOQL, no metadata token exists
    "Pipeline": "Pipeline",
    "Closed": "Closed",
    "Omitted": "Omitted",
}

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"
SEVERITY_ORDER = {ERROR: 0, WARN: 1, INFO: 2}


class Finding:
    """One check result."""

    def __init__(self, severity: str, source: str, message: str) -> None:
        self.severity = severity
        self.source = source
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity}: [{self.source}] {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Opportunity stage, sales process, record type, Path and settings "
            "metadata for the failure modes in the opportunity-management skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata tree (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat INFO findings as failures too.",
    )
    return parser.parse_args()


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def _child(element: ET.Element, name: str) -> ET.Element | None:
    """Return the first child with this tag, or None.

    A leaf Element is falsy, so never chain these with ``or``; always test
    ``is not None``.
    """
    return element.find(_tag(name))


def _text(element: ET.Element, name: str) -> str:
    """Return the stripped text of a child element, or an empty string."""
    child = _child(element, name)
    if child is None:
        return ""
    if child.text is None:
        return ""
    return child.text.strip()


def _bool(element: ET.Element, name: str, default: bool = False) -> bool:
    raw = _text(element, name)
    if not raw:
        return default
    return raw.lower() == "true"


def _parse(path: Path, findings: list[Finding]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(Finding(ERROR, path.name, f"XML will not parse: {exc}"))
        return None


def _object_files(manifest_dir: Path) -> list[Path]:
    """MDAPI-form Opportunity object files, if the tree uses that shape."""
    candidates = [
        manifest_dir / "objects" / "Opportunity.object",
        manifest_dir / "objects" / "Opportunity.object-meta.xml",
        manifest_dir / "objects" / "Opportunity" / "Opportunity.object-meta.xml",
    ]
    return [p for p in candidates if p.is_file()]


# ---------------------------------------------------------------------------
# Collectors
# ---------------------------------------------------------------------------


def collect_stages(manifest_dir: Path, findings: list[Finding]) -> dict[str, dict]:
    """Return {stage fullName: {'won':bool,'closed':bool,'category':str,'active':bool}}.

    Empty dict means the stage value set is not in this tree, which downgrades
    several downstream checks from ERROR to INFO.
    """
    path = (
        manifest_dir
        / "standardValueSets"
        / "OpportunityStage.standardValueSet-meta.xml"
    )
    if not path.is_file():
        return {}

    root = _parse(path, findings)
    if root is None:
        return {}

    stages: dict[str, dict] = {}
    for value in root.findall(_tag("standardValue")):
        name = _text(value, "fullName")
        if not name:
            continue
        category = _text(value, "forecastCategory")
        has_probability = _child(value, "probability") is not None
        stages[name] = {
            "won": _bool(value, "won"),
            "closed": _bool(value, "closed"),
            "category": category,
            "active": _bool(value, "isActive", default=True),
            "has_probability": has_probability,
        }

    if not stages:
        findings.append(
            Finding(
                WARN,
                path.name,
                "No <standardValue> entries found. A StandardValueSet deploy "
                "must contain at least one picklist value (api_meta.txt:130771-130772).",
            )
        )
    return stages


def _default_values(element: ET.Element) -> list[str]:
    """fullNames of <values> entries carrying <default>true</default>.

    OM-BP-DEFAULT-01. Opportunity is the only object the org has judged; see
    check_business_processes.
    """
    defaults: list[str] = []
    for value in element.findall(_tag("values")):
        if _bool(value, "default", False):
            defaults.append(_text(value, "fullName") or "(unnamed value)")
    return defaults


def collect_business_processes(
    manifest_dir: Path, findings: list[Finding]
) -> dict[str, dict]:
    """Return {process fullName: {'values':[str], 'active':bool, 'source':str}}."""
    processes: dict[str, dict] = {}

    def add(
        name: str,
        values: list[str],
        active: bool,
        source: str,
        defaults: list[str] | None = None,
    ) -> None:
        if not name:
            return
        if name in processes:
            findings.append(
                Finding(
                    ERROR,
                    source,
                    f"Duplicate Opportunity business process '{name}' -- also defined in "
                    f"'{processes[name]['source']}'. A business process fullName must be "
                    "unique per object; the second definition wins silently on deploy.",
                )
            )
            return
        processes[name] = {
            "values": values,
            "active": active,
            "source": source,
            "defaults": list(defaults or []),
        }

    def read_element(element: ET.Element, source: str) -> None:
        values = [
            _text(v, "fullName")
            for v in element.findall(_tag("values"))
            if _text(v, "fullName")
        ]
        defaults = _default_values(element)
        add(
            _text(element, "fullName"),
            values,
            _bool(element, "isActive", True),
            source,
            defaults,
        )

    # DX decomposed form
    bp_dir = manifest_dir / "objects" / "Opportunity" / "businessProcesses"
    if bp_dir.is_dir():
        for bp_file in sorted(bp_dir.glob("*.businessProcess-meta.xml")):
            root = _parse(bp_file, findings)
            if root is None:
                continue
            values = [
                _text(v, "fullName")
                for v in root.findall(_tag("values"))
                if _text(v, "fullName")
            ]
            # A decomposed file may omit fullName; the file name carries it.
            name = _text(root, "fullName") or bp_file.name.split(
                ".businessProcess-meta.xml"
            )[0]
            add(
                name,
                values,
                _bool(root, "isActive", True),
                bp_file.name,
                _default_values(root),
            )

    # MDAPI nested form
    for obj_file in _object_files(manifest_dir):
        root = _parse(obj_file, findings)
        if root is None:
            continue
        for element in root.findall(_tag("businessProcesses")):
            read_element(element, obj_file.name)

    return processes


def collect_record_types(
    manifest_dir: Path, findings: list[Finding]
) -> dict[str, dict]:
    """Return {record type fullName: {'active':bool, 'process':str, 'source':str}}."""
    record_types: dict[str, dict] = {}

    def add(name: str, active: bool, process: str, source: str) -> None:
        if name:
            record_types[name] = {
                "active": active,
                "process": process,
                "source": source,
            }

    rt_dir = manifest_dir / "objects" / "Opportunity" / "recordTypes"
    if rt_dir.is_dir():
        for rt_file in sorted(rt_dir.glob("*.recordType-meta.xml")):
            root = _parse(rt_file, findings)
            if root is None:
                continue
            name = _text(root, "fullName") or rt_file.name.split(
                ".recordType-meta.xml"
            )[0]
            add(
                name,
                _bool(root, "active", True),
                _text(root, "businessProcess"),
                rt_file.name,
            )

    for obj_file in _object_files(manifest_dir):
        root = _parse(obj_file, findings)
        if root is None:
            continue
        for element in root.findall(_tag("recordTypes")):
            add(
                _text(element, "fullName"),
                _bool(element, "active", True),
                _text(element, "businessProcess"),
                obj_file.name,
            )

    return record_types


def collect_paths(manifest_dir: Path, findings: list[Finding]) -> list[dict]:
    """Return one dict per Opportunity PathAssistant in the tree."""
    paths: list[dict] = []
    path_dir = manifest_dir / "pathAssistants"
    if not path_dir.is_dir():
        return paths

    for path_file in sorted(path_dir.glob("*.pathAssistant-meta.xml")):
        root = _parse(path_file, findings)
        if root is None:
            continue
        entity = _text(root, "entityName")
        if entity and entity != "Opportunity":
            continue
        steps = [
            _text(step, "picklistValueName")
            for step in root.findall(_tag("pathAssistantSteps"))
        ]
        paths.append(
            {
                "file": path_file.name,
                "entity": entity or "Opportunity",
                "field": _text(root, "fieldName"),
                "record_type": _text(root, "recordTypeName"),
                "active": _bool(root, "active", True),
                "steps": [s for s in steps if s],
            }
        )
    return paths


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_stage_values(stages: dict[str, dict], findings: list[Finding]) -> None:
    source = "OpportunityStage.standardValueSet-meta.xml"
    for name, stage in sorted(stages.items()):
        if not stage["active"]:
            continue

        category = stage["category"]
        if category and category not in VALID_METADATA_FORECAST_CATEGORIES:
            hint = ""
            if category in SOQL_TO_METADATA_CATEGORY:
                metadata_token = SOQL_TO_METADATA_CATEGORY[category]
                if metadata_token:
                    hint = (
                        f" '{category}' is the SOQL/UI label; the metadata token is "
                        f"'{metadata_token}'."
                    )
                else:
                    hint = (
                        f" '{category}' is a valid ForecastCategoryName in SOQL but has "
                        "no metadata token -- it cannot be set through the value set."
                    )
            findings.append(
                Finding(
                    ERROR,
                    source,
                    f"Stage '{name}': forecastCategory '{category}' is not in the "
                    "metadata ForecastCategories enumeration "
                    f"({', '.join(sorted(VALID_METADATA_FORECAST_CATEGORIES))})."
                    + hint,
                )
            )
        elif not category:
            findings.append(
                Finding(
                    WARN,
                    source,
                    f"Stage '{name}': no forecastCategory. The stage will not roll into "
                    "any forecast bucket.",
                )
            )

        if not stage["has_probability"]:
            findings.append(
                Finding(
                    WARN,
                    source,
                    f"Stage '{name}': no probability. Records on this stage compute "
                    "ExpectedRevenue from a default the value set does not state.",
                )
            )

        if stage["won"] and not stage["closed"]:
            findings.append(
                Finding(
                    ERROR,
                    source,
                    f"Stage '{name}': won=true with closed=false. A won stage must also "
                    "be closed; Opportunity.IsWon and IsClosed are both derived from "
                    "StageName and cannot be reconciled per record.",
                )
            )

        if stage["category"] == "Closed" and not stage["closed"]:
            findings.append(
                Finding(
                    ERROR,
                    source,
                    f"Stage '{name}': forecastCategory=Closed with closed=false. The "
                    "Closed bucket is for booked revenue.",
                )
            )


def check_business_processes(
    processes: dict[str, dict], stages: dict[str, dict], findings: list[Finding]
) -> None:
    for name, process in sorted(processes.items()):
        source = process["source"]

        # OM-BP-DEFAULT-01. Org-verified 2026-09-18 (sfskills-dev, validate-only
        # deploy at API 62.0, northwind-sales M1 run 1). Opportunity only: the
        # platform message names the object, and Lead/Case/Solution processes
        # were never put to the org.
        for value in process["defaults"]:
            findings.append(
                Finding(
                    ERROR,
                    source,
                    f"Opportunity business process '{name}' sets "
                    f"<default>true</default> on '{value}' -- the platform refuses a "
                    'default on Opportunity business processes ("Cannot specify a '
                    'default on: Opportunity", org-verified 2026-09-18); remove the '
                    "element; the stage a new Opportunity opens at is not set here.",
                )
            )

        if not process["values"]:
            findings.append(
                Finding(
                    WARN,
                    source,
                    f"Business process '{name}' lists no values. A record type bound to "
                    "it exposes no stages.",
                )
            )
            continue

        if not stages:
            findings.append(
                Finding(
                    INFO,
                    source,
                    f"Business process '{name}': cannot verify won/closed coverage -- "
                    "standardValueSets/OpportunityStage.standardValueSet-meta.xml is not "
                    "in this tree. Retrieve it, or check the ladder with query 8a in "
                    "references/metadata-examples.md.",
                )
            )
            continue

        unknown = [v for v in process["values"] if v not in stages]
        for value in unknown:
            findings.append(
                Finding(
                    WARN,
                    source,
                    f"Business process '{name}' lists stage '{value}', which is not in "
                    "the OpportunityStage value set in this tree. The deploy fails on a "
                    "missing picklist value unless the org already has it.",
                )
            )

        known = [v for v in process["values"] if v in stages]
        has_won = any(stages[v]["won"] for v in known)
        has_closed = any(stages[v]["closed"] for v in known)

        if not has_won:
            findings.append(
                Finding(
                    ERROR,
                    source,
                    f"Business process '{name}' exposes no stage with won=true. Records "
                    "on this process can never be marked won, so they never reach the "
                    "Closed forecast bucket.",
                )
            )
        if not has_closed:
            findings.append(
                Finding(
                    ERROR,
                    source,
                    f"Business process '{name}' exposes no stage with closed=true. "
                    "Records on this process stay in open pipeline forever.",
                )
            )
        elif has_won and not any(
            stages[v]["closed"] and not stages[v]["won"] for v in known
        ):
            findings.append(
                Finding(
                    WARN,
                    source,
                    f"Business process '{name}' has a won stage but no closed-lost stage "
                    "(closed=true, won=false). Lost deals have nowhere to go.",
                )
            )


def check_record_types(
    record_types: dict[str, dict],
    processes: dict[str, dict],
    findings: list[Finding],
) -> None:
    for name, record_type in sorted(record_types.items()):
        if not record_type["active"]:
            continue
        source = record_type["source"]
        process = record_type["process"]

        if not process:
            findings.append(
                Finding(
                    WARN,
                    source,
                    f"Opportunity record type '{name}' is active but names no "
                    "businessProcess. Opportunity record types require one.",
                )
            )
            continue

        if "." in process:
            findings.append(
                Finding(
                    ERROR,
                    source,
                    f"Opportunity record type '{name}' names businessProcess "
                    f"'{process}'. Inside an object definition the bare process name is "
                    "required; the object-qualified form is only for package.xml "
                    "members (api_meta.txt:42993-43008).",
                )
            )
            continue

        if processes and process not in processes:
            findings.append(
                Finding(
                    WARN,
                    source,
                    f"Opportunity record type '{name}' names businessProcess "
                    f"'{process}', which is not defined in this tree. Ship both together "
                    "or the deploy fails on an unresolved cross-reference.",
                )
            )


def check_paths(
    paths: list[dict],
    record_types: dict[str, dict],
    processes: dict[str, dict],
    findings: list[Finding],
) -> None:
    seen: dict[tuple[str, str], str] = {}

    for path in paths:
        source = path["file"]
        record_type = path["record_type"]

        key = (path["entity"], record_type)
        if key in seen:
            findings.append(
                Finding(
                    ERROR,
                    source,
                    f"A second path targets {path['entity']} record type "
                    f"'{record_type or '__Master__'}' -- already claimed by "
                    f"'{seen[key]}'. Only one path may exist per record type per object "
                    "(api_meta.txt:94496).",
                )
            )
        else:
            seen[key] = source

        if path["field"] and path["field"] != "StageName":
            findings.append(
                Finding(
                    INFO,
                    source,
                    f"fieldName is '{path['field']}', not StageName. This checker only "
                    "validates steps against the Opportunity sales process.",
                )
            )
            continue

        if not record_type:
            findings.append(
                Finding(
                    WARN,
                    source,
                    "No recordTypeName. It is a required, non-updateable field "
                    "(api_meta.txt:94513-94530); a path added without it cannot later be "
                    "repointed without delete-and-recreate.",
                )
            )
            continue

        if record_type == "__Master__":
            continue

        if record_types and record_type not in record_types:
            findings.append(
                Finding(
                    WARN,
                    source,
                    f"recordTypeName '{record_type}' is not a record type in this tree. "
                    "recordTypeName is not updateable, so a path deployed against the "
                    "wrong record type must be deleted and recreated.",
                )
            )
            continue

        process_name = record_types.get(record_type, {}).get("process", "")
        process = processes.get(process_name)
        if not process:
            continue

        allowed = set(process["values"])
        if not allowed:
            continue

        for step in path["steps"]:
            if step not in allowed:
                findings.append(
                    Finding(
                        WARN,
                        source,
                        f"Step picklistValueName '{step}' is not a value of business "
                        f"process '{process_name}', which record type '{record_type}' is "
                        "bound to. The step renders no chevron for users on that record "
                        "type.",
                    )
                )


def check_splits_are_setup_only(
    manifest_dir: Path, findings: list[Finding]
) -> None:
    """Splits enablement and split types cannot ship in a manifest. Say so, once."""
    settings_file = manifest_dir / "settings" / "Opportunity.settings-meta.xml"
    team_selling = None
    if settings_file.is_file():
        root = _parse(settings_file, findings)
        if root is not None:
            raw = _text(root, "enableOpportunityTeam")
            if raw:
                team_selling = raw.lower() == "true"

    split_backed_types: list[str] = []
    forecast_dir = manifest_dir / "forecastingTypes"
    if forecast_dir.is_dir():
        for ft_file in sorted(forecast_dir.glob("*.forecastingType-meta.xml")):
            root = _parse(ft_file, findings)
            if root is None:
                continue
            split_type = _text(root, "opportunitySplitType")
            if split_type:
                split_backed_types.append(f"{ft_file.name} -> '{split_type}'")

    if split_backed_types:
        findings.append(
            Finding(
                INFO,
                "forecastingTypes/",
                "Forecast type(s) reference an opportunity split type ("
                + "; ".join(split_backed_types)
                + "). OpportunitySplitType has no create() or delete() call and no "
                "Metadata API type, so each named split type must already exist in the "
                "target org, hand-built in Setup, with IsTotalValidated set correctly -- "
                "it cannot be changed afterwards. Record it in the manual-Setup register.",
            )
        )

    if team_selling is True and not split_backed_types:
        findings.append(
            Finding(
                INFO,
                settings_file.name,
                "enableOpportunityTeam is true. Splits enablement and split-type creation "
                "are Setup-only and are not in this manifest; if the design uses splits, "
                "add them to the manual-Setup register.",
            )
        )
    elif team_selling is False and split_backed_types:
        findings.append(
            Finding(
                ERROR,
                settings_file.name,
                "enableOpportunityTeam is false while a forecast type references an "
                "opportunity split type. Team selling is the prerequisite for splits; "
                "this manifest turns the prerequisite off.",
            )
        )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def check_opportunity_management(manifest_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    if not manifest_dir.is_dir():
        findings.append(
            Finding(ERROR, str(manifest_dir), "Manifest directory not found.")
        )
        return findings

    stages = collect_stages(manifest_dir, findings)
    processes = collect_business_processes(manifest_dir, findings)
    record_types = collect_record_types(manifest_dir, findings)
    paths = collect_paths(manifest_dir, findings)

    if not (stages or processes or record_types or paths):
        findings.append(
            Finding(
                INFO,
                str(manifest_dir),
                "No Opportunity stage value set, business process, record type or "
                "pathAssistant found. Nothing in this tree is in scope for this checker.",
            )
        )
        return findings

    check_stage_values(stages, findings)
    check_business_processes(processes, stages, findings)
    check_record_types(record_types, processes, findings)
    check_paths(paths, record_types, processes, findings)
    check_splits_are_setup_only(manifest_dir, findings)

    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.source, f.message))
    return findings


def main() -> int:
    args = parse_args()
    findings = check_opportunity_management(Path(args.manifest_dir))

    if not findings:
        print("No issues found.")
        return 0

    for finding in findings:
        print(finding)

    counts = {ERROR: 0, WARN: 0, INFO: 0}
    for finding in findings:
        counts[finding.severity] += 1
    print(
        f"\n{counts[ERROR]} error(s), {counts[WARN]} warning(s), {counts[INFO]} info."
    )

    if counts[ERROR] or counts[WARN]:
        return 1
    if args.strict and counts[INFO]:
        return 1
    return 0


if __name__ == "__main__":
    if main() != 0:
        sys.exit(1)
    sys.exit(0)
