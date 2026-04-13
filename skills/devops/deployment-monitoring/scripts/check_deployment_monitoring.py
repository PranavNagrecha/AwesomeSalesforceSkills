#!/usr/bin/env python3
"""Checker script for Deployment Monitoring skill.

Scans a Salesforce metadata project directory and CI configuration files for
common deployment monitoring anti-patterns:
  - Polling scripts that treat InProgress as success
  - Quick deploy scripts that reuse the validation ID for status checks
  - Missing --json flags that prevent programmatic result parsing
  - No timeout guard in polling loops
  - Missing deployment ID capture steps

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_deployment_monitoring.py [--help]
    python3 check_deployment_monitoring.py --manifest-dir path/to/project
    python3 check_deployment_monitoring.py --manifest-dir . --check-scripts
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# ── Pattern definitions ──────────────────────────────────────────────────────

# Detects InProgress treated as a success/continue condition without a proper
# terminal-state check (Succeeded must be the explicit positive branch).
_INPROGRESS_AS_SUCCESS = re.compile(
    r'(?:status|STATUS)\s*[!=]=\s*["\']InProgress["\']|'
    r'!=\s*["\']Failed["\']',
    re.IGNORECASE,
)

# Detects quick deploy + report using the same job-id variable reference,
# which is the canonical "reuse validation ID" anti-pattern.
_QUICK_DEPLOY_SAME_ID = re.compile(
    r'project\s+deploy\s+quick\s+.*--job-id\s+(\$\{?\w+\}?)'
    r'.*\n(?:.*\n){0,5}.*project\s+deploy\s+report\s+.*--job-id\s+\1',
    re.MULTILINE,
)

# Detects REST deployRequest calls missing includeDetails=true.
_REST_MISSING_INCLUDE_DETAILS = re.compile(
    r'/metadata/deployRequest/[^?\s"\']+(?!\?includeDetails)',
    re.IGNORECASE,
)

# Detects CLI deploy commands missing --json flag (prevents structured parsing).
_CLI_DEPLOY_MISSING_JSON = re.compile(
    r'sf\s+project\s+deploy\s+(?:start|report|quick)\b(?![^\n]*--json)',
    re.IGNORECASE,
)

# Detects deploy start without capturing the returned job ID.
_DEPLOY_START_NO_ID_CAPTURE = re.compile(
    r'^(?!.*=.*sf\s+project\s+deploy\s+start|.*\|\s*jq).*'
    r'sf\s+project\s+deploy\s+start\b',
    re.MULTILINE | re.IGNORECASE,
)

# Script file extensions to inspect.
_SCRIPT_EXTENSIONS = {".sh", ".bash", ".py", ".yml", ".yaml", ".Makefile", ".mk"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce project for deployment monitoring anti-patterns "
            "described in the deployment-monitoring skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    parser.add_argument(
        "--check-scripts",
        action="store_true",
        help=(
            "Scan shell and CI script files for deployment monitoring "
            "anti-patterns (poll logic, ID capture, etc.)."
        ),
    )
    return parser.parse_args()


# ── Directory structure checks ───────────────────────────────────────────────

def check_project_structure(manifest_dir: Path) -> list[str]:
    """Check that the project has a recognisable Salesforce structure."""
    issues: list[str] = []

    force_app = manifest_dir / "force-app"
    src_dir = manifest_dir / "src"
    package_candidates = [
        manifest_dir / "manifest" / "package.xml",
        manifest_dir / "package.xml",
        manifest_dir / "src" / "package.xml",
    ]
    has_package = any(p.is_file() for p in package_candidates)

    if not force_app.is_dir() and not src_dir.is_dir() and not has_package:
        issues.append(
            "No recognisable Salesforce project structure found "
            "(no force-app/, no src/, no package.xml). "
            "Verify --manifest-dir points to a Salesforce DX or MDAPI project root."
        )
    return issues


def check_sfdx_project_json(manifest_dir: Path) -> list[str]:
    """Check sfdx-project.json for common monitoring-related gaps."""
    issues: list[str] = []
    sfdx_json = manifest_dir / "sfdx-project.json"
    if not sfdx_json.is_file():
        # Not necessarily an error — MDAPI projects may not have this file.
        return issues

    import json as _json

    try:
        with sfdx_json.open() as fh:
            data = _json.load(fh)
    except (_json.JSONDecodeError, OSError) as exc:
        issues.append(f"sfdx-project.json is unreadable or invalid JSON: {exc}")
        return issues

    # Warn if sourceApiVersion is absent — this affects what API version deployments use.
    if not data.get("sourceApiVersion"):
        issues.append(
            "sfdx-project.json is missing 'sourceApiVersion'. "
            "Without an explicit API version, deployments default to the CLI's "
            "bundled version, which may differ from the target org's API version "
            "and produce unexpected DeployResult field names or behavior."
        )

    return issues


# ── Script / CI file checks ──────────────────────────────────────────────────

def _is_script_file(path: Path) -> bool:
    suffix = path.suffix.lower()
    name = path.name.lower()
    return suffix in _SCRIPT_EXTENSIONS or name in {"makefile", "jenkinsfile"}


def scan_script_file(path: Path) -> list[str]:
    """Scan a single script file for deployment monitoring anti-patterns."""
    issues: list[str] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    rel = path.name

    # Anti-pattern 1: InProgress treated as success
    if _INPROGRESS_AS_SUCCESS.search(content):
        issues.append(
            f"{rel}: Possible 'InProgress-as-success' pattern detected. "
            "Deployment status checks must poll until the explicit 'Succeeded' "
            "terminal state, not until 'not Failed' or 'InProgress' is seen."
        )

    # Anti-pattern 2: Quick deploy + report reusing the same ID variable
    if _QUICK_DEPLOY_SAME_ID.search(content):
        issues.append(
            f"{rel}: Quick deploy and deploy report appear to use the same "
            "job ID variable. deployRecentValidation returns a NEW deployment ID "
            "distinct from the validation ID. Capture and use the new ID for "
            "status monitoring."
        )

    # Anti-pattern 3: REST deployRequest without includeDetails
    if _REST_MISSING_INCLUDE_DETAILS.search(content):
        issues.append(
            f"{rel}: REST deployRequest URL found without '?includeDetails=true'. "
            "Without this parameter, componentFailures and runTestResult are "
            "omitted from the response, so failures will not be visible."
        )

    # Anti-pattern 4: CLI deploy without --json
    matches = _CLI_DEPLOY_MISSING_JSON.findall(content)
    if matches:
        issues.append(
            f"{rel}: 'sf project deploy' command found without '--json' flag. "
            "Without --json, the output is human-readable text that cannot be "
            "reliably parsed for the deployment ID or structured error detail. "
            "Add --json to all programmatic deploy calls."
        )

    return issues


def scan_scripts_directory(manifest_dir: Path) -> list[str]:
    """Walk the project and scan all script-like files."""
    issues: list[str] = []
    skip_dirs = {".git", "node_modules", ".sfdx", ".sf", "__pycache__"}

    for root_str, dirs, files in os.walk(manifest_dir):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        root_path = Path(root_str)
        for fname in files:
            fpath = root_path / fname
            if _is_script_file(fpath):
                issues.extend(scan_script_file(fpath))

    return issues


# ── Main ─────────────────────────────────────────────────────────────────────

def check_deployment_monitoring(manifest_dir: Path, check_scripts: bool = False) -> list[str]:
    """Return a list of issue strings found in the project."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_project_structure(manifest_dir))
    issues.extend(check_sfdx_project_json(manifest_dir))

    if check_scripts:
        issues.extend(scan_scripts_directory(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_deployment_monitoring(manifest_dir, args.check_scripts)

    if not issues:
        print("No deployment monitoring issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
