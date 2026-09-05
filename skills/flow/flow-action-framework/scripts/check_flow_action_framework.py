#!/usr/bin/env python3
"""Checker for the Flow Action Framework skill.

Parses every ``*.flow-meta.xml`` (and ``*.flow``) under --manifest-dir and validates the
*action boundary* of each flow -- the ``<actionCalls>``, ``<apexPluginCalls>`` and
``<subflows>`` elements -- cross-checking Apex actions against the ``*.cls`` files in the
same tree. Stdlib only.

Rules (grounding is cited inline in every finding; see ../references/gotchas.md and
../references/metadata-examples.md for the long form):

  FAF01  WARN     An <actionCalls> element with no <faultConnector>. The field is optional
                  in the schema -- "Specifies which node to execute if the action call
                  results in an error" (api_meta.txt L68476-68477) -- so an action ships
                  without a fault path unless one is added (Gotcha 3).
  FAF02  ERROR    <actionType>apex</actionType> whose <actionName> matches no class in the
                  tree carrying @InvocableMethod. actionName is the CLASS name, because
                  "Only one method in a class can have the InvocableMethod annotation"
                  (apexdev.txt L5422). Downgraded to ADVISORY when the tree contains no
                  *.cls at all -- the class may live in the org or in a package.
  FAF03  ERROR    An apex action whose class exposes a generic sObject surface
                  (List<SObject> / SObject on the method or on an @InvocableVariable) but
                  whose action call has no <dataTypeMappings>. FlowDataTypeMapping is how
                  the concrete type is bound: "The T__ prefix is required for input
                  variables. The U__ prefix is required for output variables"
                  (api_meta.txt L70192-L70203); the field is API 48.0+ (L68470-68472).
  FAF03b ERROR    A <dataTypeMappings><typeName> that carries neither the T__ nor the U__
                  prefix, or an empty <typeValue> (same citation).
  FAF04  WARN     <storeOutputAutomatically>true</storeOutputAutomatically> together with
                  explicit <outputParameters>. The guide describes the two as alternatives
                  -- true means outputs are "automatically available in the flow without
                  creating any variables"; false means "create variables manually to store
                  output values from the action" (api_meta.txt L68523-68529) -- but it
                  never states that the combination is rejected, so this is a WARN, not an
                  ERROR. UNVERIFIED (2026-09-05): exclusivity is implied by the field
                  description, not asserted anywhere in api_meta.txt.
  FAF05  WARN     An action call inside a loop body. Heuristic: the element is reachable
                  from a <loops> element's <nextValueConnector> along a connector chain
                  that returns to that loop (api_meta.txt L70698-70718). One action per
                  iteration is a governor multiplier where a collection input would do.
  FAF06  ADVISORY <flowTransactionModel>NewTransaction</flowTransactionModel> on an apex
                  action whose class does not declare callout=true. NewTransaction
                  "Creates a transaction before the invocable action is executed"
                  (api_meta.txt L68485-68486); the documented reason to want one is the
                  callout gate at apexdev.txt L26872-26880.
  FAF07  WARN     An <actionCalls> element with no <flowTransactionModel>. The guide marks
                  it Required (api_meta.txt L68479-68480). WARN rather than ERROR because
                  the field is API 51.0 and later, so a genuinely older flow omits it
                  legitimately -- promoted in the message when <apiVersion> is >= 51.
  FAF08  WARN     <nameSegment> or <versionSegment> on a flow whose <apiVersion> is >= 62.
                  Both are "available in API version 58.0 to 61.0. This field is deprecated
                  in API version 62.0 and later" (api_meta.txt L68495-68501, L68542-68546).
  FAF09  ERROR    <actionType>flow</actionType> in a flow whose <processType> is Flow or
                  AutoLaunchedFlow. The enum value says so directly: "This action type
                  isn't available for flows with a processType of Flow or AutolaunchedFlow.
                  To invoke an autolaunched flow from one of those types, use FlowSubflow"
                  (api_meta.txt L68749-68753).
  FAF10  WARN     An action with <isWaitUntilCompleted>true</isWaitUntilCompleted> that has
                  a <faultConnector> but no <timeoutConnector>. A timeout is not an error:
                  timeoutConnector fires "if an async action execution is timed out"
                  (api_meta.txt L68532-68534, API 62.0+) (Gotcha 8).
  FAF11  ADVISORY An <apexPluginCalls> element (a legacy Process.Plugin action). "Legacy
                  Apex actions aren't supported in auto-layout in Flow Builder"
                  (apexdev.txt L27266-27267) and the interface supports neither collections
                  nor bulk (L27262-27263) (Gotcha 12).
  FAF12  ERROR    An <actionCalls> element missing <actionName> or <actionType>; both are
                  Required (api_meta.txt L68462-68466).

Exit codes:
    0  no ERROR-severity findings (WARN and ADVISORY may be present), including the case
       where the directory exists but holds no flows
    1  at least one ERROR, or --manifest-dir does not exist, or --strict was passed and any
       WARN/ADVISORY was found

Usage:
    python3 check_flow_action_framework.py --manifest-dir force-app/main/default
    python3 check_flow_action_framework.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ERROR = "ERROR"
WARN = "WARN"
ADVISORY = "ADVISORY"

# api_meta.txt L68479-68486 -- the three documented FlowTransactionModel values.
TRANSACTION_MODELS = {"Automatic", "CurrentTransaction", "NewTransaction"}

# api_meta.txt L68749-68753 -- the two processType values from which actionType `flow` is
# unavailable. The guide spells the second one "AutolaunchedFlow" in that sentence and
# "AutoLaunchedFlow" in the FlowProcessType table, so both spellings are matched.
SUBFLOW_ONLY_PROCESS_TYPES = {"flow", "autolaunchedflow"}

# api_meta.txt L68495-68501, L68542-68546 -- deprecated in API version 62.0 and later.
VERSIONED_ACTION_FIELDS = ("nameSegment", "versionSegment")
VERSIONED_ACTION_DEPRECATED_FROM = 62.0

# api_meta.txt L68479-68481 -- flowTransactionModel is available in API version 51.0+.
TRANSACTION_MODEL_FROM = 51.0

INVOCABLE_METHOD_RE = re.compile(r"@InvocableMethod\b", re.I)
CALLOUT_TRUE_RE = re.compile(r"callout\s*=\s*true", re.I)
# A generic-sObject surface: List<SObject>, List<List<SObject>>, or a bare SObject field.
GENERIC_SOBJECT_RE = re.compile(r"\bList\s*<\s*(?:List\s*<\s*)?SObject\s*>|\bSObject\s+\w+\s*;", re.I)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the action boundary of Salesforce flows against the Apex in the same tree.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN and ADVISORY findings to failures (exit 1).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the 'no issues' line; exit code is unchanged.",
    )
    return parser.parse_args()


# --------------------------------------------------------------------------- XML helpers


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def find_child(element: ET.Element, name: str) -> ET.Element | None:
    """First direct child with this local name, or None.

    Never write ``element.find(a) or element.find(b)``: a leaf Element is falsy, so an
    element that exists but has no children would be silently discarded. Test ``is not
    None`` instead -- which is what every caller here does.
    """
    for child in element:
        if local_name(child.tag) == name:
            return child
    return None


def children(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in element if local_name(c.tag) == name]


def child_text(element: ET.Element | None, name: str) -> str:
    if element is None:
        return ""
    found = find_child(element, name)
    if found is not None and found.text:
        return found.text.strip()
    return ""


def has_child(element: ET.Element, name: str) -> bool:
    return find_child(element, name) is not None


def to_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------- Apex-side inventory


class ApexAction:
    """One Apex class in the tree that carries @InvocableMethod."""

    def __init__(self, name: str, source: str) -> None:
        self.name = name
        self.has_callout = bool(CALLOUT_TRUE_RE.search(source))
        self.is_generic = bool(GENERIC_SOBJECT_RE.search(source))


def load_apex_actions(manifest_dir: Path) -> tuple[dict[str, ApexAction], int]:
    """Return ({class name: ApexAction}, total *.cls files seen)."""
    actions: dict[str, ApexAction] = {}
    total = 0
    for path in sorted(manifest_dir.rglob("*.cls")):
        if not path.is_file():
            continue
        total += 1
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not INVOCABLE_METHOD_RE.search(source):
            continue
        actions[path.stem] = ApexAction(path.stem, source)
    return actions, total


# ------------------------------------------------------------------------ loop detection


def outgoing_targets(element: ET.Element, skip: tuple[str, ...] = ()) -> set[str]:
    """Every element name this node can hand control to."""
    targets: set[str] = set()
    connector_tags = (
        "connector",
        "defaultConnector",
        "faultConnector",
        "nextValueConnector",
        "noMoreValuesConnector",
        "timeoutConnector",
    )
    for tag in connector_tags:
        if tag in skip:
            continue
        for conn in children(element, tag):
            target = child_text(conn, "targetReference")
            if target:
                targets.add(target)
    # decision rules and wait events nest their connector one level deeper
    for container in ("rules", "waitEvents", "scheduledPaths"):
        for rule in children(element, container):
            for conn in children(rule, "connector"):
                target = child_text(conn, "targetReference")
                if target:
                    targets.add(target)
    return targets


def elements_in_loop_bodies(root: ET.Element) -> set[str]:
    """Names of elements that sit on a path from a loop back to that same loop.

    api_meta.txt L70698-70718: a FlowLoop hands control to <nextValueConnector> for each
    item and to <noMoreValuesConnector> when the collection is exhausted. Anything on a
    chain that leaves nextValueConnector and returns to the loop runs once per iteration.
    """
    by_name: dict[str, ET.Element] = {}
    for element in root:
        name = child_text(element, "name")
        if name:
            by_name[name] = element

    in_loop: set[str] = set()
    for loop in children(root, "loops"):
        loop_name = child_text(loop, "name")
        entry = child_text(find_child(loop, "nextValueConnector"), "targetReference")
        if not loop_name or not entry:
            continue

        visited: set[str] = set()
        stack = [entry]
        returns_to_loop = False
        while stack:
            current = stack.pop()
            if current == loop_name:
                returns_to_loop = True
                continue
            if current in visited or current not in by_name:
                continue
            visited.add(current)
            stack.extend(outgoing_targets(by_name[current]))
        if returns_to_loop:
            in_loop |= visited
    return in_loop


# ------------------------------------------------------------------------------- rules


def check_flow(
    path: Path,
    apex_actions: dict[str, ApexAction],
    apex_files_present: bool,
) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []

    def add(severity: str, code: str, message: str) -> None:
        findings.append((severity, f"{path}: [{code}] {message}"))

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [(ERROR, f"{path}: [FAF00] unable to parse flow metadata ({exc}).")]

    process_type = child_text(root, "processType")
    api_version = to_float(child_text(root, "apiVersion"))
    looped = elements_in_loop_bodies(root)

    for legacy in children(root, "apexPluginCalls"):
        name = child_text(legacy, "name") or "<unnamed>"
        add(
            ADVISORY, "FAF11",
            f"element '{name}' is a legacy Apex plug-in call (<apexPluginCalls>, apexClass "
            f"'{child_text(legacy, 'apexClass')}'). \"Legacy Apex actions aren't supported "
            f"in auto-layout in Flow Builder\" (apexdev.txt L27266-27267) and Process.Plugin "
            f"\"doesn't support Blob, Collection, and sObject, data types, and it doesn't "
            f"support bulk operations\" (L27262-27263). Rebuild as an @InvocableMethod "
            f"action; changing actionType alone does not convert it.",
        )

    for call in children(root, "actionCalls"):
        name = child_text(call, "name") or "<unnamed>"
        action_name = child_text(call, "actionName")
        action_type = child_text(call, "actionType")

        # FAF12 -- required identity
        if not action_name or not action_type:
            missing = " and ".join(
                t for t, v in (("<actionName>", action_name), ("<actionType>", action_type)) if not v
            )
            add(
                ERROR, "FAF12",
                f"action '{name}' is missing {missing}; both are Required on FlowActionCall "
                f"(api_meta.txt L68462-68466), and together they address the action -- "
                f"actionName \"Must be unique across actions with the same actionType\".",
            )

        # FAF01 -- fault path
        if not has_child(call, "faultConnector"):
            add(
                WARN, "FAF01",
                f"action '{name}' ({action_type or 'unknown type'}) has no <faultConnector>. "
                f"It \"Specifies which node to execute if the action call results in an "
                f"error\" (api_meta.txt L68476-68477) and is optional in the schema, so an "
                f"uncaught failure ends the interview with the platform's own message.",
            )

        # FAF07 -- required transaction model
        transaction_model = child_text(call, "flowTransactionModel")
        if not transaction_model:
            note = (
                f"the flow declares apiVersion {api_version:g}, at or above the {TRANSACTION_MODEL_FROM:g} "
                f"in which the field became available"
                if api_version is not None and api_version >= TRANSACTION_MODEL_FROM
                else "the flow declares no apiVersion, or one below 51.0, where the field does not exist"
            )
            add(
                WARN, "FAF07",
                f"action '{name}' has no <flowTransactionModel>, which the guide marks "
                f"Required (api_meta.txt L68479-68480); {note}.",
            )
        elif transaction_model not in TRANSACTION_MODELS:
            add(
                ERROR, "FAF07",
                f"action '{name}' has <flowTransactionModel>{transaction_model}</flowTransactionModel>; "
                f"the documented values are {sorted(TRANSACTION_MODELS)} (api_meta.txt L68481-68486).",
            )

        # FAF08 -- deprecated versioned-action fields
        if api_version is not None and api_version >= VERSIONED_ACTION_DEPRECATED_FROM:
            for field in VERSIONED_ACTION_FIELDS:
                if has_child(call, field):
                    add(
                        WARN, "FAF08",
                        f"action '{name}' carries <{field}>, which is \"available in API "
                        f"version 58.0 to 61.0\" and \"deprecated in API version 62.0 and "
                        f"later\" (api_meta.txt L68495-68501, L68542-68546), while this flow "
                        f"declares apiVersion {api_version:g}. Retrieve the flow after the "
                        f"next save and drop what the org no longer round-trips.",
                    )

        # FAF04 -- storeOutputAutomatically vs explicit outputs
        store_auto = child_text(call, "storeOutputAutomatically").lower() == "true"
        output_params = children(call, "outputParameters")
        if store_auto and output_params:
            names = ", ".join(child_text(p, "name") or "?" for p in output_params)
            add(
                WARN, "FAF04",
                f"action '{name}' sets <storeOutputAutomatically>true</storeOutputAutomatically> "
                f"and also declares explicit <outputParameters> ({names}). The guide presents "
                f"the two as alternatives -- true means outputs are \"automatically available "
                f"in the flow without creating any variables\", false means \"create variables "
                f"manually\" (api_meta.txt L68523-68529) -- but never states that the "
                f"combination is rejected, so confirm which one the org honours before relying "
                f"on either reference style.",
            )

        # FAF05 -- action inside a loop body
        if name in looped:
            add(
                WARN, "FAF05",
                f"action '{name}' sits on a path that leaves a loop's <nextValueConnector> "
                f"and returns to that loop (api_meta.txt L70698-70718), so it is invoked once "
                f"per collection item. Where the action accepts a collection input, build the "
                f"collection first and invoke once.",
            )

        # FAF09 -- actionType flow from a flow that must use FlowSubflow
        if action_type == "flow" and process_type.lower() in SUBFLOW_ONLY_PROCESS_TYPES:
            add(
                ERROR, "FAF09",
                f"action '{name}' uses <actionType>flow</actionType> in a flow whose "
                f"processType is '{process_type}'. That value \"isn't available for flows with "
                f"a processType of Flow or AutolaunchedFlow. To invoke an autolaunched flow "
                f"from one of those types, use FlowSubflow\" (api_meta.txt L68749-68753). "
                f"Replace the action call with a <subflows> element.",
            )

        # FAF10 -- async action with no timeout path
        if child_text(call, "isWaitUntilCompleted").lower() == "true":
            if has_child(call, "faultConnector") and not has_child(call, "timeoutConnector"):
                add(
                    WARN, "FAF10",
                    f"action '{name}' sets <isWaitUntilCompleted>true</isWaitUntilCompleted> and "
                    f"has a <faultConnector> but no <timeoutConnector>. A timeout is not an "
                    f"error: timeoutConnector fires \"if an async action execution is timed "
                    f"out\" (api_meta.txt L68532-68534, API 62.0+), enabled by "
                    f"<timeoutPathUsage>EnableTimeoutPath</timeoutPathUsage> (L68536-68540).",
                )

        # dataTypeMappings shape (independent of actionType)
        mappings = children(call, "dataTypeMappings")
        for mapping in mappings:
            type_name = child_text(mapping, "typeName")
            type_value = child_text(mapping, "typeValue")
            if not type_name.startswith(("T__", "U__")):
                add(
                    ERROR, "FAF03b",
                    f"action '{name}' has <dataTypeMappings><typeName>{type_name or '(empty)'}"
                    f"</typeName>; \"The T__ prefix is required for input variables. The U__ "
                    f"prefix is required for output variables\" (api_meta.txt L70192-L70203).",
                )
            if not type_value:
                add(
                    ERROR, "FAF03b",
                    f"action '{name}' has a <dataTypeMappings> for '{type_name}' with an empty "
                    f"<typeValue>; it must carry the \"API name of the specific sObject data "
                    f"type that this value maps to\" (api_meta.txt L70201-L70203).",
                )

        if action_type != "apex" or not action_name:
            continue

        # FAF02 -- the Apex class behind the action
        apex = apex_actions.get(action_name)
        if apex is None:
            severity = ERROR if apex_files_present else ADVISORY
            tail = (
                "no class of that name in this tree carries @InvocableMethod"
                if apex_files_present
                else "this tree contains no *.cls files, so the class may live in the org or "
                     "in an installed package -- confirm with GET "
                     f"/services/data/vXX.X/actions/custom/apex/{action_name}"
            )
            add(
                severity, "FAF02",
                f"action '{name}' names Apex action '{action_name}' and {tail}. For "
                f"actionType apex the actionName is the CLASS name, since \"Only one method "
                f"in a class can have the InvocableMethod annotation\" (apexdev.txt L5422); "
                f"a stale name is a runtime error, not a deploy error (api_rest.txt "
                f"L13781-13782).",
            )
            continue

        # FAF03 -- generic sObject surface needs dataTypeMappings
        if apex.is_generic and not mappings:
            add(
                ERROR, "FAF03",
                f"action '{name}' calls '{action_name}', whose Apex exposes a generic sObject "
                f"surface (List<SObject> or a bare SObject member), but the action call has no "
                f"<dataTypeMappings>. FlowDataTypeMapping is what binds the concrete type: "
                f"typeName takes the T__ prefix for inputs and U__ for outputs, typeValue the "
                f"sObject API name (api_meta.txt L70192-L70203; field added in API 48.0, "
                f"L68470-68472).",
            )

        # FAF06 -- NewTransaction without a callout rationale
        if transaction_model == "NewTransaction" and not apex.has_callout:
            add(
                ADVISORY, "FAF06",
                f"action '{name}' requests NewTransaction -- \"Creates a transaction before the "
                f"invocable action is executed\" (api_meta.txt L68485-68486) -- but "
                f"'{action_name}' does not declare callout=true. The documented reason to want "
                f"a fresh transaction is the callout gate (apexdev.txt L26872-26880); a new "
                f"transaction also means the earlier work is already committed and cannot be "
                f"rolled back with it. Record why, or use CurrentTransaction.",
            )

    return findings


def collect(manifest_dir: Path) -> list[tuple[str, str]]:
    flows = sorted(set(manifest_dir.rglob("*.flow-meta.xml")) | set(manifest_dir.rglob("*.flow")))
    if not flows:
        return [(WARN, f"No *.flow-meta.xml files found under {manifest_dir}")]

    apex_actions, cls_count = load_apex_actions(manifest_dir)
    findings: list[tuple[str, str]] = []
    for flow in flows:
        findings.extend(check_flow(flow, apex_actions, cls_count > 0))
    return findings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    findings = collect(manifest_dir)

    if not findings:
        if not args.quiet:
            print("No issues found.")
        return 0

    order = {ERROR: 0, WARN: 1, ADVISORY: 2}
    seen: set[tuple[str, str]] = set()
    for severity, message in sorted(findings, key=lambda f: (order[f[0]], f[1])):
        if (severity, message) in seen:
            continue
        seen.add((severity, message))
        print(f"{severity}: {message}", file=sys.stderr)

    counts = {level: sum(1 for s, _ in seen if s == level) for level in order}
    print(
        f"\n{counts[ERROR]} error(s), {counts[WARN]} warning(s), {counts[ADVISORY]} advisory.",
        file=sys.stderr,
    )

    if counts[ERROR]:
        return 1
    if args.strict and (counts[WARN] or counts[ADVISORY]):
        print("--strict: promoting warnings and advisories to failure.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
