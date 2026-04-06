#!/usr/bin/env python3
"""Checker script for Session Management And Timeout skill.

Checks org metadata or configuration relevant to session management and timeout.
Parses SecuritySettings metadata XML and profile XML for session configuration issues.
Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_session_management_and_timeout.py [--help]
    python3 check_session_management_and_timeout.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce Metadata API valid sessionTimeout enum values
VALID_TIMEOUT_ENUMS = {
    "FifteenMinutes",
    "ThirtyMinutes",
    "SixtyMinutes",
    "TwoHours",
    "FourHours",
    "EightHours",
    "TwelveHours",
    "TwentyFourHours",
}

# Timeout enum values considered too permissive for production orgs
PERMISSIVE_TIMEOUTS = {"TwelveHours", "TwentyFourHours"}

# Namespace used in Salesforce metadata XML
SF_NS = "http://soap.sforce.com/2006/04/metadata"
NS = {"sf": SF_NS}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Session Management And Timeout configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_security_settings(manifest_dir: Path) -> list[Path]:
    """Find SecuritySettings metadata files."""
    candidates: list[Path] = []
    for pattern in ["**/SecuritySettings.settings", "**/SecuritySettings.settings-meta.xml"]:
        candidates.extend(manifest_dir.glob(pattern))
    return candidates


def find_profile_files(manifest_dir: Path) -> list[Path]:
    """Find profile metadata files."""
    candidates: list[Path] = []
    for pattern in ["**/profiles/*.profile", "**/profiles/*.profile-meta.xml"]:
        candidates.extend(manifest_dir.glob(pattern))
    return candidates


def check_security_settings(file_path: Path) -> list[str]:
    """Parse a SecuritySettings XML file and check for session issues."""
    issues: list[str] = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        issues.append(f"Cannot parse {file_path}: {e}")
        return issues

    # Check sessionTimeout value
    timeout_el = root.find(".//sf:sessionTimeout", NS)
    if timeout_el is None:
        # Try without namespace (some metadata exports omit it)
        timeout_el = root.find(".//sessionTimeout")

    if timeout_el is not None and timeout_el.text:
        val = timeout_el.text.strip()
        if val not in VALID_TIMEOUT_ENUMS:
            issues.append(
                f"Invalid sessionTimeout value '{val}' in {file_path}. "
                f"Must be one of: {', '.join(sorted(VALID_TIMEOUT_ENUMS))}"
            )
        elif val in PERMISSIVE_TIMEOUTS:
            issues.append(
                f"Overly permissive sessionTimeout '{val}' in {file_path}. "
                f"Consider TwoHours or FourHours for production orgs."
            )

    # Check lockSessionsToIp
    lock_ip_el = root.find(".//sf:lockSessionsToIp", NS)
    if lock_ip_el is None:
        lock_ip_el = root.find(".//lockSessionsToIp")

    if lock_ip_el is not None and lock_ip_el.text:
        if lock_ip_el.text.strip().lower() == "true":
            issues.append(
                f"Session IP locking is enabled in {file_path}. "
                f"Verify that all user populations have stable egress IPs "
                f"(no rotating VPN, mobile carrier, or split-tunnel scenarios)."
            )

    # Check forceLogoutOnSessionTimeout
    force_logout_el = root.find(".//sf:forceLogoutOnSessionTimeout", NS)
    if force_logout_el is None:
        force_logout_el = root.find(".//forceLogoutOnSessionTimeout")

    if force_logout_el is None or (force_logout_el.text and force_logout_el.text.strip().lower() != "true"):
        issues.append(
            f"forceLogoutOnSessionTimeout is not explicitly set to true in {file_path}. "
            f"Users may not be fully logged out when the session expires."
        )

    return issues


def check_profile_session_settings(file_path: Path) -> list[str]:
    """Parse a Profile XML file and check for session-related configuration."""
    issues: list[str] = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        issues.append(f"Cannot parse {file_path}: {e}")
        return issues

    profile_name = file_path.stem.replace(".profile-meta", "").replace(".profile", "")

    # Check for profile-level session timeout
    timeout_el = root.find(".//sf:sessionTimeout", NS)
    if timeout_el is None:
        timeout_el = root.find(".//sessionTimeout")

    if timeout_el is not None and timeout_el.text:
        val = timeout_el.text.strip()
        if val not in VALID_TIMEOUT_ENUMS:
            issues.append(
                f"Invalid sessionTimeout value '{val}' in profile '{profile_name}' ({file_path}). "
                f"Must be one of: {', '.join(sorted(VALID_TIMEOUT_ENUMS))}"
            )

    return issues


def check_session_management_and_timeout(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check SecuritySettings files
    security_files = find_security_settings(manifest_dir)
    if not security_files:
        issues.append(
            f"No SecuritySettings metadata file found in {manifest_dir}. "
            f"Session timeout should be managed as metadata for repeatable deployment."
        )
    else:
        for sf in security_files:
            issues.extend(check_security_settings(sf))

    # Check profile-level session settings
    profile_files = find_profile_files(manifest_dir)
    for pf in profile_files:
        issues.extend(check_profile_session_settings(pf))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_session_management_and_timeout(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
