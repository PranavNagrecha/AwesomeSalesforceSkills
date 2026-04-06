#!/usr/bin/env python3
"""Checker script for Knowledge Taxonomy Design skill.

Inspects Salesforce metadata for Knowledge taxonomy issues:
- Data Category Group count and activation limits
- Category hierarchy depth violations (>5 levels)
- Category count per group violations (>100 categories)
- Validation Status configuration consistency

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_knowledge_taxonomy_design.py [--help]
    python3 check_knowledge_taxonomy_design.py --manifest-dir path/to/force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Platform limits from official Salesforce documentation
MAX_ACTIVE_DATA_CATEGORY_GROUPS_DEFAULT = 3
MAX_DATA_CATEGORY_GROUPS_ABSOLUTE = 5
MAX_HIERARCHY_LEVELS = 5
MAX_CATEGORIES_PER_GROUP = 100

# Salesforce metadata directory names
DATA_CATEGORY_DIR = "datacategorygroups"
KNOWLEDGE_SETTINGS_FILE = "Knowledge.settings-meta.xml"
SETTINGS_DIR = "settings"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Knowledge taxonomy metadata for common issues "
            "based on the knowledge-taxonomy-design skill guidance."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Data Category Group analysis
# ---------------------------------------------------------------------------

def _count_category_hierarchy_depth(element: ET.Element, ns: str, current_depth: int = 1) -> int:
    """Recursively count the maximum depth of the category tree."""
    child_categories = element.findall(f"{ns}dataCategories")
    if not child_categories:
        return current_depth
    return max(
        _count_category_hierarchy_depth(child, ns, current_depth + 1)
        for child in child_categories
    )


def _count_all_categories(element: ET.Element, ns: str) -> int:
    """Recursively count all category nodes in the tree."""
    children = element.findall(f"{ns}dataCategories")
    return len(children) + sum(_count_all_categories(c, ns) for c in children)


def check_data_category_groups(manifest_dir: Path) -> list[str]:
    """Check Data Category Group metadata files for taxonomy limit violations."""
    issues: list[str] = []

    datacategory_dir = manifest_dir / DATA_CATEGORY_DIR
    if not datacategory_dir.exists():
        # Try common SFDX project layout
        for candidate in manifest_dir.rglob(DATA_CATEGORY_DIR):
            if candidate.is_dir():
                datacategory_dir = candidate
                break
        else:
            # No data category metadata found — not an error, just not present
            return issues

    group_files = list(datacategory_dir.glob("*.datacategorygroup-meta.xml"))

    if not group_files:
        return issues

    active_groups: list[str] = []
    inactive_groups: list[str] = []

    for group_file in group_files:
        try:
            tree = ET.parse(group_file)
        except ET.ParseError as exc:
            issues.append(f"Cannot parse Data Category Group file {group_file.name}: {exc}")
            continue

        root = tree.getroot()

        # Handle XML namespace
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag[: root.tag.index("}") + 1]

        group_name_el = root.find(f"{ns}label") or root.find(f"{ns}name")
        group_name = group_name_el.text if group_name_el is not None else group_file.stem

        # Check active status
        active_el = root.find(f"{ns}active")
        is_active = active_el is not None and active_el.text.strip().lower() == "true"
        if is_active:
            active_groups.append(group_name)
        else:
            inactive_groups.append(group_name)

        # Gather top-level categories
        top_categories = root.findall(f"{ns}dataCategories")
        total_categories = sum(
            1 + _count_all_categories(cat, ns) for cat in top_categories
        )

        if total_categories > MAX_CATEGORIES_PER_GROUP:
            issues.append(
                f"Data Category Group '{group_name}' has {total_categories} categories, "
                f"exceeding the platform limit of {MAX_CATEGORIES_PER_GROUP}."
            )

        # Check hierarchy depth
        max_depth = max(
            (_count_category_hierarchy_depth(cat, ns) for cat in top_categories),
            default=0,
        )
        if max_depth > MAX_HIERARCHY_LEVELS:
            issues.append(
                f"Data Category Group '{group_name}' has a hierarchy depth of {max_depth} levels, "
                f"exceeding the platform limit of {MAX_HIERARCHY_LEVELS}."
            )
        elif max_depth > 3:
            issues.append(
                f"Data Category Group '{group_name}' has a hierarchy depth of {max_depth} levels. "
                f"Consider flattening to ≤3 levels to improve agent search speed and reduce "
                f"authorship overhead (platform limit is {MAX_HIERARCHY_LEVELS})."
            )

    # Check active group count
    if len(active_groups) > MAX_DATA_CATEGORY_GROUPS_ABSOLUTE:
        issues.append(
            f"Found {len(active_groups)} active Data Category Groups "
            f"({', '.join(active_groups)}), exceeding the absolute maximum of "
            f"{MAX_DATA_CATEGORY_GROUPS_ABSOLUTE}."
        )
    elif len(active_groups) > MAX_ACTIVE_DATA_CATEGORY_GROUPS_DEFAULT:
        issues.append(
            f"Found {len(active_groups)} active Data Category Groups "
            f"({', '.join(active_groups)}). The default Salesforce limit is "
            f"{MAX_ACTIVE_DATA_CATEGORY_GROUPS_DEFAULT} active groups. Verify that a support "
            f"case has been filed and approved to enable more than "
            f"{MAX_ACTIVE_DATA_CATEGORY_GROUPS_DEFAULT} active groups in this org."
        )

    return issues


# ---------------------------------------------------------------------------
# Knowledge Settings analysis
# ---------------------------------------------------------------------------

def check_knowledge_settings(manifest_dir: Path) -> list[str]:
    """Check Knowledge settings metadata for Validation Status configuration."""
    issues: list[str] = []

    settings_dir = manifest_dir / SETTINGS_DIR
    if not settings_dir.exists():
        for candidate in manifest_dir.rglob(SETTINGS_DIR):
            if candidate.is_dir() and (candidate / KNOWLEDGE_SETTINGS_FILE).exists():
                settings_dir = candidate
                break
        else:
            return issues

    settings_file = settings_dir / KNOWLEDGE_SETTINGS_FILE
    if not settings_file.exists():
        return issues

    try:
        tree = ET.parse(settings_file)
    except ET.ParseError as exc:
        issues.append(f"Cannot parse Knowledge settings file: {exc}")
        return issues

    root = tree.getroot()
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag[: root.tag.index("}") + 1]

    # Check Validation Status enabled
    vs_el = root.find(f"{ns}enableValidationStatusField") or root.find(
        f".//{ns}enableValidationStatusField"
    )
    validation_status_enabled = vs_el is not None and vs_el.text.strip().lower() == "true"

    if not validation_status_enabled:
        issues.append(
            "Knowledge Validation Status is not enabled. For KCS-aligned orgs, enabling "
            "Validation Status provides a quality gate between agent-authored (Solve Loop) "
            "and expert-reviewed (Evolve Loop) articles. If KCS is not a requirement, "
            "this warning can be ignored."
        )

    # Check for Knowledge enabled at all
    knowledge_enabled_el = root.find(f"{ns}enableKnowledge") or root.find(
        f".//{ns}enableKnowledge"
    )
    if knowledge_enabled_el is not None and knowledge_enabled_el.text.strip().lower() != "true":
        issues.append(
            "Knowledge is not enabled in Knowledge Settings. All Knowledge taxonomy "
            "design work assumes Knowledge is active."
        )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_knowledge_taxonomy_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_data_category_groups(manifest_dir))
    issues.extend(check_knowledge_settings(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_knowledge_taxonomy_design(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
