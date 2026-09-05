#!/usr/bin/env python3
"""Static checks for Workflow Outbound Message metadata.

Parses every ``workflows/*.workflow`` (and DX ``*.workflow-meta.xml``) file under a
metadata root and checks the ``outboundMessages`` entries and the ``rules`` actions
that reference them.

Grounding for every rule below is the Metadata API Developer Guide (v62 PDF,
https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf):

  * ``Workflow`` file suffix and ``workflows`` directory ......... L139896-139898
  * ``Workflow.outboundMessages`` / ``Workflow.rules`` ........... L139931, L139937
  * ``WorkflowActionReference`` ``name`` + ``type`` enum ......... L139952-139966
  * ``WorkflowOutboundMessage`` field table ...................... L140312-140371
      - ``apiVersion``  Required; valid values 8.0 and 18.0 or later   L140327-140340
      - ``endpointUrl`` Required                                       L140344
      - ``fields``      named references to the fields to be sent      L140346
      - ``includeSessionId`` Required; includes the session ID         L140354-140357
      - ``integrationUser`` Required                                   L140359
      - ``useDeadLetterQueue`` org-permission gated                    L140368-140371

ERRORs are deploy-or-delivery breaking. WARNs are decisions that should be
deliberate rather than inherited. Exit status is 1 when any ERROR is found.

stdlib only.

Usage:
    python3 check_outbound_message_setup.py --manifest-dir force-app/main/default
    python3 check_outbound_message_setup.py --manifest-dir force-app/main/default --strict
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "http://soap.sforce.com/2006/04/metadata"

# api_meta.txt L140329: "Valid API versions for outbound messages are 8.0 and 18.0 or later."
LEGAL_LEGACY_API_VERSION = 8.0
MIN_MODERN_API_VERSION = 18.0

# api_meta.txt L139961: OutboundMessage is one value of the WorkflowActionType enum.
OUTBOUND_ACTION_TYPE = "OutboundMessage"


class Finding:
    """One check result. ``level`` is 'ERROR' or 'WARN'."""

    def __init__(self, level: str, where: str, message: str) -> None:
        self.level = level
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.level}: {self.where}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Workflow Outbound Message metadata for deploy-breaking and "
            "delivery-breaking configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Metadata root containing a 'workflows' directory "
            "(e.g. force-app/main/default). Default: current directory."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN findings as well as ERROR findings.",
    )
    return parser.parse_args()


def _local(tag: str) -> str:
    """Strip the ``{namespace}`` prefix ElementTree puts on every tag."""
    return tag.split("}", 1)[1] if tag.startswith("{") else tag


def _child(parent: ET.Element, tag: str) -> ET.Element | None:
    """Return the first direct child with local name ``tag``, else None.

    Deliberately explicit about ``is not None``. A leaf Element is falsy in
    ElementTree, so ``parent.find(a) or parent.find(b)`` silently discards a real
    element that happens to have no children -- which is every element in this file.
    """
    for child in parent:
        if _local(child.tag) == tag:
            return child
    return None


def _text(parent: ET.Element, tag: str) -> str | None:
    """Return the stripped text of the first ``tag`` child, or None if absent/empty."""
    element = _child(parent, tag)
    if element is None:
        return None
    if element.text is None:
        return None
    stripped = element.text.strip()
    return stripped or None


def _texts(parent: ET.Element, tag: str) -> list[str]:
    """Return the stripped text of every ``tag`` child that has any."""
    values = []
    for child in parent:
        if _local(child.tag) == tag and child.text is not None:
            stripped = child.text.strip()
            if stripped:
                values.append(stripped)
    return values


def _children(parent: ET.Element, tag: str) -> list[ET.Element]:
    return [child for child in parent if _local(child.tag) == tag]


def workflow_files(manifest_dir: Path) -> list[Path]:
    """Every workflow file under the metadata root, MDAPI and DX forms alike."""
    found: set[Path] = set()
    for pattern in ("workflows/*.workflow", "workflows/*.workflow-meta.xml"):
        found.update(manifest_dir.glob(pattern))
    # Tolerate a manifest-dir pointed straight at the workflows folder.
    if manifest_dir.name == "workflows":
        found.update(manifest_dir.glob("*.workflow"))
        found.update(manifest_dir.glob("*.workflow-meta.xml"))
    return sorted(found)


def check_outbound_message(
    element: ET.Element, where: str
) -> tuple[str | None, list[Finding]]:
    """Check one ``<outboundMessages>`` entry. Returns (fullName, findings)."""
    findings: list[Finding] = []

    full_name = _text(element, "fullName")
    label = full_name or _text(element, "name") or "<unnamed>"
    site = f"{where} outboundMessages[{label}]"

    if full_name is None:
        findings.append(
            Finding(
                "ERROR",
                site,
                "No <fullName>. It is the developer name every rule and approval "
                "action resolves against (api_meta.txt L140348-140352); without it "
                "nothing can reference this message.",
            )
        )

    # --- endpointUrl: Required (L140344). HTTPS is the only safe transport for a
    # payload that may carry a session ID (see includeSessionId below).
    endpoint = _text(element, "endpointUrl")
    if endpoint is None:
        findings.append(
            Finding(
                "ERROR",
                site,
                "No <endpointUrl>. The field is Required (api_meta.txt L140344).",
            )
        )
    elif not endpoint.lower().startswith("https://"):
        findings.append(
            Finding(
                "ERROR",
                site,
                f"<endpointUrl> is not HTTPS: {endpoint!r}. The payload carries record "
                "data and, when includeSessionId is true, a live session for the "
                "integration user (L140354-140357). The guide's own sample uses "
                "http://www.test.com (L140626) as a placeholder, not a pattern.",
            )
        )
    elif "localhost" in endpoint or "127.0.0.1" in endpoint:
        findings.append(
            Finding(
                "WARN",
                site,
                f"<endpointUrl> points at a loopback address: {endpoint!r}. Salesforce "
                "cannot reach it from any org. Likely a local-development value "
                "committed by accident.",
            )
        )

    # --- fields: "the named references to the fields to be sent" (L140346). Not
    # marked Required, so an empty list deploys clean.
    fields = _texts(element, "fields")
    if not fields:
        findings.append(
            Finding(
                "ERROR",
                site,
                "No <fields> elements. The element is not marked Required in the guide "
                "(api_meta.txt L140346), so this deploys clean and sends a payload the "
                "listener cannot correlate. List every field the listener parses.",
            )
        )
    elif "Id" not in fields:
        findings.append(
            Finding(
                "ERROR",
                site,
                f"<fields> does not include Id (has: {', '.join(fields)}). Id is the "
                "correlation key the listener needs to make delivery idempotent; "
                "nothing in the metadata guarantees it is sent otherwise.",
            )
        )

    # --- integrationUser: Required (L140359).
    if _text(element, "integrationUser") is None:
        findings.append(
            Finding(
                "ERROR",
                site,
                "No <integrationUser>. The field is Required -- 'the named reference to "
                "the user under which this message is sent' (api_meta.txt L140359).",
            )
        )

    # --- apiVersion: Required, valid values 8.0 and 18.0 or later (L140327-140340).
    api_version = _text(element, "apiVersion")
    if api_version is None:
        findings.append(
            Finding(
                "ERROR",
                site,
                "No <apiVersion>. The field is Required (api_meta.txt L140327) and "
                "cannot be set through the Salesforce UI (L140332-140334), so an "
                "omitted value means the org, not this file, decides which WSDL the "
                "listener must consume.",
            )
        )
    else:
        try:
            value = float(api_version)
        except ValueError:
            findings.append(
                Finding(
                    "ERROR",
                    site,
                    f"<apiVersion> is not numeric: {api_version!r}. The field type is "
                    "double (api_meta.txt L140327).",
                )
            )
        else:
            if value != LEGAL_LEGACY_API_VERSION and value < MIN_MODERN_API_VERSION:
                findings.append(
                    Finding(
                        "ERROR",
                        site,
                        f"<apiVersion> {api_version} is not a legal outbound message "
                        "version. 'Valid API versions for outbound messages are 8.0 and "
                        "18.0 or later' (api_meta.txt L140329).",
                    )
                )

    # --- includeSessionId: Required (L140354-140357). True is a decision, not a default.
    include_session = _text(element, "includeSessionId")
    if include_session is None:
        findings.append(
            Finding(
                "ERROR",
                site,
                "No <includeSessionId>. The field is Required (api_meta.txt L140354).",
            )
        )
    elif include_session.lower() == "true":
        findings.append(
            Finding(
                "WARN",
                site,
                "<includeSessionId> is true: the payload carries a live Salesforce "
                "session for the integration user (api_meta.txt L140354-140357). Keep it "
                "only if the listener genuinely calls back, and scope the integration "
                "user to exactly what that callback does.",
            )
        )

    # --- useDeadLetterQueue: org-permission gated (L140368-140371).
    if _child(element, "useDeadLetterQueue") is None:
        findings.append(
            Finding(
                "WARN",
                site,
                "No <useDeadLetterQueue>. Undelivered messages have no landing place. "
                "The element only works in orgs with dead letter queue permissions "
                "turned on (api_meta.txt L140368-140371) -- either set it, or record "
                "the reconciliation plan that replaces it.",
            )
        )

    return full_name, findings


def check_rule_actions(
    root: ET.Element, declared: set[str], where: str
) -> list[Finding]:
    """Every rule action of type OutboundMessage must name a message in this file."""
    findings: list[Finding] = []

    for rule in _children(root, "rules"):
        rule_name = _text(rule, "fullName") or "<unnamed rule>"

        action_holders = [rule]
        # Time-based actions live one level deeper (api_meta.txt L140524-140530).
        action_holders.extend(_children(rule, "workflowTimeTriggers"))

        for holder in action_holders:
            for action in _children(holder, "actions"):
                action_type = _text(action, "type")
                if action_type != OUTBOUND_ACTION_TYPE:
                    continue
                action_name = _text(action, "name")
                if action_name is None:
                    findings.append(
                        Finding(
                            "ERROR",
                            f"{where} rules[{rule_name}]",
                            "An action of type OutboundMessage has no <name>. Both name "
                            "and type are Required on WorkflowActionReference "
                            "(api_meta.txt L139952-139958).",
                        )
                    )
                    continue
                if action_name not in declared:
                    known = ", ".join(sorted(declared)) or "(none in this file)"
                    findings.append(
                        Finding(
                            "ERROR",
                            f"{where} rules[{rule_name}]",
                            f"Action names outbound message {action_name!r}, which is "
                            "not declared in this file's <outboundMessages>. The "
                            "reference resolves against fullName, not the display "
                            f"name. Declared here: {known}.",
                        )
                    )

    return findings


def check_workflow_file(path: Path) -> list[Finding]:
    where = path.name
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [
            Finding(
                "ERROR",
                where,
                f"Not well-formed XML: {exc}. Note the Metadata API guide's own Workflow "
                "sample contains a mismatched tag (<fullName>...</name>, "
                "api_meta.txt L140666-140669) -- do not scaffold from it.",
            )
        ]
    except OSError as exc:
        return [Finding("ERROR", where, f"Cannot read file: {exc}")]

    findings: list[Finding] = []
    declared: set[str] = set()

    messages = _children(root, "outboundMessages")
    for message in messages:
        full_name, message_findings = check_outbound_message(message, where)
        findings.extend(message_findings)
        if full_name is not None:
            if full_name in declared:
                findings.append(
                    Finding(
                        "ERROR",
                        f"{where} outboundMessages[{full_name}]",
                        "Duplicate <fullName>. fullName 'must be unique' within the "
                        "component (api_meta.txt L140348-140350).",
                    )
                )
            declared.add(full_name)

    findings.extend(check_rule_actions(root, declared, where))
    return findings


def check_outbound_message_setup(manifest_dir: Path) -> tuple[list[Finding], int]:
    """Return (findings, number of workflow files scanned)."""
    if not manifest_dir.exists():
        return (
            [Finding("ERROR", str(manifest_dir), "Manifest directory not found.")],
            0,
        )

    files = workflow_files(manifest_dir)
    findings: list[Finding] = []
    for path in files:
        findings.extend(check_workflow_file(path))
    return findings, len(files)


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    findings, scanned = check_outbound_message_setup(manifest_dir)

    errors = [f for f in findings if f.level == "ERROR"]
    warns = [f for f in findings if f.level == "WARN"]

    if scanned == 0:
        print(
            f"No workflow files found under {manifest_dir}/workflows "
            "(expected *.workflow or *.workflow-meta.xml)."
        )

    for finding in findings:
        print(str(finding), file=sys.stderr)

    print(
        f"Scanned {scanned} workflow file(s): {len(errors)} error(s), "
        f"{len(warns)} warning(s)."
    )

    if errors:
        return 1
    if warns and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    if main() != 0:
        sys.exit(1)
    sys.exit(0)
