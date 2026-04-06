#!/usr/bin/env python3
"""Checker script for Agent Console Requirements skill.

Inspects Salesforce metadata to flag common console configuration issues:
- Console apps missing the Pinned Header page template on case pages
- Utility bars with more than 8 components (performance risk)
- Missing Omni-Channel utility bar component when Omni-Channel routing config exists
- Missing Run Macros permission in console-assigned permission sets

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agent_console_requirements.py [--help]
    python3 check_agent_console_requirements.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Salesforce metadata namespace
# ---------------------------------------------------------------------------
SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(name: str) -> str:
    """Return a namespaced tag for ElementTree queries."""
    return f"{{{SF_NS}}}{name}"


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_console_app_utility_bar(app_dir: Path) -> list[str]:
    """Check Lightning console app files for utility bar component count."""
    issues: list[str] = []
    for app_file in app_dir.glob("*.app"):
        try:
            tree = ET.parse(app_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"{app_file.name}: XML parse error — {exc}")
            continue

        # Only check console-type apps
        app_type = root.findtext(_tag("formFactor")) or ""
        is_console = False
        for nav_type in root.iter(_tag("navigationType")):
            if nav_type.text and "Console" in nav_type.text:
                is_console = True
                break

        if not is_console:
            continue

        # Count utility bar items
        utility_items = list(root.iter(_tag("utilityBarItems")))
        if len(utility_items) > 8:
            issues.append(
                f"{app_file.name}: utility bar has {len(utility_items)} components "
                f"(recommended maximum is 8 to protect console startup performance)"
            )

        # Check for Omni-Channel component
        omni_found = any(
            "OmniChannel" in (item.findtext(_tag("name")) or "")
            for item in utility_items
        )
        has_routing_config = (app_file.parent.parent / "omniChannelSettings").exists()
        if has_routing_config and not omni_found:
            issues.append(
                f"{app_file.name}: OmniChannel routing config directory found but "
                f"no Omni-Channel utility bar item detected — agents may be unable "
                f"to change presence status"
            )

    return issues


def check_flexipages_for_pinned_header(flexipage_dir: Path) -> list[str]:
    """Check Lightning flexipages assigned to console apps for Pinned Header template."""
    issues: list[str] = []
    for fp_file in flexipage_dir.glob("*.flexipage"):
        try:
            tree = ET.parse(fp_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"{fp_file.name}: XML parse error — {exc}")
            continue

        # Only check pages where sobject is Case
        sobject_type = root.findtext(_tag("sobjectType")) or ""
        if sobject_type.lower() != "case":
            continue

        # Check if this page is assigned to a console app
        is_console_page = False
        for assignment in root.iter(_tag("flexiPageRegions")):
            pass  # presence of flexiPageRegions does not confirm console alone

        # Look for template reference
        template_name = root.findtext(_tag("template")) or ""
        if not template_name:
            # Try nested template element
            for tmpl in root.iter(_tag("template")):
                template_name = tmpl.findtext(_tag("name")) or ""
                break

        # Pinned Header templates contain "PinnedHeader" or "HeaderAndRightSidebar"
        pinned_keywords = ("PinnedHeader", "HeaderAndRightSidebar", "pinned")
        is_pinned = any(kw.lower() in template_name.lower() for kw in pinned_keywords)

        # Only flag pages that have a non-empty, non-pinned template
        if template_name and not is_pinned:
            issues.append(
                f"{fp_file.name}: Case Lightning page uses template '{template_name}' "
                f"instead of a Pinned Header variant — the Highlights Panel will scroll "
                f"off-screen in the Service Console"
            )

    return issues


def check_permission_sets_for_macros(permset_dir: Path) -> list[str]:
    """Warn if no permission set in the manifest grants the Run Macros user permission."""
    issues: list[str] = []
    macro_permission_found = False

    for ps_file in permset_dir.glob("*.permissionset"):
        try:
            tree = ET.parse(ps_file)
            root = tree.getroot()
        except ET.ParseError:
            continue

        for up in root.iter(_tag("userPermissions")):
            name = up.findtext(_tag("name")) or ""
            enabled = (up.findtext(_tag("enabled")) or "false").lower()
            if name == "RunMacros" and enabled == "true":
                macro_permission_found = True
                break

        if macro_permission_found:
            break

    if permset_dir.exists() and list(permset_dir.glob("*.permissionset")) and not macro_permission_found:
        issues.append(
            "No permission set found granting 'RunMacros' user permission — "
            "agents cannot run macros without this permission, which is absent from "
            "all standard Salesforce profiles"
        )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_agent_console_requirements(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Locate metadata subdirectories using common SFDX and Ant project layouts
    # SFDX: force-app/main/default/<type>
    # Ant/mdapi: <type>

    def find_subdir(name: str) -> Path:
        # Check flat mdapi layout first
        direct = manifest_dir / name
        if direct.exists():
            return direct
        # Check SFDX nested layout
        for candidate in manifest_dir.rglob(name):
            if candidate.is_dir():
                return candidate
        return direct  # return non-existent path so callers can skip gracefully

    app_dir = find_subdir("applications")
    flexipage_dir = find_subdir("flexipages")
    permset_dir = find_subdir("permissionsets")

    issues.extend(check_console_app_utility_bar(app_dir))
    issues.extend(check_flexipages_for_pinned_header(flexipage_dir))
    issues.extend(check_permission_sets_for_macros(permset_dir))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Lightning Service Console "
            "configuration issues: utility bar overload, missing Pinned Header "
            "template on case pages, and missing Run Macros permission."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_agent_console_requirements(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
