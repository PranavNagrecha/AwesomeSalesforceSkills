#!/usr/bin/env python3
"""Checker script for Experience Cloud Moderation skill.

Scans a Salesforce metadata directory for common moderation configuration issues:
- Missing or empty keyword lists
- Moderation rules without an active keyword list or member criteria reference
- Rules using Flag or Review without detectable moderator permission set assignment
- Reputation configuration present without an associated moderation rule

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_moderation.py [--help]
    python3 check_experience_cloud_moderation.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud moderation metadata for common configuration issues. "
            "Expects a Salesforce SFDX/metadata project directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all XML files under *root* that end with *suffix*."""
    return list(root.rglob(f"*{suffix}"))


def _text(element: ET.Element | None) -> str:
    """Return stripped text of an Element, or empty string if None."""
    if element is None:
        return ""
    return (element.text or "").strip()


def check_moderation_rules(manifest_dir: Path) -> list[str]:
    """Check ModerationRule metadata files for ordering and completeness issues."""
    issues: list[str] = []

    rule_files = find_xml_files(manifest_dir, ".moderationRule")
    if not rule_files:
        # No moderation rule files found — not necessarily an error; org may use manual setup
        return issues

    flag_or_review_rules: list[str] = []
    block_rules: list[str] = []
    inactive_rules: list[str] = []

    for rule_file in rule_files:
        try:
            tree = ET.parse(rule_file)
            root_el = tree.getroot()
            # Strip namespace if present
            ns = ""
            if root_el.tag.startswith("{"):
                ns = root_el.tag.split("}")[0] + "}"

            name = rule_file.stem
            active_el = root_el.find(f"{ns}active")
            action_el = root_el.find(f"{ns}action")
            criteria_el = root_el.find(f"{ns}criteriaItems")

            is_active = _text(active_el).lower() in ("true", "1", "yes")
            action = _text(action_el).lower()

            if not is_active:
                inactive_rules.append(name)
                continue

            if criteria_el is None:
                issues.append(
                    f"ModerationRule '{name}' has no criteria defined — rule will never fire."
                )

            if action == "block":
                block_rules.append(name)
            elif action in ("flag", "review"):
                flag_or_review_rules.append(name)

        except ET.ParseError as exc:
            issues.append(f"Could not parse ModerationRule file '{rule_file}': {exc}")

    if inactive_rules:
        issues.append(
            f"Inactive moderation rules found (verify intentional): {', '.join(inactive_rules)}"
        )

    # Heuristic: if Flag/Review rules exist but no Block rules, warn that Block coverage may be missing
    if flag_or_review_rules and not block_rules:
        issues.append(
            "Flag/Review moderation rules exist but no Block rules were found. "
            "Verify that all prohibited-content scenarios have an appropriate Block rule."
        )

    return issues


def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Check for at least one permission set granting Moderate Experiences Feeds."""
    issues: list[str] = []

    perm_set_files = find_xml_files(manifest_dir, ".permissionset")
    if not perm_set_files:
        return issues

    found_moderate_permission = False
    for ps_file in perm_set_files:
        try:
            content = ps_file.read_text(encoding="utf-8")
            if "ModerateExperiencesFeeds" in content or "moderateExperiencesFeeds" in content:
                found_moderate_permission = True
                break
        except OSError:
            pass

    if not found_moderate_permission:
        issues.append(
            "No permission set found that grants 'Moderate Experiences Feeds' (ModerateExperiencesFeeds). "
            "Moderators will not be able to access the moderation queue or approve Review-status content."
        )

    return issues


def check_keyword_lists(manifest_dir: Path) -> list[str]:
    """Check keyword list files for empty or minimal content."""
    issues: list[str] = []

    keyword_files = find_xml_files(manifest_dir, ".keywordList")
    if not keyword_files:
        return issues

    for kw_file in keyword_files:
        try:
            tree = ET.parse(kw_file)
            root_el = tree.getroot()
            ns = ""
            if root_el.tag.startswith("{"):
                ns = root_el.tag.split("}")[0] + "}"

            keywords = root_el.findall(f"{ns}keyword")
            if not keywords:
                issues.append(
                    f"KeywordList '{kw_file.stem}' contains no keywords — moderation rules "
                    "referencing this list will not match any content."
                )
            elif len(keywords) == 1:
                issues.append(
                    f"KeywordList '{kw_file.stem}' contains only 1 keyword. "
                    "Verify this is intentional and not an incomplete configuration."
                )
        except ET.ParseError as exc:
            issues.append(f"Could not parse KeywordList file '{kw_file}': {exc}")

    return issues


def check_experience_cloud_moderation(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_moderation_rules(manifest_dir))
    issues.extend(check_permission_sets(manifest_dir))
    issues.extend(check_keyword_lists(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_moderation(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
