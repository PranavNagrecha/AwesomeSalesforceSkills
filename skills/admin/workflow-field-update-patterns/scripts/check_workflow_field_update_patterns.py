#!/usr/bin/env python3
"""Static checks for field-update automation in a retrieved metadata tree.

Reads `*.workflow-meta.xml` (and `*.workflow`) plus `*.flow-meta.xml` (and
`*.flow`) under a manifest directory and reports the high-confidence problems
documented in this skill, then prints a migration inventory.

Checks
------
ERROR
  E1  Field update with `<operation>Formula</operation>` and a missing or empty
      `<formula>`. The guide requires the formula when the operation is Formula
      (Metadata API Developer Guide, WorkflowFieldUpdate, api_meta.txt:140126).

WARN
  W1  Any `<fieldUpdates>` block at all — deprecated for new actions; migrate
      to a record-triggered Flow (references/gotchas.md § 3).
  W2  Active rule whose field update writes a custom field that is not present
      in `objects/<Object>/fields/`. Only reported when that folder exists in
      the tree, so a partial retrieve does not produce noise.
  W3  Active rule with `<triggerType>onAllChanges</triggerType>` whose field
      update writes a field the same rule filters on — re-evaluation loop risk
      (references/gotchas.md § 11).
  W4  Active workflow rule writing field F on object O while a before-save Flow
      on O also assigns `$Record.F` — two writers, and the Flow's write is
      overwritten by the workflow rule at step 11 (references/gotchas.md § 10).
  W5  After-save record-triggered Flow that updates its own triggering record
      with no ISCHANGED-style entry condition — recursion risk
      (references/gotchas.md § 2).
  W6  More than one record-triggered Flow with the same object and trigger type
      — non-deterministic ordering (references/gotchas.md § 7).

Inventory
---------
Counts of workflow files, active rules, field updates by operation,
`reevaluateOnChange` flags, time triggers and failed migration attempts —
the numbers a migration estimate needs.

Stdlib only.

Usage:
    python3 check_workflow_field_update_patterns.py --manifest-dir force-app/main/default
    python3 check_workflow_field_update_patterns.py --manifest-dir . --quiet-inventory
    python3 check_workflow_field_update_patterns.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"

WORKFLOW_GLOBS = ("*.workflow-meta.xml", "*.workflow")
FLOW_GLOBS = ("*.flow-meta.xml", "*.flow")


# --------------------------------------------------------------------------- #
# ElementTree helpers
#
# NOTE: never write `el.find(a) or el.find(b)`. An Element with no children is
# falsy even when it exists, so that idiom silently discards real matches.
# Always compare against None.
# --------------------------------------------------------------------------- #

def _strip_ns(tag: str) -> str:
    return tag[len(_NS_TAG):] if tag.startswith(_NS_TAG) else tag


def _child(parent, *names):
    """First direct child matching any of ``names``, or None.

    Namespace-tolerant: matches both the namespaced and bare forms.
    """
    if parent is None:
        return None
    for name in names:
        found = parent.find(f"{_NS_TAG}{name}")
        if found is not None:
            return found
        found = parent.find(name)
        if found is not None:
            return found
    return None


def _text(parent, *names) -> str:
    """Stripped text of the first matching child, or "" when absent/empty."""
    el = _child(parent, *names)
    if el is None or el.text is None:
        return ""
    return el.text.strip()


def _children(parent, name) -> list:
    if parent is None:
        return []
    found = parent.findall(f"{_NS_TAG}{name}")
    if found:
        return found
    return parent.findall(name)


def _object_name_from_path(path: Path) -> str:
    """`workflows/Opportunity.workflow-meta.xml` -> `Opportunity`."""
    stem = path.name
    for suffix in (".workflow-meta.xml", ".workflow"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return path.stem


def _unqualify(field_ref: str) -> str:
    """`Opportunity.Amount` -> `Amount`; `Amount` -> `Amount`."""
    return field_ref.rsplit(".", 1)[-1] if field_ref else ""


# --------------------------------------------------------------------------- #
# Parsed shapes
# --------------------------------------------------------------------------- #

class WorkflowFile:
    def __init__(self, path: Path, obj: str):
        self.path = path
        self.object_name = obj
        # fullName -> {"field", "operation", "formula", "reevaluate", "target"}
        self.field_updates: dict[str, dict[str, str]] = {}
        # list of {"name", "active", "triggerType", "criteria_fields",
        #          "formula", "field_update_names", "time_trigger_count",
        #          "failed_migration"}
        self.rules: list[dict] = []

    @property
    def active_rules(self) -> list[dict]:
        return [r for r in self.rules if r["active"]]


def parse_workflow(path: Path) -> WorkflowFile | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None
    if _strip_ns(root.tag) != "Workflow":
        return None

    wf = WorkflowFile(path, _object_name_from_path(path))

    for fu in _children(root, "fieldUpdates"):
        full_name = _text(fu, "fullName")
        if not full_name:
            continue
        wf.field_updates[full_name] = {
            "field": _text(fu, "field"),
            "operation": _text(fu, "operation"),
            "formula": _text(fu, "formula"),
            "literal": _text(fu, "literalValue"),
            "lookup_type": _text(fu, "lookupValueType"),
            "reevaluate": _text(fu, "reevaluateOnChange").lower(),
            "target": _text(fu, "targetObject"),
        }

    for rule in _children(root, "rules"):
        criteria_fields = []
        for item in _children(rule, "criteriaItems"):
            field_ref = _text(item, "field")
            if field_ref:
                criteria_fields.append(_unqualify(field_ref))
        fu_names = []
        for action in _children(rule, "actions"):
            if _text(action, "type") == "FieldUpdate":
                action_name = _text(action, "name")
                if action_name:
                    fu_names.append(action_name)
        wf.rules.append({
            "name": _text(rule, "fullName"),
            "active": _text(rule, "active").lower() == "true",
            "triggerType": _text(rule, "triggerType"),
            "criteria_fields": criteria_fields,
            "formula": _text(rule, "formula"),
            "field_update_names": fu_names,
            "time_trigger_count": len(_children(rule, "workflowTimeTriggers")),
            "failed_migration": _text(rule, "failedMigrationToolVersion"),
        })
    return wf


class FlowFile:
    def __init__(self, path: Path):
        self.path = path
        self.object_name = ""
        self.trigger_type = ""
        self.record_trigger_type = ""
        self.status = ""
        # fields written on $Record by before-save assignments
        self.record_assign_fields: set[str] = set()
        self.same_object_update_names: list[str] = []
        self.has_change_guard = False


def parse_flow(path: Path) -> FlowFile | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None
    if _strip_ns(root.tag) != "Flow":
        return None

    start = _child(root, "start")
    if start is None:
        return None

    obj = _text(start, "object")
    trigger_type = _text(start, "triggerType")
    if not obj or not trigger_type:
        return None

    flow = FlowFile(path)
    flow.object_name = obj
    flow.trigger_type = trigger_type
    flow.record_trigger_type = _text(start, "recordTriggerType")
    flow.status = _text(root, "status")

    # Before-save writes: Assignment items targeting $Record.<Field>.
    for assignment in _children(root, "assignments"):
        for item in _children(assignment, "assignmentItems"):
            ref = _text(item, "assignToReference")
            if ref.startswith("$Record."):
                field = ref.split(".", 1)[1]
                if field and "." not in field:
                    flow.record_assign_fields.add(field)

    # After-save writes back to the triggering record.
    for ru in _children(root, "recordUpdates"):
        ru_object = _text(ru, "object")
        input_ref = _text(ru, "inputReference")
        targets_record = input_ref in {"$Record", "Record", "$Record__Prior"}
        targets_same_object = bool(ru_object) and ru_object == obj
        if targets_record or targets_same_object:
            flow.same_object_update_names.append(_text(ru, "name") or "(unnamed)")

    # Entry-condition change guard.
    for filt in _children(start, "filters"):
        operator = _text(filt, "operator")
        if "Changed" in operator:
            flow.has_change_guard = True
            break
    filter_formula = _text(start, "filterFormula")
    if "ISCHANGED" in filter_formula.upper() or "PRIORVALUE" in filter_formula.upper():
        flow.has_change_guard = True
    if _text(start, "doesRequireRecordChangedToMeetCriteria").lower() == "true":
        flow.has_change_guard = True

    return flow


# --------------------------------------------------------------------------- #
# Object field inventory (for W2)
# --------------------------------------------------------------------------- #

def index_object_fields(root: Path) -> dict[str, set[str]]:
    """objects/<Object>/fields/<Field>.field-meta.xml -> {Object: {Field, ...}}.

    Only objects that actually have a `fields` folder in the tree appear, so
    W2 stays quiet on a partial retrieve.
    """
    index: dict[str, set[str]] = {}
    for fields_dir in root.rglob("fields"):
        if not fields_dir.is_dir():
            continue
        obj_dir = fields_dir.parent
        names: set[str] = set()
        for f in fields_dir.iterdir():
            if f.name.endswith(".field-meta.xml"):
                names.add(f.name[: -len(".field-meta.xml")])
            elif f.suffix == ".field":
                names.add(f.stem)
        if names:
            index.setdefault(obj_dir.name, set()).update(names)
    return index


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def check_workflows(
    workflows: list[WorkflowFile],
    flows: list[FlowFile],
    field_index: dict[str, set[str]],
    root: Path,
) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []

    # Before-save Flow writes, keyed by object.
    before_save_writes: dict[str, list[tuple[str, FlowFile]]] = defaultdict(list)
    for flow in flows:
        if flow.trigger_type != "RecordBeforeSave":
            continue
        if flow.status and flow.status != "Active":
            continue
        for field in flow.record_assign_fields:
            before_save_writes[flow.object_name].append((field, flow))

    for wf in workflows:
        loc = _rel(wf.path, root)

        # W1 — any field update at all.
        if wf.field_updates:
            sample = ", ".join(sorted(wf.field_updates)[:5])
            more = "…" if len(wf.field_updates) > 5 else ""
            findings.append((
                "WARN",
                f"{loc}: {len(wf.field_updates)} <fieldUpdates> action(s) ({sample}{more}) — "
                "Workflow Rule field updates are deprecated for new actions. Migrate to a "
                "record-triggered Flow; see references/metadata-examples.md Example 2 and "
                "references/gotchas.md § 3.",
            ))

        # E1 — Formula operation with no formula.
        for name, fu in sorted(wf.field_updates.items()):
            if fu["operation"] == "Formula" and not fu["formula"]:
                findings.append((
                    "ERROR",
                    f"{loc}: field update `{name}` has <operation>Formula</operation> but no "
                    "<formula> value. The Metadata API requires the formula when the operation "
                    "is Formula; this file will not deploy "
                    "(api_meta.txt:140126, references/metadata-examples.md).",
                ))

        known_fields = field_index.get(wf.object_name)

        for rule in wf.active_rules:
            rule_name = rule["name"] or "(unnamed rule)"
            rule_criteria = {f.lower() for f in rule["criteria_fields"]}
            rule_formula = rule["formula"].lower()

            for fu_name in rule["field_update_names"]:
                fu = wf.field_updates.get(fu_name)
                if fu is None:
                    findings.append((
                        "ERROR",
                        f"{loc}: rule `{rule_name}` references field update `{fu_name}` which is "
                        "not defined in this file. Workflow deploys whole-file — a dangling "
                        "actions/name reference blocks the deploy "
                        "(references/metadata-examples.md, Example 1).",
                    ))
                    continue

                field = fu["field"]
                if not field:
                    continue

                # W2 — target field not present in the retrieved object folder.
                if known_fields is not None and field.endswith("__c") \
                        and field not in known_fields:
                    findings.append((
                        "WARN",
                        f"{loc}: active rule `{rule_name}` updates `{wf.object_name}.{field}` "
                        f"via `{fu_name}`, but no "
                        f"objects/{wf.object_name}/fields/{field}.field-meta.xml exists in this "
                        "tree. Either the field is missing from the retrieve or the rule writes "
                        "a field that no longer exists — resolve before planning the migration.",
                    ))

                # W3 — onAllChanges rule writing a field it also filters on.
                if rule["triggerType"] == "onAllChanges":
                    in_criteria = field.lower() in rule_criteria
                    in_formula = bool(rule_formula) and field.lower() in rule_formula
                    if in_criteria or in_formula:
                        findings.append((
                            "WARN",
                            f"{loc}: rule `{rule_name}` has triggerType onAllChanges and its "
                            f"field update `{fu_name}` writes `{field}`, which the rule's own "
                            "criteria also test — re-evaluation loop risk. Confirm "
                            "reevaluateOnChange and the resulting cascade before migrating "
                            "(references/gotchas.md § 11).",
                        ))

                # W4 — double writer with an active before-save Flow.
                for flow_field, flow in before_save_writes.get(wf.object_name, []):
                    if flow_field == field:
                        findings.append((
                            "WARN",
                            f"{loc}: active rule `{rule_name}` writes "
                            f"`{wf.object_name}.{field}` and the active before-save Flow "
                            f"{_rel(flow.path, root)} assigns $Record.{field} — two writers on "
                            "one field. The workflow rule writes at step 11, after the Flow at "
                            "step 3, so the Flow's value does not survive. Finish the cutover: "
                            "set the rule's <active> to false in the same deploy "
                            "(references/gotchas.md § 10).",
                        ))

    return findings


def check_flows(flows: list[FlowFile], root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    by_object_trigger: dict[tuple[str, str], list[FlowFile]] = defaultdict(list)

    for flow in flows:
        by_object_trigger[(flow.object_name, flow.trigger_type)].append(flow)

        # W5 — after-save self-update with no change guard.
        if flow.trigger_type != "RecordAfterSave":
            continue
        if not flow.same_object_update_names:
            continue
        if flow.has_change_guard:
            continue
        names = ", ".join(flow.same_object_update_names[:3])
        more = "…" if len(flow.same_object_update_names) > 3 else ""
        findings.append((
            "WARN",
            f"{_rel(flow.path, root)}: after-save Flow on `{flow.object_name}` updates its own "
            f"triggering record ({names}{more}) with no ISCHANGED operator, ISCHANGED/PRIORVALUE "
            "filterFormula, or doesRequireRecordChangedToMeetCriteria — recursion risk. Move the "
            "write to a before-save Assignment or add the guard "
            "(references/gotchas.md § 2).",
        ))

    # W6 — duplicate object + trigger type.
    for (obj, trigger), files in sorted(by_object_trigger.items()):
        if len(files) > 1:
            listed = ", ".join(_rel(f.path, root) for f in files[:3])
            more = "…" if len(files) > 3 else ""
            findings.append((
                "WARN",
                f"{len(files)} record-triggered Flows on `{obj}` with trigger type `{trigger}` — "
                f"ordering between them is not guaranteed. Consolidate into one Flow per object "
                f"per save-time slot (references/gotchas.md § 7). Files: {listed}{more}",
            ))
    return findings


# --------------------------------------------------------------------------- #
# Inventory
# --------------------------------------------------------------------------- #

def build_inventory(workflows: list[WorkflowFile], flows: list[FlowFile]) -> list[str]:
    operations: Counter = Counter()
    reevaluate = 0
    cross_object = 0
    active_rules = 0
    rules_with_updates = 0
    time_trigger_rules = 0
    failed_migrations = 0
    objects_with_updates: set[str] = set()
    total_updates = 0

    for wf in workflows:
        total_updates += len(wf.field_updates)
        if wf.field_updates:
            objects_with_updates.add(wf.object_name)
        for fu in wf.field_updates.values():
            operations[fu["operation"] or "(unset)"] += 1
            if fu["reevaluate"] == "true":
                reevaluate += 1
            if fu["target"]:
                cross_object += 1
        for rule in wf.rules:
            if rule["active"]:
                active_rules += 1
                if rule["field_update_names"]:
                    rules_with_updates += 1
                if rule["time_trigger_count"]:
                    time_trigger_rules += 1
            if rule["failed_migration"]:
                failed_migrations += 1

    before_save = sum(1 for f in flows if f.trigger_type == "RecordBeforeSave")
    after_save = sum(1 for f in flows if f.trigger_type == "RecordAfterSave")

    lines = [
        "Migration inventory",
        "-------------------",
        f"  workflow files scanned            : {len(workflows)}",
        f"  objects carrying field updates    : {len(objects_with_updates)}",
        f"  field updates defined             : {total_updates}",
        f"  active rules                      : {active_rules}",
        f"  active rules with a field update  : {rules_with_updates}",
        f"  active rules with a time trigger  : {time_trigger_rules}  (become after-save Flows "
        "with scheduled paths — gotchas.md § 16)",
        f"  field updates w/ reevaluateOnChange: {reevaluate}  (cascade must be rebuilt by hand "
        "— gotchas.md § 11)",
        f"  cross-object field updates        : {cross_object}  (targetObject set; after-save "
        "Flow, not before-save)",
        f"  rules w/ failedMigrationToolVersion: {failed_migrations}  (Migrate to Flow already "
        "failed once)",
        "  operations                        : "
        + (", ".join(f"{op}={n}" for op, n in sorted(operations.items())) or "none"),
        f"  record-triggered Flows present    : {before_save} before-save, {after_save} after-save",
    ]
    if objects_with_updates:
        lines.append("  objects: " + ", ".join(sorted(objects_with_updates)))
    return lines


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def scan_tree(root: Path) -> tuple[list[tuple[str, str]], list[str]]:
    if not root.exists():
        return [("ERROR", f"manifest-dir does not exist: {root}")], []
    if not root.is_dir():
        return [("ERROR", f"manifest-dir is not a directory: {root}")], []

    workflow_paths: list[Path] = []
    for pattern in WORKFLOW_GLOBS:
        workflow_paths.extend(root.rglob(pattern))
    flow_paths: list[Path] = []
    for pattern in FLOW_GLOBS:
        flow_paths.extend(root.rglob(pattern))

    workflows = [wf for wf in (parse_workflow(p) for p in sorted(set(workflow_paths))) if wf]
    flows = [fl for fl in (parse_flow(p) for p in sorted(set(flow_paths))) if fl]

    field_index = index_object_fields(root)

    findings = check_workflows(workflows, flows, field_index, root)
    findings.extend(check_flows(flows, root))
    return findings, build_inventory(workflows, flows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a retrieved Salesforce metadata tree for Workflow Rule field-update "
            "problems and for the Flow-side patterns that replace them, then print a "
            "migration inventory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root of the retrieved metadata tree, e.g. force-app/main/default (default: '.').",
    )
    parser.add_argument(
        "--src-root",
        default=None,
        help="Deprecated alias for --manifest-dir.",
    )
    parser.add_argument(
        "--quiet-inventory",
        action="store_true",
        help="Suppress the inventory block; print findings only.",
    )
    args = parser.parse_args()

    root = Path(args.manifest_dir or args.src_root or ".")
    findings, inventory = scan_tree(root)

    if inventory and not args.quiet_inventory:
        for line in inventory:
            print(line)
        print()

    if not findings:
        print("OK: no field-update automation problems detected.")
        return 0

    errors = [m for sev, m in findings if sev == "ERROR"]
    warns = [m for sev, m in findings if sev != "ERROR"]
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in warns:
        print(f"WARN: {message}", file=sys.stderr)
    print(
        f"\n{len(findings)} finding(s): {len(errors)} error(s), {len(warns)} warning(s).",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    if main() != 0:
        sys.exit(1)
    sys.exit(0)
