#!/usr/bin/env python3
"""Checker for the Custom Notification Types skill.

Scans a Salesforce DX metadata tree and reports, by severity:

ERROR
  - a `.notiftype` file with neither `desktop` nor `mobile` set to true
    (both are required booleans and both default to false, so such a type
    deploys cleanly and delivers to nobody)
  - a hard-coded `0ML...` Notification Type Id in Apex
  - `setTitle` / `setBody` string literals over the documented caps
    (250 / 750 characters)
  - `send()` on an unbounded Set<String> with no visible chunking

WARN
  - a Flow `customNotificationAction` whose `customNotifTypeId` input is a
    hard-coded 18-character Id (the Id is org-specific; resolve by
    DeveloperName at run time)

INFO
  - a `.notiftype` in the tree that no Flow or Apex class appears to
    reference (dead type, or the sender lives outside this tree)

Grounding for the rules:
  Metadata API Developer Guide, CustomNotificationType — suffix `.notiftype`,
  directory `notificationtypes`; `desktop` and `mobile` required booleans.
  Object Reference, CustomNotificationType — Desktop/Mobile default to false.
  Apex Reference Guide, CustomNotification — setTitle max 250, setBody max
  750, send(Set<String>) max 500 values.

Exit status: 1 if any ERROR was reported, otherwise 0. WARN and INFO are
informational and do not fail the run.

Usage:
    python3 check_custom_notification_types.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

MD_NS = "http://soap.sforce.com/2006/04/metadata"

# Documented caps (Apex Reference Guide, CustomNotification).
TITLE_MAX = 250
BODY_MAX = 750
RECIPIENT_MAX = 500

HARDCODED_TYPE_ID = re.compile(r"setNotificationTypeId\(\s*'0ML[A-Za-z0-9]{12,15}'")
SET_TITLE_LITERAL = re.compile(r"setTitle\(\s*'([^']{%d,})'" % (TITLE_MAX + 1))
SET_BODY_LITERAL = re.compile(r"setBody\(\s*'([^']{%d,})'" % (BODY_MAX + 1))
BARE_SEND = re.compile(r"\.send\(\s*new\s+Set<String>\s*\(\s*(\w+)\s*\)")
ID_LITERAL_18 = re.compile(r"^0ML[A-Za-z0-9]{15}$")


class Finding:
    """One reported problem, with a severity that decides the exit status."""

    def __init__(self, severity: str, where: str, message: str) -> None:
        self.severity = severity
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity}: {self.where}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Custom Notification Type metadata and its senders.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _ns(tag: str) -> str:
    return f"{{{MD_NS}}}{tag}"


def child_text(element: ET.Element, tag: str) -> str | None:
    """Return the stripped text of a direct child, or None.

    Written as an explicit `is not None` test on purpose: a leaf Element is
    falsy in ElementTree, so `element.find(a) or element.find(b)` silently
    discards a real match whose element has no children.
    """
    found = element.find(_ns(tag))
    if found is None:
        return None
    if found.text is None:
        return None
    return found.text.strip()


def first_child_text(element: ET.Element, *tags: str) -> str | None:
    """First non-empty child text among `tags`, or None. Never uses `or`."""
    for tag in tags:
        value = child_text(element, tag)
        if value is not None and value != "":
            return value
    return None


def is_true(value: str | None) -> bool:
    return value is not None and value.strip().lower() == "true"


# ---------------------------------------------------------------- notiftype


def check_notification_types(root: Path) -> tuple[list[Finding], dict[str, Path]]:
    """Check every `.notiftype` file. Returns findings and {apiName: path}."""
    findings: list[Finding] = []
    types: dict[str, Path] = {}

    for path in sorted(root.rglob("*.notiftype-meta.xml")) + sorted(
        root.rglob("*.notiftype")
    ):
        if path in types.values():
            continue
        try:
            tree = ET.parse(path)
        except (ET.ParseError, OSError) as exc:
            findings.append(Finding("ERROR", _rel(path, root), f"unparseable XML: {exc}"))
            continue

        element = tree.getroot()
        api_name = first_child_text(element, "customNotifTypeName", "fullName")
        if api_name is None:
            api_name = path.name.split(".")[0]
        types[api_name] = path

        desktop = is_true(child_text(element, "desktop"))
        mobile = is_true(child_text(element, "mobile"))
        if not desktop and not mobile:
            findings.append(
                Finding(
                    "ERROR",
                    _rel(path, root),
                    f"'{api_name}' has neither <desktop>true</desktop> nor "
                    "<mobile>true</mobile>; both are required booleans that default "
                    "to false, so this type deploys cleanly and delivers to nobody",
                )
            )

        label = child_text(element, "masterLabel")
        if label is not None and label == api_name:
            findings.append(
                Finding(
                    "WARN",
                    _rel(path, root),
                    f"<masterLabel> is identical to the API name '{api_name}'; the "
                    "label is customer-visible copy, the API name is not",
                )
            )

        if is_true(child_text(element, "slack")):
            findings.append(
                Finding(
                    "WARN",
                    _rel(path, root),
                    "<slack>true</slack> — the Metadata API documents this field as "
                    "'Reserved for future use'; it is not the Slack delivery switch",
                )
            )

    return findings, types


# --------------------------------------------------------------------- flows


def check_flows(root: Path) -> tuple[list[Finding], list[str]]:
    """Check Flow files that call customNotificationAction.

    Returns the findings plus the raw text of every sender file, which the
    caller searches for notification-type API names.
    """
    findings: list[Finding] = []
    sender_text: list[str] = []

    for path in sorted(root.rglob("*.flow-meta.xml")) + sorted(root.rglob("*.flow")):
        try:
            tree = ET.parse(path)
        except (ET.ParseError, OSError):
            continue

        raw = _read(path)
        for action in tree.getroot().findall(_ns("actionCalls")):
            action_type = child_text(action, "actionType")
            action_name = child_text(action, "actionName")
            if action_type != "customNotificationAction" and (
                action_name != "customNotificationAction"
            ):
                continue

            element_name = child_text(action, "name")
            if element_name is None:
                element_name = "(unnamed actionCall)"

            for param in action.findall(_ns("inputParameters")):
                param_name = child_text(param, "name")
                if param_name is None:
                    continue
                value = param.find(_ns("value"))
                if value is None:
                    continue
                literal = first_child_text(value, "stringValue", "elementReference")
                if literal is None:
                    continue
                if ID_LITERAL_18.match(literal):
                    findings.append(
                        Finding(
                            "WARN",
                            f"{_rel(path, root)}:{element_name}",
                            f"input '{param_name}' is the hard-coded Id '{literal}'; "
                            "CustomNotificationType Ids are org-specific — resolve by "
                            "DeveloperName with a Get Records at run time",
                        )
                    )

        if "customNotificationAction" in raw:
            sender_text.append(raw)

    return findings, sender_text


# --------------------------------------------------------------------- apex


def check_apex(root: Path) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    sender_text: list[str] = []

    for path in sorted(root.rglob("*.cls")) + sorted(root.rglob("*.trigger")):
        text = _read(path)
        if text == "":
            continue
        where = _rel(path, root)

        for match in HARDCODED_TYPE_ID.finditer(text):
            findings.append(
                Finding(
                    "ERROR",
                    f"{where}:{_line(text, match)}",
                    "hard-coded Notification Type Id; resolve by DeveloperName",
                )
            )

        for match in SET_TITLE_LITERAL.finditer(text):
            findings.append(
                Finding(
                    "ERROR",
                    f"{where}:{_line(text, match)}",
                    f"setTitle literal over {TITLE_MAX} chars "
                    f"({len(match.group(1))} chars)",
                )
            )

        for match in SET_BODY_LITERAL.finditer(text):
            findings.append(
                Finding(
                    "ERROR",
                    f"{where}:{_line(text, match)}",
                    f"setBody literal over {BODY_MAX} chars "
                    f"({len(match.group(1))} chars)",
                )
            )

        for match in BARE_SEND.finditer(text):
            var = match.group(1)
            guard = rf"{var}\.size\(\)\s*<=\s*{RECIPIENT_MAX}|{var}\.subList|chunk"
            if re.search(guard, text) is None:
                findings.append(
                    Finding(
                        "ERROR",
                        f"{where}:{_line(text, match)}",
                        f"send() without visible {RECIPIENT_MAX}-recipient chunking",
                    )
                )

        if "CustomNotification" in text:
            sender_text.append(text)

    return findings, sender_text


# ------------------------------------------------------------------- helpers


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _line(text: str, match: re.Match[str]) -> int:
    return text[: match.start()].count("\n") + 1


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    findings: list[Finding] = []

    type_findings, types = check_notification_types(root)
    findings.extend(type_findings)

    flow_findings, flow_senders = check_flows(root)
    findings.extend(flow_findings)

    apex_findings, apex_senders = check_apex(root)
    findings.extend(apex_findings)

    senders = flow_senders + apex_senders
    for api_name, path in sorted(types.items()):
        if not any(api_name in text for text in senders):
            findings.append(
                Finding(
                    "INFO",
                    _rel(path, root),
                    f"'{api_name}' is not referenced by any Flow or Apex class in "
                    "this tree — either it is unused, or its sender lives elsewhere",
                )
            )

    if not findings:
        print(
            f"OK: {len(types)} notification type(s) checked; no issues found.",
            file=sys.stdout,
        )
        return 0

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda f: (order[f.severity], f.where))

    errors = 0
    for finding in findings:
        stream = sys.stderr if finding.severity == "ERROR" else sys.stdout
        print(str(finding), file=stream)
        if finding.severity == "ERROR":
            errors += 1

    counts = {level: 0 for level in order}
    for finding in findings:
        counts[finding.severity] += 1
    print(
        f"\n{counts['ERROR']} error(s), {counts['WARN']} warning(s), "
        f"{counts['INFO']} info across {len(types)} notification type(s).",
        file=sys.stdout,
    )

    if errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
