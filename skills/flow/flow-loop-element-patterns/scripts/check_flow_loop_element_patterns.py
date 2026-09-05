#!/usr/bin/env python3
"""Checker for the Flow Loop Element Patterns skill.

Parses every ``*.flow-meta.xml`` (and ``*.flow``) under --manifest-dir and reports
Loop-element defects that deploy cleanly and fail later. Stdlib only.

Checks implemented (see ../references/gotchas.md for the grounding):

  LOOP01  Assignment inside a loop body writes to the loop variable but never Adds it
          to another collection -> the edit is never persisted (Gotcha 1).
  LOOP02  Two loops over collections of the same sObject, one reachable from the
          other's nextValueConnector -> O(n*m); use a Filter processor (Gotcha 8, and
          references/metadata-examples.md section 3).
  LOOP03  A loop with no noMoreValuesConnector -> the interview has nowhere to go when
          the collection empties, including on the first evaluation (Gotcha 9).
  LOOP04  A collectionProcessors element carrying both <formula> and <conditions>
          -> conditionLogic decides which one runs; the other is silent (Gotcha 11).
  LOOP05  A Map processor (RecommendationMapCollectionProcessor) with <mapItems> and no
          <assignNextValueToReference> -> the mapping has no name for the source item.
          Also flags a collectionProcessorType outside the three documented values
          (Gotcha 12).
  LOOP06  <iterationOrder> outside {Asc, Desc} (Gotcha 8; api_meta.txt L70706-70710).

Usage:
    python3 check_flow_loop_element_patterns.py --manifest-dir force-app/main/default
    python3 check_flow_loop_element_patterns.py --manifest-dir . --quiet
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

# api_meta.txt L69934-69941 -- the only documented collectionProcessorType values.
PROCESSOR_TYPES = {
    "SortCollectionProcessor",
    "RecommendationMapCollectionProcessor",
    "FilterCollectionProcessor",
}
MAP_PROCESSOR = "RecommendationMapCollectionProcessor"

# api_meta.txt L70706-70710 -- iterationOrder is positional, not a sort direction.
ITERATION_ORDERS = {"Asc", "Desc"}

# Node collections whose children are flow elements with a <name>.
ELEMENT_TAGS = (
    "actionCalls",
    "assignments",
    "collectionProcessors",
    "decisions",
    "loops",
    "recordCreates",
    "recordDeletes",
    "recordLookups",
    "recordRollbacks",
    "recordUpdates",
    "screens",
    "subflows",
    "waits",
)

# Connector-bearing children whose <targetReference> continues the flow.
CONNECTOR_TAGS = (
    "connector",
    "nextValueConnector",
    "noMoreValuesConnector",
    "defaultConnector",
    "faultConnector",
)


def _child(elem, tag):
    """Return the first child with ``tag``, or None.

    An ElementTree Element with no children is falsy, so ``a.find(x) or a.find(y)``
    silently discards real leaf nodes. Always compare against None.
    """
    if elem is None:
        return None
    found = elem.find(NS + tag)
    return found if found is not None else None


def _text(elem, tag, default=""):
    node = _child(elem, tag)
    if node is None or node.text is None:
        return default
    return node.text.strip()


def _targets(elem):
    """All targetReference values reachable from ``elem`` (any connector kind)."""
    out = []
    for ctag in CONNECTOR_TAGS:
        for conn in elem.findall(NS + ctag):
            tref = _child(conn, "targetReference")
            if tref is not None and tref.text:
                out.append((ctag, tref.text.strip()))
    # decisions carry their outbound connectors inside <rules>
    for rule in elem.findall(NS + "rules"):
        for conn in rule.findall(NS + "connector"):
            tref = _child(conn, "targetReference")
            if tref is not None and tref.text:
                out.append(("connector", tref.text.strip()))
    return out


def _index_elements(root):
    """name -> (tag, element) for every named node in the flow."""
    index = {}
    for tag in ELEMENT_TAGS:
        for node in root.findall(NS + tag):
            name = _text(node, "name")
            if name:
                index[name] = (tag, node)
    return index


def _loop_body(loop, index):
    """Names reachable from a loop's nextValueConnector, stopping at the loop itself."""
    body, stack = set(), []
    for conn in loop.findall(NS + "nextValueConnector"):
        tref = _child(conn, "targetReference")
        if tref is not None and tref.text:
            stack.append(tref.text.strip())
    loop_name = _text(loop, "name")
    while stack:
        name = stack.pop()
        if name in body or name == loop_name or name not in index:
            continue
        body.add(name)
        _tag, node = index[name]
        for ctag, target in _targets(node):
            if ctag == "faultConnector":
                continue  # fault paths leave the loop; not part of the body
            stack.append(target)
    return body


def _collection_object(ref, index, flow_vars):
    """Best-effort sObject type behind a collectionReference."""
    if not ref:
        return None
    base = ref.split(".", 1)[0]
    if base in flow_vars:
        return flow_vars[base]
    if base in index:
        tag, node = index[base]
        if tag == "recordLookups":
            return _text(node, "object") or None
        if tag == "collectionProcessors":
            out = _text(node, "outputSObjectType")
            if out:
                return out
            return _collection_object(_text(node, "collectionReference"), index, flow_vars)
    return None


def check_flow(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path}: not well-formed XML ({exc})"]
    if not root.tag.endswith("}Flow") and root.tag != "Flow":
        return []

    index = _index_elements(root)
    flow_vars = {}
    for var in root.findall(NS + "variables"):
        name = _text(var, "name")
        if name and _text(var, "isCollection").lower() == "true":
            flow_vars[name] = _text(var, "objectType") or None

    loops = root.findall(NS + "loops")

    for loop in loops:
        lname = _text(loop, "name") or "(unnamed)"
        loop_var = _text(loop, "assignNextValueToReference")
        body = _loop_body(loop, index)

        # LOOP03 -- no exhausted path.
        if _child(loop, "noMoreValuesConnector") is None:
            issues.append(
                f"{path}: LOOP03 loop '{lname}' has no <noMoreValuesConnector>. "
                "An empty collection reaches that path on the first evaluation and the "
                "interview has nowhere to go (api_meta.txt L70714-70716)."
            )

        # LOOP06 -- iterationOrder enum.
        order_node = _child(loop, "iterationOrder")
        if order_node is not None:
            order = (order_node.text or "").strip()
            if order not in ITERATION_ORDERS:
                issues.append(
                    f"{path}: LOOP06 loop '{lname}' has <iterationOrder>{order}</iterationOrder>; "
                    "only Asc and Desc are valid, and both mean collection position, not sort "
                    "direction (api_meta.txt L70706-70710)."
                )

        # LOOP01 -- edits the loop variable without staging it.
        if loop_var:
            for name in sorted(body):
                tag, node = index[name]
                if tag != "assignments":
                    continue
                writes_loop_var = False
                adds_loop_var = False
                for item in node.findall(NS + "assignmentItems"):
                    target = _text(item, "assignToReference")
                    op = _text(item, "operator")
                    value_ref = _text(_child(item, "value"), "elementReference")
                    if target == loop_var or target.startswith(loop_var + "."):
                        if op != "Assign" or "." in target:
                            writes_loop_var = True
                    if op in {"Add", "AddAtStart"} and value_ref == loop_var:
                        adds_loop_var = True
                if writes_loop_var and not adds_loop_var:
                    issues.append(
                        f"{path}: LOOP01 assignment '{name}' inside loop '{lname}' writes to the "
                        f"loop variable '{loop_var}' but never Adds it to another collection. "
                        "Nothing on FlowLoop persists a modified loop variable; stage it and DML "
                        "the staged collection after the loop (api_meta.txt L70698-70716)."
                    )

        # LOOP02 -- nested loops over the same sObject.
        outer_obj = _collection_object(_text(loop, "collectionReference"), index, flow_vars)
        for other in loops:
            oname = _text(other, "name")
            if not oname or oname == lname or oname not in body:
                continue
            inner_obj = _collection_object(
                _text(other, "collectionReference"), index, flow_vars
            )
            same = outer_obj and inner_obj and outer_obj == inner_obj
            issues.append(
                f"{path}: LOOP02 loop '{oname}' is nested inside loop '{lname}'"
                + (f" and both iterate {outer_obj}" if same else "")
                + ". That is n*m element executions with no DML to blame; replace the inner "
                "loop with a FilterCollectionProcessor whose formula references the outer "
                f"loop variable '{loop_var or '<loop var>'}' "
                "(references/metadata-examples.md section 3)."
            )

    for proc in root.findall(NS + "collectionProcessors"):
        pname = _text(proc, "name") or "(unnamed)"
        ptype = _text(proc, "collectionProcessorType")

        # LOOP05 -- unknown type, or a Map with nothing to name the source item.
        if ptype and ptype not in PROCESSOR_TYPES:
            issues.append(
                f"{path}: LOOP05 processor '{pname}' has collectionProcessorType '{ptype}'. "
                "Only SortCollectionProcessor, RecommendationMapCollectionProcessor and "
                "FilterCollectionProcessor exist; the Map element's enum keeps the "
                "'Recommendation' prefix (api_meta.txt L69934-69941)."
            )
        if ptype == MAP_PROCESSOR and proc.findall(NS + "mapItems"):
            if not _text(proc, "assignNextValueToReference"):
                issues.append(
                    f"{path}: LOOP05 Map processor '{pname}' has <mapItems> but no "
                    "<assignNextValueToReference>, so its value expressions have no name for "
                    "the source item (api_meta.txt L69931-69933)."
                )

        # LOOP04 -- both routes populated.
        has_formula = bool(_text(proc, "formula"))
        has_conditions = bool(proc.findall(NS + "conditions"))
        if has_formula and has_conditions:
            logic = _text(proc, "conditionLogic") or "(unset)"
            issues.append(
                f"{path}: LOOP04 processor '{pname}' carries both <formula> and <conditions> "
                f"with conditionLogic '{logic}'. conditionLogic selects one route; the other is "
                "read by reviewers and ignored at runtime (api_meta.txt L69946-69960)."
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for Loop-element defects that deploy cleanly.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the 'no issues' line; still exits non-zero on findings.",
    )
    return parser.parse_args()


def check_flow_loop_element_patterns(manifest_dir: Path) -> list[str]:
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    flows = sorted(
        set(manifest_dir.rglob("*.flow-meta.xml")) | set(manifest_dir.rglob("*.flow"))
    )
    if not flows:
        return [f"No *.flow-meta.xml files found under {manifest_dir}"]

    issues: list[str] = []
    for flow in flows:
        issues.extend(check_flow(flow))
    return issues


def main() -> int:
    args = parse_args()
    issues = check_flow_loop_element_patterns(Path(args.manifest_dir))

    if not issues:
        if not args.quiet:
            print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
