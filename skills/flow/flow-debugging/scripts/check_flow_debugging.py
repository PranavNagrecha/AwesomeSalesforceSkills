#!/usr/bin/env python3
"""Static checks for Flow debuggability and for the capture rig around it.

Answers one question over a source tree: **if this flow fails in production tonight,
will anyone be able to find out where?** It never contacts an org, never runs a flow,
and never claims to validate a flow the way the platform does.

Six checks, each grounded in a guide line cited in ``references/metadata-examples.md``
and ``references/gotchas.md``:

1.  ERROR   ``--manifest-dir`` does not exist.
2.  WARN    A ``DebugLevel`` JSON whose own text shows flow-debugging intent sets the
            ``Workflow`` category below ``FINER``. ``FLOW_VALUE_ASSIGNMENT``,
            ``FLOW_RULE_DETAIL``, ``FLOW_LOOP_DETAIL`` and every ``*_LIMIT_USAGE`` event
            are FINER+; ``FLOW_ELEMENT_FAULT`` is WARNING+ and is dropped entirely at
            ``ERROR`` (apexdev.txt L38792, L38389-L38403).
3.  ADVISORY A ``TraceFlag`` ``ExpirationDate`` more than 24 hours after its
            ``StartDate`` (or after now, when no start is given). Log volume is capped
            org-wide and blowing the cap disables every trace flag in the org
            (apexdev.txt L38119-L38126).
4.  WARN    A ``recordUpdates`` or ``recordCreates`` element with no ``faultConnector``,
            unless that element is itself reachable from a fault route -- the terminal
            fault sink is the documented exception. Without a fault connector the failure
            logs as ``FLOW_ELEMENT_ERROR`` (ERROR+) instead of ``FLOW_ELEMENT_FAULT``
            (WARNING+) and the transaction rolls back. ``flow/fault-handling`` owns the
            deep version of this rule across every fault-capable element type; this
            package keeps one rule so a debuggability lint is not a fault-design lint.
5.  WARN    A flow with ``waits`` or scheduled paths and no ``interviewLabel``. That label
            is the only human-readable handle on ``FlowInterview.InterviewLabel`` and in
            the paused-interviews list (api_meta.txt L68156-L68160,
            object_reference.txt L139951-L139955), so paused interviews are otherwise
            unidentifiable.
6.  ADVISORY A flow shipped ``<status>Active</status>`` with no ``FlowTest`` anywhere in
            the tree naming it. ``flow/flow-testing`` owns test coverage as a gate; this
            stays advisory on purpose.
7.  ADVISORY ``apiVersion`` below 50.

Exit codes
----------
0   no ERROR findings
1   at least one ERROR finding, or --manifest-dir is missing

``--strict`` promotes every WARN to ERROR. ADVISORY is never promoted. An empty tree is
a WARN, not a failure -- pointing this at a repo with no flows yet is legitimate.

Stdlib only.

Usage
-----
    python3 check_flow_debugging.py --manifest-dir force-app/main/default
    python3 check_flow_debugging.py --manifest-dir force-app/main/default --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime, timedelta, timezone
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

ERROR, WARN, ADVISORY = "ERROR", "WARN", "ADVISORY"

# Debug log levels, lowest to highest (apexdev.txt L38396-L38403). The guide's event
# table spells the FLOW_ELEMENT_FAULT floor "WARNING" while the level list spells it
# "WARN"; both are accepted here so a hand-written DebugLevel is not failed on spelling.
LEVELS = ["NONE", "ERROR", "WARN", "INFO", "DEBUG", "FINE", "FINER", "FINEST"]
LEVEL_ALIASES = {"WARNING": "WARN"}
REQUIRED_WORKFLOW_LEVEL = "FINER"

# Node collections whose members can be connector targets. Needed to walk fault routes.
NODE_COLLECTIONS = (
    "actionCalls",
    "apexPluginCalls",
    "assignments",
    "collectionProcessors",
    "customErrors",
    "decisions",
    "loops",
    "orchestratedStages",
    "recordCreates",
    "recordDeletes",
    "recordLookups",
    "recordRollbacks",
    "recordUpdates",
    "screens",
    "steps",
    "subflows",
    "transforms",
    "waits",
)
CONNECTOR_TAGS = (
    "connector",
    "faultConnector",
    "defaultConnector",
    "nextValueConnector",
    "noMoreValuesConnector",
    "timeoutConnector",
    "connectors",
)
# The DML element types this package lints. Deliberately narrower than the fault-handling
# checker's list: one rule, not a second implementation of that skill's checks.
DML_COLLECTIONS = ("recordCreates", "recordUpdates")

# Words in a DebugLevel JSON that mark it as intended for a flow-debugging session.
FLOW_INTENT_RE = re.compile(r"flow[\s_-]*debug|debug[\s_-]*flow|flow[\s_-]*trace", re.I)


class Finding:
    __slots__ = ("severity", "path", "message")

    def __init__(self, severity: str, path: str, message: str) -> None:
        self.severity = severity
        self.path = path
        self.message = message

    def render(self, promote_warn: bool) -> str:
        sev = ERROR if (promote_warn and self.severity == WARN) else self.severity
        return f"{sev}: {self.path}: {self.message}"

    def effective(self, promote_warn: bool) -> str:
        return ERROR if (promote_warn and self.severity == WARN) else self.severity


# --------------------------------------------------------------------------- helpers


def _find(parent: ET.Element, tag: str) -> ET.Element | None:
    """Namespace-aware single-child lookup.

    Never write ``parent.find(a) or parent.find(b)``: a childless Element is falsy, so a
    real leaf element would be discarded. Always compare against None explicitly.
    """
    child = parent.find(f"{NS}{tag}")
    if child is None:
        child = parent.find(tag)
    return child


def _text(parent: ET.Element | None, tag: str) -> str:
    if parent is None:
        return ""
    child = _find(parent, tag)
    if child is None:
        return ""
    return (child.text or "").strip()


def _children(parent: ET.Element, tag: str) -> list[ET.Element]:
    found = parent.findall(f"{NS}{tag}")
    if not found:
        found = parent.findall(tag)
    return found


def _norm_level(value: str) -> str:
    v = value.strip().upper()
    return LEVEL_ALIASES.get(v, v)


def _level_rank(value: str) -> int:
    try:
        return LEVELS.index(_norm_level(value))
    except ValueError:
        return -1


def _parse_iso(value: str) -> datetime | None:
    """Parse the ISO-8601 shapes a TraceFlag body normally carries."""
    v = value.strip()
    if not v:
        return None
    v = v.replace("Z", "+00:00")
    # '+0000' -> '+00:00' so fromisoformat accepts it on older interpreters
    v = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", v)
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


# ------------------------------------------------------------------------ flow checks


def _fault_reachable(root: ET.Element) -> set[str]:
    """Names of every node reachable from any faultConnector in the flow.

    These are the fault-route elements. A DML element inside one is the terminal fault
    sink; requiring a faultConnector on it would demand an infinite regress of sinks.
    """
    by_name: dict[str, ET.Element] = {}
    for coll in NODE_COLLECTIONS:
        for node in _children(root, coll):
            name = _text(node, "name")
            if name:
                by_name[name] = node

    seeds: deque[str] = deque()
    for coll in NODE_COLLECTIONS:
        for node in _children(root, coll):
            for fc in _children(node, "faultConnector"):
                target = _text(fc, "targetReference")
                if target:
                    seeds.append(target)

    seen: set[str] = set()
    while seeds:
        name = seeds.popleft()
        if name in seen:
            continue
        seen.add(name)
        node = by_name.get(name)
        if node is None:
            continue
        for tag in CONNECTOR_TAGS:
            for conn in _children(node, tag):
                target = _text(conn, "targetReference")
                if target and target not in seen:
                    seeds.append(target)
        # decisions carry their connectors one level down, inside <rules>
        for rule in _children(node, "rules"):
            for conn in _children(rule, "connector"):
                target = _text(conn, "targetReference")
                if target and target not in seen:
                    seeds.append(target)
    return seen


def check_flow(path: Path, rel: str, flowtest_targets: set[str]) -> list[Finding]:
    out: list[Finding] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding(ERROR, rel, f"XML parse error - {exc}")]

    api_version = _text(root, "apiVersion")
    if api_version:
        try:
            if float(api_version) < 50.0:
                out.append(
                    Finding(
                        ADVISORY,
                        rel,
                        f"apiVersion {api_version} is below 50. Several debugging affordances "
                        f"this skill relies on are gated above it - runInMode "
                        f"SystemModeWithoutSharing is API 49+, FlowTest is API 55+, the "
                        f"HasError operator is API 64+, FlowInterview.Error is API 62+.",
                    )
                )
        except ValueError:
            out.append(Finding(WARN, rel, f"apiVersion '{api_version}' is not a number."))
    else:
        out.append(
            Finding(WARN, rel, "No apiVersion. Retrieved flows always carry one; a hand-written "
                               "flow without it deploys at an unpredictable version.")
        )

    # 4. DML elements without a fault connector, excluding the fault route itself.
    on_fault_route = _fault_reachable(root)
    for coll in DML_COLLECTIONS:
        for node in _children(root, coll):
            name = _text(node, "name") or "(unnamed)"
            if _find(node, "faultConnector") is not None:
                continue
            if name in on_fault_route:
                continue
            out.append(
                Finding(
                    WARN,
                    rel,
                    f"{coll} '{name}' has no faultConnector. Its failure will log as "
                    f"FLOW_ELEMENT_ERROR (Workflow ERROR+) instead of FLOW_ELEMENT_FAULT "
                    f"(Workflow WARNING+) and will roll back the transaction. See "
                    f"flow/fault-handling for the route design.",
                )
            )

    # 5. interviewLabel on flows that can pause.
    starts = _children(root, "start")
    has_scheduled_path = any(_children(s, "scheduledPaths") for s in starts)
    has_waits = bool(_children(root, "waits"))
    if (has_waits or has_scheduled_path) and not _text(root, "interviewLabel"):
        why = " and ".join(
            w for w in (("waits" if has_waits else ""), ("scheduled paths" if has_scheduled_path else "")) if w
        )
        out.append(
            Finding(
                WARN,
                rel,
                f"Flow has {why} but no interviewLabel. Paused interviews will be "
                f"unidentifiable in FlowInterview.InterviewLabel and in the paused-interviews "
                f"list, which is the only handle you get once the debug log has expired.",
            )
        )

    # 6. Active flow with no FlowTest naming it.
    if _text(root, "status") == "Active":
        api_name = path.name.split(".")[0]
        if api_name not in flowtest_targets:
            out.append(
                Finding(
                    ADVISORY,
                    rel,
                    f"Shipped as Active with no FlowTest in this tree naming "
                    f"'{api_name}'. FlowTest exists to run before activation "
                    f"(api_meta.txt L73961-L73962). flow/flow-testing owns coverage as a "
                    f"release gate; this is advisory here.",
                )
            )
    return out


def collect_flowtest_targets(manifest_dir: Path) -> set[str]:
    targets: set[str] = set()
    for path in manifest_dir.rglob("*.flowtest-meta.xml"):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        name = _text(root, "flowApiName")
        if name:
            targets.add(name)
    return targets


# ------------------------------------------------------------------- capture-rig checks


def _walk_json(obj, key_lower: str):
    """Yield every dict in the document that has a case-insensitive key match."""
    if isinstance(obj, dict):
        if any(k.lower() == key_lower for k in obj):
            yield obj
        for v in obj.values():
            yield from _walk_json(v, key_lower)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_json(v, key_lower)


def _get_ci(d: dict, key: str):
    for k, v in d.items():
        if k.lower() == key.lower():
            return v
    return None


def check_capture_json(path: Path, rel: str) -> list[Finding]:
    """Lint a DebugLevel / TraceFlag request body.

    These are Tooling API objects, not Metadata API types (apexdev.txt L39543-L39546),
    so they arrive as JSON request bodies rather than as deployable metadata.
    """
    out: list[Finding] = []
    raw = path.read_text(encoding="utf-8", errors="ignore")
    if "DebugLevel" not in raw and "TraceFlag" not in raw:
        return out
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as exc:
        return [Finding(WARN, rel, f"names DebugLevel/TraceFlag but is not valid JSON - {exc}")]

    # 2. Workflow level vs flow-debugging intent.
    for level_obj in _walk_json(doc, "workflow"):
        workflow = str(_get_ci(level_obj, "Workflow") or "")
        # Intent is read from the DebugLevel's own naming fields, falling back to the
        # whole file. Documented heuristic, not a guess about the author's mind.
        intent_text = " ".join(
            str(_get_ci(level_obj, k) or "")
            for k in ("DeveloperName", "MasterLabel", "description", "Description")
        )
        intended_for_flows = bool(FLOW_INTENT_RE.search(intent_text) or FLOW_INTENT_RE.search(raw))
        if not intended_for_flows:
            continue
        rank = _level_rank(workflow)
        if rank < 0:
            out.append(
                Finding(WARN, rel, f"DebugLevel Workflow value '{workflow}' is not one of "
                                   f"{', '.join(LEVELS)}.")
            )
        elif rank < LEVELS.index(REQUIRED_WORKFLOW_LEVEL):
            lost = []
            if rank < LEVELS.index("WARN"):
                lost.append("FLOW_ELEMENT_FAULT (WARNING+)")
            if rank < LEVELS.index("FINE"):
                lost.append("FLOW_ELEMENT_BEGIN/END (FINE+)")
            lost.append("FLOW_VALUE_ASSIGNMENT, FLOW_RULE_DETAIL and every *_LIMIT_USAGE (FINER+)")
            out.append(
                Finding(
                    WARN,
                    rel,
                    f"DebugLevel names a flow-debugging intent but sets Workflow="
                    f"{_norm_level(workflow)}, below {REQUIRED_WORKFLOW_LEVEL}. This drops: "
                    f"{'; '.join(lost)}.",
                )
            )

    # 3. TraceFlag window longer than 24 hours.
    for flag in _walk_json(doc, "expirationdate"):
        exp = _parse_iso(str(_get_ci(flag, "ExpirationDate") or ""))
        if exp is None:
            continue
        start = _parse_iso(str(_get_ci(flag, "StartDate") or "")) or datetime.now(timezone.utc)
        window = exp - start
        if window > timedelta(hours=24):
            out.append(
                Finding(
                    ADVISORY,
                    rel,
                    f"TraceFlag window is {window.days}d {window.seconds // 3600}h, more than "
                    f"24h. Log volume is capped org-wide: over 1,000 MB in 15 minutes disables "
                    f"your trace flags, and over 1,000 MB accumulated blocks anyone in the org "
                    f"from adding or editing one (apexdev.txt L38119-L38126). Scope the window "
                    f"to the reproduction.",
                )
            )
    return out


# ---------------------------------------------------------------------------- driver


def run(manifest_dir: Path) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    flowtest_targets = collect_flowtest_targets(manifest_dir)

    flows = sorted(manifest_dir.rglob("*.flow-meta.xml"))
    for path in flows:
        findings.extend(check_flow(path, str(path.relative_to(manifest_dir)), flowtest_targets))

    json_files = sorted(manifest_dir.rglob("*.json"))
    for path in json_files:
        try:
            findings.extend(check_capture_json(path, str(path.relative_to(manifest_dir))))
        except OSError:
            continue

    return findings, len(flows), len(json_files)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint Salesforce flows and debug-capture bodies for debuggability.",
    )
    parser.add_argument(
        "--manifest-dir",
        required=True,
        help="Root of the Salesforce source tree to scan (e.g. force-app/main/default).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote every WARN to ERROR. ADVISORY findings are never promoted.",
    )
    args = parser.parse_args(argv)

    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: --manifest-dir not found: {manifest_dir}")
        return 1

    findings, n_flows, n_json = run(manifest_dir)

    if n_flows == 0:
        print(
            f"WARN: no *.flow-meta.xml files under '{manifest_dir}'. If flows are expected "
            f"here, check the path; an empty tree is not a failure."
        )

    order = {ERROR: 0, WARN: 1, ADVISORY: 2}
    for finding in sorted(findings, key=lambda f: (order[f.severity], f.path, f.message)):
        print(finding.render(args.strict))

    counts = {ERROR: 0, WARN: 0, ADVISORY: 0}
    for finding in findings:
        counts[finding.effective(args.strict)] += 1

    print(
        f"\nScanned {n_flows} flow(s) and {n_json} JSON file(s) under {manifest_dir}: "
        f"{counts[ERROR]} ERROR, {counts[WARN]} WARN, {counts[ADVISORY]} ADVISORY."
        + ("" if args.strict else "  (--strict promotes WARN to ERROR)")
    )
    return 1 if counts[ERROR] else 0


if __name__ == "__main__":
    sys.exit(main())
