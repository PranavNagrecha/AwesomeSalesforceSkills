#!/usr/bin/env python3
"""Checker script for Outbound Messages and Callbacks skill.

Inspects Salesforce metadata to detect common anti-patterns and misconfigurations
related to Outbound Messages. Uses stdlib only — no pip dependencies.

Checks performed:
  1. Detects WorkflowAlert XML files that configure Outbound Message actions and
     validates that the endpoint URL uses HTTPS (not HTTP).
  2. Detects Workflow Rules that reference Outbound Messages and warns if the
     Workflow Rule evaluation criteria is set to "alwaysTrue" — a common
     misconfiguration that fires on every save, not just qualifying changes.
  3. Detects Outbound Message definitions with no fields selected beyond the
     implicit Id field — likely under-configured.
  4. Warns if Outbound Message endpoint URLs contain non-production hostnames
     (localhost, staging, dev) that may have been accidentally promoted.
  5. Reports a count of active Workflow Rules referencing Outbound Messages
     to surface volume for operations planning.

Usage:
    python3 check_outbound_messages_and_callbacks.py [--help]
    python3 check_outbound_messages_and_callbacks.py --manifest-dir path/to/metadata
    python3 check_outbound_messages_and_callbacks.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce metadata namespace used in Workflow XML files
_WF_NS = "http://soap.sforce.com/2006/04/metadata"

# Non-production hostname patterns that should not appear in production endpoint URLs
_NON_PROD_HOSTNAME_PATTERNS = re.compile(
    r"(localhost|127\.0\.0\.1|staging|stage|dev\.|sandbox|test\.)",
    re.IGNORECASE,
)


def _find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find XML files matching a suffix pattern under root."""
    return list(root.rglob(f"*{suffix}"))


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def check_outbound_message_https(manifest_dir: Path) -> list[str]:
    """Check that all Outbound Message endpoint URLs use HTTPS."""
    issues: list[str] = []
    # Outbound Message definitions are stored as .outboundMessage or inside
    # Workflow XML files (.workflow-meta.xml) depending on API version.
    # Check both locations.
    wf_files = _find_xml_files(manifest_dir, ".workflow-meta.xml")
    om_files = _find_xml_files(manifest_dir, ".outboundMessage-meta.xml")

    for path in wf_files:
        root = _parse_xml_safe(path)
        if root is None:
            continue
        # Outbound message definitions are nested under <outboundMessages> in a workflow file
        for om in root.findall(f".//{{{_WF_NS}}}outboundMessages"):
            url_elem = om.find(f"{{{_WF_NS}}}endpointUrl")
            name_elem = om.find(f"{{{_WF_NS}}}name")
            if url_elem is not None and url_elem.text:
                url = url_elem.text.strip()
                name = name_elem.text.strip() if name_elem is not None and name_elem.text else path.name
                if url.startswith("http://"):
                    issues.append(
                        f"Outbound Message '{name}' in {path.name} uses HTTP endpoint URL "
                        f"'{url}' — Salesforce requires HTTPS. Change to https://."
                    )
                if _NON_PROD_HOSTNAME_PATTERNS.search(url):
                    issues.append(
                        f"Outbound Message '{name}' in {path.name} endpoint URL '{url}' "
                        f"appears to reference a non-production hostname. Verify this is "
                        f"intentional and not a misconfigured sandbox endpoint."
                    )

    for path in om_files:
        root = _parse_xml_safe(path)
        if root is None:
            continue
        url_elem = root.find(f"{{{_WF_NS}}}endpointUrl")
        if url_elem is not None and url_elem.text:
            url = url_elem.text.strip()
            if url.startswith("http://"):
                issues.append(
                    f"Outbound Message metadata '{path.name}' uses HTTP endpoint URL "
                    f"'{url}' — Salesforce requires HTTPS. Change to https://."
                )
            if _NON_PROD_HOSTNAME_PATTERNS.search(url):
                issues.append(
                    f"Outbound Message metadata '{path.name}' endpoint URL '{url}' "
                    f"appears to reference a non-production hostname."
                )

    return issues


def check_outbound_message_field_coverage(manifest_dir: Path) -> list[str]:
    """Check that Outbound Message definitions include at least one explicit field."""
    issues: list[str] = []
    wf_files = _find_xml_files(manifest_dir, ".workflow-meta.xml")

    for path in wf_files:
        root = _parse_xml_safe(path)
        if root is None:
            continue
        for om in root.findall(f".//{{{_WF_NS}}}outboundMessages"):
            name_elem = om.find(f"{{{_WF_NS}}}name")
            name = name_elem.text.strip() if name_elem is not None and name_elem.text else path.name
            fields = om.findall(f"{{{_WF_NS}}}fields")
            # The Id field is always implicit; if no additional fields are listed,
            # the external system receives only the record Id — likely under-configured.
            if len(fields) == 0:
                issues.append(
                    f"Outbound Message '{name}' in {path.name} has no fields selected "
                    f"beyond the implicit Id. The external endpoint will receive only the "
                    f"record Id. Add the fields the endpoint needs to process the notification."
                )

    return issues


def check_workflow_rule_trigger_type(manifest_dir: Path) -> list[str]:
    """Warn on Workflow Rules that fire on every evaluation (triggerType = alwaysTrue or onAllChanges)."""
    issues: list[str] = []
    wf_files = _find_xml_files(manifest_dir, ".workflow-meta.xml")
    # Trigger types that fire on every record save (not just qualifying changes)
    # can cause unexpected Outbound Message volume.
    high_volume_trigger_types = {"alwaysTrue", "onAllChanges"}

    for path in wf_files:
        root = _parse_xml_safe(path)
        if root is None:
            continue
        for rule in root.findall(f".//{{{_WF_NS}}}rules"):
            name_elem = rule.find(f"{{{_WF_NS}}}fullName")
            rule_name = name_elem.text.strip() if name_elem is not None and name_elem.text else path.name
            active_elem = rule.find(f"{{{_WF_NS}}}active")
            if active_elem is not None and active_elem.text == "false":
                continue  # skip inactive rules
            trigger_elem = rule.find(f"{{{_WF_NS}}}triggerType")
            if trigger_elem is not None and trigger_elem.text in high_volume_trigger_types:
                # Check if this rule has any Outbound Message actions
                actions = rule.findall(f"{{{_WF_NS}}}actions")
                for action in actions:
                    action_type = action.find(f"{{{_WF_NS}}}type")
                    if action_type is not None and action_type.text == "OutboundMessage":
                        issues.append(
                            f"Workflow Rule '{rule_name}' in {path.name} has triggerType "
                            f"'{trigger_elem.text}' and sends an Outbound Message. This fires "
                            f"on every qualifying record save — confirm high-volume delivery is "
                            f"acceptable and the external endpoint is idempotent."
                        )

    return issues


def summarize_outbound_message_count(manifest_dir: Path) -> list[str]:
    """Report the count of active Workflow Rules referencing Outbound Messages."""
    info: list[str] = []
    wf_files = _find_xml_files(manifest_dir, ".workflow-meta.xml")
    om_count = 0
    active_rule_count = 0

    for path in wf_files:
        root = _parse_xml_safe(path)
        if root is None:
            continue
        # Count Outbound Message definitions
        om_count += len(root.findall(f".//{{{_WF_NS}}}outboundMessages"))
        # Count active rules with Outbound Message actions
        for rule in root.findall(f".//{{{_WF_NS}}}rules"):
            active_elem = rule.find(f"{{{_WF_NS}}}active")
            if active_elem is not None and active_elem.text != "true":
                continue
            for action in rule.findall(f"{{{_WF_NS}}}actions"):
                action_type = action.find(f"{{{_WF_NS}}}type")
                if action_type is not None and action_type.text == "OutboundMessage":
                    active_rule_count += 1
                    break

    if om_count > 0:
        info.append(
            f"INFO: Found {om_count} Outbound Message definition(s) and "
            f"{active_rule_count} active Workflow Rule(s) referencing them."
        )
    return info


def check_outbound_messages_and_callbacks(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    wf_files = _find_xml_files(manifest_dir, ".workflow-meta.xml")
    om_files = _find_xml_files(manifest_dir, ".outboundMessage-meta.xml")

    if not wf_files and not om_files:
        # No Outbound Message metadata found — nothing to check
        return issues

    issues.extend(check_outbound_message_https(manifest_dir))
    issues.extend(check_outbound_message_field_coverage(manifest_dir))
    issues.extend(check_workflow_rule_trigger_type(manifest_dir))
    # Append informational count (not an issue, but useful for operations review)
    issues.extend(summarize_outbound_message_count(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Outbound Messages and Callbacks "
            "configuration issues: HTTPS enforcement, field coverage, trigger "
            "type volume risk, and non-production endpoint URLs."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_outbound_messages_and_callbacks(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    exit_code = 0
    for issue in issues:
        if issue.startswith("INFO:"):
            print(issue)
        else:
            print(f"ISSUE: {issue}")
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
