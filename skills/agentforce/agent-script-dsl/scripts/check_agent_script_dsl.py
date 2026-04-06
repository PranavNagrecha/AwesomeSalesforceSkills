#!/usr/bin/env python3
"""Checker script for Agent Script DSL skill.

Inspects a Salesforce DX metadata directory for common issues related to
Agentforce agent metadata (GenAiPlugin, GenAiPlannerBundle, BotVersion, .agent files).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agent_script_dsl.py [--help]
    python3 check_agent_script_dsl.py --manifest-dir path/to/metadata
    python3 check_agent_script_dsl.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Agentforce Agent Script DSL metadata for common issues:\n"
            "  - Missing metadata bundle members (GenAiPlugin, GenAiPlannerBundle, BotVersion)\n"
            "  - Vague or empty topic descriptions in GenAiPlugin files\n"
            "  - Missing plannerInstructions in GenAiPlannerBundle\n"
            "  - .agent files present without corresponding XML metadata\n"
            "  - API version mismatch hints"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce DX metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_manifest_dir_exists(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
    elif not manifest_dir.is_dir():
        issues.append(f"Path is not a directory: {manifest_dir}")
    return issues


def find_files_by_suffix(root: Path, suffix: str) -> list[Path]:
    """Recursively find all files matching a given suffix under root."""
    return sorted(root.rglob(f"*{suffix}"))


def check_genai_plugin_descriptions(manifest_dir: Path) -> list[str]:
    """Check GenAiPlugin XML files for missing or suspiciously short topic descriptions."""
    issues: list[str] = []
    plugin_files = find_files_by_suffix(manifest_dir, ".genAiPlugin-meta.xml")

    if not plugin_files:
        # No plugins found — not necessarily an error (might be in a different layout)
        return issues

    for plugin_file in plugin_files:
        try:
            content = plugin_file.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"Could not read {plugin_file}: {exc}")
            continue

        # Look for <description> inside <GenAiPlugin>
        desc_matches = re.findall(r"<description>(.*?)</description>", content, re.DOTALL)

        if not desc_matches:
            issues.append(
                f"GenAiPlugin '{plugin_file.name}' has no <description> element. "
                "Topic descriptions are required for LLM routing — the planner uses this "
                "text to classify user utterances to the correct topic."
            )
            continue

        for desc in desc_matches:
            desc_stripped = desc.strip()
            if len(desc_stripped) < 20:
                issues.append(
                    f"GenAiPlugin '{plugin_file.name}' has a very short description "
                    f"({len(desc_stripped)} chars): '{desc_stripped}'. "
                    "Vague topic descriptions cause LLM routing failures. "
                    "Descriptions should clearly articulate what user intents this topic handles."
                )
            elif desc_stripped.lower() in {"todo", "todo: description", "description"}:
                issues.append(
                    f"GenAiPlugin '{plugin_file.name}' description appears to be a placeholder: "
                    f"'{desc_stripped}'. Replace with a specific, natural-language topic description."
                )

    return issues


def check_genai_planner_bundle(manifest_dir: Path) -> list[str]:
    """Check GenAiPlannerBundle XML files for missing planner instructions."""
    issues: list[str] = []
    bundle_files = find_files_by_suffix(manifest_dir, ".genAiPlannerBundle-meta.xml")
    planner_files = find_files_by_suffix(manifest_dir, ".genAiPlanner-meta.xml")

    all_planner_files = bundle_files + planner_files

    for planner_file in all_planner_files:
        try:
            content = planner_file.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"Could not read {planner_file}: {exc}")
            continue

        # Check for plannerInstructions / description element used as system prompt
        has_instructions = (
            "<plannerInstructions>" in content
            or "<description>" in content
        )
        if not has_instructions:
            issues.append(
                f"GenAiPlannerBundle/GenAiPlanner '{planner_file.name}' appears to be missing "
                "planner instructions (system prompt). A missing plannerInstructions block "
                "produces an agent with no persona, constraints, or fallback guidance."
            )

        # Check for suspiciously short instructions
        instr_matches = re.findall(
            r"<plannerInstructions>(.*?)</plannerInstructions>", content, re.DOTALL
        )
        for instr in instr_matches:
            instr_stripped = instr.strip()
            if len(instr_stripped) < 30:
                issues.append(
                    f"GenAiPlannerBundle '{planner_file.name}' has very short "
                    f"plannerInstructions ({len(instr_stripped)} chars). "
                    "Planner instructions should contain a specific persona, constraints, "
                    "and fallback behavior to guide the LLM reasoning engine."
                )

    return issues


def check_bot_version_has_planner_reference(manifest_dir: Path) -> list[str]:
    """Check BotVersion XML files for a GenAiPlannerBundle reference.

    A BotVersion without a planner bundle reference is a legacy Einstein Bot,
    not an Agentforce agent.
    """
    issues: list[str] = []
    bot_version_files = find_files_by_suffix(manifest_dir, ".botVersion-meta.xml")

    for bv_file in bot_version_files:
        try:
            content = bv_file.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"Could not read {bv_file}: {exc}")
            continue

        has_planner_ref = (
            "genAiPlannerBundle" in content
            or "genAiPlanner" in content
        )
        if not has_planner_ref:
            issues.append(
                f"BotVersion '{bv_file.name}' does not reference a GenAiPlannerBundle or "
                "GenAiPlanner. A BotVersion without a planner reference is a legacy Einstein "
                "Bot (FSM-based), not an Agentforce agent. If this is intentional, ignore this "
                "finding. If you expect this to be an Agentforce agent, add the "
                "<genAiPlannerBundle> element."
            )

    return issues


def check_agent_files_have_metadata(manifest_dir: Path) -> list[str]:
    """Check that .agent YAML files have corresponding XML metadata files present."""
    issues: list[str] = []
    agent_files = find_files_by_suffix(manifest_dir, ".agent-meta.xml")
    # Also look for plain .agent files (Salesforce CLI may use either extension)
    agent_files += find_files_by_suffix(manifest_dir, ".agent")

    # Deduplicate by stem
    seen_names: set[str] = set()
    for agent_file in agent_files:
        name = agent_file.stem.replace(".agent", "")
        if name in seen_names:
            continue
        seen_names.add(name)

        # Check that at least one GenAiPlugin exists in the directory tree
        plugin_files = find_files_by_suffix(manifest_dir, ".genAiPlugin-meta.xml")
        if not plugin_files:
            issues.append(
                f"Agent file '{agent_file.name}' found but no GenAiPlugin metadata files "
                "exist in the project. An Agentforce agent requires at least one GenAiPlugin "
                "(topic) to route user requests. Deploy will succeed but the agent will have "
                "no topics and will fall back on every query."
            )

    return issues


def check_sfdx_project_api_version(manifest_dir: Path) -> list[str]:
    """Warn if sfdx-project.json specifies API v63 or lower alongside GenAiPlannerBundle files."""
    issues: list[str] = []

    # Look for sfdx-project.json in or above manifest_dir
    sfdx_project_candidates = list(manifest_dir.rglob("sfdx-project.json"))
    if not sfdx_project_candidates:
        # Try parent directories (common when manifest_dir is force-app/main/default)
        candidate = manifest_dir
        for _ in range(4):
            candidate = candidate.parent
            p = candidate / "sfdx-project.json"
            if p.exists():
                sfdx_project_candidates.append(p)
                break

    if not sfdx_project_candidates:
        return issues

    sfdx_project_file = sfdx_project_candidates[0]
    try:
        content = sfdx_project_file.read_text(encoding="utf-8")
    except OSError:
        return issues

    # Extract apiVersion value
    version_match = re.search(r'"apiVersion"\s*:\s*"?([0-9]+(?:\.[0-9]+)?)"?', content)
    if not version_match:
        return issues

    try:
        api_version = float(version_match.group(1))
    except ValueError:
        return issues

    bundle_files = find_files_by_suffix(manifest_dir, ".genAiPlannerBundle-meta.xml")
    if bundle_files and api_version < 64.0:
        issues.append(
            f"sfdx-project.json specifies apiVersion {api_version} but "
            "GenAiPlannerBundle metadata files are present. GenAiPlannerBundle requires "
            "API v64.0+ (Spring '26). Set apiVersion to 64.0 or higher in sfdx-project.json, "
            "or replace GenAiPlannerBundle with GenAiPlanner (compatible with v60–v63)."
        )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_agent_script_dsl(manifest_dir: Path) -> list[str]:
    """Run all checks and return a flat list of issue strings."""
    issues: list[str] = []

    dir_issues = check_manifest_dir_exists(manifest_dir)
    if dir_issues:
        return dir_issues

    issues.extend(check_genai_plugin_descriptions(manifest_dir))
    issues.extend(check_genai_planner_bundle(manifest_dir))
    issues.extend(check_bot_version_has_planner_reference(manifest_dir))
    issues.extend(check_agent_files_have_metadata(manifest_dir))
    issues.extend(check_sfdx_project_api_version(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_agent_script_dsl(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
