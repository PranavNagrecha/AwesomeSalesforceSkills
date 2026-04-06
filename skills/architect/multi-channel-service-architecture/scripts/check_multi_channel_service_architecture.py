#!/usr/bin/env python3
"""Checker script for Multi Channel Service Architecture skill.

Checks org metadata or configuration relevant to multi-channel service
architecture: Omni-Channel Service Channels, capacity weights, Email-to-Case,
Messaging, and legacy Live Agent references.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_multi_channel_service_architecture.py [--help]
    python3 check_multi_channel_service_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Multi Channel Service Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find files with a given suffix."""
    results: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(suffix):
                results.append(Path(dirpath) / fname)
    return results


def _parse_xml_safe(filepath: Path) -> ET.Element | None:
    """Parse XML, returning None on failure."""
    try:
        tree = ET.parse(filepath)
        return tree.getroot()
    except (ET.ParseError, OSError):
        return None


def check_legacy_live_agent_references(manifest_dir: Path) -> list[str]:
    """Detect references to legacy Live Agent objects in Flows, Apex, and LWC."""
    issues: list[str] = []
    legacy_patterns = [
        re.compile(r"\bLiveChatTranscript\b"),
        re.compile(r"\bLiveChatButton\b"),
        re.compile(r"\bLiveAgentSession\b"),
        re.compile(r"\bLive\s*Agent\b", re.IGNORECASE),
    ]
    scan_suffixes = (".cls", ".trigger", ".flow-meta.xml", ".js", ".html")

    for suffix in scan_suffixes:
        for filepath in _find_files(manifest_dir, suffix):
            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for pattern in legacy_patterns:
                if pattern.search(content):
                    issues.append(
                        f"Legacy Live Agent reference found in {filepath.relative_to(manifest_dir)}: "
                        f"pattern '{pattern.pattern}'. Migrate to Messaging for In-App/Web."
                    )
                    break  # One issue per file is enough
    return issues


def check_service_channel_capacity_weights(manifest_dir: Path) -> list[str]:
    """Check ServiceChannel metadata for missing or zero capacity weights."""
    issues: list[str] = []
    channel_files = _find_files(manifest_dir, ".serviceChannel-meta.xml")

    if not channel_files:
        # Not necessarily an issue — metadata may not be retrieved
        return issues

    for filepath in channel_files:
        root = _parse_xml_safe(filepath)
        if root is None:
            issues.append(f"Could not parse Service Channel metadata: {filepath.name}")
            continue

        # Check for capacity weight — namespace-agnostic tag search
        capacity_el = None
        for el in root.iter():
            if el.tag.endswith("relatedEntityCapacityWeight") or el.tag.endswith("capacityWeight"):
                capacity_el = el
                break

        if capacity_el is not None:
            try:
                weight = int(capacity_el.text or "0")
                if weight == 0:
                    issues.append(
                        f"Service Channel '{filepath.stem.replace('.serviceChannel-meta', '')}' has "
                        f"capacity weight of 0. This means unlimited work items — likely a misconfiguration."
                    )
            except ValueError:
                pass

    return issues


def check_email_to_case_config(manifest_dir: Path) -> list[str]:
    """Check for Email-to-Case configuration presence."""
    issues: list[str] = []
    # Look for EmailServicesFunction or EmailToCaseRoutingAddress metadata
    email_files = _find_files(manifest_dir, ".emailServicesFunction-meta.xml")
    routing_files = _find_files(manifest_dir, ".emailToCaseRoutingAddress-meta.xml")

    # If we find email service functions but no routing addresses, flag it
    if email_files and not routing_files:
        issues.append(
            "Email Services Functions found but no Email-to-Case routing addresses detected. "
            "Verify Email-to-Case is configured if email is a supported service channel."
        )
    return issues


def check_omni_channel_presence_configs(manifest_dir: Path) -> list[str]:
    """Check Presence Configuration for potential multi-channel issues."""
    issues: list[str] = []
    presence_files = _find_files(manifest_dir, ".presenceConfig-meta.xml")

    for filepath in presence_files:
        root = _parse_xml_safe(filepath)
        if root is None:
            continue

        # Check if capacity is set
        capacity_el = None
        for el in root.iter():
            if el.tag.endswith("capacity"):
                capacity_el = el
                break

        if capacity_el is not None:
            try:
                capacity = int(capacity_el.text or "0")
                if capacity < 1:
                    issues.append(
                        f"Presence Configuration '{filepath.stem}' has capacity < 1. "
                        f"Agents with this config cannot receive work."
                    )
            except ValueError:
                pass

    return issues


def check_multi_channel_service_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_legacy_live_agent_references(manifest_dir))
    issues.extend(check_service_channel_capacity_weights(manifest_dir))
    issues.extend(check_email_to_case_config(manifest_dir))
    issues.extend(check_omni_channel_presence_configs(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_multi_channel_service_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
