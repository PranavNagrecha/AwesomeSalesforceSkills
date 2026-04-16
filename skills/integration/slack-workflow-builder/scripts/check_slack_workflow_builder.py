#!/usr/bin/env python3
"""Checker script for Slack Workflow Builder skill.

Scans Salesforce Flow metadata for common mistakes when a flow is meant to be
invoked from Slack Workflow Builder's **Run a Flow** connector (autolaunched,
active flows only). Uses stdlib only — no pip dependencies.

Usage:
    python3 check_slack_workflow_builder.py [--help]
    python3 check_slack_workflow_builder.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FLOW_FILE = re.compile(r"\.flow-meta\.xml$", re.IGNORECASE)
API_NAME_RE = re.compile(r"<apiName>([^<]+)</apiName>")
PROCESS_TYPE_RE = re.compile(r"<processType>([^<]+)</processType>")
STATUS_RE = re.compile(r"<status>([^<]+)</status>")


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def _slack_invocation_naming(api_name: str | None, relpath: str) -> bool:
    """Heuristic: flow name/path suggests Slack Workflow Builder handoff work."""
    blob = f"{api_name or ''} {relpath}".lower()
    if "slack" not in blob:
        return False
    # Exclude extremely generic paths while keeping *_slack_* style matches
    return True


def check_slack_workflow_builder(manifest_dir: Path) -> list[str]:
    """Return actionable issues found in Flow metadata."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    flow_files = [p for p in manifest_dir.rglob("*") if p.is_file() and FLOW_FILE.search(p.name)]
    if not flow_files:
        return issues

    for path in sorted(flow_files):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            issues.append(f"{path}: could not read file ({exc})")
            continue

        api_name = _first_match(API_NAME_RE, text)
        process_type = _first_match(PROCESS_TYPE_RE, text)
        status = _first_match(STATUS_RE, text)
        rel = str(path.relative_to(manifest_dir))

        if not process_type:
            continue

        if not _slack_invocation_naming(api_name, rel):
            continue

        if process_type != "AutoLaunchedFlow":
            issues.append(
                f"{rel}: processType is '{process_type}' but API/path suggests Slack-related "
                "automation. Slack Workflow Builder **Run a Flow** can invoke **autolaunched** flows "
                "only — use an autolaunched entry flow (or rename if this flow is Salesforce-only)."
            )
            continue

        if status and status != "Active":
            issues.append(
                f"{rel}: autolaunched flow '{api_name or '?'}' has status '{status}'. "
                "Inactive flows cannot be selected for reliable **Run a Flow** execution from Slack."
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for Slack Workflow Builder Run a Flow readiness.",
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
    issues = check_slack_workflow_builder(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
