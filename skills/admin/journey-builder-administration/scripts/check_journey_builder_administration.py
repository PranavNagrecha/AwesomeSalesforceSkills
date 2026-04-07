#!/usr/bin/env python3
"""Checker script for Journey Builder Administration skill.

Validates a journey configuration document or metadata directory for common
Journey Builder administration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_journey_builder_administration.py [--help]
    python3 check_journey_builder_administration.py --manifest-dir path/to/metadata
    python3 check_journey_builder_administration.py --journey-doc path/to/journey-config.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Journey Builder Administration configuration documents or metadata "
            "for common issues: missing re-entry settings, misuse of exit criteria, "
            "unpopulated split fields, and version strategy gaps."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce/Marketing Cloud metadata (optional).",
    )
    parser.add_argument(
        "--journey-doc",
        default=None,
        help="Path to a journey configuration markdown document to check (optional).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Checks on a journey configuration document (markdown)
# ---------------------------------------------------------------------------

def check_reentry_policy(text: str) -> list[str]:
    """Warn if re-entry policy is not explicitly addressed."""
    issues: list[str] = []
    reentry_patterns = [
        r"re.?entry",
        r"re-enter",
        r"minimum interval",
        r"entry interval",
    ]
    mentioned = any(re.search(p, text, re.IGNORECASE) for p in reentry_patterns)
    if not mentioned:
        issues.append(
            "Re-entry policy is not mentioned. "
            "Journey Builder allows each contact in a version only once by default. "
            "Explicitly document whether re-entry is enabled and what the minimum interval is."
        )
    return issues


def check_exit_criteria_realtime_claim(text: str) -> list[str]:
    """Flag if the document implies exit criteria are real-time."""
    issues: list[str] = []
    realtime_patterns = [
        r"immediately removed",
        r"instantly exit",
        r"real.?time.*exit criteria",
        r"exit criteria.*real.?time",
        r"exit criteria.*instant",
        r"instant.*exit criteria",
    ]
    for pattern in realtime_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(
                f"Possible real-time exit criteria claim detected (pattern: '{pattern}'). "
                "Exit Criteria in Journey Builder run on a scheduled evaluation cycle "
                "(every 15 minutes by default) — they are NOT real-time. "
                "Update the document to reflect the evaluation lag."
            )
    return issues


def check_goal_defined(text: str) -> list[str]:
    """Warn if no goal definition is present in the document."""
    issues: list[str] = []
    goal_patterns = [
        r"\bgoal\b",
        r"conversion event",
        r"goal condition",
        r"goal path",
    ]
    mentioned = any(re.search(p, text, re.IGNORECASE) for p in goal_patterns)
    if not mentioned:
        issues.append(
            "No goal definition detected in the document. "
            "If this journey tracks a conversion event, a Goal should be configured "
            "to ensure correct Journey Analytics conversion reporting. "
            "If no goal is intentional, document that decision explicitly."
        )
    return issues


def check_version_strategy(text: str) -> list[str]:
    """Warn if version management is not addressed."""
    issues: list[str] = []
    version_patterns = [
        r"new version",
        r"journey version",
        r"version \d",
        r"publish.*version",
        r"immutable",
        r"in.?flight",
    ]
    mentioned = any(re.search(p, text, re.IGNORECASE) for p in version_patterns)
    if not mentioned:
        issues.append(
            "Journey version strategy is not addressed. "
            "Published journey versions are immutable — any change requires a new version. "
            "Document how in-flight contacts will be handled when a new version is created."
        )
    return issues


def check_split_default_arm(text: str) -> list[str]:
    """Warn if decision splits are mentioned without a default arm."""
    issues: list[str] = []
    has_split = bool(re.search(r"decision split|attribute split", text, re.IGNORECASE))
    has_default = bool(re.search(r"default arm|default path|default split", text, re.IGNORECASE))
    if has_split and not has_default:
        issues.append(
            "Decision split is mentioned but no Default arm is documented. "
            "Contacts with null or unmatched attribute values route to the Default arm silently. "
            "Ensure a Default arm activity is configured and document its routing behavior."
        )
    return issues


def check_test_mode_mentioned(text: str) -> list[str]:
    """Warn if test mode is not mentioned for journeys that will go live."""
    issues: list[str] = []
    test_patterns = [r"test mode", r"test contact", r"sandbox.*journey", r"journey.*test"]
    mentioned = any(re.search(p, text, re.IGNORECASE) for p in test_patterns)
    if not mentioned:
        issues.append(
            "Test Mode is not mentioned. "
            "Journey Builder Test Mode should be used to validate split routing, "
            "goal exit behavior, and activity firing before publishing. "
            "Document which scenarios were tested in Test Mode."
        )
    return issues


def check_business_unit_scope(text: str) -> list[str]:
    """Warn if Business Unit scope is not addressed in multi-activity journeys."""
    issues: list[str] = []
    bu_patterns = [r"business unit", r"\bBU\b", r"child BU", r"parent BU"]
    has_activities = bool(
        re.search(r"email activity|sms activity|update contact|api event", text, re.IGNORECASE)
    )
    has_bu = any(re.search(p, text, re.IGNORECASE) for p in bu_patterns)
    if has_activities and not has_bu:
        issues.append(
            "Journey activities are referenced but Business Unit scope is not mentioned. "
            "Journey Builder, entry source Data Extensions, and channel activities must all "
            "exist within the same Marketing Cloud Business Unit. "
            "Confirm BU context, especially in multi-BU enterprise orgs."
        )
    return issues


# ---------------------------------------------------------------------------
# Checks on a metadata directory
# ---------------------------------------------------------------------------

def check_manifest_directory(manifest_dir: Path) -> list[str]:
    """Check a metadata/manifest directory for journey-related configuration files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for any journey configuration files (JSON or XML are common for MC exports)
    journey_files = list(manifest_dir.rglob("*.json")) + list(manifest_dir.rglob("*.xml"))
    if not journey_files:
        issues.append(
            f"No JSON or XML files found in {manifest_dir}. "
            "Journey Builder configuration exports are typically JSON. "
            "Ensure the correct directory is provided."
        )
        return issues

    for jf in journey_files:
        try:
            content = jf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Check for re-entry settings in journey config JSON
        if "reEntry" not in content and "re_entry" not in content and "reentry" not in content.lower():
            # Only flag if this looks like a journey definition file
            if "journeyDefinition" in content or "activities" in content.lower():
                issues.append(
                    f"{jf.name}: Re-entry policy ('reEntry') field not found. "
                    "Verify re-entry is explicitly configured in this journey definition."
                )

        # Check for goal definition
        if "goal" not in content.lower():
            if "journeyDefinition" in content or '"activities"' in content:
                issues.append(
                    f"{jf.name}: No 'goal' definition found. "
                    "If this journey tracks conversions, a goal should be configured."
                )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    # Check journey document if provided
    if args.journey_doc:
        doc_path = Path(args.journey_doc)
        if not doc_path.exists():
            print(f"WARN: Journey document not found: {doc_path}", file=sys.stderr)
            return 1
        text = doc_path.read_text(encoding="utf-8", errors="replace")
        all_issues += check_reentry_policy(text)
        all_issues += check_exit_criteria_realtime_claim(text)
        all_issues += check_goal_defined(text)
        all_issues += check_version_strategy(text)
        all_issues += check_split_default_arm(text)
        all_issues += check_test_mode_mentioned(text)
        all_issues += check_business_unit_scope(text)

    # Check metadata directory if provided
    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        all_issues += check_manifest_directory(manifest_dir)

    # Default: if neither is provided, run a self-check against the skill directory
    if not args.journey_doc and not args.manifest_dir:
        skill_dir = Path(__file__).parent.parent
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            text = skill_md.read_text(encoding="utf-8", errors="replace")
            # Check that the skill document itself follows the patterns
            all_issues += check_exit_criteria_realtime_claim(text)
        else:
            all_issues.append(f"SKILL.md not found at expected path: {skill_md}")

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
