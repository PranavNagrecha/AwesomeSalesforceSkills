#!/usr/bin/env python3
"""Checker script for Messaging and Chat Setup skill.

Inspects Salesforce metadata in a local project directory for common MIAW
(Messaging for In-App and Web) configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_messaging_and_chat_setup.py [--help]
    python3 check_messaging_and_chat_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Messaging for In-App and Web (MIAW) configuration and metadata "
            "for common setup issues."
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

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files under root matching glob pattern."""
    return list(root.rglob(pattern))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Strip XML namespace from a tag string."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def find_text(element: ET.Element, tag: str) -> str | None:
    """Find the text of a direct or namespaced child element."""
    for child in element:
        if strip_ns(child.tag) == tag:
            return (child.text or "").strip()
    return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_embedded_service_deployments(manifest_dir: Path) -> list[str]:
    """Warn about Embedded Service Deployments using legacy Chat type."""
    issues: list[str] = []
    deployment_files = find_files(manifest_dir, "*.embeddedServiceConfig")
    if not deployment_files:
        deployment_files = find_files(manifest_dir, "*.embeddedServiceFlowConfig")

    # Also look for EmbeddedServiceLiveAgent metadata files (legacy)
    legacy_files = find_files(manifest_dir, "*.embeddedServiceLiveAgent")
    for path in legacy_files:
        issues.append(
            f"Legacy Embedded Service Live Agent deployment detected: {path.name}. "
            "MIAW requires an Embedded Service Deployment of type 'Messaging for In-App and Web'. "
            "Legacy Chat deployments route to LiveChatTranscript, not MessagingSession."
        )

    return issues


def check_cors_and_csp_pairing(manifest_dir: Path) -> list[str]:
    """Check that CORS and CSP Trusted Sites are both present (non-empty lists)."""
    issues: list[str] = []

    cors_files = find_files(manifest_dir, "*.corsWhitelistOrigin")
    csp_files = find_files(manifest_dir, "*.cspTrustedSite")

    # Also check package.xml or SFDX source for metadata types
    cors_count = len(cors_files)
    csp_count = len(csp_files)

    if cors_count == 0 and csp_count == 0:
        issues.append(
            "No CORS Trusted Sites or CSP Trusted Sites found in metadata. "
            "MIAW widgets require both CORS (Setup > CORS) and CSP (Setup > CSP Trusted Sites) "
            "entries for every domain where the chat widget is embedded."
        )
    elif cors_count == 0:
        issues.append(
            f"CSP Trusted Sites found ({csp_count}) but no CORS Trusted Sites detected. "
            "MIAW requires both. Add a CORS Trusted Site entry for every widget domain."
        )
    elif csp_count == 0:
        issues.append(
            f"CORS Trusted Sites found ({cors_count}) but no CSP Trusted Sites detected. "
            "MIAW requires both. Add a CSP Trusted Site entry for every widget domain."
        )
    elif cors_count != csp_count:
        issues.append(
            f"CORS Trusted Site count ({cors_count}) does not match "
            f"CSP Trusted Site count ({csp_count}). "
            "Each widget domain should have exactly one entry in both lists. "
            "Review for missing or extra entries."
        )

    return issues


def check_omni_channel_settings(manifest_dir: Path) -> list[str]:
    """Check OmniChannel settings files for capacity model configuration."""
    issues: list[str] = []

    settings_files = find_files(manifest_dir, "OmniChannel.settings-meta.xml")
    if not settings_files:
        # Try non-meta variant
        settings_files = find_files(manifest_dir, "OmniChannel.settings")

    for path in settings_files:
        root = parse_xml_safe(path)
        if root is None:
            issues.append(f"Could not parse Omni-Channel settings file: {path}")
            continue

        capacity_model = find_text(root, "capacityModel")
        if capacity_model and capacity_model.lower() == "tab":
            issues.append(
                f"Omni-Channel capacity model is set to 'Tab' in {path.name}. "
                "For MIAW (asynchronous messaging), Status-Based capacity is strongly recommended. "
                "Tab-Based capacity is unreliable for async sessions that persist across browser reloads."
            )

    return issues


def check_presence_configurations(manifest_dir: Path) -> list[str]:
    """Check Presence Configurations for missing capacity values."""
    issues: list[str] = []

    presence_files = (
        find_files(manifest_dir, "*.presenceConfig-meta.xml")
        + find_files(manifest_dir, "*.presenceConfig")
    )

    for path in presence_files:
        root = parse_xml_safe(path)
        if root is None:
            continue

        capacity = find_text(root, "capacity")
        label = find_text(root, "label") or path.stem

        if capacity is None or capacity == "":
            issues.append(
                f"Presence Configuration '{label}' ({path.name}) has no capacity value set. "
                "Under Status-Based capacity, a numeric capacity is required for agents to accept "
                "Messaging sessions. Set the capacity field to the maximum concurrent sessions per agent."
            )
        else:
            try:
                cap_int = int(capacity)
                if cap_int == 0:
                    issues.append(
                        f"Presence Configuration '{label}' ({path.name}) has capacity set to 0. "
                        "Agents with this configuration will not receive any Messaging sessions."
                    )
            except ValueError:
                issues.append(
                    f"Presence Configuration '{label}' ({path.name}) has a non-numeric capacity value: '{capacity}'."
                )

    return issues


def check_messaging_channels(manifest_dir: Path) -> list[str]:
    """Check Messaging Channel metadata for missing fallback queue or routing config."""
    issues: list[str] = []

    channel_files = (
        find_files(manifest_dir, "*.messagingChannel-meta.xml")
        + find_files(manifest_dir, "*.messagingChannel")
    )

    for path in channel_files:
        root = parse_xml_safe(path)
        if root is None:
            continue

        label = find_text(root, "masterLabel") or find_text(root, "label") or path.stem

        # Check for fallback queue
        fallback_queue = find_text(root, "fallbackQueue") or find_text(root, "routingFallbackQueue")
        if not fallback_queue:
            issues.append(
                f"Messaging Channel '{label}' ({path.name}) has no fallback queue configured. "
                "Without a fallback queue, Omni-Channel Flow failures silently strand sessions "
                "in a 'Waiting' state with no error surfaced to agents or supervisors."
            )

    return issues


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def check_messaging_and_chat_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_embedded_service_deployments(manifest_dir))
    issues.extend(check_cors_and_csp_pairing(manifest_dir))
    issues.extend(check_omni_channel_settings(manifest_dir))
    issues.extend(check_presence_configurations(manifest_dir))
    issues.extend(check_messaging_channels(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_messaging_and_chat_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
