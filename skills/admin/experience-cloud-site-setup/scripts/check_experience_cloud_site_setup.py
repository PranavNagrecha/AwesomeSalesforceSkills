#!/usr/bin/env python3
"""Checker script for Experience Cloud Site Setup skill.

Inspects Salesforce metadata in a project directory for common Experience Cloud
site setup issues: missing LWR targets on components, Aura component usage in
LWR sites, and missing branding token usage in component CSS.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_site_setup.py [--help]
    python3 check_experience_cloud_site_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud site setup metadata for common issues: "
            "missing LWR component targets, Aura component usage, and branding "
            "anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_lwc_experience_targets(manifest_dir: Path) -> list[str]:
    """Warn when a LWC component lacks Experience Cloud target declarations.

    Components intended for Experience Builder must declare at least one of:
      - lightningCommunity__Page
      - lightningCommunity__Default

    in their *.js-meta.xml isExposed/targets block.
    """
    issues: list[str] = []
    lwc_dir = manifest_dir / "lwc"
    if not lwc_dir.exists():
        return issues

    experience_targets = {
        "lightningCommunity__Page",
        "lightningCommunity__Default",
    }

    for meta_file in sorted(lwc_dir.rglob("*.js-meta.xml")):
        try:
            tree = ET.parse(meta_file)
        except ET.ParseError as exc:
            issues.append(f"XML parse error in {meta_file.relative_to(manifest_dir)}: {exc}")
            continue

        root = tree.getroot()
        # Strip namespace for easier querying
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        is_exposed_el = root.find(f"{ns}isExposed")
        is_exposed = is_exposed_el is not None and is_exposed_el.text == "true"
        if not is_exposed:
            continue  # Not exposed to any builder — skip

        declared_targets: set[str] = set()
        for target_el in root.findall(f".//{ns}target"):
            if target_el.text:
                declared_targets.add(target_el.text.strip())

        has_experience_target = bool(declared_targets & experience_targets)
        if not has_experience_target:
            issues.append(
                f"LWC component '{meta_file.parent.name}' is exposed but has no "
                f"Experience Cloud target (lightningCommunity__Page or "
                f"lightningCommunity__Default). It will not appear in Experience Builder. "
                f"File: {meta_file.relative_to(manifest_dir)}"
            )

    return issues


def check_aura_components_present(manifest_dir: Path) -> list[str]:
    """Warn when Aura components are present alongside LWR-only site indicators.

    If the metadata contains Aura components AND an LWR-type ExperienceBundle,
    this is a likely mismatch that will cause components to be missing in
    Experience Builder.
    """
    issues: list[str] = []
    aura_dir = manifest_dir / "aura"
    experience_dir = manifest_dir / "experiences"

    if not aura_dir.exists() or not experience_dir.exists():
        return issues

    aura_components = [d for d in aura_dir.iterdir() if d.is_dir()]
    if not aura_components:
        return issues

    # Check for any LWR-type site bundles (type = LWR in config)
    lwr_sites: list[str] = []
    for config_file in experience_dir.rglob("*.json"):
        try:
            import json
            data = json.loads(config_file.read_text(encoding="utf-8"))
            site_type = data.get("type", "")
            site_name = data.get("label", config_file.parent.name)
            if "LWR" in site_type.upper():
                lwr_sites.append(site_name)
        except Exception:
            pass  # Best-effort; skip unreadable files

    if lwr_sites:
        component_names = [c.name for c in aura_components[:5]]
        extra = f" (and {len(aura_components) - 5} more)" if len(aura_components) > 5 else ""
        issues.append(
            f"Aura components found ({', '.join(component_names)}{extra}) alongside "
            f"LWR site(s) ({', '.join(lwr_sites)}). Aura components are not available "
            f"in Experience Builder for LWR sites. Migrate to LWC or reconsider template."
        )

    return issues


def check_hardcoded_colors_in_lwc_css(manifest_dir: Path) -> list[str]:
    """Warn when LWC CSS files use hardcoded hex colors instead of --dxp- tokens.

    For Experience Cloud LWR sites, component CSS should consume --dxp-* CSS
    custom property tokens. Hardcoded values break site-wide branding changes.
    """
    issues: list[str] = []
    lwc_dir = manifest_dir / "lwc"
    if not lwc_dir.exists():
        return issues

    import re
    hex_pattern = re.compile(r":\s*#[0-9a-fA-F]{3,6}\b")

    for css_file in sorted(lwc_dir.rglob("*.css")):
        try:
            content = css_file.read_text(encoding="utf-8")
        except OSError:
            continue

        matches = hex_pattern.findall(content)
        if matches:
            # Only flag if the file does NOT already use any --dxp- tokens
            uses_dxp = "--dxp-" in content
            if not uses_dxp:
                issues.append(
                    f"LWC CSS '{css_file.relative_to(manifest_dir)}' uses "
                    f"{len(matches)} hardcoded color value(s) and no --dxp-* tokens. "
                    f"For Experience Cloud LWR sites, consume --dxp-* branding tokens "
                    f"so site-wide branding changes propagate correctly."
                )

    return issues


def check_experience_bundle_guest_access(manifest_dir: Path) -> list[str]:
    """Warn when ExperienceBundle JSON indicates guest access is broadly enabled.

    A guest user profile with 'isEnabled: true' and no explicit page-level
    restrictions is a common overpermission pattern.
    This is a lightweight heuristic check — full guest profile review requires
    profile metadata inspection outside the bundle.
    """
    issues: list[str] = []
    experience_dir = manifest_dir / "experiences"
    if not experience_dir.exists():
        return issues

    import json
    for config_file in experience_dir.rglob("*.json"):
        try:
            data = json.loads(config_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Look for guestAccess or similar top-level keys that suggest broad exposure
        guest_access = data.get("guestAccess", None)
        if guest_access is True:
            site_name = data.get("label", config_file.parent.name)
            issues.append(
                f"Experience site '{site_name}' has guestAccess: true. "
                f"Verify the guest user profile permissions are scoped to minimum "
                f"necessary object/field access before go-live."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_experience_cloud_site_setup(manifest_dir: Path) -> list[str]:
    """Run all Experience Cloud site setup checks and return a list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_lwc_experience_targets(manifest_dir))
    issues.extend(check_aura_components_present(manifest_dir))
    issues.extend(check_hardcoded_colors_in_lwc_css(manifest_dir))
    issues.extend(check_experience_bundle_guest_access(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_site_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
