#!/usr/bin/env python3
"""Checker script for Change Data Capture Admin skill.

Checks CDC-related metadata for common configuration issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_change_data_capture_admin.py [--help]
    python3 check_change_data_capture_admin.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CDC metadata for common configuration issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_platform_event_channels(manifest_dir: Path) -> list[str]:
    """Check PlatformEventChannel metadata for CDC configuration issues."""
    issues: list[str] = []

    # Check for PlatformEventChannel metadata files
    pec_dir = manifest_dir / "platformEventChannels"
    if not pec_dir.exists():
        return issues

    for pec_file in pec_dir.glob("*.platformEventChannel"):
        try:
            tree = ET.parse(pec_file)
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            channel_name = pec_file.stem

            # Warn if channel name contains DataCloud (should not be manually managed)
            if "datacloud" in channel_name.lower() or "data_cloud" in channel_name.lower():
                issues.append(
                    f"PlatformEventChannel '{channel_name}' appears to be a Data Cloud-managed channel. "
                    "Do not modify Data Cloud CDC channel members via Metadata API — "
                    "manage through Data Cloud Admin UI instead."
                )

        except (ET.ParseError, OSError):
            pass

    return issues


def check_platform_event_channel_members(manifest_dir: Path) -> list[str]:
    """Check PlatformEventChannelMember metadata for enrichment on per-object channels."""
    issues: list[str] = []

    pec_member_dir = manifest_dir / "platformEventChannelMembers"
    if not pec_member_dir.exists():
        return issues

    # Per-object system channels that don't support enrichment
    system_channel_prefixes = ("/data/", "data/")

    for member_file in pec_member_dir.glob("*.platformEventChannelMember"):
        try:
            tree = ET.parse(member_file)
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            member_name = member_file.stem

            # Check for enriched fields on what appears to be a per-object channel member
            channel_elem = root.find(f"{ns}eventChannel")
            enriched_fields = root.findall(f"{ns}enrichedFields")

            if channel_elem is not None and enriched_fields:
                channel_name = channel_elem.text or ""
                if any(channel_name.startswith(prefix) for prefix in system_channel_prefixes):
                    issues.append(
                        f"PlatformEventChannelMember '{member_name}': "
                        f"Enriched fields configured on per-object channel '{channel_name}'. "
                        "Enrichment is only supported on custom multi-entity channels, "
                        "not on system per-object channels."
                    )

        except (ET.ParseError, OSError):
            pass

    return issues


def check_change_data_capture_admin(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_platform_event_channels(manifest_dir))
    issues.extend(check_platform_event_channel_members(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_change_data_capture_admin(manifest_dir)

    if not issues:
        print("No CDC admin configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
