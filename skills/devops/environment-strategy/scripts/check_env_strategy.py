#!/usr/bin/env python3
"""Checker script for Environment Strategy skill.

Checks a Salesforce DX project for environment strategy configuration issues:
- Presence of sfdx-project.json with packageDirectories
- Presence of at least one scratch org definition file
- Scratch org definition files do not set 'release: preview' unintentionally
- CI pipeline files reference scratch org deletion steps

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_env_strategy.py [--project-dir PATH]
    python3 check_env_strategy.py --project-dir /path/to/sf-project
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce DX project for environment strategy configuration issues. "
            "Validates sfdx-project.json, scratch org definition files, and CI pipeline scripts."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


def check_sfdx_project_json(project_dir: Path) -> list[str]:
    """Check sfdx-project.json for required fields."""
    issues: list[str] = []
    sfdx_json = project_dir / "sfdx-project.json"

    if not sfdx_json.exists():
        issues.append(
            "sfdx-project.json not found in project root. "
            "Source-driven development requires this file. "
            "Run 'sf project generate' to create it."
        )
        return issues

    try:
        data = json.loads(sfdx_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(f"sfdx-project.json is not valid JSON: {exc}")
        return issues

    if "packageDirectories" not in data:
        issues.append(
            "sfdx-project.json is missing 'packageDirectories'. "
            "This field is required for source-driven deployments. "
            "Add at least one entry pointing to your source directory (e.g., 'force-app')."
        )

    pkg_dirs = data.get("packageDirectories", [])
    if isinstance(pkg_dirs, list) and len(pkg_dirs) == 0:
        issues.append(
            "'packageDirectories' in sfdx-project.json is empty. "
            "Add at least one source directory entry."
        )

    return issues


def find_scratch_org_definitions(project_dir: Path) -> list[Path]:
    """Return all .json files under config/ that look like scratch org definitions."""
    config_dir = project_dir / "config"
    if not config_dir.exists():
        return []

    candidates = list(config_dir.glob("*.json"))
    scratch_defs = []
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        # Scratch org definition files typically have 'edition' or 'orgName'
        if "edition" in data or "orgName" in data or "features" in data:
            scratch_defs.append(path)
    return scratch_defs


def check_scratch_org_definitions(project_dir: Path) -> list[str]:
    """Check scratch org definition files for common issues."""
    issues: list[str] = []
    scratch_defs = find_scratch_org_definitions(project_dir)

    if not scratch_defs:
        issues.append(
            "No scratch org definition file found under config/. "
            "If your environment strategy includes scratch orgs for CI or development, "
            "create config/project-scratch-def.json. "
            "If you use sandboxes only, you can ignore this warning."
        )
        return issues

    for def_file in scratch_defs:
        try:
            data = json.loads(def_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        release_value = data.get("release", "").lower()
        if release_value == "preview":
            issues.append(
                f"{def_file.name}: 'release' is set to 'preview'. "
                "Preview scratch orgs receive the next Salesforce release before production, "
                "which can cause CI failures on features that behave differently between releases. "
                "Remove 'release: preview' unless you are explicitly testing release readiness."
            )

        edition = data.get("edition", "")
        if not edition:
            issues.append(
                f"{def_file.name}: 'edition' field is missing. "
                "Specify 'edition' (e.g., 'Developer' or 'Enterprise') to ensure "
                "scratch orgs are created with the correct feature set."
            )

    return issues


def check_ci_pipeline_files(project_dir: Path) -> list[str]:
    """Check common CI pipeline files for scratch org deletion steps."""
    issues: list[str] = []

    # Common CI config file locations
    ci_candidates = [
        project_dir / ".github" / "workflows",
        project_dir / ".circleci",
        project_dir / ".gitlab-ci.yml",
        project_dir / "Jenkinsfile",
        project_dir / "bitbucket-pipelines.yml",
    ]

    pipeline_files: list[Path] = []
    for candidate in ci_candidates:
        if candidate.is_dir():
            pipeline_files.extend(candidate.glob("*.yml"))
            pipeline_files.extend(candidate.glob("*.yaml"))
        elif candidate.is_file():
            pipeline_files.append(candidate)

    if not pipeline_files:
        # No CI files found — not necessarily an issue
        return issues

    for pipeline_file in pipeline_files:
        try:
            content = pipeline_file.read_text(encoding="utf-8")
        except OSError:
            continue

        creates_scratch_org = (
            "org create scratch" in content
            or "force:org:create" in content
        )
        deletes_scratch_org = (
            "org delete scratch" in content
            or "force:org:delete" in content
        )

        if creates_scratch_org and not deletes_scratch_org:
            issues.append(
                f"{pipeline_file.relative_to(project_dir)}: "
                "Creates a scratch org but does not appear to delete it. "
                "Active scratch orgs count against your Dev Hub limit (typically 40 max). "
                "Add 'sf org delete scratch --no-prompt --target-org <alias>' "
                "in a cleanup or finally step to avoid hitting the limit."
            )

    return issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()

    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}")
        return 1

    all_issues: list[str] = []
    all_issues.extend(check_sfdx_project_json(project_dir))
    all_issues.extend(check_scratch_org_definitions(project_dir))
    all_issues.extend(check_ci_pipeline_files(project_dir))

    if not all_issues:
        print("No environment strategy issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
