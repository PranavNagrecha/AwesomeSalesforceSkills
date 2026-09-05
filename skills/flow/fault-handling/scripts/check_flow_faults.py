#!/usr/bin/env python3
"""Static checks for Flow fault handling.

Parses every ``*.flow-meta.xml`` under ``--manifest-dir`` and reports the fault-path
shapes that deploy cleanly and then lose the error at run time. Stdlib only; never
contacts an org, never claims to run a flow.

Checks
------
1.  Every fault-capable element on a non-fault path carries a ``faultConnector``.
    Fault-capable means the metadata type documents the field: ``recordCreates``,
    ``recordUpdates``, ``recordDeletes``, ``recordLookups``, ``actionCalls``,
    ``apexPluginCalls``, ``waits`` (Metadata API Developer Guide, Flow section).
2.  Every ``faultConnector`` (and every other connector) points at an element that
    exists in the same file.
3.  A DML element that sits *on* a fault path has its own ``faultConnector``. The
    exception is a write to a platform event (``object`` ending ``__e``), which is
    the documented way to leave evidence that outlives a rollback.
4.  ``$Flow.FaultMessage`` is referenced only from elements reachable from a
    ``faultConnector``. It is set by taking the fault connector, so anywhere else it
    is empty.
5.  ``recordRollbacks`` appears only in a screen flow (``processType`` = ``Flow``).
6.  ``customErrors`` appears only in a record-triggered flow (``start`` declares a
    record ``triggerType``).
7.  ``subflows`` never carries a ``faultConnector`` — ``FlowSubflow`` has no such
    field.
8.  Every ``customErrors`` element carries the ``connector`` the guide marks Required.

Grounding for every element name, enum value and version floor above is cited by
``grep -n`` line in ``references/metadata-examples.md`` and ``references/gotchas.md``.

Usage
-----
    python3 check_flow_faults.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

# Node collections whose metadata type documents a faultConnector field.
FAULT_CAPABLE = (
    "recordCreates",
    "recordUpdates",
    "recordDeletes",
    "recordLookups",
    "actionCalls",
    "apexPluginCalls",
    "waits",
)
# Node collections that write to the database.
DML_NODES = ("recordCreates", "recordUpdates", "recordDeletes")
# Every collection whose members are flow nodes, and therefore connector targets.
NODE_COLLECTIONS = FAULT_CAPABLE + (
    "assignments",
    "decisions",
    "loops",
    "screens",
    "subflows",
    "steps",
    "customErrors",
    "recordRollbacks",
    "collectionProcessors",
    "transforms",
    "orchestratedStages",
)
# Connector-bearing child tags. A connector's target is its <targetReference>.
CONNECTOR_TAGS = (
    "connector",
    "faultConnector",
    "defaultConnector",
    "nextValueConnector",
    "noMoreValuesConnector",
    "timeoutConnector",
)
# triggerType values that make a flow record-triggered.
RECORD_TRIGGER_TYPES = {"RecordBeforeSave", "RecordAfterSave", "RecordBeforeDelete"}

FAULT_MESSAGE = "$Flow.FaultMessage"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for fault paths that lose the error.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree to scan (default: current directory).",
    )
    return parser.parse_args()


def _tag(el: ET.Element) -> str:
    """Local name of an element, namespace stripped."""
    return el.tag.split("}")[-1]


def _child(parent: ET.Element | None, name: str) -> ET.Element | None:
    """First direct child named `name`, or None.

    ElementTree Elements with no children are falsy, so callers MUST compare the
    result against None rather than using it in a boolean context. Keeping that
    rule in one helper is why this function exists.
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


def _node_name(node: ET.Element) -> str:
    return _text(node, "name") or "<unnamed>"


def _connectors(node: ET.Element) -> list[tuple[str, str]]:
    """Every (connector tag, target name) this node can hand control to.

    Includes connectors nested one level down, which is where a decision's rule
    connectors and a wait's event connectors live.
    """
    out: list[tuple[str, str]] = []
    for scope in (node,) + tuple(node):
        for child in scope:
            if _tag(child) not in CONNECTOR_TAGS:
                continue
            target = _text(child, "targetReference")
            if target:
                out.append((_tag(child), target))
    return out


def _subtree_text(node: ET.Element) -> str:
    return "".join(part for part in node.itertext() if part)


def _collect_nodes(root: ET.Element) -> dict[str, tuple[str, ET.Element]]:
    """name -> (collection tag, element) for every flow node in the file."""
    nodes: dict[str, tuple[str, ET.Element]] = {}
    for collection in NODE_COLLECTIONS:
        for node in _children(root, collection):
            nodes[_node_name(node)] = (collection, node)
    return nodes


def _fault_reachable(nodes: dict[str, tuple[str, ET.Element]]) -> set[str]:
    """Every node reachable from any faultConnector, following all connectors."""
    frontier: deque[str] = deque()
    seen: set[str] = set()
    for _collection, node in nodes.values():
        for tag, target in _connectors(node):
            if tag == "faultConnector" and target not in seen:
                seen.add(target)
                frontier.append(target)
    while frontier:
        name = frontier.popleft()
        entry = nodes.get(name)
        if entry is None:
            continue
        for _tag_name, target in _connectors(entry[1]):
            if target not in seen:
                seen.add(target)
                frontier.append(target)
    return seen


def check_flow(path: Path) -> list[str]:
    label = path.name
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{label}: not well-formed XML ({exc}). Nothing else could be checked."]

    issues: list[str] = []
    nodes = _collect_nodes(root)
    on_fault_path = _fault_reachable(nodes)
    process_type = _text(root, "processType")
    start = _child(root, "start")
    trigger_type = _text(start, "triggerType") if start is not None else None
    is_record_triggered = trigger_type in RECORD_TRIGGER_TYPES

    # 2. Dangling connector targets.
    for name, (collection, node) in sorted(nodes.items()):
        for tag, target in _connectors(node):
            if target not in nodes:
                issues.append(
                    f"{label}: `{name}` ({collection}) has a <{tag}> pointing at "
                    f"`{target}`, which is not an element in this file."
                )

    for name, (collection, node) in sorted(nodes.items()):
        has_fault = any(tag == "faultConnector" for tag, _ in _connectors(node))

        # 7. FlowSubflow has no faultConnector field.
        if collection == "subflows" and has_fault:
            issues.append(
                f"{label}: `{name}` is a subflow with a <faultConnector>. FlowSubflow has "
                "no such field - handle the failure inside the child flow and return the "
                "outcome through an outputAssignment the parent branches on."
            )

        # 1 and 3. Fault-capable elements without a fault path.
        if collection in FAULT_CAPABLE and not has_fault:
            if name in on_fault_path:
                if collection in DML_NODES:
                    obj = _text(node, "object") or ""
                    if not obj.endswith("__e"):
                        issues.append(
                            f"{label}: `{name}` ({collection} on {obj or 'unknown object'}) "
                            "writes records from inside a fault path and has no "
                            "<faultConnector> of its own. If the original failure was a "
                            "governor limit, this write fails too and the run leaves "
                            "nothing behind. Give it a fault path, or make the last hop a "
                            "platform event."
                        )
            else:
                issues.append(
                    f"{label}: `{name}` ({collection}) has no <faultConnector>. An "
                    "unhandled fault here ends the interview and the transaction is never "
                    "committed."
                )

        # 4. $Flow.FaultMessage outside a fault branch.
        if FAULT_MESSAGE in _subtree_text(node) and name not in on_fault_path:
            issues.append(
                f"{label}: `{name}` ({collection}) references {FAULT_MESSAGE} but is not "
                "reachable from any <faultConnector>. The global is set by taking the "
                "fault connector, so it is empty here."
            )

        # 8. Custom Error elements need the connector the guide marks Required.
        if collection == "customErrors" and _child(node, "connector") is None:
            issues.append(
                f"{label}: `{name}` is a customErrors element with no <connector>. "
                "FlowCustomError.connector is documented as Required even though Flow "
                "Builder draws the element as terminal."
            )

    # 5. Roll Back Records outside a screen flow.
    for node in _children(root, "recordRollbacks"):
        if process_type != "Flow":
            issues.append(
                f"{label}: `{_node_name(node)}` is a recordRollbacks element in a flow "
                f"whose processType is {process_type or 'unset'}. FlowRecordRollback is "
                "available only in screen flows (processType Flow)."
            )

    # 6. Custom Error outside a record-triggered flow.
    for node in _children(root, "customErrors"):
        if not is_record_triggered:
            issues.append(
                f"{label}: `{_node_name(node)}` is a customErrors element in a flow with "
                f"triggerType {trigger_type or 'unset'}. The Custom Error element rolls "
                "back the change that triggered the flow, which only means something in a "
                "record-triggered flow."
            )

    return issues


def coverage_note(manifest_dir: Path) -> str | None:
    """Say so when there was nothing of this type to check.

    Silence and a pass look identical to a build step, so an empty manifest gets a
    printed warning. It does not change the exit code: plenty of packages contain no
    Flow at all.
    """
    if not manifest_dir.exists():
        print(f"ERROR: --manifest-dir ({manifest_dir}) does not exist.", file=sys.stderr)
        sys.exit(2)
    if any(manifest_dir.rglob("*.flow-meta.xml")):
        return None
    return (
        f"WARN: no Flow files found under --manifest-dir ({manifest_dir}); "
        "looked for *.flow-meta.xml anywhere beneath it. Nothing was checked."
    )


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    note = coverage_note(manifest_dir)
    if note:
        print(note)
        return 0

    issues: list[str] = []
    for path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        issues.extend(check_flow(path))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
