#!/usr/bin/env python3
"""Checker script for Analytics Embedded Components skill.

Scans LWC metadata in a Salesforce project for common embedding anti-patterns:
  - wave-community-dashboard used on Lightning (non-Experience-Cloud) pages
  - wave-wave-dashboard-lwc used on Experience Cloud pages
  - Both 'dashboard' and 'developer-name' attributes set on the same component element
  - analytics__Dashboard target combined with Lightning page targets in js-meta.xml
  - State attribute values that are not valid JSON (for hardcoded state strings)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_embedded_components.py [--manifest-dir path/to/sfdx/project]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LIGHTNING_TARGETS = {
    "lightning__RecordPage",
    "lightning__AppPage",
    "lightning__HomePage",
    "lightning__UtilityBar",
    "lightning__Tab",
}

EXPERIENCE_CLOUD_TARGETS = {
    "comm__Page",
    "lightning__CommunityPage",
}

ANALYTICS_DASHBOARD_TARGET = "analytics__Dashboard"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_lwc_dirs(manifest_dir: Path) -> list[Path]:
    """Return all LWC component directories under manifest_dir."""
    lwc_root = manifest_dir / "lwc"
    if not lwc_root.exists():
        # Try common SFDX paths
        for candidate in [
            manifest_dir / "force-app" / "main" / "default" / "lwc",
            manifest_dir / "src" / "lwc",
        ]:
            if candidate.exists():
                lwc_root = candidate
                break
        else:
            return []
    return [d for d in lwc_root.iterdir() if d.is_dir()]


def parse_js_meta_targets(meta_path: Path) -> list[str]:
    """Parse <targets> from a js-meta.xml file. Returns list of target strings."""
    try:
        tree = ET.parse(meta_path)
        root = tree.getroot()
        # Handle namespace
        ns_match = re.match(r"\{(.+)\}", root.tag)
        ns = f"{{{ns_match.group(1)}}}" if ns_match else ""
        targets_el = root.find(f"{ns}targets")
        if targets_el is None:
            return []
        return [t.text.strip() for t in targets_el.findall(f"{ns}target") if t.text]
    except ET.ParseError:
        return []


def find_html_files(component_dir: Path) -> list[Path]:
    """Return all .html files in a component directory."""
    return list(component_dir.glob("*.html"))


def check_html_for_embedding_issues(html_path: Path, targets: list[str]) -> list[str]:
    """Scan an HTML template for embedding anti-patterns.

    Returns list of issue strings.
    """
    issues: list[str] = []
    try:
        content = html_path.read_text(encoding="utf-8")
    except OSError:
        return issues

    rel = html_path.relative_to(html_path.parents[2]) if html_path.parents[2].exists() else html_path

    # --- Check 1: wave-community-dashboard on Lightning pages ---
    if "wave-community-dashboard" in content:
        lightning_page_targets = set(targets) & LIGHTNING_TARGETS
        if lightning_page_targets:
            issues.append(
                f"{rel}: uses <wave-community-dashboard> but component is registered for "
                f"Lightning targets {sorted(lightning_page_targets)}. "
                f"Use <wave-wave-dashboard-lwc> for Lightning App Builder pages."
            )

    # --- Check 2: wave-wave-dashboard-lwc on Experience Cloud pages ---
    if "wave-wave-dashboard-lwc" in content:
        exp_targets = set(targets) & EXPERIENCE_CLOUD_TARGETS
        if exp_targets:
            issues.append(
                f"{rel}: uses <wave-wave-dashboard-lwc> but component is registered for "
                f"Experience Cloud targets {sorted(exp_targets)}. "
                f"Use <wave-community-dashboard> for Experience Cloud pages."
            )

    # --- Check 3: Both 'dashboard' ID attr and 'developer-name' on same element ---
    # Match opening tags of either wave component
    wave_tags = re.findall(
        r"<wave-(?:wave-dashboard-lwc|community-dashboard)[^>]*?>",
        content,
        re.DOTALL,
    )
    for tag in wave_tags:
        has_dashboard_id = bool(re.search(r'\bdashboard\s*=\s*["\']0FK', tag))
        has_developer_name = bool(re.search(r'\bdeveloper-name\s*=', tag))
        if has_dashboard_id and has_developer_name:
            issues.append(
                f"{rel}: wave dashboard component has both 'dashboard' (0FK ID) and "
                f"'developer-name' attributes set. They are mutually exclusive — "
                f"the 'dashboard' ID silently takes precedence. Use only one."
            )

    # --- Check 4: Hardcoded state attribute that is not valid JSON ---
    # Only check hardcoded strings (quoted values), skip bindings like state={{state}}
    state_matches = re.findall(r'\bstate\s*=\s*"([^"{}][^"]*)"', content)
    for state_val in state_matches:
        try:
            json.loads(state_val)
        except json.JSONDecodeError:
            issues.append(
                f"{rel}: hardcoded 'state' attribute value is not valid JSON: "
                f"{state_val[:80]!r}. Invalid JSON causes silent dashboard load "
                f"in default state with no error."
            )

    return issues


def check_js_meta_for_target_conflicts(meta_path: Path, targets: list[str]) -> list[str]:
    """Check js-meta.xml for incompatible target combinations."""
    issues: list[str] = []
    rel = meta_path

    target_set = set(targets)

    # Check: analytics__Dashboard combined with Lightning page targets (unusual; warn)
    if ANALYTICS_DASHBOARD_TARGET in target_set:
        combined_lightning = target_set & LIGHTNING_TARGETS
        if combined_lightning:
            issues.append(
                f"{rel}: js-meta.xml declares both 'analytics__Dashboard' and Lightning "
                f"page targets {sorted(combined_lightning)}. "
                f"'analytics__Dashboard' registers a component as an Analytics dashboard "
                f"canvas widget (Pattern B). Lightning page targets register it for App "
                f"Builder (Pattern A). Confirm this dual-target registration is intentional — "
                f"these are different embedding patterns with separate use cases."
            )

    return issues


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------

def check_analytics_embedded_components(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    lwc_dirs = find_lwc_dirs(manifest_dir)
    if not lwc_dirs:
        # No LWC directory found — not necessarily an error for all project types
        return issues

    for component_dir in lwc_dirs:
        meta_files = list(component_dir.glob("*.js-meta.xml"))
        targets: list[str] = []
        if meta_files:
            targets = parse_js_meta_targets(meta_files[0])
            issues.extend(check_js_meta_for_target_conflicts(meta_files[0], targets))

        for html_file in find_html_files(component_dir):
            issues.extend(check_html_for_embedding_issues(html_file, targets))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce LWC metadata for Analytics Embedded Component anti-patterns. "
            "Detects wrong component for surface, mutual-exclusivity violations, invalid state JSON, "
            "and incompatible js-meta.xml target combinations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project or metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_analytics_embedded_components(manifest_dir)

    if not issues:
        print("No analytics embedding issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
