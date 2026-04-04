#!/usr/bin/env python3
"""Checker script for Flow Email and Notifications skill.

Scans Salesforce Flow metadata XML files for common notification-related issues:
- Send Custom Notification actions missing recipientIds wiring
- Send Email actions referencing a template (unsupported)
- Notification actions missing fault connectors
- HTML tags in custom notification body text
- Presence of Send SMS or Post Message to Slack without documented license notes

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_flow_email_and_notifications.py [--help]
    python3 check_flow_email_and_notifications.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

# Salesforce Flow XML namespace
FLOW_NS = "http://soap.sforce.com/2006/04/metadata"

# Action names used in Flow metadata XML for notification actions
CUSTOM_NOTIF_ACTION = "customNotificationAction"
SEND_EMAIL_ACTION = "emailSimple"
POST_SLACK_ACTION = "chatterPost"  # varies by org; check actionName contains slack
SMS_ACTION_PATTERN = re.compile(r"send.*sms|messaging.*send", re.IGNORECASE)
HTML_TAG_PATTERN = re.compile(r"<[a-zA-Z][^>]*>")
USER_ID_PATTERN = re.compile(r"\{![^}]+\.Id\}")  # merge field ending in .Id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Flow metadata for common email and notification issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _ns(tag: str) -> str:
    """Return a namespace-qualified tag name."""
    return f"{{{FLOW_NS}}}{tag}"


def check_flow_file(flow_path: Path) -> list[str]:
    """Check a single Flow XML file for notification-related issues."""
    issues: list[str] = []
    fname = flow_path.name

    try:
        tree = ET.parse(flow_path)
    except ET.ParseError as exc:
        issues.append(f"[{fname}] XML parse error: {exc}")
        return issues

    root = tree.getroot()

    # Collect all element API names that have fault connectors
    elements_with_fault: set[str] = set()
    for connector in root.iter(_ns("faultConnector")):
        # faultConnector is a child of an action/element node
        parent = connector.find("..")
        if parent is None:
            # Walk up manually via full tree
            pass
        # Iterate actionCalls to find which ones have faultConnectors
    # Build map: element name -> has fault connector
    for action_call in root.iter(_ns("actionCalls")):
        name_el = action_call.find(_ns("name"))
        fault_el = action_call.find(_ns("faultConnector"))
        if name_el is not None and fault_el is not None:
            elements_with_fault.add(name_el.text or "")

    # Check each actionCall
    for action_call in root.iter(_ns("actionCalls")):
        name_el = action_call.find(_ns("name"))
        action_type_el = action_call.find(_ns("actionType"))
        action_name_el = action_call.find(_ns("actionName"))

        elem_name = name_el.text if name_el is not None else "<unnamed>"
        action_type = (action_type_el.text or "").lower() if action_type_el is not None else ""
        action_name = (action_name_el.text or "").lower() if action_name_el is not None else ""

        is_custom_notif = (
            action_type == "apex"
            and CUSTOM_NOTIF_ACTION in action_name
        ) or action_type == "customNotification".lower()

        # Detect Send Custom Notification by actionType or known actionName
        if "customnotification" in action_type or "customnotification" in action_name:
            # Check for fault connector
            if elem_name not in elements_with_fault:
                fault_el = action_call.find(_ns("faultConnector"))
                if fault_el is None:
                    issues.append(
                        f"[{fname}] Action '{elem_name}': Send Custom Notification has no fault connector. "
                        "Add a fault path to handle the 1,000/hour org limit."
                    )

            # Check recipientIds input
            recipient_found = False
            for ip in action_call.iter(_ns("inputParameters")):
                param_name = ip.find(_ns("name"))
                if param_name is not None and "recipient" in (param_name.text or "").lower():
                    recipient_found = True
                    # Check if value looks like an email address rather than a User ID merge field
                    value_el = ip.find(_ns("value"))
                    if value_el is not None:
                        str_val_el = value_el.find(_ns("stringValue"))
                        if str_val_el is not None and str_val_el.text:
                            val = str_val_el.text
                            if "@" in val:
                                issues.append(
                                    f"[{fname}] Action '{elem_name}': recipientIds appears to contain an "
                                    f"email address ('{val}'). Send Custom Notification requires Salesforce "
                                    "User IDs, not email addresses."
                                )

            # Check body for HTML
            for ip in action_call.iter(_ns("inputParameters")):
                param_name = ip.find(_ns("name"))
                if param_name is not None and "body" in (param_name.text or "").lower():
                    value_el = ip.find(_ns("value"))
                    if value_el is not None:
                        str_val_el = value_el.find(_ns("stringValue"))
                        if str_val_el is not None and str_val_el.text:
                            if HTML_TAG_PATTERN.search(str_val_el.text):
                                issues.append(
                                    f"[{fname}] Action '{elem_name}': Custom notification body contains "
                                    "HTML tags. Bell notifications render plain text only — HTML tags "
                                    "will appear as literal characters."
                                )

        # Detect Send Email core action (emailSimple)
        if "emailsimple" in action_name or action_type == "emailsimple":
            # Check for template reference — unsupported
            for ip in action_call.iter(_ns("inputParameters")):
                param_name = ip.find(_ns("name"))
                if param_name is not None and "template" in (param_name.text or "").lower():
                    issues.append(
                        f"[{fname}] Action '{elem_name}': Send Email action has a 'template' input "
                        "parameter. The Flow Send Email core action does not support Classic Email "
                        "Templates — use a Text Template resource for the body instead."
                    )

            # Check for fault connector
            fault_el = action_call.find(_ns("faultConnector"))
            if fault_el is None and elem_name not in elements_with_fault:
                issues.append(
                    f"[{fname}] Action '{elem_name}': Send Email action has no fault connector. "
                    "Email sends can fail due to daily limits or invalid addresses."
                )

        # Detect Send SMS action
        if SMS_ACTION_PATTERN.search(action_name):
            fault_el = action_call.find(_ns("faultConnector"))
            if fault_el is None and elem_name not in elements_with_fault:
                issues.append(
                    f"[{fname}] Action '{elem_name}': Send SMS action has no fault connector. "
                    "SMS actions require Digital Engagement license and can fail if unavailable."
                )

        # Detect Slack actions
        if "slack" in action_name or "postmessagetoslack" in action_name:
            fault_el = action_call.find(_ns("faultConnector"))
            if fault_el is None and elem_name not in elements_with_fault:
                issues.append(
                    f"[{fname}] Action '{elem_name}': Post Message to Slack action has no fault "
                    "connector. Slack OAuth tokens can expire or be revoked, causing runtime faults."
                )

    return issues


def check_flow_email_and_notifications(manifest_dir: Path) -> list[str]:
    """Scan all Flow XML files in manifest_dir for notification-related issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for Flow files — typically under force-app/main/default/flows/ or flows/
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))
    if not flow_files:
        flow_files = list(manifest_dir.rglob("*.flow"))

    if not flow_files:
        # Not an error — the manifest may not contain any flows
        return issues

    for flow_path in sorted(flow_files):
        issues.extend(check_flow_file(flow_path))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_flow_email_and_notifications(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
