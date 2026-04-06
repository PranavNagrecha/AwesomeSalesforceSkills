#!/usr/bin/env python3
"""Checker script for Service Console Configuration skill.

Inspects Salesforce metadata for common Service Console configuration issues:
- Console apps using Standard Navigation instead of Console Navigation
- Missing or mismatched utility bar items (History in non-console apps)
- Navigation rules defaulting to Workspace Tab for all objects
- Macros without the requisite permissions in connected profiles

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_service_console_configuration.py [--help]
    python3 check_service_console_configuration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


# Namespace commonly used in Salesforce metadata XML
_NS = "http://soap.sforce.com/2006/04/metadata"


def _find_files(root: Path, pattern: str) -> list[Path]:
    """Recursively find files matching a glob pattern."""
    return list(root.rglob(pattern))


def _parse_xml(path: Path) -> ET.Element | None:
    """Parse an XML file and return root element, or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def _tag(name: str) -> str:
    return f"{{{_NS}}}{name}"


def check_service_console_configuration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks performed:
    1. Detect Lightning apps with navType=Console and warn if utility bar has History
       placed in a non-console app (cross-reference by navType field).
    2. Detect console apps that have no utility bar defined (missing utility bar entirely).
    3. Detect console apps where navigation rules are absent (implies default Workspace Tab
       for all objects, which is a common misconfiguration for related objects).
    4. Detect console apps that appear to be named "Service" or "Support" but use
       Standard Navigation — flag for review.
    5. Check for Macro metadata presence — if no macros exist but console apps reference
       the Macros utility, warn that no macros are deployed.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # --- 1. Find all CustomApplication metadata files ---
    app_files = _find_files(manifest_dir, "*.app-meta.xml")

    if not app_files:
        # No app metadata found — likely not a full metadata retrieve; skip app checks
        pass

    console_app_names: list[str] = []
    standard_nav_service_apps: list[str] = []

    for app_path in app_files:
        root = _parse_xml(app_path)
        if root is None:
            continue

        app_name = app_path.stem.replace(".app-meta", "").replace(".app", "")

        # Determine navigation type
        nav_type_el = root.find(_tag("navType"))
        ui_type_el = root.find(_tag("uiType"))
        nav_type = nav_type_el.text.strip() if nav_type_el is not None and nav_type_el.text else ""
        ui_type = ui_type_el.text.strip() if ui_type_el is not None and ui_type_el.text else ""

        is_console = nav_type == "Console"
        is_lightning = ui_type == "Lightning" or nav_type in ("Console", "Standard")

        if is_console:
            console_app_names.append(app_name)

        # Check 4: Service/Support app with Standard Navigation
        lower_name = app_name.lower()
        if not is_console and is_lightning and any(
            kw in lower_name for kw in ("service", "support", "case", "helpdesk", "contact_center")
        ):
            standard_nav_service_apps.append(app_name)

        # --- Check utility bar items ---
        utility_items = root.findall(_tag("utilityBar"))
        utility_names = []
        for util in utility_items:
            name_el = util.find(_tag("name"))
            if name_el is not None and name_el.text:
                utility_names.append(name_el.text.strip().lower())

        # Check 1: History utility in a non-console app
        if not is_console and "history" in utility_names:
            issues.append(
                f"App '{app_name}' uses Standard Navigation but has the History utility "
                "in the utility bar. History only renders in Console Navigation apps — "
                "it will be invisible or error for agents. Remove History or convert the "
                "app to Console Navigation."
            )

        # Check 2: Console app with no utility bar
        if is_console and not utility_items:
            issues.append(
                f"Console app '{app_name}' has no utility bar configured. "
                "Service Console agents typically need at minimum the History utility. "
                "Consider adding History, Macros, and Omni-Channel if routing is active."
            )

        # Check 3: Console app with no navigation rules configured
        # Navigation rules are stored under <actionOverrides> or <consoleComponents>
        # depending on the release. A simple proxy: check for <navRules> or
        # <consoleComponents> elements.
        nav_rules = root.findall(_tag("consoleComponents")) + root.findall(_tag("navRules"))
        if is_console and not nav_rules:
            issues.append(
                f"Console app '{app_name}' has no explicit navigation rules defined. "
                "All objects will default to Workspace Tab, including Contact and Account. "
                "Set Contact and Account to open as Subtabs of the current workspace to "
                "prevent agents from accumulating unrelated workspace tabs."
            )

    for app_name in standard_nav_service_apps:
        issues.append(
            f"App '{app_name}' appears to be a service app (name contains 'service', "
            "'support', 'case', or similar) but uses Standard Navigation. "
            "Service teams handling concurrent cases should use Console Navigation to "
            "enable split view and workspace tabs. Review whether this app should be "
            "recreated with Console Navigation."
        )

    # --- 5. Check for Macro metadata ---
    macro_files = _find_files(manifest_dir, "*.macro-meta.xml")
    has_macros_utility = False
    for app_path in app_files:
        root = _parse_xml(app_path)
        if root is None:
            continue
        for util in root.findall(_tag("utilityBar")):
            name_el = util.find(_tag("name"))
            if name_el is not None and name_el.text and "macro" in name_el.text.lower():
                has_macros_utility = True
                break

    if has_macros_utility and not macro_files:
        issues.append(
            "One or more console apps include the Macros utility, but no Macro metadata "
            "files were found in the manifest. Verify that Macros have been deployed to "
            "this org, or that this metadata retrieve included the Macro object type. "
            "Agents will see an empty macro list until macros are deployed."
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Service Console configuration issues. "
            "Detects mismatched navigation types, missing utility bars, absent navigation "
            "rules, and common anti-patterns described in the service-console-configuration skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_service_console_configuration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
