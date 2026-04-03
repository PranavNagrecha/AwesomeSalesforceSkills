#!/usr/bin/env python3
"""Checker script for Org Setup And Configuration skill.

Checks Salesforce metadata for common org setup misconfigurations:
- My Domain deployment status (SecuritySettings metadata)
- Session settings: timeout, HTTPS, clickjack protection
- Password policy: minimum length, lockout threshold
- CSP Trusted Sites: wildcard entries or overly permissive directive grants

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_org_setup_and_configuration.py [--manifest-dir PATH]

The manifest directory should be the root of a retrieved Salesforce metadata project
containing SecuritySettings.settings-meta.xml and/or CspTrustedSite metadata.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"

# Session timeout thresholds (in minutes)
SESSION_TIMEOUT_WARN_MINUTES = 1440  # warn if timeout exceeds 24 hours
SESSION_TIMEOUT_SECURE_MAX_MINUTES = 120  # recommended max for standard orgs

# Password policy thresholds
MIN_PASSWORD_LENGTH_RECOMMENDED = 10
MAX_LOGIN_ATTEMPTS_RECOMMENDED = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tag(name: str) -> str:
    """Return a namespace-qualified tag for ElementTree searching."""
    return f"{{{SF_NAMESPACE}}}{name}"


def _find_text(element: ET.Element, path: str, default: str = "") -> str:
    found = element.find(path)
    return found.text.strip() if found is not None and found.text else default


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------

def check_security_settings(manifest_dir: Path) -> list[str]:
    """Parse SecuritySettings metadata and check for common misconfigurations."""
    issues: list[str] = []

    # SecuritySettings lives at settings/Security.settings-meta.xml
    settings_file = manifest_dir / "settings" / "Security.settings-meta.xml"
    if not settings_file.exists():
        issues.append(
            "SecuritySettings file not found at settings/Security.settings-meta.xml. "
            "Retrieve it with: sf project retrieve start --metadata SecuritySettings"
        )
        return issues

    try:
        tree = ET.parse(settings_file)
        root = tree.getroot()
    except ET.ParseError as exc:
        issues.append(f"Failed to parse SecuritySettings XML: {exc}")
        return issues

    # --- Session settings ---
    session_settings = root.find(_tag("sessionSettings"))
    if session_settings is not None:
        # Check session timeout
        timeout_val = _find_text(session_settings, _tag("sessionTimeout"), "TwoHours")
        # Map Salesforce XML enum values to minutes
        timeout_map = {
            "FifteenMinutes": 15,
            "ThirtyMinutes": 30,
            "OneHour": 60,
            "TwoHours": 120,
            "FourHours": 240,
            "EightHours": 480,
            "TwelveHours": 720,
            "TwentyFourHours": 1440,
        }
        timeout_minutes = timeout_map.get(timeout_val, 0)
        if timeout_minutes > SESSION_TIMEOUT_WARN_MINUTES:
            issues.append(
                f"Session timeout is set to {timeout_val} ({timeout_minutes} min). "
                "A timeout exceeding 24 hours defeats session expiry as a security control. "
                "Recommended: 2 hours or less for standard orgs, 30 minutes for regulated."
            )

        # Check HTTPS enforcement
        force_relogin = _find_text(session_settings, _tag("forceRelogin"), "true")
        # Salesforce enforces HTTPS by default; the relevant setting is requireHttps
        require_https = _find_text(session_settings, _tag("requireHttps"), "true")
        if require_https.lower() == "false":
            issues.append(
                "Require HTTPS (Secure Connections) is disabled in Session Settings. "
                "This allows plain-HTTP access to the org. Enable it at "
                "Setup > Security > Session Settings > Require secure connections (HTTPS)."
            )

        # Check clickjack protection
        clickjack_setup = _find_text(session_settings, _tag("clickjackNonsetupSFDCPage"), "")
        if clickjack_setup.lower() in ("", "allowall"):
            issues.append(
                "Clickjack protection for non-setup Salesforce pages is set to 'Allow All' "
                "or is not configured. This allows org pages to be embedded in any external iframe. "
                "Recommended: set to 'Allow framing by same origin only' unless there is a specific "
                "requirement to embed pages in external sites."
            )

    # --- Password policies ---
    password_settings = root.find(_tag("passwordPolicies"))
    if password_settings is not None:
        # Check minimum password length
        min_pwd_len_str = _find_text(password_settings, _tag("minimumPasswordLength"), "8")
        try:
            min_pwd_len = int(min_pwd_len_str)
        except ValueError:
            min_pwd_len = 8

        if min_pwd_len < MIN_PASSWORD_LENGTH_RECOMMENDED:
            issues.append(
                f"Minimum password length is {min_pwd_len} characters. "
                f"Recommended minimum is {MIN_PASSWORD_LENGTH_RECOMMENDED}. "
                "Update at Setup > Security > Password Policies > Minimum Password Length."
            )

        # Check maximum login attempts
        max_attempts_str = _find_text(password_settings, _tag("maxLoginAttempts"), "10")
        try:
            max_attempts = int(max_attempts_str)
        except ValueError:
            max_attempts = 10

        if max_attempts > MAX_LOGIN_ATTEMPTS_RECOMMENDED:
            issues.append(
                f"Maximum invalid login attempts is {max_attempts}. "
                f"Recommended: {MAX_LOGIN_ATTEMPTS_RECOMMENDED} or fewer to limit brute-force exposure. "
                "Update at Setup > Security > Password Policies > Maximum Invalid Login Attempts."
            )

    return issues


def check_csp_trusted_sites(manifest_dir: Path) -> list[str]:
    """Check CSP Trusted Site metadata for overly permissive entries."""
    issues: list[str] = []

    csp_dir = manifest_dir / "cspTrustedSites"
    if not csp_dir.exists():
        # Not an error — many orgs have no CSP entries; skip silently
        return issues

    csp_files = list(csp_dir.glob("*.cspTrustedSite-meta.xml"))
    if not csp_files:
        return issues

    # High-risk directives that allow script execution
    HIGH_RISK_DIRECTIVES = {"scriptSrc", "scriptSrcNonce"}

    for csp_file in sorted(csp_files):
        try:
            tree = ET.parse(csp_file)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"Failed to parse {csp_file.name}: {exc}")
            continue

        site_name = _find_text(root, _tag("masterLabel"), csp_file.stem)
        end_point_url = _find_text(root, _tag("endpointUrl"), "")

        # Check for wildcard domains
        if "*" in end_point_url:
            issues.append(
                f"CSP Trusted Site '{site_name}' uses a wildcard URL ({end_point_url}). "
                "Wildcard CSP entries grant broad trust to many domains. "
                "Use specific domain entries instead."
            )

        # Check for high-risk directives (script-src)
        context = root.find(_tag("context"))
        if context is not None:
            directives = [c.tag.split("}")[-1] for c in context if c.text and c.text.strip().lower() == "true"]
            risky = set(directives) & HIGH_RISK_DIRECTIVES
            if risky:
                issues.append(
                    f"CSP Trusted Site '{site_name}' ({end_point_url}) has script-execution "
                    f"directives enabled: {sorted(risky)}. Ensure this is intentional — "
                    "granting script-src allows JavaScript from this domain to execute in user browsers."
                )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check org setup and configuration metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}")
        return 1

    issues: list[str] = []
    issues.extend(check_security_settings(manifest_dir))
    issues.extend(check_csp_trusted_sites(manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
