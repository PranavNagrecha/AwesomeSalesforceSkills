#!/usr/bin/env python3
"""Checker script for CRM Analytics Dashboard JSON skill.

Checks dashboard JSON files for common issues identified in the skill's
gotchas and LLM anti-patterns documentation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_dashboard_json.py [--help]
    python3 check_analytics_dashboard_json.py --dashboard-file path/to/dashboard.json
    python3 check_analytics_dashboard_json.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Pattern that matches a valid dataset ID (starts with 0Fb, 18-char Salesforce ID)
DATASET_ID_PATTERN = re.compile(r"^0Fb[A-Za-z0-9]{15}$")

# Pattern that matches a valid dataset version ID (starts with 0Fc)
DATASET_VERSION_PATTERN = re.compile(r"^0Fc[A-Za-z0-9]{15}$")

# Pattern for a name-based load in SAQL — load "SomeName" where name starts with a letter
SAQL_NAME_LOAD_PATTERN = re.compile(r'load\s+"([A-Za-z][^"]*)"')

# Pattern for valid ID-based load in SAQL — load "0FbXXX/0FcXXX"
SAQL_ID_LOAD_PATTERN = re.compile(r'load\s+"0Fb[A-Za-z0-9]+/0Fc[A-Za-z0-9]+"')

# Pattern to detect a binding in a SAQL query string
BINDING_IN_QUERY_PATTERN = re.compile(r"\{\{cell\([^}]+\)\}\}")

# Pattern to detect if an empty-binding guard is present alongside the binding
EMPTY_GUARD_PATTERN = re.compile(r'"\s*==\s*"\{\{cell\(')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics dashboard JSON files for common issues: "
            "dataset name references instead of IDs, missing step limits, "
            "missing empty-binding guards."
        ),
    )
    parser.add_argument(
        "--dashboard-file",
        help="Path to a single dashboard JSON file to check.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory to scan for *.json files that look like dashboard bodies "
            "(default: current directory). Ignored if --dashboard-file is provided."
        ),
    )
    return parser.parse_args()


def check_step_dataset_references(step_name: str, step: dict) -> list[str]:
    """Check a single step for dataset name references instead of IDs."""
    issues: list[str] = []

    datasets = step.get("datasets", [])
    for ds in datasets:
        ds_id = ds.get("id", "")
        ds_version = ds.get("version", "")

        if ds_id and not DATASET_ID_PATTERN.match(ds_id):
            issues.append(
                f"Step '{step_name}': dataset 'id' field is '{ds_id}' — "
                f"expected a Salesforce dataset ID starting with '0Fb' (18 chars). "
                f"Name-based references fail silently after org migration."
            )

        if ds_version and not DATASET_VERSION_PATTERN.match(ds_version):
            issues.append(
                f"Step '{step_name}': dataset 'version' field is '{ds_version}' — "
                f"expected a dataset version ID starting with '0Fc' (18 chars). "
                f"Use the currentVersionId from GET /wave/datasets."
            )

        if not ds_version:
            issues.append(
                f"Step '{step_name}': dataset entry is missing 'version' "
                f"(datasetVersionId). Steps without an explicit version ID resolve "
                f"to the current version at render time, which can change unexpectedly."
            )

    # Also check the SAQL query string for name-based load statements
    query = step.get("query", "")
    if step.get("type") == "saql" and query:
        name_loads = SAQL_NAME_LOAD_PATTERN.findall(query)
        id_loads = SAQL_ID_LOAD_PATTERN.findall(query)

        if name_loads and not id_loads:
            for name in name_loads:
                issues.append(
                    f"Step '{step_name}': SAQL query uses name-based load "
                    f"'load \"{name}\"'. Use load \"datasetId/datasetVersionId\" "
                    f"format instead to ensure portability across orgs."
                )

    return issues


def check_step_row_limit(step_name: str, step: dict) -> list[str]:
    """Check that steps with SAQL limit clauses also have the step-level limit property."""
    issues: list[str] = []

    step_type = step.get("type", "")
    if step_type != "saql":
        return issues

    query = step.get("query", "")
    step_limit = step.get("limit")

    # Check for limit clause in SAQL query
    has_saql_limit = bool(re.search(r"\blimit\s+q\s+\d+", query, re.IGNORECASE))

    if step_limit is None:
        issues.append(
            f"Step '{step_name}': missing 'limit' property on step object. "
            f"Default is 2,000 rows. Add '\"limit\": 10000' (or appropriate value) "
            f"to prevent silent truncation for steps that need more than 2,000 rows."
        )
    elif step_limit > 10000:
        issues.append(
            f"Step '{step_name}': 'limit' is {step_limit}, which exceeds the "
            f"platform maximum of 10,000 rows. The platform will silently cap this "
            f"at 10,000."
        )

    if has_saql_limit and step_limit is None:
        issues.append(
            f"Step '{step_name}': SAQL query has a 'limit q N' clause but the "
            f"step object has no 'limit' property. Both must be set for the higher "
            f"row count to take effect."
        )

    return issues


def check_binding_empty_guards(step_name: str, step: dict) -> list[str]:
    """Check if SAQL queries with bindings have empty-string guards."""
    issues: list[str] = []

    query = step.get("query", "")
    if not query:
        return issues

    if BINDING_IN_QUERY_PATTERN.search(query):
        # Binding present — check for empty-string guard
        if not EMPTY_GUARD_PATTERN.search(query):
            issues.append(
                f"Step '{step_name}': SAQL query contains a {{{{cell(...)}}}} binding "
                f"but no empty-string guard was detected. When no user selection is "
                f"active, the binding returns an empty string. Add an '|| \"\" == "
                f"\"{{{{cell(...)}}}}\"' guard to prevent unintended full-population "
                f"results or zero-row charts on initial load."
            )

    return issues


def check_dashboard_body(body: dict, source_label: str) -> list[str]:
    """Run all checks on a parsed dashboard JSON body."""
    issues: list[str] = []

    steps = body.get("steps", {})
    if not isinstance(steps, dict):
        issues.append(f"{source_label}: 'steps' is not a dict — unexpected dashboard structure.")
        return issues

    for step_name, step in steps.items():
        if not isinstance(step, dict):
            continue
        issues.extend(check_step_dataset_references(step_name, step))
        issues.extend(check_step_row_limit(step_name, step))
        issues.extend(check_binding_empty_guards(step_name, step))

    # Check that top-level sections exist
    for required_key in ("steps", "widgets", "state"):
        if required_key not in body:
            issues.append(
                f"{source_label}: missing top-level key '{required_key}'. "
                f"Dashboard JSON must include 'steps', 'widgets', and 'state'."
            )

    return issues


def is_dashboard_body(data: dict) -> bool:
    """Heuristic: a dict with a 'steps' key containing dicts is likely a dashboard body."""
    if not isinstance(data, dict):
        return False
    steps = data.get("steps")
    if isinstance(steps, dict):
        return True
    return False


def check_file(path: Path) -> list[str]:
    """Parse a JSON file and run dashboard checks if it looks like a dashboard body."""
    issues: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        # Not a JSON file or malformed — skip silently unless it has a .json extension
        if path.suffix.lower() == ".json":
            issues.append(f"{path}: invalid JSON — {exc}")
        return issues

    # Some dashboard REST API responses wrap the body in a top-level object
    # Try both the raw body and a nested 'body' key if present
    if isinstance(data, dict) and "body" in data and isinstance(data["body"], dict):
        body = data["body"]
    else:
        body = data

    if not is_dashboard_body(body):
        return issues  # Not a dashboard file — skip

    issues.extend(check_dashboard_body(body, str(path)))
    return issues


def check_analytics_dashboard_json(manifest_dir: Path) -> list[str]:
    """Scan a directory for dashboard JSON files and return all issues found."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Directory not found: {manifest_dir}")
        return issues

    json_files = list(manifest_dir.rglob("*.json"))
    if not json_files:
        issues.append(f"No .json files found under {manifest_dir}")
        return issues

    for json_file in sorted(json_files):
        issues.extend(check_file(json_file))

    return issues


def main() -> int:
    args = parse_args()

    if args.dashboard_file:
        path = Path(args.dashboard_file)
        issues = check_file(path)
    else:
        manifest_dir = Path(args.manifest_dir)
        issues = check_analytics_dashboard_json(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
