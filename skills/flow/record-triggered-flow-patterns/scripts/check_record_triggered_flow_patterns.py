#!/usr/bin/env python3
"""Static checks for record-triggered Flow metadata.

Parses every ``*.flow-meta.xml`` under ``--manifest-dir`` and reports the shapes
that deploy cleanly but misbehave at runtime. Stdlib only; never contacts an org.

Checks
------
1.  A record-triggered flow declares ``triggerType``, ``recordTriggerType`` and
    ``object`` on its Start element.
2.  A ``RecordBeforeSave`` flow contains no ``recordCreates`` / ``recordUpdates`` /
    ``recordDeletes`` / ``actionCalls`` / ``subflows`` — before-save assignments to
    ``$Record`` persist as part of the save (Apex Developer Guide, order of
    execution steps 3 and 7).
3.  A ``RecordAfterSave`` flow that writes back to its own triggering object has
    either entry criteria (``filters`` / ``filterFormula``) or
    ``doesRequireRecordChangedToMeetCriteria``.
4.  Every fault-capable element (Create / Update / Delete / Get / Action /
    Subflow) has a ``faultConnector``. Elements that are themselves the target of
    a ``faultConnector`` are exempt — a fault path on a fault path is unbounded.
5.  No Get Records (or any DML) is reachable from a Loop's
    ``nextValueConnector``.
6.  ``apiVersion`` is present — it is a behavioural setting, not bookkeeping.
7.  ``status`` is one of the documented ``FlowVersionStatus`` values.
8.  ``triggerOrder`` is set whenever the manifest holds more than one
    record-triggered flow on the same object in the same trigger type.
9.  A ``FlowTest``'s Start test point carries the ``$Record`` parameter pair
    that matches the target flow's ``recordTriggerType``:

    - ``Create`` + an ``InputTriggeringRecordUpdated`` parameter -> ERROR. Proven
      live (dry-run, API 67.0, 2026-09-12): "The test point for elementApiName
      "Start" contains the incompatible parameter value "$Record" of type
      InputTriggeringRecordUpdated. Remove the parameter or change the
      recordTriggerType for the flow."
    - ``Create`` with no ``InputTriggeringRecordInitial`` parameter -> ERROR.
      Proven live: "The test point for elementApiName "Start" is missing a
      parameter of type InputTriggeringRecordInitial."
    - ``Update`` with only one of ``InputTriggeringRecordInitial`` /
      ``InputTriggeringRecordUpdated`` -> WARN. The documented shape
      (``references/metadata-examples.md`` § 4.1) is both; a single parameter on
      an Update-triggered flow is unverified, not confirmed to fail.
    - ``CreateAndUpdate`` -> INFO. Not observed live either way; the rule for
      this trigger shape is UNVERIFIED (2026-09-12) — flagged, not enforced.
    - The ``FlowTest``'s ``<flowApiName>`` does not match any ``*.flow-meta.xml``
      found under ``--manifest-dir`` -> WARN (cannot check).

Every element name and enum value above comes from the Metadata API Developer
Guide, Flow section, except rule 9's error text and the Create/Initial-only
requirement, which were proven by a live check-only deploy, not stated in the
guide. See ``references/metadata-examples.md`` for the grounded citations and
for a passing example of each shape, and ``references/gotchas.md`` for the
narrative on rule 9.

Exit codes
----------
0 -- no ERROR (and no WARN when ``--strict`` is passed)
1 -- at least one ERROR, or at least one WARN under ``--strict``

Usage
-----
    python3 check_record_triggered_flow_patterns.py --manifest-dir force-app/main/default
    python3 check_record_triggered_flow_patterns.py --manifest-dir force-app/main/default --strict
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

RECORD_TRIGGER_TYPES = {"RecordBeforeSave", "RecordAfterSave", "RecordBeforeDelete"}
VALID_STATUS = {"Active", "Draft", "Obsolete", "InvalidDraft", "UnderReview"}
VALID_RECORD_TRIGGER_TYPES = {"Create", "Update", "CreateAndUpdate", "Delete", "None"}

# Node collections that can carry a faultConnector.
FAULT_CAPABLE = ("recordCreates", "recordUpdates", "recordDeletes", "recordLookups", "actionCalls", "subflows")
# Node collections that write to the database.
DML_NODES = ("recordCreates", "recordUpdates", "recordDeletes")
# Everything that is a flow node and can therefore be a connector target.
NODE_COLLECTIONS = FAULT_CAPABLE + (
    "assignments",
    "decisions",
    "loops",
    "screens",
    "waits",
    "collectionProcessors",
    "customErrors",
    "transforms",
    "recordRollbacks",
    "steps",
    "apexPluginCalls",
)
# Connector-bearing child tags. A connector's target is its <targetReference>.
CONNECTOR_TAGS = (
    "connector",
    "faultConnector",
    "defaultConnector",
    "nextValueConnector",
    "noMoreValuesConnector",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check record-triggered Flow metadata for runtime-only failure shapes.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree to scan (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on warnings as well as errors.",
    )
    return parser.parse_args()


def _tag(el: ET.Element) -> str:
    """Local name of an element, namespace stripped."""
    return el.tag.split("}")[-1]


def _child(parent: ET.Element | None, name: str) -> ET.Element | None:
    """First direct child named `name`, or None.

    ElementTree Elements with no children are falsy, so callers MUST compare the
    result against None rather than using it in a boolean context. This helper
    exists so that rule is enforced in exactly one place.
    """
    if parent is None:
        return None
    found = parent.find(f"{NS}{name}")
    if found is None:
        found = parent.find(name)
    return found


def _text(parent: ET.Element | None, name: str) -> str | None:
    el = _child(parent, name)
    if el is None or el.text is None:
        return None
    value = el.text.strip()
    return value or None


def _children(parent: ET.Element | None, name: str) -> list[ET.Element]:
    if parent is None:
        return []
    found = parent.findall(f"{NS}{name}")
    if not found:
        found = parent.findall(name)
    return found


def _has(parent: ET.Element | None, name: str) -> bool:
    return _child(parent, name) is not None


def _node_name(node: ET.Element) -> str:
    return _text(node, "name") or "<unnamed>"


def _flow_api_name(flow_path: Path) -> str:
    """A flow's API name from its SFDX filename.

    ``Path.stem`` only strips the final suffix, so ``X.flow-meta.xml`` yields
    ``X.flow-meta`` instead of ``X`` — wrong for matching a FlowTest's
    ``<flowApiName>`` against the file that defines the flow. Strip the whole
    ``.flow-meta.xml`` extension instead.
    """
    name = flow_path.name
    if name.endswith(".flow-meta.xml"):
        return name[: -len(".flow-meta.xml")]
    return flow_path.stem


def _connector_targets(node: ET.Element, tags: tuple[str, ...] = CONNECTOR_TAGS) -> list[str]:
    """Every element this node can hand control to, via any connector shape.

    Includes connectors nested one level down (decision `rules`, start
    `scheduledPaths`, wait `waitEvents`), which is where most of them live.
    """
    targets: list[str] = []
    for connector in node.iter():
        if _tag(connector) not in tags:
            continue
        target = _text(connector, "targetReference")
        if target:
            targets.append(target)
    return targets


def _collect_nodes(root: ET.Element) -> dict[str, tuple[str, ET.Element]]:
    """Map element API name -> (collection name, element)."""
    nodes: dict[str, tuple[str, ET.Element]] = {}
    for collection in NODE_COLLECTIONS:
        for node in _children(root, collection):
            nodes[_node_name(node)] = (collection, node)
    return nodes


def _fault_targets(root: ET.Element) -> set[str]:
    """Names of elements that some other element routes its faults to."""
    targets: set[str] = set()
    for connector in root.iter():
        if _tag(connector) != "faultConnector":
            continue
        target = _text(connector, "targetReference")
        if target:
            targets.add(target)
    return targets


def _reachable_from(start_names: list[str], nodes: dict[str, tuple[str, ET.Element]], stop: set[str]) -> set[str]:
    """Breadth-first walk of the connector graph, halting at `stop` names."""
    seen: set[str] = set()
    queue = [n for n in start_names if n not in stop]
    while queue:
        current = queue.pop()
        if current in seen or current in stop:
            continue
        seen.add(current)
        entry = nodes.get(current)
        if entry is None:
            continue
        for target in _connector_targets(entry[1]):
            if target not in seen and target not in stop:
                queue.append(target)
    return seen


def check_flow(flow_path: Path, root: ET.Element) -> tuple[list[str], dict | None]:
    """Return (issues, registration) for one flow. registration is None when the
    flow is not record-triggered."""
    issues: list[str] = []
    where = flow_path.name

    start = _child(root, "start")
    trigger_type = _text(start, "triggerType")
    if trigger_type not in RECORD_TRIGGER_TYPES:
        return issues, None

    obj = _text(start, "object")
    record_trigger_type = _text(start, "recordTriggerType")
    trigger_order = _text(root, "triggerOrder")

    # 1. Start element completeness.
    if obj is None:
        issues.append(f"{where}: record-triggered flow has <triggerType>{trigger_type}</triggerType> but no <object> on <start>.")
    if record_trigger_type is None:
        issues.append(
            f"{where}: record-triggered flow has no <recordTriggerType> on <start>; "
            f"expected one of {', '.join(sorted(VALID_RECORD_TRIGGER_TYPES))}."
        )
    elif record_trigger_type not in VALID_RECORD_TRIGGER_TYPES:
        issues.append(f"{where}: <recordTriggerType>{record_trigger_type}</recordTriggerType> is not a documented value.")
    elif trigger_type == "RecordBeforeDelete" and record_trigger_type != "Delete":
        issues.append(
            f"{where}: RecordBeforeDelete flow declares <recordTriggerType>{record_trigger_type}</recordTriggerType>; "
            "a delete-triggered flow takes Delete."
        )

    # 6. apiVersion.
    if _text(root, "apiVersion") is None:
        issues.append(
            f"{where}: no <apiVersion>. It sets the flow's execution behavior — "
            "after-save flows on API 53.0 and earlier run after entitlement rules."
        )

    # 7. status enum.
    status = _text(root, "status")
    if status is None:
        issues.append(f"{where}: no <status>. A flow deployed without one lands as Draft; say so explicitly.")
    elif status not in VALID_STATUS:
        issues.append(f"{where}: <status>{status}</status> is not a documented FlowVersionStatus value.")

    nodes = _collect_nodes(root)

    # 2. Before-save must be assignment-only.
    if trigger_type == "RecordBeforeSave":
        for collection in ("recordCreates", "recordUpdates", "recordDeletes", "actionCalls", "subflows"):
            for node in _children(root, collection):
                issues.append(
                    f"{where}: before-save flow contains <{collection}> element '{_node_name(node)}'. "
                    "Assignments to $Record persist as part of the save; move side effects to an after-save flow."
                )

    # 3. After-save writing back to its own object needs a transition guard.
    if trigger_type == "RecordAfterSave" and obj:
        writes_self = [
            _node_name(node)
            for collection in DML_NODES
            for node in _children(root, collection)
            if _text(node, "object") == obj
        ]
        has_entry_criteria = _has(start, "filters") or _text(start, "filterFormula") is not None
        requires_change = (_text(start, "doesRequireRecordChangedToMeetCriteria") or "").lower() == "true"
        if writes_self and not (has_entry_criteria or requires_change):
            issues.append(
                f"{where}: after-save flow writes to its own object ({obj}) in "
                f"{', '.join(writes_self)} with no <filters>, <filterFormula>, or "
                "<doesRequireRecordChangedToMeetCriteria>. This re-enters the save procedure."
            )
        elif writes_self and has_entry_criteria and not requires_change:
            issues.append(
                f"{where}: after-save flow writes to its own object ({obj}) and has entry criteria but "
                "<doesRequireRecordChangedToMeetCriteria> is not true; the criteria test a state, not a "
                "transition, so every later edit that still matches re-fires the flow."
            )

    # 4. Fault paths.
    exempt = _fault_targets(root)
    for collection in FAULT_CAPABLE:
        for node in _children(root, collection):
            name = _node_name(node)
            if name in exempt:
                continue
            if not _has(node, "faultConnector"):
                issues.append(
                    f"{where}: <{collection}> element '{name}' has no <faultConnector>. "
                    "On failure the interview stops silently."
                )

    # 5. Get Records / DML inside a loop.
    for loop in _children(root, "loops"):
        loop_name = _node_name(loop)
        entry = _connector_targets(loop, tags=("nextValueConnector",))
        if not entry:
            continue
        body = _reachable_from(entry, nodes, stop={loop_name})
        for name in sorted(body):
            collection = nodes.get(name, ("", None))[0]
            if collection == "recordLookups":
                issues.append(
                    f"{where}: Get Records '{name}' is reachable from loop '{loop_name}'. "
                    "Query once before the loop and match in memory."
                )
            elif collection in DML_NODES:
                issues.append(
                    f"{where}: <{collection}> element '{name}' is reachable from loop '{loop_name}'. "
                    "Build a collection in the loop and perform one DML after it."
                )

    registration = {
        "file": where,
        "object": obj,
        "trigger_type": trigger_type,
        "trigger_order": trigger_order,
    }
    return issues, registration


def check_flow_tests(manifest_dir: Path, flow_registry: dict[str, dict]) -> tuple[list[str], list[str], list[str]]:
    """Rule 9: a FlowTest's Start test point must carry the $Record parameter(s)
    that match the recordTriggerType of the flow it targets.

    The flow a FlowTest targets is named by its top-level ``<flowApiName>``
    element (``api_meta.txt`` FlowTest field table; confirmed against a real
    ``*.flowtest-meta.xml`` sample, where it sits alongside ``<label>``, not
    inside ``<testPoints>``). Lookup is by that name against every
    ``*.flow-meta.xml`` filename stem under ``manifest_dir`` — SFDX source
    format names a component's file after its API name.

    Severities (proven live in a dry-run, API 67.0, 2026-09-12 — none of this
    is stated in api_meta.txt):

    - Create + InputTriggeringRecordUpdated present -> ERROR.
    - Create with InputTriggeringRecordInitial absent -> ERROR.
    - Update with exactly one of the pair -> WARN (unverified, not proven to fail).
    - CreateAndUpdate -> INFO (not observed either way; rule not enforced).
    - flowApiName not found among the manifest's flows -> WARN (cannot check).
    """
    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []

    for test_path in sorted(manifest_dir.rglob("*.flowtest-meta.xml")):
        where = test_path.name
        try:
            root = ET.parse(test_path).getroot()
        except ET.ParseError as exc:
            errors.append(f"{where}: not well-formed XML ({exc}).")
            continue

        flow_api_name = _text(root, "flowApiName")
        if not flow_api_name:
            errors.append(f"{where}: FlowTest has no <flowApiName>; cannot tell which flow it targets.")
            continue

        start_point = None
        for test_point in _children(root, "testPoints"):
            if _text(test_point, "elementApiName") == "Start":
                start_point = test_point
                break
        if start_point is None:
            continue  # no Start test point to check the $Record parameters of

        param_types = {_text(p, "type") for p in _children(start_point, "parameters")}
        param_types.discard(None)
        has_initial = "InputTriggeringRecordInitial" in param_types
        has_updated = "InputTriggeringRecordUpdated" in param_types

        flow_info = flow_registry.get(flow_api_name)
        if flow_info is None:
            warnings.append(
                f"{where}: targets flowApiName '{flow_api_name}', which does not match any "
                f"*.flow-meta.xml filename under {manifest_dir}. Cannot check its Start test "
                "point parameters against recordTriggerType."
            )
            continue

        record_trigger_type = flow_info.get("record_trigger_type")

        if record_trigger_type == "Create":
            # The org checks "is Initial present" before "is Updated absent" — proven live
            # (dry-run, API 67.0, 2026-09-12): Updated-only produces the missing-Initial
            # message, not both messages at once; Initial+Updated produces the
            # incompatible-Updated message. `elif`, not two independent `if`s, so this
            # doesn't over-report a message the org never actually shows for that shape.
            if not has_initial:
                errors.append(
                    f"{where}: targets '{flow_api_name}' (recordTriggerType Create) and its Start "
                    "test point has no InputTriggeringRecordInitial parameter. Org text: "
                    '"The test point for elementApiName \\"Start\\" is missing a parameter of type '
                    'InputTriggeringRecordInitial." This is the message whether '
                    "InputTriggeringRecordUpdated is also present or the test point carries "
                    "neither parameter — only Initial-only is the fix."
                )
            elif has_updated:
                errors.append(
                    f"{where}: targets '{flow_api_name}' (recordTriggerType Create) and its Start "
                    "test point carries an InputTriggeringRecordUpdated parameter. Org text: "
                    '"The test point for elementApiName \\"Start\\" contains the incompatible '
                    'parameter value \\"$Record\\" of type InputTriggeringRecordUpdated. Remove the '
                    'parameter or change the recordTriggerType for the flow." Create takes '
                    "InputTriggeringRecordInitial only."
                )
        elif record_trigger_type == "Update":
            if has_initial != has_updated:
                missing = "InputTriggeringRecordUpdated" if has_initial else "InputTriggeringRecordInitial"
                warnings.append(
                    f"{where}: targets '{flow_api_name}' (recordTriggerType Update) and its Start "
                    f"test point carries only one of the pair (missing {missing}). "
                    "references/metadata-examples.md § 4.1 shows Update taking both "
                    "InputTriggeringRecordInitial and InputTriggeringRecordUpdated; a single "
                    "parameter here is UNVERIFIED to fail, not the documented shape."
                )
        elif record_trigger_type == "CreateAndUpdate":
            infos.append(
                f"{where}: targets '{flow_api_name}' (recordTriggerType CreateAndUpdate). Whether "
                "its Start test point wants one or both $Record parameters is UNVERIFIED "
                "(2026-09-12) — not observed live, not stated in api_meta.txt. Not enforced."
            )
        # Delete / None / no recordTriggerType: no $Record transition parameters to check.

    return errors, warnings, infos


def check_record_triggered_flow_patterns(manifest_dir: Path) -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    infos: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"], [], []

    registrations: list[dict] = []
    flow_registry: dict[str, dict] = {}

    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        try:
            root = ET.parse(flow_path).getroot()
        except ET.ParseError as exc:
            errors.append(f"{flow_path.name}: not well-formed XML ({exc}).")
            continue
        start_for_registry = _child(root, "start")
        flow_registry[_flow_api_name(flow_path)] = {
            "trigger_type": _text(start_for_registry, "triggerType"),
            "record_trigger_type": _text(start_for_registry, "recordTriggerType"),
        }
        flow_issues, registration = check_flow(flow_path, root)
        errors.extend(flow_issues)
        if registration is not None:
            registrations.append(registration)

    # 8. triggerOrder when more than one flow shares an object + trigger type.
    by_context: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for reg in registrations:
        if reg["object"]:
            by_context[(reg["object"], reg["trigger_type"])].append(reg)

    for (obj, trigger_type), group in sorted(by_context.items()):
        if len(group) < 2:
            continue
        unset = [r["file"] for r in group if r["trigger_order"] is None]
        for name in unset:
            errors.append(
                f"{name}: {len(group)} {trigger_type} flows on {obj} in this manifest and this one has no "
                "<triggerOrder>. Their relative run order is not declared."
            )
        orders = [r["trigger_order"] for r in group if r["trigger_order"] is not None]
        duplicates = {o for o in orders if orders.count(o) > 1}
        for order in sorted(duplicates):
            tied = ", ".join(r["file"] for r in group if r["trigger_order"] == order)
            errors.append(
                f"{tied}: {trigger_type} flows on {obj} share <triggerOrder>{order}</triggerOrder>. "
                "Give each a distinct value."
            )

    # 9. FlowTest Start test point parameters vs. the target flow's recordTriggerType.
    ft_errors, ft_warnings, ft_infos = check_flow_tests(manifest_dir, flow_registry)
    errors.extend(ft_errors)
    warnings.extend(ft_warnings)
    infos.extend(ft_infos)

    return errors, warnings, infos


def coverage_note(manifest_dir: Path) -> str | None:
    """Say so when there was nothing of this type to check.

    Silence and a pass look identical to a build step's acceptance test, so an
    empty manifest gets a printed warning. It does not change the exit code:
    plenty of packages legitimately contain no Flow.
    """
    if not manifest_dir.exists():
        return None
    if any(manifest_dir.rglob("*.flow-meta.xml")):
        return None
    return (
        f"WARN: no Flow files found under --manifest-dir ({manifest_dir}); "
        "looked for *.flow-meta.xml anywhere beneath it. Nothing was checked."
    )


def print_block(title: str, lines: list[str]) -> None:
    if not lines:
        return
    print(title)
    for line in lines:
        print(f"  {line}")
    print()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    errors, warnings, infos = check_record_triggered_flow_patterns(manifest_dir)

    note = coverage_note(manifest_dir)
    if note:
        print(note)

    if not errors and not warnings and not infos:
        print("No issues found.")
        return 0

    print_block("ERROR:", errors)
    print_block("WARN:", warnings)
    print_block("INFO:", infos)

    print(f"Summary: {len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info.")

    if errors:
        return 1
    if args.strict and warnings:
        print("--strict: failing on warnings.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
