#!/usr/bin/env python3
"""Checker script for Change Data Capture Integration skill.

Checks org metadata or configuration relevant to Change Data Capture Integration.
Uses stdlib only — no pip dependencies.

Checks performed:
  1. Detects PlatformEventChannelMember XML files and warns if more than 5 entities
     are selected (default free-tier limit).
  2. Warns if any custom PlatformEventChannel has channelType other than 'data'
     (common misconfiguration when Platform Event channels are mixed with CDC channels).
  3. Detects Streaming API subscriber code that references changeType without a GAP_
     check (likely missing gap event handling).
  4. Detects CometD subscriber code that reads changedFields from ChangeEventHeader
     (changedFields is not available in CometD — only in Pub/Sub API).
  5. Detects CDC subscriber code that hardcodes replay ID -1 without a comment
     explaining why tip-only is intentional.

Usage:
    python3 check_change_data_capture_integration.py [--manifest-dir path/to/metadata]
    python3 check_change_data_capture_integration.py [--source-dir path/to/src]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# XML namespace used by Salesforce Metadata API
# ---------------------------------------------------------------------------
_SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    return f"{{{_SF_NS}}}{local}"


# ---------------------------------------------------------------------------
# Check 1 — Entity selection count
# ---------------------------------------------------------------------------

def check_entity_selection_count(manifest_dir: Path) -> list[str]:
    """Warn if more than 5 CDC entity selections exist across all channels."""
    issues: list[str] = []
    member_files = list(manifest_dir.rglob("*.platformEventChannelMember"))
    if not member_files:
        return issues

    entities: set[str] = set()
    for f in member_files:
        try:
            tree = ElementTree.parse(f)
            root = tree.getroot()
            channel_type_el = root.find(_tag("channelType"))
            # Only count CDC channel members (channelType == 'data')
            # Some files may omit channelType; assume data if absent
            if channel_type_el is not None and channel_type_el.text != "data":
                continue
            selected_el = root.find(_tag("selectedEntity"))
            if selected_el is not None and selected_el.text:
                entities.add(selected_el.text.strip())
        except ElementTree.ParseError:
            issues.append(f"Could not parse PlatformEventChannelMember XML: {f.name}")

    if len(entities) > 5:
        issues.append(
            f"CDC entity selection count is {len(entities)} ({', '.join(sorted(entities))}). "
            "The default limit is 5 entities across all channels for all editions. "
            "Exceeding this requires a Change Data Capture add-on license. "
            "See: https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/"
            "change_data_capture/cdc_allocations.htm"
        )
    return issues


# ---------------------------------------------------------------------------
# Check 2 — PlatformEventChannel channelType for CDC channels
# ---------------------------------------------------------------------------

def check_channel_type(manifest_dir: Path) -> list[str]:
    """Warn if a PlatformEventChannel used for CDC does not have channelType=data."""
    issues: list[str] = []
    channel_files = list(manifest_dir.rglob("*.platformEventChannel"))

    for f in channel_files:
        try:
            tree = ElementTree.parse(f)
            root = tree.getroot()
            channel_type_el = root.find(_tag("channelType"))
            label_el = root.find(_tag("label"))
            label = label_el.text.strip() if label_el is not None and label_el.text else f.stem
            if channel_type_el is None:
                issues.append(
                    f"PlatformEventChannel '{label}' ({f.name}) is missing <channelType>. "
                    "CDC custom channels must set channelType to 'data'."
                )
            elif channel_type_el.text and channel_type_el.text.strip() not in ("data", "event"):
                issues.append(
                    f"PlatformEventChannel '{label}' ({f.name}) has unrecognised channelType "
                    f"'{channel_type_el.text.strip()}'. Expected 'data' (CDC) or 'event' (Platform Event)."
                )
        except ElementTree.ParseError:
            issues.append(f"Could not parse PlatformEventChannel XML: {f.name}")

    return issues


# ---------------------------------------------------------------------------
# Check 3 — Gap event handling in source code
# ---------------------------------------------------------------------------

_CHANGETYPE_READ_RE = re.compile(
    r'changeType|change_type|getChangeType',
    re.IGNORECASE,
)
_GAP_CHECK_RE = re.compile(
    r'GAP_|startswith.*GAP|gap.*prefix|changeType.*GAP',
    re.IGNORECASE,
)


def check_gap_event_handling(source_dir: Path) -> list[str]:
    """Warn if source files read changeType but have no GAP_ check nearby."""
    issues: list[str] = []
    source_files = [
        f for f in source_dir.rglob("*")
        if f.suffix in {".java", ".py", ".js", ".ts", ".cls", ".xml"}
        and f.is_file()
        and f.name != "check_change_data_capture_integration.py"
    ]

    for f in source_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if _CHANGETYPE_READ_RE.search(text) and not _GAP_CHECK_RE.search(text):
            issues.append(
                f"{f}: References 'changeType' but has no GAP_ prefix check. "
                "CDC subscribers must handle gap events (GAP_CREATE, GAP_UPDATE, GAP_DELETE, "
                "GAP_UNDELETE, GAP_OVERFLOW) by fetching current record state from REST API. "
                "Missing gap handling causes silent data drift."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 4 — CometD subscriber reading changedFields (not available in CometD)
# ---------------------------------------------------------------------------

_COMETD_INDICATOR_RE = re.compile(
    r'/cometd/|EmpConnector|bayeux|BayeuxClient|long.?poll',
    re.IGNORECASE,
)
_CHANGED_FIELDS_RE = re.compile(
    r'changedFields|changed_fields|nulledFields|diffFields',
    re.IGNORECASE,
)


def check_cometd_changed_fields(source_dir: Path) -> list[str]:
    """Warn if a CometD subscriber reads changedFields (only available in Pub/Sub API)."""
    issues: list[str] = []
    source_files = [
        f for f in source_dir.rglob("*")
        if f.suffix in {".java", ".py", ".js", ".ts", ".cls"}
        and f.is_file()
        and f.name != "check_change_data_capture_integration.py"
    ]

    for f in source_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if _COMETD_INDICATOR_RE.search(text) and _CHANGED_FIELDS_RE.search(text):
            issues.append(
                f"{f}: File appears to use CometD (EMP Connector / Bayeux / long-poll) "
                "but also reads changedFields/nulledFields/diffFields. "
                "These ChangeEventHeader fields are NOT available in CometD — only in "
                "Pub/Sub API (gRPC) and Apex trigger subscribers. "
                "Switch to Pub/Sub API if field-level deltas are required."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 5 — Hardcoded replay ID -1 without explanation
# ---------------------------------------------------------------------------

_REPLAY_MINUS1_RE = re.compile(
    r'replay.*=.*-1\b|replayId.*-1\b|-1.*replay',
    re.IGNORECASE,
)
_REPLAY_COMMENT_RE = re.compile(
    r'tip.?only|intentional|no.?history|tip\s+replay',
    re.IGNORECASE,
)


def check_hardcoded_replay_tip(source_dir: Path) -> list[str]:
    """Warn if replay ID is hardcoded to -1 without an explanatory comment nearby."""
    issues: list[str] = []
    source_files = [
        f for f in source_dir.rglob("*")
        if f.suffix in {".java", ".py", ".js", ".ts", ".cls"}
        and f.is_file()
        and f.name != "check_change_data_capture_integration.py"
    ]

    for f in source_files:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        for i, line in enumerate(lines):
            if _REPLAY_MINUS1_RE.search(line):
                # Check surrounding 3 lines for an explanatory comment
                window_start = max(0, i - 2)
                window_end = min(len(lines), i + 4)
                window = "\n".join(lines[window_start:window_end])
                if not _REPLAY_COMMENT_RE.search(window):
                    issues.append(
                        f"{f}:{i + 1}: Replay ID hardcoded to -1 (tip-only) without an "
                        "explanatory comment. In production CDC integrations, replay ID should "
                        "be loaded from durable external state to ensure no events are missed "
                        "after a subscriber restart. Use -1 only if tip-only behavior is "
                        "explicitly intentional and documented."
                    )
    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Change Data Capture Integration configuration and source code for common issues.",
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

    all_issues: list[str] = []

    if not manifest_dir.exists():
        print(f"ISSUE: Manifest directory not found: {manifest_dir}")
        return 1

    all_issues.extend(check_entity_selection_count(manifest_dir))
    all_issues.extend(check_channel_type(manifest_dir))
    all_issues.extend(check_gap_event_handling(source_dir))
    all_issues.extend(check_cometd_changed_fields(source_dir))
    all_issues.extend(check_hardcoded_replay_tip(source_dir))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
