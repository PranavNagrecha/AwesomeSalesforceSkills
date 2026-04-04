#!/usr/bin/env python3
"""Checker script for Einstein Bots to Agentforce Migration skill.

Inspects a Salesforce metadata project directory for common issues
that arise during Einstein Bot to Agentforce migrations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_bots_to_agentforce_migration.py [--help]
    python3 check_einstein_bots_to_agentforce_migration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Einstein Bot to Agentforce "
            "migration issues: missing GenAiPlannerBundle, absent Topics or Actions, "
            "and bot metadata without agent metadata."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Metadata helpers
# ---------------------------------------------------------------------------

def find_files_by_suffix(root: Path, suffix: str) -> list[Path]:
    """Recursively find all files with the given suffix under root."""
    return sorted(root.rglob(f"*{suffix}"))


def find_files_by_name_fragment(root: Path, fragment: str) -> list[Path]:
    """Recursively find files whose name contains the given fragment (case-insensitive)."""
    fragment_lower = fragment.lower()
    return sorted(p for p in root.rglob("*") if fragment_lower in p.name.lower())


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_manifest_dir_exists(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
    elif not manifest_dir.is_dir():
        issues.append(f"Manifest path is not a directory: {manifest_dir}")
    return issues


def check_bot_files_exist(manifest_dir: Path) -> list[str]:
    """An Agentforce agent requires Bot and BotVersion metadata."""
    issues: list[str] = []
    bot_files = find_files_by_suffix(manifest_dir, ".bot-meta.xml")
    bot_version_files = find_files_by_suffix(manifest_dir, ".botVersion-meta.xml")

    if not bot_files:
        issues.append(
            "No .bot-meta.xml files found. "
            "An Agentforce agent requires Bot metadata. "
            "Ensure the agent metadata is included in this project."
        )
    else:
        print(f"  Bot files found: {len(bot_files)}")
        for f in bot_files:
            print(f"    {f.relative_to(manifest_dir)}")

    if not bot_version_files:
        issues.append(
            "No .botVersion-meta.xml files found. "
            "An Agentforce agent requires a BotVersion metadata component."
        )
    else:
        print(f"  BotVersion files found: {len(bot_version_files)}")

    return issues


def check_genai_planner_bundle_exists(manifest_dir: Path) -> list[str]:
    """GenAiPlannerBundle distinguishes an Agentforce agent from a chatbot."""
    issues: list[str] = []
    # GenAiPlannerBundle metadata uses .genAiPlannerBundle-meta.xml suffix
    planner_bundle_files = find_files_by_suffix(manifest_dir, ".genAiPlannerBundle-meta.xml")
    # Also check for legacy GenAiPlanner (API v60-63)
    legacy_planner_files = find_files_by_suffix(manifest_dir, ".genAiPlanner-meta.xml")

    if not planner_bundle_files and not legacy_planner_files:
        issues.append(
            "No GenAiPlannerBundle or GenAiPlanner metadata found. "
            "Without GenAiPlannerBundle, the Bot is a classic chatbot, not an Agentforce agent. "
            "The full agent bundle requires: Bot, BotVersion, GenAiPlannerBundle, "
            "GenAiPlugin (Topics), and GenAiFunction (Actions). "
            "Use GenAiPlannerBundle for API v64+."
        )
    else:
        if planner_bundle_files:
            print(f"  GenAiPlannerBundle files found: {len(planner_bundle_files)}")
        if legacy_planner_files:
            print(
                f"  GenAiPlanner (legacy) files found: {len(legacy_planner_files)} "
                "(consider upgrading to GenAiPlannerBundle for API v64+)"
            )

    return issues


def check_topics_exist(manifest_dir: Path) -> list[str]:
    """An Agentforce agent must have at least one Topic (GenAiPlugin)."""
    issues: list[str] = []
    topic_files = find_files_by_suffix(manifest_dir, ".genAiPlugin-meta.xml")

    if not topic_files:
        issues.append(
            "No GenAiPlugin (Topic) metadata found. "
            "An Agentforce agent requires at least one Topic. "
            "Migrated bot dialogs should be represented as Topics — "
            "each Topic needs a clear LLM-routing description, not just the dialog name."
        )
    else:
        print(f"  Topic (GenAiPlugin) files found: {len(topic_files)}")
        for f in topic_files:
            print(f"    {f.relative_to(manifest_dir)}")

    return issues


def check_actions_exist(manifest_dir: Path) -> list[str]:
    """An Agentforce agent should have at least one Action (GenAiFunction)."""
    issues: list[str] = []
    action_files = find_files_by_suffix(manifest_dir, ".genAiFunction-meta.xml")

    if not action_files:
        issues.append(
            "No GenAiFunction (Action) metadata found. "
            "An Agentforce agent needs Actions to perform work. "
            "If migrating from a bot, dialog steps that perform data lookups or updates "
            "must be implemented as Actions backed by Flows or Apex. "
            "The 'Create AI Agent from Bot' tool generates Action placeholders — "
            "these must be implemented with real logic before activation."
        )
    else:
        print(f"  Action (GenAiFunction) files found: {len(action_files)}")

    return issues


def check_bot_without_planner(manifest_dir: Path) -> list[str]:
    """Warn if Bot metadata is present but GenAiPlannerBundle is absent."""
    issues: list[str] = []
    bot_files = find_files_by_suffix(manifest_dir, ".bot-meta.xml")
    planner_bundle_files = find_files_by_suffix(manifest_dir, ".genAiPlannerBundle-meta.xml")
    legacy_planner_files = find_files_by_suffix(manifest_dir, ".genAiPlanner-meta.xml")

    if bot_files and not planner_bundle_files and not legacy_planner_files:
        issues.append(
            "Bot metadata found but no GenAiPlannerBundle metadata found. "
            "Deploying Bot + BotVersion without GenAiPlannerBundle produces a classic chatbot, "
            "not an Agentforce agent. The agent will respond but will not perform LLM-based "
            "reasoning or route to Topics. "
            "Add GenAiPlannerBundle to the deployment package."
        )

    return issues


def check_for_legacy_bot_indicators(manifest_dir: Path) -> list[str]:
    """Look for indicators that this might be a Classic/Legacy bot rather than an Agentforce agent."""
    issues: list[str] = []

    # BotDialog metadata indicates a Classic or Enhanced bot dialog structure
    # (vs GenAiPlugin for Agentforce Topics)
    dialog_files = find_files_by_name_fragment(manifest_dir, "BotDialog")
    topic_files = find_files_by_suffix(manifest_dir, ".genAiPlugin-meta.xml")

    if dialog_files and not topic_files:
        issues.append(
            f"BotDialog metadata found ({len(dialog_files)} file(s)) but no GenAiPlugin (Topic) "
            "metadata found. This appears to be a Classic or Enhanced Bot project without "
            "Agentforce Topics. If migrating to Agentforce, each dialog must be represented "
            "as a Topic (GenAiPlugin) with a clear LLM-routing description."
        )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_migration_readiness(manifest_dir: Path) -> list[str]:
    """Run all migration readiness checks and return a list of issue strings."""
    issues: list[str] = []

    existence_issues = check_manifest_dir_exists(manifest_dir)
    if existence_issues:
        return existence_issues

    print("\n--- Bot Metadata ---")
    issues.extend(check_bot_files_exist(manifest_dir))

    print("\n--- Agentforce Agent Metadata ---")
    issues.extend(check_genai_planner_bundle_exists(manifest_dir))
    issues.extend(check_topics_exist(manifest_dir))
    issues.extend(check_actions_exist(manifest_dir))

    print("\n--- Migration Consistency ---")
    issues.extend(check_bot_without_planner(manifest_dir))
    issues.extend(check_for_legacy_bot_indicators(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    print(f"Checking Einstein Bot to Agentforce migration metadata in: {manifest_dir.resolve()}")

    issues = check_migration_readiness(manifest_dir)

    print()
    if not issues:
        print("No migration issues found.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"ISSUE {i}: {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
