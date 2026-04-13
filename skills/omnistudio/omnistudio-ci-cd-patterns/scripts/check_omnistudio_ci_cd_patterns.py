#!/usr/bin/env python3
"""Checker script for OmniStudio CI/CD Patterns skill.

Checks pipeline configuration files and DataPack job files for common CI/CD anti-patterns.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_ci_cd_patterns.py [--help]
    python3 check_omnistudio_ci_cd_patterns.py --manifest-dir path/to/pipeline-config
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check OmniStudio CI/CD pipeline files for common anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the project (default: current directory).",
    )
    return parser.parse_args()


def check_job_files(project_dir: Path) -> list[str]:
    """Check OmniStudio Build Tool job files for anti-patterns."""
    issues: list[str] = []

    # Find YAML job files that may be OmniStudio Build Tool job files
    for yaml_file in project_dir.rglob("*.yaml"):
        try:
            content = yaml_file.read_text(encoding="utf-8")

            # Check for inline credentials in job files
            if any(key in content for key in ("password:", "securityToken:", "accessToken:")):
                # Also check that vlocityNamespace is present (strong signal this is a job file)
                if "vlocityNamespace" in content or "omnistudio" in content.lower():
                    issues.append(
                        f"Potential credential in OmniStudio job file: {yaml_file}. "
                        "Credentials must not be inline in job files — use environment variables "
                        "and CI/CD secrets instead."
                    )
        except OSError:
            pass

    return issues


def check_pipeline_files(project_dir: Path) -> list[str]:
    """Check CI/CD pipeline files for missing --activate flag in DataPack deploy commands."""
    issues: list[str] = []

    # Check GitHub Actions workflows
    workflow_dir = project_dir / ".github" / "workflows"
    if workflow_dir.exists():
        for workflow_file in workflow_dir.glob("*.yml"):
            try:
                content = workflow_file.read_text(encoding="utf-8")

                # Check for DataPack deploy commands missing --activate
                deploy_cmds = re.findall(
                    r"(omnistudio datapack deploy[^\n]*|packDeploy[^\n]*)", content
                )
                for cmd in deploy_cmds:
                    if "--activate" not in cmd and "activate" not in cmd:
                        issues.append(
                            f"DataPack deploy command in {workflow_file} may be missing "
                            f"--activate flag: '{cmd.strip()}'. "
                            "Without --activate, the imported component version will not go live."
                        )
            except OSError:
                pass

    # Check Bitbucket Pipelines
    bitbucket_file = project_dir / "bitbucket-pipelines.yml"
    if bitbucket_file.exists():
        try:
            content = bitbucket_file.read_text(encoding="utf-8")
            deploy_cmds = re.findall(
                r"(omnistudio datapack deploy[^\n]*|packDeploy[^\n]*)", content
            )
            for cmd in deploy_cmds:
                if "--activate" not in cmd and "activate" not in cmd:
                    issues.append(
                        f"DataPack deploy command in {bitbucket_file} may be missing "
                        f"--activate flag: '{cmd.strip()}'."
                    )
        except OSError:
            pass

    return issues


def check_datapack_manifests(project_dir: Path) -> list[str]:
    """Check for DataPack JSON files and warn if they appear to be incomplete exports."""
    issues: list[str] = []

    # Find DataPack directories
    for dp_dir in project_dir.rglob("datapacks"):
        if not dp_dir.is_dir():
            continue

        json_files = list(dp_dir.glob("**/*.json"))
        if not json_files:
            issues.append(
                f"DataPack directory {dp_dir} contains no JSON files. "
                "Ensure DataPack export has been run and committed."
            )
            continue

        # Check each DataPack JSON for basic structure
        for json_file in json_files[:10]:  # Limit to avoid excessive scanning
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    dp_type = data.get("VlocityDataPackType", "")
                    if dp_type and "VlocityMatchingRecords" not in data:
                        issues.append(
                            f"DataPack file {json_file} has VlocityDataPackType '{dp_type}' "
                            "but no VlocityMatchingRecords — may be an incomplete export."
                        )
            except (json.JSONDecodeError, OSError):
                pass

    return issues


def check_omnistudio_ci_cd_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_job_files(manifest_dir))
    issues.extend(check_pipeline_files(manifest_dir))
    issues.extend(check_datapack_manifests(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_omnistudio_ci_cd_patterns(manifest_dir)

    if not issues:
        print("No OmniStudio CI/CD anti-patterns found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
