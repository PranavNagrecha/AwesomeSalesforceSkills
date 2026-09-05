#!/usr/bin/env python3
"""Static bulkification checks for Salesforce Flow metadata.

Parses every ``*.flow-meta.xml`` (and ``*.flow``) under ``--manifest-dir`` and reports the
shapes that deploy cleanly, pass a single-interview flow test, and then exhaust a
transaction's governor budget — or silently write nothing — the first time real volume
arrives. Stdlib only; never contacts an org, never claims to run a flow.

Checks
------
1.  DML-IN-LOOP: a ``recordCreates`` / ``recordUpdates`` / ``recordDeletes`` element is
    reachable from a Loop's ``nextValueConnector`` without passing back through the loop.
    Each execution costs one DML statement against a per-transaction budget of 150
    (apexdev.txt L19554).
2.  READ-IN-LOOP: a ``recordLookups`` / ``actionCalls`` / ``apexPluginCalls`` /
    ``subflows`` element is reachable the same way. A Get costs one SOQL query against a
    budget of 100 synchronous (apexdev.txt L19544); an action or subflow can cost both.
3.  NO-COMMIT: a Loop has no ``noMoreValuesConnector``, or its ``noMoreValuesConnector``
    path reaches no DML element, while the flow declares a collection variable that the
    loop body appends to. Everything the loop staged is discarded with no error.
    ``noMoreValuesConnector`` is "The element to navigate to when all entries in the
    collection have been iterated through" (api_meta.txt L70716-70717).
4.  NO-STAGING: a Loop whose body contains no ``assignments`` element that appends to a
    declared collection variable (operator ``Add`` / ``AddAtStart``), in a flow that
    performs DML. Either the loop is doing per-record work some other way, or the
    collection pattern was started and not finished.
5.  DML-COUNT: the flow declares more than ``--max-dml`` DML elements. Each is a separate
    statement every time it executes; the budget is shared with every other automation in
    the transaction.
6.  PER-RECORD-UPDATE: a ``recordUpdates`` uses ``filters`` + ``inputAssignments`` rather
    than ``inputReference``. That form re-queries and writes one matched set per
    execution; the collection form takes a staged collection
    (api_meta.txt L71286-L71296).
7.  UNBOUNDED-SCHEDULE: a flow whose Start has ``<triggerType>Scheduled</triggerType>``
    either carries ``<object>`` — "A flow interview starts for each record that meets the
    filter conditions" (api_meta.txt L72424-72428), with no batch-size field anywhere on
    ``FlowSchedule`` (L71335-71386) — or reads records with no ``<limit>`` on the Get and
    no ``<limit>`` on a Collection Sort/Filter bounding what it commits.
8.  LOOKUP-SHAPE: a ``recordLookups`` that feeds a Loop has
    ``<getFirstRecordOnly>true</getFirstRecordOnly>``, or has
    ``storeOutputAutomatically`` false with an ``outputReference`` that is not a declared
    collection variable. Both return one record into something the flow iterates
    (api_meta.txt L71153-71162, L71195-71200).

Exit code is 1 when anything is reported, 0 otherwise.

Usage
-----
    python3 check_flow_bulkification.py --manifest-dir force-app/main/default
    python3 check_flow_bulkification.py --manifest-dir fixtures --max-dml 2
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

# Node collections that read from or write to the database, or hand off to something that can.
DML_NODES = ("recordCreates", "recordUpdates", "recordDeletes")
READ_NODES = ("recordLookups", "actionCalls", "apexPluginCalls", "subflows")
# Every flow node collection, so a connector target can be resolved to its element.
NODE_COLLECTIONS = DML_NODES + READ_NODES + (
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
)
CONNECTOR_TAGS = (
    "connector",
    "faultConnector",
    "defaultConnector",
    "nextValueConnector",
    "noMoreValuesConnector",
)
APPEND_OPERATORS = {"Add", "AddAtStart"}


# --------------------------------------------------------------------------- helpers
# ElementTree Elements with no children are falsy. Every lookup below therefore compares
# against None explicitly, and the comparison lives in exactly one place.


def _tag(el: ET.Element) -> str:
    return el.tag.split("}")[-1]


def _child(parent: ET.Element | None, name: str) -> ET.Element | None:
    if parent is None:
        return None
    found = parent.find(f"{NS}{name}")
    if found is None:
        found = parent.find(name)
    return found


def _children(parent: ET.Element | None, name: str) -> list[ET.Element]:
    if parent is None:
        return []
    found = parent.findall(f"{NS}{name}")
    if not found:
        found = parent.findall(name)
    return found


def _text(parent: ET.Element | None, name: str) -> str | None:
    el = _child(parent, name)
    if el is None or el.text is None:
        return None
    return el.text.strip() or None


def _has(parent: ET.Element | None, name: str) -> bool:
    return _child(parent, name) is not None


def _node_name(node: ET.Element) -> str:
    return _text(node, "name") or "<unnamed>"


def _connector_targets(node: ET.Element, tags: tuple[str, ...] = CONNECTOR_TAGS) -> list[str]:
    """Every element this node hands control to, through any connector shape.

    Connectors nested one level down are included — decision `rules`, wait `waitEvents`,
    start `scheduledPaths` — which is where most of them live.
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
    nodes: dict[str, tuple[str, ET.Element]] = {}
    for collection in NODE_COLLECTIONS:
        for node in _children(root, collection):
            nodes[_node_name(node)] = (collection, node)
    return nodes


def _walk(seeds: list[str], nodes: dict[str, tuple[str, ET.Element]], stop: set[str]) -> set[str]:
    """Breadth-first walk of the connector graph, halting at `stop` names."""
    seen: set[str] = set()
    queue = [n for n in seeds if n not in stop]
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


def _collection_variables(root: ET.Element) -> set[str]:
    names: set[str] = set()
    for var in _children(root, "variables"):
        if (_text(var, "isCollection") or "").lower() == "true":
            name = _text(var, "name")
            if name:
                names.add(name)
    return names


def _loop_body(loop: ET.Element, nodes: dict[str, tuple[str, ET.Element]]) -> set[str]:
    """Element names reachable from this loop's nextValueConnector.

    The walk stops at the loop itself (the back edge that closes the cycle) and at every
    target of its noMoreValuesConnector, so the after-last path is never counted as loop
    body. Fault paths are followed: an element on a fault route inside a loop still costs
    per iteration when the fault repeats.
    """
    loop_name = _node_name(loop)
    after_last = set(_connector_targets(loop, ("noMoreValuesConnector",)))
    seeds = _connector_targets(loop, ("nextValueConnector",))
    return _walk(seeds, nodes, stop={loop_name} | after_last)


# --------------------------------------------------------------------------- checks


def check_flow(path: Path, root: ET.Element, max_dml: int) -> list[str]:
    issues: list[str] = []
    where = path.name
    nodes = _collect_nodes(root)
    loops = _children(root, "loops")
    collection_vars = _collection_variables(root)
    dml_names = {_node_name(n) for c in DML_NODES for n in _children(root, c)}

    # --- 1 & 2: database elements on a loop path
    for loop in loops:
        loop_name = _node_name(loop)
        body = _loop_body(loop, nodes)
        for name in sorted(body):
            entry = nodes.get(name)
            if entry is None:
                continue
            collection = entry[0]
            if collection in DML_NODES:
                issues.append(
                    f"{where}: DML-IN-LOOP — <{collection}> '{name}' is reachable from "
                    f"loop '{loop_name}' via nextValueConnector. One DML statement per "
                    f"iteration per interview, against 150 per transaction. Stage into a "
                    f"collection variable inside the loop and commit once on "
                    f"noMoreValuesConnector."
                )
            elif collection in READ_NODES:
                issues.append(
                    f"{where}: READ-IN-LOOP — <{collection}> '{name}' is reachable from "
                    f"loop '{loop_name}' via nextValueConnector. Query or call once above "
                    f"the loop and match in memory; 100 SOQL queries per synchronous "
                    f"transaction is the budget this spends."
                )

        # --- 3: the loop stages work and never commits it
        after_last = _connector_targets(loop, ("noMoreValuesConnector",))
        staged = _staged_collections(loop, body, nodes, collection_vars)
        if staged and not after_last:
            issues.append(
                f"{where}: NO-COMMIT — loop '{loop_name}' appends to "
                f"{', '.join(sorted(staged))} but has no <noMoreValuesConnector>. "
                f"Everything the loop staged is discarded when the interview ends, with "
                f"no error and no fault path."
            )
        elif staged:
            reachable_after = _walk(after_last, nodes, stop={loop_name})
            if not (reachable_after & dml_names):
                issues.append(
                    f"{where}: NO-COMMIT — loop '{loop_name}' appends to "
                    f"{', '.join(sorted(staged))} and its noMoreValuesConnector path "
                    f"reaches no Create/Update/Delete Records element. The collection is "
                    f"built and never written."
                )

        # --- 4: a loop that does not stage, in a flow that writes
        if not staged and dml_names:
            issues.append(
                f"{where}: NO-STAGING — loop '{loop_name}' has no Assignment appending to "
                f"a declared collection variable (operator Add/AddAtStart), yet the flow "
                f"performs DML. Either the loop writes per record, or the collection "
                f"pattern was started and not finished."
            )

    # --- 5: DML element count
    if len(dml_names) > max_dml:
        issues.append(
            f"{where}: DML-COUNT — {len(dml_names)} DML elements "
            f"({', '.join(sorted(dml_names))}) exceeds --max-dml {max_dml}. Every one is "
            f"a separate statement each time it executes, drawn from the same 150 the "
            f"object's Apex triggers and other flows are also spending."
        )

    # --- 6: per-record update shape
    for node in _children(root, "recordUpdates"):
        name = _node_name(node)
        if _has(node, "inputReference"):
            continue
        if _has(node, "filters") or _has(node, "inputAssignments"):
            issues.append(
                f"{where}: PER-RECORD-UPDATE — <recordUpdates> '{name}' uses "
                f"filters/inputAssignments instead of <inputReference>. That form "
                f"re-queries and writes one matched set per execution; the bulk-safe form "
                f"passes a staged collection through <inputReference>."
            )

    # --- 7: scheduled flow without a bounded working set
    start = _child(root, "start")
    if start is not None and _text(start, "triggerType") == "Scheduled":
        if _has(start, "object"):
            issues.append(
                f"{where}: UNBOUNDED-SCHEDULE — schedule-triggered flow carries <object>"
                f"{_text(start, 'object')}</object> on <start>, so one interview starts "
                f"per record that meets the filter conditions. FlowSchedule has no "
                f"batch-size field; maxBatchSize belongs to scheduled paths on "
                f"record-triggered flows. Drop <object> and bound a single interview with "
                f"a Get <limit> and a Collection Sort <limit>."
            )
        else:
            lookups = _children(root, "recordLookups")
            unbounded = [_node_name(n) for n in lookups if not _has(n, "limit")]
            sort_bounded = any(_has(n, "limit") for n in _children(root, "collectionProcessors"))
            if lookups and unbounded and not sort_bounded:
                issues.append(
                    f"{where}: UNBOUNDED-SCHEDULE — scheduled flow reads "
                    f"{', '.join(sorted(unbounded))} with no <limit>, and no Collection "
                    f"Filter/Sort <limit> bounds what it commits. The working set is "
                    f"whatever the org happens to hold on the night it runs."
                )

    # --- 8: a Get that feeds a Loop but returns one record
    looped_sources = {_text(loop, "collectionReference") for loop in loops}
    looped_sources.discard(None)
    for node in _children(root, "recordLookups"):
        name = _node_name(node)
        auto = (_text(node, "storeOutputAutomatically") or "").lower() == "true"
        output_ref = _text(node, "outputReference")
        feeds_loop = name in looped_sources or (output_ref is not None and output_ref in looped_sources)
        if not feeds_loop:
            continue
        if (_text(node, "getFirstRecordOnly") or "").lower() == "true":
            issues.append(
                f"{where}: LOOKUP-SHAPE — <recordLookups> '{name}' feeds a loop but sets "
                f"<getFirstRecordOnly>true</getFirstRecordOnly>. It stores one record even "
                f"when many match, so the loop iterates once and the flow looks correct."
            )
        if not auto and output_ref is not None and output_ref not in collection_vars:
            issues.append(
                f"{where}: LOOKUP-SHAPE — <recordLookups> '{name}' feeds a loop through "
                f"<outputReference>{output_ref}</outputReference>, which is not a variable "
                f"declared with <isCollection>true</isCollection>. With "
                f"storeOutputAutomatically false, the variable's shape is what decides "
                f"whether one record or many are stored."
            )

    return issues


def _staged_collections(
    loop: ET.Element,
    body: set[str],
    nodes: dict[str, tuple[str, ET.Element]],
    collection_vars: set[str],
) -> set[str]:
    """Collection variables this loop's body appends to with Add / AddAtStart."""
    staged: set[str] = set()
    for name in body:
        entry = nodes.get(name)
        if entry is None or entry[0] != "assignments":
            continue
        for item in _children(entry[1], "assignmentItems"):
            target = _text(item, "assignToReference")
            operator = _text(item, "operator")
            if target in collection_vars and operator in APPEND_OPERATORS:
                staged.add(target)
    return staged


# --------------------------------------------------------------------------- driver


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for bulkification failures that only appear at volume.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree to scan (default: current directory).",
    )
    parser.add_argument(
        "--max-dml",
        type=int,
        default=3,
        help="Report flows declaring more than this many DML elements (default: 3).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ISSUE: manifest directory not found: {manifest_dir}")
        return 1

    paths = sorted(set(manifest_dir.rglob("*.flow-meta.xml")) | set(manifest_dir.rglob("*.flow")))
    if not paths:
        print(f"No *.flow-meta.xml found under {manifest_dir}.")
        return 0

    issues: list[str] = []
    for path in paths:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            issues.append(f"{path.name}: unable to parse flow metadata ({exc}).")
            continue
        issues.extend(check_flow(path, root, args.max_dml))

    if not issues:
        print(f"No issues found across {len(paths)} flow(s).")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    print(f"\n{len(issues)} finding(s) across {len(paths)} flow(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
