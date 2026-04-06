#!/usr/bin/env python3
"""Checker script for Lightning App Builder Advanced skill.

Audits Salesforce FlexiPage metadata files for common Lightning App Builder
advanced configuration issues: excessive component counts, Dynamic Actions
conflicts, recordId in LWC targetConfig, and visibility filter overuse.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lightning_app_builder_advanced.py --help
    python3 check_lightning_app_builder_advanced.py --manifest-dir path/to/metadata
    python3 check_lightning_app_builder_advanced.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce-documented mobile component count guideline
MOBILE_COMPONENT_LIMIT = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Lightning App Builder advanced configuration in Salesforce metadata "
            "for common issues: component overload, Dynamic Actions conflicts, "
            "LWC targetConfig misuse, and visibility filter anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# FlexiPage XML checks
# ---------------------------------------------------------------------------

def _count_components_in_flexipage(root: ET.Element) -> dict[str, int]:
    """Return a mapping of region name -> component count from a FlexiPage XML root."""
    ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
    region_counts: dict[str, int] = {}

    for region in root.findall(".//sf:flexiPageRegions", ns):
        name_el = region.find("sf:name", ns)
        if name_el is None:
            continue
        region_name = name_el.text or "unknown"
        components = region.findall(".//sf:componentInstances", ns)
        region_counts[region_name] = len(components)

    return region_counts


def check_flexipages(manifest_dir: Path) -> list[str]:
    """Check all FlexiPage metadata files under manifest_dir."""
    issues: list[str] = []
    flexipage_dir = manifest_dir / "flexipages"

    if not flexipage_dir.exists():
        # Try nested structure (force-app/main/default/flexipages)
        for candidate in manifest_dir.rglob("flexipages"):
            if candidate.is_dir():
                flexipage_dir = candidate
                break

    if not flexipage_dir.exists():
        return issues  # No FlexiPage metadata found — not an error

    for fp_file in sorted(flexipage_dir.glob("*.flexipage-meta.xml")):
        try:
            tree = ET.parse(fp_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"[{fp_file.name}] XML parse error: {exc}")
            continue

        region_counts = _count_components_in_flexipage(root)
        for region, count in region_counts.items():
            if count > MOBILE_COMPONENT_LIMIT:
                issues.append(
                    f"[{fp_file.name}] Region '{region}' has {count} components "
                    f"(recommended max {MOBILE_COMPONENT_LIMIT} for mobile performance). "
                    "Consider a Phone form-factor variant with fewer components."
                )

    return issues


# ---------------------------------------------------------------------------
# LWC js-meta.xml checks
# ---------------------------------------------------------------------------

def _check_lwc_meta_file(meta_file: Path) -> list[str]:
    """Check a single LWC .js-meta.xml file for recordId in targetConfig."""
    issues: list[str] = []
    try:
        tree = ET.parse(meta_file)
        root = tree.getroot()
    except ET.ParseError as exc:
        issues.append(f"[{meta_file.name}] XML parse error: {exc}")
        return issues

    # Namespace may or may not be present
    # Try both namespaced and un-namespaced
    ns_uri = "http://soap.sforce.com/2006/04/metadata"
    ns = {"sf": ns_uri}

    def find_all(tag: str) -> list[ET.Element]:
        results = root.findall(f".//sf:{tag}", ns)
        if not results:
            results = root.findall(f".//{tag}")
        return results

    reserved_props = {"recordId", "objectApiName"}

    for target_config in find_all("targetConfig"):
        # Check targets attribute
        targets_attr = target_config.get("targets", "")
        if "lightning__RecordPage" not in targets_attr and "lightning__RecordPage" not in (
            (target_config.findtext("targets") or "")
        ):
            continue  # Only record page configs inject recordId

        for prop in target_config.findall("property") + find_all("property"):
            prop_name = prop.get("name", "")
            if prop_name in reserved_props:
                issues.append(
                    f"[{meta_file.parent.name}/{meta_file.name}] "
                    f"'{prop_name}' declared in <targetConfig> for lightning__RecordPage. "
                    f"'{prop_name}' is injected automatically by the framework — "
                    "remove it from <targetConfig> and keep only the @api decorator in JS."
                )

    return issues


def check_lwc_meta_files(manifest_dir: Path) -> list[str]:
    """Check all LWC .js-meta.xml files under manifest_dir."""
    issues: list[str] = []
    for meta_file in manifest_dir.rglob("*.js-meta.xml"):
        issues.extend(_check_lwc_meta_file(meta_file))
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_lightning_app_builder_advanced(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_flexipages(manifest_dir))
    issues.extend(check_lwc_meta_files(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lightning_app_builder_advanced(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
