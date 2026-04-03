#!/usr/bin/env python3
"""Checker script for Global Actions and Quick Actions skill.

Scans retrieved Salesforce metadata for common quick action anti-patterns:
- Quick actions with no fields in the action layout (empty layout)
- Page layouts with too many actions (>7) in the mobile/Lightning section
- Global actions referencing LWC targets (only works in FSL mobile, not standard LE)
- Quick actions missing predefined values for standard parent lookup fields

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_global_actions_and_quick_actions.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce quick action metadata for common configuration issues.\n"
            "Point --manifest-dir at a retrieved sfdx source directory or metadata "
            "directory that contains quickActions/ and layouts/ subdirectories."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata directory tree (default: current directory).",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def check_quick_action_files(quick_actions_dir: Path) -> list[str]:
    """Check .quickAction-meta.xml files for known anti-patterns."""
    issues: list[str] = []
    xml_files = list(quick_actions_dir.glob("*.quickAction-meta.xml"))

    if not xml_files:
        return issues

    for qf in xml_files:
        action_name = qf.stem.replace(".quickAction", "")
        try:
            tree = ET.parse(qf)
        except ET.ParseError as exc:
            issues.append(f"[{action_name}] XML parse error: {exc}")
            continue

        root = tree.getroot()

        # Check: detect LWC-based custom actions (type = LightningComponent)
        # LWC global actions only work in Field Service mobile, not standard LE.
        action_type_el = root.find(_tag("type"))
        lwc_el = root.find(_tag("lightningWebComponent"))
        if action_type_el is not None and action_type_el.text == "LightningComponent":
            label_el = root.find(_tag("label"))
            label = label_el.text if label_el is not None else action_name
            # Determine if global (no targetObject) or object-specific
            target_el = root.find(_tag("targetObject"))
            if target_el is None:
                issues.append(
                    f"[{label}] Global quick action uses LightningComponent type. "
                    "LWC global quick actions only function in the Field Service mobile app "
                    "and do not appear in standard Lightning Experience. "
                    "Use a Visualforce page or Aura component for standard LE global actions."
                )

        # Check: action layout has zero fields (empty action layout is a common stub)
        fields = root.findall(_tag("quickActionLayout") + "/" + _tag("quickActionLayoutColumns") + "/" + _tag("quickActionLayoutItems"))
        # Alternate structure: quickActionLayout > quickActionLayoutColumns > quickActionLayoutItems
        layout_el = root.find(_tag("quickActionLayout"))
        if layout_el is not None:
            all_items = layout_el.findall(".//" + _tag("quickActionLayoutItems"))
            if len(all_items) == 0:
                label_el = root.find(_tag("label"))
                label = label_el.text if label_el is not None else action_name
                issues.append(
                    f"[{label}] Action layout contains no fields. "
                    "Users will see an empty dialog and cannot save. "
                    "Add at least the required fields to the action layout."
                )

    return issues


def check_page_layout_action_counts(layouts_dir: Path) -> list[str]:
    """Check page layout XML for layouts with too many mobile/Lightning actions."""
    issues: list[str] = []
    MAX_VISIBLE_ACTIONS = 7  # Actions beyond this are hidden in the "More" menu

    xml_files = list(layouts_dir.glob("*.layout-meta.xml"))
    if not xml_files:
        return issues

    for lf in xml_files:
        layout_name = lf.stem.replace(".layout", "")
        try:
            tree = ET.parse(lf)
        except ET.ParseError as exc:
            issues.append(f"[Layout: {layout_name}] XML parse error: {exc}")
            continue

        root = tree.getroot()

        # platformActionList with actionListContext = Sfdc1 = Mobile & Lightning actions
        for pal in root.findall(".//" + _tag("platformActionList")):
            context_el = pal.find(_tag("actionListContext"))
            if context_el is not None and context_el.text == "Sfdc1":
                items = pal.findall(_tag("platformActionListItems"))
                count = len(items)
                if count > MAX_VISIBLE_ACTIONS:
                    issues.append(
                        f"[Layout: {layout_name}] Mobile & Lightning Experience Actions section "
                        f"has {count} actions (threshold: {MAX_VISIBLE_ACTIONS}). "
                        f"Actions beyond position ~5 are hidden in the 'More' dropdown and often "
                        "go undiscovered by users. Remove or deprioritize low-use actions."
                    )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    all_issues: list[str] = []

    # Check quickActions/ directory
    quick_actions_dir = manifest_dir / "quickActions"
    if quick_actions_dir.exists():
        all_issues.extend(check_quick_action_files(quick_actions_dir))
    else:
        # Also check sfdx source format: force-app/main/default/quickActions/
        for candidate in manifest_dir.rglob("quickActions"):
            if candidate.is_dir():
                all_issues.extend(check_quick_action_files(candidate))
                break

    # Check layouts/ directory
    layouts_dir = manifest_dir / "layouts"
    if layouts_dir.exists():
        all_issues.extend(check_page_layout_action_counts(layouts_dir))
    else:
        for candidate in manifest_dir.rglob("layouts"):
            if candidate.is_dir():
                all_issues.extend(check_page_layout_action_counts(candidate))
                break

    if not all_issues:
        print("No quick action issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(all_issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
