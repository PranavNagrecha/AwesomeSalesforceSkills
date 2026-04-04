#!/usr/bin/env python3
"""Checker script for Enterprise Territory Management skill.

Checks Salesforce metadata files for common ETM configuration issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_enterprise_territory_management.py [--help]
    python3 check_enterprise_territory_management.py --manifest-dir path/to/metadata
    python3 check_enterprise_territory_management.py --manifest-dir force-app/main/default

Checks performed:
  1. Territory count per model (warns if approaching 1,000 default limit)
  2. Territory types defined (required — every territory must have a type)
  3. Assignment rules with IsActive=false (rules that won't auto-run)
  4. Territory2ObjSharingConfig presence (access level for Opps/Contacts)
  5. Territory depth warning (hierarchies deeper than 6 levels)
  6. Territory model state in metadata (flags if multiple Active models present)
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TERRITORY_LIMIT_WARNING = 800   # warn at 80% of the 1,000 default limit
TERRITORY_LIMIT_ERROR = 1000    # hard limit for Enterprise Edition (default)
MAX_RECOMMENDED_DEPTH = 6


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from a tag name."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def get_text(element: ET.Element, child_tag: str) -> str:
    """Return text content of a direct child element, or empty string."""
    for child in element:
        if strip_ns(child.tag) == child_tag:
            return (child.text or "").strip()
    return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_territory_count(manifest_dir: Path) -> list[str]:
    """Warn if territory count per model approaches or exceeds the default limit."""
    issues: list[str] = []
    territory_files = find_files(manifest_dir, "*.territory2")
    # Group by parent directory as a proxy for model (standard Metadata API layout)
    model_counts: dict[str, int] = defaultdict(int)
    for tf in territory_files:
        model_name = tf.parent.name if tf.parent else "unknown"
        model_counts[model_name] += 1

    for model, count in model_counts.items():
        if count >= TERRITORY_LIMIT_ERROR:
            issues.append(
                f"Territory count EXCEEDS default limit: model '{model}' has {count} territories "
                f"(default limit is {TERRITORY_LIMIT_ERROR} for Enterprise Edition). "
                "Contact Salesforce Support to raise the limit for Performance/Unlimited editions."
            )
        elif count >= TERRITORY_LIMIT_WARNING:
            issues.append(
                f"Territory count WARNING: model '{model}' has {count} territories "
                f"(approaching {TERRITORY_LIMIT_ERROR} default limit). "
                "Plan a limit increase request if the model is expected to grow."
            )
    return issues


def check_territory_types_defined(manifest_dir: Path) -> list[str]:
    """Warn if no Territory2Type metadata files are found but territory2 files exist."""
    issues: list[str] = []
    type_files = find_files(manifest_dir, "*.territory2Type")
    if not type_files:
        territory_files = find_files(manifest_dir, "*.territory2")
        if territory_files:
            issues.append(
                "No Territory2Type metadata files found, but territory2 files exist. "
                "Every territory must have a territory type assigned. "
                "Define at least one Territory2Type in your metadata."
            )
    return issues


def check_inactive_assignment_rules(manifest_dir: Path) -> list[str]:
    """Flag assignment rules with isActive=false — they won't auto-run on account changes."""
    issues: list[str] = []
    rule_files = find_files(manifest_dir, "*.accountTerritoryAssignmentRule")
    for rule_file in rule_files:
        root = parse_xml_safe(rule_file)
        if root is None:
            continue
        is_active = get_text(root, "isActive").lower()
        rule_name = get_text(root, "name") or rule_file.stem
        if is_active == "false":
            issues.append(
                f"Assignment rule '{rule_name}' ({rule_file.name}) has isActive=false. "
                "This rule will NOT run automatically when accounts are created or updated. "
                "Set isActive=true if automatic execution is intended, "
                "or manually run assignment rules after deployment."
            )
    return issues


def check_obj_sharing_config(manifest_dir: Path) -> list[str]:
    """Warn if Territory2ObjSharingConfig metadata is absent."""
    issues: list[str] = []
    sharing_files = find_files(manifest_dir, "*.territory2ObjectSharing")
    territory_files = find_files(manifest_dir, "*.territory2")
    if territory_files and not sharing_files:
        issues.append(
            "No Territory2ObjSharingConfig (territory2ObjectSharing) metadata found. "
            "Territory members receive Read access to Accounts by default, but access to "
            "related Opportunities and Contacts is controlled by this metadata. "
            "Verify that Territory2ObjSharingConfig is deployed with the intended access levels "
            "(Read vs Read/Write) for Opportunity and Contact."
        )
    return issues


def check_territory_hierarchy_depth(manifest_dir: Path) -> list[str]:
    """Warn if any territory hierarchy branch exceeds the recommended depth."""
    issues: list[str] = []
    territory_files = find_files(manifest_dir, "*.territory2")
    if not territory_files:
        return issues

    parent_map: dict[str, str] = {}
    territory_names: set[str] = set()

    for tf in territory_files:
        root = parse_xml_safe(tf)
        if root is None:
            continue
        name = get_text(root, "name") or tf.stem
        territory_names.add(name)
        parent = get_text(root, "parentTerritory")
        if parent:
            parent_map[name] = parent

    def compute_depth(name: str, visited: set[str]) -> int:
        if name in visited:
            return 0  # cycle guard
        visited.add(name)
        parent = parent_map.get(name)
        if parent is None:
            return 1
        return 1 + compute_depth(parent, visited)

    deep_territories: list[tuple[str, int]] = []
    for name in territory_names:
        depth = compute_depth(name, set())
        if depth > MAX_RECOMMENDED_DEPTH:
            deep_territories.append((name, depth))

    if deep_territories:
        deep_territories.sort(key=lambda x: x[1], reverse=True)
        examples = ", ".join(f"'{n}' (depth {d})" for n, d in deep_territories[:5])
        issues.append(
            f"Territory hierarchy depth exceeds recommended maximum of {MAX_RECOMMENDED_DEPTH} levels. "
            f"Affected territories: {examples}. "
            "Deep hierarchies increase complexity of forecast rollups and sharing group recalculation. "
            "Consider flattening the hierarchy."
        )
    return issues


def check_multiple_active_models(manifest_dir: Path) -> list[str]:
    """Flag if more than one Territory2Model is marked Active in the metadata."""
    issues: list[str] = []
    model_files = find_files(manifest_dir, "*.territory2Model")
    active_models: list[str] = []
    for mf in model_files:
        root = parse_xml_safe(mf)
        if root is None:
            continue
        state = get_text(root, "state").lower()
        if state == "active":
            model_name = get_text(root, "name") or mf.stem
            active_models.append(model_name)

    if len(active_models) > 1:
        issues.append(
            f"Multiple territory models are marked Active in metadata: {active_models}. "
            "Only one territory model can be Active in Salesforce at any time. "
            "This deployment will fail or produce unexpected behavior. "
            "Ensure exactly one model has state=Active."
        )
    return issues


def check_no_territory_metadata(manifest_dir: Path) -> list[str]:
    """Informational: note if no territory metadata is found at all."""
    issues: list[str] = []
    territory_files = (
        find_files(manifest_dir, "*.territory2")
        + find_files(manifest_dir, "*.territory2Model")
        + find_files(manifest_dir, "*.territory2Type")
    )
    if not territory_files:
        issues.append(
            "No ETM metadata files found (*.territory2, *.territory2Model, *.territory2Type). "
            "If ETM is not deployed via this metadata directory, this check can be ignored. "
            "If ETM should be included in this deployment, verify the metadata directory path."
        )
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    all_issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    all_issues.extend(check_no_territory_metadata(manifest_dir))
    all_issues.extend(check_territory_count(manifest_dir))
    all_issues.extend(check_territory_types_defined(manifest_dir))
    all_issues.extend(check_inactive_assignment_rules(manifest_dir))
    all_issues.extend(check_obj_sharing_config(manifest_dir))
    all_issues.extend(check_territory_hierarchy_depth(manifest_dir))
    all_issues.extend(check_multiple_active_models(manifest_dir))

    return all_issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Enterprise Territory Management metadata for common issues. "
            "Point --manifest-dir at the root of your Salesforce metadata project or "
            "the force-app/main/default directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    print(f"Checking Enterprise Territory Management metadata in: {manifest_dir}\n")

    issues = run_all_checks(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}\n")

    print(f"{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
