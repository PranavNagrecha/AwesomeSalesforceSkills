#!/usr/bin/env python3
"""Checker script for VS Code Salesforce Extensions skill.

Validates that a Salesforce DX project workspace is correctly configured
for the Salesforce Extension Pack in VS Code.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_vscode_salesforce_extensions.py [--help]
    python3 check_vscode_salesforce_extensions.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check VS Code Salesforce Extensions workspace configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict | list | None:
    """Load a JSON file, returning None on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def check_sfdx_project(manifest_dir: Path) -> list[str]:
    """Check that sfdx-project.json exists at the workspace root."""
    issues: list[str] = []
    project_file = manifest_dir / "sfdx-project.json"
    if not project_file.exists():
        issues.append(
            "sfdx-project.json not found at workspace root. "
            "The Apex Language Server will not activate without it. "
            "Ensure VS Code opens the folder that directly contains sfdx-project.json."
        )
        return issues

    data = _load_json(project_file)
    if data is None:
        issues.append("sfdx-project.json exists but is not valid JSON.")
        return issues

    if not isinstance(data, dict):
        issues.append("sfdx-project.json should be a JSON object at the top level.")
        return issues

    # Check packageDirectories
    pkg_dirs = data.get("packageDirectories")
    if not pkg_dirs or not isinstance(pkg_dirs, list):
        issues.append(
            "sfdx-project.json is missing 'packageDirectories'. "
            "The Apex Language Server needs at least one package directory to index."
        )
    elif len(pkg_dirs) > 10:
        issues.append(
            f"sfdx-project.json declares {len(pkg_dirs)} packageDirectories. "
            "Large numbers slow Apex Language Server indexing. "
            "Consider consolidating or reducing scope."
        )

    return issues


def check_vscode_settings(manifest_dir: Path) -> list[str]:
    """Check .vscode/settings.json for Salesforce extension configuration."""
    issues: list[str] = []
    settings_file = manifest_dir / ".vscode" / "settings.json"

    if not settings_file.exists():
        issues.append(
            ".vscode/settings.json not found. "
            "Consider creating one with salesforcedx-vscode-apex.java.home "
            "and deploy-on-save settings for team consistency."
        )
        return issues

    data = _load_json(settings_file)
    if data is None:
        issues.append(".vscode/settings.json exists but is not valid JSON.")
        return issues

    if not isinstance(data, dict):
        issues.append(".vscode/settings.json should be a JSON object.")
        return issues

    # Check java.home setting
    java_home = data.get("salesforcedx-vscode-apex.java.home")
    if not java_home:
        issues.append(
            "salesforcedx-vscode-apex.java.home is not set in .vscode/settings.json. "
            "The Apex Language Server will fall back to JAVA_HOME, which may not be "
            "consistent across team members. Set it explicitly for reliability."
        )
    elif isinstance(java_home, str):
        # Check for JDK 8 references
        if re.search(r"jdk[-_]?1\.8|jdk[-_]?8|java[-_]?8|openjdk@8", java_home, re.IGNORECASE):
            issues.append(
                f"java.home points to what appears to be JDK 8 ({java_home}). "
                "The Apex Language Server requires JDK 11, 17, or 21 (21 recommended)."
            )

    # Check deploy-on-save — warn if enabled (we can't determine org type from config alone)
    deploy_on_save = data.get("salesforcedx-vscode-core.push-or-deploy-on-save.enabled")
    if deploy_on_save is True:
        issues.append(
            "deploy-on-save is enabled. This is safe for source-tracked orgs "
            "(scratch orgs, tracked sandboxes) but dangerous for non-tracked orgs "
            "where it silently overwrites server changes. Verify the default org is source-tracked."
        )

    return issues


def check_launch_json(manifest_dir: Path) -> list[str]:
    """Check .vscode/launch.json for debug configurations."""
    issues: list[str] = []
    launch_file = manifest_dir / ".vscode" / "launch.json"

    if not launch_file.exists():
        # Not an issue per se — not everyone debugs
        return issues

    data = _load_json(launch_file)
    if data is None:
        issues.append(".vscode/launch.json exists but is not valid JSON.")
        return issues

    if isinstance(data, dict):
        configs = data.get("configurations", [])
        if isinstance(configs, list):
            apex_configs = [c for c in configs if isinstance(c, dict) and c.get("type") == "apex"]
            if not apex_configs:
                issues.append(
                    ".vscode/launch.json exists but contains no Apex debug configurations. "
                    "Add a configuration with type 'apex' for the Interactive Debugger."
                )

    return issues


def check_gitignore(manifest_dir: Path) -> list[str]:
    """Check that .sfdx and .sf directories are in .gitignore."""
    issues: list[str] = []
    gitignore = manifest_dir / ".gitignore"

    if not gitignore.exists():
        issues.append(
            ".gitignore not found. Ensure .sfdx/ and .sf/ directories "
            "(which contain auth tokens) are excluded from version control."
        )
        return issues

    try:
        content = gitignore.read_text(encoding="utf-8")
    except OSError:
        return issues

    patterns_to_check = [
        (".sfdx", r"\.sfdx"),
        (".sf", r"\.sf(?:/|\s|$)"),
    ]

    for dirname, pattern in patterns_to_check:
        if not re.search(pattern, content):
            issues.append(
                f"{dirname}/ directory is not in .gitignore. "
                f"This directory may contain org auth tokens and should not be committed."
            )

    return issues


def check_vscode_salesforce_extensions(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sfdx_project(manifest_dir))
    issues.extend(check_vscode_settings(manifest_dir))
    issues.extend(check_launch_json(manifest_dir))
    issues.extend(check_gitignore(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_vscode_salesforce_extensions(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
