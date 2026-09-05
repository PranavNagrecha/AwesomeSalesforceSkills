#!/usr/bin/env python3
"""Static checks for Salesforce QuickAction metadata.

Point --manifest-dir at a retrieved SFDX source tree (or an mdapi package) that
contains some of: quickActions/, layouts/, flexipages/, flows/, objects/.
Checks that need a neighbouring folder are skipped silently when it is absent,
so the script is useful against a partial retrieve.

Findings and their severities
  ERROR  Create action with no <targetObject>            - cannot deploy / nothing to create
  ERROR  <targetRecordType> outside the documented enum  - Business Account | Person Account | Master
  WARN   Create/Update/LogACall action with no <quickActionLayout>
  WARN   <quickActionLayout> present but containing no <quickActionLayoutItems>
  WARN   <optionsCreateFeedItem> missing on a Create/Update/LogACall action (schema: required)
  WARN   <fieldOverrides><field> naming a custom field absent from objects/<Obj>/fields/
  WARN   Flow action whose <flowDefinition> is absent from flows/
  WARN   Global action of type LightningComponent (Field Service mobile only)
  WARN   Layout action bar carrying more actions than the visibility threshold
  INFO   Action referenced by no Layout and no FlexiPage in the tree (unplaced)

Exit codes
  0  no ERROR and no WARN (INFO may be present)
  1  at least one ERROR or WARN
  2  --manifest-dir does not exist

Element names, enumerations and required-ness come from the Metadata API
Developer Guide v67.0 (Summer '26), QuickAction and Layout types:
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

Stdlib only.

Usage:
    python3 check_global_actions_and_quick_actions.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

# QuickActionType values whose records are built from a quickActionLayout.
LAYOUT_BEARING_TYPES = {"Create", "Update", "LogACall"}

# QuickAction.targetRecordType documented enum.
VALID_TARGET_RECORD_TYPES = {"Business Account", "Person Account", "Master"}

# PlatformActionList.actionListContext values that render a user-facing action bar
# on a record. Kept narrow on purpose: other contexts are different surfaces.
RECORD_BAR_CONTEXTS = {"Record", "Flexipage"}

# Actions past roughly the fifth slot collapse into the "More" overflow.
MAX_VISIBLE_ACTIONS = 7

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_BAD_ARGS = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce QuickAction metadata for deploy-blocking and "
            "visibility problems. Point --manifest-dir at a retrieved sfdx "
            "source directory or mdapi package."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata directory tree (default: current directory).",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def _child(parent, local: str):
    """Return the first child element named `local`, or None.

    Never chain these with `or`: an ElementTree element with no children is
    falsy even when it exists, so `a.find(x) or a.find(y)` silently discards a
    real element. Always compare against None.
    """
    if parent is None:
        return None
    return parent.find(_tag(local))


def _text(parent, local: str) -> str | None:
    el = _child(parent, local)
    if el is None or el.text is None:
        return None
    return el.text.strip() or None


class Finding:
    __slots__ = ("severity", "subject", "message")

    def __init__(self, severity: str, subject: str, message: str) -> None:
        self.severity = severity
        self.subject = subject
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity:<5} [{self.subject}] {self.message}"


def find_dirs(root: Path, name: str) -> list[Path]:
    """All directories called `name` anywhere under root (plus root/name itself)."""
    found: list[Path] = []
    direct = root / name
    if direct.is_dir():
        found.append(direct)
    for candidate in root.rglob(name):
        if candidate.is_dir() and candidate not in found:
            found.append(candidate)
    return found


def action_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for d in find_dirs(root, "quickActions"):
        files.extend(sorted(d.glob("*.quickAction-meta.xml")))
        files.extend(sorted(d.glob("*.quickAction")))
    return files


def action_full_name(path: Path) -> str:
    """'Account.New_Case.quickAction-meta.xml' -> 'Account.New_Case'."""
    name = path.name
    for suffix in (".quickAction-meta.xml", ".quickAction"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def split_scope(full_name: str) -> tuple[str | None, str]:
    """Return (host object or None for global, developer name)."""
    if "." in full_name:
        host, _, dev = full_name.partition(".")
        return host, dev
    return None, full_name


def custom_fields_for(root: Path, object_name: str) -> set[str] | None:
    """Custom field API names declared for `object_name`, or None if unknown.

    None means "this object's fields/ folder is not in the tree", which must be
    treated as no-opinion rather than as an empty set.
    """
    for objects_dir in find_dirs(root, "objects"):
        fields_dir = objects_dir / object_name / "fields"
        if fields_dir.is_dir():
            names = set()
            for f in fields_dir.glob("*.field-meta.xml"):
                names.add(f.name[: -len(".field-meta.xml")])
            for f in fields_dir.glob("*.field"):
                names.add(f.name[: -len(".field")])
            return names
    return None


def flow_api_names(root: Path) -> set[str] | None:
    dirs = find_dirs(root, "flows")
    if not dirs:
        return None
    names: set[str] = set()
    for d in dirs:
        for f in d.glob("*.flow-meta.xml"):
            names.add(f.name[: -len(".flow-meta.xml")])
        for f in d.glob("*.flow"):
            names.add(f.name[: -len(".flow")])
    return names


def referenced_action_names(root: Path) -> tuple[set[str] | None, list[Finding]]:
    """Action names named by any Layout or FlexiPage, plus layout-level findings.

    Returns (None, findings) when neither layouts/ nor flexipages/ is present,
    so the caller can skip the placement check instead of reporting everything
    as unplaced.
    """
    findings: list[Finding] = []
    layout_dirs = find_dirs(root, "layouts")
    flexi_dirs = find_dirs(root, "flexipages")
    if not layout_dirs and not flexi_dirs:
        return None, findings

    referenced: set[str] = set()

    def collect(path: Path, label: str):
        try:
            root_el = ET.parse(path).getroot()
        except ET.ParseError as exc:
            findings.append(Finding("ERROR", label, f"XML parse error: {exc}"))
            return None
        for el in root_el.iter():
            if el.tag in (_tag("quickActionName"), _tag("actionName")) and el.text:
                referenced.add(el.text.strip())
        return root_el

    for d in layout_dirs:
        files = sorted(d.glob("*.layout-meta.xml")) + sorted(d.glob("*.layout"))
        for lf in files:
            layout_label = "Layout: " + lf.name.split(".layout")[0]
            root_el = collect(lf, layout_label)
            if root_el is None:
                continue
            for pal in root_el.iter(_tag("platformActionList")):
                context = _text(pal, "actionListContext")
                if context not in RECORD_BAR_CONTEXTS:
                    continue
                count = len(pal.findall(_tag("platformActionListItems")))
                if count > MAX_VISIBLE_ACTIONS:
                    findings.append(
                        Finding(
                            "WARN",
                            layout_label,
                            f"platformActionList (actionListContext={context}) has {count} "
                            f"actions, over the {MAX_VISIBLE_ACTIONS} threshold. Actions past "
                            "roughly the fifth sortOrder collapse into the 'More' overflow and "
                            "go undiscovered. Re-sort or remove low-use actions.",
                        )
                    )

    for d in flexi_dirs:
        files = sorted(d.glob("*.flexipage-meta.xml")) + sorted(d.glob("*.flexipage"))
        for ff in files:
            root_el = collect(ff, "FlexiPage: " + ff.name.split(".flexipage")[0])
            if root_el is None:
                continue
            # Dynamic Actions carry the action name in a generic <value> element
            # inside componentInstanceProperties, not in <actionName>.
            for el in root_el.iter(_tag("value")):
                if el.text:
                    referenced.add(el.text.strip())

    return referenced, findings


def check_action(
    path: Path,
    root: Path,
    referenced: set[str] | None,
    flows: set[str] | None,
) -> list[Finding]:
    findings: list[Finding] = []
    full_name = action_full_name(path)
    host_object, _dev_name = split_scope(full_name)

    try:
        action = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding("ERROR", full_name, f"XML parse error: {exc}")]

    action_type = _text(action, "type")
    target_object = _text(action, "targetObject")
    label = _text(action, "label") or full_name
    subject = f"{full_name}" if label == full_name else f"{full_name} ({label})"

    # 1. Create action with nothing to create.
    if action_type == "Create" and target_object is None:
        findings.append(
            Finding(
                "ERROR",
                subject,
                "type is Create but <targetObject> is missing. A Create action must name "
                "the object it creates; the deploy fails or the action has nothing to open.",
            )
        )

    # 2. targetRecordType outside the documented enum.
    target_record_type = _text(action, "targetRecordType")
    if target_record_type is not None and target_record_type not in VALID_TARGET_RECORD_TYPES:
        findings.append(
            Finding(
                "ERROR",
                subject,
                f"<targetRecordType>{target_record_type}</targetRecordType> is not one of "
                f"{sorted(VALID_TARGET_RECORD_TYPES)}. That element is the Account "
                "business-vs-person switch only. To pin a custom record type, use a "
                "<fieldOverrides> entry on RecordTypeId instead.",
            )
        )

    # 3. Record-building action with no action layout at all.
    layout_el = _child(action, "quickActionLayout")
    if action_type in LAYOUT_BEARING_TYPES:
        if layout_el is None:
            findings.append(
                Finding(
                    "WARN",
                    subject,
                    f"type is {action_type} but there is no <quickActionLayout>. The dialog "
                    "falls back to whatever the platform picks; declare the fields explicitly.",
                )
            )
        else:
            items = layout_el.findall(".//" + _tag("quickActionLayoutItems"))
            if not items:
                findings.append(
                    Finding(
                        "WARN",
                        subject,
                        "<quickActionLayout> contains no <quickActionLayoutItems>. Users get "
                        "an empty dialog and cannot supply required fields.",
                    )
                )

        # 4. optionsCreateFeedItem is required in the schema for these types.
        if _text(action, "optionsCreateFeedItem") is None:
            findings.append(
                Finding(
                    "WARN",
                    subject,
                    "<optionsCreateFeedItem> is missing. The Metadata API marks it Required "
                    f"and it applies to {sorted(LAYOUT_BEARING_TYPES)} actions. State true or "
                    "false deliberately rather than inheriting a feed post.",
                )
            )

    # 5. Global custom-component action.
    if action_type == "LightningComponent" and host_object is None:
        findings.append(
            Finding(
                "WARN",
                subject,
                "Global action of type LightningComponent. Custom components exposed as a "
                "global action run in the Field Service mobile app, not in standard Lightning "
                "Experience, so this action can test green in an FSL org and be invisible in "
                "production. Use a Visualforce page for a standard LE global action.",
            )
        )

    # 6. fieldOverrides naming a custom field the tree does not declare.
    override_object = target_object or host_object
    if override_object:
        declared = custom_fields_for(root, override_object)
        if declared is not None:
            for override in action.findall(_tag("fieldOverrides")):
                field_name = _text(override, "field")
                if field_name is None:
                    findings.append(
                        Finding("ERROR", subject, "<fieldOverrides> entry has no <field>.")
                    )
                    continue
                if field_name.endswith("__c") and field_name not in declared:
                    findings.append(
                        Finding(
                            "WARN",
                            subject,
                            f"predefined value targets {override_object}.{field_name}, which is "
                            f"not declared under objects/{override_object}/fields/. Either the "
                            "field is missing from this deployment or the API name is stale.",
                        )
                    )

    # 7. Flow action pointing at a flow that is not in the tree.
    if action_type == "Flow":
        flow_name = _text(action, "flowDefinition")
        if flow_name is None:
            findings.append(
                Finding(
                    "ERROR",
                    subject,
                    "type is Flow but <flowDefinition> is missing. It must hold the flow's "
                    "API name.",
                )
            )
        elif flows is not None and flow_name not in flows:
            findings.append(
                Finding(
                    "WARN",
                    subject,
                    f"<flowDefinition>{flow_name}</flowDefinition> has no matching file under "
                    "flows/. Deploy the flow in the same change or the action opens onto "
                    "nothing.",
                )
            )

    # 8. Unplaced action.
    if referenced is not None and full_name not in referenced:
        findings.append(
            Finding(
                "INFO",
                subject,
                "no Layout or FlexiPage in this tree references the action. It will deploy "
                "cleanly and be invisible to every user. Add it to a platformActionList "
                "(actionListContext Record) or to the object's Lightning record page.",
            )
        )

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists():
        print(f"ERROR: Manifest directory not found: {root}", file=sys.stderr)
        return EXIT_BAD_ARGS

    actions = action_files(root)
    referenced, findings = referenced_action_names(root)
    flows = flow_api_names(root)

    for path in actions:
        findings.extend(check_action(path, root, referenced, flows))

    if not actions:
        print(f"No .quickAction metadata found under {root}. Nothing to check.")

    errors = [f for f in findings if f.severity == "ERROR"]
    warns = [f for f in findings if f.severity == "WARN"]
    infos = [f for f in findings if f.severity == "INFO"]

    for finding in errors + warns + infos:
        print(finding)

    print(
        f"\n{len(actions)} action(s) checked. "
        f"{len(errors)} error(s), {len(warns)} warning(s), {len(infos)} info."
    )

    if errors or warns:
        return EXIT_FINDINGS
    return EXIT_OK


if __name__ == "__main__":
    _result = main()
    if _result == EXIT_FINDINGS:
        # Explicit non-zero exit so CI fails on ERROR or WARN findings.
        sys.exit(1)
    sys.exit(_result)
