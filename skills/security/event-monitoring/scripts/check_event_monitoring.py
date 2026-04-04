#!/usr/bin/env python3
"""Checker script for Event Monitoring skill.

Validates Salesforce metadata for Event Monitoring configuration issues.
Checks PlatformEventChannel and PlatformEventChannelMember metadata files
for common anti-patterns described in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_event_monitoring.py [--help]
    python3 check_event_monitoring.py --manifest-dir path/to/metadata
    python3 check_event_monitoring.py --manifest-dir force-app/main/default

Checks performed:
  1. PlatformEventChannel files — confirms eventType=monitoring for RTEM channels
  2. PlatformEventChannelMember files — confirms selectedEntity is a valid RTEM event type
  3. TransactionSecurityPolicy files — warns on event types that do not support policies
  4. General — warns if no Event Monitoring metadata found at all
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# RTEM event types that can be used in Transaction Security Policies
# Source: Platform Events Developer Guide — "Can Be Used in a Transaction Security Policy?" table
POLICY_SUPPORTED_EVENTS: frozenset[str] = frozenset(
    {
        "ApiAnomalyEvent",
        "ApiEventStream",
        "BulkApiResultEvent",
        "CredentialStuffingEvent",
        "FileEvent",
        "GuestUserAnomalyEvent",
        "LoginAnomalyEvent",
        "LoginAsEvent",
        "LoginAsEventStream",
        "LoginEvent",
        "LoginEventStream",
        "LogoutEvent",
        "LogoutEventStream",
        "PermissionSetEvent",
        "ReportAnomalyEvent",
        "ReportEventStream",
        "SessionHijackingEvent",
        "UriEventStream",
    }
)

# RTEM event types confirmed not to support Transaction Security Policies
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

# All known RTEM event types (platform events, not EventLogFile types)
KNOWN_RTEM_EVENTS: frozenset[str] = POLICY_SUPPORTED_EVENTS | POLICY_UNSUPPORTED_EVENTS | frozenset(
    {
        "ApiEventStream",
        "BulkApiResultEvent",
        "LightningUriEventStream",
        "ListViewEventStream",
    }
)


def _extract_xml_value(content: str, tag: str) -> str | None:
    """Extract the text value of a simple XML tag. Returns None if not found."""
    pattern = rf"<{re.escape(tag)}\s*>(.*?)</{re.escape(tag)}>"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def check_platform_event_channels(manifest_dir: Path) -> list[str]:
    """Check PlatformEventChannel metadata files for RTEM configuration issues."""
    issues: list[str] = []
    channel_files = list(manifest_dir.rglob("*.platformEventChannel"))

    for path in channel_files:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"WARN {path}: could not read file")
            continue

        channel_type = _extract_xml_value(content, "channelType")
        event_type = _extract_xml_value(content, "eventType")

        # A channel intended for RTEM must have channelType=event AND eventType=monitoring
        if channel_type == "event" and event_type != "monitoring":
            issues.append(
                f"HIGH {path.name}: PlatformEventChannel has channelType=event but "
                f"eventType='{event_type}' (expected 'monitoring' for Real-Time Event Monitoring). "
                "RTEM events will not be deliverable to this channel."
            )
        elif channel_type is None:
            issues.append(
                f"WARN {path.name}: PlatformEventChannel is missing <channelType> element."
            )

    return issues


def check_platform_event_channel_members(manifest_dir: Path) -> list[str]:
    """Check PlatformEventChannelMember files for valid RTEM event type selection."""
    issues: list[str] = []
    member_files = list(manifest_dir.rglob("*.platformEventChannelMember"))

    for path in member_files:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"WARN {path}: could not read file")
            continue

        selected_entity = _extract_xml_value(content, "selectedEntity")

        if selected_entity is None:
            issues.append(
                f"HIGH {path.name}: PlatformEventChannelMember is missing <selectedEntity>."
            )
            continue

        # Warn if the entity name looks like an EventLogFile type rather than an RTEM type
        # EventLogFile types are plain strings like 'Login', 'Report'; RTEM types end with 'Event'
        if not selected_entity.endswith("Event") and not selected_entity.endswith("Stream"):
            issues.append(
                f"WARN {path.name}: selectedEntity='{selected_entity}' does not look like an RTEM "
                "event type. RTEM event types end in 'Event' (e.g., LoginEvent, ApiAnomalyEvent). "
                "EventLogFile event types (e.g., 'Login', 'Report') are not valid channel members."
            )

    return issues


def check_transaction_security_policies(manifest_dir: Path) -> list[str]:
    """Check TransactionSecurityPolicy metadata for unsupported event types."""
    issues: list[str] = []
    policy_files = list(manifest_dir.rglob("*.transactionSecurityPolicy"))

    for path in policy_files:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            issues.append(f"WARN {path}: could not read file")
            continue

        # TransactionSecurityPolicy uses <eventType> to specify the monitored event
        event_type = _extract_xml_value(content, "eventType")

        if event_type is None:
            issues.append(
                f"WARN {path.name}: TransactionSecurityPolicy missing <eventType> element."
            )
            continue

        if event_type in POLICY_UNSUPPORTED_EVENTS:
            issues.append(
                f"HIGH {path.name}: TransactionSecurityPolicy uses eventType='{event_type}', "
                "which does NOT support Transaction Security policy enforcement. "
                "This policy will silently never fire. "
                f"Supported types include: {', '.join(sorted(POLICY_SUPPORTED_EVENTS)[:5])}..."
            )
        elif event_type not in POLICY_SUPPORTED_EVENTS and not event_type.startswith("__"):
            issues.append(
                f"WARN {path.name}: TransactionSecurityPolicy eventType='{event_type}' "
                "is not in the confirmed policy-supported event list. "
                "Verify this event type supports Transaction Security policy enforcement "
                "in the Salesforce Object Reference before deploying."
            )

    return issues


def check_for_any_monitoring_config(manifest_dir: Path) -> list[str]:
    """Warn if no Event Monitoring metadata is found at all."""
    issues: list[str] = []
    has_channels = bool(list(manifest_dir.rglob("*.platformEventChannel")))
    has_members = bool(list(manifest_dir.rglob("*.platformEventChannelMember")))
    has_policies = bool(list(manifest_dir.rglob("*.transactionSecurityPolicy")))

    if not has_channels and not has_members and not has_policies:
        issues.append(
            "INFO: No Event Monitoring metadata found (no .platformEventChannel, "
            ".platformEventChannelMember, or .transactionSecurityPolicy files). "
            "If this org uses Real-Time Event Monitoring or Transaction Security, "
            "add the metadata to this directory for validation."
        )

    return issues


def check_event_monitoring(manifest_dir: Path) -> list[str]:
    """Run all Event Monitoring checks. Returns list of issue strings."""
    if not manifest_dir.exists():
        return [f"HIGH: Manifest directory not found: {manifest_dir}"]

    issues: list[str] = []
    issues.extend(check_platform_event_channels(manifest_dir))
    issues.extend(check_platform_event_channel_members(manifest_dir))
    issues.extend(check_transaction_security_policies(manifest_dir))
    issues.extend(check_for_any_monitoring_config(manifest_dir))
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Event Monitoring configuration issues. "
            "Validates PlatformEventChannel, PlatformEventChannelMember, and "
            "TransactionSecurityPolicy files against known RTEM anti-patterns."
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
    issues = check_event_monitoring(manifest_dir)

    high_count = sum(1 for i in issues if i.startswith("HIGH"))
    warn_count = sum(1 for i in issues if i.startswith("WARN"))
    info_count = sum(1 for i in issues if i.startswith("INFO"))

    if not issues:
        print("No Event Monitoring issues found.")
        return 0

    for issue in issues:
        print(issue)

    print()
    print(
        f"Summary: {high_count} HIGH, {warn_count} WARN, {info_count} INFO "
        f"({len(issues)} total)"
    )

    # Exit non-zero only on HIGH findings
    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
