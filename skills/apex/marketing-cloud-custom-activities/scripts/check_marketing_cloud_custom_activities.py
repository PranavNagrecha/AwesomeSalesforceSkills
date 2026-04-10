#!/usr/bin/env python3
"""Checker script for Marketing Cloud Custom Activities skill.

Validates custom activity configuration files and endpoint implementation files
for common issues documented in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_cloud_custom_activities.py [--help]
    python3 check_marketing_cloud_custom_activities.py --manifest-dir path/to/project
    python3 check_marketing_cloud_custom_activities.py --config path/to/config.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Marketing Cloud Custom Activity configuration and implementation "
            "files for common issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the project (default: current directory).",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to a specific config.json file to validate.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# config.json checks
# ---------------------------------------------------------------------------

def check_config_json(config_path: Path) -> list[str]:
    """Validate a custom activity config.json file."""
    issues: list[str] = []

    if not config_path.exists():
        issues.append(f"config.json not found at: {config_path}")
        return issues

    try:
        with config_path.open() as f:
            config = json.load(f)
    except json.JSONDecodeError as exc:
        issues.append(f"config.json is not valid JSON: {exc}")
        return issues

    # Required top-level keys
    required_keys = ["workflowApiVersion", "metaData", "endpoints", "userInterfaces"]
    for key in required_keys:
        if key not in config:
            issues.append(f"config.json missing required key: '{key}'")

    # HTTPS enforcement on all URLs
    def collect_urls(obj: object, path: str = "") -> list[tuple[str, str]]:
        """Recursively collect all string values that look like URLs."""
        found: list[tuple[str, str]] = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                found.extend(collect_urls(v, f"{path}.{k}" if path else k))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                found.extend(collect_urls(item, f"{path}[{i}]"))
        elif isinstance(obj, str) and obj.startswith("http"):
            found.append((path, obj))
        return found

    for field_path, url in collect_urls(config):
        if url.startswith("http://"):
            issues.append(
                f"config.json contains HTTP (not HTTPS) URL at '{field_path}': {url}"
            )

    # workflowApiVersion should be "1.1"
    api_version = config.get("workflowApiVersion", "")
    if api_version and str(api_version) != "1.1":
        issues.append(
            f"config.json workflowApiVersion is '{api_version}'; expected '1.1'"
        )

    # Check outcomes keys are present if this is a split activity
    meta = config.get("metaData", {})
    outcomes = meta.get("outcomes", [])
    if outcomes:
        for i, outcome in enumerate(outcomes):
            if not isinstance(outcome, dict):
                issues.append(f"config.json metaData.outcomes[{i}] is not an object")
                continue
            if "key" not in outcome:
                issues.append(
                    f"config.json metaData.outcomes[{i}] missing required 'key' field"
                )
            if "label" not in outcome:
                issues.append(
                    f"config.json metaData.outcomes[{i}] missing required 'label' field"
                )
            key = outcome.get("key", "")
            label = outcome.get("label", "")
            if key and label and key == label:
                issues.append(
                    f"config.json metaData.outcomes[{i}]: key and label are identical ('{key}'); "
                    "key should be a machine identifier, label should be human-readable"
                )

    # Check execute endpoint is present
    endpoints = config.get("endpoints", {})
    execute = endpoints.get("execute", {})
    if not execute:
        issues.append("config.json endpoints.execute is missing")
    elif "url" not in execute:
        issues.append("config.json endpoints.execute.url is missing")

    return issues


# ---------------------------------------------------------------------------
# JavaScript / source file checks
# ---------------------------------------------------------------------------

def check_js_files(root: Path) -> list[str]:
    """Scan JS files for Postmonger anti-patterns."""
    issues: list[str] = []

    js_files = list(root.rglob("*.js"))
    if not js_files:
        return issues

    postmonger_pattern = re.compile(r"Postmonger", re.IGNORECASE)
    trigger_before_ready = re.compile(
        r"connection\.trigger\s*\(\s*['\"]request", re.IGNORECASE
    )
    on_ready_pattern = re.compile(
        r"connection\.on\s*\(\s*['\"]ready['\"]", re.IGNORECASE
    )

    for js_file in js_files:
        try:
            content = js_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if not postmonger_pattern.search(content):
            continue  # Not a customActivity.js file

        lines = content.splitlines()
        first_trigger_line = None
        first_ready_listener_line = None

        for i, line in enumerate(lines, start=1):
            if trigger_before_ready.search(line) and first_trigger_line is None:
                first_trigger_line = i
            if on_ready_pattern.search(line) and first_ready_listener_line is None:
                first_ready_listener_line = i

        if (
            first_trigger_line is not None
            and first_ready_listener_line is not None
            and first_trigger_line < first_ready_listener_line
        ):
            issues.append(
                f"{js_file}: Postmonger trigger('request...') called at line {first_trigger_line} "
                f"before connection.on('ready') registered at line {first_ready_listener_line}. "
                "Triggers must not be called before the ready event handler is registered."
            )

    return issues


# ---------------------------------------------------------------------------
# Server-side execute endpoint checks
# ---------------------------------------------------------------------------

def check_server_files(root: Path) -> list[str]:
    """Scan server-side files for execute endpoint anti-patterns."""
    issues: list[str] = []

    # Check Python and JS server files
    candidate_extensions = ["*.js", "*.py", "*.ts"]
    server_files: list[Path] = []
    for ext in candidate_extensions:
        server_files.extend(root.rglob(ext))

    http_202_pattern = re.compile(
        r"(?:status|sendStatus)\s*\(\s*(?:202|201|204)\s*\)", re.IGNORECASE
    )
    non_200_response_pattern = re.compile(
        r"res\.(?:status|sendStatus)\s*\(\s*([2-5]\d{2})\s*\)"
    )
    jwt_verify_pattern = re.compile(r"jwt\.verify\s*\(", re.IGNORECASE)
    execute_route_pattern = re.compile(
        r"""(?:app|router)\.post\s*\(\s*['"][^'"]*execute[^'"]*['"]""",
        re.IGNORECASE,
    )
    branch_result_pattern = re.compile(r"""['"](branchResult)['"]\s*:""")
    wrong_branch_field_pattern = re.compile(
        r"""['"](?:outcome|branch|result|splitResult)['"]\s*:""", re.IGNORECASE
    )

    for server_file in server_files:
        try:
            content = server_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Check for non-200 status codes in execute routes
        if execute_route_pattern.search(content):
            for match in http_202_pattern.finditer(content):
                issues.append(
                    f"{server_file}: Execute endpoint uses non-200 HTTP status "
                    f"'{match.group()}' — Journey Builder requires exactly HTTP 200. "
                    "Contacts will error out on any other status code."
                )

            # Warn if no JWT verification found in file containing an execute route
            if not jwt_verify_pattern.search(content):
                issues.append(
                    f"{server_file}: Execute route found but no jwt.verify() call detected. "
                    "Journey Builder POSTs include a JWT in the Authorization header; "
                    "verify it before processing contact data."
                )

            # Warn if wrong branch result field name is used
            if wrong_branch_field_pattern.search(content) and not branch_result_pattern.search(content):
                issues.append(
                    f"{server_file}: Possible incorrect branchResult field name. "
                    "Custom split execute response must use exactly 'branchResult' as the JSON key."
                )

    return issues


# ---------------------------------------------------------------------------
# HTTPS check across all config-like files
# ---------------------------------------------------------------------------

def check_http_urls_in_project(root: Path) -> list[str]:
    """Warn about http:// URLs in any JSON file in the project."""
    issues: list[str] = []
    http_pattern = re.compile(r'"http://[^"]*"')

    for json_file in root.rglob("*.json"):
        try:
            content = json_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in http_pattern.finditer(content):
            issues.append(
                f"{json_file}: HTTP (not HTTPS) URL found: {match.group()}. "
                "Journey Builder requires HTTPS for all activity endpoints and UI URLs."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_marketing_cloud_custom_activities(manifest_dir: Path, config_path: Path | None = None) -> list[str]:
    """Return a list of issue strings found in the project."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # config.json validation
    if config_path is not None:
        issues.extend(check_config_json(config_path))
    else:
        # Search for config.json files in the project
        config_files = list(manifest_dir.rglob("config.json"))
        if not config_files:
            issues.append(
                "No config.json found in project. "
                "A custom activity requires a config.json served at the registered App Extension URL."
            )
        for cf in config_files:
            issues.extend(check_config_json(cf))

    # Postmonger sequence checks
    issues.extend(check_js_files(manifest_dir))

    # Execute endpoint checks
    issues.extend(check_server_files(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    config_path = Path(args.config) if args.config else None

    issues = check_marketing_cloud_custom_activities(manifest_dir, config_path)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
