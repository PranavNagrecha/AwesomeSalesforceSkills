#!/usr/bin/env python3
"""Checker script for Remote Site Settings skill.

Checks Remote Site Settings metadata and Apex code for common misconfigurations.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_remote_site_settings.py [--help]
    python3 check_remote_site_settings.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Remote Site Settings and Apex callout code for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_remote_site_settings_metadata(manifest_dir: Path) -> list[str]:
    """Check RemoteSiteSetting metadata files for issues."""
    issues: list[str] = []

    rss_dir = manifest_dir / "remoteSiteSettings"
    if not rss_dir.exists():
        return issues

    for rss_file in rss_dir.glob("*.remoteSite"):
        try:
            tree = ET.parse(rss_file)
            root = tree.getroot()
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            rss_name = rss_file.stem

            # Check for disableProtocolSecurity=true on what appears to be HTTPS URL
            disable_protocol = root.find(f"{ns}disableProtocolSecurity")
            url_elem = root.find(f"{ns}url")
            if disable_protocol is not None and disable_protocol.text == "true":
                url = url_elem.text if url_elem is not None else ""
                if url.startswith("https://"):
                    issues.append(
                        f"Remote Site Setting '{rss_name}': "
                        "disableProtocolSecurity is true for an HTTPS URL. "
                        "This disables TLS/SSL validation for this endpoint. "
                        "Only set this for HTTP or self-signed certificate (sandbox) scenarios."
                    )

            # Check for HTTP URL (non-HTTPS) — warn for production use
            if url_elem is not None and url_elem.text and url_elem.text.startswith("http://"):
                issues.append(
                    f"Remote Site Setting '{rss_name}': "
                    f"URL uses HTTP (not HTTPS): '{url_elem.text}'. "
                    "Verify this is intentional — HTTP transmits data unencrypted."
                )

        except (ET.ParseError, OSError):
            pass

    return issues


def check_apex_callouts_for_missing_rss(manifest_dir: Path) -> list[str]:
    """Check Apex code for Http.send() patterns and compare to known Remote Site Settings."""
    issues: list[str] = []

    # Collect all registered Remote Site URLs
    registered_urls: set[str] = set()
    rss_dir = manifest_dir / "remoteSiteSettings"
    if rss_dir.exists():
        for rss_file in rss_dir.glob("*.remoteSite"):
            try:
                tree = ET.parse(rss_file)
                root = tree.getroot()
                ns = ""
                if root.tag.startswith("{"):
                    ns = root.tag.split("}")[0] + "}"
                url_elem = root.find(f"{ns}url")
                if url_elem is not None and url_elem.text:
                    registered_urls.add(url_elem.text.rstrip("/").lower())
            except (ET.ParseError, OSError):
                pass

    # Scan Apex classes for Http.send() with hardcoded URLs
    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        return issues

    url_pattern = re.compile(r'setEndpoint\(["\']((https?://[^"\']+))["\']', re.IGNORECASE)
    named_cred_pattern = re.compile(r'setEndpoint\(["\']callout:', re.IGNORECASE)

    for apex_file in apex_dir.glob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8")

            # Skip if using Named Credentials (they manage their own allowlist)
            if named_cred_pattern.search(content):
                continue

            # Find hardcoded endpoint URLs
            for match in url_pattern.finditer(content):
                endpoint_url = match.group(1)
                # Extract just the scheme + host
                url_parts = endpoint_url.split("/")
                if len(url_parts) >= 3:
                    base_url = "/".join(url_parts[:3]).lower()

                    # Check if this base URL has a Remote Site Setting
                    covered = any(base_url.startswith(rss_url) or rss_url.startswith(base_url)
                                  for rss_url in registered_urls)
                    if not covered:
                        issues.append(
                            f"Apex class '{apex_file.stem}': "
                            f"Hardcoded endpoint '{base_url}' may not have a Remote Site Setting. "
                            "Verify Setup > Security > Remote Site Settings covers this URL."
                        )
        except OSError:
            pass

    return issues


def check_remote_site_settings(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_remote_site_settings_metadata(manifest_dir))
    issues.extend(check_apex_callouts_for_missing_rss(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_remote_site_settings(manifest_dir)

    if not issues:
        print("No Remote Site Settings issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
