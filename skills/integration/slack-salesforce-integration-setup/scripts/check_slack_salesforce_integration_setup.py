#!/usr/bin/env python3
"""Checker script for Slack Salesforce Integration Setup skill.

Checks org metadata or configuration relevant to Slack Salesforce Integration Setup.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_slack_salesforce_integration_setup.py [--help]
    python3 check_slack_salesforce_integration_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Slack Salesforce Integration Setup configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_slack_salesforce_integration_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check connected app metadata for Slack-related apps
    connected_app_files = list(manifest_dir.rglob("*.connectedApp-meta.xml"))
    for app_file in connected_app_files:
        try:
            text = app_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "slack" in text.lower() or "Slack" in text:
            # Warn about Government Cloud usage
            if "GovernmentCloud" in text or "government" in text.lower():
                issues.append(
                    f"{app_file}: Connected app references Government Cloud — "
                    "Government Cloud Salesforce orgs cannot connect to Slack workspaces."
                )

    # Check profile/permission set files for Slack permission sets
    permission_files = list(manifest_dir.rglob("*.permissionset-meta.xml"))
    slack_permission_found = any(
        "SlackStandardUser" in f.read_text(encoding="utf-8", errors="ignore")
        for f in permission_files
        if f.exists()
    )
    if permission_files and not slack_permission_found:
        issues.append(
            "No Slack permission set assignments found in permissionset metadata — "
            "Users need 'Slack Standard User' or equivalent permission set to use Salesforce for Slack features."
        )

    # Check for more than 20 connected Salesforce orgs hint in any config files
    config_files = list(manifest_dir.rglob("*.json")) + list(manifest_dir.rglob("*.yaml"))
    for config_file in config_files:
        try:
            text = config_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "salesforce_orgs" in text or "connected_orgs" in text:
            import re
            count_match = re.search(r'"count"\s*:\s*(\d+)', text)
            if count_match and int(count_match.group(1)) > 20:
                issues.append(
                    f"{config_file}: Configuration suggests more than 20 connected Salesforce orgs — "
                    "Slack workspace limit is 20 Salesforce org connections."
                )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_slack_salesforce_integration_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
