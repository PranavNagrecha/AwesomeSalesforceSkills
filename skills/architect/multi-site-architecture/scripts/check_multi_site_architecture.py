#!/usr/bin/env python3
"""Checker script for Multi-Site Architecture skill.

Scans Salesforce DX project metadata to detect anti-patterns and risks
described in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Checks performed:
  1. Hardcoded production custom domain URLs in Apex and Flow metadata
  2. LWC components that appear to be used in Experience Cloud (isExposed=true)
     but lack @api property declarations (no per-site configurability)
  3. Session-token-like strings passed as URL parameters in Apex (XSS / session leak risk)
  4. Custom metadata types for site URL configuration (presence is good; absence is a warning)

Usage:
    python3 check_multi_site_architecture.py [--help]
    python3 check_multi_site_architecture.py --manifest-dir path/to/sfdx/project
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Matches hardcoded https:// URLs that include a company TLD (not .salesforce.com,
# not .my.site.com, not .force.com) — likely production custom domains embedded in code.
_HARDCODED_DOMAIN_RE = re.compile(
    r"""https://(?![\w-]+\.(?:salesforce|my\.site|force|visualforce|lightning)\.com)"""
    r"""[\w-]+\.[\w.-]+""",
    re.IGNORECASE,
)

# Matches session ID / token patterns passed as URL parameters — a known anti-pattern
# for cross-site navigation.
_SESSION_IN_URL_RE = re.compile(
    r"""['\"][^'"]*\?[^'"]*(?:sessionId|session_id|sid|authToken|auth_token|accessToken|access_token)="""
    r"""[^'\"]*['\"]""",
    re.IGNORECASE,
)

# Matches window.location assignments or href constructions that include session-like params.
_SESSION_IN_HREF_RE = re.compile(
    r"""(?:href|location\.href|location\.replace)\s*[=+]\s*[^;]*(?:sessionId|session_id|sid|authToken)[^;]*;""",
    re.IGNORECASE,
)

# Detect APEX string literals that look like bare custom domain URLs (not in comments).
_APEX_STRING_URL_RE = re.compile(
    r"""'https://[\w-]+\.[\w-]+\.[a-z]{2,}(?:/[^']*)?'""",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    if not root.is_dir():
        return []
    return [p for p in root.rglob("*") if p.suffix.lower() in suffixes]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _is_salesforce_url(url: str) -> bool:
    """Return True if the URL is a Salesforce-owned domain (not a custom domain)."""
    salesforce_domains = (
        ".salesforce.com",
        ".my.site.com",
        ".force.com",
        ".visualforce.com",
        ".lightning.force.com",
        ".sandbox.my.site.com",
    )
    return any(d in url.lower() for d in salesforce_domains)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_hardcoded_custom_domain_in_apex(manifest_dir: Path) -> list[str]:
    """Warn when Apex classes contain hardcoded non-Salesforce HTTPS URLs."""
    issues: list[str] = []
    apex_dir = manifest_dir / "force-app" / "main" / "default" / "classes"
    if not apex_dir.exists():
        # Try alternate common paths
        apex_dir = manifest_dir / "classes"

    for apex_file in _iter_files(apex_dir, (".cls",)):
        text = _read_text(apex_file)
        matches = _APEX_STRING_URL_RE.findall(text)
        for match in matches:
            url = match.strip("'")
            if not _is_salesforce_url(url):
                issues.append(
                    f"[hardcoded-url] {apex_file.name}: hardcoded non-Salesforce URL "
                    f"'{url}' found in Apex string literal. "
                    "Externalize site base URLs via Custom Metadata or Named Credentials — "
                    "hardcoded URLs break sandbox environments."
                )
    return issues


def check_session_in_url_apex(manifest_dir: Path) -> list[str]:
    """Warn when Apex constructs URLs that include session or auth token parameters."""
    issues: list[str] = []
    apex_dir = manifest_dir / "force-app" / "main" / "default" / "classes"
    if not apex_dir.exists():
        apex_dir = manifest_dir / "classes"

    for apex_file in _iter_files(apex_dir, (".cls",)):
        text = _read_text(apex_file)
        if _SESSION_IN_URL_RE.search(text):
            issues.append(
                f"[session-in-url] {apex_file.name}: URL construction that includes "
                "a session ID or auth token as a query parameter detected. "
                "Passing session tokens via URL is a security anti-pattern and does not "
                "work for cross-site navigation in Experience Cloud. "
                "Use SSO via an external IdP for cross-site authentication."
            )
    return issues


def check_session_in_url_lwc(manifest_dir: Path) -> list[str]:
    """Warn when LWC JavaScript constructs URLs with session token parameters."""
    issues: list[str] = []
    lwc_dir = manifest_dir / "force-app" / "main" / "default" / "lwc"
    if not lwc_dir.exists():
        lwc_dir = manifest_dir / "lwc"

    for js_file in _iter_files(lwc_dir, (".js",)):
        text = _read_text(js_file)
        if _SESSION_IN_HREF_RE.search(text) or _SESSION_IN_URL_RE.search(text):
            issues.append(
                f"[session-in-url-lwc] {js_file.name}: LWC JavaScript constructs "
                "a URL with a session ID or auth token parameter. "
                "This is a security anti-pattern and will not provide cross-site "
                "authentication in Experience Cloud. Use SSO via external IdP."
            )
    return issues


def check_lwc_experience_cloud_api_properties(manifest_dir: Path) -> list[str]:
    """Warn when Experience Cloud LWC components have no @api properties (no per-site config)."""
    issues: list[str] = []
    lwc_dir = manifest_dir / "force-app" / "main" / "default" / "lwc"
    if not lwc_dir.exists():
        lwc_dir = manifest_dir / "lwc"

    if not lwc_dir.is_dir():
        return issues

    for meta_file in lwc_dir.rglob("*.js-meta.xml"):
        text = _read_text(meta_file)
        # Check if the component targets Experience Cloud
        is_experience_cloud = (
            "lightningCommunity__Page" in text
            or "lightningCommunity__Default" in text
            or "lightningCommunity__Theme" in text
        )
        if not is_experience_cloud:
            continue

        # Check if isExposed is true
        if "<isExposed>true</isExposed>" not in text:
            continue

        # Check if there are any @api property declarations in the component's JS
        component_dir = meta_file.parent
        js_files = list(component_dir.glob("*.js"))
        has_api_props = False
        for js_file in js_files:
            if "@api" in _read_text(js_file):
                has_api_props = True
                break

        if not has_api_props:
            issues.append(
                f"[no-api-properties] {meta_file.parent.name}: Experience Cloud LWC component "
                "is exposed in Experience Builder but has no @api properties. "
                "Components shared across multiple sites should expose @api properties "
                "so per-site configuration (labels, links, disclaimers) can be set in "
                "Experience Builder without code changes."
            )

    return issues


def check_custom_metadata_site_url_config(manifest_dir: Path) -> list[str]:
    """Advisory: flag if no Custom Metadata type named with 'Site' and 'Config' or 'URL' exists.

    Absence is not necessarily wrong, but it is a signal to verify that site base URLs
    are externalized via some mechanism.
    """
    issues: list[str] = []
    cmd_dir = manifest_dir / "force-app" / "main" / "default" / "customMetadata"
    if not cmd_dir.exists():
        cmd_dir = manifest_dir / "customMetadata"

    if not cmd_dir.is_dir():
        # No custom metadata at all — advisory only
        issues.append(
            "[advisory] No customMetadata directory found. If this project uses "
            "Experience Cloud sites with custom domains, verify that site base URLs "
            "are externalized via Custom Metadata, Custom Settings, or Named Credentials "
            "rather than hardcoded in Apex or Flow. See references/llm-anti-patterns.md."
        )
        return issues

    # Look for any Custom Metadata type that looks like a site URL config
    has_site_url_config = False
    for md_file in cmd_dir.rglob("*.md-meta.xml"):
        name = md_file.name.lower()
        if ("site" in name or "community" in name or "portal" in name) and (
            "url" in name or "config" in name or "setting" in name
        ):
            has_site_url_config = True
            break

    if not has_site_url_config:
        issues.append(
            "[advisory] No site URL configuration Custom Metadata record detected. "
            "For multi-site architectures with custom domains, it is recommended to "
            "store the site base URL per environment in Custom Metadata "
            "(e.g., Site_Config__mdt) so Apex, Flow, and components can reference "
            "the correct URL without hardcoding."
        )

    return issues


def check_hardcoded_domain_in_flow(manifest_dir: Path) -> list[str]:
    """Warn when Flow metadata contains hardcoded non-Salesforce URLs in string values."""
    issues: list[str] = []
    flow_dir = manifest_dir / "force-app" / "main" / "default" / "flows"
    if not flow_dir.exists():
        flow_dir = manifest_dir / "flows"

    for flow_file in _iter_files(flow_dir, (".flow-meta.xml",)):
        text = _read_text(flow_file)
        matches = _HARDCODED_DOMAIN_RE.findall(text)
        for match in matches:
            if not _is_salesforce_url(match):
                issues.append(
                    f"[hardcoded-url-flow] {flow_file.name}: Flow metadata contains "
                    f"hardcoded non-Salesforce URL '{match}'. "
                    "Use Custom Metadata or a Formula to look up the environment-specific "
                    "site URL instead."
                )
                break  # One warning per flow file is sufficient

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_multi_site_architecture(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_hardcoded_custom_domain_in_apex(manifest_dir))
    issues.extend(check_session_in_url_apex(manifest_dir))
    issues.extend(check_session_in_url_lwc(manifest_dir))
    issues.extend(check_lwc_experience_cloud_api_properties(manifest_dir))
    issues.extend(check_hardcoded_domain_in_flow(manifest_dir))
    issues.extend(check_custom_metadata_site_url_config(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce DX project metadata for multi-site Experience Cloud "
            "anti-patterns described in the multi-site-architecture skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_multi_site_architecture(manifest_dir)

    advisory = [i for i in issues if i.startswith("[advisory]")]
    warnings = [i for i in issues if not i.startswith("[advisory]")]

    if warnings:
        for issue in warnings:
            print(f"WARN: {issue}", file=sys.stderr)

    if advisory:
        for issue in advisory:
            print(f"INFO: {issue}")

    if not issues:
        print("No issues found.")
        return 0

    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
