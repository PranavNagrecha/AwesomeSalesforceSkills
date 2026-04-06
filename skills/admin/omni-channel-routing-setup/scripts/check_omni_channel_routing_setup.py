#!/usr/bin/env python3
"""Checker script for Omni-Channel Routing Setup skill.

Validates Salesforce metadata for common Omni-Channel routing configuration issues.
Checks Service Channel, Routing Configuration, Presence Configuration, and
Presence Status metadata files for anti-patterns documented in this skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omni_channel_routing_setup.py [--help]
    python3 check_omni_channel_routing_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Omni-Channel routing setup metadata for common configuration issues. "
            "Checks Service Channels, Routing Configurations, Presence Configurations, "
            "and Presence Statuses for anti-patterns documented in the skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _find_xml_files(root: Path, pattern: str) -> list[Path]:
    """Return all XML files matching the glob pattern under root."""
    return list(root.rglob(pattern))


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse XML file, returning root element or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def _get_text(element: ET.Element | None, tag: str, ns: str = "") -> str:
    """Get text content of a child tag, stripping namespace if present."""
    if element is None:
        return ""
    # Try with namespace prefix
    child = element.find(f"{ns}{tag}" if ns else tag)
    if child is None:
        # Try stripping namespace from element tags via search
        for child_elem in element:
            local = child_elem.tag.split("}")[-1] if "}" in child_elem.tag else child_elem.tag
            if local == tag:
                return (child_elem.text or "").strip()
        return ""
    return (child.text or "").strip()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_routing_configurations(manifest_dir: Path) -> list[str]:
    """Check RoutingConfiguration metadata for common issues."""
    issues: list[str] = []

    routing_configs = _find_xml_files(manifest_dir, "*.routingConfiguration")
    if not routing_configs:
        # Also try inner directory structure
        routing_configs = _find_xml_files(manifest_dir, "*.RoutingConfiguration")

    if not routing_configs:
        return issues  # No routing configs found — not an error, just nothing to check

    for rc_path in routing_configs:
        root = _parse_xml_safe(rc_path)
        if root is None:
            issues.append(f"Cannot parse RoutingConfiguration XML: {rc_path.name}")
            continue

        name = rc_path.stem or str(rc_path)

        # Check 1: Push Timeout should be set (non-zero)
        push_timeout = _get_text(root, "pushTimeout")
        if push_timeout in ("", "0", "0.0"):
            issues.append(
                f"RoutingConfiguration '{name}': pushTimeout is missing or 0. "
                "Always set an explicit push timeout (recommended: 30 seconds) to prevent "
                "work items from blocking agent capacity indefinitely on non-acceptance."
            )

        # Check 2: Routing Model should be a known value
        routing_model = _get_text(root, "routingModel")
        valid_models = {"leastActive", "mostAvailable", "skillsBased", "ExternalRouting"}
        if routing_model and routing_model not in valid_models:
            issues.append(
                f"RoutingConfiguration '{name}': routingModel '{routing_model}' is not a "
                f"recognised value. Expected one of: {', '.join(sorted(valid_models))}."
            )

        # Check 3: Units of capacity should be > 0
        capacity = _get_text(root, "capacityWeight")
        if capacity:
            try:
                cap_val = float(capacity)
                if cap_val <= 0:
                    issues.append(
                        f"RoutingConfiguration '{name}': capacityWeight is {capacity}. "
                        "Capacity weight must be greater than 0 for work items to consume "
                        "agent capacity correctly."
                    )
            except ValueError:
                pass  # Non-numeric value handled by Salesforce validation

        # Check 4: Priority should be set and > 0
        priority = _get_text(root, "priority")
        if priority in ("", "0"):
            issues.append(
                f"RoutingConfiguration '{name}': routing priority is missing or 0. "
                "Set an explicit priority (1 = highest) to control work item sequencing "
                "when an agent is eligible for multiple queues."
            )

    return issues


def check_service_channels(manifest_dir: Path) -> list[str]:
    """Check ServiceChannel metadata for common issues."""
    issues: list[str] = []

    service_channels = _find_xml_files(manifest_dir, "*.serviceChannel")
    if not service_channels:
        service_channels = _find_xml_files(manifest_dir, "*.ServiceChannel")

    if not service_channels:
        return issues

    for sc_path in service_channels:
        root = _parse_xml_safe(sc_path)
        if root is None:
            issues.append(f"Cannot parse ServiceChannel XML: {sc_path.name}")
            continue

        name = sc_path.stem or str(sc_path)

        # Check: Capacity weight should be set and positive
        capacity = _get_text(root, "capacityWeight")
        if capacity in ("", "0", "0.0"):
            issues.append(
                f"ServiceChannel '{name}': capacityWeight is missing or 0. "
                "Each service channel must have a capacity weight > 0 so work items "
                "consume agent capacity correctly (recommended: Case=5, Chat=3, Voice=10)."
            )

        # Check: Related entity type (Salesforce object) should be set
        related_entity = _get_text(root, "relatedEntityType")
        if not related_entity:
            issues.append(
                f"ServiceChannel '{name}': relatedEntityType is not set. "
                "Every Service Channel must reference a Salesforce object (e.g., Case, "
                "ChatTranscript) to define what type of work items it routes."
            )

    return issues


def check_presence_configurations(manifest_dir: Path) -> list[str]:
    """Check PresenceConfiguration metadata for common issues."""
    issues: list[str] = []

    presence_configs = _find_xml_files(manifest_dir, "*.presenceConfiguration")
    if not presence_configs:
        presence_configs = _find_xml_files(manifest_dir, "*.PresenceConfiguration")

    if not presence_configs:
        return issues

    for pc_path in presence_configs:
        root = _parse_xml_safe(pc_path)
        if root is None:
            issues.append(f"Cannot parse PresenceConfiguration XML: {pc_path.name}")
            continue

        name = pc_path.stem or str(pc_path)

        # Check: Capacity should be set and > 0
        capacity = _get_text(root, "capacity")
        if capacity in ("", "0", "0.0"):
            issues.append(
                f"PresenceConfiguration '{name}': capacity is missing or 0. "
                "Set a positive capacity value (e.g., 10) to define the agent workload ceiling."
            )

        # Check: At least one service channel should be configured
        # (look for servicePresenceStatusChannels or assigned channels)
        channels_found = False
        for child in root:
            local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if "channel" in local.lower() or "Channel" in local:
                channels_found = True
                break

        if not channels_found:
            issues.append(
                f"PresenceConfiguration '{name}': no Service Channels detected in configuration. "
                "Agents assigned to this Presence Configuration will not receive any work items. "
                "Add at least one Service Channel to the configuration."
            )

    return issues


def check_presence_statuses(manifest_dir: Path) -> list[str]:
    """Check PresenceUserConfig / PresenceStatus metadata for common issues."""
    issues: list[str] = []

    # Presence statuses may be in PresenceUserConfig or custom metadata
    status_files = _find_xml_files(manifest_dir, "*.presenceUserConfig")
    if not status_files:
        status_files = _find_xml_files(manifest_dir, "*.PresenceUserConfig")

    # Also check for presenceStatus files
    status_files += _find_xml_files(manifest_dir, "*.presenceStatus")

    if not status_files:
        return issues

    for ps_path in status_files:
        root = _parse_xml_safe(ps_path)
        if root is None:
            issues.append(f"Cannot parse Presence Status/Config XML: {ps_path.name}")
            continue

        name = ps_path.stem or str(ps_path)

        # Check: Status type should be set to a known value
        status_type = _get_text(root, "statusType") or _get_text(root, "optionType")
        if status_type:
            valid_status_types = {"Online", "Busy", "OnBreak"}
            if status_type not in valid_status_types:
                issues.append(
                    f"PresenceStatus '{name}': statusType '{status_type}' is not a standard "
                    f"value. Expected one of: {', '.join(sorted(valid_status_types))}."
                )

    return issues


def check_for_apex_routing_triggers(manifest_dir: Path) -> list[str]:
    """Warn if Apex triggers appear to be setting Case.OwnerId directly (routing anti-pattern)."""
    issues: list[str] = []

    trigger_files = _find_xml_files(manifest_dir, "*.trigger")
    # Also scan .cls files in triggers/ directory
    trigger_files += list(manifest_dir.rglob("triggers/*.cls"))

    for trigger_path in trigger_files:
        try:
            content = trigger_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Look for OwnerId assignment patterns on Case records in triggers
        # This is a heuristic — not all OwnerId sets are wrong, but in routing context they are
        if (
            "OwnerId" in content
            and "Case" in content
            and ("insert" in content.lower() or "update" in content.lower())
            and "Queue" not in content  # Setting to a Queue ID is fine
        ):
            issues.append(
                f"Apex trigger '{trigger_path.name}' may be setting Case.OwnerId directly "
                "to a User record for routing purposes. This bypasses Omni-Channel capacity "
                "enforcement and agent availability checks. Use Routing Configurations and "
                "queue-based assignment instead. Review this trigger before enabling Omni-Channel."
            )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_omni_channel_routing_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_routing_configurations(manifest_dir))
    issues.extend(check_service_channels(manifest_dir))
    issues.extend(check_presence_configurations(manifest_dir))
    issues.extend(check_presence_statuses(manifest_dir))
    issues.extend(check_for_apex_routing_triggers(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_omni_channel_routing_setup(manifest_dir)

    if not issues:
        print("No Omni-Channel routing setup issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
