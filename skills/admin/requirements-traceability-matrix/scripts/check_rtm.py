#!/usr/bin/env python3
"""Lint a Requirements Traceability Matrix — the artefact this skill produces.

Two schemas are accepted, detected from the header:

* **audit RTM** (``templates/rtm.md`` § CSV Schema) — one row per requirement with
  ``story_ids`` / ``test_case_ids`` / ``defect_ids`` / ``sprint`` / ``release``.
* **build-layer RTM** — the ``traceability.md`` shape from
  ``standards/build-orchestration.md`` § 2: ``req_id, source, requirement, step_id,
  artefact, agent, decision_ref, test_id, test_type, status``. Worked end to end in
  ``references/worked-examples.md``.

Two input formats are accepted: CSV, and a markdown pipe table whose header row
carries ``req_id`` (however it is spelled — ``REQ id``, ``Req ID``, ``req_id``).

Checks performed
----------------
1.  Required columns are present for the detected schema.
2.  ``req_id`` is unique across the matrix.
3.  ``req_id`` is well formed: an optional project prefix, then ``REQ-`` or ``FG-``,
    then digits, with an optional lowercase suffix (``ACME-REQ-001``, ``FG-021``,
    ``REQ-007a``). Both prefixes are legal — a fit-gap-led project keys on ``FG-``.
4.  ``status`` is in the closed enum; ``source`` is in the audit enum, or a build
    clarification id matching ``plan.json`` clarifications (``Q1``) / a named person;
    ``step_id`` and ``decision_ref`` match the build-plan shapes.
5.  Coverage: every row has an artefact **and** a test. Missing either is an ERROR
    while the row claims ``In Build`` / ``In UAT`` / ``Released``, and a waived
    coverage gap (WARN) while it is ``Draft`` / ``Deferred`` / ``Dropped``.
6.  ``test_type`` is one of the five runners in build-orchestration § 5.
7.  ``agent`` resolves to ``agents/<id>/AGENT.md`` when ``--repo-root`` is given.
8.  ``artefact`` API names resolve against the metadata under ``--manifest-dir``
    (package.xml members plus the source files themselves). Unresolved names are
    reported; they are an ERROR only under ``--strict``, because a component the
    Metadata API cannot carry legitimately has no file (mark those ``setup-only:``).
9.  Orphans: components in the manifest that no row's ``artefact`` names.
10. Multi-value cells use the pipe delimiter (audit schema).

Member-form to file-path resolution
------------------------------------
Several Metadata API types name their members in a form that is not the bare
file stem: a folder-qualified name, an ``<Object>.<Child>`` composite, or a
name that lives inside one shared container file rather than its own file.
``index_manifest`` maps each of these back to the source-format path that
evidences it. The suffixes below are the Metadata API's own per-type
``fileSuffix`` / ``directoryName`` pairs (Metadata API Developer Guide,
per-type reference pages) — this repo's
``skills/devops/salesforce-dx-project-structure`` package documents the
project-level ``sfdx-project.json`` / ``packageDirectories`` layer, not a
per-type suffix table, so it is deliberately not cited per row here.

| Metadata type | RTM ``artefact`` member form | Source-format file(s) |
|---|---|---|
| CustomField | ``Object.Field__c`` | ``objects/Object/fields/Field__c.field-meta.xml`` |
| ValidationRule | ``Object.Rule_Name`` | ``objects/Object/validationRules/Rule_Name.validationRule-meta.xml`` |
| RecordType | ``Object.Record_Type`` | ``objects/Object/recordTypes/Record_Type.recordType-meta.xml`` |
| CompactLayout | ``Object.Layout_Name`` | ``objects/Object/compactLayouts/Layout_Name.compactLayout-meta.xml`` |
| BusinessProcess | ``Object.Process_Name`` | ``objects/Object/businessProcesses/Process_Name.businessProcess-meta.xml`` |
| AssignmentRules / AutoResponseRules / EscalationRules | ``Object`` (container — the ``package.xml``/``deploy-order.md`` form) or ``AssignmentRule``/``AutoResponseRule``/``EscalationRule``:``Object.Rule_Name`` (one rule) | ``assignmentRules/Object.assignmentRules-meta.xml`` etc. — one shared file. A row naming the container covers every rule inside it; a row naming one rule covers that rule and, transitively, the container (Gotcha 17). |
| EmailTemplate | ``Folder/Name`` | ``email/Folder/Name.email`` + ``email/Folder/Name.email-meta.xml`` |
| EmailFolder | ``Folder`` | ``email/Folder.emailFolder-meta.xml`` |
| SharingRules | ``Object`` | ``sharingRules/Object.sharingRules-meta.xml`` |
| Layout | ``Object-Layout Name`` (spaces legal) | ``layouts/Object-Layout Name.layout-meta.xml`` |
| Settings | e.g. ``Case`` | ``settings/Case.settings-meta.xml`` |
| Settings (entry-bearing — currently ``BusinessHours``) | ``Settings:BusinessHours`` (container) or ``BusinessHoursEntry:<calendar name>`` (one entry) | ``settings/BusinessHours.settings-meta.xml`` — one shared file holding every entry. A row naming the container covers every entry inside it; a row naming one entry covers that entry and, transitively, the container (Gotcha 18, same key-based resolution as Gotcha 17). |
| StandardValueSet | e.g. ``Industry`` | ``standardValueSets/Industry.standardValueSet-meta.xml`` |
| Queue / Group | bare name | ``queues/Name.queue-meta.xml`` / ``groups/Name.group-meta.xml`` |
| PermissionSet / PermissionSetGroup / Profile | bare name, may contain spaces | ``permissionsets/Name.permissionset-meta.xml`` / ``profiles/System Administrator.profile-meta.xml`` |

Anything not in this table falls back to a same-name, any-type stem match
(the final loop in ``resolve_artefact``), so a slightly wrong type spelling
still resolves against the right file.

Both derived views — coverage gaps and orphans — are printed, and written as
markdown to ``--report-dir`` when one is given.

Usage
-----
    python3 check_rtm.py --file governance/rtm.csv
    python3 check_rtm.py --file build/traceability.md --manifest-dir build/ --repo-root .
    python3 check_rtm.py --manifest-dir .sfskills/builds/acme-case-intake --repo-root .
    python3 check_rtm.py --manifest-dir build/ --report-dir reports/
    python3 check_rtm.py --self-check

Exit code
---------
    0 — no errors (warnings alone do not fail unless --strict)
    1 — at least one ERROR, or any warning under --strict

A named ``--file`` (or ``--csv``) that does not exist is an ERROR::

    $ python3 check_rtm.py --file build/traceability.md
    ERROR: --file /abs/build/traceability.md does not exist (or is not a file).
    Nothing was validated.
    $ echo $?
    1

Discovery is the lenient path, because "this repo has no RTM yet" is a real
state: with ``--manifest-dir`` and no ``--file``, an absent matrix is an INFO
and exit 0. Naming a file that is not there is a broken invocation, and a step
whose ``traceability.md`` was never written must not pass its own test.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

AUDIT_COLUMNS = [
    "req_id", "source", "description", "priority", "story_ids",
    "test_case_ids", "defect_ids", "sprint", "release", "status",
]

BUILD_COLUMNS = [
    "req_id", "source", "requirement", "step_id", "artefact",
    "agent", "decision_ref", "test_id", "test_type", "status",
]

ALLOWED_STATUS = {"Draft", "In Build", "In UAT", "Released", "Deferred", "Dropped"}
TERMINAL_STATUS = {"Draft", "Deferred", "Dropped"}
ACTIVE_STATUS = {"In Build", "In UAT", "Released"}

ALLOWED_SOURCE = {"interview", "sow", "regulatory", "change-request", "defect-driven"}

# standards/build-orchestration.md section 5.
ALLOWED_TEST_TYPE = {"checker", "xml", "manifest", "command", "manual"}

# SKILL.md section "REQ-XXX <-> FG-XXX": both prefixes are legal keys.
REQ_ID_RE = re.compile(r"^(?:[A-Z][A-Z0-9]{1,11}-)?(?:REQ|FG)-\d{2,6}[a-z]?$")
CLARIFICATION_RE = re.compile(r"^Q\d+$")
STEP_ID_RE = re.compile(r"^M\d+-S\d{2,}$")
DECISION_RE = re.compile(r"^D\d+$")

EMPTY_MARKERS = {"", "-", "--", "—", "–", "n/a", "na", "none", "tbd"}

# Metadata source-format suffix -> Metadata API type name. Only the types this
# skill's rows actually name; unknown suffixes fall through to a generic rule.
SUFFIX_TYPE = {
    ".object": "CustomObject",
    ".field": "CustomField",
    ".validationRule": "ValidationRule",
    ".recordType": "RecordType",
    ".listView": "ListView",
    ".webLink": "WebLink",
    ".queue": "Queue",
    ".group": "Group",
    ".flow": "Flow",
    ".permissionset": "PermissionSet",
    ".permissionsetgroup": "PermissionSetGroup",
    ".profile": "Profile",
    ".layout": "Layout",
    ".flexipage": "FlexiPage",
    ".assignmentRules": "AssignmentRules",
    ".autoResponseRules": "AutoResponseRules",
    ".escalationRules": "EscalationRules",
    ".entitlementProcess": "EntitlementProcess",
    ".milestoneType": "MilestoneType",
    ".serviceChannel": "ServiceChannel",
    ".queueRoutingConfig": "QueueRoutingConfig",
    ".presenceUserConfig": "PresenceUserConfig",
    ".servicePresenceStatus": "ServicePresenceStatus",
    ".presenceDeclineReason": "PresenceDeclineReason",
    ".businessProcess": "BusinessProcess",
    ".email": "EmailTemplate",
    ".emailFolder": "EmailFolder",
    ".labels": "CustomLabels",
    ".settings": "Settings",
    ".sharingRules": "SharingRules",
    ".standardValueSet": "StandardValueSet",
    ".cls": "ApexClass",
    ".trigger": "ApexTrigger",
}

# Child components stored inside an object folder: dir name -> type.
OBJECT_CHILD_DIR = {
    "fields": "CustomField",
    "validationRules": "ValidationRule",
    "recordTypes": "RecordType",
    "listViews": "ListView",
    "webLinks": "WebLink",
    "compactLayouts": "CompactLayout",
    "businessProcesses": "BusinessProcess",
}

# Metadata types whose FullName is folder-qualified: <container>/<Folder>/.../
# <Name>.<suffix> for the contained item (member key "Folder/Name"), or
# <container>/<Folder>.<folderSuffix>-meta.xml for the folder itself (member
# key "Folder"). Top-level container directory name -> nothing extra needed;
# the folder path segments between the container and the file ARE the prefix.
# See the docstring table above for EmailTemplate / EmailFolder.
FOLDERED_CONTAINERS = {"email"}

# Rule containers hold named rules whose members use the SINGULAR type name
# (api_meta.txt L23675-23682): Case.assignmentRules holds AssignmentRule members.
RULE_CONTAINERS = {
    "AssignmentRules": ("AssignmentRule", "assignmentRule"),
    "AutoResponseRules": ("AutoResponseRule", "autoResponseRule"),
    "EscalationRules": ("EscalationRule", "escalationRule"),
}

# Settings components hold named entries in ONE file per settings component
# (api_meta.txt L111264-111273): every calendar in the org lives in
# settings/businessHours.settings. Index the entries so a row can name one.
# Same container/child shape as RULE_CONTAINERS above (one shared file mints
# several derived keys) — both feed the same `container_children` map in
# `index_manifest`, so container <-> child coverage resolves identically for
# either deriver (Gotcha 18).
# settings stem (lowercased) -> (entry type, container tag, name tag)
SETTINGS_ENTRIES = {
    "businesshours": ("BusinessHoursEntry", "businessHours", "name"),
}


# --------------------------------------------------------------------------- #
# Small XML helpers
#
# NOTE: an ElementTree element with no children is falsy, so `a.find(x) or
# a.find(y)` silently discards a real leaf element. Everything below tests
# `is not None` explicitly.
# --------------------------------------------------------------------------- #

def _local(tag: str) -> str:
    """Strip the XML namespace from a tag name."""
    return tag.rsplit("}", 1)[-1]


def children_named(elem, *names: str) -> list:
    """Every direct child whose local tag is one of *names*, in document order."""
    wanted = set(names)
    return [c for c in list(elem) if _local(c.tag) in wanted]


def first_named(elem, *names: str):
    """The first direct child whose local tag is one of *names*, or None.

    Written as an explicit loop rather than `find(a) or find(b)` on purpose.
    """
    found = children_named(elem, *names)
    if found:
        return found[0]
    return None


def child_text(elem, *names: str) -> str:
    node = first_named(elem, *names)
    if node is None:
        return ""
    return (node.text or "").strip()


# --------------------------------------------------------------------------- #
# Input parsing
# --------------------------------------------------------------------------- #

HEADER_ALIASES = {
    "req": "req_id", "reqid": "req_id", "requirement_id": "req_id",
    "requirementid": "req_id", "id": "req_id",
    "artifact": "artefact", "salesforce_artefact": "artefact",
    "salesforce_artifact": "artefact", "metadata": "artefact",
    "owning_run_time_agent": "agent", "owning_agent": "agent",
    "recommended_agent": "agent",
    "design_decision_ref": "decision_ref", "decision": "decision_ref",
    "step": "step_id", "test": "test_id",
    "requirement_text": "requirement",
}


def normalise_header(cell: str) -> str:
    text = cell.strip().strip("*").strip("`").strip()
    text = re.sub(r"[^0-9A-Za-z]+", "_", text).strip("_").lower()
    return HEADER_ALIASES.get(text, text)


def is_blank(value: str) -> bool:
    return (value or "").strip().lower() in EMPTY_MARKERS


def clean(value: str) -> str:
    text = (value or "").strip()
    if text.lower() in EMPTY_MARKERS:
        return ""
    return text.strip("`").strip()


def parse_csv_text(text: str) -> list[dict]:
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any((c or "").strip() for c in r)]
    if not rows:
        return []
    header = [normalise_header(c) for c in rows[0]]
    out = []
    for raw in rows[1:]:
        raw = list(raw) + [""] * (len(header) - len(raw))
        out.append({header[i]: raw[i] for i in range(len(header))})
    return out


_SEPARATOR_RE = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")


def _split_md_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    # A cell may contain an escaped pipe (\|) — the canonical multi-value form.
    parts, buf, escaped = [], [], False
    for ch in body:
        if escaped:
            buf.append(ch if ch == "|" else "\\" + ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == "|":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return [p.strip() for p in parts]


def parse_markdown_text(text: str) -> list[dict]:
    """Return the rows of the first pipe table whose header carries req_id."""
    lines = text.splitlines()
    in_fence = False
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            idx += 1
            continue
        if in_fence or "|" not in line:
            idx += 1
            continue
        header = [normalise_header(c) for c in _split_md_row(line)]
        if "req_id" not in header or idx + 1 >= len(lines):
            idx += 1
            continue
        if not _SEPARATOR_RE.match(lines[idx + 1]):
            idx += 1
            continue
        rows = []
        cursor = idx + 2
        while cursor < len(lines) and "|" in lines[cursor] and lines[cursor].strip():
            cells = _split_md_row(lines[cursor])
            cells += [""] * (len(header) - len(cells))
            rows.append({header[i]: cells[i] for i in range(len(header))})
            cursor += 1
        return rows
    return []


def load_matrix(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".csv", ".tsv"}:
        return parse_csv_text(text)
    rows = parse_markdown_text(text)
    if rows:
        return rows
    # A .md that carries the matrix inside a ```csv fence.
    fence = re.search(r"```(?:csv)?\n(req_id,.*?)```", text, re.S)
    if fence:
        return parse_csv_text(fence.group(1))
    return []


RTM_FILENAMES = (
    "traceability.md", "traceability.csv",
    "rtm.csv", "rtm.md",
    "requirements-traceability-matrix.csv",
    "requirements-traceability-matrix.md",
)


def discover_matrix(manifest_dir: Path) -> Path | None:
    for name in RTM_FILENAMES:
        direct = manifest_dir / name
        if direct.is_file():
            return direct
    for root, dirs, files in os.walk(manifest_dir):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules"}]
        for name in sorted(files):
            if name in RTM_FILENAMES:
                return Path(root) / name
    return None


# --------------------------------------------------------------------------- #
# Manifest index — what artefacts actually exist
# --------------------------------------------------------------------------- #

def index_manifest(manifest_dir: Path) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Map ``Type:FullName`` -> the path that evidences it.

    Also returns ``container_children``: every key minted for a container
    whose file also mints per-member child keys — rule containers
    (``AssignmentRules:Case`` -> ``AssignmentRule:Case.Case_Intake_Routing``,
    ...; RULE_CONTAINERS) and entry-bearing settings components
    (``Settings:BusinessHours`` -> ``BusinessHoursEntry:US Support``, ...;
    SETTINGS_ENTRIES) both populate the same map. Container/child coverage is
    resolved from this map, not from the ``where`` path either key happens to
    carry — ``package.xml`` and the container's own file both mint the *same*
    container key via ``index.setdefault``, so whichever ``os.walk`` visits
    first wins that path, and either way it legitimately differs from the
    children's path (always the one shared container file). No path-based
    sibling sweep is used for this reason. See ``references/gotchas.md``
    Gotcha 17 (rules) and Gotcha 18 (settings entries).
    """
    index: dict[str, str] = {}
    container_children: dict[str, list[str]] = {}

    def add(mtype: str, name: str, where: str) -> None:
        if mtype and name:
            index.setdefault(f"{mtype}:{name}", where)

    for root, dirs, files in os.walk(manifest_dir):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules"}]
        root_path = Path(root)
        for name in files:
            path = root_path / name
            rel = str(path.relative_to(manifest_dir))

            if name == "package.xml" or name.startswith("destructiveChanges"):
                for mtype, member in read_manifest_members(path):
                    add(mtype, member, rel)
                continue

            base = name[:-len("-meta.xml")] if name.endswith("-meta.xml") else name
            stem, _, suffix = base.rpartition(".")
            if not stem:
                continue
            suffix = "." + suffix

            parent = root_path.name
            grandparent = root_path.parent.name
            if parent in OBJECT_CHILD_DIR and grandparent:
                add(OBJECT_CHILD_DIR[parent], f"{grandparent}.{stem}", rel)
                continue

            mtype = SUFFIX_TYPE.get(suffix)
            if not mtype:
                continue

            # Foldered metadata (EmailTemplate/EmailFolder): the member key is
            # folder-qualified. The directory segments between the container
            # (e.g. "email") and the file ARE the folder path; join them with
            # "/" ahead of the stem. A file straight under the container (the
            # folder's own -meta.xml) has no segments, so the key is the bare
            # stem — see the docstring table above. Detected off the
            # immediate parent/grandparent (not the path from manifest_dir)
            # so an arbitrary root nesting depth — e.g. a per-step
            # artefacts/<step-id>/email/... layout — does not matter: the
            # template's grandparent is the container ("email"); the
            # folder's own -meta.xml sits directly in the container, so its
            # grandparent is whatever wraps the container instead.
            if grandparent in FOLDERED_CONTAINERS:
                member_name = f"{parent}/{stem}"
            else:
                member_name = stem
            add(mtype, member_name, rel)

            if mtype in RULE_CONTAINERS:
                singular, child_tag = RULE_CONTAINERS[mtype]
                container_key = f"{mtype}:{member_name}"
                for rule_name in read_rule_names(path, child_tag):
                    add(singular, f"{stem}.{rule_name}", rel)
                    container_children.setdefault(container_key, []).append(
                        f"{singular}:{stem}.{rule_name}"
                    )

            if mtype == "Settings" and stem.lower() in SETTINGS_ENTRIES:
                entry_type, container_tag, name_tag = SETTINGS_ENTRIES[stem.lower()]
                container_key = f"{mtype}:{member_name}"
                for entry in read_settings_entries(path, container_tag, name_tag):
                    add(entry_type, entry, rel)
                    container_children.setdefault(container_key, []).append(
                        f"{entry_type}:{entry}"
                    )

    return index, container_children


def read_manifest_members(path: Path) -> list[tuple[str, str]]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return []
    out: list[tuple[str, str]] = []
    for types_node in children_named(root, "types"):
        name_node = first_named(types_node, "name")
        if name_node is None:
            continue
        mtype = (name_node.text or "").strip()
        for member_node in children_named(types_node, "members"):
            member = (member_node.text or "").strip()
            if member and member != "*":
                out.append((mtype, member))
    return out


def read_rule_names(path: Path, child_tag: str) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return []
    names = []
    for rule in children_named(root, child_tag):
        full = child_text(rule, "fullName")
        if full:
            names.append(full)
    return names


def read_settings_entries(path: Path, container_tag: str, name_tag: str) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return []
    names = []
    for entry in children_named(root, container_tag):
        value = child_text(entry, name_tag, "fullName")
        if value:
            names.append(value)
    return names


def resolve_artefact(artefact: str, index: dict[str, str]) -> str | None:
    """Return the evidencing path, or None when the artefact does not resolve."""
    if not index:
        return None
    if artefact in index:
        return index[artefact]
    mtype, _, name = artefact.partition(":")
    if not name:
        name = mtype
        mtype = ""
    lowered = {k.lower(): v for k, v in index.items()}
    if mtype and f"{mtype}:{name}".lower() in lowered:
        return lowered[f"{mtype}:{name}".lower()]
    # Same name, different type spelling (AssignmentRules vs AssignmentRule).
    for key, where in index.items():
        if key.split(":", 1)[-1].lower() == name.lower():
            return where
    return None


def container_key_match(artefact: str, container_children: dict[str, list[str]]) -> str | None:
    """Return the canonical container key ``artefact`` names, or None.

    Covers both derivers that mint several keys out of one shared file:
    RULE_CONTAINERS (``AssignmentRule:Case.Rule_A``, ``AssignmentRule:Case.Rule_B``
    inside ``AssignmentRules:Case``) and SETTINGS_ENTRIES (``BusinessHoursEntry:
    US Support`` inside ``Settings:BusinessHours``). Every child sharing a
    container's file also shares that file's evidencing path, so the
    path-based sweep in ``_validate_build_row`` cannot be used to decide
    coverage between them — it would mark every sibling child referenced the
    moment any one of them, or the container, is named. Container/child
    coverage is resolved on keys instead: this match feeds the container ↔
    child expansion in ``validate`` (see its comment and
    ``references/gotchas.md`` Gotcha 17 / Gotcha 18). Case-insensitive,
    matching ``resolve_artefact``.
    """
    lowered = artefact.lower()
    for container_key, children in container_children.items():
        if container_key.lower() == lowered:
            return container_key
        for child_key in children:
            if child_key.lower() == lowered:
                return child_key
    return None


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #

class Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.coverage_gaps: list[dict] = []
        self.orphans: list[dict] = []
        self.schema = "unknown"
        self.row_count = 0


def split_multi(cell: str) -> list[str]:
    if not cell:
        return []
    return [v.strip() for v in cell.split("|") if v.strip()]


def cell_uses_wrong_delimiter(cell: str) -> bool:
    if not cell or "|" in cell:
        return False
    return ("," in cell) or (";" in cell)


def detect_schema(header: set[str]) -> str:
    if "artefact" in header or "test_id" in header or "step_id" in header:
        return "build"
    if "story_ids" in header or "test_case_ids" in header:
        return "audit"
    return "build" if "requirement" in header else "audit"


def validate(
    rows: list[dict],
    manifest_index: dict[str, str] | None = None,
    repo_root: Path | None = None,
    manifest_dir: Path | None = None,
    container_children: dict[str, list[str]] | None = None,
) -> Result:
    res = Result()
    manifest_index = manifest_index or {}
    container_children = container_children or {}

    if not rows:
        res.warnings.append("matrix has zero data rows")
        return res

    header = set(rows[0].keys())
    res.schema = detect_schema(header)
    res.row_count = len(rows)
    required = BUILD_COLUMNS if res.schema == "build" else AUDIT_COLUMNS

    missing = [c for c in required if c not in header]
    if missing:
        res.errors.append(
            f"missing required columns for the {res.schema} schema: {', '.join(missing)}"
        )
        return res

    seen: dict[str, int] = {}
    referenced: set[str] = set()

    for line_no, row in enumerate(rows, start=2):
        rid = clean(row.get("req_id"))
        status = clean(row.get("status"))
        label = rid or f"row {line_no}"

        # 2/3 — key present, unique, well formed.
        if not rid:
            res.errors.append(f"row {line_no}: empty req_id")
        elif rid in seen:
            res.errors.append(
                f"row {line_no}: duplicate req_id '{rid}' (also at row {seen[rid]})"
            )
        else:
            seen[rid] = line_no
            if not REQ_ID_RE.match(rid):
                res.errors.append(
                    f"row {line_no}: req_id '{rid}' is malformed — expected an optional "
                    f"project prefix then REQ-<digits> or FG-<digits> "
                    f"(REQ-001, FG-021, ACME-REQ-001, REQ-007a)"
                )

        # 4 — status enum.
        if status and status not in ALLOWED_STATUS:
            res.errors.append(
                f"row {line_no} ({label}): status '{status}' not in "
                f"{sorted(ALLOWED_STATUS)}"
            )

        if res.schema == "audit":
            _validate_audit_row(res, line_no, label, row, status)
            continue

        _validate_build_row(
            res, line_no, label, row, status, manifest_index, repo_root, referenced,
            manifest_dir, container_children,
        )

    # Container/child coverage (RULE_CONTAINERS, SETTINGS_ENTRIES): a row
    # naming the container key (`AssignmentRules:Case`, `Settings:
    # BusinessHours`) covers every child key read out of that same file; a
    # row naming one child covers that child and, since the container's own
    # row need not be repeated per child, the container key too. Resolved on
    # keys via `container_children`, not on `where` paths — see
    # `index_manifest`'s docstring and references/gotchas.md Gotcha 17 /
    # Gotcha 18 for why the paths are not comparable.
    for container_key, children in container_children.items():
        if container_key in referenced:
            referenced.update(children)
        elif any(child in referenced for child in children):
            referenced.add(container_key)

    # 9 — orphans: indexed components no row names.
    for key, where in sorted(manifest_index.items()):
        if key in referenced:
            continue
        if key.startswith("Manifest:") or key.startswith("Settings:"):
            continue
        res.orphans.append({"artefact": key, "path": where})
    if res.orphans:
        res.warnings.append(
            f"orphan artefacts: {len(res.orphans)} component(s) in the manifest are "
            f"named by no requirement — see the orphan report"
        )

    return res


def _validate_audit_row(res, line_no, label, row, status) -> None:
    source = clean(row.get("source"))
    if source and source not in ALLOWED_SOURCE:
        res.errors.append(
            f"row {line_no} ({label}): source '{source}' not in {sorted(ALLOWED_SOURCE)}"
        )

    story_cell = row.get("story_ids") or ""
    test_cell = row.get("test_case_ids") or ""
    stories = split_multi(clean(story_cell))
    tests = split_multi(clean(test_cell))

    if status in {"In Build", "In UAT", "Released"} and not stories:
        res.errors.append(
            f"row {line_no} ({label}): status '{status}' requires at least one story_id"
        )
    if status in {"In UAT", "Released"} and not tests:
        res.errors.append(
            f"row {line_no} ({label}): status '{status}' requires at least one test_case_id"
        )
    if not tests or not stories:
        res.coverage_gaps.append({
            "req_id": label,
            "missing": [n for n, v in (("story_ids", stories), ("test_case_ids", tests)) if not v],
            "status": status,
            "disposition": "WAIVED" if status in TERMINAL_STATUS else "BLOCKER",
        })

    for col in ("story_ids", "test_case_ids", "defect_ids"):
        cell = clean(row.get(col))
        if cell_uses_wrong_delimiter(cell):
            res.warnings.append(
                f"row {line_no} ({label}): {col} '{cell}' looks like it uses ',' or ';' "
                f"instead of the canonical '|' delimiter"
            )


def _validate_build_row(
    res, line_no, label, row, status, manifest_index, repo_root, referenced,
    manifest_dir=None, container_children=None,
) -> None:
    container_children = container_children or {}
    source = clean(row.get("source"))
    step_id = clean(row.get("step_id"))
    artefact = clean(row.get("artefact"))
    agent = clean(row.get("agent"))
    decision = clean(row.get("decision_ref"))
    test_id = clean(row.get("test_id"))
    test_type = clean(row.get("test_type"))
    active = status in ACTIVE_STATUS

    if not source:
        res.warnings.append(
            f"row {line_no} ({label}): empty source — name the clarification id (Q<n>) "
            f"or the stakeholder who raised it"
        )
    elif source[0] in "Qq" and not CLARIFICATION_RE.match(source):
        res.warnings.append(
            f"row {line_no} ({label}): source '{source}' looks like a clarification id but is "
            f"not the build-plan shape Q<n> (plan.json clarifications[].id)"
        )
    if not clean(row.get("requirement")):
        res.errors.append(f"row {line_no} ({label}): empty requirement statement")

    if step_id and not STEP_ID_RE.match(step_id):
        res.warnings.append(
            f"row {line_no} ({label}): step_id '{step_id}' is not the build-plan shape "
            f"M<n>-S<nn>"
        )
    if decision and not DECISION_RE.match(decision):
        res.warnings.append(
            f"row {line_no} ({label}): decision_ref '{decision}' is not the build-plan "
            f"shape D<n>"
        )
    if status in TERMINAL_STATUS and status != "Draft" and not decision:
        res.errors.append(
            f"row {line_no} ({label}): status '{status}' with no decision_ref — a "
            f"deferred or dropped requirement needs the decision that dropped it"
        )

    # 5 — coverage. Every row needs an artefact and a test.
    setup_only = artefact.lower().startswith("setup-only")
    missing = []
    if not artefact:
        missing.append("artefact")
    if not test_id:
        missing.append("test_id")
    if missing:
        detail = " and no ".join(missing).replace("_", " ")
        message = (
            f"coverage gap: {label} has no {detail} while status is '{status}'"
            if active else
            f"coverage gap: {label} has no {detail} (status '{status}')"
        )
        if active:
            res.errors.append(f"row {line_no}: {message}")
        else:
            res.warnings.append(
                f"row {line_no}: {message} — waived by decision {decision or 'NONE'}"
            )
        res.coverage_gaps.append({
            "req_id": label,
            "missing": missing,
            "status": status,
            "decision_ref": decision,
            "disposition": "BLOCKER" if active else "WAIVED",
        })

    # 6 — test type.
    if test_id and not test_type:
        res.errors.append(
            f"row {line_no} ({label}): test_id '{test_id}' has no test_type — one of "
            f"{sorted(ALLOWED_TEST_TYPE)}"
        )
    elif test_type and test_type not in ALLOWED_TEST_TYPE:
        res.errors.append(
            f"row {line_no} ({label}): test_type '{test_type}' is not one of the five "
            f"runners {sorted(ALLOWED_TEST_TYPE)}"
        )

    # 7 — the owning agent must exist.
    if not agent and active:
        res.errors.append(
            f"row {line_no} ({label}): no owning agent — every step has exactly one "
            f"run-time agent (standards/build-orchestration.md section 4)"
        )
    elif agent and repo_root is not None:
        agent_md = repo_root / "agents" / agent / "AGENT.md"
        if not agent_md.is_file():
            res.errors.append(
                f"row {line_no} ({label}): agent '{agent}' does not resolve to "
                f"agents/{agent}/AGENT.md"
            )

    # 8 — artefact resolution against the manifest.
    if artefact and artefact.lower().startswith("file:"):
        rel = artefact.split(":", 1)[1].strip()
        if manifest_dir is not None and not (manifest_dir / rel).exists():
            res.warnings.append(
                f"row {line_no} ({label}): file artefact '{rel}' does not exist under "
                f"the manifest dir"
            )
        referenced.add(artefact)
    elif artefact and not setup_only:
        if ":" not in artefact:
            res.warnings.append(
                f"row {line_no} ({label}): artefact '{artefact}' has no metadata type — "
                f"write <MetadataType>:<ApiName>"
            )
        if manifest_index:
            where = resolve_artefact(artefact, manifest_index)
            if where is None:
                res.warnings.append(
                    f"row {line_no} ({label}): artefact '{artefact}' not found under the "
                    f"manifest dir — check the fullName, or mark the row 'setup-only:' "
                    f"if the Metadata API cannot carry it"
                )
            else:
                container_key = container_key_match(artefact, container_children)
                if container_key is not None:
                    # RULE_CONTAINERS / SETTINGS_ENTRIES: coverage between a
                    # container and its children is resolved by key in
                    # `validate` (container -> every child, one child -> just
                    # itself + container), not by this path sweep — every
                    # child sharing one container file shares one evidencing
                    # path, so the sweep would wrongly cover every sibling
                    # child the moment any one of them is named.
                    referenced.add(container_key)
                else:
                    referenced.update(
                        k for k in manifest_index
                        if k == artefact or manifest_index[k] == where
                    )


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #

def render_coverage_report(res: Result) -> str:
    lines = ["# Coverage Gaps", "",
             "Requirements with no artefact or no test.", ""]
    if not res.coverage_gaps:
        lines.append("None. Every row carries an artefact and a test.")
        return "\n".join(lines) + "\n"
    lines += ["| req_id | missing | status | decision_ref | disposition |",
              "|---|---|---|---|---|"]
    for gap in res.coverage_gaps:
        lines.append(
            f"| {gap['req_id']} | {', '.join(gap['missing'])} | {gap['status'] or '—'} "
            f"| {gap.get('decision_ref') or '—'} | {gap['disposition']} |"
        )
    blockers = sum(1 for g in res.coverage_gaps if g["disposition"] == "BLOCKER")
    lines += ["", f"**{len(res.coverage_gaps)} gap(s), {blockers} blocker(s).** "
                  f"Gate verdict: {'FAIL' if blockers else 'PASS'}."]
    return "\n".join(lines) + "\n"


def render_orphan_report(res: Result) -> str:
    lines = ["# Orphan Artefacts", "",
             "Components in the manifest that no requirement names. Legal dispositions: "
             "adopt (write the requirement), remove (its own destructive change), or "
             "document as a dependency.", ""]
    if not res.orphans:
        lines.append("None. Every component traces back to a requirement.")
        return "\n".join(lines) + "\n"
    lines += ["| artefact | evidenced by | disposition |", "|---|---|---|"]
    for orphan in res.orphans:
        lines.append(f"| `{orphan['artefact']}` | `{orphan['path']}` | REVIEW |")
    lines += ["", f"**{len(res.orphans)} orphan(s).** Gate verdict: REVIEW."]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Self check
# --------------------------------------------------------------------------- #

SELF_CHECK_MATRIX = """req_id,source,requirement,step_id,artefact,agent,decision_ref,test_id,test_type,status
REQ-001,Q1,Region drives the SLA calendar,M1-S01,CustomField:Account.Region__c,object-designer,D1,M1-S01-T1,checker,Released
REQ-001,Q2,Duplicate key,M1-S01,CustomField:Case.Severity__c,object-designer,D1,M1-S01-T2,checker,Released
BAD-042,Q3,Malformed key,M1-S02,Queue:Tier_1_General,object-designer,D2,M1-S02-T1,xml,Released
FG-021,Q4,Fit-gap keys are legal,M1-S02,Queue:Billing_Queue,object-designer,D2,M1-S02-T2,xml,Released
REQ-004,Q5,No artefact and no test while active,M2-S01,,object-designer,D3,,,In Build
REQ-005,Q6,Unknown test runner,M2-S02,Flow:Case_Set_Calendar,object-designer,D4,T-9,smoke,Released
REQ-006,Q7,Unknown agent,M2-S03,Flow:Case_Route,no-such-agent-xyz,D5,T-10,manual,Released
REQ-007,Q8,Dropped with no decision,,,,,,,Dropped
REQ-008,Q9,Bad status,M3-S01,Queue:Tier_2_Support_Queue,object-designer,D6,T-11,manual,Active
REQ-009,Question 4,Malformed clarification id,M3-S02,Queue:Tier_1_General,object-designer,D7,T-12,manual,Released
"""


def run_self_check(repo_root: Path | None) -> int:
    rows = parse_csv_text(SELF_CHECK_MATRIX)
    res = validate(rows, manifest_index={}, repo_root=repo_root)
    expected = [
        "duplicate req_id 'REQ-001'",
        "req_id 'BAD-042' is malformed",
        "coverage gap: REQ-004 has no artefact and no test id while status is 'In Build'",
        "test_type 'smoke' is not one of the five runners",
        "status 'Dropped' with no decision_ref",
        "status 'Active' not in",
    ]
    missing = [e for e in expected if not any(e in got for got in res.errors)]

    source_warned = any(
        "source 'Question 4' looks like a clarification id" in w for w in res.warnings
    )

    # FG- must be accepted, not flagged.
    fg_flagged = any("req_id 'FG-021'" in e for e in res.errors)

    # The agent check only fires with a repo root.
    agent_flagged = any("no-such-agent-xyz" in e for e in res.errors)
    agent_ok = agent_flagged if repo_root is not None else not agent_flagged

    # Markdown parsing must produce the same rows as the CSV.
    md = "| req_id | source | requirement | step_id | artefact | agent | decision_ref | test_id | test_type | status |\n"
    md += "|---|---|---|---|---|---|---|---|---|---|\n"
    md += "| REQ-001 | Q1 | R | M1-S01 | `Queue:Q1` | object-designer | D1 | T1 | manual | Released |\n"
    md_rows = parse_markdown_text(md)
    md_ok = len(md_rows) == 1 and md_rows[0]["req_id"] == "REQ-001" \
        and md_rows[0]["artefact"] == "`Queue:Q1`"

    if missing or fg_flagged or not agent_ok or not md_ok or not source_warned:
        print("SELF-CHECK FAIL", file=sys.stderr)
        print(f"  missing expected errors : {missing}", file=sys.stderr)
        print(f"  FG- id wrongly flagged  : {fg_flagged}", file=sys.stderr)
        print(f"  agent check behaved     : {agent_ok}", file=sys.stderr)
        print(f"  markdown parse ok       : {md_ok}", file=sys.stderr)
        print(f"  source shape warned     : {source_warned}", file=sys.stderr)
        return 1
    print(
        "SELF-CHECK PASS — key, coverage, test-type, decision, status, source shape, "
        "FG- acceptance and markdown parsing all exercised."
    )
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint a Salesforce Requirements Traceability Matrix "
                    "(audit RTM or build-layer traceability.md).",
    )
    parser.add_argument("--file", help="Path to the RTM (.csv or .md).")
    parser.add_argument(
        "--csv", default=None,
        help="Alias for --file, kept for callers pinned to the CSV schema "
             "(default: governance/rtm.csv when nothing else is given).",
    )
    parser.add_argument(
        "--manifest-dir",
        help="Build or metadata directory. Used to discover the matrix when --file "
             "is absent, and to resolve artefact API names against real components.",
    )
    parser.add_argument(
        "--repo-root",
        help="Repo root. Enables the agent check: every agent id must resolve to "
             "agents/<id>/AGENT.md.",
    )
    parser.add_argument(
        "--report-dir",
        help="Write rtm-coverage-report.md and rtm-orphan-report.md here.",
    )
    parser.add_argument("--strict", action="store_true",
                        help="Treat warnings as errors (non-zero exit).")
    parser.add_argument("--self-check", action="store_true",
                        help="Exercise every rule against an in-memory fixture and exit.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else None

    if args.self_check:
        return run_self_check(repo_root)

    manifest_dir = Path(args.manifest_dir).resolve() if args.manifest_dir else None
    if manifest_dir is not None and not manifest_dir.is_dir():
        print(f"ERROR: --manifest-dir {manifest_dir} is not a directory", file=sys.stderr)
        return 1

    target = args.file or args.csv
    explicitly_named = target is not None
    matrix_path = Path(target).resolve() if target else None
    if matrix_path is None and manifest_dir is not None:
        matrix_path = discover_matrix(manifest_dir)
        if matrix_path is None:
            print(
                f"INFO: no RTM found under {manifest_dir} "
                f"(looked for {', '.join(RTM_FILENAMES)}); nothing to validate.",
                file=sys.stderr,
            )
            return 0
    if matrix_path is None:
        matrix_path = Path("governance/rtm.csv").resolve()

    if not matrix_path.is_file():
        if explicitly_named:
            # The caller named a file. A named file that is not there is a broken
            # invocation, not a pre-RTM repo: exit 1 so a step whose traceability
            # artefact was never written cannot pass its own acceptance test.
            print(
                f"ERROR: --file {matrix_path} does not exist (or is not a file). "
                "Nothing was validated.",
                file=sys.stderr,
            )
            return 1
        # A pre-RTM repo has no matrix yet; that is not a failure of this checker.
        print(f"INFO: no RTM at {matrix_path}; nothing to validate.", file=sys.stderr)
        return 0

    rows = load_matrix(matrix_path)
    manifest_index, container_children = index_manifest(manifest_dir) if manifest_dir else ({}, {})
    res = validate(
        rows, manifest_index=manifest_index, repo_root=repo_root,
        manifest_dir=manifest_dir, container_children=container_children,
    )

    for warning in res.warnings:
        print(f"WARN: {warning}", file=sys.stderr)
    for error in res.errors:
        print(f"ERROR: {error}", file=sys.stderr)

    print(
        f"{matrix_path.name}: {res.row_count} row(s), {res.schema} schema, "
        f"{len(res.coverage_gaps)} coverage gap(s), {len(res.orphans)} orphan(s), "
        f"{len(res.errors)} error(s), {len(res.warnings)} warning(s)"
    )

    if args.report_dir:
        report_dir = Path(args.report_dir)
        report_dir.mkdir(parents=True, exist_ok=True)
        (report_dir / "rtm-coverage-report.md").write_text(
            render_coverage_report(res), encoding="utf-8")
        (report_dir / "rtm-orphan-report.md").write_text(
            render_orphan_report(res), encoding="utf-8")
        print(f"reports written to {report_dir}/")

    if res.errors:
        return 1
    if args.strict and res.warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
