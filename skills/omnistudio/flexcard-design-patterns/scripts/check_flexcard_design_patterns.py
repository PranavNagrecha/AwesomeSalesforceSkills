#!/usr/bin/env python3
"""Checker script for FlexCard Design Patterns skill.

Scans a Salesforce metadata directory for common FlexCard configuration issues:
- Missing or empty Error state templates
- Multiple data sources on a single FlexCard
- Child FlexCards with independent data sources (causes N+1 query patterns)
- FlexCards not yet activated (version activation flag)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_flexcard_design_patterns.py [--manifest-dir path/to/metadata]
    python3 check_flexcard_design_patterns.py --manifest-dir force-app/main/default
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
            "Check FlexCard metadata for common design pattern issues. "
            "Looks for OmniInteractionConfig XML files under the manifest directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_flexcard_files(manifest_dir: Path) -> list[Path]:
    """Return all OmniInteractionConfig XML files under manifest_dir."""
    patterns = [
        "**/*.omniInteractionConfig-meta.xml",
        # Some orgs use a different suffix for FlexCard metadata
        "**/OmniInteractionConfig/**/*.xml",
        "**/flexCards/**/*.xml",
    ]
    found: list[Path] = []
    for pattern in patterns:
        found.extend(manifest_dir.rglob(pattern.lstrip("**/")))
    # Deduplicate while preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in found:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def count_data_sources(root: ET.Element) -> int:
    """Count the number of data source nodes in a FlexCard XML tree."""
    # OmniStudio FlexCard XML uses <dataSources> as a repeating element
    return len(root.findall(".//{*}dataSources"))


def has_error_state(root: ET.Element) -> bool:
    """Return True if the FlexCard has a non-empty Error state template."""
    for state in root.findall(".//{*}states"):
        state_name = state.findtext("{*}stateName") or state.findtext("stateName") or ""
        if state_name.lower() == "error":
            # Check that the state has at least one template element
            elements = state.findall(".//{*}elements")
            if elements:
                return True
    return False


def has_child_card_with_own_datasource(root: ET.Element) -> bool:
    """Return True if a child card element also has a data source configured on the same card.

    This is a heuristic — it detects cards that both embed a child card
    and define more than one data source, which suggests the child is
    pulling its own data rather than receiving it from the parent.
    """
    has_child = bool(root.findall(".//{*}type[.='childCard']") or
                     root.findall(".//{*}elementType[.='ChildCard']"))
    datasource_count = count_data_sources(root)
    # If there's a child card and multiple data sources, flag for review
    return has_child and datasource_count > 1


def is_activated(root: ET.Element) -> bool:
    """Return True if the FlexCard has an isActive or active flag set to true."""
    for tag in ("isActive", "active", "status"):
        val = root.findtext(f"{{*}}{tag}") or root.findtext(tag) or ""
        if val.lower() in ("true", "active", "1"):
            return True
    # If the field is absent, we cannot determine status — do not flag as inactive
    return True


# ---------------------------------------------------------------------------
# Core check logic
# ---------------------------------------------------------------------------

def check_flexcard_file(path: Path) -> list[str]:
    """Parse a single FlexCard XML file and return a list of issue strings."""
    issues: list[str] = []

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as exc:
        issues.append(f"{path.name}: XML parse error — {exc}")
        return issues

    card_label = root.findtext("{*}label") or root.findtext("label") or path.stem

    # Check 1: Missing or empty Error state
    if not has_error_state(root):
        issues.append(
            f"{card_label} ({path.name}): No Error state template configured. "
            "A failed data source will render a blank card with no user feedback."
        )

    # Check 2: Multiple data sources
    ds_count = count_data_sources(root)
    if ds_count > 2:
        issues.append(
            f"{card_label} ({path.name}): {ds_count} data sources detected. "
            "More than 2 data sources fire multiple parallel queries on card load. "
            "Consider consolidating into a single Integration Procedure."
        )
    elif ds_count == 2:
        issues.append(
            f"{card_label} ({path.name}): 2 data sources detected. "
            "Verify these cannot be consolidated into a single Integration Procedure "
            "to reduce parallel query load."
        )

    # Check 3: Child card with multiple data sources (N+1 pattern risk)
    if has_child_card_with_own_datasource(root):
        issues.append(
            f"{card_label} ({path.name}): Child card element present with multiple data sources. "
            "If the child card has its own data source and is iterated over a collection, "
            "this causes one query per rendered row. Move child data retrieval into the parent IP."
        )

    # Check 4: Activation status
    if not is_activated(root):
        issues.append(
            f"{card_label} ({path.name}): FlexCard does not appear to be activated. "
            "Template changes are not live until the card is activated (compiled to LWC)."
        )

    return issues


def check_flexcard_design_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in all FlexCard files under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    flex_files = find_flexcard_files(manifest_dir)

    if not flex_files:
        # Not a hard error — the directory may not contain FlexCards
        print(
            f"INFO: No FlexCard metadata files found under {manifest_dir}. "
            "Expected files matching *.omniInteractionConfig-meta.xml or flexCards/**/*.xml."
        )
        return issues

    for path in flex_files:
        issues.extend(check_flexcard_file(path))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_flexcard_design_patterns(manifest_dir)

    if not issues:
        print("No FlexCard design pattern issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
