#!/usr/bin/env python3
"""Checker script for Flow For Slack skill.

Checks org metadata or configuration relevant to Flow For Slack.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_flow_for_slack.py [--help]
    python3 check_flow_for_slack.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow For Slack configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_flow_for_slack(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Flow XML for Slack actions in before-save execution context
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))
    for flow_file in flow_files:
        try:
            text = flow_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        has_before_save = "triggerType>Before_Save" in text or "RecordBeforeSave" in text
        has_slack_action = any(
            kw in text
            for kw in ["SendSlackMessage", "CreateSlackChannel", "AddUsersToChannel",
                       "ArchiveSlackChannel", "CheckSlackUserConnection"]
        )
        if has_before_save and has_slack_action:
            issues.append(
                f"{flow_file}: Slack Core Action detected in before-save Flow — "
                "Slack actions are callouts and cannot run in synchronous before-save context. "
                "Move to after-save asynchronous execution path."
            )
        # Check for Slack actions without fault connectors
        if has_slack_action:
            # Simple heuristic: if no faultConnector element exists
            if "faultConnector" not in text and "faultPath" not in text:
                issues.append(
                    f"{flow_file}: Slack action detected but no fault connector found — "
                    "Slack actions can fail silently (revoked token, missing permission set). "
                    "Add a fault path to surface errors."
                )

    # Check for channel name patterns that may violate Slack naming rules
    import re
    for flow_file in flow_files:
        try:
            text = flow_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "CreateSlackChannel" in text:
            # Detect uppercase channel name assignments
            uppercase_match = re.search(r"<channelName>[A-Z]", text)
            if uppercase_match:
                issues.append(
                    f"{flow_file}: CreateSlackChannel action may use uppercase channel name — "
                    "Slack channel names must be lowercase. Apply LOWER() formula transformation."
                )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_flow_for_slack(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
