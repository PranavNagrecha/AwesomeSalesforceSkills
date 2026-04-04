#!/usr/bin/env python3
"""Checker script for Login Forensics skill.

Validates Salesforce metadata relevant to login security configuration:
- Profile login hours restrictions
- Profile login IP range restrictions
- Login Flow attachments
- Session settings timeout values

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_login_forensics.py [--help]
    python3 check_login_forensics.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce Metadata API namespace
_SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(name: str) -> str:
    return f"{{{_SF_NS}}}{name}"


# ──────────────────────────────────────────────────────────────────────────────
# Check 1: Profiles missing login hour restrictions
# ──────────────────────────────────────────────────────────────────────────────

_PROFILES_THAT_SHOULD_HAVE_LOGIN_HOURS = {
    "System Administrator",
    "Standard User",
}

_HIGH_RISK_PROFILE_KEYWORDS = [
    "admin",
    "executive",
    "data export",
    "super user",
    "integration",
]


def _profile_is_high_risk(profile_name: str) -> bool:
    lower = profile_name.lower()
    return any(kw in lower for kw in _HIGH_RISK_PROFILE_KEYWORDS)


def check_profiles(manifest_dir: Path) -> list[str]:
    """Check profile metadata for missing login hours and IP ranges."""
    issues: list[str] = []
    profiles_dir = manifest_dir / "profiles"

    if not profiles_dir.exists():
        # Not an error — profiles may not be in this manifest
        return issues

    for profile_path in sorted(profiles_dir.glob("*.profile-meta.xml")):
        profile_name = profile_path.stem.replace(".profile-meta", "")
        try:
            tree = ET.parse(profile_path)
        except ET.ParseError as exc:
            issues.append(f"[{profile_name}] XML parse error: {exc}")
            continue

        root = tree.getroot()

        # Check for loginHours
        login_hours = root.findall(_tag("loginHours"))
        if not login_hours and _profile_is_high_risk(profile_name):
            issues.append(
                f"[{profile_name}] High-risk profile has no loginHours restriction. "
                "Consider restricting login to business hours to limit the attack window "
                "for credential-stuffing outside working hours."
            )

        # Check for loginIpRanges
        ip_ranges = root.findall(_tag("loginIpRanges"))
        if not ip_ranges and _profile_is_high_risk(profile_name):
            issues.append(
                f"[{profile_name}] High-risk profile has no loginIpRanges restriction. "
                "Consider adding IP range allowlists (Setup > Profiles > Login IP Ranges) "
                "to reduce the blast radius of compromised credentials."
            )

    return issues


# ──────────────────────────────────────────────────────────────────────────────
# Check 2: Session settings — timeout too long
# ──────────────────────────────────────────────────────────────────────────────

# Salesforce session timeout options (minutes). Values above this threshold
# are considered too permissive for security-sensitive orgs.
_SESSION_TIMEOUT_WARNING_THRESHOLD_MINUTES = 240  # 4 hours


def check_session_settings(manifest_dir: Path) -> list[str]:
    """Check SecuritySettings metadata for overly permissive session timeouts."""
    issues: list[str] = []

    # SecuritySettings is typically in settings/Security.settings-meta.xml
    settings_path = manifest_dir / "settings" / "Security.settings-meta.xml"
    if not settings_path.exists():
        return issues

    try:
        tree = ET.parse(settings_path)
    except ET.ParseError as exc:
        issues.append(f"[SecuritySettings] XML parse error: {exc}")
        return issues

    root = tree.getroot()

    # sessionTimeout is nested under sessionSettings > sessionTimeout
    session_settings = root.find(_tag("sessionSettings"))
    if session_settings is None:
        return issues

    timeout_el = session_settings.find(_tag("sessionTimeout"))
    if timeout_el is not None and timeout_el.text:
        # Timeout values in the metadata are strings like "TwoHours", "FourHours",
        # "EightHours", "TwelveHours", "TwentyFourHours", "ThirtyMinutes", etc.
        timeout_str = timeout_el.text.strip()
        long_timeouts = {
            "EightHours",
            "TwelveHours",
            "TwentyFourHours",
        }
        if timeout_str in long_timeouts:
            issues.append(
                f"[SecuritySettings] Session timeout is set to '{timeout_str}'. "
                "Sessions longer than 4 hours increase the window of opportunity for "
                "session token theft. Consider reducing to 'TwoHours' or less for "
                "security-sensitive orgs. (Setup > Session Settings > Timeout Value)"
            )

    # Check whether sessions are locked to IP
    lock_to_ip_el = session_settings.find(_tag("lockSessionsToIp"))
    if lock_to_ip_el is not None and lock_to_ip_el.text:
        if lock_to_ip_el.text.strip().lower() == "false":
            issues.append(
                "[SecuritySettings] 'Lock sessions to the IP address from which they "
                "originated' is disabled. Enabling this setting (Setup > Session Settings) "
                "prevents session token replay from a different IP address — a common "
                "technique in session hijacking attacks."
            )

    return issues


# ──────────────────────────────────────────────────────────────────────────────
# Check 3: Login Flow attachments — detect profiles with no Login Flow
# ──────────────────────────────────────────────────────────────────────────────

def check_login_flows(manifest_dir: Path) -> list[str]:
    """Check whether high-risk profiles have a Login Flow attached."""
    issues: list[str] = []

    # Login Flow attachments are stored in loginFlows/*.loginFlow-meta.xml
    login_flows_dir = manifest_dir / "loginFlows"
    if not login_flows_dir.exists():
        # No login flows directory present at all
        if any(
            (manifest_dir / "profiles").exists()
            and _profile_is_high_risk(p.stem.replace(".profile-meta", ""))
            for p in (manifest_dir / "profiles").glob("*.profile-meta.xml")
        ) if (manifest_dir / "profiles").exists() else []:
            issues.append(
                "[LoginFlows] No loginFlows directory found in manifest. "
                "Consider attaching Login Flows to high-risk profiles to enforce "
                "step-up authentication at login time."
            )
        return issues

    login_flow_files = list(login_flows_dir.glob("*.loginFlow-meta.xml"))
    if not login_flow_files:
        issues.append(
            "[LoginFlows] loginFlows directory is present but contains no Login Flow "
            "definitions. If step-up authentication is required for any profiles, "
            "configure a Login Flow in Setup > Login Flows."
        )
        return issues

    # Parse each Login Flow to check it references an active Flow version
    for lf_path in sorted(login_flow_files):
        try:
            tree = ET.parse(lf_path)
        except ET.ParseError as exc:
            issues.append(f"[LoginFlow:{lf_path.stem}] XML parse error: {exc}")
            continue

        root = tree.getroot()
        flow_el = root.find(_tag("flow"))
        enabled_el = root.find(_tag("useLightningRuntime"))

        if flow_el is None or not flow_el.text:
            issues.append(
                f"[LoginFlow:{lf_path.stem}] Login Flow definition has no associated "
                "Flow name. The flow attachment will not fire at login."
            )

        # useLightningRuntime should be true — classic runtime is deprecated
        if enabled_el is not None and enabled_el.text:
            if enabled_el.text.strip().lower() == "false":
                issues.append(
                    f"[LoginFlow:{lf_path.stem}] 'useLightningRuntime' is false. "
                    "Classic Flow runtime is deprecated. Migrate this Login Flow to "
                    "Lightning runtime to avoid breakage."
                )

    return issues


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def check_login_forensics(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_profiles(manifest_dir))
    issues.extend(check_session_settings(manifest_dir))
    issues.extend(check_login_flows(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for login security configuration gaps: "
            "profile login hours/IP restrictions, session timeout settings, "
            "and Login Flow attachments."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_login_forensics(manifest_dir)

    if not issues:
        print("No login security configuration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
