#!/usr/bin/env python3
"""Checker script for Transaction Security Policies skill.

Validates Salesforce metadata for Transaction Security Policy configuration issues.
Parses TransactionSecurityPolicy XML files for common anti-patterns described
in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_transaction_security.py [--help]
    python3 check_transaction_security.py --manifest-dir path/to/metadata
    python3 check_transaction_security.py --manifest-dir force-app/main/default

Checks performed:
  1. TransactionSecurityPolicy files — reads <eventName> (Real-Time Event Monitoring) and
     warns on event names that do not support policies; <eventType>/<resourceName> are
     Legacy Transaction Security fields (retired Summer '20) and are only reported
  2. TransactionSecurityPolicy files — flags policies that are in Monitor (inactive) mode
  3. TransactionSecurityPolicy files — flags Apex policies (<type>CustomApexPolicy</type>)
     with no <apexClass> (required for Apex-based policies)
  4. TransactionSecurityPolicy files — flags a blocking action with no top-level
     <blockMessage> on events that support one (ApiEvent, ListViewEvent,
     BulkApiResultEventStore, ReportEvent)
  5. General — warns if no TransactionSecurityPolicy metadata is found at all

Field reference: api_meta TransactionSecurityPolicy. <executionUser> is Legacy
Transaction Security only, so its absence is not flagged.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Event type classification
# ---------------------------------------------------------------------------

# RTEM event types confirmed to support Transaction Security Policy enforcement.
# Source: Salesforce Platform Events Developer Guide —
#   "Can Be Used in a Transaction Security Policy?" column
POLICY_SUPPORTED_EVENTS: frozenset[str] = frozenset(
    {
        # Valid <eventName> values per the Metadata API TransactionSecurityPolicy type.
        "AdminSetupEvent",
        "ApiAnomalyEventStore",
        "ApiEvent",
        "BulkApiResultEventStore",
        "CredentialStuffingEventStore",
        "FileEventStore",
        "GuestUserAnomalyEventStore",
        "LoginAnomalyEventStore",
        "PermissionSetEventStore",
        "ReportAnomalyEventStore",
        "SessionHijackingEventStore",
        "UniversalAnomalyEventStore",
        "ApiAnomalyEvent",
        "ApiEventStream",
        "BulkApiResultEvent",
        "ConnectedApplication",
        "CredentialStuffingEvent",
        "FileEvent",
        "GuestUserAnomalyEvent",
        "ListViewEvent",
        "ListViewEventStream",
        "LoginAnomalyEvent",
        "LoginAsEvent",
        "LoginAsEventStream",
        "LoginEvent",
        "LoginEventStream",
        "LogoutEvent",
        "LogoutEventStream",
        "PermissionSetEvent",
        "ReportAnomalyEvent",
        "ReportEvent",
        "ReportEventStream",
        "SessionHijackingEvent",
        "UriEventStream",
    }
)

# RTEM event types explicitly confirmed NOT to support Transaction Security Policies.
# Policies on these event types silently never evaluate.
POLICY_UNSUPPORTED_EVENTS: frozenset[str] = frozenset(
    {
        "ConcurLongRunApexErrEvent",
        "IdentityProviderEvent",
        "IdentityVerificationEvent",
        "MobileEmailEvent",
        "MobileEnforcedPolicyEvent",
        "MobileScreenshotEvent",
        "MobileTelephonyEvent",
    }
)


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------


def _extract_xml_value(content: str, tag: str) -> str | None:
    """Extract the text content of the first occurrence of a simple XML element.

    Returns None if the tag is not found.
    """
    pattern = rf"<{re.escape(tag)}\s*>(.*?)</{re.escape(tag)}>"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def _extract_all_xml_values(content: str, tag: str) -> list[str]:
    """Extract the text content of all occurrences of a simple XML element."""
    pattern = rf"<{re.escape(tag)}\s*>(.*?)</{re.escape(tag)}>"
    return [m.group(1).strip() for m in re.finditer(pattern, content, re.DOTALL)]


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_event_type_support(path: Path, content: str) -> list[str]:
    """Flag policies whose event name does not support enforcement.

    Real-Time Event Monitoring policies name the event in <eventName>. <eventType>
    belongs to Legacy Transaction Security, a retired feature since Summer '20.
    """
    issues: list[str] = []
    event_name = _extract_xml_value(content, "eventName")

    if event_name is None:
        legacy = _extract_xml_value(content, "eventType")
        if legacy is not None:
            issues.append(
                f"WARN {path.name}: policy sets <eventType>{legacy}</eventType> but no "
                "<eventName>. eventType is Legacy Transaction Security only (retired in "
                "Summer '20); a Real-Time Event Monitoring policy names its event in "
                "<eventName> (e.g. LoginEvent, ReportEvent)."
            )
        else:
            issues.append(
                f"WARN {path.name}: TransactionSecurityPolicy is missing an <eventName> "
                "element. Real-Time Event Monitoring policies name the event they monitor."
            )
        return issues

    event_type = event_name

    if event_type in POLICY_UNSUPPORTED_EVENTS:
        issues.append(
            f"HIGH {path.name}: eventName='{event_type}' does NOT support Transaction Security "
            "Policy enforcement. This policy will silently never fire regardless of its Active "
            "flag or condition logic. Remove or retype this policy against a supported event. "
            f"Supported events include: {', '.join(sorted(POLICY_SUPPORTED_EVENTS)[:6])}..."
        )
    elif event_type not in POLICY_SUPPORTED_EVENTS:
        issues.append(
            f"WARN {path.name}: eventName='{event_type}' is not in the confirmed "
            "policy-supported event list. Verify it is a valid TransactionSecurityEventName "
            "value in the Metadata API Developer Guide before deploying."
        )

    return issues


def check_active_flag(path: Path, content: str) -> list[str]:
    """Warn on policies that are inactive (Monitor mode only)."""
    issues: list[str] = []
    active = _extract_xml_value(content, "active")

    if active is None:
        issues.append(
            f"WARN {path.name}: TransactionSecurityPolicy is missing <active> element. "
            "The policy may default to inactive (Monitor mode). Explicitly set <active>true</active> "
            "to enable enforcement, or <active>false</active> for Monitor mode."
        )
    elif active.lower() == "false":
        issues.append(
            f"INFO {path.name}: Policy is in Monitor mode (<active>false</active>). "
            "No enforcement actions will fire. This is expected during validation; "
            "switch to <active>true</active> to enable enforcement."
        )

    return issues


# Events for which <blockMessage> is available (api_meta TransactionSecurityPolicy).
_BLOCK_MESSAGE_EVENTS = frozenset(
    {"ApiEvent", "ListViewEvent", "BulkApiResultEventStore", "ReportEvent"}
)


def check_block_action_message(path: Path, content: str) -> list[str]:
    """Warn on blocking policies that have no custom block message configured.

    The block flag lives in <action><block>true</block></action>; <blockMessage> is a
    top-level element of the policy, available only for the events listed above.
    """
    issues: list[str] = []
    event_name = _extract_xml_value(content, "eventName")
    if event_name not in _BLOCK_MESSAGE_EVENTS:
        return issues

    for action_block in re.findall(r"<action>(.*?)</action>", content, re.DOTALL):
        block = _extract_xml_value(action_block, "block")
        if block is not None and block.lower() == "true":
            block_message = _extract_xml_value(content, "blockMessage")
            if block_message is None or block_message.strip() == "":
                issues.append(
                    f"WARN {path.name}: Policy blocks {event_name} but no <blockMessage> is "
                    "configured. Users who are blocked will see the default message "
                    "rather than an actionable one. Add a <blockMessage> (max 1000 "
                    "characters) that explains the restriction and how to seek assistance."
                )
            break  # Only report once per policy

    return issues


def check_apex_policy_flag(path: Path, content: str) -> list[str]:
    """Flag Apex-based policies (type CustomApexPolicy) that name no apexClass."""
    issues: list[str] = []
    policy_type = _extract_xml_value(content, "type")
    apex_class = _extract_xml_value(content, "apexClass")

    if policy_type == "CustomApexPolicy" and (apex_class is None or apex_class == ""):
        issues.append(
            f"HIGH {path.name}: Policy is <type>CustomApexPolicy</type> but has no "
            "<apexClass>. apexClass (a class implementing TxnSecurity.PolicyCondition or "
            "TxnSecurity.EventCondition) is required for Apex-based policies."
        )

    return issues


# ---------------------------------------------------------------------------
# Directory-level check
# ---------------------------------------------------------------------------


def check_for_any_policies(manifest_dir: Path) -> list[str]:
    """Warn if no TransactionSecurityPolicy metadata is found in the manifest."""
    issues: list[str] = []
    policy_files = list(manifest_dir.rglob("*.transactionSecurityPolicy"))

    if not policy_files:
        issues.append(
            "INFO: No TransactionSecurityPolicy metadata found "
            f"(searched '{manifest_dir}' recursively for *.transactionSecurityPolicy). "
            "If this org uses Transaction Security, retrieve the metadata with: "
            "sf project retrieve start -m TransactionSecurityPolicy. "
            "Note: absence of policy metadata in source does not mean the org enforces "
            "no policy — eligible Event Monitoring and Shield orgs may carry a "
            "Salesforce-deployed default ReportEvent policy that no one authored "
            "(see references/gotchas.md Gotcha 6). Confirm against Setup, not source."
        )

    return issues


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------


def check_transaction_security(manifest_dir: Path) -> list[str]:
    """Run all Transaction Security Policy checks. Returns list of issue strings."""
    if not manifest_dir.exists():
        return [f"HIGH: Manifest directory not found: {manifest_dir}"]

    issues: list[str] = []
    policy_files = list(manifest_dir.rglob("*.transactionSecurityPolicy"))

    for path in policy_files:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"WARN {path.name}: could not read file — skipping.")
            continue

        issues.extend(check_event_type_support(path, content))
        issues.extend(check_active_flag(path, content))
        issues.extend(check_block_action_message(path, content))
        issues.extend(check_apex_policy_flag(path, content))

    issues.extend(check_for_any_policies(manifest_dir))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Transaction Security Policy configuration issues. "
            "Validates .transactionSecurityPolicy XML files against known anti-patterns "
            "including unsupported event names, Monitor-mode policies, Apex policies "
            "without an apexClass, and blocking policies without a block message."
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
    issues = check_transaction_security(manifest_dir)

    high_count = sum(1 for i in issues if i.startswith("HIGH"))
    warn_count = sum(1 for i in issues if i.startswith("WARN"))
    info_count = sum(1 for i in issues if i.startswith("INFO"))

    if not issues:
        print("No Transaction Security Policy issues found.")
        return 0

    for issue in issues:
        print(issue)

    print()
    print(
        f"Summary: {high_count} HIGH, {warn_count} WARN, {info_count} INFO "
        f"({len(issues)} total)"
    )

    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
