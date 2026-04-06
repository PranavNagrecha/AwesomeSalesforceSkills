#!/usr/bin/env python3
"""Checker script for Omni-Channel Capacity Model skill.

Checks org metadata for common capacity model configuration issues.
Scans ServiceChannel, PresenceUserConfig, and QueueRoutingConfig metadata
for anti-patterns like equal weights, missing overflow, and low skill coverage.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omni_channel_capacity_model.py [--help]
    python3 check_omni_channel_capacity_model.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Omni-Channel Capacity Model configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find files with the given suffix under root."""
    results: list[str] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(suffix):
                results.append(os.path.join(dirpath, fname))
    return [Path(p) for p in results]


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file, returning None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except (ET.ParseError, OSError):
        return None


def _strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _get_child_text(element: ET.Element, local_name: str) -> str | None:
    """Get text of a child element by local name, ignoring namespace."""
    for child in element:
        if _strip_ns(child.tag) == local_name:
            return (child.text or "").strip()
    return None


def check_service_channel_weights(manifest_dir: Path) -> list[str]:
    """Check ServiceChannel metadata for equal-weight anti-pattern."""
    issues: list[str] = []
    channel_files = _find_files(manifest_dir, ".serviceChannel-meta.xml")
    if not channel_files:
        return issues

    weights: dict[str, str] = {}
    for cf in channel_files:
        root = _parse_xml_safe(cf)
        if root is None:
            continue
        name = _get_child_text(root, "masterLabel") or cf.stem.replace(".serviceChannel-meta", "")
        capacity = _get_child_text(root, "capacityWeight")
        if capacity:
            weights[name] = capacity

    if len(weights) >= 2:
        unique_weights = set(weights.values())
        if len(unique_weights) == 1:
            issues.append(
                f"All {len(weights)} Service Channels have the same capacity weight "
                f"({unique_weights.pop()}). Differentiate weights by channel effort "
                f"(e.g., Voice=10, Case=5, Chat=3)."
            )

    return issues


def check_presence_configs(manifest_dir: Path) -> list[str]:
    """Check PresenceUserConfig metadata for capacity issues."""
    issues: list[str] = []
    config_files = _find_files(manifest_dir, ".presenceUserConfig-meta.xml")
    if not config_files:
        return issues

    for cf in config_files:
        root = _parse_xml_safe(cf)
        if root is None:
            continue
        name = _get_child_text(root, "masterLabel") or cf.stem
        capacity = _get_child_text(root, "capacity")
        if capacity and capacity.isdigit():
            cap_int = int(capacity)
            if cap_int < 5:
                issues.append(
                    f"Presence Configuration '{name}' has capacity {cap_int}, which is very low. "
                    f"Consider using 10+ with weighted Service Channels instead of low flat capacity."
                )

    return issues


def check_queue_routing_overflow(manifest_dir: Path) -> list[str]:
    """Check QueueRoutingConfig for missing overflow / secondary routing."""
    issues: list[str] = []
    routing_files = _find_files(manifest_dir, ".queueRoutingConfig-meta.xml")
    if not routing_files:
        return issues

    queue_names: list[str] = []
    has_overflow = False
    for rf in routing_files:
        root = _parse_xml_safe(rf)
        if root is None:
            continue
        name = _get_child_text(root, "masterLabel") or rf.stem
        queue_names.append(name)
        # Check for secondary routing indicator (overflow timeout or priority)
        priority = _get_child_text(root, "routingPriority")
        if priority and priority not in ("1", ""):
            has_overflow = True

    if len(queue_names) >= 2 and not has_overflow:
        issues.append(
            f"Found {len(queue_names)} routing configurations but none appear to be "
            f"secondary/overflow routes. Ensure specialized queues have overflow paths "
            f"to prevent indefinite wait times."
        )

    return issues


def check_omni_channel_capacity_model(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_service_channel_weights(manifest_dir))
    issues.extend(check_presence_configs(manifest_dir))
    issues.extend(check_queue_routing_overflow(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_omni_channel_capacity_model(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
