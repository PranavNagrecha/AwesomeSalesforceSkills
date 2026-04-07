#!/usr/bin/env python3
"""Checker script for LWR Site Development skill.

Validates LWC component metadata for LWR Experience Cloud site compatibility.
Checks for:
  - Correct lightningCommunity__* targets in js-meta.xml files
  - Missing default slot in theme layout templates
  - Absence of @slot JSDoc annotations in layout components
  - Aura component references (.cmp files) in the manifest directory
  - Restricted DOM API usage (window.location, document.domain, etc.)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lwr_site_development.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree

# LWR-valid community targets
LWR_TARGETS = {
    "lightningCommunity__Page",
    "lightningCommunity__Page_Layout",
    "lightningCommunity__Theme_Layout",
    "lightningCommunity__Default",
}

# Targets that indicate a theme or page layout role
LAYOUT_TARGETS = {
    "lightningCommunity__Theme_Layout",
    "lightningCommunity__Page_Layout",
}

# DOM APIs restricted under Lightning Web Security in LWR sites
RESTRICTED_LWS_APIS = [
    r"document\.domain",
    r"document\.location",
    r"window\.location",
    r"window\.top",
]

RESTRICTED_PATTERN = re.compile("|".join(RESTRICTED_LWS_APIS))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check LWR site component metadata for common LWR compatibility issues.\n"
            "Scans js-meta.xml, .html templates, and .js files under the manifest directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _get_targets_from_meta(meta_path: Path) -> list[str]:
    """Parse targets from a js-meta.xml file. Returns empty list on parse error."""
    try:
        tree = ElementTree.parse(meta_path)
        root = tree.getroot()
        # Strip namespace if present
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"
        targets = []
        for target_el in root.iter(f"{ns}target"):
            if target_el.text:
                targets.append(target_el.text.strip())
        return targets
    except ElementTree.ParseError:
        return []


def check_aura_components(manifest_dir: Path) -> list[str]:
    """Detect .cmp Aura component files — unsupported in LWR sites."""
    issues = []
    cmp_files = list(manifest_dir.rglob("*.cmp"))
    for cmp_file in cmp_files:
        issues.append(
            f"Aura component detected (unsupported in LWR sites): {cmp_file.relative_to(manifest_dir)}"
        )
    return issues


def check_meta_xml_targets(manifest_dir: Path) -> list[str]:
    """Check js-meta.xml files for LWR-compatible targets."""
    issues = []
    meta_files = list(manifest_dir.rglob("*-meta.xml"))

    for meta_path in meta_files:
        # Only check LightningComponentBundle metadata
        try:
            tree = ElementTree.parse(meta_path)
            root = tree.getroot()
        except ElementTree.ParseError:
            continue

        if "LightningComponentBundle" not in root.tag and root.tag != "LightningComponentBundle":
            # Try stripped tag name
            stripped = root.tag.split("}")[-1]
            if stripped != "LightningComponentBundle":
                continue

        targets = _get_targets_from_meta(meta_path)
        if not targets:
            continue

        # Warn if any non-LWR community target is present
        for t in targets:
            if t.startswith("lightningCommunity__") and t not in LWR_TARGETS:
                issues.append(
                    f"{meta_path.relative_to(manifest_dir)}: "
                    f"Unrecognized lightningCommunity__ target '{t}'. "
                    "Verify this target is valid for LWR sites."
                )

        # If component declares a layout target, check for lightningCommunity__Default
        # (required for editable properties — only warn if targetConfigs also present)
        has_layout_target = any(t in LAYOUT_TARGETS for t in targets)
        has_default_target = "lightningCommunity__Default" in targets
        if has_layout_target and not has_default_target:
            # Not strictly required if no properties needed; only informational
            pass  # Would be noise without checking targetConfigs

    return issues


def check_theme_layout_templates(manifest_dir: Path) -> list[str]:
    """Check theme layout LWC HTML templates for required default slot."""
    issues = []
    meta_files = list(manifest_dir.rglob("*-meta.xml"))

    for meta_path in meta_files:
        targets = _get_targets_from_meta(meta_path)
        if "lightningCommunity__Theme_Layout" not in targets:
            continue

        # Find the corresponding .html template (same name, same directory)
        component_name = meta_path.name.replace("-meta.xml", "")
        # js-meta.xml is named <componentName>.js-meta.xml
        # strip the .js from the stem
        if component_name.endswith(".js"):
            component_name = component_name[:-3]

        html_path = meta_path.parent / f"{component_name}.html"
        if not html_path.exists():
            issues.append(
                f"Theme layout component missing HTML template: "
                f"{meta_path.parent.relative_to(manifest_dir)}/{component_name}.html"
            )
            continue

        content = html_path.read_text(encoding="utf-8", errors="replace")

        # Check for unnamed default slot: <slot> or <slot></slot> (no name attribute)
        # Regex: <slot> not followed by name=
        default_slot_pattern = re.compile(r"<slot(?!\s+name)[^>]*>", re.IGNORECASE)
        if not default_slot_pattern.search(content):
            issues.append(
                f"{html_path.relative_to(manifest_dir)}: "
                "Theme layout component is missing a default unnamed <slot></slot>. "
                "Main page content will not render without it."
            )

    return issues


def check_layout_slot_annotations(manifest_dir: Path) -> list[str]:
    """Check page layout and theme layout JS files for @slot JSDoc annotations."""
    issues = []
    meta_files = list(manifest_dir.rglob("*-meta.xml"))

    for meta_path in meta_files:
        targets = _get_targets_from_meta(meta_path)
        is_layout = any(t in LAYOUT_TARGETS for t in targets)
        if not is_layout:
            continue

        component_name = meta_path.name.replace("-meta.xml", "")
        if component_name.endswith(".js"):
            component_name = component_name[:-3]

        js_path = meta_path.parent / f"{component_name}.js"
        if not js_path.exists():
            continue

        content = js_path.read_text(encoding="utf-8", errors="replace")

        # Check for @slot annotation
        if "@slot" not in content:
            issues.append(
                f"{js_path.relative_to(manifest_dir)}: "
                "Layout component (Page_Layout or Theme_Layout) is missing @slot JSDoc annotations. "
                "Named regions will not appear in Experience Builder without them."
            )

    return issues


def check_restricted_lws_apis(manifest_dir: Path) -> list[str]:
    """Check JS files for DOM APIs restricted under LWS in LWR sites."""
    issues = []
    js_files = list(manifest_dir.rglob("*.js"))

    for js_path in js_files:
        # Skip meta XML (handled separately) and test files
        if "meta.xml" in js_path.name:
            continue
        if "__tests__" in str(js_path) or ".test." in js_path.name:
            continue

        try:
            content = js_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        matches = RESTRICTED_PATTERN.findall(content)
        if matches:
            unique_matches = sorted(set(matches))
            issues.append(
                f"{js_path.relative_to(manifest_dir)}: "
                f"Restricted LWS DOM API usage detected: {', '.join(unique_matches)}. "
                "These APIs are unsupported in LWR sites under Lightning Web Security."
            )

    return issues


def check_lwr_site_development(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_aura_components(manifest_dir))
    issues.extend(check_meta_xml_targets(manifest_dir))
    issues.extend(check_theme_layout_templates(manifest_dir))
    issues.extend(check_layout_slot_annotations(manifest_dir))
    issues.extend(check_restricted_lws_apis(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwr_site_development(manifest_dir)

    if not issues:
        print("No LWR compatibility issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
