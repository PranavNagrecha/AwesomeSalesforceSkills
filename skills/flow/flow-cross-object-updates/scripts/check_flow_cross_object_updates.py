#!/usr/bin/env python3
"""check_flow_cross_object_updates.py — static checks for cross-object writes in Flow.

Reads a Salesforce source tree (``--manifest-dir``) and inspects, together:

  * ``*.flow-meta.xml``  — the flows, their triggering object, and what they write
  * ``*.field-meta.xml`` and inline ``<fields>`` in ``*.object-meta.xml`` / ``*.object``
    — the relationship fields the flows write across

Several of the rules below are only decidable when both sides are present, which is why
this checker looks at the whole tree rather than one file.

Rules
-----
ERROR    DML_IN_LOOP        A ``recordUpdates`` / ``recordCreates`` / ``recordDeletes``
                            element is reachable from a Loop's ``nextValueConnector``.
                            One rule only; `flow/flow-bulkification` owns the subject.
ERROR    PING_PONG          Flow A is triggered on object X and updates object Y, flow B
                            is triggered on Y and updates X, both are ``Active``, and
                            neither carries ``doesRequireRecordChangedToMeetCriteria``
                            nor an entry ``filterFormula``. Nothing breaks the cycle.
WARN     NO_PARENT_GUARD    A ``recordUpdates`` whose ``inputReference`` is a
                            ``$Record.<Relationship>`` path, in a flow with no
                            ``decisions`` condition referencing that lookup. Heuristic.
WARN     UNBOUNDED_CHILD_GET A collection ``recordLookups`` with no ``<limit>`` and/or no
                            filter on the triggering record's Id.
ADVISORY ROLLUP_BY_LOOP     A Loop stages an ``Add`` onto a Number/Currency variable —
                            an aggregate — while a MasterDetail relationship exists
                            between the two objects, where a roll-up summary would do.
ADVISORY SETNULL_ASSUMED    A flow reads or writes through a Lookup whose effective
                            ``deleteConstraint`` is ``SetNull`` (the documented default)
                            without an ``IsNull`` guard on it.

Exit codes
----------
0  no ERROR (WARN / ADVISORY may be present), or an empty tree
1  at least one ERROR, or ``--manifest-dir`` does not exist

``--strict`` promotes every WARN to an ERROR. ADVISORY is never promoted; it is a design
observation, not a defect.

Usage:
    python3 check_flow_cross_object_updates.py --manifest-dir force-app/main/default
    python3 check_flow_cross_object_updates.py --manifest-dir force-app/main/default --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}
DML_TAGS = ("recordUpdates", "recordCreates", "recordDeletes")
NODE_TAGS = (
    "actionCalls", "assignments", "decisions", "loops", "recordCreates",
    "recordDeletes", "recordLookups", "recordUpdates", "screens", "subflows",
    "waits", "collectionProcessors", "transforms", "customErrors", "recordRollbacks",
)
NUMERIC_TYPES = {"Number", "Currency"}
RECORD_PATH_RE = re.compile(r"^\$Record\.(\w+)$")


# --------------------------------------------------------------------------- helpers
# ElementTree leaf Elements are falsy, so `el.find(a) or el.find(b)` silently discards a
# real match. Every lookup below goes through these two helpers instead.

def child(el, tag: str):
    """The first child element named `tag`, or None. Never used in a boolean context."""
    if el is None:
        return None
    found = el.find(f"sf:{tag}", NS)
    return found if found is not None else None


def text_of(el, tag: str, default: str = "") -> str:
    found = child(el, tag)
    if found is None:
        return default
    return (found.text or default).strip()


def children(el, tag: str) -> list:
    if el is None:
        return []
    return el.findall(f"sf:{tag}", NS)


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- models

class FlowFile:
    def __init__(self, path: Path, root: ET.Element):
        self.path = path
        self.root = root
        self.name = path.name.split(".")[0]
        self.status = text_of(root, "status")
        start = child(root, "start")
        self.start = start
        self.trigger_object = text_of(start, "object") if start is not None else ""
        self.trigger_type = text_of(start, "triggerType") if start is not None else ""
        self.filter_formula = text_of(start, "filterFormula") if start is not None else ""
        self.start_requires_change = (
            text_of(start, "doesRequireRecordChangedToMeetCriteria").lower() == "true"
            if start is not None else False
        )
        # any decision rule may also carry the flag
        self.rule_requires_change = any(
            text_of(rule, "doesRequireRecordChangedToMeetCriteria").lower() == "true"
            for dec in children(root, "decisions")
            for rule in children(dec, "rules")
        )
        self.nodes: dict[str, tuple[str, ET.Element]] = {}
        for tag in NODE_TAGS:
            for el in children(root, tag):
                nm = text_of(el, "name")
                if nm:
                    self.nodes[nm] = (tag, el)
        self.variables = {
            text_of(v, "name"): text_of(v, "dataType") for v in children(root, "variables")
        }
        self.updated_objects = {
            text_of(el, "object") for el in children(root, "recordUpdates") if text_of(el, "object")
        }

    @property
    def is_record_triggered(self) -> bool:
        return self.trigger_type.startswith("Record") and bool(self.trigger_object)

    @property
    def breaks_cycle(self) -> bool:
        return self.start_requires_change or self.rule_requires_change or bool(self.filter_formula)

    def successors(self, name: str) -> set[str]:
        """Names reachable in one hop from node `name`, following every connector kind."""
        entry = self.nodes.get(name)
        if entry is None:
            return set()
        _tag, el = entry
        out: set[str] = set()
        for conn_tag in ("connector", "nextValueConnector", "noMoreValuesConnector",
                         "defaultConnector", "faultConnector"):
            for conn in children(el, conn_tag):
                tref = text_of(conn, "targetReference")
                if tref:
                    out.add(tref)
        for rule in children(el, "rules"):
            for conn in children(rule, "connector"):
                tref = text_of(conn, "targetReference")
                if tref:
                    out.add(tref)
        for wt in children(el, "waitEvents"):
            for conn in children(wt, "connector"):
                tref = text_of(conn, "targetReference")
                if tref:
                    out.add(tref)
        return out

    def loop_bodies(self) -> dict[str, set[str]]:
        """For each loop, the node names on its nextValueConnector path, stopping at the
        loop itself (the back-edge) and at its noMoreValuesConnector target."""
        bodies: dict[str, set[str]] = {}
        for loop_name, (tag, el) in self.nodes.items():
            if tag != "loops":
                continue
            nxt = child(el, "nextValueConnector")
            if nxt is None:
                bodies[loop_name] = set()
                continue
            exits = {loop_name}
            done = child(el, "noMoreValuesConnector")
            if done is not None:
                exit_ref = text_of(done, "targetReference")
                if exit_ref:
                    exits.add(exit_ref)
            seen: set[str] = set()
            stack = [text_of(nxt, "targetReference")]
            while stack:
                cur = stack.pop()
                if not cur or cur in seen or cur in exits:
                    continue
                seen.add(cur)
                stack.extend(self.successors(cur))
            bodies[loop_name] = seen
        return bodies


class FieldDef:
    def __init__(self, api_name: str, sobject: str, el: ET.Element):
        self.api_name = api_name
        self.sobject = sobject
        self.type = text_of(el, "type")
        self.reference_to = text_of(el, "referenceTo")
        self.relationship_name = text_of(el, "relationshipName")
        # SetNull "is the default" per api_meta.txt L43350-43356
        self.delete_constraint = text_of(el, "deleteConstraint", "SetNull")


# --------------------------------------------------------------------------- loading

def load_flows(root: Path) -> list[FlowFile]:
    flows: list[FlowFile] = []
    for path in sorted(root.rglob("*.flow-meta.xml")):
        try:
            flows.append(FlowFile(path, ET.parse(path).getroot()))
        except ET.ParseError as exc:
            print(f"ERROR {rel(path, root)}: unparseable XML — {exc}", file=sys.stderr)
    return flows


def load_fields(root: Path) -> list[FieldDef]:
    fields: list[FieldDef] = []
    for path in sorted(root.rglob("*.field-meta.xml")):
        try:
            el = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        # .../objects/<Object>/fields/<Field>.field-meta.xml
        parts = path.parts
        sobject = parts[-3] if len(parts) >= 3 and parts[-2] == "fields" else ""
        api = text_of(el, "fullName") or path.name.split(".")[0]
        fields.append(FieldDef(api, sobject, el))
    for pattern in ("*.object-meta.xml", "*.object"):
        for path in sorted(root.rglob(pattern)):
            try:
                el = ET.parse(path).getroot()
            except ET.ParseError:
                continue
            sobject = path.name.split(".")[0]
            for f in children(el, "fields"):
                api = text_of(f, "fullName")
                if api:
                    fields.append(FieldDef(api, sobject, f))
    return fields


# --------------------------------------------------------------------------- rules

def rule_dml_in_loop(flow: FlowFile, root: Path, out: list[tuple[str, str]]) -> None:
    for loop_name, body in flow.loop_bodies().items():
        for node_name in sorted(body):
            tag, _el = flow.nodes.get(node_name, ("", None))
            if tag in DML_TAGS:
                out.append((
                    "ERROR",
                    f"{rel(flow.path, root)}: DML_IN_LOOP — '{node_name}' ({tag}) is reachable "
                    f"from loop '{loop_name}' nextValueConnector. Stage in an Assignment and "
                    f"move the DML after the loop; see flow/flow-bulkification",
                ))


def rule_ping_pong(flows: list[FlowFile], root: Path, out: list[tuple[str, str]]) -> None:
    active = [f for f in flows if f.is_record_triggered and f.status == "Active"]
    seen: set[tuple[str, str]] = set()
    for a in active:
        for b in active:
            if a is b:
                continue
            if b.trigger_object not in a.updated_objects:
                continue
            if a.trigger_object not in b.updated_objects:
                continue
            key = tuple(sorted((a.name, b.name)))
            if key in seen:
                continue
            seen.add(key)
            if a.breaks_cycle or b.breaks_cycle:
                continue
            out.append((
                "ERROR",
                f"{rel(a.path, root)}: PING_PONG — Active flow '{a.name}' on {a.trigger_object} "
                f"updates {b.trigger_object}, and Active flow '{b.name}' on {b.trigger_object} "
                f"updates {a.trigger_object}. Neither carries "
                f"doesRequireRecordChangedToMeetCriteria nor an entry filterFormula, so nothing "
                f"stops the write cycle before stack depth 16",
            ))


def _guarded_lookups(flow: FlowFile) -> set[str]:
    """Field/relationship names appearing on the left side of any Decision condition."""
    guarded: set[str] = set()
    for _name, (tag, el) in flow.nodes.items():
        if tag != "decisions":
            continue
        for rule in children(el, "rules"):
            for cond in children(rule, "conditions"):
                left = text_of(cond, "leftValueReference")
                if left.startswith("$Record."):
                    guarded.add(left[len("$Record."):].rstrip("."))
    if flow.filter_formula:
        guarded.update(re.findall(r"\$Record\.(\w+)", flow.filter_formula))
    return guarded


def rule_no_parent_guard(flow: FlowFile, root: Path, out: list[tuple[str, str]]) -> None:
    guarded = _guarded_lookups(flow)
    for name, (tag, el) in sorted(flow.nodes.items()):
        if tag != "recordUpdates":
            continue
        ref = text_of(el, "inputReference")
        if not ref.startswith("$Record."):
            continue
        path_tail = ref[len("$Record."):]
        if "." in path_tail or path_tail.endswith("__r"):
            relationship = path_tail.split(".")[0]
            lookup = relationship[:-3] + "__c" if relationship.endswith("__r") else relationship
            if relationship in guarded or lookup in guarded:
                continue
            out.append((
                "WARN",
                f"{rel(flow.path, root)}: NO_PARENT_GUARD — '{name}' updates the parent through "
                f"'{ref}' but no Decision condition references '{lookup}'. If the lookup is empty "
                f"the traversal resolves to nothing; add an IsNull branch before the update",
            ))


def rule_unbounded_child_get(flow: FlowFile, root: Path, out: list[tuple[str, str]]) -> None:
    if not flow.is_record_triggered:
        return
    for name, (tag, el) in sorted(flow.nodes.items()):
        if tag != "recordLookups":
            continue
        if text_of(el, "getFirstRecordOnly").lower() == "true":
            continue
        has_limit = child(el, "limit") is not None
        filters_on_parent = False
        for filt in children(el, "filters"):
            val = child(filt, "value")
            if val is None:
                continue
            eref = text_of(val, "elementReference")
            if eref in ("$Record.Id", "$Record.id"):
                filters_on_parent = True
        if has_limit and filters_on_parent:
            continue
        missing = []
        if not filters_on_parent:
            missing.append("a filter on $Record.Id")
        if not has_limit:
            missing.append("a <limit>")
        out.append((
            "WARN",
            f"{rel(flow.path, root)}: UNBOUNDED_CHILD_GET — '{name}' queries "
            f"{text_of(el, 'object') or 'an object'} without {' and without '.join(missing)}. "
            f"One interview per triggering record shares 10,000 DML rows per transaction",
        ))


def rule_rollup_by_loop(flow: FlowFile, fields: list[FieldDef], root: Path,
                        out: list[tuple[str, str]]) -> None:
    master_detail_pairs = {
        (f.sobject, f.reference_to) for f in fields if f.type == "MasterDetail" and f.reference_to
    }
    if not master_detail_pairs:
        return
    for loop_name, body in flow.loop_bodies().items():
        loop_el = flow.nodes[loop_name][1]
        source = text_of(loop_el, "collectionReference")
        source_entry = flow.nodes.get(source)
        child_object = ""
        if source_entry is not None and source_entry[0] == "recordLookups":
            child_object = text_of(source_entry[1], "object")
        if (child_object, flow.trigger_object) not in master_detail_pairs:
            continue
        for node_name in sorted(body):
            tag, el = flow.nodes.get(node_name, ("", None))
            if tag != "assignments":
                continue
            for item in children(el, "assignmentItems"):
                if text_of(item, "operator") != "Add":
                    continue
                target = text_of(item, "assignToReference")
                if flow.variables.get(target) in NUMERIC_TYPES:
                    out.append((
                        "ADVISORY",
                        f"{rel(flow.path, root)}: ROLLUP_BY_LOOP — '{node_name}' accumulates onto "
                        f"the {flow.variables[target]} variable '{target}' while looping "
                        f"{child_object}, which is MasterDetail to {flow.trigger_object}. A "
                        f"Summary CustomField (summaryOperation Sum/Count) computes this without "
                        f"a flow; see references/metadata-examples.md § 5.3",
                    ))


def rule_setnull_assumed(flow: FlowFile, fields: list[FieldDef], root: Path,
                         out: list[tuple[str, str]]) -> None:
    if not flow.trigger_object:
        return
    guarded = _guarded_lookups(flow)
    body = ET.tostring(flow.root, encoding="unicode")
    for f in fields:
        if f.type != "Lookup" or f.sobject != flow.trigger_object:
            continue
        if f.delete_constraint != "SetNull":
            continue
        # The parent-side traversal name comes from the FIELD api name (Subscription__c ->
        # Subscription__r; AccountId -> Account), never from relationshipName, which is the
        # child-relationship name used from the parent side.
        if f.api_name.endswith("__c"):
            traversal = f.api_name[:-3] + "__r"
        elif f.api_name.endswith("Id") and len(f.api_name) > 2:
            traversal = f.api_name[:-2]
        else:
            traversal = f.api_name
        used = (f"$Record.{f.api_name}" in body) or (f"$Record.{traversal}" in body)
        if not used:
            continue
        if f.api_name in guarded or traversal in guarded:
            continue
        out.append((
            "ADVISORY",
            f"{rel(flow.path, root)}: SETNULL_ASSUMED — the flow reads or writes through "
            f"{flow.trigger_object}.{f.api_name}, a Lookup whose deleteConstraint resolves to "
            f"SetNull (the documented default). Deleting the parent clears this field and leaves "
            f"orphan children the flow will still be triggered on",
        ))


# --------------------------------------------------------------------------- driver

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Check cross-object write patterns in Flow metadata.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--manifest-dir", default=".",
                    help="Root of the Salesforce source tree to scan.")
    ap.add_argument("--strict", action="store_true",
                    help="Promote every WARN to an ERROR. ADVISORY is never promoted.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: --manifest-dir not found: {root}", file=sys.stderr)
        return 1

    flows = load_flows(root)
    if not flows:
        print(f"WARN: no *.flow-meta.xml under {root} — nothing to check.")
        return 0
    fields = load_fields(root)

    findings: list[tuple[str, str]] = []
    for flow in flows:
        rule_dml_in_loop(flow, root, findings)
        rule_no_parent_guard(flow, root, findings)
        rule_unbounded_child_get(flow, root, findings)
        rule_rollup_by_loop(flow, fields, root, findings)
        rule_setnull_assumed(flow, fields, root, findings)
    rule_ping_pong(flows, root, findings)

    if args.strict:
        findings = [("ERROR", m) if sev == "WARN" else (sev, m) for sev, m in findings]

    order = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}
    findings.sort(key=lambda x: (order[x[0]], x[1]))
    errors = sum(1 for sev, _ in findings if sev == "ERROR")

    if not findings:
        print(f"OK: {len(flows)} flow(s), {len(fields)} field definition(s) scanned; "
              f"no cross-object findings.")
        return 0
    for sev, msg in findings:
        stream = sys.stderr if sev == "ERROR" else sys.stdout
        print(f"{sev} {msg}", file=stream)
    print(f"\n{len(flows)} flow(s), {len(fields)} field definition(s) scanned; "
          f"{errors} error(s), {len(findings) - errors} non-blocking finding(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
