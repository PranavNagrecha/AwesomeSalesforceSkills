#!/usr/bin/env python3
"""Checker for the flow-for-slack skill.

Parses Flow metadata (`*.flow-meta.xml` / `*.flow`) and reports problems with Slack
core actions. Slack action types come from the Metadata API InvocableActionType list
(Summer '26): slackPostMessage, slackSendMessageToLaunchFlow, slackCreateChannel,
slackArchiveChannel, slackInviteUsersToChannel, slackCheckUsersAreConnectedToSlack,
slackGetConversationInfo, slackUpdateMessage, slackPinMessage.

  ERROR   flow file does not parse
  HIGH    Slack action in a RecordBeforeSave flow (before-save flows update the
          triggering record; the Metadata API describes them that way)
  HIGH    Slack action without a faultConnector
  HIGH    slackSendMessageToLaunchFlow names a flow in this tree that is not a screen
          flow (processType Flow) saved with the Slack environment
  MEDIUM  slackCreateChannel with a literal channel name that breaks Slack's rules
          (lowercase letters, numbers, hyphens, underscores; 80 characters maximum)
  REVIEW  Slack action in a record-triggered flow that is not reachable from an
          AsyncAfterCommit path (Salesforce Help recommends the async path; UNVERIFIED
          in the fetched sources, so this is advisory)
  REVIEW  literal Slack channel name or ID in an action input (use configuration)

Input parameter API names for the Slack actions are not in the fetched Metadata API
or Actions guides, so the channel-name rule matches any slackCreateChannel input whose
name contains "name", and the launch-target rule matches any literal input that equals
a flow API name in the scanned tree.

Exit codes: 1 if the directory is missing, a file does not parse, or any HIGH finding
exists (MEDIUM and REVIEW too with --strict); 0 otherwise. Stdlib only.

Usage:
    python3 check_flow_for_slack.py --manifest-dir force-app [--strict]
    python3 check_flow_for_slack.py --self-test
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SUFFIXES = (".flow-meta.xml", ".flow")
CHANNEL_NAME_RE = re.compile(r"^[a-z0-9_-]{1,80}$")
LITERAL_CHANNEL_RE = re.compile(r"^(#[A-Za-z0-9_-]+|[CGD][A-Z0-9]{8,})$")


def _local(tag: str) -> str:
    return tag.split("}")[-1]


def _text(parent: ET.Element, name: str) -> str:
    for el in parent:
        if _local(el.tag) == name:
            return (el.text or "").strip()
    return ""


def _children(parent: ET.Element, name: str) -> list[ET.Element]:
    return [el for el in parent if _local(el.tag) == name]


def _targets(node: ET.Element) -> list[str]:
    out: list[str] = []
    for el in node.iter():
        if _local(el.tag) == "targetReference" and el.text:
            out.append(el.text.strip())
    return out


def _flow_name(path: Path) -> str:
    for sfx in SUFFIXES:
        if path.name.endswith(sfx):
            return path.name[: -len(sfx)]
    return path.stem


def load_flows(root: Path) -> tuple[dict[str, ET.Element], list[tuple[str, str, str]]]:
    flows: dict[str, ET.Element] = {}
    errors: list[tuple[str, str, str]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file() and p.name.endswith(SUFFIXES)):
        try:
            flows[str(path)] = ET.parse(path).getroot()
        except ET.ParseError as exc:
            errors.append(("ERROR", str(path), f"XML does not parse: {exc}"))
    return flows, errors


def check(root: Path) -> list[tuple[str, str, str]]:
    flows, findings = load_flows(root)
    by_name = {_flow_name(Path(p)): r for p, r in flows.items()}
    for path, flow in flows.items():
        start = next((el for el in flow if _local(el.tag) == "start"), None)
        trigger = _text(start, "triggerType") if start is not None else ""
        nodes = {_text(el, "name"): el for el in flow if _text(el, "name")}
        async_reach: set[str] = set()
        if start is not None:
            frontier = []
            for sp in _children(start, "scheduledPaths"):
                if _text(sp, "pathType") == "AsyncAfterCommit":
                    frontier.extend(_targets(sp))
            while frontier:
                name = frontier.pop()
                if name in async_reach or name not in nodes:
                    continue
                async_reach.add(name)
                frontier.extend(_targets(nodes[name]))
        for action in _children(flow, "actionCalls"):
            atype = _text(action, "actionType")
            if not atype.startswith("slack"):
                continue
            name = _text(action, "name")
            where = f"{path} [{name}]"
            if trigger == "RecordBeforeSave":
                findings.append(("HIGH", where, f"{atype} in a before-save flow; move it to an after-save async path"))
            if not _children(action, "faultConnector"):
                findings.append(("HIGH", where, f"{atype} has no faultConnector; failures will go unnoticed"))
            if trigger == "RecordAfterSave" and name not in async_reach:
                findings.append(("REVIEW", where, f"{atype} is not on an AsyncAfterCommit path"))
            for param in _children(action, "inputParameters"):
                pname = _text(param, "name")
                value = param.find("{*}value") if param.find("{*}value") is not None else param.find("value")
                literal = _text(value, "stringValue") if value is not None else ""
                if not literal:
                    continue
                if atype == "slackCreateChannel" and "name" in pname.lower() and not CHANNEL_NAME_RE.match(literal):
                    findings.append(("MEDIUM", where, f"channel name '{literal}' breaks Slack rules (lowercase, digits, hyphen, underscore, <=80)"))
                if LITERAL_CHANNEL_RE.match(literal):
                    findings.append(("REVIEW", where, f"literal channel '{literal}' in input '{pname}'; read it from configuration"))
                if atype == "slackSendMessageToLaunchFlow" and literal in by_name:
                    target = by_name[literal]
                    envs = [(_t.text or "").strip() for _t in target if _local(_t.tag) == "environments"]
                    if _text(target, "processType") != "Flow" or "Slack" not in envs:
                        findings.append(("HIGH", where, f"launch target '{literal}' must be a screen flow saved with the Slack environment"))
    return findings


def _self_test() -> int:
    fixtures = Path(__file__).resolve().parent / "fixtures"
    good = check(fixtures / "good")
    bad = check(fixtures / "bad")
    empty = check(fixtures / "empty")
    ok = True
    if any(s in ("ERROR", "HIGH", "MEDIUM") for s, _, _ in good):
        ok = False
        print(f"SELF-TEST FAIL good: {good}")
    wanted = ["before-save flow", "no faultConnector", "launch target", "breaks Slack rules"]
    seen = " | ".join(m for _, _, m in bad)
    missing = [w for w in wanted if w not in seen]
    if missing:
        ok = False
        print(f"SELF-TEST FAIL bad: missing {missing}; got {bad}")
    if empty:
        ok = False
        print(f"SELF-TEST FAIL empty: {empty}")
    print("SELF-TEST PASS" if ok else "SELF-TEST FAILED")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Flow metadata for Slack core action problems.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata (default: .)")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on MEDIUM and REVIEW findings too.")
    parser.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = parser.parse_args()
    if args.self_test:
        return _self_test()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    if not any(p.name.endswith(SUFFIXES) for p in root.rglob("*") if p.is_file()):
        print(f"WARN: no flow metadata found under {root}")
        return 0
    findings = check(root)
    for severity, where, message in findings:
        print(f"{severity}: {where}: {message}")
    if not findings:
        print("OK: no Slack action issues found")
    blocking = {"ERROR", "HIGH"} | ({"MEDIUM", "REVIEW"} if args.strict else set())
    return 1 if any(s in blocking for s, _, _ in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
