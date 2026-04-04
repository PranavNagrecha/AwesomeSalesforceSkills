#!/usr/bin/env python3
"""Checker script for Source Tracking and Conflict Resolution skill.

Validates a Salesforce DX project directory for common source-tracking
hygiene issues: .sf/ in .gitignore, deprecated sfdx force:source commands
in CI files, and .sf/ tracking files accidentally committed to Git.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_source_tracking_and_conflict_resolution.py [--help]
    python3 check_source_tracking_and_conflict_resolution.py --project-dir path/to/sf/project
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce DX project for source-tracking hygiene issues: "
            ".sf/ in .gitignore, deprecated command usage, and tracking files "
            "accidentally committed to version control."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_sf_in_gitignore(project_dir: Path) -> list[str]:
    """Verify that .sf/ is listed in .gitignore to prevent tracking files being committed."""
    issues: list[str] = []
    gitignore = project_dir / ".gitignore"

    if not gitignore.exists():
        issues.append(
            ".gitignore not found in project root. "
            "Create one and add '.sf/' to prevent tracking files from being committed to Git."
        )
        return issues

    content = gitignore.read_text(encoding="utf-8")
    lines = [line.strip() for line in content.splitlines()]

    # Accept: .sf/, .sf, **/.sf/, **/.sf
    sf_patterns = {".sf/", ".sf", "**/.sf/", "**/.sf"}
    matched = any(line in sf_patterns for line in lines)

    if not matched:
        issues.append(
            ".gitignore exists but '.sf/' is not listed. "
            "Add '.sf/' to .gitignore to prevent source tracking files from being committed. "
            "Tracking files are machine-local and org-ID-specific; sharing them via Git causes "
            "incorrect conflict detection for all team members."
        )

    return issues


def check_sf_dir_not_committed(project_dir: Path) -> list[str]:
    """Check if .sf/ directory exists and warn if it looks like it may be tracked by Git."""
    issues: list[str] = []
    sf_dir = project_dir / ".sf"

    if not sf_dir.exists():
        return issues  # No .sf/ present — nothing to check

    # Check if .git exists (this is a git repo)
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        return issues  # Not a git repo — skip

    # Look for maxRevision.json to confirm this is a real tracking directory
    max_revision_files = list(sf_dir.rglob("maxRevision.json"))
    if not max_revision_files:
        return issues

    # Check if any tracking files show up in git index by looking for .sf/ in git ls-files output
    # We cannot run git commands here (stdlib only), so we inspect .git/index indirectly
    # by checking if .sf/ appears to be excluded by .gitignore content we already validated above.
    # If check_sf_in_gitignore passed, .sf/ is excluded. This check is informational only.
    issues.append(
        ".sf/ tracking directory found in project root. "
        "Confirm it is excluded by .gitignore (see companion check). "
        "Never commit .sf/ to Git — tracking files are rebuilt automatically by "
        "'sf project retrieve start' and are machine/org-specific."
    )

    return issues


def check_deprecated_sfdx_commands(project_dir: Path) -> list[str]:
    """Scan CI config files and shell scripts for deprecated sfdx force:source:* commands."""
    issues: list[str] = []

    deprecated_patterns = [
        (r"sfdx\s+force:source:pull", "sfdx force:source:pull", "sf project retrieve start"),
        (r"sfdx\s+force:source:push", "sfdx force:source:push", "sf project deploy start"),
        (r"sfdx\s+force:source:status", "sfdx force:source:status", "sf project deploy preview"),
        (r"--forceoverwrite", "--forceoverwrite", "--ignore-conflicts"),
        (r"--force-overwrite", "--force-overwrite (on sf project commands)", "--ignore-conflicts"),
    ]

    # Files to scan: CI config files, shell scripts, package.json scripts
    scan_patterns = [
        "**/.github/**/*.yml",
        "**/.github/**/*.yaml",
        "**/Jenkinsfile",
        "**/Dockerfile",
        "**/*.sh",
        "**/package.json",
        "**/bitbucket-pipelines.yml",
        "**/.gitlab-ci.yml",
        "**/circle.yml",
        "**/.circleci/**/*.yml",
    ]

    scanned_files: set[Path] = set()
    for glob_pattern in scan_patterns:
        for fpath in project_dir.glob(glob_pattern):
            if fpath.is_file() and fpath not in scanned_files:
                scanned_files.add(fpath)
                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue

                for pattern_regex, deprecated_cmd, replacement in deprecated_patterns:
                    if re.search(pattern_regex, content, re.IGNORECASE):
                        issues.append(
                            f"{fpath.relative_to(project_dir)}: uses deprecated '{deprecated_cmd}'. "
                            f"Replace with '{replacement}' (sf CLI v2, Spring '25+)."
                        )

    return issues


def check_sfdx_project_json(project_dir: Path) -> list[str]:
    """Check sfdx-project.json for sourceApiVersion and packageDirectories configuration."""
    issues: list[str] = []
    proj_file = project_dir / "sfdx-project.json"

    if not proj_file.exists():
        issues.append(
            "sfdx-project.json not found. "
            "This file is required for source tracking to work. "
            "Run 'sf project generate' to initialize a Salesforce DX project."
        )
        return issues

    try:
        data = json.loads(proj_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(f"sfdx-project.json is not valid JSON: {exc}")
        return issues

    # Check sourceApiVersion is set (required for deterministic tracking behavior)
    if "sourceApiVersion" not in data:
        issues.append(
            "sfdx-project.json is missing 'sourceApiVersion'. "
            "Without this, the CLI uses its bundled default API version, which may differ "
            "from the org API version and cause inconsistent tracking behavior. "
            "Add: \"sourceApiVersion\": \"63.0\" (or your target API version)."
        )

    # Check packageDirectories is present and non-empty
    pkg_dirs = data.get("packageDirectories", [])
    if not pkg_dirs:
        issues.append(
            "sfdx-project.json has no 'packageDirectories' defined. "
            "Source tracking requires at least one package directory. "
            "Add a packageDirectories entry pointing to your source root (e.g. 'force-app')."
        )

    return issues


def check_max_revision_manually_edited(project_dir: Path) -> list[str]:
    """Warn if maxRevision.json files have unusually low or zero revision counters.

    This heuristic detects files that may have been manually reset, which causes
    the CLI to treat all components as if they have never been retrieved.
    """
    issues: list[str] = []
    sf_dir = project_dir / ".sf"

    if not sf_dir.exists():
        return issues

    for max_rev_file in sf_dir.rglob("maxRevision.json"):
        try:
            data = json.loads(max_rev_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            issues.append(
                f"{max_rev_file.relative_to(project_dir)}: could not be parsed as JSON. "
                "The tracking file may be corrupted. Delete '.sf/orgs/<orgId>/' and run "
                "'sf project retrieve start' to rebuild tracking state."
            )
            continue

        # If the file has entries but all RevisionCounters are 0, it may have been manually zeroed
        source_members = data.get("sourceMembers", {})
        if source_members:
            zero_count = sum(
                1 for v in source_members.values()
                if isinstance(v, dict) and v.get("lastRetrievedFromServer") == 0
            )
            total = len(source_members)
            if total > 10 and zero_count == total:
                issues.append(
                    f"{max_rev_file.relative_to(project_dir)}: all {total} SourceMember entries "
                    "have 'lastRetrievedFromServer' = 0. This may indicate the file was manually "
                    "edited or improperly initialized. Consider deleting '.sf/orgs/<orgId>/' and "
                    "running 'sf project retrieve start' to rebuild from the org."
                )

    return issues


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_source_tracking_and_conflict_resolution(project_dir: Path) -> list[str]:
    """Run all source-tracking hygiene checks and return a list of issue strings."""
    issues: list[str] = []

    if not project_dir.exists():
        issues.append(f"Project directory not found: {project_dir}")
        return issues

    issues.extend(check_sf_in_gitignore(project_dir))
    issues.extend(check_sf_dir_not_committed(project_dir))
    issues.extend(check_deprecated_sfdx_commands(project_dir))
    issues.extend(check_sfdx_project_json(project_dir))
    issues.extend(check_max_revision_manually_edited(project_dir))

    return issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()
    issues = check_source_tracking_and_conflict_resolution(project_dir)

    if not issues:
        print("No source tracking hygiene issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
