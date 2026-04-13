#!/usr/bin/env python3
"""Checker script for Integration Admin Connected Apps skill.

Checks Connected App metadata for common security misconfigurations.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_integration_admin_connected_apps.py [--help]
    python3 check_integration_admin_connected_apps.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Connected App metadata for common security misconfigurations.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_connected_app(app_file: Path) -> list[str]:
    """Check a ConnectedApp metadata file for common issues."""
    issues: list[str] = []

    try:
        tree = ET.parse(app_file)
        root = tree.getroot()
        # Strip namespace if present
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"
    except ET.ParseError:
        return issues

    app_name = app_file.stem

    # Check OAuth settings
    oauth_config = root.find(f"{ns}oauthConfig")
    if oauth_config is None:
        return issues  # Not an OAuth app — skip

    # Check for scopes — warn if 'full' scope is granted (overly broad)
    scopes = [s.text for s in oauth_config.findall(f"{ns}scopes") if s.text]
    if "Full" in scopes or "full" in scopes:
        issues.append(
            f"Connected App '{app_name}': OAuth scope 'Full' is granted. "
            "This grants all permissions the user has. "
            "Prefer specific scopes (api, refresh_token) for integration apps."
        )

    # Check session timeout — very long sessions may be a risk
    session_timeout = oauth_config.find(f"{ns}oauthClientCredentialUser")
    if session_timeout is not None and session_timeout.text:
        issues.append(
            f"Connected App '{app_name}': Client credentials user '{session_timeout.text}' configured. "
            "Ensure this is a dedicated integration user, not an admin user."
        )

    # Check for IP relaxation setting
    # Note: oauthPolicies are in the ConnectedApp, not oauthConfig
    ip_relaxation = root.find(f"{ns}oauthPolicy")
    if ip_relaxation is not None:
        permitted_users = ip_relaxation.find(f"{ns}permittedUsers")
        if permitted_users is not None and permitted_users.text == "AllUsers":
            issues.append(
                f"Connected App '{app_name}': Permitted Users is set to 'AllUsers'. "
                "For integration apps, consider 'AdminApprovedUsers' to restrict to "
                "only pre-authorized integration users."
            )

    return issues


def check_integration_admin_connected_apps(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check ConnectedApp metadata files
    connected_app_dir = manifest_dir / "connectedApps"
    if connected_app_dir.exists():
        for app_file in connected_app_dir.glob("*.connectedApp"):
            issues.extend(check_connected_app(app_file))

    # Also check in the root for any .connectedApp files
    for app_file in manifest_dir.rglob("*.connectedApp"):
        if app_file.parent.name != "connectedApps":
            issues.extend(check_connected_app(app_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_integration_admin_connected_apps(manifest_dir)

    if not issues:
        print("No Connected App configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
