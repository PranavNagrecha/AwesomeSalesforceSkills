#!/usr/bin/env python3
"""Checker script for Experience Cloud CMS Content skill.

Scans a Salesforce metadata directory for common CMS content configuration issues:
- Missing or misconfigured ManagedContentType metadata files
- CMS channel type mismatches in ExperienceBundle configuration
- Unmanaged content patterns in Experience Builder page metadata

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_cms_content.py [--help]
    python3 check_experience_cloud_cms_content.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud CMS content configuration and metadata "
            "for common issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_managed_content_types(manifest_dir: Path) -> list[str]:
    """Check ManagedContentType metadata files for required fields."""
    issues: list[str] = []
    pattern = "**/*.managedContentType-meta.xml"
    files = list(manifest_dir.glob(pattern))

    if not files:
        # Not an error — org may use only standard content types.
        return issues

    for path in files:
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            # Strip namespace if present
            tag = root.tag
            if "}" in tag:
                ns = tag.split("}")[0] + "}"
            else:
                ns = ""

            dev_name = root.find(f"{ns}developerName")
            label = root.find(f"{ns}masterLabel")

            if dev_name is None or not (dev_name.text or "").strip():
                issues.append(
                    f"{path.name}: ManagedContentType is missing <developerName>."
                )
            if label is None or not (label.text or "").strip():
                issues.append(
                    f"{path.name}: ManagedContentType is missing <masterLabel>."
                )

            nodes = root.findall(f"{ns}managedContentNodeTypes")
            if not nodes:
                issues.append(
                    f"{path.name}: ManagedContentType defines no "
                    "<managedContentNodeTypes> — content type will have no fields."
                )
        except ET.ParseError as exc:
            issues.append(f"{path.name}: XML parse error — {exc}")

    return issues


def check_experience_bundles(manifest_dir: Path) -> list[str]:
    """Check ExperienceBundle config for CMS channel type issues."""
    issues: list[str] = []
    # ExperienceBundle config lives under experiences/<site>/<site>.site-meta.xml
    # or experiences/<site>/config/*.json — check .site-meta.xml for channel refs
    site_meta_files = list(manifest_dir.glob("**/experiences/**/*.site-meta.xml"))

    for path in site_meta_files:
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            tag = root.tag
            ns = (tag.split("}")[0] + "}") if "}" in tag else ""

            # Look for channel type hints — presence of PublicChannel on a site bundle
            # is a warning signal (should be ExperienceChannel for site delivery).
            raw = path.read_text(encoding="utf-8")
            if "PublicChannel" in raw:
                issues.append(
                    f"{path.name}: references 'PublicChannel' — verify this is "
                    "intentional. ExperienceChannel is required for Experience Cloud "
                    "site content delivery; PublicChannel is for headless API delivery."
                )
        except ET.ParseError as exc:
            issues.append(f"{path.name}: XML parse error — {exc}")

    return issues


def check_for_hardcoded_content_patterns(manifest_dir: Path) -> list[str]:
    """Warn when Experience Builder JSON pages contain large inline text blocks
    that suggest content is hardcoded instead of CMS-managed."""
    issues: list[str] = []
    # Experience Builder pages are JSON files under experiences/<site>/views/
    view_files = list(manifest_dir.glob("**/experiences/**/views/*.json"))

    INLINE_TEXT_THRESHOLD = 500  # characters — heuristic for hardcoded content

    for path in view_files:
        try:
            raw = path.read_text(encoding="utf-8")
            # Heuristic: large "value" strings in JSON page definitions suggest
            # inline content rather than CMS component bindings.
            import json
            data = json.loads(raw)
            large_values = _find_large_text_values(data, INLINE_TEXT_THRESHOLD)
            if large_values:
                issues.append(
                    f"{path.name}: contains {len(large_values)} inline text value(s) "
                    f"exceeding {INLINE_TEXT_THRESHOLD} characters. Consider moving "
                    "this content to a managed CMS content item."
                )
        except (ValueError, OSError):
            # Skip non-JSON or unreadable files silently
            pass

    return issues


def _find_large_text_values(obj: object, threshold: int) -> list[str]:
    """Recursively find string values in a JSON structure exceeding threshold length."""
    found: list[str] = []
    if isinstance(obj, str):
        if len(obj) > threshold:
            found.append(obj[:80] + "...")
    elif isinstance(obj, dict):
        for v in obj.values():
            found.extend(_find_large_text_values(v, threshold))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(_find_large_text_values(item, threshold))
    return found


def check_experience_cloud_cms_content(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_managed_content_types(manifest_dir))
    issues.extend(check_experience_bundles(manifest_dir))
    issues.extend(check_for_hardcoded_content_patterns(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_cms_content(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
