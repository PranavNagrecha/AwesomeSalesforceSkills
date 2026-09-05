#!/usr/bin/env python3
"""Static checks for Flow collection-processing metadata.

Parses ``*.flow-meta.xml`` files and reports the collection-element defects that
deploy cleanly (or fail with an unhelpful enum error) and then misbehave at run
time. Every rule below cites the Metadata API Developer Guide line range it
rests on; see ``references/gotchas.md`` for the full statement of each.

Rules
-----
ERROR  E1  ``collectionProcessorType`` outside the documented three-value enum
           (api_meta.txt L69934-L69940).
ERROR  E2  A ``SortCollectionProcessor`` that carries ``limit`` but no
           ``sortOptions`` — "sorted before the limit takes effect" only holds
           when a sort is configured (api_meta.txt L69961-L69967).
ERROR  E3  A ``RecommendationMapCollectionProcessor`` missing
           ``assignNextValueToReference`` or ``outputSObjectType``
           (api_meta.txt L69931-L69932, L69979).
ERROR  E4  ``transformType`` outside the documented enum
           (api_meta.txt L72776-L72788).
ERROR  E5  An ``AssignCount`` assignment whose ``assignToReference`` names a
           variable declared in this flow with a ``dataType`` other than
           ``Number`` (api_meta.txt L69813-L69818, L72866-L72884).
ERROR  E6  An ``AddItem`` assignment whose ``assignToReference`` names a variable
           declared in this flow with a ``dataType`` other than ``Multipicklist``.
           ``AddItem`` is "supported only when the assignToReference field is a
           variable of type multipicklist" (api_meta.txt L69799-L69802); the
           collection append operator is ``Add``.
WARN   W1  A collection processor carrying BOTH ``formula`` and ``conditions``.
           The guide documents both fields and lets ``conditionLogic`` select
           between them; it never states they are mutually exclusive, so this
           is reported as WARN rather than ERROR
           (api_meta.txt L69945-L69959).
WARN   W2  A Loop whose body neither writes (recordCreates / recordUpdates /
           recordDeletes) nor calls out (actionCalls / subflows) — it only
           assigns. A Filter, Sort or Map processor usually replaces it
           (api_meta.txt L69926-L69928).
WARN   W3  A collection processor or transform whose ``collectionReference`` /
           aggregation input names nothing declared in the flow.

Exit codes
----------
0  no ERROR findings (WARNs may be present)
1  at least one ERROR, or --manifest-dir does not exist

``--strict`` promotes every WARN to ERROR.

Usage
-----
    python3 check_flow_collection_processing.py --manifest-dir force-app
    python3 check_flow_collection_processing.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://soap.sforce.com/2006/04/metadata"

# api_meta.txt L69934-L69940. There is no `MapCollectionProcessor`.
COLLECTION_PROCESSOR_TYPES = {
    "SortCollectionProcessor",            # API 50.0 and later
    "RecommendationMapCollectionProcessor",  # API 53.0 and later
    "FilterCollectionProcessor",          # API 53.0 and later
}

# api_meta.txt L72776-L72788.
TRANSFORM_TYPES = {
    "Count",
    "GetItemByIndex",   # documented, "Reserved for future use"
    "InnerJoin",        # API 63.0 and later
    "InvocableAction",  # documented, "Reserved for future use"
    "Map",
    "Sum",
}

DML_TAGS = {"recordCreates", "recordUpdates", "recordDeletes"}
SIDE_EFFECT_TAGS = DML_TAGS | {"actionCalls", "subflows", "waits", "screens", "recordRollbacks"}

# Every Flow child tag that carries a <name> and can be a connector target.
NODE_TAGS = {
    "actionCalls", "apexPluginCalls", "assignments", "collectionProcessors",
    "customErrors", "decisions", "loops", "orchestratedStages", "recordCreates",
    "recordDeletes", "recordLookups", "recordRollbacks", "recordUpdates",
    "screens", "steps", "subflows", "transforms", "waits",
}


def q(tag: str) -> str:
    """Namespace-qualify a Flow metadata tag name."""
    return f"{{{NS}}}{tag}"


def local(elem: ET.Element) -> str:
    """Return an element's tag with the Flow namespace stripped."""
    return elem.tag.split("}", 1)[-1] if "}" in elem.tag else elem.tag


def child_text(elem: ET.Element, tag: str) -> str | None:
    """Text of the first direct child named ``tag``, or None.

    Written as an explicit ``is not None`` test on purpose: an ElementTree
    element with no children is falsy, so ``elem.find(a) or elem.find(b)``
    silently discards a leaf element that was found.
    """
    found = elem.find(q(tag))
    if found is None:
        return None
    return (found.text or "").strip() or None


def has_child(elem: ET.Element, tag: str) -> bool:
    return elem.find(q(tag)) is not None


class Finding:
    __slots__ = ("severity", "rule", "path", "element", "message")

    def __init__(self, severity: str, rule: str, path: Path, element: str, message: str) -> None:
        self.severity = severity
        self.rule = rule
        self.path = path
        self.element = element
        self.message = message

    def render(self) -> str:
        return f"{self.severity} {self.rule} {self.path.name} [{self.element}]: {self.message}"


def _index_nodes(root: ET.Element) -> dict[str, ET.Element]:
    """Map every named flow node to its element."""
    nodes: dict[str, ET.Element] = {}
    for child in root:
        if local(child) not in NODE_TAGS:
            continue
        name = child_text(child, "name")
        if name:
            nodes[name] = child
    return nodes


def _index_variables(root: ET.Element) -> dict[str, dict[str, str | bool]]:
    """Map declared variable names to their dataType / isCollection / objectType."""
    variables: dict[str, dict[str, str | bool]] = {}
    for var in root.findall(q("variables")):
        name = child_text(var, "name")
        if not name:
            continue
        variables[name] = {
            "dataType": child_text(var, "dataType") or "",
            "objectType": child_text(var, "objectType") or "",
            "isCollection": (child_text(var, "isCollection") or "false").lower() == "true",
        }
    return variables


def _connector_targets(elem: ET.Element, tags: tuple[str, ...]) -> list[str]:
    targets: list[str] = []
    for tag in tags:
        for conn in elem.findall(q(tag)):
            ref = conn.find(q("targetReference"))
            if ref is not None and ref.text:
                targets.append(ref.text.strip())
    return targets


def _loop_body(loop: ET.Element, nodes: dict[str, ET.Element], loop_names: set[str]) -> list[ET.Element]:
    """Breadth-first walk of a loop body, stopping when control returns to a loop."""
    entry = _connector_targets(loop, ("nextValueConnector",))
    seen: set[str] = set()
    queue = list(entry)
    body: list[ET.Element] = []
    while queue:
        name = queue.pop(0)
        if name in seen or name in loop_names:
            continue
        seen.add(name)
        node = nodes.get(name)
        if node is None:
            continue
        body.append(node)
        queue.extend(_connector_targets(node, ("connector", "faultConnector", "defaultConnector")))
        for rule in node.findall(q("rules")):
            queue.extend(_connector_targets(rule, ("connector",)))
    return body


def check_flow(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding("ERROR", "E0", path, "(file)", f"XML does not parse — {exc}")]

    nodes = _index_nodes(root)
    variables = _index_variables(root)
    # Names a collectionReference may legally resolve to: a variable, or another
    # node whose output the flow addresses by element name.
    resolvable = set(variables) | set(nodes)

    # ---- collection processors -------------------------------------------
    for proc in root.findall(q("collectionProcessors")):
        name = child_text(proc, "name") or "(unnamed)"
        ptype = child_text(proc, "collectionProcessorType")

        if ptype not in COLLECTION_PROCESSOR_TYPES:
            findings.append(Finding(
                "ERROR", "E1", path, name,
                f"collectionProcessorType {ptype!r} is not one of "
                f"{sorted(COLLECTION_PROCESSOR_TYPES)}. The Map element's enum value is "
                "RecommendationMapCollectionProcessor; MapCollectionProcessor does not exist.",
            ))

        if ptype == "SortCollectionProcessor" and has_child(proc, "limit") and not has_child(proc, "sortOptions"):
            findings.append(Finding(
                "ERROR", "E2", path, name,
                "limit is set but sortOptions is absent, so this takes an arbitrary N rather than "
                "a top N. limit applies after the sort; add sortOptions/sortField+sortOrder or "
                "move the cap onto the upstream Get Records.",
            ))

        if ptype == "RecommendationMapCollectionProcessor":
            missing = [f for f in ("assignNextValueToReference", "outputSObjectType") if not has_child(proc, f)]
            if missing:
                findings.append(Finding(
                    "ERROR", "E3", path, name,
                    f"Map processor is missing {', '.join(missing)}. Without "
                    "assignNextValueToReference the mapItems have no source item to read; without "
                    "outputSObjectType the generated collection has no type.",
                ))

        if has_child(proc, "formula") and has_child(proc, "conditions"):
            findings.append(Finding(
                "WARN", "W1", path, name,
                "processor carries both <formula> and <conditions>. conditionLogic selects which "
                f"one runs (here: {child_text(proc, 'conditionLogic')!r}); the other is dead XML a "
                "reviewer will read as live filter criteria.",
            ))

        ref = child_text(proc, "collectionReference")
        if ref and ref.split(".", 1)[0] not in resolvable:
            findings.append(Finding(
                "WARN", "W3", path, name,
                f"collectionReference {ref!r} resolves to nothing declared in this flow.",
            ))

    # ---- transforms -------------------------------------------------------
    for tr in root.findall(q("transforms")):
        name = child_text(tr, "name") or "(unnamed)"
        for value in tr.findall(q("transformValues")):
            for action in value.findall(q("transformValueActions")):
                ttype = child_text(action, "transformType")
                if ttype not in TRANSFORM_TYPES:
                    findings.append(Finding(
                        "ERROR", "E4", path, name,
                        f"transformType {ttype!r} is not one of {sorted(TRANSFORM_TYPES)}.",
                    ))
                for param in action.findall(q("inputParameters")):
                    pval = param.find(q("value"))
                    if pval is None:
                        continue
                    eref = pval.find(q("elementReference"))
                    if eref is None or not eref.text:
                        continue
                    head = eref.text.strip().split(".", 1)[0]
                    if head not in resolvable and not head.startswith("$"):
                        findings.append(Finding(
                            "WARN", "W3", path, name,
                            f"transform input {eref.text.strip()!r} resolves to nothing declared "
                            "in this flow.",
                        ))

    # ---- assignment operator vs declared target type ----------------------
    for assign in root.findall(q("assignments")):
        name = child_text(assign, "name") or "(unnamed)"
        for item in assign.findall(q("assignmentItems")):
            operator = child_text(item, "operator")
            if operator not in ("AssignCount", "AddItem"):
                continue
            target = child_text(item, "assignToReference")
            if not target:
                continue
            head = target.split(".", 1)[0]
            declared = variables.get(head)
            if declared is None:
                # declared elsewhere (subflow input, $Flow global) — not this rule's business
                continue
            if operator == "AssignCount" and (declared["dataType"] != "Number" or declared["isCollection"]):
                findings.append(Finding(
                    "ERROR", "E5", path, name,
                    f"AssignCount writes to {target!r}, declared dataType="
                    f"{declared['dataType']!r} isCollection={declared['isCollection']}. "
                    "AssignCount yields the item count, so the target must be a non-collection "
                    "Number variable.",
                ))
            if operator == "AddItem" and declared["dataType"] != "Multipicklist":
                findings.append(Finding(
                    "ERROR", "E6", path, name,
                    f"AddItem writes to {target!r}, declared dataType="
                    f"{declared['dataType']!r} isCollection={declared['isCollection']}. "
                    "AddItem is a multi-select-picklist operator; to append to a collection use "
                    "Add, or AddAtStart to prepend.",
                ))

    # ---- loops that only shuffle a collection -----------------------------
    loop_names = {child_text(lp, "name") for lp in root.findall(q("loops"))}
    loop_names.discard(None)
    for loop in root.findall(q("loops")):
        lname = child_text(loop, "name") or "(unnamed)"
        body = _loop_body(loop, nodes, {n for n in loop_names if n})
        if not body:
            continue
        body_tags = {local(node) for node in body}
        if body_tags and body_tags.isdisjoint(SIDE_EFFECT_TAGS) and body_tags <= {"assignments", "decisions"}:
            findings.append(Finding(
                "WARN", "W2", path, lname,
                "loop body only assigns and branches — no DML, action, subflow or screen. A "
                "Collection Filter (subset), Sort (order/top N) or Map (typed copy) processor "
                "usually replaces this whole loop with one element.",
            ))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for collection-processing defects.",
    )
    parser.add_argument(
        "--manifest-dir",
        required=True,
        help="Directory searched recursively for *.flow-meta.xml files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat every WARN as an ERROR.",
    )
    args = parser.parse_args(argv)

    root_dir = Path(args.manifest_dir)
    if not root_dir.is_dir():
        print(f"ERROR --manifest-dir not found: {root_dir}")
        return 1

    flows = sorted(root_dir.rglob("*.flow-meta.xml"))
    if not flows:
        print(f"WARN no *.flow-meta.xml files under {root_dir} — nothing to check.")
        return 0

    findings: list[Finding] = []
    for flow in flows:
        findings.extend(check_flow(flow))

    if args.strict:
        for finding in findings:
            finding.severity = "ERROR"

    for finding in sorted(findings, key=lambda f: (f.severity != "ERROR", str(f.path), f.rule)):
        print(finding.render())

    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = len(findings) - errors
    print(f"\n{len(flows)} flow(s) checked — {errors} ERROR, {warns} WARN")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
