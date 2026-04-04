#!/usr/bin/env python3
"""Checker script for Event-Driven Architecture Patterns skill.

Checks org metadata and source code for common misconfigurations when
mixing Platform Events, CDC, Streaming API (PushTopic), and Outbound
Messages in the same org or project.

Uses stdlib only — no pip dependencies.

Checks performed:
  1. Detects PushTopic records (via Apex or XML metadata) alongside CDC channel
     member definitions — warns that both patterns are in use and recommends
     consolidation.
  2. Detects LWC components that import 'lightning/empApi' and subscribe to a
     '/topic/' channel (PushTopic) — empApi does not support PushTopic channels.
  3. Detects Apex or Flow trigger code that publishes Platform Events on an
     after-update trigger on an object also enabled for CDC — warns of potential
     duplicate event streams.
  4. Detects source files that reference WorkflowOutboundMessage metadata
     alongside Platform Event references, suggesting a partial migration that
     may have inconsistent delivery guarantees.
  5. Detects hardcoded Streaming API replay ID -1 (tip-only) in external
     subscriber code without a justifying comment — warns of data-loss risk
     on reconnect.

Usage:
    python3 check_event_driven_architecture_patterns.py [--manifest-dir path/to/metadata]
    python3 check_event_driven_architecture_patterns.py [--source-dir path/to/src]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Salesforce Metadata API XML namespace
# ---------------------------------------------------------------------------
_SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    return f"{{{_SF_NS}}}{local}"


# ---------------------------------------------------------------------------
# Check 1 — Mixed PushTopic + CDC usage in the same project
# ---------------------------------------------------------------------------

_PUSHTOPIC_APEX_RE = re.compile(
    r'\bPushTopic\b',
    re.IGNORECASE,
)

_CDC_CHANNEL_RE = re.compile(
    r'/data/\w+ChangeEvent|ChangeEventHeader|changeType',
    re.IGNORECASE,
)


def check_mixed_pushtopic_cdc(manifest_dir: Path, source_dir: Path) -> list[str]:
    """Warn if both PushTopic and CDC patterns are present in the same project."""
    issues: list[str] = []

    has_pushtopic = False
    has_cdc = False

    # Check for PlatformEventChannelMember files (CDC enablement)
    cdc_member_files = list(manifest_dir.rglob("*.platformEventChannelMember"))
    if cdc_member_files:
        has_cdc = True

    # Check source files for PushTopic references and CDC usage
    source_files = [
        f for f in source_dir.rglob("*")
        if f.suffix in {".java", ".py", ".js", ".ts", ".cls", ".xml"}
        and f.is_file()
        and f.name != "check_event_driven_architecture_patterns.py"
    ]

    pushtopic_files: list[str] = []
    cdc_files: list[str] = []

    for f in source_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if _PUSHTOPIC_APEX_RE.search(text):
            has_pushtopic = True
            pushtopic_files.append(f.name)

        if _CDC_CHANNEL_RE.search(text):
            has_cdc = True
            cdc_files.append(f.name)

    if has_pushtopic and has_cdc:
        issues.append(
            "Both PushTopic (Streaming API) and CDC patterns are present in this project. "
            f"PushTopic references found in: {', '.join(sorted(set(pushtopic_files))[:5])}. "
            "PushTopic provides only 24-hour event retention vs CDC's 72-hour window and "
            "does not include automatic changedFields tracking. "
            "Evaluate whether PushTopic subscriptions can be migrated to CDC or Platform Events. "
            "See: integration/streaming-api-and-pushtopic and integration/change-data-capture-integration skills."
        )
    return issues


# ---------------------------------------------------------------------------
# Check 2 — LWC empApi subscribing to /topic/ (PushTopic) channel
# ---------------------------------------------------------------------------

_EMPAPI_IMPORT_RE = re.compile(
    r"from\s+['\"]lightning/empApi['\"]",
    re.IGNORECASE,
)
_TOPIC_CHANNEL_RE = re.compile(
    r"['\"/]topic/",
    re.IGNORECASE,
)


def check_lwc_empapi_pushtopic(source_dir: Path) -> list[str]:
    """Warn if LWC uses empApi with a /topic/ channel (not supported)."""
    issues: list[str] = []
    lwc_files = [
        f for f in source_dir.rglob("*.js")
        if f.is_file() and f.name != "check_event_driven_architecture_patterns.py"
    ]

    for f in lwc_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if _EMPAPI_IMPORT_RE.search(text) and _TOPIC_CHANNEL_RE.search(text):
            issues.append(
                f"{f}: LWC component imports 'lightning/empApi' and references a '/topic/' "
                "channel. The empApi module does NOT support PushTopic channels — it only "
                "supports Platform Event channels (/event/) and CDC channels (/data/). "
                "Change the channel to '/event/YourPlatformEvent__e' or subscribe to a "
                "Platform Event instead of a PushTopic. "
                "See: https://developer.salesforce.com/docs/platform/lwc/guide/use-emp-api.html"
            )
    return issues


# ---------------------------------------------------------------------------
# Check 3 — Platform Event publish on after-update trigger for CDC-enabled object
# ---------------------------------------------------------------------------

_AFTER_UPDATE_TRIGGER_RE = re.compile(
    r'trigger\s+\w+\s+on\s+(\w+)\s*\([^)]*after\s+update',
    re.IGNORECASE,
)
_EVENTBUS_PUBLISH_RE = re.compile(
    r'EventBus\.publish',
    re.IGNORECASE,
)


def check_duplicate_event_streams(source_dir: Path, manifest_dir: Path) -> list[str]:
    """Warn if Apex publishes Platform Events on after-update for CDC-enabled objects."""
    issues: list[str] = []

    # Collect CDC-enabled entity names from PlatformEventChannelMember files
    cdc_entities: set[str] = set()
    for f in manifest_dir.rglob("*.platformEventChannelMember"):
        try:
            tree = ElementTree.parse(f)
            root = tree.getroot()
            selected_el = root.find(_tag("selectedEntity"))
            if selected_el is not None and selected_el.text:
                cdc_entities.add(selected_el.text.strip().lower())
        except ElementTree.ParseError:
            continue

    if not cdc_entities:
        return issues

    # Check Apex trigger files
    apex_files = [
        f for f in source_dir.rglob("*.trigger")
        if f.is_file()
    ]

    for f in apex_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        trigger_match = _AFTER_UPDATE_TRIGGER_RE.search(text)
        if trigger_match and _EVENTBUS_PUBLISH_RE.search(text):
            object_name = trigger_match.group(1).lower()
            if object_name in cdc_entities:
                issues.append(
                    f"{f}: Apex trigger on '{trigger_match.group(1)}' (after update) publishes "
                    "a Platform Event via EventBus.publish(), but this object is also enabled for "
                    "CDC. This may create a duplicate event stream — both the Platform Event and "
                    "the CDC ChangeEvent will fire for the same record update. "
                    "Evaluate whether both streams are intentionally serving different consumers, "
                    "or if one can be eliminated to reduce complexity and event volume."
                )
    return issues


# ---------------------------------------------------------------------------
# Check 4 — Mixed Outbound Messages and Platform Events (partial migration)
# ---------------------------------------------------------------------------

_OUTBOUND_MSG_RE = re.compile(
    r'WorkflowOutboundMessage|OutboundMessage|outboundMessages',
    re.IGNORECASE,
)
_PLATFORM_EVENT_PUBLISH_RE = re.compile(
    r'EventBus\.publish|publishPlatformEvent|/services/data/.*/sobjects/\w+__e',
    re.IGNORECASE,
)


def check_partial_outbound_migration(source_dir: Path, manifest_dir: Path) -> list[str]:
    """Warn if project references both Outbound Messages and Platform Events (partial migration)."""
    issues: list[str] = []

    has_outbound = False
    has_platform_event = False
    outbound_files: list[str] = []
    pe_files: list[str] = []

    # Check XML metadata for Outbound Message definitions
    for f in manifest_dir.rglob("*.workflow"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _OUTBOUND_MSG_RE.search(text):
            has_outbound = True
            outbound_files.append(f.name)

    # Check source files
    source_files = [
        f for f in source_dir.rglob("*")
        if f.suffix in {".java", ".py", ".js", ".ts", ".cls", ".xml"}
        and f.is_file()
        and f.name != "check_event_driven_architecture_patterns.py"
    ]

    for f in source_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if _OUTBOUND_MSG_RE.search(text):
            has_outbound = True
            outbound_files.append(f.name)

        if _PLATFORM_EVENT_PUBLISH_RE.search(text):
            has_platform_event = True
            pe_files.append(f.name)

    if has_outbound and has_platform_event:
        issues.append(
            "Project references both Outbound Messages (SOAP, at-least-once with ACK retry) "
            "and Platform Events (pub/sub, fire-and-forget). This suggests a partial migration "
            f"may be in progress. Outbound Message references in: {', '.join(sorted(set(outbound_files))[:3])}. "
            "Verify that delivery guarantees are intentionally different for each integration path. "
            "Outbound Messages provide SOAP ACK-retry guarantees that Platform Events do not replicate "
            "without an explicit retry layer on the subscriber side. "
            "See: integration/event-driven-architecture-patterns skill — Outbound Messages section."
        )
    return issues


# ---------------------------------------------------------------------------
# Check 5 — Hardcoded Streaming API replay ID -1 without justification
# ---------------------------------------------------------------------------

_STREAMING_REPLAY_MINUS1_RE = re.compile(
    r"['\"/]topic/.*['\"].*-1\b|replay.*-1\b|-1.*replay",
    re.IGNORECASE,
)
_REPLAY_JUSTIFICATION_RE = re.compile(
    r'tip.?only|intentional|new.?events.?only|no.?history|new.?subscription',
    re.IGNORECASE,
)


def check_streaming_tip_only_replay(source_dir: Path) -> list[str]:
    """Warn if Streaming API subscriber hardcodes replay -1 without explanation."""
    issues: list[str] = []
    source_files = [
        f for f in source_dir.rglob("*")
        if f.suffix in {".java", ".py", ".js", ".ts"}
        and f.is_file()
        and f.name != "check_event_driven_architecture_patterns.py"
    ]

    for f in source_files:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for i, line in enumerate(lines):
            if _STREAMING_REPLAY_MINUS1_RE.search(line):
                window_start = max(0, i - 3)
                window_end = min(len(lines), i + 4)
                window = "\n".join(lines[window_start:window_end])
                if not _REPLAY_JUSTIFICATION_RE.search(window):
                    issues.append(
                        f"{f}:{i + 1}: Streaming API subscription appears to use replay ID -1 "
                        "(tip-only — receive only new events, no replay on reconnect) without "
                        "an explanatory comment. In production integrations, the replay ID should "
                        "be loaded from durable storage to prevent event loss after reconnect. "
                        "Only use replay -1 if tip-only behavior is explicitly intentional. "
                        "Streaming API retains events for only 24 hours; lost events cannot be recovered."
                    )
    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check event-driven architecture patterns for common misconfigurations "
            "when mixing Platform Events, CDC, Streaming API, and Outbound Messages."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--source-dir",
        default=None,
        help="Root directory for source code checks (defaults to --manifest-dir).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    source_dir = Path(args.source_dir) if args.source_dir else manifest_dir

    if not manifest_dir.exists():
        print(f"ISSUE: Manifest directory not found: {manifest_dir}")
        return 1

    all_issues: list[str] = []
    all_issues.extend(check_mixed_pushtopic_cdc(manifest_dir, source_dir))
    all_issues.extend(check_lwc_empapi_pushtopic(source_dir))
    all_issues.extend(check_duplicate_event_streams(source_dir, manifest_dir))
    all_issues.extend(check_partial_outbound_migration(source_dir, manifest_dir))
    all_issues.extend(check_streaming_tip_only_replay(source_dir))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
