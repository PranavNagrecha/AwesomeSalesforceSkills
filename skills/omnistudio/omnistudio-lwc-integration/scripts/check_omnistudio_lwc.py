#!/usr/bin/env python3
"""Checker script for OmniStudio LWC Integration skill.

Scans HTML and XML metadata files for omnistudio-omni-script and c-omni-script
tags, detects mixed namespace usage in the same file, and reports seed data
attribute issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_lwc.py [--help]
    python3 check_omnistudio_lwc.py --manifest-dir path/to/metadata
    python3 check_omnistudio_lwc.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Tag patterns for native vs managed package OmniScript component
NATIVE_TAG_RE = re.compile(r"<omnistudio-omni-script", re.IGNORECASE)
MANAGED_TAG_RE = re.compile(r"<c-omni-script", re.IGNORECASE)

# Detect seed data being set imperatively after mount (querySelector + assignment)
IMPERATIVE_SEED_RE = re.compile(
    r"querySelector\s*\([^)]*omni[^)]*\)\s*\.\s*omniSeedJson\s*=",
    re.IGNORECASE,
)

# Detect wire decorator inside a file that also declares omniJsonData (custom element marker)
WIRE_DECORATOR_RE = re.compile(r"@wire\s*\(", re.IGNORECASE)
OMNI_JSON_DATA_RE = re.compile(r"@api\s+omniJsonData", re.IGNORECASE)

# Detect direct REST calls to Integration Procedure endpoints
DIRECT_REST_IP_RE = re.compile(
    r"fetch\s*\(\s*['\"].*integrationprocedure",
    re.IGNORECASE,
)

# Detect NavigationMixin to OmniScript wrapper without state
NAV_OMNI_RE = re.compile(
    r"standard__component['\"][\s\S]{0,400}OmniScriptWrapper",
    re.IGNORECASE,
)
NAV_OMNI_WITH_STATE_RE = re.compile(
    r"standard__component['\"][\s\S]{0,800}state\s*:",
    re.IGNORECASE,
)


def check_html_file(path: Path) -> list[str]:
    """Check an HTML template file for OmniStudio LWC integration issues."""
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    has_native = bool(NATIVE_TAG_RE.search(text))
    has_managed = bool(MANAGED_TAG_RE.search(text))

    if has_native and has_managed:
        issues.append(
            f"{path}: Mixed namespace — both 'omnistudio-omni-script' (native) and "
            f"'c-omni-script' (managed package) found in the same file. "
            f"Use one namespace consistently based on the org's OmniStudio runtime."
        )

    return issues


def check_js_file(path: Path) -> list[str]:
    """Check a JavaScript file for OmniStudio LWC integration issues."""
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    # Detect imperative seed data setting after mount
    if IMPERATIVE_SEED_RE.search(text):
        issues.append(
            f"{path}: Possible imperative seed data assignment detected "
            f"(querySelector + omniSeedJson=). Seed data must be bound as a reactive "
            f"template expression before the OmniScript component mounts, not set "
            f"imperatively after mount."
        )

    # Detect wire adapter inside a custom OmniScript element (has omniJsonData)
    if WIRE_DECORATOR_RE.search(text) and OMNI_JSON_DATA_RE.search(text):
        issues.append(
            f"{path}: @wire decorator found in a file that declares '@api omniJsonData' "
            f"(a custom OmniScript element marker). Wire adapters may not resolve "
            f"correctly inside the OmniScript runtime across step navigations. "
            f"Use imperative Apex calls and derive state from omniJsonData instead."
        )

    # Detect direct REST calls to Integration Procedure endpoints
    if DIRECT_REST_IP_RE.search(text):
        issues.append(
            f"{path}: Direct REST call to an Integration Procedure endpoint detected. "
            f"Route Integration Procedure calls through an @AuraEnabled Apex method "
            f"to preserve sharing enforcement and governor limit controls."
        )

    # Detect NavigationMixin OmniScript launch without state
    if NAV_OMNI_RE.search(text) and not NAV_OMNI_WITH_STATE_RE.search(text):
        issues.append(
            f"{path}: NavigationMixin call to OmniScriptWrapper detected without "
            f"a 'state' property. Include seed data and OmniScript type/subtype "
            f"in the navigation state to pre-populate the launched OmniScript."
        )

    return issues


def check_xml_file(path: Path) -> list[str]:
    """Check an XML metadata file for OmniStudio namespace issues."""
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")

    has_native = bool(NATIVE_TAG_RE.search(text))
    has_managed = bool(MANAGED_TAG_RE.search(text))

    if has_native and has_managed:
        issues.append(
            f"{path}: Mixed namespace references in XML metadata — both "
            f"'omnistudio-omni-script' and 'c-omni-script' found. "
            f"Review and align to the org's OmniStudio runtime namespace."
        )

    return issues


def check_omnistudio_lwc(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan HTML template files
    for html_path in manifest_dir.rglob("*.html"):
        issues.extend(check_html_file(html_path))

    # Scan JavaScript files
    for js_path in manifest_dir.rglob("*.js"):
        issues.extend(check_js_file(js_path))

    # Scan XML metadata files (FlexCard and OmniScript definitions may reference components)
    for xml_path in manifest_dir.rglob("*.xml"):
        issues.extend(check_xml_file(xml_path))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for OmniStudio LWC integration issues. "
            "Detects mixed namespace tags (native vs managed package), imperative "
            "seed data patterns, wire adapters inside custom OmniScript elements, "
            "and direct REST calls to Integration Procedure endpoints."
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
    manifest_dir = Path(args.manifest_dir)
    issues = check_omnistudio_lwc(manifest_dir)

    if not issues:
        print("No OmniStudio LWC integration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
