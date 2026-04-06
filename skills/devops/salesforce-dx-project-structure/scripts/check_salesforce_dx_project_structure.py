#!/usr/bin/env python3
"""Checker script for Salesforce DX Project Structure skill.

Validates sfdx-project.json configuration for common issues:
- Missing or malformed packageDirectories
- Missing default flag
- Invalid sourceApiVersion format
- Duplicate paths
- Hardcoded build numbers in versionNumber
- Credential leaks
- Non-existent package directory paths

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_salesforce_dx_project_structure.py [--help]
    python3 check_salesforce_dx_project_structure.py --project-dir path/to/project
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check sfdx-project.json for common configuration issues.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


def check_sfdx_project_json_exists(project_dir: Path) -> tuple[dict | None, list[str]]:
    """Check that sfdx-project.json exists and is valid JSON. Return parsed data and issues."""
    issues: list[str] = []
    sfdx_json = project_dir / "sfdx-project.json"

    if not sfdx_json.exists():
        issues.append(
            "sfdx-project.json not found at project root. "
            "Run 'sf project generate --name <name>' to create one."
        )
        return None, issues

    try:
        data = json.loads(sfdx_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(f"sfdx-project.json is not valid JSON: {exc}")
        return None, issues

    if not isinstance(data, dict):
        issues.append("sfdx-project.json root must be a JSON object, not an array or primitive.")
        return None, issues

    return data, issues


def check_package_directories(data: dict, project_dir: Path) -> list[str]:
    """Validate the packageDirectories array."""
    issues: list[str] = []

    pkg_dirs = data.get("packageDirectories")
    if pkg_dirs is None:
        issues.append(
            "Missing required 'packageDirectories' array in sfdx-project.json. "
            "At least one entry with a 'path' is required."
        )
        return issues

    if not isinstance(pkg_dirs, list) or len(pkg_dirs) == 0:
        issues.append(
            "'packageDirectories' must be a non-empty array. "
            "Add at least one entry: {\"path\": \"force-app\", \"default\": true}."
        )
        return issues

    # Check for default flag
    defaults = [entry for entry in pkg_dirs if entry.get("default") is True]
    if len(defaults) == 0:
        issues.append(
            "No packageDirectory has '\"default\": true'. "
            "Exactly one entry must be the default so the CLI knows where to place new metadata."
        )
    elif len(defaults) > 1:
        issues.append(
            f"Multiple packageDirectories have '\"default\": true' ({len(defaults)} found). "
            "Exactly one entry should be the default."
        )

    # Check paths
    seen_paths: set[str] = set()
    for i, entry in enumerate(pkg_dirs):
        if not isinstance(entry, dict):
            issues.append(f"packageDirectories[{i}] is not a JSON object.")
            continue

        path_val = entry.get("path")
        if not path_val:
            issues.append(f"packageDirectories[{i}] is missing the required 'path' field.")
            continue

        # Duplicate path check
        normalized = str(Path(path_val))
        if normalized in seen_paths:
            issues.append(
                f"Duplicate path '{path_val}' in packageDirectories. "
                "Each entry must point to a unique directory."
            )
        seen_paths.add(normalized)

        # Directory existence check
        resolved = project_dir / path_val
        if not resolved.is_dir():
            issues.append(
                f"packageDirectories[{i}].path '{path_val}' does not exist as a directory. "
                "Create the directory or fix the path."
            )

        # versionNumber format check
        version_num = entry.get("versionNumber")
        if version_num:
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", version_num):
                issues.append(
                    f"packageDirectories[{i}].versionNumber '{version_num}' uses a hardcoded "
                    "build number. Use 'NEXT' as the fourth segment (e.g., '1.0.0.NEXT') "
                    "so the CLI auto-increments during package version creation."
                )
            elif not re.match(r"^\d+\.\d+\.\d+\.(NEXT|LATEST)$", version_num):
                issues.append(
                    f"packageDirectories[{i}].versionNumber '{version_num}' does not match "
                    "the required format: MAJOR.MINOR.PATCH.NEXT (or .LATEST for dependencies)."
                )

    return issues


def check_source_api_version(data: dict) -> list[str]:
    """Validate sourceApiVersion format."""
    issues: list[str] = []

    version = data.get("sourceApiVersion")
    if version is None:
        issues.append(
            "Missing 'sourceApiVersion' in sfdx-project.json. "
            "Set it to the API version of your lowest-supported target org (e.g., \"62.0\")."
        )
        return issues

    if not isinstance(version, str):
        issues.append(
            f"'sourceApiVersion' must be a string (e.g., \"62.0\"), not {type(version).__name__}. "
            "Numeric values cause CLI parsing issues."
        )
        return issues

    if not re.match(r"^\d+\.\d+$", version):
        issues.append(
            f"'sourceApiVersion' value '{version}' does not match expected format 'NN.0' "
            "(e.g., '62.0')."
        )

    return issues


def check_credential_leaks(data: dict) -> list[str]:
    """Check for credential-like values in the project config."""
    issues: list[str] = []

    raw_text = json.dumps(data)

    # Check for sfdxAuthUrl patterns
    if "force://" in raw_text.lower():
        issues.append(
            "Possible sfdxAuthUrl detected in sfdx-project.json. "
            "Auth URLs must never be committed to version control. "
            "Use CI secrets or 'sf org login' instead."
        )

    # Check for common credential keys
    credential_keys = {"password", "secret", "token", "accessToken", "refreshToken"}
    for key in data:
        if key.lower() in {k.lower() for k in credential_keys}:
            issues.append(
                f"Suspicious key '{key}' found at top level of sfdx-project.json. "
                "Credentials should not be stored in the project config file."
            )

    return issues


def check_unknown_top_level_keys(data: dict) -> list[str]:
    """Warn about top-level keys that are not part of the known schema."""
    issues: list[str] = []

    known_keys = {
        "packageDirectories",
        "namespace",
        "sourceApiVersion",
        "sfdcLoginUrl",
        "signupTargetLoginUrl",
        "plugins",
        "packageAliases",
        "oauthLocalPort",
    }

    # Keys that suggest scratch org config was mixed in
    scratch_org_keys = {"edition", "features", "orgName", "settings", "orgPreferences"}

    for key in data:
        if key not in known_keys:
            if key in scratch_org_keys:
                issues.append(
                    f"Key '{key}' belongs in the scratch org definition file "
                    "(config/project-scratch-def.json), not in sfdx-project.json."
                )
            else:
                issues.append(
                    f"Unknown top-level key '{key}' in sfdx-project.json. "
                    "It will be silently ignored by the CLI. "
                    f"Known keys: {', '.join(sorted(known_keys))}."
                )

    return issues


def check_gitignore(project_dir: Path) -> list[str]:
    """Check that .gitignore excludes sensitive directories."""
    issues: list[str] = []

    gitignore = project_dir / ".gitignore"
    if not gitignore.exists():
        issues.append(
            "No .gitignore found at project root. "
            "Add one with entries for .sfdx/, .sf/, and auth credential files."
        )
        return issues

    content = gitignore.read_text(encoding="utf-8", errors="replace")
    required_patterns = [".sfdx", ".sf"]

    for pattern in required_patterns:
        # Check for the pattern (with or without trailing slash)
        if pattern not in content:
            issues.append(
                f".gitignore does not appear to exclude '{pattern}/'. "
                "This directory contains local auth state and should never be committed."
            )

    return issues


def check_salesforce_dx_project_structure(project_dir: Path) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    all_issues: list[str] = []

    data, parse_issues = check_sfdx_project_json_exists(project_dir)
    all_issues.extend(parse_issues)

    if data is None:
        return all_issues

    all_issues.extend(check_package_directories(data, project_dir))
    all_issues.extend(check_source_api_version(data))
    all_issues.extend(check_credential_leaks(data))
    all_issues.extend(check_unknown_top_level_keys(data))
    all_issues.extend(check_gitignore(project_dir))

    return all_issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    issues = check_salesforce_dx_project_structure(project_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
