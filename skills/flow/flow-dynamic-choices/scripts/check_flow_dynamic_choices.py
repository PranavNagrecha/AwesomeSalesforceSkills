#!/usr/bin/env python3
"""Static checks for Flow choice-set metadata.

Parses ``*.flow-meta.xml`` files under ``--manifest-dir`` and reports the
choice-set defects that either fail a deploy with an unhelpful enum error or
deploy cleanly and then misbehave on screen. Every rule cites the Metadata API
Developer Guide line range it rests on (``api_meta.txt``, Summer '26 / v62
extract of https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf);
``references/gotchas.md`` carries the full statement of each.

Rules
-----
ERROR  E1  A picklist choice set (``picklistField`` + ``picklistObject``) whose
           ``dataType`` is not ``Picklist`` or ``Multipicklist``. "If a dynamic
           choice has the picklistField and picklistObject parameters set, it's a
           picklist choice and it must have a data type of Picklist or
           Multipicklist" (api_meta.txt L70273-L70276).
ERROR  E2  A record choice set (``object``, no ``picklistField``) whose
           ``dataType`` IS ``Picklist`` or ``Multipicklist`` — "it's a record
           choice and it can't have a data type of Picklist or Multipicklist"
           (api_meta.txt L70269-L70272).
ERROR  E3  ``limit`` on a dynamic choice set outside 1..200. "Maximum and
           default: 200" (api_meta.txt L70319-L70321).
ERROR  E4  A screen field ``dataType`` outside FlowScreenField's own enum
           (Boolean, Currency, Date, DateTime, Number, String, Time —
           api_meta.txt L71611-L71621). Catches ``Picklist`` copied off the
           choice set onto the field that consumes it.
ERROR  E5  A ``MultiSelectCheckboxes`` / ``MultiSelectPicklist`` field whose
           ``dataType`` is not ``String``. "Only the string data type is
           supported for multi-select checkboxes and multi-select picklist
           fields" (api_meta.txt L71625-L71628).
ERROR  E6  ``choiceReferences`` on a ``fieldType`` that does not support it. The
           supported four are RadioButtons, DropdownBox, MultiSelectCheckboxes
           and MultiSelectPicklist (api_meta.txt L71588-L71601).
ERROR  E7  ``choiceReferences`` naming a choice or choice set that this flow does
           not declare in ``<choices>`` or ``<dynamicChoiceSets>``.
ERROR  E8  ``defaultSelectedChoiceReference`` naming something that is not in the
           same field's ``choiceReferences`` (api_meta.txt L71634-L71646).
ERROR  E9  A multi-select field's value assigned to a variable this flow declares
           with a ``dataType`` other than ``String`` or ``Multipicklist``. A
           multi-select field "stores its field value as a concatenation of the
           user-selected choice values, separated by semicolons"
           (api_meta.txt L71714-L71720).

WARN   W1  A record choice set with no ``limit``. The default is the maximum, so
           omission means 200 rows fetched per render, not "all of them"
           (api_meta.txt L70319-L70321).
WARN   W2  ``filterLogic`` inside a ``dynamicChoiceSets`` element.
           FlowDynamicChoiceSet's field table (api_meta.txt L70278-L70386)
           enumerates no ``filterLogic``; FlowRecordLookup's does
           (api_meta.txt L71124-L71131). Move multi-condition logic to a Get
           Records feeding a collection choice set.
WARN   W3  A record choice set that sets exactly one of ``sortField`` /
           ``sortOrder``. Each says separately that without it "the returned
           records aren't sorted" (api_meta.txt L70367-L70379), and ``limit``
           applies after the sort.

ADVISORY A1  A record choice set with no ``sortField`` at all — the choice order
             the user sees is arbitrary, and a ``limit`` on top of it is an
             arbitrary N rather than a top N (api_meta.txt L70321-L70322).
ADVISORY A2  A dynamic choice set with more than one ``filters`` entry. They
             combine implicitly; the type documents no override (see W2).
ADVISORY A3  An Active flow whose ``processType`` is ``Flow`` (a screen flow) that
             a ``*.flowtest-meta.xml`` under --manifest-dir names in
             ``flowApiName``. FlowTest covers "record-triggered, autolaunched, or
             Data Cloud-triggered" flows (api_meta.txt L73960-L73962); a FlowTest
             against a screen flow is dead metadata.

Exit codes
----------
0  no ERROR findings (WARN and ADVISORY findings may be present)
1  at least one ERROR, or --manifest-dir does not exist

``--strict`` promotes every WARN to ERROR. ADVISORY findings never fail the run.

Usage
-----
    python3 check_flow_dynamic_choices.py --manifest-dir force-app
    python3 check_flow_dynamic_choices.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

NS = "http://soap.sforce.com/2006/04/metadata"

# api_meta.txt L71588-L71601 — the only four fieldTypes that take choiceReferences.
CHOICE_BEARING_FIELD_TYPES = {
    "RadioButtons",
    "DropdownBox",
    "MultiSelectCheckboxes",   # API 26.0 and later
    "MultiSelectPicklist",     # API 26.0 and later
}

# api_meta.txt L71714-L71720 — these store a semicolon-joined string.
MULTI_SELECT_FIELD_TYPES = {"MultiSelectCheckboxes", "MultiSelectPicklist"}

# api_meta.txt L71611-L71621 — FlowScreenField.dataType. Deliberately has no
# Picklist / Multipicklist value; FlowDynamicChoiceSet.dataType does.
SCREEN_FIELD_DATA_TYPES = {
    "Boolean", "Currency", "Date", "DateTime", "Number", "String", "Time",
}

# api_meta.txt L70286-L70301 — FlowDynamicChoiceSet.dataType, picklist-only values.
PICKLIST_CHOICE_DATA_TYPES = {"Picklist", "Multipicklist"}

# api_meta.txt L70319-L70321 — "Maximum and default: 200".
DYNAMIC_CHOICE_LIMIT_MAX = 200

SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}


@dataclass
class Finding:
    severity: str
    rule: str
    path: Path
    element: str
    message: str

    def render(self) -> str:
        return f"{self.severity} {self.rule} {self.path}:{self.element} — {self.message}"


def child(elem: ET.Element, name: str) -> ET.Element | None:
    """First direct child named `name`, or None.

    Written as an explicit ``is not None`` test: a leaf ElementTree Element is
    falsy, so ``elem.find(a) or elem.find(b)`` silently drops real elements.
    """
    found = elem.find(f"{{{NS}}}{name}")
    if found is not None:
        return found
    return None


def text(elem: ET.Element | None, name: str) -> str | None:
    if elem is None:
        return None
    node = child(elem, name)
    if node is None or node.text is None:
        return None
    return node.text.strip()


def texts(elem: ET.Element, name: str) -> list[str]:
    out: list[str] = []
    for node in elem.findall(f"{{{NS}}}{name}"):
        if node.text is not None and node.text.strip():
            out.append(node.text.strip())
    return out


def kids(elem: ET.Element, name: str) -> list[ET.Element]:
    return list(elem.findall(f"{{{NS}}}{name}"))


def iter_screen_fields(screen: ET.Element):
    """Yield every FlowScreenField in a screen, descending through Region /
    RegionContainer nesting (FlowScreenField.fields, api_meta.txt L71669-L71672)."""
    stack = list(kids(screen, "fields"))
    while stack:
        field = stack.pop()
        yield field
        stack.extend(kids(field, "fields"))


def _classify_choice_set(dcs: ET.Element) -> str:
    """'picklist' | 'record' | 'collection' per api_meta.txt L70269-L70280."""
    if text(dcs, "picklistField") or text(dcs, "picklistObject"):
        return "picklist"
    if text(dcs, "collectionReference"):
        return "collection"
    return "record"


def _flow_test_targets(root_dir: Path) -> set[str]:
    """flowApiName values across every *.flowtest-meta.xml under the tree."""
    targets: set[str] = set()
    for test_path in root_dir.rglob("*.flowtest-meta.xml"):
        try:
            node = ET.parse(test_path).getroot()
        except ET.ParseError:
            continue
        name = text(node, "flowApiName")
        if name:
            targets.add(name)
    return targets


def check_flow(path: Path, flow_test_targets: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding("ERROR", "E0", path, "-", f"not well-formed XML: {exc}")]

    static_choices = {text(c, "name") for c in kids(root, "choices")}
    static_choices.discard(None)
    dynamic_sets = {text(d, "name"): d for d in kids(root, "dynamicChoiceSets") if text(d, "name")}
    declared_choices = static_choices | set(dynamic_sets)
    variables = {
        text(v, "name"): (text(v, "dataType") or "")
        for v in kids(root, "variables")
        if text(v, "name")
    }

    # ---- dynamic choice set rules -------------------------------------------------
    for name, dcs in dynamic_sets.items():
        kind = _classify_choice_set(dcs)
        data_type = text(dcs, "dataType") or ""

        if kind == "picklist" and data_type not in PICKLIST_CHOICE_DATA_TYPES:
            findings.append(Finding(
                "ERROR", "E1", path, name,
                f"picklist choice set (picklistField/picklistObject set) declares "
                f"dataType '{data_type or '(missing)'}'; it must be Picklist or "
                f"Multipicklist (api_meta.txt L70273-L70276).",
            ))
        if kind != "picklist" and data_type in PICKLIST_CHOICE_DATA_TYPES:
            findings.append(Finding(
                "ERROR", "E2", path, name,
                f"a record or collection choice set cannot declare dataType "
                f"'{data_type}' — that value is reserved for picklist choices "
                f"(api_meta.txt L70269-L70272).",
            ))

        raw_limit = text(dcs, "limit")
        if raw_limit:
            try:
                value = int(raw_limit)
            except ValueError:
                findings.append(Finding(
                    "ERROR", "E3", path, name,
                    f"limit '{raw_limit}' is not an integer (api_meta.txt L70319).",
                ))
            else:
                if value < 1 or value > DYNAMIC_CHOICE_LIMIT_MAX:
                    findings.append(Finding(
                        "ERROR", "E3", path, name,
                        f"limit {value} is outside 1..{DYNAMIC_CHOICE_LIMIT_MAX}; "
                        f"'Maximum and default: 200' (api_meta.txt L70319-L70321).",
                    ))
        elif kind == "record":
            findings.append(Finding(
                "WARN", "W1", path, name,
                "record choice set has no <limit>. The default IS the maximum, so "
                "this fetches up to 200 rows every time its screen renders "
                "(api_meta.txt L70319-L70321).",
            ))

        if child(dcs, "filterLogic") is not None:
            findings.append(Finding(
                "WARN", "W2", path, name,
                "filterLogic is not a documented FlowDynamicChoiceSet field "
                "(api_meta.txt L70278-L70386); FlowRecordLookup has it "
                "(L71124-L71131). Move multi-condition logic to a Get Records "
                "feeding a collection choice set.",
            ))

        filters = kids(dcs, "filters")
        if len(filters) > 1:
            findings.append(Finding(
                "ADVISORY", "A2", path, name,
                f"{len(filters)} filters on one choice set combine implicitly — the "
                "type documents no filterLogic override.",
            ))

        if kind == "record":
            sort_field = text(dcs, "sortField")
            sort_order = text(dcs, "sortOrder")
            if bool(sort_field) != bool(sort_order):
                findings.append(Finding(
                    "WARN", "W3", path, name,
                    "record choice set sets only one of sortField/sortOrder; each "
                    "says separately that without it the records aren't sorted "
                    "(api_meta.txt L70367-L70379).",
                ))
            elif not sort_field:
                findings.append(Finding(
                    "ADVISORY", "A1", path, name,
                    "record choice set has no sortField — choice order is arbitrary, "
                    "and any limit on top of it is an arbitrary N, not a top N "
                    "(api_meta.txt L70321-L70322).",
                ))

    # ---- screen field rules -------------------------------------------------------
    multi_select_fields: set[str] = set()
    for screen in kids(root, "screens"):
        screen_name = text(screen, "name") or "(unnamed screen)"
        for field in iter_screen_fields(screen):
            field_name = text(field, "name") or "(unnamed field)"
            where = f"{screen_name}/{field_name}"
            field_type = text(field, "fieldType") or ""
            data_type = text(field, "dataType")
            refs = texts(field, "choiceReferences")

            if data_type and data_type not in SCREEN_FIELD_DATA_TYPES:
                findings.append(Finding(
                    "ERROR", "E4", path, where,
                    f"screen field dataType '{data_type}' is not a FlowScreenField "
                    f"value. Valid: {', '.join(sorted(SCREEN_FIELD_DATA_TYPES))} "
                    f"(api_meta.txt L71611-L71621). A choice set's Picklist dataType "
                    f"does not carry over to the field that consumes it.",
                ))

            if field_type in MULTI_SELECT_FIELD_TYPES:
                multi_select_fields.add(field_name)
                if data_type and data_type != "String":
                    findings.append(Finding(
                        "ERROR", "E5", path, where,
                        f"{field_type} declares dataType '{data_type}'; only String is "
                        f"supported for multi-select fields (api_meta.txt L71625-L71628).",
                    ))

            if refs and field_type and field_type not in CHOICE_BEARING_FIELD_TYPES:
                findings.append(Finding(
                    "ERROR", "E6", path, where,
                    f"choiceReferences on fieldType '{field_type}'. Supported only on "
                    f"{', '.join(sorted(CHOICE_BEARING_FIELD_TYPES))} "
                    f"(api_meta.txt L71588-L71601).",
                ))

            for ref in refs:
                if ref not in declared_choices:
                    findings.append(Finding(
                        "ERROR", "E7", path, where,
                        f"choiceReferences names '{ref}', which this flow declares "
                        f"neither in <choices> nor in <dynamicChoiceSets>.",
                    ))

            default_ref = text(field, "defaultSelectedChoiceReference")
            if default_ref and default_ref not in refs:
                findings.append(Finding(
                    "ERROR", "E8", path, where,
                    f"defaultSelectedChoiceReference '{default_ref}' is not among this "
                    f"field's choiceReferences ({', '.join(refs) or 'none'}) "
                    f"(api_meta.txt L71634-L71646).",
                ))

    # ---- multi-select output typing -----------------------------------------------
    if multi_select_fields:
        for holder_tag in ("assignments", "recordCreates", "recordUpdates"):
            for node in kids(root, holder_tag):
                node_name = text(node, "name") or f"(unnamed {holder_tag})"
                item_tag = "assignmentItems" if holder_tag == "assignments" else "inputAssignments"
                for item in kids(node, item_tag):
                    value = child(item, "value")
                    if value is None:
                        continue
                    ref = text(value, "elementReference")
                    if ref is None or ref not in multi_select_fields:
                        continue
                    target = text(item, "assignToReference")
                    if target is None or target not in variables:
                        continue
                    target_type = variables[target]
                    if target_type not in {"String", "Multipicklist"}:
                        findings.append(Finding(
                            "ERROR", "E9", path, f"{node_name}/{target}",
                            f"the multi-select field '{ref}' stores a semicolon-joined "
                            f"string (api_meta.txt L71714-L71720), but '{target}' is "
                            f"declared dataType '{target_type}'. Use String (or "
                            f"Multipicklist), or decompose the value first.",
                        ))

    # ---- screen flow vs FlowTest ---------------------------------------------------
    process_type = text(root, "processType")
    status = text(root, "status")
    flow_api_name = path.name[: -len(".flow-meta.xml")]
    if (
        process_type == "Flow"
        and status == "Active"
        and flow_api_name in flow_test_targets
    ):
        findings.append(Finding(
            "ADVISORY", "A3", path, flow_api_name,
            "an Active screen flow named by a *.flowtest-meta.xml. FlowTest covers "
            "record-triggered, autolaunched and Data Cloud-triggered flows "
            "(api_meta.txt L73960-L73962); verify screen choices with a debug run "
            "instead (references/metadata-examples.md §6).",
        ))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for choice-set defects.",
    )
    parser.add_argument(
        "--manifest-dir",
        required=True,
        help="Directory searched recursively for *.flow-meta.xml files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat every WARN as an ERROR. ADVISORY findings still never fail.",
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

    flow_test_targets = _flow_test_targets(root_dir)

    findings: list[Finding] = []
    for flow in flows:
        findings.extend(check_flow(flow, flow_test_targets))

    if args.strict:
        for finding in findings:
            if finding.severity == "WARN":
                finding.severity = "ERROR"

    for finding in sorted(
        findings, key=lambda f: (SEVERITY_ORDER[f.severity], str(f.path), f.rule)
    ):
        print(finding.render())

    errors = sum(1 for f in findings if f.severity == "ERROR")
    warns = sum(1 for f in findings if f.severity == "WARN")
    advisories = sum(1 for f in findings if f.severity == "ADVISORY")
    print(
        f"\n{len(flows)} flow(s) checked — {errors} ERROR, {warns} WARN, "
        f"{advisories} ADVISORY"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
