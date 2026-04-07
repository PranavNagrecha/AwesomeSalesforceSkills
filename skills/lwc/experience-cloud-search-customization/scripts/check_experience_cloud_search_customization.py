#!/usr/bin/env python3
"""Checker script for Experience Cloud Search Customization skill.

Checks Salesforce metadata files for common Experience Cloud search
configuration issues: federated search setup, search scope, and
LWR vs Aura component compatibility signals.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_search_customization.py [--help]
    python3 check_experience_cloud_search_customization.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Experience Cloud search "
            "configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_network_metadata(manifest_dir: Path) -> list[str]:
    """Check Experience Cloud site (Network) metadata files for search signals."""
    issues: list[str] = []
    network_dir = manifest_dir / "networks"
    if not network_dir.exists():
        return issues

    for network_file in network_dir.glob("*.network-meta.xml"):
        try:
            tree = ET.parse(network_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"{network_file.name}: XML parse error — {exc}")
            continue

        # Salesforce namespace stripping for portability
        def tag(element: ET.Element) -> str:
            return element.tag.split("}")[-1] if "}" in element.tag else element.tag

        # Check: guestChatterEnabled / allowMembersToFlag as proxy for guest access
        # Check: selfRegistrationEnabled as signal that guest UX matters
        self_reg = any(
            tag(el) == "selfRegistrationEnabled" and el.text and el.text.strip().lower() == "true"
            for el in root.iter()
        )
        if self_reg:
            # Self-registration implies guest-facing UX; surface a reminder
            issues.append(
                f"{network_file.name}: self-registration enabled — confirm "
                "Secure Guest User Record Access setting is reviewed and "
                "guest search scope is explicitly configured in Search Manager."
            )

    return issues


def check_custom_metadata_federated_search(manifest_dir: Path) -> list[str]:
    """Check for any federated search source custom metadata records."""
    issues: list[str] = []
    # Federated search sources can appear as CustomMetadata records or in the
    # site configuration. Check for any CustomMetadata directory.
    cmd_dir = manifest_dir / "customMetadata"
    if not cmd_dir.exists():
        return issues

    federated_files = list(cmd_dir.glob("FederatedSearchSource*.md-meta.xml"))
    if federated_files:
        for fed_file in federated_files:
            try:
                tree = ET.parse(fed_file)
                root = tree.getroot()
            except ET.ParseError as exc:
                issues.append(f"{fed_file.name}: XML parse error — {exc}")
                continue

            # Look for endpoint URL — warn if it looks like a plain HTTP URL
            for el in root.iter():
                local = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                if local == "value" and el.text and el.text.strip().startswith("http://"):
                    issues.append(
                        f"{fed_file.name}: federated search endpoint uses plain HTTP "
                        "(not HTTPS) — external endpoints must use HTTPS."
                    )

    return issues


def check_lwc_components_for_search_patterns(manifest_dir: Path) -> list[str]:
    """Warn if LWC HTML files reference the Aura search component by tag name."""
    issues: list[str] = []
    lwc_dir = manifest_dir / "lwc"
    if not lwc_dir.exists():
        # Also check a force-app style layout
        lwc_dir = manifest_dir / "force-app" / "main" / "default" / "lwc"
        if not lwc_dir.exists():
            return issues

    for html_file in lwc_dir.rglob("*.html"):
        try:
            content = html_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # The Aura search component is referenced as <c-search> or
        # <lightning-community-search> in Aura templates; in LWC HTML files
        # these would be unusual and signal a cross-template mis-use.
        if "<lightning-community-search" in content:
            issues.append(
                f"{html_file.relative_to(manifest_dir)}: references "
                "<lightning-community-search> — this is the Aura search "
                "component tag and is not supported on LWR sites. Use the "
                "standard LWR Search Bar + Search Results components instead."
            )

        # Warn on raw SOSL in LWC JS (searches that should go through Search Manager)
        if "FIND :" in content.upper() or "Database.search" in content:
            issues.append(
                f"{html_file.relative_to(manifest_dir)}: possible SOSL / Database.search "
                "reference in an LWC HTML file — confirm this is intentional and "
                "not a replacement for Experience Cloud's native Search Manager "
                "infrastructure."
            )

    for js_file in lwc_dir.rglob("*.js"):
        try:
            content = js_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "Database.search" in content:
            issues.append(
                f"{js_file.relative_to(manifest_dir)}: Database.search reference "
                "in LWC JS — confirm this is a specialized in-page search and not "
                "a replacement for the site-level Search Manager configuration."
            )

    return issues


def check_sharing_settings_for_guest(manifest_dir: Path) -> list[str]:
    """Check SharingSettings metadata for guest user record access setting."""
    issues: list[str] = []
    sharing_files = list(manifest_dir.glob("**/*SharingSettings*.settings-meta.xml"))
    sharing_files += list(manifest_dir.glob("**/SharingSettings.settings"))

    for sharing_file in sharing_files:
        try:
            tree = ET.parse(sharing_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"{sharing_file.name}: XML parse error — {exc}")
            continue

        for el in root.iter():
            local = el.tag.split("}")[-1] if "}" in el.tag else el.tag
            if local == "enableSecureGuestAccess":
                if el.text and el.text.strip().lower() == "false":
                    issues.append(
                        f"{sharing_file.name}: enableSecureGuestAccess is set to false. "
                        "Salesforce recommends enabling Secure Guest User Record Access "
                        "(Winter '21+). Disabling this setting may expose records to "
                        "guest users beyond intended sharing boundaries. Confirm this "
                        "is intentional and that guest search scope is explicitly "
                        "locked down in Search Manager."
                    )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def check_experience_cloud_search_customization(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_network_metadata(manifest_dir))
    issues.extend(check_custom_metadata_federated_search(manifest_dir))
    issues.extend(check_lwc_components_for_search_patterns(manifest_dir))
    issues.extend(check_sharing_settings_for_guest(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_search_customization(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
