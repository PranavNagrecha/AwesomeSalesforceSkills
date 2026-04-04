#!/usr/bin/env python3
"""Checker script for API Security and Rate Limiting skill.

Inspects Salesforce metadata (Connected App XML files) for common
API security misconfigurations: overly broad OAuth scopes, missing IP
restrictions, and permissive IP relaxation policies.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_api_security_and_rate_limiting.py --manifest-dir path/to/metadata
    python3 check_api_security_and_rate_limiting.py --manifest-dir force-app/main/default

The script recursively searches the manifest directory for
*.connectedApp-meta.xml files and evaluates each one.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Scopes considered high-risk for server-to-server integrations.
HIGH_RISK_SCOPES = {
    "full",
    "web",
}

# Scopes that are acceptable for typical headless integrations.
ACCEPTABLE_HEADLESS_SCOPES = {
    "api",
    "refresh_token",
    "offline_access",
}

# IP Relaxation values considered insecure for system integrations.
INSECURE_IP_RELAXATION = {
    "RelaxedForContactsAndLeads",
    "Relax",
    "RelaxedForExistingUsers",
}

# IP Relaxation value that is safest for server-to-server integrations.
SAFE_IP_RELAXATION = "EnforceThirdPartyLoginIP"

# Session timeout threshold in seconds — warn if set longer than this.
# 28800 seconds = 8 hours; appropriate upper bound for most integrations.
MAX_SAFE_SESSION_TIMEOUT_SECONDS = 28800


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _ns_strip(tag: str) -> str:
    """Strip XML namespace prefix from a tag name."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _find_text(element: ET.Element, path_parts: list[str]) -> str | None:
    """Walk a path of tag names (namespace-agnostic) and return text of the leaf."""
    current = element
    for part in path_parts:
        match = None
        for child in current:
            if _ns_strip(child.tag) == part:
                match = child
                break
        if match is None:
            return None
        current = match
    return current.text


def _find_all_text(element: ET.Element, tag: str) -> list[str]:
    """Return text content of all direct children matching tag (namespace-agnostic)."""
    return [
        child.text.strip()
        for child in element
        if _ns_strip(child.tag) == tag and child.text
    ]


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_connected_app(path: Path) -> list[str]:
    """Return a list of issue strings for a single Connected App metadata file."""
    issues: list[str] = []
    app_name = path.stem.replace(".connectedApp-meta", "").replace(".connectedApp", "")

    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except ET.ParseError as exc:
        issues.append(f"[{app_name}] Could not parse XML: {exc}")
        return issues

    # -----------------------------------------------------------------------
    # 1. OAuth scope checks
    # -----------------------------------------------------------------------
    # Scopes may appear as <scopes> children directly under root, or under
    # <oauthConfig><scopes> depending on the metadata shape.
    scope_elements: list[str] = []
    for child in root:
        tag = _ns_strip(child.tag)
        if tag == "scopes":
            if child.text:
                scope_elements.append(child.text.strip())
        elif tag == "oauthConfig":
            scope_elements.extend(_find_all_text(child, "scopes"))

    granted_scopes = {s.lower() for s in scope_elements}

    for risky_scope in HIGH_RISK_SCOPES:
        if risky_scope in granted_scopes:
            issues.append(
                f"[{app_name}] High-risk OAuth scope granted: '{risky_scope}'. "
                f"Replace with 'api' (and 'refresh_token' if offline access is needed) "
                f"for server-to-server integrations."
            )

    if not granted_scopes:
        issues.append(
            f"[{app_name}] No OAuth scopes found in metadata. "
            f"Verify the Connected App metadata is complete and scopes are explicitly declared."
        )

    # -----------------------------------------------------------------------
    # 2. IP Relaxation policy check
    # -----------------------------------------------------------------------
    ip_relaxation: str | None = None
    for child in root:
        tag = _ns_strip(child.tag)
        if tag == "ipRelaxation" and child.text:
            ip_relaxation = child.text.strip()
            break
        elif tag == "oauthConfig":
            val = _find_text(child, ["ipRelaxation"])
            if val:
                ip_relaxation = val.strip()
                break

    if ip_relaxation is None:
        issues.append(
            f"[{app_name}] IP Relaxation policy not found in metadata. "
            f"Ensure 'ipRelaxation' is explicitly set to '{SAFE_IP_RELAXATION}' "
            f"for all server-to-server Connected Apps."
        )
    elif ip_relaxation in INSECURE_IP_RELAXATION:
        issues.append(
            f"[{app_name}] Insecure IP Relaxation policy: '{ip_relaxation}'. "
            f"For server-to-server integrations, use '{SAFE_IP_RELAXATION}' "
            f"to enforce IP ranges on every request."
        )
    elif ip_relaxation != SAFE_IP_RELAXATION:
        # Unknown/intermediate value — warn but do not hard-fail
        issues.append(
            f"[{app_name}] Unrecognized IP Relaxation value: '{ip_relaxation}'. "
            f"Verify this is the intended policy. '{SAFE_IP_RELAXATION}' is recommended "
            f"for server-to-server integrations."
        )

    # -----------------------------------------------------------------------
    # 3. Session timeout check
    # -----------------------------------------------------------------------
    session_timeout: str | None = None
    for child in root:
        tag = _ns_strip(child.tag)
        if tag == "sessionTimeout" and child.text:
            session_timeout = child.text.strip()
            break
        elif tag == "oauthConfig":
            val = _find_text(child, ["sessionTimeout"])
            if val:
                session_timeout = val.strip()
                break

    if session_timeout is not None:
        # Salesforce stores timeout as an enum string (e.g., "TwelveHours", "TwentyFourHours")
        # or in some API versions as seconds. Map known enum values to seconds.
        timeout_map = {
            "FifteenMinutes": 900,
            "ThirtyMinutes": 1800,
            "OneHour": 3600,
            "TwoHours": 7200,
            "FourHours": 14400,
            "EightHours": 28800,
            "TwelveHours": 43200,
            "TwentyFourHours": 86400,
        }
        timeout_seconds = timeout_map.get(session_timeout)
        if timeout_seconds is None:
            # Try parsing as integer (seconds)
            try:
                timeout_seconds = int(session_timeout)
            except ValueError:
                timeout_seconds = None

        if timeout_seconds is not None and timeout_seconds > MAX_SAFE_SESSION_TIMEOUT_SECONDS:
            issues.append(
                f"[{app_name}] Session timeout is set to '{session_timeout}' "
                f"({timeout_seconds}s), which exceeds the recommended maximum of "
                f"{MAX_SAFE_SESSION_TIMEOUT_SECONDS}s (8 hours). "
                f"Use shorter timeouts and rely on refresh tokens for long-running integrations."
            )

    # -----------------------------------------------------------------------
    # 4. Refresh token policy check
    # -----------------------------------------------------------------------
    refresh_token_policy: str | None = None
    for child in root:
        tag = _ns_strip(child.tag)
        if tag == "refreshTokenPolicy" and child.text:
            refresh_token_policy = child.text.strip()
            break
        elif tag == "oauthConfig":
            val = _find_text(child, ["refreshTokenPolicy"])
            if val:
                refresh_token_policy = val.strip()
                break

    if refresh_token_policy is None:
        # Not all Connected Apps use refresh tokens; skip if scopes don't include it
        if "refresh_token" in granted_scopes or "offline_access" in granted_scopes:
            issues.append(
                f"[{app_name}] Connected App grants 'refresh_token' or 'offline_access' scope "
                f"but 'refreshTokenPolicy' is not set in metadata. "
                f"Configure an explicit expiry policy rather than leaving refresh tokens "
                f"valid indefinitely."
            )
    elif "infinite" in refresh_token_policy.lower() or "validuntilrevoked" in refresh_token_policy.lower().replace("_", "").replace("-", ""):
        issues.append(
            f"[{app_name}] Refresh token policy is set to '{refresh_token_policy}' "
            f"(no expiry). Configure a specific expiry period for production integrations "
            f"to limit the window of exposure from a compromised refresh token."
        )

    return issues


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def check_all_connected_apps(manifest_dir: Path) -> list[str]:
    """Find and check all Connected App metadata files under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    connected_app_files = list(manifest_dir.rglob("*.connectedApp-meta.xml"))
    if not connected_app_files:
        # Also check for non-.meta extension (older sfdx packaging)
        connected_app_files = list(manifest_dir.rglob("*.connectedApp"))

    if not connected_app_files:
        issues.append(
            f"No Connected App metadata files found under {manifest_dir}. "
            f"This check requires *.connectedApp-meta.xml files to be present. "
            f"If Connected Apps are configured in the org but not in source, "
            f"retrieve them with 'sf project retrieve start --metadata ConnectedApp'."
        )
        return issues

    for app_path in sorted(connected_app_files):
        app_issues = check_connected_app(app_path)
        issues.extend(app_issues)

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Connected App metadata for API security misconfigurations: "
            "overly broad OAuth scopes, missing IP restrictions, insecure IP relaxation policies, "
            "and excessive session timeouts."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_all_connected_apps(manifest_dir)

    if not issues:
        print("No API security issues found in Connected App metadata.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
