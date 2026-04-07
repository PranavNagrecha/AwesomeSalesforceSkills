#!/usr/bin/env python3
"""Checker script for Experience Cloud Authentication skill.

Scans Salesforce metadata in a project directory for common authentication
configuration issues specific to Experience Cloud custom login flows.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_authentication.py [--help]
    python3 check_experience_cloud_authentication.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud Authentication configuration and metadata "
            "for common issues: missing community parameter in SSO URLs, "
            "wrong handler interfaces, VF login pages on LWR sites."
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

def check_sso_url_missing_community(manifest_dir: Path) -> list[str]:
    """Warn if any LWC or Aura JS file redirects to /services/auth/sso/ without community param."""
    issues: list[str] = []
    js_files = list(manifest_dir.rglob("*.js"))
    for path in js_files:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "/services/auth/sso/" in content and "community" not in content.split("/services/auth/sso/")[1][:300]:
            issues.append(
                f"{path.relative_to(manifest_dir)}: Contains '/services/auth/sso/' redirect "
                "without a 'community' parameter — users will land on the internal org login "
                "instead of the Experience Cloud site after the IdP handshake."
            )
    return issues


def check_registration_handler_used_for_headless(manifest_dir: Path) -> list[str]:
    """Warn if an Apex class implements Auth.RegistrationHandler but also contains headless keywords."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls"))
    headless_keywords = ["headless", "HeadlessPasswordless", "HeadlessSelfReg", "passwordless"]
    for path in apex_files:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        implements_std = "Auth.RegistrationHandler" in content
        has_headless = any(kw.lower() in content.lower() for kw in headless_keywords)
        if implements_std and has_headless:
            issues.append(
                f"{path.relative_to(manifest_dir)}: Implements 'Auth.RegistrationHandler' but "
                "contains headless/passwordless keywords. Headless flows require "
                "'Auth.HeadlessSelfRegistrationHandler' — these are separate interfaces."
            )
    return issues


def check_vf_login_page_on_lwr_site(manifest_dir: Path) -> list[str]:
    """Warn if a Network metadata file references a VF login page on an LWR-type site."""
    issues: list[str] = []
    network_files = list(manifest_dir.rglob("*.network"))
    for path in network_files:
        try:
            tree = ET.parse(path)
        except ET.ParseError:
            continue
        root = tree.getroot()
        # Strip namespace if present
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        site_type_el = root.find(f"{ns}siteType")
        login_type_el = root.find(f"{ns}loginPageType")
        login_vf_el = root.find(f"{ns}loginPage")

        site_type = site_type_el.text if site_type_el is not None else ""
        login_type = login_type_el.text if login_type_el is not None else ""

        lwr_types = {"Lwr", "LWR", "MicroSite", "Microsite"}
        if site_type in lwr_types and login_type.lower() == "visualforce":
            vf_name = login_vf_el.text if login_vf_el is not None else "(unknown)"
            issues.append(
                f"{path.relative_to(manifest_dir)}: Site type '{site_type}' is LWR but "
                f"loginPageType is 'Visualforce' (page: {vf_name}). "
                "LWR sites ignore VF login pages — use an LWC with the "
                "'lightningCommunity__Page' target instead."
            )
    return issues


def check_missing_federation_identifier(manifest_dir: Path) -> list[str]:
    """Warn if RegistrationHandler-style Apex classes query users by email only without FederationIdentifier."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls"))
    for path in apex_files:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Auth.RegistrationHandler" not in content and "HeadlessSelfRegistrationHandler" not in content:
            continue
        lower = content.lower()
        queries_email_only = (
            "where email" in lower
            and "federationidentifier" not in lower
        )
        if queries_email_only:
            issues.append(
                f"{path.relative_to(manifest_dir)}: Registration handler queries users by email "
                "but does not use FederationIdentifier. Email-only matching produces duplicate "
                "user records when users change their IdP email address."
            )
    return issues


def check_headless_handler_missing_discovery(manifest_dir: Path) -> list[str]:
    """Warn if HeadlessSelfRegistrationHandler is present but HeadlessUserDiscoveryHandler is absent."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls"))
    has_self_reg = False
    has_discovery = False
    for path in apex_files:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "HeadlessSelfRegistrationHandler" in content:
            has_self_reg = True
        if "HeadlessUserDiscoveryHandler" in content:
            has_discovery = True
    if has_self_reg and not has_discovery:
        issues.append(
            "HeadlessSelfRegistrationHandler implementation found but no HeadlessUserDiscoveryHandler. "
            "Headless flows require both handlers: HeadlessUserDiscoveryHandler (to discover/route "
            "existing users) and HeadlessSelfRegistrationHandler (to register new users)."
        )
    return issues


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def check_experience_cloud_authentication(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sso_url_missing_community(manifest_dir))
    issues.extend(check_registration_handler_used_for_headless(manifest_dir))
    issues.extend(check_vf_login_page_on_lwr_site(manifest_dir))
    issues.extend(check_missing_federation_identifier(manifest_dir))
    issues.extend(check_headless_handler_missing_discovery(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_authentication(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
