#!/usr/bin/env python3
"""Checker script for Scratch Org Management skill.

Validates scratch org definition files (project-scratch-def.json) for the most
common authoring mistakes documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_scratch_org_management.py [--help]
    python3 check_scratch_org_management.py --project-dir path/to/sfdx-project
    python3 check_scratch_org_management.py --def-file config/project-scratch-def.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Valid scratch org editions per Salesforce DX Developer Guide
VALID_EDITIONS = {
    "Developer",
    "Enterprise",
    "Group",
    "Professional",
    "Partner Developer",
    "Partner Enterprise",
}

# Maximum allowed duration in days per platform limit
MAX_DURATION_DAYS = 30

# Deprecated top-level field that silently drops settings
DEPRECATED_FIELDS = {"orgPreferences"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate scratch org definition files for common authoring mistakes.\n"
            "Checks edition validity, deprecated fields, duration limits, and hasSampleData."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--project-dir",
        default=None,
        help=(
            "Root of the SFDX project. The checker will search for all "
            "project-scratch-def.json files under config/ (default: current directory)."
        ),
    )
    group.add_argument(
        "--def-file",
        default=None,
        help="Path to a specific scratch org definition file to check.",
    )
    return parser.parse_args()


def find_def_files(project_dir: Path) -> list[Path]:
    """Return all JSON files named *scratch*def* under the project directory."""
    candidates = list(project_dir.rglob("*scratch*def*.json"))
    # Also check the canonical location directly
    canonical = project_dir / "config" / "project-scratch-def.json"
    if canonical.exists() and canonical not in candidates:
        candidates.append(canonical)
    return candidates


def check_def_file(def_file: Path) -> list[str]:
    """Return a list of issue strings for a single scratch org definition file."""
    issues: list[str] = []

    # --- Parse JSON ---
    try:
        raw = def_file.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        issues.append(f"{def_file}: Invalid JSON — {exc}")
        return issues
    except OSError as exc:
        issues.append(f"{def_file}: Cannot read file — {exc}")
        return issues

    if not isinstance(data, dict):
        issues.append(f"{def_file}: Definition file must be a JSON object at the top level.")
        return issues

    # --- Check 1: edition is present and valid ---
    edition = data.get("edition")
    if edition is None:
        issues.append(
            f"{def_file}: Missing required field 'edition'. "
            f"Valid values: {sorted(VALID_EDITIONS)}"
        )
    elif edition not in VALID_EDITIONS:
        issues.append(
            f"{def_file}: Invalid edition '{edition}'. "
            f"Valid values: {sorted(VALID_EDITIONS)}"
        )

    # --- Check 2: deprecated orgPreferences field ---
    for deprecated in DEPRECATED_FIELDS:
        if deprecated in data:
            issues.append(
                f"{def_file}: Deprecated field '{deprecated}' found. "
                "Replace with 'settings' using Metadata API settings objects. "
                "orgPreferences silently drops settings on current API versions."
            )

    # --- Check 3: duration within platform limits ---
    duration = data.get("duration")
    if duration is not None:
        try:
            duration_int = int(duration)
        except (TypeError, ValueError):
            issues.append(
                f"{def_file}: Field 'duration' must be an integer (days). Got: {duration!r}"
            )
            duration_int = None
        if duration_int is not None:
            if duration_int < 1:
                issues.append(
                    f"{def_file}: Field 'duration' must be at least 1 day. Got: {duration_int}"
                )
            elif duration_int > MAX_DURATION_DAYS:
                issues.append(
                    f"{def_file}: Field 'duration' exceeds platform maximum of "
                    f"{MAX_DURATION_DAYS} days. Got: {duration_int}"
                )

    # --- Check 4: hasSampleData warning for CI contexts ---
    has_sample_data = data.get("hasSampleData")
    if has_sample_data is True:
        issues.append(
            f"{def_file}: 'hasSampleData' is set to true. "
            "This adds 3–5 minutes to scratch org provisioning. "
            "Disable unless tests explicitly depend on standard sample objects."
        )

    # --- Check 5: features must be a list of strings ---
    features = data.get("features")
    if features is not None:
        if not isinstance(features, list):
            issues.append(
                f"{def_file}: Field 'features' must be a JSON array. Got: {type(features).__name__}"
            )
        else:
            non_string = [f for f in features if not isinstance(f, str)]
            if non_string:
                issues.append(
                    f"{def_file}: All entries in 'features' must be strings. "
                    f"Non-string entries: {non_string}"
                )

    # --- Check 6: settings must be a dict if present ---
    settings = data.get("settings")
    if settings is not None and not isinstance(settings, dict):
        issues.append(
            f"{def_file}: Field 'settings' must be a JSON object. "
            f"Got: {type(settings).__name__}"
        )

    return issues


def check_project(project_dir: Path) -> list[str]:
    """Check all scratch org definition files found in a project directory."""
    issues: list[str] = []

    if not project_dir.exists():
        issues.append(f"Project directory not found: {project_dir}")
        return issues

    def_files = find_def_files(project_dir)

    if not def_files:
        issues.append(
            f"No scratch org definition files found under {project_dir}. "
            "Expected at least one file matching *scratch*def*.json, "
            "typically at config/project-scratch-def.json."
        )
        return issues

    for def_file in def_files:
        issues.extend(check_def_file(def_file))

    return issues


def main() -> int:
    args = parse_args()

    if args.def_file:
        target = Path(args.def_file)
        if not target.exists():
            print(f"ISSUE: Definition file not found: {target}")
            return 1
        issues = check_def_file(target)
    else:
        project_dir = Path(args.project_dir) if args.project_dir else Path(".")
        issues = check_project(project_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
