#!/usr/bin/env python3
"""Checker script for Platform Events Integration skill.

Inspects Salesforce metadata files for common Platform Events integration
issues: missing correlation ID fields, fields that attempt to set per-event
retention (which is fixed and not configurable), legacy standard-volume events
retiring in Summer '27, and subscription configurations lacking replay ID
guidance.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_platform_events_integration.py [--help]
    python3 check_platform_events_integration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce metadata XML namespace
_SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Org-wide platform event publishing allocation per hour for high-volume events
# on Enterprise / Performance / Unlimited (50,000 on Developer). This is a hard
# org allocation, not a per-event-tier property — no event type exceeds it.
# https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
_HOURLY_PUBLISH_ALLOCATION = 250_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Platform Events integration issues "
            "including missing correlation ID fields, standard vs high-volume selection, "
            "and replay ID design gaps."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_platform_event_files(root: Path) -> list[Path]:
    """Return all .object-meta.xml files under root whose name ends in __e."""
    results: list[Path] = []
    for p in root.rglob("*.object-meta.xml"):
        if p.stem.endswith("__e"):
            results.append(p)
    return results


def _find_field_files(root: Path, event_name: str) -> list[Path]:
    """Return field metadata files for the given event (event_name without extension)."""
    # Metadata API v2 structure: objects/<EventName__e>/fields/*.field-meta.xml
    event_dir = root / "objects" / event_name / "fields"
    if event_dir.exists():
        return list(event_dir.glob("*.field-meta.xml"))
    return []


def _has_correlation_id_field(field_files: list[Path]) -> bool:
    """Return True if any field looks like a correlation / idempotency key."""
    correlation_hints = {"correlationid", "idempotency", "correlationkey", "msgid", "messageid"}
    for fpath in field_files:
        name_lower = fpath.stem.lower().replace("__c", "").replace("_", "")
        if any(hint in name_lower for hint in correlation_hints):
            return True
    return False


def _declares_standard_volume(xml_path: Path) -> bool:
    """Return True if the event object metadata explicitly declares standard-volume.

    New platform events are high volume by default; standard-volume custom
    platform events can no longer be defined and are retired in Summer '27.
    https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_event_limits.htm
    """
    try:
        tree = ET.parse(xml_path)
        root_el = tree.getroot()
        for tag in ("eventType", "eventChannel", "eventChannelUsage"):
            for el in root_el.iter(f"{{{_SF_NS}}}{tag}"):
                if "standardvolume" in (el.text or "").lower().replace(" ", ""):
                    return True
    except ET.ParseError:
        pass
    return False


def _check_event_file(xml_path: Path, manifest_dir: Path) -> list[str]:
    """Run checks on a single platform event object-meta.xml file."""
    issues: list[str] = []
    event_name = xml_path.stem  # e.g. OrderShipped__e

    # Check 1: Correlation / idempotency field presence
    field_files = _find_field_files(manifest_dir, event_name)
    if field_files and not _has_correlation_id_field(field_files):
        issues.append(
            f"{event_name}: No correlation/idempotency key field found. "
            "External subscribers receive at-least-once delivery. Add a CorrelationId__c "
            "or similar Text field to enable idempotent processing."
        )

    # Check 2: Fabricated retention field on the event schema.
    # Platform event retention is a fixed platform property (72h high-volume,
    # 24h legacy standard-volume) and is NOT settable per event. A field named
    # RetainUntilDate / RetentionDate / ExpiresAt on an __e object is either a
    # no-op the publisher believes is extending retention, or a custom field
    # whose name will mislead the next reader. Either way, flag it.
    bogus_retention_names = {
        "retainuntildate",
        "retainuntil",
        "retentiondate",
        "retentionuntil",
        "expiresat",
        "expiryDate".lower(),
    }
    for fpath in field_files:
        stem_lower = fpath.stem.lower().replace("__c", "").replace("_", "")
        if stem_lower in {n.replace("_", "") for n in bogus_retention_names}:
            issues.append(
                f"{event_name}: field '{fpath.stem}' looks like an attempt to set "
                "per-event retention. Platform event retention is fixed and not "
                "configurable (72 hours for high-volume events, 24 hours for legacy "
                "standard-volume events); there is no RetainUntilDate field on any "
                "Platform Event and an unrecognized key is ignored at publish time "
                "without error. For a replay window beyond 72 hours, have the publisher "
                "write a durable copy (Big Object / external queue) and backfill from it. "
                "See references/gotchas.md Gotcha 1."
            )

    # Check 3: legacy standard-volume events are retiring in Summer '27.
    # The retirement target moved: the Summer '25 (API 64.0) edition of the
    # allocations page projected Summer '25; the current edition says Summer '27.
    # Existing standard-volume events keep working until then.
    if _declares_standard_volume(xml_path):
        issues.append(
            f"{event_name}: declared as a standard-volume platform event. "
            "New standard-volume custom platform events can no longer be defined "
            "(new platform events are high volume by default), and Salesforce retires "
            "standard-volume custom platform events in Summer '27 -- this event still "
            "publishes and delivers until then. Plan a migration to a high-volume event; "
            "note the allocation and retention change "
            "(100,000 -> 250,000 publishes/hour on EE/Perf/Unlimited; 24h -> 72h retention)."
        )

    return issues


def _check_for_replay_documentation(manifest_dir: Path) -> list[str]:
    """
    Look for any documentation or configuration file referencing replay strategy.
    Warn if platform event files exist but no replay/subscriber documentation is found.
    """
    issues: list[str] = []
    event_files = _find_platform_event_files(manifest_dir)
    if not event_files:
        return issues

    # Heuristic: look for markdown or config files mentioning replay strategy
    replay_hints = {"replayid", "replay_id", "replay-id", "durable subscription", "backfill"}
    found_replay_doc = False
    for fpath in manifest_dir.rglob("*.md"):
        try:
            content_lower = fpath.read_text(encoding="utf-8", errors="ignore").lower()
            if any(hint in content_lower for hint in replay_hints):
                found_replay_doc = True
                break
        except OSError:
            continue

    if not found_replay_doc:
        issues.append(
            "No documentation referencing replay ID strategy found in this manifest directory. "
            "External Platform Event subscribers must persist replayId durably. "
            "Document the replay strategy (starting position, storage mechanism, "
            "behavior on first run and on reconnect after outage)."
        )

    return issues


def check_platform_events_integration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    event_files = _find_platform_event_files(manifest_dir)

    if not event_files:
        # No platform events found — nothing to check
        return issues

    for event_file in sorted(event_files):
        issues.extend(_check_event_file(event_file, manifest_dir))

    issues.extend(_check_for_replay_documentation(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_platform_events_integration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
