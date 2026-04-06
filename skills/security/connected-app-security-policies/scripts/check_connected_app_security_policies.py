#!/usr/bin/env python3
"""Checker script for Connected App Security Policies skill.

Inspects Salesforce ConnectedApp metadata XML files for common policy
misconfigurations documented in this skill:
  - IP relaxation set to relaxIpRanges (fully permissive)
  - PKCE and Require Secret both enabled simultaneously
  - Missing oauthPolicy block
  - High Assurance not configured (missing or empty)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_connected_app_security_policies.py [--manifest-dir PATH]

    PATH should be the root of a Salesforce SFDX project or a metadata
    directory that contains a 'connectedApps/' subfolder with .connectedApp
    XML files.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CONNECTED_APP_EXTENSION = ".connectedApp"
SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"

# IP relaxation values — worst to best
RELAXED_IP = "relaxIpRanges"
RELAXED_WITH_2FA = "relaxIpRangesWithSecondFactor"
ENFORCE_IP = "enforceIpRanges"

PERMISSIVE_IP_VALUES = {RELAXED_IP}

HIGH_ASSURANCE_STATES = {
    "highAssurance",
    "switchToHighAssurance",
    "blocked",
}


def _tag(local: str) -> str:
    """Return a namespace-qualified tag name."""
    return f"{{{SF_NAMESPACE}}}{local}"


def _text(element: ET.Element | None) -> str:
    """Return stripped text content of an element, or empty string."""
    if element is None:
        return ""
    return (element.text or "").strip()


def check_file(path: Path) -> list[str]:
    """Return a list of issue strings for a single .connectedApp file."""
    issues: list[str] = []
    app_name = path.stem

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"[{app_name}] XML parse error: {exc}"]

    root = tree.getroot()

    # --- oauthPolicy block ---
    oauth_policy = root.find(_tag("oauthPolicy"))
    if oauth_policy is None:
        issues.append(
            f"[{app_name}] Missing <oauthPolicy> block. "
            "IP relaxation and session policies cannot be audited."
        )
        return issues

    # --- IP Relaxation ---
    ip_relaxation_el = oauth_policy.find(_tag("ipRelaxation"))
    ip_relaxation = _text(ip_relaxation_el)

    if not ip_relaxation:
        issues.append(
            f"[{app_name}] <ipRelaxation> is absent or empty. "
            "Policy defaults to platform default — verify this is intentional."
        )
    elif ip_relaxation in PERMISSIVE_IP_VALUES:
        issues.append(
            f"[{app_name}] IP relaxation is '{ip_relaxation}' (fully permissive). "
            "Stolen tokens can be replayed from any network. "
            "Use 'enforceIpRanges' for server-to-server or "
            "'relaxIpRangesWithSecondFactor' for human-facing apps."
        )

    # --- PKCE vs Require Secret mutual exclusion ---
    oauth_config = root.find(_tag("oauthConfig"))
    if oauth_config is not None:
        pkce_el = oauth_config.find(_tag("requireProofKeyForCodeExchange"))
        require_secret_el = oauth_config.find(_tag("requireSecretForWebServerFlow"))

        pkce_enabled = _text(pkce_el).lower() == "true"
        require_secret_enabled = _text(require_secret_el).lower() == "true"

        if pkce_enabled and require_secret_enabled:
            issues.append(
                f"[{app_name}] PKCE and 'Require Secret for Web Server Flow' are both enabled. "
                "These are mutually exclusive — token exchange will fail at runtime. "
                "Disable 'requireSecretForWebServerFlow' when PKCE is active."
            )

    # --- High Assurance session policy ---
    # The sessionTimeout or high assurance level may be in oauthPolicy or a separate sessionPolicy
    # block depending on API version. Check both locations.
    session_level_el = oauth_policy.find(_tag("highAssuranceRequired"))
    if session_level_el is None:
        # Also check top-level sessionPolicy element (some API versions)
        session_policy = root.find(_tag("sessionPolicy"))
        if session_policy is not None:
            session_level_el = session_policy.find(_tag("requiredSessionLevel"))

    session_level = _text(session_level_el).lower() if session_level_el is not None else ""

    if not session_level:
        issues.append(
            f"[{app_name}] High Assurance session policy is not configured. "
            "For API-only Connected Apps consider setting to 'blocked' to deny "
            "low-assurance tokens."
        )
    elif session_level == "switchtohighassurance":
        issues.append(
            f"[{app_name}] High Assurance is set to 'switchToHighAssurance'. "
            "This prompts but does NOT block low-assurance sessions. "
            "If enforcement is the goal, change to 'blocked'."
        )

    return issues


def find_connected_app_files(manifest_dir: Path) -> list[Path]:
    """Recursively find all .connectedApp XML files under manifest_dir."""
    return sorted(manifest_dir.rglob(f"*{CONNECTED_APP_EXTENSION}"))


def check_manifest(manifest_dir: Path) -> list[str]:
    """Scan all Connected App metadata files and return consolidated issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    app_files = find_connected_app_files(manifest_dir)

    if not app_files:
        issues.append(
            f"No {CONNECTED_APP_EXTENSION} files found under {manifest_dir}. "
            "Ensure the path contains a 'connectedApps/' subfolder with metadata XML files."
        )
        return issues

    for app_file in app_files:
        issues.extend(check_file(app_file))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce ConnectedApp metadata XML files for common "
            "security policy misconfigurations."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory of the Salesforce metadata project "
            "(default: current directory). "
            "The script searches recursively for *.connectedApp files."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    print(f"Scanning: {manifest_dir}")
    issues = check_manifest(manifest_dir)

    if not issues:
        print("No Connected App security policy issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:\n")
    for issue in issues:
        print(f"  ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
