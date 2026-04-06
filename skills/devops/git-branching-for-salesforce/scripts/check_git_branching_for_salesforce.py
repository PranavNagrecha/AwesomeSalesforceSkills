#!/usr/bin/env python3
"""Checker script for Git Branching For Salesforce skill.

Analyzes a Salesforce DX project repository for branching strategy hygiene:
- Checks for branch protection indicators (.github/ or .gitlab/ configs)
- Validates sfdx-project.json package ancestor consistency
- Detects long-lived branches that may indicate branching model issues
- Checks for destructive changes manifests without CI integration

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_git_branching_for_salesforce.py [--help]
    python3 check_git_branching_for_salesforce.py --project-dir path/to/sfdx-project
    python3 check_git_branching_for_salesforce.py --project-dir . --check-branches
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Git branching strategy hygiene for a Salesforce DX project.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    parser.add_argument(
        "--check-branches",
        action="store_true",
        help="Query git for branch information (requires git repo).",
    )
    return parser.parse_args()


def check_sfdx_project_json(project_dir: Path) -> list[str]:
    """Check sfdx-project.json for package ancestor consistency."""
    issues: list[str] = []
    project_file = project_dir / "sfdx-project.json"

    if not project_file.exists():
        issues.append(
            f"No sfdx-project.json found at {project_dir}. "
            "Cannot validate package configuration."
        )
        return issues

    try:
        with open(project_file, "r", encoding="utf-8") as f:
            project_data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        issues.append(f"Failed to parse sfdx-project.json: {e}")
        return issues

    package_dirs = project_data.get("packageDirectories", [])
    if not package_dirs:
        issues.append(
            "sfdx-project.json has no packageDirectories. "
            "If using packages, define at least one package directory."
        )
        return issues

    for pkg_dir in package_dirs:
        pkg_name = pkg_dir.get("package", pkg_dir.get("path", "unknown"))
        version_number = pkg_dir.get("versionNumber", "")
        ancestor_id = pkg_dir.get("ancestorId", "")
        ancestor_version = pkg_dir.get("ancestorVersion", "")

        # Check that packages with version numbers have ancestor tracking
        if version_number and not ancestor_id and not ancestor_version:
            # Only flag if this looks like it's not the first version
            if version_number and not version_number.startswith("1.0.0"):
                issues.append(
                    f"Package '{pkg_name}' has versionNumber '{version_number}' "
                    "but no ancestorId or ancestorVersion. "
                    "Package versions after 1.0.0 should specify an ancestor "
                    "to maintain linear version ancestry."
                )

        # Check for HIGHEST keyword (recommended practice)
        if ancestor_version == "HIGHEST":
            pass  # This is the recommended practice, no issue
        elif ancestor_id and not ancestor_id.startswith("04t"):
            issues.append(
                f"Package '{pkg_name}' has ancestorId '{ancestor_id}' "
                "which does not start with '04t'. "
                "Ancestor IDs should be SubscriberPackageVersion IDs (04t prefix)."
            )

    return issues


def check_branch_protection_config(project_dir: Path) -> list[str]:
    """Check for branch protection configuration files."""
    issues: list[str] = []

    # Check GitHub branch protection (CODEOWNERS, workflow files)
    github_dir = project_dir / ".github"
    has_github = github_dir.exists()
    has_codeowners = (
        (project_dir / "CODEOWNERS").exists()
        or (github_dir / "CODEOWNERS").exists()
    )

    # Check for CI workflow files that enforce branch rules
    workflows_dir = github_dir / "workflows" if has_github else None
    has_ci_workflows = False
    ci_checks_main = False

    if workflows_dir and workflows_dir.exists():
        for wf_file in workflows_dir.glob("*.yml"):
            has_ci_workflows = True
            try:
                content = wf_file.read_text(encoding="utf-8")
                if re.search(
                    r"branches:\s*\n\s*-\s*(main|master)", content
                ):
                    ci_checks_main = True
            except OSError:
                pass
        for wf_file in workflows_dir.glob("*.yaml"):
            has_ci_workflows = True
            try:
                content = wf_file.read_text(encoding="utf-8")
                if re.search(
                    r"branches:\s*\n\s*-\s*(main|master)", content
                ):
                    ci_checks_main = True
            except OSError:
                pass

    # Check GitLab CI
    gitlab_ci = project_dir / ".gitlab-ci.yml"
    has_gitlab_ci = gitlab_ci.exists()

    if not has_ci_workflows and not has_gitlab_ci:
        issues.append(
            "No CI workflow files found (.github/workflows/*.yml or .gitlab-ci.yml). "
            "Branch protection without CI enforcement is incomplete. "
            "Add CI workflows that validate deploys on pull requests to main."
        )
    elif has_ci_workflows and not ci_checks_main:
        issues.append(
            "CI workflows exist but none appear to run on the main/master branch. "
            "Ensure at least one workflow triggers on pull_request to main."
        )

    if not has_codeowners and has_github:
        issues.append(
            "No CODEOWNERS file found. Consider adding one to enforce "
            "review requirements for critical paths (sfdx-project.json, "
            "destructive changes, permission sets)."
        )

    return issues


def check_destructive_changes(project_dir: Path) -> list[str]:
    """Check for destructive changes manifests and their CI integration."""
    issues: list[str] = []

    destructive_files = list(project_dir.rglob("destructiveChanges*.xml"))
    pre_destructive = list(project_dir.rglob("destructiveChangesPre.xml"))
    post_destructive = list(project_dir.rglob("destructiveChangesPost.xml"))

    if not destructive_files:
        return issues  # No destructive changes present, nothing to check

    # Check if CI config references destructive changes
    ci_handles_destructive = False

    # Check GitHub Actions
    workflows_dir = project_dir / ".github" / "workflows"
    if workflows_dir.exists():
        for wf_file in list(workflows_dir.glob("*.yml")) + list(
            workflows_dir.glob("*.yaml")
        ):
            try:
                content = wf_file.read_text(encoding="utf-8")
                if "destructive" in content.lower():
                    ci_handles_destructive = True
                    break
            except OSError:
                pass

    # Check GitLab CI
    gitlab_ci = project_dir / ".gitlab-ci.yml"
    if gitlab_ci.exists():
        try:
            content = gitlab_ci.read_text(encoding="utf-8")
            if "destructive" in content.lower():
                ci_handles_destructive = True
        except OSError:
            pass

    if not ci_handles_destructive:
        files_str = ", ".join(str(f.relative_to(project_dir)) for f in destructive_files[:3])
        issues.append(
            f"Destructive change manifests found ({files_str}) but CI config "
            "does not reference destructive changes. Deletions will not be "
            "applied on deploy. Add --pre-destructive-changes or "
            "--post-destructive-changes flags to your deploy commands."
        )

    return issues


def check_git_branches(project_dir: Path) -> list[str]:
    """Check git branch state for branching strategy issues."""
    issues: list[str] = []

    try:
        result = subprocess.run(
            ["git", "branch", "-a", "--format=%(refname:short) %(committerdate:relative)"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=10,
        )
        if result.returncode != 0:
            issues.append(
                "Could not list git branches. Ensure this is a git repository."
            )
            return issues
    except (FileNotFoundError, subprocess.TimeoutExpired):
        issues.append("git command not available or timed out.")
        return issues

    lines = result.stdout.strip().split("\n")
    feature_branches = []
    stale_branches = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parts = line.split(" ", 1)
        branch_name = parts[0]
        age_info = parts[1] if len(parts) > 1 else ""

        # Identify feature branches
        if branch_name.startswith("feature/") or branch_name.startswith("origin/feature/"):
            feature_branches.append(branch_name)

            # Check for stale feature branches (older than 2 weeks)
            if any(
                period in age_info
                for period in ["months ago", "years ago", "weeks ago"]
            ):
                # "weeks ago" could be 1 week; only flag if > 2 weeks
                if "months ago" in age_info or "years ago" in age_info:
                    stale_branches.append(branch_name)
                elif "weeks ago" in age_info:
                    # Extract week count
                    week_match = re.search(r"(\d+)\s+weeks?\s+ago", age_info)
                    if week_match and int(week_match.group(1)) > 2:
                        stale_branches.append(branch_name)

    if stale_branches:
        branch_list = ", ".join(stale_branches[:5])
        suffix = f" (and {len(stale_branches) - 5} more)" if len(stale_branches) > 5 else ""
        issues.append(
            f"Stale feature branches detected: {branch_list}{suffix}. "
            "Feature branches older than 2 weeks accumulate merge debt. "
            "Consider merging or deleting them."
        )

    # Check for main/master branch existence
    branch_names = [line.split()[0] for line in lines if line.strip()]
    has_main = any(
        b in ("main", "master", "origin/main", "origin/master")
        for b in branch_names
    )
    if not has_main:
        issues.append(
            "No main or master branch found. "
            "A primary branch is required as the production source of truth."
        )

    return issues


def check_git_branching_for_salesforce(
    project_dir: Path, check_branches: bool = False
) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    issues: list[str] = []

    if not project_dir.exists():
        issues.append(f"Project directory not found: {project_dir}")
        return issues

    issues.extend(check_sfdx_project_json(project_dir))
    issues.extend(check_branch_protection_config(project_dir))
    issues.extend(check_destructive_changes(project_dir))

    if check_branches:
        issues.extend(check_git_branches(project_dir))

    return issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    issues = check_git_branching_for_salesforce(
        project_dir, check_branches=args.check_branches
    )

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
