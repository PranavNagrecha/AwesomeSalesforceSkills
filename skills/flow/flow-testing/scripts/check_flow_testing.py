#!/usr/bin/env python3
"""Checker for the Flow Testing skill.

Parses every ``*.flow-meta.xml`` / ``*.flow`` and every ``*.flowtest-meta.xml`` /
``*.flowtest`` under --manifest-dir, plus any Apex class that drives a flow, and reports
test defects that deploy cleanly and prove nothing at run time. Stdlib only.

Checks implemented (see ../references/gotchas.md for the grounding):

  FT01  A flow whose <status> is Active and that FlowTest can cover, with no FlowTest in
        the tree naming it in <flowApiName>. FlowTest exists to run before activation
        (api_meta.txt L73961-73962). Flow types the guide does not list -- screen,
        scheduled-only, platform-event -- are exempt, not flagged (Gotcha 7).
  FT02  A FlowTest whose <flowApiName> resolves to no flow file in the tree. The field is
        required and is a plain string, so a rename leaves it dangling (api_meta.txt
        L73990-73995, Gotcha 9).
  FT03  A FlowTest with a Start test point and no Finish test point. Assertions can only
        be attached to Start and Finish (api_meta.txt L74143-74150); with no Finish point
        nothing about the flow's outcome is asserted (Gotcha 5).
  FT04  A test point that carries neither <assertions> nor <parameters> (inert), or a
        Finish test point with zero <assertions>. "If one assertion evaluates to false,
        the test run fails" -- zero assertions means the run cannot fail (api_meta.txt
        L74157-74159).
  FT05  A FlowTest for a flow whose <recordTriggerType> is Update or CreateAndUpdate that
        omits an InputTriggeringRecordInitial or InputTriggeringRecordUpdated parameter.
        Both types exist and both require $Record (api_meta.txt L74296-74320, Gotcha 8).
  FT06  An Apex class that references Flow.Interview and contains no assertion. A flow
        that merely started is not a flow that behaved (Gotcha 9: getVariableValue "checks
        for the existence of the variable at run time only", apexrefguide.txt L158150).
  FT07  A test point whose <elementApiName> is not Start or Finish -- the only two
        documented values (api_meta.txt L74143-74150).

Exit codes: 1 if --manifest-dir does not exist or any issue is found, else 0.
An empty tree is a WARN, not a failure.

Usage:
    python3 check_flow_testing.py --manifest-dir force-app/main/default
    python3 check_flow_testing.py --manifest-dir . --quiet
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

# api_meta.txt L74143-74150 -- the only documented elementApiName values.
TEST_POINTS = ("Start", "Finish")

# api_meta.txt L73961-73962 -- the flow kinds FlowTest is documented to cover. A flow with
# no <triggerType> "starts only when a user or app launches the flow" (L72496-72499), i.e.
# it is autolaunched.
TESTABLE_TRIGGER_TYPES = {
    "",
    "RecordBeforeSave",
    "RecordAfterSave",
    "RecordBeforeDelete",
    "DataCloudDataChange",
}

# api_meta.txt L72448-72457 -- trigger types that carry a before and an after image.
UPDATE_TRIGGER_TYPES = {"Update", "CreateAndUpdate"}

PARAM_INITIAL = "InputTriggeringRecordInitial"
PARAM_UPDATED = "InputTriggeringRecordUpdated"

ASSERT_RE = re.compile(
    r"\b(?:Assert\s*\.\s*\w+|System\s*\.\s*assert\w*|assertEquals|assertNotEquals)\s*\(",
    re.IGNORECASE,
)
INTERVIEW_RE = re.compile(r"\bFlow\s*\.\s*Interview\b")
ISTEST_RE = re.compile(r"@\s*IsTest\b", re.IGNORECASE)


def _child(elem, tag):
    """First child with ``tag``, or None.

    An ElementTree Element with no children is falsy, so ``a.find(x) or a.find(y)``
    silently discards real leaf nodes. Always compare against None.
    """
    if elem is None:
        return None
    found = elem.find(f"{NS}{tag}")
    if found is None:
        found = elem.find(tag)
    return found


def _children(elem, tag):
    if elem is None:
        return []
    found = elem.findall(f"{NS}{tag}")
    return found if found else elem.findall(tag)


def _text(elem, tag, default=""):
    node = _child(elem, tag)
    if node is None or node.text is None:
        return default
    return node.text.strip()


def _api_name(path: Path) -> str:
    name = path.name
    for suffix in (".flowtest-meta.xml", ".flowtest", ".flow-meta.xml", ".flow"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def _parse(path: Path):
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, f"{path}: not well-formed XML ({exc}). Nothing below could be checked."


def collect_flows(manifest_dir: Path):
    """Return {api_name: {...}} for every flow file, plus parse errors."""
    flows, issues = {}, []
    paths = sorted(set(manifest_dir.rglob("*.flow-meta.xml")) | set(manifest_dir.rglob("*.flow")))
    for path in paths:
        root, err = _parse(path)
        if err:
            issues.append(err)
            continue
        start = _child(root, "start")
        flows[_api_name(path)] = {
            "path": path,
            "status": _text(root, "status"),
            "processType": _text(root, "processType"),
            "triggerType": _text(start, "triggerType") if start is not None else "",
            "recordTriggerType": _text(start, "recordTriggerType") if start is not None else "",
        }
    return flows, issues


def collect_flowtests(manifest_dir: Path):
    tests, issues = [], []
    paths = sorted(
        set(manifest_dir.rglob("*.flowtest-meta.xml")) | set(manifest_dir.rglob("*.flowtest"))
    )
    for path in paths:
        root, err = _parse(path)
        if err:
            issues.append(err)
            continue
        tests.append((path, root))
    return tests, issues


def check_flowtest(path: Path, root, flows: dict) -> list[str]:
    issues: list[str] = []
    name = _api_name(path)
    flow_api_name = _text(root, "flowApiName")

    # FT02
    flow = flows.get(flow_api_name)
    if not flow_api_name:
        issues.append(
            f"{path}: FT02 no <flowApiName>. The field is required (api_meta.txt L73990-73995); "
            "this component names no flow at all."
        )
    elif flow is None:
        issues.append(
            f"{path}: FT02 <flowApiName>{flow_api_name}</flowApiName> resolves to no "
            f"*.flow-meta.xml in the tree. <flowApiName> is a plain string, so a flow rename "
            "leaves it dangling and the test silently stops covering anything (Gotcha 9)."
        )

    points = _children(root, "testPoints")
    kinds = [_text(p, "elementApiName") for p in points]

    # FT07
    for kind in kinds:
        if kind not in TEST_POINTS:
            issues.append(
                f"{path}: FT07 test point <elementApiName>{kind or '(empty)'}</elementApiName> is "
                "not Start or Finish, the only two documented values (api_meta.txt L74143-74150). "
                "A FlowTest cannot assert mid-flow; write the branch outcome to a flow variable "
                "and assert it at Finish."
            )

    # FT03
    if "Start" in kinds and "Finish" not in kinds:
        issues.append(
            f"{path}: FT03 has a Start test point and no Finish test point. Nothing about the "
            "flow's outcome is asserted, so this test can only fail by erroring out."
        )

    # FT04
    for point, kind in zip(points, kinds):
        assertions = _children(point, "assertions")
        parameters = _children(point, "parameters")
        if kind == "Finish" and not assertions:
            issues.append(
                f"{path}: FT04 the Finish test point has zero <assertions>. \"If one assertion "
                "evaluates to false, the test run fails\" (api_meta.txt L74157-74159) -- with "
                "none, the run cannot fail."
            )
        elif not assertions and not parameters:
            issues.append(
                f"{path}: FT04 the '{kind or '(unnamed)'}' test point carries neither "
                "<assertions> nor <parameters>. It feeds nothing in and proves nothing."
            )

    # FT05
    if flow is not None and flow["recordTriggerType"] in UPDATE_TRIGGER_TYPES:
        seen = {
            _text(param, "type")
            for point in points
            for param in _children(point, "parameters")
        }
        for required, why in (
            (PARAM_INITIAL, "the before image"),
            (PARAM_UPDATED, "the after image"),
        ):
            if required not in seen:
                issues.append(
                    f"{path}: FT05 covers '{flow_api_name}', whose recordTriggerType is "
                    f"{flow['recordTriggerType']}, but supplies no <type>{required}</type> "
                    f"parameter -- {why} is missing. An update-triggered flow evaluated against "
                    "one image is being tested as a create (api_meta.txt L74296-74320, Gotcha 8)."
                )

    return issues


def check_active_flows(flows: dict, tested: set) -> list[str]:
    issues = []
    for name, flow in sorted(flows.items()):
        if flow["status"] != "Active":
            continue
        if flow["processType"] != "AutoLaunchedFlow":
            continue  # screen flows are exempt: FlowTest does not cover them (Gotcha 7)
        if flow["triggerType"] not in TESTABLE_TRIGGER_TYPES:
            continue  # scheduled / platform-event / segment flows are not in the guide's list
        if name in tested:
            continue
        issues.append(
            f"{flow['path']}: FT01 <status>Active</status> and no FlowTest in this tree names "
            f"'{name}' in <flowApiName>. FlowTest is documented as the pre-activation check "
            "(api_meta.txt L73961-73962); this flow was activated without one."
        )
    return issues


def check_apex(manifest_dir: Path) -> list[str]:
    issues = []
    for path in sorted(manifest_dir.rglob("*.cls")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if not INTERVIEW_RE.search(text):
            continue
        if not ISTEST_RE.search(text):
            continue
        if ASSERT_RE.search(text):
            continue
        issues.append(
            f"{path}: FT06 is a test class that starts a flow through Flow.Interview and "
            "contains no assertion. getVariableValue \"checks for the existence of the variable "
            "at run time only, not at compile time\" and returns null for a name it cannot find "
            "(apexrefguide.txt L158148-158153), so a run that does not throw proves nothing."
        )
    return issues


def check_flow_testing(manifest_dir: Path) -> tuple[list[str], list[str]]:
    """Return (issues, warnings)."""
    flows, issues = collect_flows(manifest_dir)
    tests, test_errors = collect_flowtests(manifest_dir)
    issues.extend(test_errors)

    warnings: list[str] = []
    if not flows and not tests:
        warnings.append(
            f"No *.flow-meta.xml and no *.flowtest-meta.xml found under {manifest_dir}. "
            "Point --manifest-dir at the source root (for example force-app/main/default)."
        )

    tested = set()
    for path, root in tests:
        tested.add(_text(root, "flowApiName"))
        issues.extend(check_flowtest(path, root, flows))

    issues.extend(check_active_flows(flows, tested))
    issues.extend(check_apex(manifest_dir))
    return issues, warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check flows, FlowTests and Apex flow drivers for coverage defects that deploy cleanly.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source tree (default: current directory).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the 'no issues' line; still exits non-zero on findings.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues, warnings = check_flow_testing(manifest_dir)

    for warning in warnings:
        print(f"WARN: {warning}", file=sys.stderr)

    if not issues:
        if not args.quiet:
            print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
