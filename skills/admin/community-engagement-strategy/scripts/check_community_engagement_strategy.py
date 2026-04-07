#!/usr/bin/env python3
"""Checker script for Community Engagement Strategy skill.

Checks Salesforce metadata for common community engagement configuration issues:
- Reputation tiers using generic names ("Level N")
- Missing IdeaTheme records in metadata exports
- Missing Ideas tab in navigation metadata

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_community_engagement_strategy.py [--help]
    python3 check_community_engagement_strategy.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud community engagement configuration for common issues. "
            "Looks for generic reputation tier names, missing IdeaTheme metadata, "
            "and missing Ideas tab in navigation XML."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


_GENERIC_TIER_PATTERN = re.compile(r"\bLevel\s+\d+\b", re.IGNORECASE)
_IDEA_THEME_TAG = re.compile(r"<IdeaTheme\b", re.IGNORECASE)
_IDEAS_NAV_TAB = re.compile(r"<label\s*>\s*Ideas\s*</label>", re.IGNORECASE)


def check_reputation_tier_names(manifest_dir: Path) -> list[str]:
    """Warn if any NetworkMember or Reputation metadata uses generic 'Level N' tier names."""
    issues: list[str] = []
    reputation_files = list(manifest_dir.rglob("*.network")) + list(
        manifest_dir.rglob("*Reputation*.xml")
    )
    for f in reputation_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = _GENERIC_TIER_PATTERN.findall(content)
        if matches:
            issues.append(
                f"{f}: Reputation tier uses generic name(s) {matches}. "
                "Replace with role-meaningful tier names (e.g., 'Trusted Expert', 'Legend')."
            )
    return issues


def check_idea_theme_exists(manifest_dir: Path) -> list[str]:
    """Warn if no IdeaTheme metadata is found anywhere in the manifest."""
    issues: list[str] = []
    all_xml = list(manifest_dir.rglob("*.xml"))
    found = False
    for f in all_xml:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if _IDEA_THEME_TAG.search(content):
            found = True
            break
    if not found and any(manifest_dir.rglob("*.xml")):
        issues.append(
            "No IdeaTheme metadata found in manifest. "
            "At least one active IdeaTheme is required for the idea submission UI to appear. "
            "Create an IdeaTheme before opening ideation to members."
        )
    return issues


def check_ideas_tab_in_navigation(manifest_dir: Path) -> list[str]:
    """Warn if navigation metadata exists but does not include an Ideas tab label."""
    issues: list[str] = []
    nav_files = list(manifest_dir.rglob("*Navigation*.xml")) + list(
        manifest_dir.rglob("*nav*.xml")
    )
    for f in nav_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Only check files that look like Experience Builder navigation menus
        if "<navigationMenuItem>" not in content and "<NavigationMenuItem>" not in content:
            continue
        if not _IDEAS_NAV_TAB.search(content):
            issues.append(
                f"{f}: Ideas tab not found in navigation metadata. "
                "Add an Ideas tab via Experience Builder navigation to make ideation visible to members."
            )
    return issues


def check_community_engagement_strategy(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_reputation_tier_names(manifest_dir))
    issues.extend(check_idea_theme_exists(manifest_dir))
    issues.extend(check_ideas_tab_in_navigation(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_community_engagement_strategy(manifest_dir)

    if not issues:
        print("No community engagement configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
