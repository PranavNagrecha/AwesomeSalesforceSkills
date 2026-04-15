#!/usr/bin/env python3
"""Checker script for AI Adoption Change Management skill.

Inspects a Salesforce metadata manifest directory for signals that indicate
an AI feature deployment without appropriate adoption management artifacts.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ai_adoption_change_management.py [--help]
    python3 check_ai_adoption_change_management.py --manifest-dir path/to/metadata
    python3 check_ai_adoption_change_management.py --manifest-dir . --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata manifest for missing AI adoption "
            "change management artifacts (Feedback API, adoption metrics, "
            "trust communication markers)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def _check_agentforce_present(manifest_dir: Path) -> list[str]:
    """Detect Agentforce / Einstein feature metadata without feedback config."""
    issues: list[str] = []

    # Look for bot or agent metadata — signals an AI feature is deployed
    bot_files = list(manifest_dir.rglob("*.bot-meta.xml")) + list(manifest_dir.rglob("*.bot"))
    agent_files = list(manifest_dir.rglob("*.aiAssistantDefinition*"))
    ai_feature_files = bot_files + agent_files

    if not ai_feature_files:
        return issues  # No AI features detected — checks not applicable

    # Check for a feedback configuration file or known feedback-related keyword
    feedback_markers = list(manifest_dir.rglob("*feedback*")) + list(
        manifest_dir.rglob("*Feedback*")
    )

    if ai_feature_files and not feedback_markers:
        issues.append(
            "AI feature metadata detected (bot/agent definitions) but no feedback "
            "configuration files found. Ensure the Feedback API is enabled on all "
            "AI surfaces and that Agentforce Analytics Data 360 dashboards are "
            "configured before go-live. See references/gotchas.md #1."
        )

    return issues


def _check_adoption_plan_artifacts(manifest_dir: Path) -> list[str]:
    """Look for common adoption plan document markers in the project root."""
    issues: list[str] = []

    # These checks are heuristic — they look for adoption plan documents
    # in a project directory that typically sits alongside a metadata folder.
    project_root = manifest_dir.parent
    candidate_dirs = [manifest_dir, project_root]

    adoption_keywords = ["levers", "adoption-plan", "ai-adoption", "change-management"]
    found_adoption_doc = False

    for search_dir in candidate_dirs:
        for keyword in adoption_keywords:
            matches = list(search_dir.rglob(f"*{keyword}*"))
            if matches:
                found_adoption_doc = True
                break
        if found_adoption_doc:
            break

    bot_files = list(manifest_dir.rglob("*.bot-meta.xml")) + list(manifest_dir.rglob("*.bot"))
    agent_files = list(manifest_dir.rglob("*.aiAssistantDefinition*"))

    if (bot_files or agent_files) and not found_adoption_doc:
        issues.append(
            "AI feature metadata found but no adoption plan document detected "
            "(expected a file with 'levers', 'adoption-plan', 'ai-adoption', or "
            "'change-management' in its name). Before deploying Agentforce features, "
            "complete a LEVERS gap analysis and confirm 4+ levers are actively engaged."
        )

    return issues


def _check_bot_metadata_for_feedback(manifest_dir: Path) -> list[str]:
    """Check bot/agent XML for feedback-related configuration."""
    issues: list[str] = []

    bot_xml_files = list(manifest_dir.rglob("*.bot-meta.xml"))

    for bot_file in bot_xml_files:
        try:
            content = bot_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Heuristic: feedback typically referenced as feedbackEnabled or FeedbackApi
        feedback_pattern = re.compile(r"feedback", re.IGNORECASE)
        if not feedback_pattern.search(content):
            issues.append(
                f"Bot metadata '{bot_file.name}' does not appear to reference feedback "
                "configuration. Verify the Feedback API (thumbs-up/down + reason text) "
                "is enabled on this agent. Without it, adoption signal is limited to "
                "usage volume only. See SKILL.md — Core Concepts: Feedback API."
            )

    return issues


def _check_for_trust_communication_template(manifest_dir: Path) -> list[str]:
    """Warn if an AI feature is present but no trust comms template is found."""
    issues: list[str] = []

    agent_files = (
        list(manifest_dir.rglob("*.bot-meta.xml"))
        + list(manifest_dir.rglob("*.bot"))
        + list(manifest_dir.rglob("*.aiAssistantDefinition*"))
    )

    if not agent_files:
        return issues

    trust_keywords = ["trust", "transparency", "job-security", "communication-plan"]
    project_root = manifest_dir.parent

    found_trust_doc = False
    for search_dir in [manifest_dir, project_root]:
        for kw in trust_keywords:
            matches = list(search_dir.rglob(f"*{kw}*"))
            if matches:
                found_trust_doc = True
                break
        if found_trust_doc:
            break

    if not found_trust_doc:
        issues.append(
            "AI feature metadata detected but no trust or transparency communication "
            "artifact found. An executive-authored trust communication addressing the "
            "black-box problem must be delivered before go-live, not after. "
            "See references/gotchas.md #5 and references/examples.md."
        )

    return issues


def _check_metrics_baseline_defined(manifest_dir: Path) -> list[str]:
    """Check for a metrics baseline document alongside the deployment."""
    issues: list[str] = []

    agent_files = (
        list(manifest_dir.rglob("*.bot-meta.xml"))
        + list(manifest_dir.rglob("*.bot"))
        + list(manifest_dir.rglob("*.aiAssistantDefinition*"))
    )

    if not agent_files:
        return issues

    metrics_keywords = [
        "metrics", "adoption-metrics", "acceptance-rate", "data360", "agentforce-analytics"
    ]
    project_root = manifest_dir.parent

    found_metrics_doc = False
    for search_dir in [manifest_dir, project_root]:
        for kw in metrics_keywords:
            matches = list(search_dir.rglob(f"*{kw}*"))
            if matches:
                found_metrics_doc = True
                break
        if found_metrics_doc:
            break

    if not found_metrics_doc:
        issues.append(
            "AI feature metadata detected but no adoption metrics baseline document "
            "found. Agentforce Analytics Data 360 dashboards and target metrics "
            "(invocation rate, acceptance rate, feedback participation rate) must be "
            "defined before go-live, not post-launch. See SKILL.md — Decision Guidance."
        )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_ai_adoption_change_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Each returned string is a concrete, actionable issue with a reference
    to the relevant skill guidance.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(_check_agentforce_present(manifest_dir))
    issues.extend(_check_adoption_plan_artifacts(manifest_dir))
    issues.extend(_check_bot_metadata_for_feedback(manifest_dir))
    issues.extend(_check_for_trust_communication_template(manifest_dir))
    issues.extend(_check_metrics_baseline_defined(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_ai_adoption_change_management(manifest_dir)

    if args.json:
        print(json.dumps({"issues": issues, "count": len(issues)}, indent=2))
        return 1 if issues else 0

    if not issues:
        print("No AI adoption change management issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
