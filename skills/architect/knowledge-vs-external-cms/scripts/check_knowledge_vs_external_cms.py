#!/usr/bin/env python3
"""Checker script for Knowledge vs External CMS skill.

Scans org metadata for Knowledge configuration, CMS Connect presence,
and common misconfigurations in hybrid content architectures.
Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_knowledge_vs_external_cms.py [--help]
    python3 check_knowledge_vs_external_cms.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Knowledge vs External CMS configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find files with the given suffix under root."""
    results: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(suffix):
                results.append(Path(dirpath) / fname)
    return results


def _parse_xml_safe(filepath: Path) -> ET.Element | None:
    """Parse XML and return root element, or None on failure."""
    try:
        tree = ET.parse(filepath)
        return tree.getroot()
    except (ET.ParseError, OSError):
        return None


def check_knowledge_enabled(manifest_dir: Path) -> list[str]:
    """Check whether Knowledge is enabled in the org settings."""
    issues: list[str] = []
    settings_files = _find_files(manifest_dir, "KnowledgeSettings.settings-meta.xml")
    if not settings_files:
        settings_files = _find_files(manifest_dir, "Knowledge.settings-meta.xml")

    if not settings_files:
        issues.append(
            "No KnowledgeSettings metadata found. Cannot verify whether "
            "Salesforce Knowledge is enabled. If Knowledge is part of the "
            "content strategy, ensure it is enabled and metadata is retrieved."
        )
        return issues

    for sf in settings_files:
        root = _parse_xml_safe(sf)
        if root is None:
            issues.append(f"Could not parse Knowledge settings file: {sf}")
    return issues


def check_data_categories(manifest_dir: Path) -> list[str]:
    """Check for data category group definitions."""
    issues: list[str] = []
    cat_files = _find_files(manifest_dir, ".datacategorygroup-meta.xml")

    if not cat_files:
        issues.append(
            "No data category group metadata found. Knowledge article "
            "visibility relies on data categories. If Knowledge is in use, "
            "verify that data category groups are defined and retrieved."
        )
    return issues


def check_cms_connect_sites(manifest_dir: Path) -> list[str]:
    """Look for Experience Cloud site metadata that might use CMS Connect."""
    issues: list[str] = []
    site_files = _find_files(manifest_dir, ".site-meta.xml")
    network_files = _find_files(manifest_dir, ".network-meta.xml")

    if not site_files and not network_files:
        # Not necessarily an issue -- org may not use Experience Cloud.
        return issues

    # If sites exist but no CMS connection metadata, flag for review.
    cms_files = _find_files(manifest_dir, ".cmsConnectSource-meta.xml")
    content_space_files = _find_files(manifest_dir, ".managedContentType-meta.xml")

    if (site_files or network_files) and not cms_files and not content_space_files:
        issues.append(
            "Experience Cloud site metadata found but no CMS Connect or "
            "managed content type metadata detected. If external CMS content "
            "should appear in the portal, verify CMS Connect configuration."
        )
    return issues


def check_knowledge_article_types(manifest_dir: Path) -> list[str]:
    """Check for Knowledge article type definitions."""
    issues: list[str] = []
    kav_dirs = []
    for dirpath, dirnames, _filenames in os.walk(manifest_dir):
        for d in dirnames:
            if d.endswith("__kav"):
                kav_dirs.append(Path(dirpath) / d)

    kav_objects = _find_files(manifest_dir, "__kav.object-meta.xml")

    if not kav_dirs and not kav_objects:
        issues.append(
            "No Knowledge article type objects (*__kav) found in metadata. "
            "If Knowledge is part of the content strategy, ensure article "
            "types are defined and metadata is retrieved."
        )
    return issues


def check_knowledge_vs_external_cms(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_knowledge_enabled(manifest_dir))
    issues.extend(check_data_categories(manifest_dir))
    issues.extend(check_knowledge_article_types(manifest_dir))
    issues.extend(check_cms_connect_sites(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_knowledge_vs_external_cms(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
