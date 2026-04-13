#!/usr/bin/env python3
"""Checker script for Conversational AI Architecture skill.

Checks org metadata or configuration relevant to Conversational AI Architecture.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_conversational_ai_architecture.py [--help]
    python3 check_conversational_ai_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Maximum recommended topics per Agentforce agent before routing accuracy degrades.
MAX_TOPICS_PER_AGENT = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Conversational AI Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_metadata_files(manifest_dir: Path, suffix: str) -> list[Path]:
    """Return all files under manifest_dir that end with the given suffix."""
    return list(manifest_dir.rglob(f"*{suffix}"))


def check_conversational_ai_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks:
    1. Whether AgentTopic metadata files are present.
    2. Whether EinsteinBot metadata files are present.
    3. If both exist, whether transfer actions connecting them are present.
    4. Whether any Agentforce agent has more than MAX_TOPICS_PER_AGENT topics (scope too broad).
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # --- Check 1: Locate AgentTopic metadata files ---
    # Salesforce deploys Agentforce topic configuration as AgentTopic metadata.
    # File pattern: <TopicName>.agentTopic-meta.xml
    agent_topic_files = find_metadata_files(manifest_dir, ".agentTopic-meta.xml")
    has_agent_topics = len(agent_topic_files) > 0

    if not has_agent_topics:
        issues.append(
            "No AgentTopic metadata files found (*.agentTopic-meta.xml). "
            "If this org uses Agentforce, at least one AgentTopic should be present in the manifest."
        )
    else:
        # --- Check 4: Warn if topic count is too high ---
        # Group topics by their parent agent by inspecting directory structure.
        # AgentTopic files are typically co-located under an agent-specific directory.
        # We use a simple heuristic: count topics per parent directory.
        topics_by_parent: dict[str, list[Path]] = {}
        for topic_file in agent_topic_files:
            parent_key = str(topic_file.parent)
            topics_by_parent.setdefault(parent_key, []).append(topic_file)

        for parent_dir, topics in topics_by_parent.items():
            if len(topics) > MAX_TOPICS_PER_AGENT:
                issues.append(
                    f"Agent directory '{parent_dir}' contains {len(topics)} AgentTopic files "
                    f"(threshold: {MAX_TOPICS_PER_AGENT}). A large topic count on a single agent "
                    "degrades Atlas Reasoning Engine routing accuracy and maintainability. "
                    "Consider splitting into multiple specialized agents with an orchestrator."
                )

    # --- Check 2: Locate EinsteinBot metadata files ---
    # Einstein Bot configuration is deployed as Bot metadata.
    # File pattern: <BotName>.bot-meta.xml
    bot_files = find_metadata_files(manifest_dir, ".bot-meta.xml")
    has_einstein_bots = len(bot_files) > 0

    # --- Check 3: If both Einstein Bot and Agentforce are present, check for transfer actions ---
    if has_einstein_bots and has_agent_topics:
        # Look for EinsteinBot dialog step files that reference a transfer-to-agent action.
        # Transfer step files use the .botVersion-meta.xml or embedded dialog XML.
        # We search for the string "TransferToAgent" or "transferToAgentforce" in bot metadata files.
        transfer_action_found = False
        bot_meta_files = find_metadata_files(manifest_dir, ".bot-meta.xml")
        bot_version_files = find_metadata_files(manifest_dir, ".botVersion-meta.xml")

        all_bot_files = bot_meta_files + bot_version_files
        for bot_file in all_bot_files:
            try:
                content = bot_file.read_text(encoding="utf-8", errors="replace")
                # Check for transfer action indicators in bot metadata XML.
                # Salesforce bot transfer actions contain "transferToAgent" type references.
                if (
                    "transferToAgent" in content
                    or "TransferToAgent" in content
                    or "agentforce" in content.lower()
                ):
                    transfer_action_found = True
                    break
            except OSError:
                # Skip files that cannot be read.
                continue

        if not transfer_action_found:
            issues.append(
                "Einstein Bot metadata and AgentTopic metadata are both present, "
                "but no transfer action connecting them was detected in bot metadata files. "
                "If these systems are intended to work together, ensure the Einstein Bot has a "
                "'Transfer to Agent' action configured to hand off sessions to the Agentforce agent queue. "
                "Also verify that transfer attributes are explicitly mapped to carry session context "
                "(verified account ID, intent category, conversation summary) to the Agentforce agent."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_conversational_ai_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
