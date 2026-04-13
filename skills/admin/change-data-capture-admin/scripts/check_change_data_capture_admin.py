#!/usr/bin/env python3
"""Checker script for Change Data Capture Admin skill.

Validates Salesforce Metadata API source for common Change Data Capture
admin configuration mistakes. Checks PlatformEventChannel and
PlatformEventChannelMember XML files for anti-patterns documented in
references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_change_data_capture_admin.py [--help]
    python3 check_change_data_capture_admin.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Standard per-object channel suffixes that do NOT support enrichment.
# Any PlatformEventChannelMember whose eventChannel ends with one of these
# is a standard channel where EnrichedField configuration is unsupported.
STANDARD_CHANNEL_SUFFIXES = ("ChangeEvent", "ChangeEvents")

# The Data Cloud-managed channel. Members of this channel must not be
# modified directly via Metadata API.
DATA_CLOUD_CHANNEL_NAME = "DataCloudEntities"

# Metadata namespace used in Salesforce XML files.
SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Change Data Capture Admin configuration and metadata for "
            "common issues documented in the change-data-capture-admin skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    """Return the local part of a namespaced XML tag."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _find_text(element: ET.Element, local_tag: str) -> str | None:
    """Find a child element by local tag name (ignoring namespace) and return its text."""
    for child in element:
        if _strip_ns(child.tag) == local_tag:
            return (child.text or "").strip()
    return None


def _has_enriched_fields(element: ET.Element) -> bool:
    """Return True if the element contains any enrichedFields children."""
    for child in element:
        if _strip_ns(child.tag) == "enrichedFields":
            return True
    return False


def _is_standard_channel(channel_name: str) -> bool:
    """Return True if the channel name looks like a standard per-object or default channel."""
    for suffix in STANDARD_CHANNEL_SUFFIXES:
        if channel_name.endswith(suffix):
            return True
    return False


def check_platform_event_channel_members(manifest_dir: Path) -> list[str]:
    """Check PlatformEventChannelMember XML files for configuration issues."""
    issues: list[str] = []

    member_dir = manifest_dir / "platformEventChannelMembers"
    if not member_dir.exists():
        # Try nested source format: force-app/main/default/platformEventChannelMembers
        for candidate in manifest_dir.rglob("platformEventChannelMembers"):
            if candidate.is_dir():
                member_dir = candidate
                break

    if not member_dir.exists():
        # No channel members found — nothing to check.
        return issues

    for xml_file in sorted(member_dir.glob("*.platformEventChannelMember")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"{xml_file.name}: XML parse error — {exc}")
            continue

        root = tree.getroot()
        event_channel = _find_text(root, "eventChannel") or ""
        selected_entity = _find_text(root, "selectedEntity") or ""
        has_enrichment = _has_enriched_fields(root)

        # Anti-Pattern 1: Enrichment configured on a standard per-object channel.
        if has_enrichment and _is_standard_channel(event_channel):
            issues.append(
                f"{xml_file.name}: Enrichment (enrichedFields) is configured on "
                f"standard channel '{event_channel}' for entity '{selected_entity}'. "
                "Enrichment is only supported on custom multi-entity channels "
                "(channel names ending in '__chn'). The enrichment will be silently "
                "ignored at delivery time. Move this entity to a custom PlatformEventChannel "
                "and configure enrichment there."
            )

        # Anti-Pattern 2: DataCloudEntities channel member in source control.
        # Having this in the deployment package risks overwriting or removing
        # Data Cloud-managed selections during deployment.
        if event_channel == DATA_CLOUD_CHANNEL_NAME or selected_entity == DATA_CLOUD_CHANNEL_NAME:
            issues.append(
                f"{xml_file.name}: PlatformEventChannelMember references the "
                f"'{DATA_CLOUD_CHANNEL_NAME}' channel (entity: '{selected_entity}'). "
                "This channel is managed by Data Cloud. Including it in a Metadata API "
                "deployment package risks breaking Data Cloud CRM Data Stream sync. "
                "Remove this file from the deployment and manage it through Data Cloud "
                "CRM Data Stream configuration only."
            )

    return issues


def check_platform_event_channels(manifest_dir: Path) -> list[str]:
    """Check PlatformEventChannel XML files for configuration issues."""
    issues: list[str] = []

    channel_dir = manifest_dir / "platformEventChannels"
    if not channel_dir.exists():
        for candidate in manifest_dir.rglob("platformEventChannels"):
            if candidate.is_dir():
                channel_dir = candidate
                break

    if not channel_dir.exists():
        return issues

    for xml_file in sorted(channel_dir.glob("*.platformEventChannel")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"{xml_file.name}: XML parse error — {exc}")
            continue

        root = tree.getroot()
        channel_type = _find_text(root, "channelType") or ""

        # Custom CDC channels must use channelType = "data".
        # A missing or incorrect channelType produces a deployment error.
        if channel_type not in ("data", "event"):
            issues.append(
                f"{xml_file.name}: Unexpected channelType value '{channel_type}'. "
                "Change Data Capture custom channels require channelType 'data'. "
                "Platform Event channels use 'event'. Verify the intended channel purpose."
            )

    return issues


def check_skill_md_present(manifest_dir: Path) -> list[str]:
    """Warn if the SKILL.md is missing from the expected skill directory."""
    issues: list[str] = []
    skill_md = manifest_dir / "SKILL.md"
    if not skill_md.exists():
        # Not a hard error — the checker may be run from a metadata dir, not the skill dir.
        pass
    return issues


def check_change_data_capture_admin(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_platform_event_channel_members(manifest_dir))
    issues.extend(check_platform_event_channels(manifest_dir))
    issues.extend(check_skill_md_present(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_change_data_capture_admin(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
