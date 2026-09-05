#!/usr/bin/env python3
"""Static review of Flow metadata (.flow-meta.xml / .flow) before deploy.

Checks, in the order they are reported:

  ERROR  hard-coded 15- or 18-character Salesforce record Id literal in an
         assignment value, a record filter, or a field input assignment
         (shape heuristic — see looks_like_record_id)
  HIGH   DML or action element (recordCreates / recordUpdates / recordDeletes /
         recordLookups / actionCalls) with no <faultConnector>
  HIGH   <status>InvalidDraft</status> — the version will not activate
  MEDIUM Get Records (recordLookups) reachable from a <loops> element
  MEDIUM more than 10 <decisions> in one flow
  LOW    record-triggered flow whose <start> has neither <filters> nor
         <filterFormula> — every save on the object starts an interview
  LOW    missing or empty <description> on the flow
  INFO   <apiVersion> older than 55.0, or absent

Stdlib only. Namespace-agnostic: the Metadata API namespace is stripped from
every tag before comparison, so files retrieved with or without the xmlns
declaration behave the same.

Never uses `element.find(a) or element.find(b)` — a leaf Element is falsy, so
that idiom silently discards real matches. Use `first_child()` below.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


FLOW_SUFFIXES = (".flow-meta.xml", ".flow")

# Elements that perform a database operation or invoke an action, and so can
# fail at run time. Metadata API Developer Guide, Flow: each of these types
# documents a faultConnector field.
DATA_ACTION_ELEMENTS = {
    "recordCreates",
    "recordDeletes",
    "recordLookups",
    "recordUpdates",
    "actionCalls",
    "apexPluginCalls",
}

# Every element type that can carry a <connector>/<targetReference> and so
# participate in the flow graph.
NODE_ELEMENTS = DATA_ACTION_ELEMENTS | {
    "assignments",
    "decisions",
    "loops",
    "screens",
    "subflows",
    "steps",
    "waits",
    "collectionProcessors",
    "transforms",
    "recordRollbacks",
    "customErrors",
    "orchestratedStages",
}

CONNECTOR_TAGS = {
    "connector",
    "faultConnector",
    "defaultConnector",
    "nextValueConnector",
    "noMoreValuesConnector",
    "timeoutConnector",
}

RECORD_TRIGGER_TYPES = {"RecordBeforeSave", "RecordAfterSave", "RecordBeforeDelete"}

# 15- or 18-character Salesforce Id: 3-char key prefix, then base-62-ish body.
# Anchored to the whole trimmed value so ordinary text is not swept up.
ID_LITERAL_RE = re.compile(r"^[a-zA-Z0-9]{3}[0-9a-zA-Z]{12}(?:[0-9a-zA-Z]{3})?$")
# A real key prefix always contains at least one digit; this rejects ordinary
# 15-letter words such as "Closedescalated" that would otherwise match.
ID_HAS_DIGIT_RE = re.compile(r"\d")

MIN_API_VERSION = 55.0
MAX_DECISIONS = 10

SEVERITY_WEIGHTS = {
    "ERROR": 25,
    "CRITICAL": 20,
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 1,
    "INFO": 0,
    "REVIEW": 0,
}


def local_name(tag: str) -> str:
    """Tag name with any XML namespace stripped."""
    return tag.split("}", 1)[-1]


def first_child(element: ET.Element, *child_names: str) -> ET.Element | None:
    """First direct child whose local name is one of child_names, else None.

    Written as an explicit `is not None` search on purpose: an ElementTree
    Element with no sub-elements is falsy, so `a.find(x) or a.find(y)` drops
    real leaf matches.
    """
    for child in element:
        if local_name(child.tag) in child_names:
            return child
    return None


def child_text(element: ET.Element, *child_names: str) -> str:
    found = first_child(element, *child_names)
    if found is None:
        return ""
    return (found.text or "").strip()


def has_child(element: ET.Element, child_name: str) -> bool:
    return first_child(element, child_name) is not None


def element_label(element: ET.Element) -> str:
    return (
        child_text(element, "name")
        or child_text(element, "label")
        or "<unnamed element>"
    )


def iter_flow_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for suffix in FLOW_SUFFIXES:
                files.extend(
                    candidate
                    for candidate in path.rglob(f"*{suffix}")
                    if candidate.is_file()
                )
        elif path.is_file() and path.name.endswith(FLOW_SUFFIXES):
            files.append(path)
    return sorted(set(files))


def looks_like_record_id(value: str) -> bool:
    value = value.strip()
    if not ID_LITERAL_RE.match(value):
        return False
    return bool(ID_HAS_DIGIT_RE.search(value[:5]))


def build_graph(
    root: ET.Element, *, include_fault: bool = True
) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Return (adjacency by element name, element name -> element type).

    With include_fault=False the fault edges are omitted, which is what
    separates "reachable on the happy path" from "reachable only after a
    fault".
    """
    tags = CONNECTOR_TAGS if include_fault else CONNECTOR_TAGS - {"faultConnector"}
    adjacency: dict[str, list[str]] = {}
    kinds: dict[str, str] = {}
    for child in root:
        tag = local_name(child.tag)
        if tag not in NODE_ELEMENTS:
            continue
        name = child_text(child, "name")
        if not name:
            continue
        kinds[name] = tag
        targets: list[str] = []
        for descendant in child.iter():
            if local_name(descendant.tag) in tags:
                target = child_text(descendant, "targetReference")
                if target:
                    targets.append(target)
        adjacency[name] = targets
    return adjacency, kinds


def fault_path_nodes(root: ET.Element) -> set[str]:
    """Element names reachable only by following a <faultConnector>.

    An element on a fault path is the last line of defence; giving it its own
    fault connector just moves the problem, so a missing one there is reported
    as INFO rather than HIGH.
    """
    adjacency, _ = build_graph(root, include_fault=False)
    normal_reachable: set[str] = set()
    fault_reachable: set[str] = set()

    start = first_child(root, "start")
    seeds: list[str] = []
    if start is not None:
        connector = first_child(start, "connector")
        if connector is not None:
            target = child_text(connector, "targetReference")
            if target:
                seeds.append(target)

    def walk(seeds: list[str], acc: set[str]) -> None:
        stack = list(seeds)
        while stack:
            node = stack.pop()
            if node in acc:
                continue
            acc.add(node)
            stack.extend(adjacency.get(node, []))

    walk(seeds, normal_reachable)

    fault_adjacency, _ = build_graph(root)
    fault_seeds: list[str] = []
    for child in root:
        for descendant in child.iter():
            if local_name(descendant.tag) == "faultConnector":
                target = child_text(descendant, "targetReference")
                if target:
                    fault_seeds.append(target)
    stack = list(fault_seeds)
    while stack:
        node = stack.pop()
        if node in fault_reachable:
            continue
        fault_reachable.add(node)
        stack.extend(fault_adjacency.get(node, []))

    # Nodes the happy path never reaches are fault-path-only.
    return fault_reachable - normal_reachable


def lookups_reachable_from_loops(root: ET.Element) -> list[tuple[str, str]]:
    """(loop name, recordLookups name) pairs where the Get is inside the loop body.

    Heuristic, and deliberately a conservative one: walk forward from each
    loops element's nextValueConnector (the "for each iteration" branch) and
    report any recordLookups reached before the walk returns to the loop
    element itself. It cannot distinguish a Get that the loop body reaches via
    a Go To connector out of the loop, so treat findings as "confirm", not
    "proven". It will not report a Get placed before the loop, which is the
    correct pattern.
    """
    adjacency, kinds = build_graph(root)
    findings: list[tuple[str, str]] = []
    for child in root:
        if local_name(child.tag) != "loops":
            continue
        loop_name = child_text(child, "name")
        entry = first_child(child, "nextValueConnector")
        if entry is None:
            continue
        start = child_text(entry, "targetReference")
        if not start:
            continue
        seen: set[str] = set()
        stack = [start]
        while stack:
            node = stack.pop()
            if node in seen or node == loop_name:
                continue
            seen.add(node)
            if kinds.get(node) == "recordLookups":
                findings.append((loop_name, node))
            stack.extend(adjacency.get(node, []))
    return findings


def audit_flow(path: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def report(severity: str, location: str, message: str) -> None:
        findings.append(
            {"severity": severity, "location": location, "message": message}
        )

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        report("ERROR", str(path), f"not well-formed XML: {exc}")
        return findings

    fault_only = fault_path_nodes(root)
    decisions = 0
    trigger_type = ""
    status = ""
    api_version = ""

    for child in root:
        tag = local_name(child.tag)

        if tag == "decisions":
            decisions += 1
        elif tag == "status":
            status = (child.text or "").strip()
        elif tag == "apiVersion":
            api_version = (child.text or "").strip()
        elif tag == "start":
            trigger_type = child_text(child, "triggerType")
            if trigger_type in RECORD_TRIGGER_TYPES and not (
                has_child(child, "filters") or has_child(child, "filterFormula")
            ):
                report(
                    "LOW",
                    f"{path}:start",
                    f"record-triggered flow ({trigger_type}) has no <filters> and no "
                    "<filterFormula> — every save on the object starts an interview",
                )

        if tag in DATA_ACTION_ELEMENTS and not has_child(child, "faultConnector"):
            if child_text(child, "name") in fault_only:
                report(
                    "INFO",
                    f"{path}:{element_label(child)}",
                    f"{tag} element on a fault path has no <faultConnector> of its "
                    "own — acceptable as a terminal notifier, but a failure here is "
                    "silent; prefer the cheapest possible action on a fault path",
                )
            else:
                report(
                    "HIGH",
                    f"{path}:{element_label(child)}",
                    f"{tag} element has no <faultConnector> — an unhandled fault rolls "
                    "back the whole triggering transaction and notifies no one",
                )

        # Hard-coded record Id literals anywhere under a node element.
        if tag in NODE_ELEMENTS or tag == "start":
            for descendant in child.iter():
                dtag = local_name(descendant.tag)
                if dtag != "stringValue":
                    continue
                value = (descendant.text or "").strip()
                if looks_like_record_id(value):
                    report(
                        "ERROR",
                        f"{path}:{element_label(child)}",
                        f"'{value}' in <{dtag}> looks like a hard-coded 15/18-character "
                        "record Id — it does not exist in the next org; use a Custom "
                        "Metadata Type, a Custom Label, or a query on a stable field. "
                        "Heuristic: 15 or 18 alphanumerics with a digit in the key "
                        "prefix, so a similarly shaped literal string can trip it",
                    )

    if status == "InvalidDraft":
        report(
            "HIGH",
            str(path),
            "<status>InvalidDraft</status> — the version references something that no "
            "longer resolves and will not activate (Setup displays this as 'Draft')",
        )

    for loop_name, lookup_name in lookups_reachable_from_loops(root):
        report(
            "MEDIUM",
            f"{path}:{lookup_name}",
            f"Get Records '{lookup_name}' is reachable from loop '{loop_name}' — one "
            "SOQL per iteration against a 100-query transaction budget. Heuristic: "
            "forward walk from the loop's nextValueConnector; confirm manually",
        )

    if decisions > MAX_DECISIONS:
        report(
            "MEDIUM",
            str(path),
            f"flow has {decisions} decision elements (threshold {MAX_DECISIONS}) — "
            "extract reusable branches into subflows",
        )

    if not child_text(root, "description"):
        report(
            "LOW",
            str(path),
            "no <description> — nothing else in the metadata records why this flow "
            "exists or who owns it",
        )

    if not api_version:
        report(
            "INFO",
            str(path),
            "no <apiVersion> — run-time behaviour is not pinned; set it explicitly",
        )
    else:
        try:
            if float(api_version) < MIN_API_VERSION:
                report(
                    "INFO",
                    str(path),
                    f"<apiVersion>{api_version}</apiVersion> is older than "
                    f"{MIN_API_VERSION:g} — the flow runs with that version's semantics",
                )
        except ValueError:
            report(
                "INFO",
                str(path),
                f"<apiVersion>{api_version}</apiVersion> is not a number",
            )

    return findings


def emit_result(findings: list[dict[str, str]], summary: str) -> int:
    score = max(
        0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in findings)
    )
    print(json.dumps({"score": score, "findings": findings, "summary": summary}, indent=2))
    blocking = [f for f in findings if f["severity"] in {"ERROR", "CRITICAL", "HIGH"}]
    if findings:
        print(f"WARN: {len(findings)} finding(s), {len(blocking)} blocking", file=sys.stderr)
    return 1 if blocking else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Flow metadata for missing fault connectors, hard-coded record Ids, "
            "queries inside loops, missing entry criteria, and stale API versions."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to scan (e.g. force-app/main/default/flows)",
    )
    parser.add_argument(
        "--manifest-dir",
        action="append",
        default=[],
        metavar="DIR",
        help="Directory of retrieved metadata to scan; repeatable. "
        "Equivalent to passing the directory positionally.",
    )
    args = parser.parse_args()

    targets = [Path(v) for v in (args.paths + args.manifest_dir)]
    if not targets:
        parser.error("provide at least one path or --manifest-dir")

    files = iter_flow_files(targets)
    if not files:
        return emit_result(
            [
                {
                    "severity": "HIGH",
                    "location": ", ".join(str(t) for t in targets),
                    "message": "no Flow metadata files found (*.flow-meta.xml, *.flow)",
                }
            ],
            "Scanned 0 Flow metadata file(s); no files matched the provided paths.",
        )

    findings: list[dict[str, str]] = []
    for path in files:
        findings.extend(audit_flow(path))

    summary = (
        f"Scanned {len(files)} Flow metadata file(s); {len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary)


if __name__ == "__main__":
    sys.exit(main())
