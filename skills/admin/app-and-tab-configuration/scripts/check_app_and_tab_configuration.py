#!/usr/bin/env python3
"""Checker script for App and Tab Configuration skill.

Scans a Salesforce metadata directory for common Lightning app and tab
configuration problems documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_app_and_tab_configuration.py [--manifest-dir path/to/metadata]

Checks performed:
  1. Lightning apps that have no profiles or permission sets assigned (invisible apps).
  2. CustomApplication entries that have navItems but no matching CustomTab definition.
  3. Apps that declare utility items — emits a reminder to test on mobile.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Lightning app and tab metadata for common "
            "configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata source (sfdx format or mdapi format). "
             "Default: current directory.",
    )
    return parser.parse_args()


def find_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all XML files matching *suffix* under *root*."""
    return list(root.rglob(f"*{suffix}"))


def get_text(element: ET.Element, tag: str) -> str:
    child = element.find(_tag(tag))
    return child.text.strip() if child is not None and child.text else ""


def check_apps(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    app_files = find_xml_files(manifest_dir, ".app-meta.xml")
    if not app_files:
        # Try mdapi format: applications/*.app
        app_files = find_xml_files(manifest_dir, ".app")

    if not app_files:
        return issues  # No app metadata found; nothing to check.

    # Collect known tab names from CustomTab metadata
    tab_names: set[str] = set()
    for tab_file in find_xml_files(manifest_dir, ".tab-meta.xml") + find_xml_files(manifest_dir, ".tab"):
        tab_names.add(tab_file.stem.replace("-meta", ""))

    for app_file in app_files:
        try:
            tree = ET.parse(app_file)
        except ET.ParseError as exc:
            issues.append(f"[{app_file.name}] XML parse error: {exc}")
            continue

        root_el = tree.getroot()
        app_label = get_text(root_el, "label") or app_file.stem

        # Check 1: App type is Lightning but has no profile/permset visibility entries.
        app_type = get_text(root_el, "appPreferences")  # simplified; actual varies
        profile_items = root_el.findall(_tag("profileActionOverrides")) + \
                        root_el.findall(_tag("userCustomizations"))
        # Heuristic: if there are navItems but no actionOverrides referencing profiles,
        # the app may not be visible to anyone except System Administrator.
        nav_items = root_el.findall(_tag("navItems"))
        if nav_items and not profile_items:
            issues.append(
                f"[{app_label}] App has navigation items but no explicit profile "
                "visibility configuration detected. Verify that the correct profiles "
                "have 'Visible in App Launcher' enabled via App Manager in Setup."
            )

        # Check 2: Nav items that reference tabs not found in local metadata.
        for nav_item in nav_items:
            item_name = get_text(nav_item, "name")
            if item_name and "." not in item_name and item_name not in tab_names:
                # Skip standard objects (they don't have tab files in sfdx source)
                # Only flag items that look like custom tab API names
                if item_name.endswith("__c") or item_name.endswith("__x"):
                    issues.append(
                        f"[{app_label}] Nav item '{item_name}' looks like a custom "
                        "tab but no matching .tab metadata file was found locally. "
                        "Ensure the CustomTab is included in the deployment package."
                    )

        # Check 3: App has utilityItems — remind about mobile limitation.
        utility_items = root_el.findall(_tag("utilityItems"))
        if utility_items:
            issues.append(
                f"[{app_label}] REMINDER: This app has {len(utility_items)} utility "
                "bar item(s). Utility bars are NOT visible in the Salesforce mobile "
                "app. Verify that mobile users have an alternative workflow for any "
                "utility-bar-only features (e.g., CTI softphone)."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}")
        return 1

    issues = check_apps(manifest_dir)

    if not issues:
        print("OK: No Lightning app or tab configuration issues detected.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    # Reminders are informational; only return non-zero for hard issues.
    hard_issues = [i for i in issues if not i.startswith("[") or "REMINDER" not in i]
    return 1 if any("REMINDER" not in i for i in issues if "ERROR" in i or "Nav item" in i) else 0


if __name__ == "__main__":
    sys.exit(main())
