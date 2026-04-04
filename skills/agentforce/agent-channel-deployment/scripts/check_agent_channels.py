#!/usr/bin/env python3
"""Checker script for Agentforce Agent Channel Deployment skill.

Inspects a Salesforce metadata directory and reports findings related to
Agentforce channel deployment: EmbeddedServiceConfig, MessagingChannel,
BotChannelAssociation, and Connected App OAuth scope presence.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agent_channels.py [--help]
    python3 check_agent_channels.py --manifest-dir path/to/metadata
    python3 check_agent_channels.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Agentforce channel deployment artifacts. "
            "Lists EmbeddedServiceConfig and MessagingChannel components and reports "
            "common configuration issues. Pass a Salesforce metadata project root "
            "via --manifest-dir."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root, sorted."""
    return sorted(root.rglob(pattern))


def parse_xml_text(path: Path, tag: str) -> str | None:
    """Return the text of the first matching tag in an XML file, or None."""
    try:
        tree = ET.parse(path)
        root_elem = tree.getroot()
        for elem in root_elem.iter():
            local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if local == tag and elem.text:
                return elem.text.strip()
    except ET.ParseError:
        pass
    return None


def parse_xml_all_text(path: Path, tag: str) -> list[str]:
    """Return the text content of all elements matching tag in an XML file."""
    results: list[str] = []
    try:
        tree = ET.parse(path)
        root_elem = tree.getroot()
        for elem in root_elem.iter():
            local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if local == tag and elem.text:
                results.append(elem.text.strip())
    except ET.ParseError:
        pass
    return results


# ---------------------------------------------------------------------------
# Discovery: list channel artifacts
# ---------------------------------------------------------------------------

def list_embedded_service_configs(manifest_dir: Path) -> list[Path]:
    """Return all EmbeddedServiceConfig metadata files found."""
    # EmbeddedServiceConfig files use the pattern: <name>.embeddedServiceConfig-meta.xml
    return find_files(manifest_dir, "*.embeddedServiceConfig-meta.xml")


def list_messaging_channels(manifest_dir: Path) -> list[Path]:
    """Return all MessagingChannel metadata files found."""
    # MessagingChannel files: <name>.messagingChannel-meta.xml
    return find_files(manifest_dir, "*.messagingChannel-meta.xml")


def list_bot_channel_associations(manifest_dir: Path) -> list[Path]:
    """Return all BotChannelAssociation metadata files found."""
    return find_files(manifest_dir, "*.botChannelAssociation-meta.xml")


def list_connected_apps(manifest_dir: Path) -> list[Path]:
    """Return all Connected App metadata files found."""
    return find_files(manifest_dir, "*.connectedApp-meta.xml")


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_embedded_service_configs(manifest_dir: Path) -> list[str]:
    """List found EmbeddedServiceConfig files and check for common issues."""
    issues: list[str] = []
    esd_files = list_embedded_service_configs(manifest_dir)

    if not esd_files:
        # Not necessarily an issue — project may use a different channel type
        return issues

    print(f"\nEmbeddedServiceConfig components found ({len(esd_files)}):")
    for f in esd_files:
        label = parse_xml_text(f, "masterLabel") or f.stem
        site = parse_xml_text(f, "site") or "(no site configured)"
        print(f"  - {f.stem}  |  label: {label}  |  site: {site}")

        # Check if a site is configured
        if site == "(no site configured)":
            issues.append(
                f"{f.name}: No site configured in EmbeddedServiceConfig. "
                "For Experience Cloud deployments, a published site must be associated. "
                "For external-site-only deployments, verify CORS Allowed Origins are set in Setup."
            )

    return issues


def check_messaging_channels(manifest_dir: Path) -> list[str]:
    """List found MessagingChannel files and check for common issues."""
    issues: list[str] = []
    mc_files = list_messaging_channels(manifest_dir)

    if not mc_files:
        return issues

    print(f"\nMessagingChannel components found ({len(mc_files)}):")
    for f in mc_files:
        label = parse_xml_text(f, "masterLabel") or f.stem
        channel_type = parse_xml_text(f, "messagingChannelType") or "(unknown type)"
        print(f"  - {f.stem}  |  label: {label}  |  type: {channel_type}")

        # Check that channel type is a recognized Agentforce-compatible type
        recognized_types = {
            "EmbeddedMessaging",
            "Slack",
            "FacebookMessenger",
            "WhatsApp",
            "AppleMessagesForBusiness",
            "InApp",
        }
        if channel_type not in recognized_types and channel_type != "(unknown type)":
            issues.append(
                f"{f.name}: MessagingChannel type '{channel_type}' is not a recognized "
                "Agentforce-compatible channel type. Verify the channel type is correct."
            )

    return issues


def check_bot_channel_associations(manifest_dir: Path) -> list[str]:
    """List BotChannelAssociation files and check for agent references."""
    issues: list[str] = []
    bca_files = list_bot_channel_associations(manifest_dir)

    if not bca_files:
        # May not be present in all project structures; note but do not error
        return issues

    print(f"\nBotChannelAssociation components found ({len(bca_files)}):")
    for f in bca_files:
        bot_ref = parse_xml_text(f, "bot") or "(no bot reference)"
        channel_ref = parse_xml_text(f, "channel") or "(no channel reference)"
        print(f"  - {f.stem}  |  bot: {bot_ref}  |  channel: {channel_ref}")

        if bot_ref == "(no bot reference)":
            issues.append(
                f"{f.name}: BotChannelAssociation has no bot reference. "
                "This association cannot route to an agent without a bot reference."
            )
        if channel_ref == "(no channel reference)":
            issues.append(
                f"{f.name}: BotChannelAssociation has no channel reference. "
                "This association is incomplete."
            )

    return issues


def check_connected_apps_for_chatbot_scope(manifest_dir: Path) -> list[str]:
    """Warn if Connected Apps with 'agent' or 'chatbot' in the name lack the chatbot_api scope."""
    issues: list[str] = []
    ca_files = list_connected_apps(manifest_dir)

    agent_ca_files = [
        f for f in ca_files
        if any(kw in f.stem.lower() for kw in ("agent", "chatbot", "agentforce", "einstein"))
    ]

    if not agent_ca_files:
        return issues

    print(f"\nAgent-related Connected App components found ({len(agent_ca_files)}):")
    for f in agent_ca_files:
        scopes = parse_xml_all_text(f, "oauthScopes")
        scope_str = ", ".join(scopes) if scopes else "(no scopes listed)"
        print(f"  - {f.stem}  |  scopes: {scope_str}")

        if scopes and "chatbot_api" not in scopes:
            issues.append(
                f"{f.name}: Connected App does not include the 'chatbot_api' OAuth scope. "
                "The Agentforce Agent REST API requires the 'chatbot_api' scope in addition "
                "to the standard 'api' scope. Without it, session creation returns HTTP 403. "
                "Add 'chatbot_api' (labeled 'Agentforce API' in the UI) to the Connected App."
            )

    return issues


def check_bot_files_exist(manifest_dir: Path) -> list[str]:
    """Check that at least one Bot metadata file exists (agent prerequisite)."""
    issues: list[str] = []
    bot_files = find_files(manifest_dir, "*.bot-meta.xml")

    if not bot_files:
        issues.append(
            "No .bot-meta.xml files found. Channel deployment requires an Agentforce agent "
            "(Bot metadata component). Ensure the agent metadata is included in this project."
        )
    else:
        print(f"\nBot (agent) metadata components found ({len(bot_files)}):")
        for f in bot_files:
            status = parse_xml_text(f, "status") or "(status unknown)"
            print(f"  - {f.stem}  |  status: {status}")
            if status.lower() not in ("active",) and status != "(status unknown)":
                issues.append(
                    f"{f.name}: Agent status is '{status}' — not Active. "
                    "Channel deployments require the associated agent to be Active. "
                    "Activate the agent in Setup > Agentforce Agents before publishing channels."
                )

    return issues


# ---------------------------------------------------------------------------
# Summary reporter
# ---------------------------------------------------------------------------

def report_summary(manifest_dir: Path) -> None:
    """Print a summary of all channel-related metadata found."""
    esd = list_embedded_service_configs(manifest_dir)
    mc = list_messaging_channels(manifest_dir)
    bca = list_bot_channel_associations(manifest_dir)
    ca = list_connected_apps(manifest_dir)
    bots = find_files(manifest_dir, "*.bot-meta.xml")

    print("\n--- Agentforce Channel Deployment Metadata Summary ---")
    print(f"  Bot (agent) definitions:        {len(bots)}")
    print(f"  EmbeddedServiceConfig:          {len(esd)}")
    print(f"  MessagingChannel:               {len(mc)}")
    print(f"  BotChannelAssociation:          {len(bca)}")
    print(f"  Connected Apps (all):           {len(ca)}")
    print("------------------------------------------------------")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_agent_channels(manifest_dir: Path) -> list[str]:
    """Run all channel deployment checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    report_summary(manifest_dir)

    issues.extend(check_bot_files_exist(manifest_dir))
    issues.extend(check_embedded_service_configs(manifest_dir))
    issues.extend(check_messaging_channels(manifest_dir))
    issues.extend(check_bot_channel_associations(manifest_dir))
    issues.extend(check_connected_apps_for_chatbot_scope(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    print(f"Checking Agentforce channel deployment metadata in: {manifest_dir.resolve()}")

    issues = check_agent_channels(manifest_dir)

    print()
    if not issues:
        print("No Agentforce channel deployment issues found.")
        return 0

    print(f"Issues found ({len(issues)}):")
    for issue in issues:
        print(f"\n  ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
