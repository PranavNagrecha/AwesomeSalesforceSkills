#!/usr/bin/env python3
"""Checker script for Migration From Change Sets To SFDX skill.

Inspects an SFDX project directory for common migration issues:
- Missing or misconfigured sfdx-project.json
- Missing .forceignore
- Profiles present in source (should be excluded)
- sourceApiVersion mismatch or staleness
- Empty force-app directory (conversion not yet run)
- Managed-package metadata leaking into source

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_migration_from_change_sets_to_sfdx.py --project-dir path/to/sfdx-project
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check an SFDX project for common change-set-to-SFDX migration issues.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the SFDX project (default: current directory).",
    )
    parser.add_argument(
        "--expected-api-version",
        default=None,
        help="Expected sourceApiVersion (e.g., '62.0'). Warns if sfdx-project.json differs.",
    )
    return parser.parse_args()


def check_sfdx_project_json(project_dir: Path, expected_api: str | None) -> list[str]:
    """Check sfdx-project.json for migration-relevant issues."""
    issues: list[str] = []
    proj_file = project_dir / "sfdx-project.json"

    if not proj_file.exists():
        issues.append(
            "sfdx-project.json not found. Run 'sf project generate' to create an SFDX project "
            "before converting metadata."
        )
        return issues

    try:
        with open(proj_file) as f:
            proj = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        issues.append(f"sfdx-project.json is not valid JSON: {e}")
        return issues

    # Check sourceApiVersion
    api_version = proj.get("sourceApiVersion")
    if not api_version:
        issues.append(
            "sfdx-project.json is missing 'sourceApiVersion'. Set it to match the org's "
            "current API version to avoid missing metadata fields during retrieval."
        )
    elif expected_api and api_version != expected_api:
        issues.append(
            f"sourceApiVersion is '{api_version}' but expected '{expected_api}'. "
            f"Mismatched API versions cause silent metadata field omission during retrieval."
        )

    # Check packageDirectories
    pkg_dirs = proj.get("packageDirectories", [])
    if not pkg_dirs:
        issues.append(
            "sfdx-project.json has no 'packageDirectories' entries. At least one entry "
            "(typically pointing to 'force-app') is required."
        )
    else:
        paths_exist = []
        for entry in pkg_dirs:
            p = entry.get("path", "")
            full = project_dir / p
            if not full.exists():
                issues.append(
                    f"packageDirectories path '{p}' does not exist on disk. "
                    f"Run 'sf project convert mdapi' with --output-dir {p}/ to populate it."
                )
            else:
                paths_exist.append(full)

        # Check if any source directory is empty (conversion not run)
        for src_path in paths_exist:
            default_dir = src_path / "main" / "default"
            if default_dir.exists() and not any(default_dir.iterdir()):
                issues.append(
                    f"Source directory '{src_path}/main/default/' exists but is empty. "
                    f"Has 'sf project convert mdapi' been run?"
                )

    return issues


def check_forceignore(project_dir: Path) -> list[str]:
    """Check for .forceignore and common exclusion patterns."""
    issues: list[str] = []
    fi = project_dir / ".forceignore"

    if not fi.exists():
        issues.append(
            ".forceignore not found. Without it, deploys may include managed-package "
            "components and profiles, causing errors or unintended overwrites."
        )
        return issues

    try:
        content = fi.read_text()
    except OSError:
        issues.append(".forceignore exists but cannot be read.")
        return issues

    # Check for common recommended exclusions
    if "**/profiles/**" not in content and "profiles/" not in content:
        issues.append(
            ".forceignore does not exclude profiles. Deploying profiles overwrites the "
            "entire profile in the target org. Add '**/profiles/**' unless profiles "
            "are intentionally managed in source."
        )

    if "**/installedPackages/**" not in content and "installedPackages" not in content:
        issues.append(
            ".forceignore does not exclude installedPackages. Managed-package metadata "
            "cannot be redeployed and will cause errors. Add '**/installedPackages/**'."
        )

    return issues


def check_for_profile_leakage(project_dir: Path) -> list[str]:
    """Check if profile metadata is present in source directories."""
    issues: list[str] = []

    for pkg_dir in (project_dir / "force-app", project_dir / "src"):
        profiles_dir = pkg_dir / "main" / "default" / "profiles"
        if profiles_dir.exists():
            profile_files = list(profiles_dir.glob("*.profile-meta.xml"))
            if profile_files:
                names = [p.stem.replace(".profile-meta", "") for p in profile_files[:5]]
                suffix = f" (and {len(profile_files) - 5} more)" if len(profile_files) > 5 else ""
                issues.append(
                    f"Found {len(profile_files)} profile(s) in source: "
                    f"{', '.join(names)}{suffix}. Profiles should be excluded via "
                    f".forceignore and managed through permission sets."
                )

    return issues


def check_for_managed_package_leakage(project_dir: Path) -> list[str]:
    """Check if managed-package metadata leaked into source."""
    issues: list[str] = []
    installed_dir = project_dir / "force-app" / "main" / "default" / "installedPackages"
    if installed_dir.exists() and any(installed_dir.iterdir()):
        issues.append(
            "installedPackages directory found in source. Managed-package metadata "
            "cannot be redeployed and should be excluded via .forceignore."
        )
    return issues


def check_migration_from_change_sets_to_sfdx(
    project_dir: Path, expected_api: str | None
) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    issues: list[str] = []

    if not project_dir.exists():
        issues.append(f"Project directory not found: {project_dir}")
        return issues

    issues.extend(check_sfdx_project_json(project_dir, expected_api))
    issues.extend(check_forceignore(project_dir))
    issues.extend(check_for_profile_leakage(project_dir))
    issues.extend(check_for_managed_package_leakage(project_dir))

    return issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    issues = check_migration_from_change_sets_to_sfdx(project_dir, args.expected_api_version)

    if not issues:
        print("No migration issues found. Project structure looks ready for source-driven development.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
