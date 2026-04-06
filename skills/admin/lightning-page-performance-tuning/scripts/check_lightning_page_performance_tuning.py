#!/usr/bin/env python3
"""Checker script for Lightning Page Performance Tuning skill.

Parses Salesforce FlexiPage metadata XML files (retrieved via sfdx/sf CLI or
Metadata API) and flags common performance anti-patterns documented in
references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lightning_page_performance_tuning.py [--help]
    python3 check_lightning_page_performance_tuning.py --manifest-dir path/to/metadata

The script looks for *.flexipage-meta.xml files under the manifest directory,
typically at: force-app/main/default/flexipages/*.flexipage-meta.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_NS = "http://soap.sforce.com/2006/04/metadata"

# Component types that are known to be data-heavy (trigger XHR on render).
HEAVY_COMPONENT_TYPES = {
    "flexipage:reportChart",
    "flexipage:relatedList",
    "force:relatedListContainer",
    "runtime_sales_activities:activityPanel",
    "force:reportChart",
}

# Lightweight component types that are acceptable on initial viewport.
LIGHT_COMPONENT_TYPES = {
    "flexipage:richText",
    "force:highlightsPanel",
    "force:recordDetail",
    "flexipage:column",
    "flexipage:region",
}

# Threshold for initial-viewport component count warning.
INITIAL_VIEWPORT_WARN_THRESHOLD = 10

# Threshold for total component count warning.
TOTAL_COMPONENT_WARN_THRESHOLD = 20


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def _tag(name: str) -> str:
    """Return a namespace-qualified tag name."""
    return f"{{{_NS}}}{name}"


def _find_all_components(root: ET.Element) -> list[ET.Element]:
    """Find all componentInstance elements in a FlexiPage."""
    return root.iter(_tag("componentInstance"))


def _get_component_type(comp: ET.Element) -> str | None:
    """Extract the componentName from a componentInstance element."""
    name_el = comp.find(_tag("componentName"))
    if name_el is not None and name_el.text:
        return name_el.text.strip()
    return None


def _has_tabs_component(root: ET.Element) -> bool:
    """Check whether the page uses a Tabs component for progressive disclosure."""
    for comp in root.iter(_tag("componentInstance")):
        ctype = _get_component_type(comp)
        if ctype and "tab" in ctype.lower():
            return True
    return False


def _count_regions(root: ET.Element) -> int:
    """Count top-level flexipageRegion elements (proxy for layout sections)."""
    return len(list(root.iter(_tag("flexipageRegion"))))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_flexipage(path: Path) -> list[str]:
    """Run performance checks on a single FlexiPage XML file.

    Returns a list of warning strings. An empty list means no issues found.
    """
    warnings: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"  XML parse error in {path.name}: {exc}"]

    root = tree.getroot()
    components = list(_find_all_components(root))
    total_count = len(components)

    # --- Check 1: Total component count ---
    if total_count > TOTAL_COMPONENT_WARN_THRESHOLD:
        warnings.append(
            f"  HIGH COMPONENT COUNT: {path.name} has {total_count} components "
            f"(threshold: {TOTAL_COMPONENT_WARN_THRESHOLD}). "
            "Consider removing unused components or deferring to tabs."
        )

    # --- Check 2: Heavy components on the page ---
    heavy_components: list[str] = []
    for comp in components:
        ctype = _get_component_type(comp)
        if ctype and ctype in HEAVY_COMPONENT_TYPES:
            heavy_components.append(ctype)

    if heavy_components:
        warnings.append(
            f"  DATA-HEAVY COMPONENTS: {path.name} contains "
            f"{len(heavy_components)} data-heavy component(s): "
            f"{', '.join(heavy_components)}. "
            "These trigger XHR calls on render. Consider deferring to non-default tabs."
        )

    # --- Check 3: No tabs component detected ---
    if total_count > INITIAL_VIEWPORT_WARN_THRESHOLD and not _has_tabs_component(root):
        warnings.append(
            f"  NO PROGRESSIVE DISCLOSURE: {path.name} has {total_count} components "
            "but does not use a Tabs component. "
            "Consider grouping secondary components into tabs to defer rendering."
        )

    # --- Check 4: Report Chart components (especially costly) ---
    report_charts = [
        c for c in components
        if _get_component_type(c) in ("flexipage:reportChart", "force:reportChart")
    ]
    if len(report_charts) > 2:
        warnings.append(
            f"  EXCESSIVE REPORT CHARTS: {path.name} has {len(report_charts)} "
            "Report Chart components. Each executes the underlying report on every "
            "page load. Consider reducing to 2 or fewer, or deferring to tabs."
        )

    return warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check FlexiPage metadata for Lightning page performance anti-patterns."
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=Path("force-app/main/default/flexipages"),
        help="Directory containing *.flexipage-meta.xml files "
             "(default: force-app/main/default/flexipages)",
    )
    args = parser.parse_args()

    manifest_dir: Path = args.manifest_dir
    if not manifest_dir.is_dir():
        print(f"Directory not found: {manifest_dir}")
        print("Provide the path to your flexipages metadata directory via --manifest-dir.")
        return 1

    flexipage_files = sorted(manifest_dir.glob("*.flexipage-meta.xml"))
    if not flexipage_files:
        print(f"No *.flexipage-meta.xml files found in {manifest_dir}")
        return 1

    print(f"Scanning {len(flexipage_files)} FlexiPage file(s) in {manifest_dir}…\n")

    all_warnings: list[str] = []
    for fp in flexipage_files:
        file_warnings = check_flexipage(fp)
        if file_warnings:
            all_warnings.extend(file_warnings)

    if all_warnings:
        print("⚠  Performance warnings found:\n")
        for w in all_warnings:
            print(w)
        print(f"\nTotal: {len(all_warnings)} warning(s) across {len(flexipage_files)} file(s).")
        return 1

    print(f"✓ No performance anti-patterns detected in {len(flexipage_files)} FlexiPage file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
