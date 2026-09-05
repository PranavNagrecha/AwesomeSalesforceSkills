#!/usr/bin/env python3
"""check_flow_error_monitoring.py — lint a metadata tree for flow error-monitoring gaps.

Six rules, all of them about whether a production failure would ever become visible:

  1. fault-sink-unreachable  (WARN)     a flow's fault routes never reach a Create Records
                                        on the org's error-log object
  2. log-write-unusable      (WARN)     the fault-path Create Records omits the flow name
                                        or the fault message
  3. exception-email-orphan  (ADVISORY) apexEmailNotifications exists but Flow.settings has
                                        enableFlowUseApexExceptionEmail = false, so flow
                                        error email still goes to the last modifier
  4. interview-label-missing (ADVISORY) a flow with waits/scheduledPaths has no
                                        interviewLabel, so its paused backlog is untriageable
  5. log-object-truncates    (ERROR)    the error-log object has no LongTextArea/TextArea
                                        field, so every fault message is silently truncated
  6. flowtest-missing        (ADVISORY) a flow with a fault path has no FlowTest

Grounding for each rule is in ../references/gotchas.md and ../references/metadata-examples.md.

Severity handling:
  ERROR     -> exit 1 always
  WARN      -> exit 1 only with --strict
  ADVISORY  -> never affects the exit code

stdlib only. This script reads metadata; it never contacts an org and never claims to
validate a flow the way the platform does.

Usage:
    python3 check_flow_error_monitoring.py --manifest-dir force-app/main/default
    python3 check_flow_error_monitoring.py --manifest-dir src --log-object Flow_Error_Log__c
    python3 check_flow_error_monitoring.py --manifest-dir src --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

# Flow node collections that can carry a faultConnector (api_meta.txt: FlowRecordCreate
# L70965, FlowRecordDelete L71046, FlowRecordLookup L71120, FlowRecordUpdate L71283,
# FlowActionCall L68476, FlowApexPluginCall L69688, FlowWait L72993).
FAULT_CAPABLE = (
    "recordCreates",
    "recordUpdates",
    "recordDeletes",
    "recordLookups",
    "actionCalls",
    "apexPluginCalls",
    "waits",
)

# Every collection that can be a connector target, so a fault route can be walked.
NODE_TAGS = FAULT_CAPABLE + (
    "assignments",
    "decisions",
    "loops",
    "screens",
    "subflows",
    "collectionProcessors",
    "customErrors",
    "recordRollbacks",
    "transforms",
    "orchestratedStages",
    "steps",
)

FLOW_NAME_FIELDS = ("source__c", "flow_name__c", "flow__c", "flow_api_name__c")
MESSAGE_FIELDS = ("message__c", "fault_message__c", "error_message__c", "long_message__c")
LONG_TEXT_TYPES = ("LongTextArea", "TextArea", "Html")

SEV_ORDER = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}


# --------------------------------------------------------------------------- helpers
def child(el, tag):
    """Return a direct child Element or None.

    NEVER write `el.find(a) or el.find(b)` — an Element with no children is falsy, so a
    real match would be discarded. Always compare against None.
    """
    if el is None:
        return None
    found = el.find(NS + tag)
    if found is None:
        found = el.find(tag)
    return found


def children(el, tag):
    if el is None:
        return []
    out = el.findall(NS + tag)
    if not out:
        out = el.findall(tag)
    return out


def text(el, tag, default=""):
    node = child(el, tag)
    if node is None or node.text is None:
        return default
    return node.text.strip()


def parse(path):
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, f"{path}: not well-formed XML ({exc})"


def localname(tag):
    return tag.split("}")[-1]


# --------------------------------------------------------------------------- discovery
def find_flows(root: Path):
    files = list(root.rglob("*.flow-meta.xml")) + list(root.rglob("*.flow"))
    return sorted(set(files))


def find_flowtests(root: Path):
    return sorted(set(list(root.rglob("*.flowtest-meta.xml")) + list(root.rglob("*.flowtest"))))


def find_flow_settings(root: Path):
    hits = [p for p in root.rglob("Flow.settings*") if p.is_file()]
    return sorted(hits)


def find_apex_email_notifications(root: Path):
    hits = [p for p in root.rglob("*.notifications*") if p.is_file()]
    hits += [p for p in root.rglob("*") if p.is_file() and p.name.startswith("apexEmailNotifications.")]
    return sorted(set(hits))


def find_log_object(root: Path, log_object: str):
    """Return (object_file, [field_files]) for the error-log object in either layout.

    Source format: objects/<Obj>/<Obj>.object-meta.xml + objects/<Obj>/fields/*.field-meta.xml
    MDAPI format:  objects/<Obj>.object with inline <fields> elements
    """
    obj_files = [
        p
        for p in root.rglob("*")
        if p.is_file()
        and (p.name == f"{log_object}.object-meta.xml" or p.name == f"{log_object}.object")
    ]
    if not obj_files:
        return None, []
    obj_file = obj_files[0]
    fields_dir = obj_file.parent / "fields"
    field_files = sorted(fields_dir.glob("*.field-meta.xml")) if fields_dir.is_dir() else []
    return obj_file, field_files


# --------------------------------------------------------------------------- flow model
class FlowModel:
    def __init__(self, path: Path, root_el):
        self.path = path
        self.api_name = path.name.split(".")[0]
        self.root = root_el
        self.nodes = {}          # name -> (collection tag, element)
        self.fault_capable = []  # (collection tag, name, element)
        for tag in NODE_TAGS:
            for el in children(root_el, tag):
                name = text(el, "name")
                if not name:
                    continue
                self.nodes[name] = (tag, el)
                if tag in FAULT_CAPABLE:
                    self.fault_capable.append((tag, name, el))

    def out_edges(self, el):
        targets = []
        for conn_tag in ("connector", "faultConnector", "defaultConnector",
                         "nextValueConnector", "noMoreValuesConnector"):
            for conn in children(el, conn_tag):
                ref = text(conn, "targetReference")
                if ref:
                    targets.append(ref)
        # decisions nest their connector inside each <rules>
        for rule in children(el, "rules"):
            for conn in children(rule, "connector"):
                ref = text(conn, "targetReference")
                if ref:
                    targets.append(ref)
        # waits nest theirs inside each <waitEvents>
        for ev in children(el, "waitEvents"):
            for conn in children(ev, "connector"):
                ref = text(conn, "targetReference")
                if ref:
                    targets.append(ref)
        return targets

    def fault_targets(self):
        out = []
        for _tag, name, el in self.fault_capable:
            for conn in children(el, "faultConnector"):
                ref = text(conn, "targetReference")
                if ref:
                    out.append((name, ref))
        return out

    def reachable(self, start, limit=60):
        """Node names reachable from `start`, following every connector kind."""
        seen, stack = set(), [start]
        while stack and len(seen) < limit:
            cur = stack.pop()
            if cur in seen or cur not in self.nodes:
                continue
            seen.add(cur)
            stack.extend(self.out_edges(self.nodes[cur][1]))
        return seen

    def log_writes(self, log_object):
        """Create Records elements targeting the error-log object."""
        out = []
        for el in children(self.root, "recordCreates"):
            if text(el, "object").lower() == log_object.lower():
                out.append((text(el, "name"), el))
        return out

    def has_scheduled_or_wait(self):
        if children(self.root, "waits"):
            return True
        start = child(self.root, "start")
        return bool(children(start, "scheduledPaths"))

    def interview_label(self):
        return text(self.root, "interviewLabel")


# --------------------------------------------------------------------------- rules
def rule_fault_sink(flows, log_object, issues):
    for fm in flows:
        if not fm.fault_capable:
            continue
        sinks = {name for name, _el in fm.log_writes(log_object)}
        if not sinks:
            unwired = [n for _t, n, el in fm.fault_capable if child(el, "faultConnector") is None]
            detail = f" ({len(unwired)} element(s) carry no faultConnector at all: {', '.join(sorted(unwired)[:4])})" if unwired else ""
            issues.append((
                "WARN", "fault-sink-unreachable", str(fm.path),
                f"{fm.api_name}: {len(fm.fault_capable)} fault-capable element(s) and no "
                f"Create Records on {log_object}. A failure here leaves no queryable row"
                f"{detail}.",
            ))
            continue
        reached = set()
        for _src, target in fm.fault_targets():
            reached |= fm.reachable(target)
        if not (reached & sinks):
            issues.append((
                "WARN", "fault-sink-unreachable", str(fm.path),
                f"{fm.api_name}: a {log_object} Create Records exists ({', '.join(sorted(sinks))}) "
                f"but no faultConnector route reaches it. The sink is on the success path only.",
            ))


def rule_log_write_fields(flows, log_object, issues):
    for fm in flows:
        fault_reached = set()
        for _src, target in fm.fault_targets():
            fault_reached |= fm.reachable(target)
        for name, el in fm.log_writes(log_object):
            if name not in fault_reached:
                continue
            mapped, values = set(), []
            for ia in children(el, "inputAssignments"):
                field = text(ia, "field").lower()
                mapped.add(field)
                val = child(ia, "value")
                values.append((text(val, "elementReference") + " " + text(val, "stringValue")).lower())
            blob = " ".join(values)
            missing = []
            if not (mapped & set(FLOW_NAME_FIELDS)):
                missing.append("flow name (expected one of: " + ", ".join(FLOW_NAME_FIELDS) + ")")
            has_msg_field = bool(mapped & set(MESSAGE_FIELDS))
            has_msg_value = "faultmessage" in blob
            if not (has_msg_field and has_msg_value):
                if not has_msg_field:
                    missing.append("fault message field (expected one of: " + ", ".join(MESSAGE_FIELDS) + ")")
                elif not has_msg_value:
                    missing.append("a $Flow.FaultMessage reference in the message field")
            if missing:
                issues.append((
                    "WARN", "log-write-unusable", str(fm.path),
                    f"{fm.api_name}.{name} writes to {log_object} on the fault path but omits "
                    + "; ".join(missing) + ". A log row without those two is a row nobody can triage.",
                ))


def rule_exception_email(settings_files, notif_files, issues):
    if not notif_files:
        return
    for path in settings_files:
        root_el, err = parse(path)
        if root_el is None:
            issues.append(("ERROR", "unparseable", str(path), err))
            continue
        val = text(root_el, "enableFlowUseApexExceptionEmail")
        if val.lower() == "false":
            issues.append((
                "ADVISORY", "exception-email-orphan", str(path),
                "enableFlowUseApexExceptionEmail is false while "
                f"{notif_files[0].name} defines recipients. Flow error email still goes to "
                "the user who last modified the flow, not to that list "
                "(api_meta.txt L116961-L116967).",
            ))


def rule_interview_label(flows, issues):
    for fm in flows:
        if fm.has_scheduled_or_wait() and not fm.interview_label():
            issues.append((
                "ADVISORY", "interview-label-missing", str(fm.path),
                f"{fm.api_name} has waits or scheduledPaths but no interviewLabel. Paused "
                "interviews will be indistinguishable in FlowInterview.InterviewLabel and in "
                "the paused-interview list (api_meta.txt L68156-L68160). flow/flow-debugging "
                "owns the element-naming rule this extends.",
            ))


def rule_log_object_field(obj_file, field_files, log_object, issues):
    if obj_file is None:
        return
    types = []
    for fpath in field_files:
        root_el, err = parse(fpath)
        if root_el is None:
            issues.append(("ERROR", "unparseable", str(fpath), err))
            continue
        types.append(text(root_el, "type"))
    root_el, err = parse(obj_file)
    if root_el is None:
        issues.append(("ERROR", "unparseable", str(obj_file), err))
        return
    for fel in children(root_el, "fields"):
        types.append(text(fel, "type"))
    if not any(t in LONG_TEXT_TYPES for t in types):
        issues.append((
            "ERROR", "log-object-truncates", str(obj_file),
            f"{log_object} has no LongTextArea/TextArea field ({len(types)} field(s) found: "
            f"{', '.join(sorted(set(t for t in types if t))) or 'none'}). A fault message "
            "written into a Text field is truncated on save, so the row looks like a log entry "
            "and is not one.",
        ))


def rule_flowtest(flows, flowtest_files, issues):
    covered = set()
    for path in flowtest_files:
        root_el, err = parse(path)
        if root_el is None:
            issues.append(("ERROR", "unparseable", str(path), err))
            continue
        api = text(root_el, "flowApiName")
        if api:
            covered.add(api)
    for fm in flows:
        if not fm.fault_targets():
            continue
        if fm.api_name not in covered:
            issues.append((
                "ADVISORY", "flowtest-missing", str(fm.path),
                f"{fm.api_name} has a fault path and no FlowTest naming it in flowApiName. "
                "Use the HasError operator (api_meta.txt L74203, API 64.0+) to prove the "
                "fault route is reached. flow/flow-testing owns strategy.",
            ))


# --------------------------------------------------------------------------- driver
def run(manifest_dir: Path, log_object: str):
    issues = []
    flow_files = find_flows(manifest_dir)
    flowtest_files = find_flowtests(manifest_dir)
    settings_files = find_flow_settings(manifest_dir)
    notif_files = find_apex_email_notifications(manifest_dir)
    obj_file, field_files = find_log_object(manifest_dir, log_object)

    scanned = len(flow_files) + len(flowtest_files) + len(settings_files) + len(notif_files)
    if obj_file is not None:
        scanned += 1

    flows = []
    for path in flow_files:
        root_el, err = parse(path)
        if root_el is None:
            issues.append(("ERROR", "unparseable", str(path), err))
            continue
        if localname(root_el.tag) != "Flow":
            continue
        flows.append(FlowModel(path, root_el))

    rule_fault_sink(flows, log_object, issues)
    rule_log_write_fields(flows, log_object, issues)
    rule_exception_email(settings_files, notif_files, issues)
    rule_interview_label(flows, issues)
    rule_log_object_field(obj_file, field_files, log_object, issues)
    rule_flowtest(flows, flowtest_files, issues)
    return issues, scanned, len(flows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint Salesforce metadata for flow error-monitoring gaps.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata source tree (default: current directory).",
    )
    parser.add_argument(
        "--log-object",
        default="Application_Log__c",
        help="API name of the org's central error-log object (default: Application_Log__c).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN to a failing exit code. ADVISORY never fails.",
    )
    args = parser.parse_args()

    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues, scanned, n_flows = run(manifest_dir, args.log_object)

    if scanned == 0:
        print(
            f"WARN: no flows, flow tests, Flow.settings, apexEmailNotifications or "
            f"{args.log_object} metadata found under {manifest_dir} — nothing to check.",
            file=sys.stderr,
        )
        return 0

    issues.sort(key=lambda i: (SEV_ORDER.get(i[0], 3), i[1], i[2]))
    for severity, rule, where, message in issues:
        stream = sys.stderr if severity in ("ERROR", "WARN") else sys.stdout
        print(f"{severity}: [{rule}] {where}: {message}", file=stream)

    errors = sum(1 for i in issues if i[0] == "ERROR")
    warns = sum(1 for i in issues if i[0] == "WARN")
    advisories = sum(1 for i in issues if i[0] == "ADVISORY")
    print(
        f"\nScanned {scanned} file(s) ({n_flows} flow(s)) under {manifest_dir} "
        f"against log object {args.log_object}: "
        f"{errors} ERROR, {warns} WARN, {advisories} ADVISORY."
    )

    if errors:
        return 1
    if args.strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
