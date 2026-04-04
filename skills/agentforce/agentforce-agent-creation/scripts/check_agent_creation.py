#!/usr/bin/env python3
"""Checker script for Agentforce Agent Creation skill.

Inspects a Salesforce metadata directory and reports issues related to
Agentforce agent configuration: missing required metadata layers, inactive
agent states, missing agent user references, incomplete topic/action sets,
and unsafe permission patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agent_creation.py [--help]
    python3 check_agent_creation.py --manifest-dir path/to/metadata
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
            "Check Agentforce agent metadata for common configuration issues. "
            "Pass a Salesforce metadata project root via --manifest-dir."
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
    """Return all files matching a glob pattern under root."""
    return sorted(root.rglob(pattern))


def parse_xml_text(path: Path, tag: str) -> str | None:
    """Return the text of the first matching tag in an XML file, or None."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # Strip namespace if present
        for elem in root.iter():
            if elem.tag.endswith(f"}}{tag}") or elem.tag == tag:
                return (elem.text or "").strip() or None
    except ET.ParseError:
        pass
    return None


def parse_xml_all_text(path: Path, tag: str) -> list[str]:
    """Return text of all matching tags in an XML file."""
    results: list[str] = []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        for elem in root.iter():
            local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if local == tag and elem.text:
                results.append(elem.text.strip())
    except ET.ParseError:
        pass
    return results


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_bot_files_exist(manifest_dir: Path) -> list[str]:
    """An agent requires Bot and BotVersion metadata."""
    issues: list[str] = []
    bot_files = find_files(manifest_dir, "*.bot-meta.xml")
    botversion_files = find_files(manifest_dir, "*.botVersion-meta.xml")

    if not bot_files:
        issues.append(
            "No .bot-meta.xml files found. An Agentforce agent requires a Bot metadata component."
        )
    if not botversion_files:
        issues.append(
            "No .botVersion-meta.xml files found. An Agentforce agent requires a BotVersion component."
        )
    return issues


def check_planner_bundle_exists(manifest_dir: Path) -> list[str]:
    """Agent reasoning requires GenAiPlannerBundle (API v64+) or GenAiPlanner (v60-63)."""
    issues: list[str] = []
    bundle_files = find_files(manifest_dir, "*.genAiPlannerBundle-meta.xml")
    legacy_planner_files = find_files(manifest_dir, "*.genAiPlanner-meta.xml")

    if not bundle_files and not legacy_planner_files:
        issues.append(
            "No GenAiPlannerBundle or GenAiPlanner metadata found. "
            "Without this, the Bot is a basic chatbot, not an Agentforce agent. "
            "Use GenAiPlannerBundle for API v64+."
        )
    if legacy_planner_files and not bundle_files:
        issues.append(
            "GenAiPlanner metadata found but no GenAiPlannerBundle. "
            "GenAiPlanner is deprecated as of API v64. "
            "Consider migrating to GenAiPlannerBundle for current releases."
        )
    return issues


def check_topics_exist(manifest_dir: Path) -> list[str]:
    """An agent should have at least one GenAiPlugin (topic)."""
    issues: list[str] = []
    plugin_files = find_files(manifest_dir, "*.genAiPlugin-meta.xml")
    if not plugin_files:
        issues.append(
            "No GenAiPlugin (topic) metadata found. "
            "An agent with no topics cannot route or execute tasks. "
            "Add at least one topic before activation."
        )
    return issues


def check_actions_exist(manifest_dir: Path) -> list[str]:
    """An agent should have at least one GenAiFunction (action)."""
    issues: list[str] = []
    function_files = find_files(manifest_dir, "*.genAiFunction-meta.xml")
    if not function_files:
        issues.append(
            "No GenAiFunction (action) metadata found. "
            "Topics without actions cannot complete tasks. "
            "Add at least one action before activation."
        )
    return issues


def check_bot_active_status(manifest_dir: Path) -> list[str]:
    """Warn if any Bot definition is not set to Active."""
    issues: list[str] = []
    bot_files = find_files(manifest_dir, "*.bot-meta.xml")
    for bot_file in bot_files:
        status = parse_xml_text(bot_file, "status")
        if status and status.lower() not in ("active",):
            issues.append(
                f"{bot_file.name}: Agent status is '{status}' — not Active. "
                "Users cannot interact with an agent that is not in Active state. "
                "Remember: activation does not carry between environments; activate manually in each target org."
            )
    return issues


def check_api_name_patterns(manifest_dir: Path) -> list[str]:
    """Warn if bot API names look like placeholders or temp names."""
    issues: list[str] = []
    suspicious_fragments = ("test", "temp", "v1", "v2", "v3", "draft", "placeholder", "sample")
    bot_files = find_files(manifest_dir, "*.bot-meta.xml")
    for bot_file in bot_files:
        stem = bot_file.stem.replace(".bot-meta", "").lower()
        for fragment in suspicious_fragments:
            if fragment in stem:
                issues.append(
                    f"{bot_file.name}: API Name '{bot_file.stem}' contains '{fragment}'. "
                    "Agent API Names are immutable after creation. "
                    "Verify this is the intended permanent name."
                )
                break
    return issues


def check_permission_sets_not_sysadmin(manifest_dir: Path) -> list[str]:
    """Warn if any permission set referenced for an agent grants System Administrator-level access."""
    issues: list[str] = []
    ps_files = find_files(manifest_dir, "*.permissionset-meta.xml")
    for ps_file in ps_files:
        # Check if the permission set has 'einstein' or 'agent' in the name
        stem_lower = ps_file.stem.lower()
        if "einstein" not in stem_lower and "agent" not in stem_lower:
            continue
        # Look for userPermissions that suggest admin-level access
        admin_perms = ["ModifyAllData", "ViewAllData", "ManageUsers"]
        granted = parse_xml_all_text(ps_file, "name")
        for perm in admin_perms:
            if perm in granted:
                issues.append(
                    f"{ps_file.name}: Permission set contains '{perm}'. "
                    "Agent user permission sets should be scoped narrowly. "
                    "Avoid granting broad data permissions to the EinsteinServiceAgent User."
                )
    return issues


def check_topic_has_classification_description(manifest_dir: Path) -> list[str]:
    """Warn if topic files have empty or missing classification descriptions."""
    issues: list[str] = []
    plugin_files = find_files(manifest_dir, "*.genAiPlugin-meta.xml")
    for plugin_file in plugin_files:
        desc = parse_xml_text(plugin_file, "description")
        if not desc:
            issues.append(
                f"{plugin_file.name}: GenAiPlugin (topic) has no description. "
                "Topics without classification descriptions will produce unreliable routing. "
                "Add a clear scope statement describing when this topic activates and what it does not cover."
            )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_agent_creation(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    issues.extend(check_bot_files_exist(manifest_dir))
    issues.extend(check_planner_bundle_exists(manifest_dir))
    issues.extend(check_topics_exist(manifest_dir))
    issues.extend(check_actions_exist(manifest_dir))
    issues.extend(check_bot_active_status(manifest_dir))
    issues.extend(check_api_name_patterns(manifest_dir))
    issues.extend(check_permission_sets_not_sysadmin(manifest_dir))
    issues.extend(check_topic_has_classification_description(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_agent_creation(manifest_dir)

    if not issues:
        print("No Agentforce agent creation issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
