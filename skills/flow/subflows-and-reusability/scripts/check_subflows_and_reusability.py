#!/usr/bin/env python3
"""Validate Flow subflow contracts across a Salesforce source tree.

Unlike a single-file linter, this checker resolves every ``<subflows>`` element against
the child flow in the same manifest and validates the two files *against each other* --
the one thing neither ``sf project deploy validate`` nor a per-file review does.

Checks
------
1. RESOLVE      every ``<flowName>`` resolves to a ``*.flow-meta.xml`` in the manifest
                (WARN when the child is outside the manifest -- it may exist in the org);
                and ``<flowName>`` never carries a ``-<version>`` suffix, which
                ``FlowSubflow.flowName`` forbids (api_meta.txt L72638-72643).
2. INPUTS       every ``<inputAssignments><name>`` names a child variable whose
                ``<isInput>`` is ``true`` (api_meta.txt L72662-72672, L72886-72897).
3. OUTPUTS      every ``<outputAssignments><name>`` names a child variable whose
                ``<isOutput>`` is ``true``, and ``<assignToReference>`` names a variable
                that exists in the *parent* (api_meta.txt L72674-72684).
4. FAULT        no ``<faultConnector>`` on a ``<subflows>`` element -- ``FlowSubflow`` has
                no such field (api_meta.txt L72628-72660); and when the child performs DML
                its DML elements must carry a ``faultConnector`` and the child must expose
                an ``isOutput`` status variable the parent actually reads.
5. RECURSION    a flow never calls itself, and no two flows call each other.
6. PROCESSTYPE  the child's ``<processType>`` is ``AutoLaunchedFlow`` -- a subflow invokes
                an autolaunched flow (api_meta.txt L68751-68754) -- and the child declares
                no ``<triggerType>``, which would make it record-triggered rather than
                callable.
7. STATUS       the child's ``<status>`` is a recognised value, and a ``flowDefinitions``
                directory in the manifest is flagged because ``activeVersionNumber``
                overrides deployed ``status`` fields (api_meta.txt L73929-73934).
8. WIDTH        contract-width heuristic from SKILL.md (<= 5 inputs, <= 3 outputs) and the
                over-decomposition heuristic (> 3 subflow calls in one parent).

Stdlib only. Exit 1 when any ERROR is found; WARN lines never fail the run on their own.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

DML_TAGS = {"recordCreates", "recordUpdates", "recordDeletes"}
VALID_STATUS = {"Active", "Draft", "Obsolete", "InvalidDraft"}
MAX_INPUTS = 5
MAX_OUTPUTS = 3
MAX_SUBFLOW_CALLS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Flow subflow contracts across a source tree.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARN findings as failures too.",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def find_child(element: ET.Element, name: str) -> ET.Element | None:
    """Return the first direct child with this local name, or None.

    Never write ``element.find(a) or element.find(b)``: a leaf Element is falsy, so an
    element that exists but has no children would be discarded. Always test ``is not None``.
    """
    for child in element:
        if local_name(child.tag) == name:
            return child
    return None


def child_text(element: ET.Element, name: str) -> str:
    found = find_child(element, name)
    if found is not None and found.text:
        return found.text.strip()
    return ""


def children(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in element if local_name(c.tag) == name]


def is_true(element: ET.Element, name: str) -> bool:
    return child_text(element, name).lower() == "true"


class FlowFile:
    """One parsed ``*.flow-meta.xml``."""

    def __init__(self, path: Path, root: ET.Element) -> None:
        self.path = path
        self.root = root
        self.api_name = path.name.split(".")[0]
        self.process_type = child_text(root, "processType")
        self.status = child_text(root, "status")
        self.api_version = child_text(root, "apiVersion")
        start = find_child(root, "start")
        self.trigger_type = child_text(start, "triggerType") if start is not None else ""

        self.variables: dict[str, ET.Element] = {}
        for var in children(root, "variables"):
            name = child_text(var, "name")
            if name:
                self.variables[name] = var

        self.inputs = {n for n, v in self.variables.items() if is_true(v, "isInput")}
        self.outputs = {n for n, v in self.variables.items() if is_true(v, "isOutput")}
        self.subflow_calls = children(root, "subflows")

        self.dml_elements: list[tuple[str, str, bool]] = []
        for tag in DML_TAGS:
            for el in children(root, tag):
                self.dml_elements.append(
                    (tag, child_text(el, "name"), find_child(el, "faultConnector") is not None)
                )

        # Elements that are themselves the target of some faultConnector are already on a
        # fault path; requiring a fault path on them invites an infinite regress.
        self.fault_targets: set[str] = set()
        for el in root.iter():
            fc = find_child(el, "faultConnector")
            if fc is not None:
                target = child_text(fc, "targetReference")
                if target:
                    self.fault_targets.add(target)

    @property
    def does_dml(self) -> bool:
        return bool(self.dml_elements)


def load_flows(manifest_dir: Path, issues: list[str]) -> dict[str, FlowFile]:
    flows: dict[str, FlowFile] = {}
    for path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            issues.append(f"ERROR {path}: unable to parse flow metadata ({exc}).")
            continue
        flow = FlowFile(path, root)
        flows[flow.api_name] = flow
    return flows


def check_child_shape(parent: FlowFile, child: FlowFile, call_label: str, issues: list[str]) -> None:
    if child.process_type and child.process_type != "AutoLaunchedFlow":
        issues.append(
            f"ERROR {parent.path}: subflow `{call_label}` calls `{child.api_name}`, whose "
            f"processType is `{child.process_type}`; a subflow invokes an autolaunched flow "
            f"(api_meta.txt L68751-68754)."
        )
    if child.trigger_type and child.trigger_type != "None":
        issues.append(
            f"ERROR {parent.path}: subflow `{call_label}` calls `{child.api_name}`, which "
            f"declares triggerType `{child.trigger_type}`; a record-triggered flow starts on "
            f"record change, not on invocation."
        )
    if child.status and child.status not in VALID_STATUS:
        issues.append(
            f"ERROR {child.path}: status `{child.status}` is not one of "
            f"{sorted(VALID_STATUS)} (api_meta.txt Flow.status)."
        )
    elif child.status == "Draft":
        issues.append(
            f"WARN  {parent.path}: subflow `{call_label}` calls `{child.api_name}`, which "
            f"ships as Draft; a parent binds to the ACTIVE version, so the child must be "
            f"activated in the target org before this call resolves."
        )


def check_contract(parent: FlowFile, child: FlowFile, call: ET.Element, label: str, issues: list[str]) -> None:
    for assign in children(call, "inputAssignments"):
        name = child_text(assign, "name")
        if not name:
            issues.append(f"ERROR {parent.path}: subflow `{label}` has an inputAssignment with no <name>.")
            continue
        if name not in child.variables:
            issues.append(
                f"ERROR {parent.path}: subflow `{label}` passes `{name}`, which is not a "
                f"variable of `{child.api_name}`."
            )
        elif name not in child.inputs:
            issues.append(
                f"ERROR {parent.path}: subflow `{label}` passes `{name}`, but "
                f"`{child.api_name}` does not set <isInput>true</isInput> on it; isInput "
                f"defaults to false (api_meta.txt L72891-72897), so the value never arrives."
            )

    for assign in children(call, "outputAssignments"):
        name = child_text(assign, "name")
        target = child_text(assign, "assignToReference")
        if not name:
            issues.append(f"ERROR {parent.path}: subflow `{label}` has an outputAssignment with no <name>.")
            continue
        if name not in child.variables:
            issues.append(
                f"ERROR {parent.path}: subflow `{label}` reads `{name}`, which is not a "
                f"variable of `{child.api_name}`."
            )
        elif name not in child.outputs:
            issues.append(
                f"ERROR {parent.path}: subflow `{label}` reads `{name}`, but "
                f"`{child.api_name}` does not set <isOutput>true</isOutput> on it; isOutput "
                f"defaults to false (api_meta.txt L72918-72924), so the value comes back blank."
            )
        if target and target not in parent.variables and not target.startswith("$"):
            issues.append(
                f"WARN  {parent.path}: subflow `{label}` assigns `{name}` to "
                f"`{target}`, which is not a declared variable of this flow; "
                f"<assignToReference> names a variable in the PARENT (api_meta.txt L72679)."
            )


def check_child_fault_contract(parent: FlowFile, child: FlowFile, call: ET.Element, label: str, issues: list[str]) -> None:
    if not child.does_dml:
        return
    for tag, name, has_fault in child.dml_elements:
        if not has_fault and name not in child.fault_targets:
            issues.append(
                f"ERROR {child.path}: `{tag}` element `{name}` has no faultConnector. A "
                f"<subflows> element cannot carry one (api_meta.txt L72628-72660), so an "
                f"escaping fault gives caller `{parent.api_name}` no branch to take."
            )
    read_outputs = {child_text(a, "name") for a in children(call, "outputAssignments")}
    status_like = {n for n in child.outputs if child_text(child.variables[n], "dataType") == "Boolean"}
    if not status_like:
        issues.append(
            f"ERROR {child.path}: performs DML but exposes no Boolean isOutput variable. A "
            f"writing child needs a status output because the caller has no fault connector."
        )
    elif not (status_like & read_outputs):
        issues.append(
            f"WARN  {parent.path}: subflow `{label}` calls a writing child but reads none of "
            f"its status outputs ({sorted(status_like)}); the failure is invisible to the caller."
        )


def check_flows(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"ERROR Manifest directory not found: {manifest_dir}"]

    flows = load_flows(manifest_dir, issues)
    if not flows:
        issues.append(f"WARN  No *.flow-meta.xml files found under {manifest_dir}.")
        return issues

    for defs_dir in manifest_dir.rglob("flowDefinitions"):
        if defs_dir.is_dir() and any(defs_dir.iterdir()):
            issues.append(
                f"ERROR {defs_dir}: a non-empty flowDefinitions directory overrides the "
                f"status fields of every deployed flow via activeVersionNumber "
                f"(api_meta.txt L73929-73934). Ship Flow members only."
            )

    call_graph: dict[str, set[str]] = {}

    for parent in flows.values():
        if not parent.api_version:
            issues.append(f"WARN  {parent.path}: no <apiVersion>; the flow's execution behaviour is unpinned.")
        if not parent.subflow_calls:
            continue

        if len(parent.subflow_calls) > MAX_SUBFLOW_CALLS:
            issues.append(
                f"WARN  {parent.path}: contains {len(parent.subflow_calls)} subflow calls; "
                f"review whether the flow has been over-decomposed."
            )

        called: set[str] = set()
        for call in parent.subflow_calls:
            label = child_text(call, "name") or child_text(call, "label") or "<unnamed subflow>"
            flow_name = child_text(call, "flowName")

            if find_child(call, "faultConnector") is not None:
                issues.append(
                    f"ERROR {parent.path}: subflow `{label}` declares a <faultConnector>, "
                    f"which is not a field of FlowSubflow (api_meta.txt L72628-72660). Use a "
                    f"status output plus a Decision instead."
                )

            if not flow_name:
                issues.append(f"ERROR {parent.path}: subflow `{label}` has no <flowName>.")
                continue

            base, _, suffix = flow_name.rpartition("-")
            if base and suffix.isdigit():
                issues.append(
                    f"ERROR {parent.path}: subflow `{label}` names `{flow_name}`; flowName "
                    f"\"can't contain an appended hyphen and version number\" "
                    f"(api_meta.txt L72638-72643). A parent binds to the active version."
                )
                flow_name = base

            called.add(flow_name)
            if flow_name == parent.api_name:
                issues.append(f"ERROR {parent.path}: subflow `{label}` calls its own flow `{flow_name}` (direct recursion).")
                continue

            n_in = len(children(call, "inputAssignments"))
            n_out = len(children(call, "outputAssignments"))
            if n_in == 0 and n_out == 0:
                issues.append(
                    f"WARN  {parent.path}: subflow `{label}` has no input or output "
                    f"assignments; confirm the reusable contract is intentional."
                )
            if n_in > MAX_INPUTS or n_out > MAX_OUTPUTS:
                issues.append(
                    f"WARN  {parent.path}: subflow `{label}` has a wide contract "
                    f"({n_in} inputs, {n_out} outputs); the SKILL.md heuristic is "
                    f"<= {MAX_INPUTS} inputs and <= {MAX_OUTPUTS} outputs."
                )

            child = flows.get(flow_name)
            if child is None:
                issues.append(
                    f"WARN  {parent.path}: subflow `{label}` references `{flow_name}`, which "
                    f"is not in this manifest; the contract could not be validated."
                )
                continue

            check_child_shape(parent, child, label, issues)
            check_contract(parent, child, call, label, issues)
            check_child_fault_contract(parent, child, call, label, issues)

        call_graph[parent.api_name] = called

    for name, called in call_graph.items():
        for other in called:
            if other != name and name in call_graph.get(other, set()):
                issues.append(
                    f"ERROR {flows[name].path}: `{name}` and `{other}` call each other "
                    f"(mutual recursion between flows)."
                )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_flows(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    seen: set[str] = set()
    for issue in issues:
        if issue in seen:
            continue
        seen.add(issue)
        print(issue)

    errors = sum(1 for i in seen if i.startswith("ERROR"))
    warns = len(seen) - errors
    print(f"\n{errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
