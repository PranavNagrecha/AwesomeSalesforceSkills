#!/usr/bin/env python3
"""Static governance checks for a Flow portfolio.

Reads a ``flow-governance-policy.yaml`` (see
``references/metadata-examples.md`` section 6) and lints every ``*.flow-meta.xml``,
``*.flowDefinition`` and ``settings/Flow.settings`` under ``--manifest-dir`` against it.
Stdlib only; never contacts an org, never claims to run or activate a flow.

Checks
------
0.  The policy file itself: required keys, enum values that exist in the Metadata API
    guide, a ``naming.pattern`` that compiles, ``trigger_order_*`` inside the documented
    1-2,000 range (``api_meta.txt`` L68438).
1.  Naming: every flow API name matches ``naming.pattern`` and contains none of
    ``naming.forbidden_substrings`` (API name or ``<label>``).
2.  Documentation: ``<description>`` present and long enough, carrying the owner marker;
    ``<interviewLabel>`` present.
3.  ``<apiVersion>`` present and >= ``versions.min_api_version``. The field "defines the
    execution behavior of the flow" and is available in API version 50.0 and later
    (``api_meta.txt`` L68075).
4.  ``<runInMode>`` inside ``versions.allowed_run_in_mode`` and ``<status>`` inside
    ``versions.allowed_status``. Enum values: ``DefaultMode``,
    ``SystemModeWithSharing``, ``SystemModeWithoutSharing`` (L68374); ``Active``,
    ``Draft``, ``Obsolete``, ``InvalidDraft``, ``UnderReview`` (L68416).
5.  Co-residency: more than one Active record-triggered flow on the same
    ``start/object`` + ``start/triggerType`` must each declare a ``<triggerOrder>``, and
    those values must not tie.
6.  Entry criteria: an Active ``RecordAfterSave`` flow declares ``<filters>`` or
    ``<filterFormula>`` on ``<start>`` when the policy asks for it (``api_meta.txt``
    L72366, L72425). Advisory, not an error - some after-save flows legitimately run on
    every save.
7.  Test coverage: a flow with ``<status>Active</status>`` whose ``processType`` is
    testable has a ``*.flowtest-meta.xml`` / ``*.flowtest`` in the manifest naming it in
    ``<flowApiName>`` (FlowTest, ``api_meta.txt`` L73953).
8.  Activation control: ``activation_control`` and the tree agree — ``flow_status``
    requires an empty ``flowDefinitions/``; ``flow_definition`` requires a
    ``.flowDefinition`` for every Active flow. Deploying both lets
    ``activeVersionNumber`` silently override ``<status>`` (L73929-73932).
9.  ``settings/Flow.settings``: flags the deprecated ``isAccessToInvokedApexRequired`` /
    ``isFlowApexContextRetired`` (API 47.0-58.0, deprecated 59.0+, L116988, L117016) and
    warns when ``enableFlowDeployAsActiveEnabled`` is false while the manifest carries
    Active flows (L116877).
10. Fault paths are NOT judged here. Presence of the requirement is reported and the
    judgement is delegated by name to ``flow/fault-handling``
    ``scripts/check_flow_faults.py``.

Usage
-----
    python3 check_flow_governance.py --manifest-dir force-app/main/default
    python3 check_flow_governance.py --manifest-dir force-app --policy governance/flow-governance-policy.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

# --------------------------------------------------------------------------- #
# Documented enum values (Metadata API Developer Guide, Flow section)
# --------------------------------------------------------------------------- #

RUN_IN_MODE = {"DefaultMode", "SystemModeWithSharing", "SystemModeWithoutSharing"}
FLOW_STATUS = {"Active", "Draft", "Obsolete", "InvalidDraft", "UnderReview"}
RECORD_TRIGGER_TYPES = {"RecordBeforeSave", "RecordAfterSave", "RecordBeforeDelete"}
TRIGGER_ORDER_FLOOR, TRIGGER_ORDER_CEILING = 1, 2000
DEPRECATED_FLOW_SETTINGS = {
    "isAccessToInvokedApexRequired": "API 47.0-58.0, deprecated in 59.0 and later",
    "isFlowApexContextRetired": "API 49.0-58.0, deprecated in 59.0 and later",
    "enableFlowCustomPropertyEditor": "API 48.0-50.0, deprecated in 50.0 and later",
    "enableInvocableFlowFixEnabled": "removed in API version 50.0 and later",
}
FAULT_CHECKER = "flow/fault-handling scripts/check_flow_faults.py"

DEFAULT_POLICY = {
    "activation_control": "flow_status",
    "naming": {"pattern": "", "forbidden_substrings": []},
    "versions": {
        "min_api_version": 0,
        "allowed_run_in_mode": sorted(RUN_IN_MODE),
        "allowed_status": sorted(FLOW_STATUS),
    },
    "record_triggered": {
        "require_trigger_order_when_co_resident": True,
        "trigger_order_min": TRIGGER_ORDER_FLOOR,
        "trigger_order_max": TRIGGER_ORDER_CEILING,
    },
    "documentation": {
        "require_description": False,
        "min_description_chars": 0,
        "require_interview_label": False,
        "require_owner_in_description": False,
        "owner_marker": "Owner:",
    },
    "testing": {"require_flow_test_for_active": False, "testable_process_types": []},
    "fault_paths": {"require_fault_connectors": False},
}


# --------------------------------------------------------------------------- #
# Minimal YAML-subset parser (stdlib only): mappings, lists, scalars, comments
# --------------------------------------------------------------------------- #

def _scalar(raw: str):
    text = raw.strip()
    if text[:1] in ("'", '"'):
        closing = text.find(text[0], 1)
        return text[1:closing] if closing != -1 else text[1:]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [_scalar(part) for part in inner.split(",")] if inner else []
    text = re.split(r"\s+#", text, maxsplit=1)[0].strip()
    if text in ("null", "~", ""):
        return None
    if text in ("true", "false"):
        return text == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _significant_lines(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for raw in text.splitlines():
        raw = raw.replace("\t", "  ")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        out.append((len(raw) - len(raw.lstrip(" ")), stripped))
    return out


def _parse_block(lines: list[tuple[int, str]], idx: int, indent: int):
    if idx >= len(lines):
        return None, idx

    if lines[idx][1].startswith("- ") or lines[idx][1] == "-":
        items: list = []
        while idx < len(lines):
            line_indent, content = lines[idx]
            if line_indent != indent or not (content.startswith("- ") or content == "-"):
                break
            inner = content[2:].strip() if content.startswith("- ") else ""
            if inner == "":
                idx += 1
                if idx < len(lines) and lines[idx][0] > indent:
                    value, idx = _parse_block(lines, idx, lines[idx][0])
                else:
                    value = None
                items.append(value)
            elif ":" in inner and inner[0] not in ("'", '"', "["):
                child_indent = indent + 2
                sub = [(child_indent, inner)]
                idx += 1
                while idx < len(lines) and lines[idx][0] >= child_indent:
                    sub.append(lines[idx])
                    idx += 1
                value, _ = _parse_block(sub, 0, child_indent)
                items.append(value)
            else:
                items.append(_scalar(inner))
                idx += 1
        return items, idx

    mapping: dict = {}
    while idx < len(lines):
        line_indent, content = lines[idx]
        if line_indent < indent:
            break
        if line_indent > indent:
            idx += 1
            continue
        if content.startswith("- ") or content == "-":
            break
        if ":" not in content:
            idx += 1
            continue
        key, _, rest = content.partition(":")
        key, rest = key.strip(), rest.strip()
        idx += 1
        if rest and rest not in (">-", ">", "|", "|-"):
            mapping[key] = _scalar(rest)
        elif rest in (">-", ">", "|", "|-"):
            body: list[str] = []
            while idx < len(lines) and lines[idx][0] > line_indent:
                body.append(lines[idx][1])
                idx += 1
            mapping[key] = " ".join(body)
        elif idx < len(lines) and lines[idx][0] > line_indent:
            value, idx = _parse_block(lines, idx, lines[idx][0])
            mapping[key] = value
        else:
            mapping[key] = None
    return mapping, idx


def parse_yaml_subset(text: str) -> dict:
    lines = _significant_lines(text)
    if not lines:
        return {}
    value, _ = _parse_block(lines, 0, lines[0][0])
    return value if isinstance(value, dict) else {}


# --------------------------------------------------------------------------- #
# ElementTree helpers.  A leaf Element is falsy, so every lookup tests
# `is not None` explicitly -- never `root.find(a) or root.find(b)`.
# --------------------------------------------------------------------------- #

def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child(parent, name: str):
    """First direct child with this local name, or None."""
    if parent is None:
        return None
    for element in list(parent):
        if local_name(element.tag) == name:
            return element
    return None


def child_text(parent, name: str) -> str:
    element = child(parent, name)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def first_of(parent, *names):
    """First direct child matching any of these names, or None."""
    for name in names:
        element = child(parent, name)
        if element is not None:
            return element
    return None


def parse_xml(path: Path):
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def flow_api_name(path: Path) -> str:
    name = path.name
    for suffix in (".flow-meta.xml", ".flow"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


# --------------------------------------------------------------------------- #
# Policy access
# --------------------------------------------------------------------------- #

def _section(policy: dict, key: str) -> dict:
    merged = dict(DEFAULT_POLICY.get(key, {}))
    value = policy.get(key)
    if isinstance(value, dict):
        merged.update({k: v for k, v in value.items() if v is not None})
    return merged


def _string_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value if v is not None]
    if isinstance(value, str) and value:
        return [value]
    return []


def find_policy(manifest_dir: Path, explicit: str | None) -> tuple[dict, str, list[str]]:
    """Return (policy mapping, source label, issues)."""
    if explicit:
        path = Path(explicit)
        if not path.exists():
            return {}, str(path), [f"ERROR Policy file not found: {path}"]
        document = parse_yaml_subset(path.read_text(encoding="utf-8"))
        policy = document.get("flow_governance_policy")
        if not isinstance(policy, dict):
            return {}, str(path), [f"ERROR {path}: no top-level 'flow_governance_policy:' mapping."]
        return policy, str(path), []

    candidates = sorted(
        p for suffix in ("*.yaml", "*.yml")
        for p in manifest_dir.rglob(suffix)
        if p.is_file()
    )
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "flow_governance_policy:" not in text:
            continue
        document = parse_yaml_subset(text)
        policy = document.get("flow_governance_policy")
        if isinstance(policy, dict):
            return policy, str(path), []
    return {}, "(none)", [
        "WARN No flow-governance-policy.yaml found under the manifest directory. "
        "Only the checks that need no policy are running; naming, API-version floor, "
        "run-mode allow-list and test coverage are NOT being enforced. "
        "See references/metadata-examples.md section 6."
    ]


def check_policy(policy: dict, source: str) -> list[str]:
    issues: list[str] = []
    if not policy:
        return issues
    label = f"[{source}]"

    activation = policy.get("activation_control")
    if activation not in ("flow_status", "flow_definition"):
        issues.append(
            f"ERROR {label} activation_control is {activation!r}; expected 'flow_status' or "
            "'flow_definition'. A repo that does not declare which one wins cannot tell a "
            "reviewer which version will be live (api_meta.txt L73929-73932)."
        )

    naming = _section(policy, "naming")
    pattern = naming.get("pattern") or ""
    if pattern:
        try:
            re.compile(pattern)
        except re.error as exc:
            issues.append(f"ERROR {label} naming.pattern is not a valid regex: {exc}")

    versions = _section(policy, "versions")
    for mode in _string_list(versions.get("allowed_run_in_mode")):
        if mode not in RUN_IN_MODE:
            issues.append(
                f"ERROR {label} versions.allowed_run_in_mode contains {mode!r}, which is not a "
                f"documented FlowRunInMode value {sorted(RUN_IN_MODE)} (api_meta.txt L68374)."
            )
    for status in _string_list(versions.get("allowed_status")):
        if status not in FLOW_STATUS:
            issues.append(
                f"ERROR {label} versions.allowed_status contains {status!r}, which is not a "
                f"documented FlowVersionStatus value {sorted(FLOW_STATUS)} (api_meta.txt L68416)."
            )

    rt = _section(policy, "record_triggered")
    low, high = rt.get("trigger_order_min"), rt.get("trigger_order_max")
    if isinstance(low, int) and low < TRIGGER_ORDER_FLOOR:
        issues.append(
            f"ERROR {label} record_triggered.trigger_order_min is {low}; triggerOrder runs from "
            f"{TRIGGER_ORDER_FLOOR} to {TRIGGER_ORDER_CEILING} (api_meta.txt L68438)."
        )
    if isinstance(high, int) and high > TRIGGER_ORDER_CEILING:
        issues.append(
            f"ERROR {label} record_triggered.trigger_order_max is {high}; triggerOrder runs from "
            f"{TRIGGER_ORDER_FLOOR} to {TRIGGER_ORDER_CEILING} (api_meta.txt L68438)."
        )

    gates = policy.get("review_gates")
    if not isinstance(gates, list) or not gates:
        issues.append(
            f"WARN {label} review_gates is empty. Those are the human gates this checker "
            "cannot evaluate; an empty list means the standard claims full automation it "
            "does not have."
        )

    if _section(policy, "fault_paths").get("require_fault_connectors"):
        issues.append(
            f"NOTE {label} fault_paths.require_fault_connectors is true. This checker does not "
            f"judge fault paths; run {FAULT_CHECKER} over the same --manifest-dir."
        )
    return issues


# --------------------------------------------------------------------------- #
# Flow inspection
# --------------------------------------------------------------------------- #

class FlowFacts:
    __slots__ = ("path", "api_name", "label", "description", "interview_label",
                 "status", "run_in_mode", "api_version", "process_type",
                 "trigger_type", "trigger_object", "trigger_order", "has_entry_criteria")

    def __init__(self, path: Path, root):
        self.path = path
        self.api_name = flow_api_name(path)
        self.label = child_text(root, "label")
        self.description = child_text(root, "description")
        self.interview_label = child_text(root, "interviewLabel")
        self.status = child_text(root, "status")
        self.run_in_mode = child_text(root, "runInMode")
        self.api_version = child_text(root, "apiVersion")
        self.process_type = child_text(root, "processType")
        start = child(root, "start")
        self.trigger_type = child_text(start, "triggerType") if start is not None else ""
        self.trigger_object = child_text(start, "object") if start is not None else ""
        self.trigger_order = child_text(root, "triggerOrder")
        # Entry criteria on the Start element: FlowRecordFilter[] `filters` (api_meta.txt
        # L72425), `filterFormula` "a formula that's used to filter what records execute
        # the flow during a save. Available only in record-triggered flows" (L72366).
        self.has_entry_criteria = (
            start is not None
            and first_of(start, "filters", "filterFormula") is not None
        )

    @property
    def is_active(self) -> bool:
        # "Any flow without a status value is deployed or retrieved with a status value of
        # Draft" (api_meta.txt L73187-73188), so an absent status is never Active.
        return self.status == "Active"

    @property
    def is_record_triggered(self) -> bool:
        return self.trigger_type in RECORD_TRIGGER_TYPES


def collect_flows(manifest_dir: Path) -> tuple[list[FlowFacts], list[str]]:
    flows, issues = [], []
    paths = sorted(set(manifest_dir.rglob("*.flow-meta.xml")) | set(manifest_dir.rglob("*.flow")))
    for path in paths:
        root = parse_xml(path)
        if root is None:
            issues.append(f"ERROR {path}: unable to parse flow metadata as XML.")
            continue
        flows.append(FlowFacts(path, root))
    return flows, issues


def collect_flow_tests(manifest_dir: Path) -> set[str]:
    covered: set[str] = set()
    paths = set(manifest_dir.rglob("*.flowtest-meta.xml")) | set(manifest_dir.rglob("*.flowtest"))
    for path in sorted(paths):
        root = parse_xml(path)
        if root is None:
            continue
        name = child_text(root, "flowApiName")
        if name:
            covered.add(name)
    return covered


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

def check_naming(flow: FlowFacts, policy: dict) -> list[str]:
    naming = _section(policy, "naming")
    issues: list[str] = []
    pattern = naming.get("pattern") or ""
    if pattern:
        try:
            compiled = re.compile(pattern)
        except re.error:
            compiled = None
        if compiled is not None and not compiled.match(flow.api_name):
            issues.append(
                f"ERROR {flow.path}: API name {flow.api_name!r} does not match "
                f"naming.pattern {pattern!r}. Rename before activation - a flow cannot be "
                "renamed cheaply once interviews and permission sets reference it."
            )
    haystacks = [flow.api_name, flow.label]
    for banned in _string_list(naming.get("forbidden_substrings")):
        for text in haystacks:
            if text and banned.lower() in text.lower():
                issues.append(
                    f"ERROR {flow.path}: {banned!r} appears in {text!r}. Generic and "
                    "provenance names outlive the sprint that created them."
                )
                break
    return issues


def check_documentation(flow: FlowFacts, policy: dict) -> list[str]:
    doc = _section(policy, "documentation")
    issues: list[str] = []
    minimum = doc.get("min_description_chars") or 0
    if doc.get("require_description") and not flow.description:
        issues.append(
            f"ERROR {flow.path}: no <description>. FlowDefinitionView.Description is the only "
            "field the portfolio inventory can read (object_reference.txt L139340)."
        )
    elif flow.description and isinstance(minimum, int) and len(flow.description) < minimum:
        issues.append(
            f"WARN {flow.path}: <description> is {len(flow.description)} characters; policy "
            f"asks for {minimum}. Purpose, owner and escalation do not fit in a clause."
        )
    marker = doc.get("owner_marker") or "Owner:"
    if doc.get("require_owner_in_description") and marker.lower() not in flow.description.lower():
        issues.append(
            f"ERROR {flow.path}: <description> has no {marker!r} marker. Flow error email goes "
            "to the last modifier unless enableFlowUseApexExceptionEmail is true "
            "(api_meta.txt L116961), so 'who owns this' has to be written down."
        )
    if doc.get("require_interview_label") and not flow.interview_label:
        issues.append(
            f"WARN {flow.path}: no <interviewLabel>. This is the string shown in the Paused Flow "
            "Interviews list and on FlowInterview.InterviewLabel (api_meta.txt L68168)."
        )
    return issues


def check_versions(flow: FlowFacts, policy: dict) -> list[str]:
    versions = _section(policy, "versions")
    issues: list[str] = []

    floor = versions.get("min_api_version") or 0
    if not flow.api_version:
        issues.append(
            f"ERROR {flow.path}: no <apiVersion>. The field 'defines the execution behavior of "
            "the flow' (api_meta.txt L68075); without it the flow's run-time behaviour is "
            "whatever the org defaulted to at save time."
        )
    else:
        try:
            value = float(flow.api_version)
        except ValueError:
            issues.append(f"ERROR {flow.path}: <apiVersion> {flow.api_version!r} is not numeric.")
        else:
            if isinstance(floor, int) and floor and value < floor:
                issues.append(
                    f"ERROR {flow.path}: <apiVersion> {flow.api_version} is below the policy floor "
                    f"{floor}. Two flows on one object at different API versions adopt different "
                    "versioned run-time behaviour in the same save."
                )

    allowed_modes = _string_list(versions.get("allowed_run_in_mode"))
    if flow.run_in_mode and allowed_modes and flow.run_in_mode not in allowed_modes:
        issues.append(
            f"ERROR {flow.path}: <runInMode> {flow.run_in_mode!r} is outside the policy set "
            f"{allowed_modes}. SystemModeWithoutSharing means 'the flow can access all data' "
            "(api_meta.txt L68382) and is a security review, not a build choice."
        )
    if flow.run_in_mode and flow.run_in_mode not in RUN_IN_MODE:
        issues.append(
            f"ERROR {flow.path}: <runInMode> {flow.run_in_mode!r} is not a documented "
            f"FlowRunInMode value {sorted(RUN_IN_MODE)} (api_meta.txt L68374)."
        )

    allowed_status = _string_list(versions.get("allowed_status"))
    if flow.status and flow.status not in FLOW_STATUS:
        issues.append(
            f"ERROR {flow.path}: <status> {flow.status!r} is not a documented FlowVersionStatus "
            f"value {sorted(FLOW_STATUS)} (api_meta.txt L68416)."
        )
    elif flow.status and allowed_status and flow.status not in allowed_status:
        issues.append(
            f"ERROR {flow.path}: <status> {flow.status!r} is outside the policy set "
            f"{allowed_status}."
        )
    elif not flow.status:
        issues.append(
            f"WARN {flow.path}: no <status>. 'Any flow without a status value is deployed or "
            "retrieved with a status value of Draft' (api_meta.txt L73187) - state it "
            "explicitly so the diff says what will be live."
        )
    return issues


def check_co_residency(flows: list[FlowFacts], policy: dict) -> list[str]:
    rt = _section(policy, "record_triggered")
    if not rt.get("require_trigger_order_when_co_resident", True):
        return []
    low = rt.get("trigger_order_min") or TRIGGER_ORDER_FLOOR
    high = rt.get("trigger_order_max") or TRIGGER_ORDER_CEILING
    issues: list[str] = []

    groups: dict[tuple[str, str], list[FlowFacts]] = {}
    for flow in flows:
        if flow.is_active and flow.is_record_triggered and flow.trigger_object:
            groups.setdefault((flow.trigger_object, flow.trigger_type), []).append(flow)

    for (obj, trigger), members in sorted(groups.items()):
        for flow in members:
            if flow.trigger_order:
                try:
                    order = int(flow.trigger_order)
                except ValueError:
                    issues.append(
                        f"ERROR {flow.path}: <triggerOrder> {flow.trigger_order!r} is not an integer."
                    )
                    continue
                if order < low or order > high:
                    issues.append(
                        f"ERROR {flow.path}: <triggerOrder> {order} is outside {low}-{high}. The "
                        "field runs from 1 to 2,000 (api_meta.txt L68438)."
                    )
        if len(members) < 2:
            continue

        unordered = [f for f in members if not f.trigger_order]
        if unordered:
            names = ", ".join(sorted(f.api_name for f in unordered))
            issues.append(
                f"ERROR {obj}/{trigger}: {len(members)} Active record-triggered flows share this "
                f"save context and {len(unordered)} declare no <triggerOrder> ({names}). The Apex "
                "order of execution names steps 3 and 14 as single steps (apexdev.txt L15440, "
                "L15466) and does not order flows within them; triggerOrder is what does."
            )

        seen: dict[int, list[str]] = {}
        for flow in members:
            if not flow.trigger_order:
                continue
            try:
                order = int(flow.trigger_order)
            except ValueError:
                continue
            seen.setdefault(order, []).append(flow.api_name)
        for order, names in sorted(seen.items()):
            if len(names) > 1:
                issues.append(
                    f"ERROR {obj}/{trigger}: <triggerOrder> {order} is declared by "
                    f"{len(names)} Active flows ({', '.join(sorted(names))}). A tie is not an "
                    "order; give each flow a distinct value."
                )
    return issues


def check_entry_criteria(flows: list[FlowFacts], policy: dict) -> list[str]:
    rt = _section(policy, "record_triggered")
    if not rt.get("require_entry_criteria_for_after_save"):
        return []
    issues: list[str] = []
    for flow in flows:
        if flow.trigger_type != "RecordAfterSave" or not flow.is_active:
            continue
        if flow.has_entry_criteria:
            continue
        issues.append(
            f"WARN {flow.path}: after-save flow with no <filters> or <filterFormula> on "
            "<start>. It runs on every save of every record of this object. "
            "doesRequireRecordChangedToMeetCriteria only narrows conditions that exist "
            "(api_meta.txt L72322)."
        )
    return issues


def check_testing(flows: list[FlowFacts], covered: set[str], policy: dict) -> list[str]:
    testing = _section(policy, "testing")
    if not testing.get("require_flow_test_for_active"):
        return []
    testable = set(_string_list(testing.get("testable_process_types")))
    issues: list[str] = []
    for flow in flows:
        if not flow.is_active:
            continue
        if testable and flow.process_type not in testable:
            continue
        if flow.api_name in covered:
            continue
        issues.append(
            f"ERROR {flow.path}: <status>Active</status> with no FlowTest in the manifest naming "
            f"{flow.api_name!r} in <flowApiName>. FlowTest exists for exactly this case - "
            "'before you activate a record-triggered, autolaunched, or Data Cloud-triggered "
            "flow, you can test it' (api_meta.txt L73953)."
        )
    return issues


def check_activation_control(manifest_dir: Path, flows: list[FlowFacts], policy: dict) -> list[str]:
    mode = policy.get("activation_control")
    if mode not in ("flow_status", "flow_definition"):
        return []
    definitions: dict[str, Path] = {}
    for path in sorted(manifest_dir.rglob("*.flowDefinition*")):
        if path.is_file():
            definitions[path.name.split(".")[0]] = path
    issues: list[str] = []

    if mode == "flow_status" and definitions:
        names = ", ".join(sorted(definitions))
        issues.append(
            "ERROR activation_control is 'flow_status' but the tree carries FlowDefinition files "
            f"({names}). 'If you deploy with flow definitions, the active version numbers in the "
            "flow definitions override the status fields in the flows' (api_meta.txt "
            "L73929-73932) - so these files, not the <status> in your diff, decide what is live. "
            "The upgrade checklist asks for an empty flowDefinitions directory (L73189)."
        )
    if mode == "flow_definition":
        for flow in flows:
            if flow.is_active and flow.api_name not in definitions:
                issues.append(
                    f"ERROR {flow.path}: activation_control is 'flow_definition' but there is no "
                    f"{flow.api_name}.flowDefinition declaring <activeVersionNumber>. Under this "
                    "mode <status> is documentation; nothing in the manifest activates this flow."
                )
        for name, path in sorted(definitions.items()):
            root = parse_xml(path)
            if root is None:
                issues.append(f"ERROR {path}: unable to parse FlowDefinition as XML.")
                continue
            active = child_text(root, "activeVersionNumber")
            if not active:
                issues.append(
                    f"WARN {path}: no <activeVersionNumber>. FlowDefinition has only four fields "
                    "and this is the one that does anything (api_meta.txt L73938-73946)."
                )
            elif active == "0":
                issues.append(
                    f"NOTE {path}: <activeVersionNumber>0</activeVersionNumber> deactivates "
                    f"{name}. Confirm this is the intended retirement, not a merge artefact."
                )
    return issues


def check_flow_settings(manifest_dir: Path, flows: list[FlowFacts]) -> list[str]:
    issues: list[str] = []
    paths = [p for p in sorted(manifest_dir.rglob("Flow.settings")) if p.is_file()]
    has_active = any(flow.is_active for flow in flows)
    if not paths:
        if has_active:
            issues.append(
                "WARN The manifest carries Active flows but no settings/Flow.settings. "
                "enableFlowDeployAsActiveEnabled defaults to false in production orgs, so those "
                "flows land Draft (api_meta.txt L116877-116886). Feature settings do not accept "
                "the package.xml wildcard (L117094), so this file has to be named explicitly."
            )
        return issues

    for path in paths:
        root = parse_xml(path)
        if root is None:
            issues.append(f"ERROR {path}: unable to parse Flow.settings as XML.")
            continue
        for field, note in DEPRECATED_FLOW_SETTINGS.items():
            if child(root, field) is not None:
                issues.append(
                    f"ERROR {path}: <{field}> is deprecated ({note}). Deploying it against a "
                    "modern package.xml version is governance debt, not governance."
                )
        deploy_active = child_text(root, "enableFlowDeployAsActiveEnabled")
        if deploy_active == "false" and has_active:
            issues.append(
                f"ERROR {path}: enableFlowDeployAsActiveEnabled is false while the manifest "
                "carries flows with <status>Active</status>. 'When the value is false, all "
                "processes and flows are deployed as inactive' (api_meta.txt L116877) - the "
                "deploy will succeed and activate nothing."
            )
        session_id = child_text(root, "isFlowBlockAccessToSessionIDEnabled")
        if session_id == "false":
            issues.append(
                f"WARN {path}: isFlowBlockAccessToSessionIDEnabled is false, so any flow author "
                "can mint a valid session ID through API.SessionID (api_meta.txt L117035)."
            )
        field_filter = child_text(root, "enableFlowFieldFilterEnabled")
        if field_filter == "true":
            issues.append(
                f"WARN {path}: enableFlowFieldFilterEnabled is true. Create/Update Records "
                "elements then 'set only the fields that the running user can edit. No "
                "notification is sent' (api_meta.txt L116889-116898) - the fault paths "
                f"{FAULT_CHECKER} verifies will never fire for that class of failure."
            )
    return issues


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def check_flow_governance(manifest_dir: Path, policy_path: str | None) -> list[str]:
    if not manifest_dir.exists():
        return [f"ERROR Manifest directory not found: {manifest_dir}"]

    policy, source, issues = find_policy(manifest_dir, policy_path)
    issues += check_policy(policy, source)

    flows, parse_issues = collect_flows(manifest_dir)
    issues += parse_issues
    if not flows:
        issues.append(f"WARN No *.flow-meta.xml files found under {manifest_dir}.")

    covered = collect_flow_tests(manifest_dir)
    for flow in flows:
        issues += check_naming(flow, policy)
        issues += check_documentation(flow, policy)
        issues += check_versions(flow, policy)
    issues += check_co_residency(flows, policy)
    issues += check_entry_criteria(flows, policy)
    issues += check_testing(flows, covered, policy)
    issues += check_activation_control(manifest_dir, flows, policy)
    issues += check_flow_settings(manifest_dir, flows)
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint a Flow portfolio against flow-governance-policy.yaml.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the retrieved Salesforce source tree (default: current directory).",
    )
    parser.add_argument(
        "--policy",
        default=None,
        help="Path to flow-governance-policy.yaml (otherwise discovered under --manifest-dir).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues = check_flow_governance(Path(args.manifest_dir), args.policy)

    errors = [i for i in issues if i.startswith("ERROR")]
    for issue in issues:
        print(issue)
    if not issues:
        print("No issues found.")
        return 0
    print(f"\n{len(errors)} error(s), {len(issues) - len(errors)} advisory.")
    print(f"Fault-path correctness is not checked here; run {FAULT_CHECKER}.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
