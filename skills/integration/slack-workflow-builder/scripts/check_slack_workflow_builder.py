#!/usr/bin/env python3
"""Checker script for Slack Workflow Builder skill.

Scans Salesforce Flow metadata for common mistakes when a flow is meant to be
invoked from Slack Workflow Builder's **Run a Flow** connector (autolaunched,
active flows only). Uses stdlib only — no pip dependencies.

Rules (grounded on Slack's Salesforce connector schema, deno-slack-hub run_flow.ts:
"Select a Flow (Only auto-launched flows are currently supported)", and the Slack Help
article Authenticate third-party accounts to use connector steps, fetched 2026-10-03):
  * Slack-named flow whose processType is not AutoLaunchedFlow.
  * Slack-named autolaunched flow that is not Active.
  * Slack-named autolaunched flow with no input variable (Run a Flow cannot pass values).
  * Coded workflow (Deno Slack SDK) whose RunFlow flow_name has no matching flow file in
    the scanned tree (checked only when flow files are present).
  * Coded workflow whose RunFlow step uses credential_source "DEVELOPER": every run uses one
    collaborator's Salesforce account; document why per-user END_USER auth is not used.

Usage:
    python3 check_slack_workflow_builder.py [--help]
    python3 check_slack_workflow_builder.py --manifest-dir path/to/metadata
    python3 check_slack_workflow_builder.py --self-test
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
        if "<isInput>true</isInput>" not in text:
            issues.append(
                f"{rel}: autolaunched flow '{api_name or path.stem}' has no input variable "
                "(isInput true); the Run a Flow step cannot pass Slack values into it."
            )

    flow_names = {p.name.split(".")[0] for p in flow_files}
    for ts_file in sorted(manifest_dir.rglob("*.ts")):
        try:
            ts = ts_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "Connectors.Salesforce.functions.RunFlow" not in ts:
            continue
        rel = str(ts_file.relative_to(manifest_dir))
        for name in re.findall(r"flow_name\s*:\s*[\"']([^\"']+)[\"']", ts):
            if flow_names and name not in flow_names:
                issues.append(f"{rel}: RunFlow flow_name '{name}' has no matching flow file in the scanned tree.")
        if re.search(r"credential_source\s*:\s*[\"']DEVELOPER[\"']", ts):
            issues.append(
                f"{rel}: RunFlow uses credential_source DEVELOPER, so every run uses one collaborator's "
                "Salesforce account; prefer END_USER (link trigger) or document the shared identity."
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
    parser.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    return parser.parse_args()


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    good = check_slack_workflow_builder(here / "good")
    bad = check_slack_workflow_builder(here / "bad")
    expected = ["processType is 'Flow'", "has status 'Draft'", "has no input variable",
                "has no matching flow file", "credential_source DEVELOPER"]
    missing = [e for e in expected if not any(e in issue for issue in bad)]
    print(f"good fixtures: {len(good)} issue(s) (expected 0)")
    for g in good:
        print(f"  unexpected: {g}")
    print(f"bad fixtures: {len(bad)} issue(s); missing expected: {missing or 'none'}")
    return 0 if not good and not missing else 1


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
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
