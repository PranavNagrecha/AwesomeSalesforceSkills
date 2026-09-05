#!/usr/bin/env python3
"""Static governor-limit budget for Flow metadata.

Parses every ``*.flow-meta.xml`` under ``--manifest-dir``, estimates what each
flow spends from the per-transaction meters, and reports the shapes that make a
budget unbudgetable. Stdlib only.

What it can and cannot know
---------------------------
Element counts are arithmetic and are reported exactly. CPU time and heap are
NOT estimated: the developer guides publish no per-element cost, and CPU
"is calculated for all executions on the Salesforce application servers"
including any Apex an action calls (apexdev.txt footnote 5, L19652-L19657).
Any tool that prints a millisecond figure from element counts invented it.
Measure CPU and heap from FLOW_INTERVIEW_FINISHED_LIMIT_USAGE instead
(references/metadata-examples.md section 7a).

Ceilings quoted below are the synchronous per-transaction limits from the Apex
Developer Guide's governor-limit table (apexdev.txt L19542-L19599).

Rules
-----
ERROR    E0  the file does not parse as XML.
ERROR    E1  a DML element (recordCreates / recordUpdates / recordDeletes) is
             reachable from a loop's nextValueConnector. The DML statement meter
             is 150 per transaction (apexdev.txt L19554); one statement per
             iteration breaches it at iteration 150 regardless of batch size.
             This rule reports the fact only - the refactor (collection staging,
             where to put the Assignment, when to escalate to Apex) belongs to
             flow/flow-bulkification and its checker. One rule here, not five.
WARN     W1  a recordLookups element is reachable from a loop's
             nextValueConnector. SOQL queries are 100 per transaction
             (apexdev.txt L19544). WARN rather than ERROR because a Get inside a
             loop over a small, provably bounded collection is survivable where
             a DML is not - but it is never free.
WARN     W2  the non-loop DML elements of every Active flow sharing one
             object + triggerType sum above --dml-budget (default 10). Limits are
             per transaction, not per flow: every one of those flows spends from
             the same 150 statements on the same save.
ADVISORY A1  an actionCalls element with actionType "apex" carries no
             flowTransactionModel. The field is Required on FlowActionCall
             (api_meta.txt L68472-L68479); when it is absent the effective model
             is not visible in source, so the action's own SOQL/DML/CPU cannot be
             attributed to a transaction by reading the file.
ADVISORY A2  a flow has 3 or more DML elements and no scheduled path at all, or
             scheduled paths but none with pathType AsyncAfterCommit
             (api_meta.txt L71412-L71414). Everything is atomic with the save the
             user is waiting on. That may be correct - it is a design question,
             which is why this is advisory.

Exit codes
----------
0  no ERROR findings
1  at least one ERROR, or --manifest-dir does not exist

--strict promotes every WARN to ERROR and every ADVISORY to WARN.

Usage
-----
    python3 check_flow_governor_limits_deep_dive.py --manifest-dir force-app
    python3 check_flow_governor_limits_deep_dive.py --manifest-dir force-app --strict
    python3 check_flow_governor_limits_deep_dive.py --manifest-dir force-app --dml-budget 6
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

NS = "http://soap.sforce.com/2006/04/metadata"

# apexdev.txt L19554, L19556, L19544, L19546, L19575, L19598-L19599.
DML_STATEMENT_LIMIT = 150
DML_ROW_LIMIT = 10_000
SOQL_QUERY_LIMIT = 100
SOQL_ROW_LIMIT = 50_000
EMAIL_INVOCATION_LIMIT = 10
PUBLISH_IMMEDIATE_LIMIT = 150

DML_TAGS = ("recordCreates", "recordUpdates", "recordDeletes")
SOQL_TAGS = ("recordLookups",)

# api_meta.txt L68729, L68731 - the two actionType values that spend the email
# invocation meter rather than a DML or SOQL one.
EMAIL_ACTION_TYPES = {"emailAlert", "emailSimple"}

# Every Flow child tag that carries a <name> and can be a connector target.
NODE_TAGS = {
    "actionCalls", "apexPluginCalls", "assignments", "collectionProcessors",
    "customErrors", "decisions", "loops", "orchestratedStages", "recordCreates",
    "recordDeletes", "recordLookups", "recordRollbacks", "recordUpdates",
    "screens", "steps", "subflows", "transforms", "waits",
}

SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}


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
    silently discards a leaf element that was in fact found.
    """
    found = elem.find(q(tag))
    if found is None:
        return None
    return (found.text or "").strip() or None


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


class FlowBudget:
    """The arithmetic half of a flow's governor spend."""

    __slots__ = (
        "path", "label", "status", "trigger_object", "trigger_type",
        "dml_outside", "dml_inside", "soql_outside", "soql_inside",
        "actions_outside", "actions_inside", "email_actions",
        "apex_actions_no_model", "apex_actions_new_txn",
        "scheduled_paths", "async_paths", "subflows",
    )

    def __init__(self, path: Path) -> None:
        self.path = path
        self.label = path.name
        self.status = ""
        self.trigger_object = ""
        self.trigger_type = ""
        self.dml_outside: list[str] = []
        self.dml_inside: list[str] = []
        self.soql_outside: list[str] = []
        self.soql_inside: list[str] = []
        self.actions_outside: list[str] = []
        self.actions_inside: list[str] = []
        self.email_actions: list[str] = []
        self.apex_actions_no_model: list[str] = []
        self.apex_actions_new_txn: list[str] = []
        self.scheduled_paths: list[str] = []
        self.async_paths: list[str] = []
        self.subflows: list[str] = []

    @property
    def trigger_key(self) -> str:
        return f"{self.trigger_object or '(none)'}/{self.trigger_type or '(none)'}"

    def render(self) -> str:
        parts = [
            f"  {self.path.name}  status={self.status or '(unset)'}  on={self.trigger_key}",
            f"    DML elements       : {len(self.dml_outside)} outside a loop"
            f"  / {len(self.dml_inside)} inside  (statement ceiling {DML_STATEMENT_LIMIT},"
            f" row ceiling {DML_ROW_LIMIT})",
            f"    Get Records        : {len(self.soql_outside)} outside a loop"
            f"  / {len(self.soql_inside)} inside  (query ceiling {SOQL_QUERY_LIMIT},"
            f" row ceiling {SOQL_ROW_LIMIT})",
            f"    Actions            : {len(self.actions_outside)} outside a loop"
            f"  / {len(self.actions_inside)} inside"
            f"  ({len(self.email_actions)} spend the email meter, ceiling {EMAIL_INVOCATION_LIMIT})",
            f"    Subflows           : {len(self.subflows)} (spend the parent's meters)",
            f"    Scheduled paths    : {len(self.scheduled_paths)}"
            f"  ({len(self.async_paths)} AsyncAfterCommit)",
            "    CPU / heap         : not estimated - no per-element cost is published;"
            " read FLOW_INTERVIEW_FINISHED_LIMIT_USAGE",
        ]
        return "\n".join(parts)


def _connector_targets(elem: ET.Element, tags: tuple[str, ...]) -> list[str]:
    targets: list[str] = []
    for tag in tags:
        for conn in elem.findall(q(tag)):
            ref = conn.find(q("targetReference"))
            if ref is not None and ref.text:
                targets.append(ref.text.strip())
    return targets


def _index_nodes(root: ET.Element) -> dict[str, ET.Element]:
    nodes: dict[str, ET.Element] = {}
    for child in root:
        if local(child) not in NODE_TAGS:
            continue
        name = child_text(child, "name")
        if name:
            nodes[name] = child
    return nodes


def _loop_body_names(root: ET.Element, nodes: dict[str, ET.Element]) -> set[str]:
    """Names of every node reachable from any loop's nextValueConnector.

    The walk stops when control returns to a loop element, which is what closes
    the body: a Flow loop body ends by connecting back to the Loop itself.
    """
    loop_names = {n for n in (child_text(lp, "name") for lp in root.findall(q("loops"))) if n}
    inside: set[str] = set()
    for loop in root.findall(q("loops")):
        queue = _connector_targets(loop, ("nextValueConnector",))
        seen: set[str] = set()
        while queue:
            name = queue.pop(0)
            if name in seen or name in loop_names:
                continue
            seen.add(name)
            node = nodes.get(name)
            if node is None:
                continue
            inside.add(name)
            queue.extend(_connector_targets(node, ("connector", "faultConnector", "defaultConnector")))
            for rule in node.findall(q("rules")):
                queue.extend(_connector_targets(rule, ("connector",)))
            for wait_event in node.findall(q("waitEvents")):
                queue.extend(_connector_targets(wait_event, ("connector",)))
    return inside


def analyse_flow(path: Path) -> tuple[FlowBudget | None, list[Finding]]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return None, [Finding("ERROR", "E0", path, "(file)", f"XML does not parse - {exc}")]

    budget = FlowBudget(path)
    findings: list[Finding] = []

    budget.label = child_text(root, "label") or path.name
    budget.status = child_text(root, "status") or ""

    start = root.find(q("start"))
    if start is not None:
        budget.trigger_object = child_text(start, "object") or ""
        budget.trigger_type = child_text(start, "triggerType") or ""
        for sp in start.findall(q("scheduledPaths")):
            sp_name = child_text(sp, "name") or "(unnamed path)"
            budget.scheduled_paths.append(sp_name)
            if (child_text(sp, "pathType") or "") == "AsyncAfterCommit":
                budget.async_paths.append(sp_name)

    nodes = _index_nodes(root)
    inside = _loop_body_names(root, nodes)

    for tag in DML_TAGS:
        for elem in root.findall(q(tag)):
            name = child_text(elem, "name") or "(unnamed)"
            if name in inside:
                budget.dml_inside.append(name)
                findings.append(Finding(
                    "ERROR", "E1", path, name,
                    f"<{tag}> is reachable from a loop's nextValueConnector. The DML statement "
                    f"meter is {DML_STATEMENT_LIMIT} per transaction, so this breaches at "
                    "iteration 150 whatever the batch size. Stage the records in a collection and "
                    "put one DML after the loop - flow/flow-bulkification owns the refactor.",
                ))
            else:
                budget.dml_outside.append(name)

    for tag in SOQL_TAGS:
        for elem in root.findall(q(tag)):
            name = child_text(elem, "name") or "(unnamed)"
            if name in inside:
                budget.soql_inside.append(name)
                findings.append(Finding(
                    "WARN", "W1", path, name,
                    f"<{tag}> is reachable from a loop's nextValueConnector. The SOQL query meter "
                    f"is {SOQL_QUERY_LIMIT} per transaction and it is shared with every trigger, "
                    "validation rule and flow on this save. Hoist the Get above the loop and match "
                    "in memory - flow/flow-get-records-optimization owns the query shape.",
                ))
            else:
                budget.soql_outside.append(name)

    for elem in root.findall(q("subflows")):
        budget.subflows.append(child_text(elem, "name") or "(unnamed)")

    for elem in root.findall(q("actionCalls")):
        name = child_text(elem, "name") or "(unnamed)"
        action_type = child_text(elem, "actionType") or ""
        model = child_text(elem, "flowTransactionModel")
        if name in inside:
            budget.actions_inside.append(name)
        else:
            budget.actions_outside.append(name)
        if action_type in EMAIL_ACTION_TYPES:
            budget.email_actions.append(name)
        if action_type == "apex":
            if model is None:
                budget.apex_actions_no_model.append(name)
                findings.append(Finding(
                    "ADVISORY", "A1", path, name,
                    "actionType is apex but flowTransactionModel is absent. The field is Required "
                    "on FlowActionCall and selects Automatic / CurrentTransaction / NewTransaction; "
                    "with it unset, whether this action's own SOQL, DML and CPU land in this "
                    "transaction cannot be read off the source. State it explicitly.",
                ))
            elif model == "NewTransaction":
                budget.apex_actions_new_txn.append(name)

    if len(budget.email_actions) > EMAIL_INVOCATION_LIMIT:
        findings.append(Finding(
            "WARN", "W1", path, budget.email_actions[0],
            f"{len(budget.email_actions)} email actions in one flow against a ceiling of "
            f"{EMAIL_INVOCATION_LIMIT} email invocations for the whole transaction.",
        ))

    dml_total = len(budget.dml_outside) + len(budget.dml_inside)
    if dml_total >= 3 and not budget.async_paths:
        if budget.scheduled_paths:
            detail = (
                f"{len(budget.scheduled_paths)} scheduled path(s) but none with pathType "
                "AsyncAfterCommit, so nothing runs post-commit"
            )
        else:
            detail = "no scheduled path at all"
        findings.append(Finding(
            "ADVISORY", "A2", path, budget.label,
            f"{dml_total} DML elements and {detail}. Everything here is atomic with the save the "
            "user is waiting on. If any of it need not be, an AsyncAfterCommit path moves it onto "
            "its own budget - flow/flow-transactional-boundaries owns where the boundary belongs.",
        ))

    return budget, findings


def cross_flow_findings(budgets: list[FlowBudget], dml_budget: int) -> list[Finding]:
    """W2: Active flows on the same object + triggerType share one DML meter."""
    findings: list[Finding] = []
    groups: dict[str, list[FlowBudget]] = defaultdict(list)
    for b in budgets:
        if b.status != "Active" or not b.trigger_object:
            continue
        groups[b.trigger_key].append(b)

    for key, group in sorted(groups.items()):
        total = sum(len(b.dml_outside) for b in group)
        if total <= dml_budget:
            continue
        detail = ", ".join(f"{b.path.name}={len(b.dml_outside)}" for b in sorted(group, key=lambda x: x.path.name))
        findings.append(Finding(
            "WARN", "W2", group[0].path, key,
            f"{len(group)} Active flow(s) on {key} declare {total} non-loop DML elements together "
            f"(threshold {dml_budget}; --dml-budget changes it). They all fire on the same save and "
            f"spend from one {DML_STATEMENT_LIMIT}-statement, {DML_ROW_LIMIT}-row budget, alongside "
            f"any Apex trigger on the object. Breakdown: {detail}.",
        ))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Estimate Flow governor-limit spend and flag the shapes that make it unbudgetable.",
    )
    parser.add_argument(
        "--manifest-dir",
        required=True,
        help="Directory searched recursively for *.flow-meta.xml files.",
    )
    parser.add_argument(
        "--dml-budget",
        type=int,
        default=10,
        help="W2 threshold: non-loop DML elements summed across Active flows on one "
             "object + triggerType (default 10).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote every WARN to ERROR and every ADVISORY to WARN.",
    )
    args = parser.parse_args(argv)

    root_dir = Path(args.manifest_dir)
    if not root_dir.is_dir():
        print(f"ERROR --manifest-dir not found: {root_dir}")
        return 1

    flows = sorted(root_dir.rglob("*.flow-meta.xml"))
    if not flows:
        print(f"WARN no *.flow-meta.xml files under {root_dir} - nothing to check.")
        return 0

    budgets: list[FlowBudget] = []
    findings: list[Finding] = []
    for flow in flows:
        budget, flow_findings = analyse_flow(flow)
        findings.extend(flow_findings)
        if budget is not None:
            budgets.append(budget)

    findings.extend(cross_flow_findings(budgets, args.dml_budget))

    if args.strict:
        for finding in findings:
            if finding.severity == "WARN":
                finding.severity = "ERROR"
            elif finding.severity == "ADVISORY":
                finding.severity = "WARN"

    print("Static budget (element counts only):")
    for budget in budgets:
        print(budget.render())
    print()

    for finding in sorted(
        findings,
        key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), str(f.path), f.rule, f.element),
    ):
        print(finding.render())

    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = sum(1 for f in findings if f.severity == "WARN")
    advisories = sum(1 for f in findings if f.severity == "ADVISORY")
    print(f"\n{len(flows)} flow(s) checked - {errors} ERROR, {warns} WARN, {advisories} ADVISORY")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
