#!/usr/bin/env python3
"""Checker script for Second-Generation Managed Packages skill.

Validates a Salesforce DX project directory for common 2GP managed package
configuration issues. Uses stdlib only — no pip dependencies.

Checks performed:
  1. sfdx-project.json exists and is valid JSON.
  2. A namespace is declared in sfdx-project.json.
  3. At least one packageDirectory entry with a package name and versionNumber exists.
  4. Package type is Managed (where detectable via packageAliases 0Ho ID prefix).
  5. versionNumber uses the correct major.minor.patch.build format.
  6. packageAliases section is present.
  7. Any declared dependencies reference an alias that exists in packageAliases.
  8. The scratch org definition file exists (config/project-scratch-def.json by convention).

Usage:
    python3 check_second_generation_managed_packages.py [--project-dir PATH]

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


VERSION_NUMBER_RE = re.compile(
    r"^\d+\.\d+\.\d+\.(NEXT|\d+)$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce DX project for common 2GP managed package "
            "configuration issues."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


def load_sfdx_project(project_dir: Path) -> tuple[dict | None, list[str]]:
    """Load and parse sfdx-project.json. Returns (data, issues)."""
    issues: list[str] = []
    config_path = project_dir / "sfdx-project.json"

    if not config_path.exists():
        issues.append(
            f"sfdx-project.json not found at {config_path}. "
            "Every 2GP project requires this file."
        )
        return None, issues

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(f"sfdx-project.json is not valid JSON: {exc}")
        return None, issues

    return data, issues


def check_namespace(data: dict) -> list[str]:
    """Check that a namespace is declared."""
    issues: list[str] = []
    ns = data.get("namespace", "")
    if not ns or not str(ns).strip():
        issues.append(
            "sfdx-project.json is missing a 'namespace' value. "
            "Managed 2GP packages require a registered namespace linked to the Dev Hub."
        )
    return issues


def check_package_directories(data: dict) -> list[str]:
    """Check packageDirectories entries for required fields."""
    issues: list[str] = []
    dirs = data.get("packageDirectories", [])

    if not dirs:
        issues.append(
            "'packageDirectories' is empty or missing in sfdx-project.json. "
            "At least one entry with 'package' and 'versionNumber' is required."
        )
        return issues

    for i, entry in enumerate(dirs):
        label = entry.get("package") or f"entry[{i}]"

        if not entry.get("package"):
            issues.append(
                f"packageDirectories[{i}] is missing a 'package' name. "
                "Each managed package directory must declare the package name."
            )

        version_number = entry.get("versionNumber", "")
        if not version_number:
            issues.append(
                f"packageDirectories entry '{label}' is missing 'versionNumber'. "
                "Use format major.minor.patch.NEXT (e.g., '1.0.0.NEXT')."
            )
        elif not VERSION_NUMBER_RE.match(str(version_number)):
            issues.append(
                f"packageDirectories entry '{label}' has an invalid 'versionNumber': "
                f"'{version_number}'. Expected format: major.minor.patch.NEXT or "
                "major.minor.patch.build (e.g., '2.1.0.NEXT')."
            )

    return issues


def check_package_aliases(data: dict) -> list[str]:
    """Check packageAliases section is present and non-empty."""
    issues: list[str] = []
    aliases = data.get("packageAliases", {})

    if not aliases:
        issues.append(
            "'packageAliases' is missing or empty in sfdx-project.json. "
            "Package aliases map package names and version names to 0Ho/04t IDs. "
            "Run 'sf package create' and 'sf package version create' to populate this."
        )
        return issues

    # Check that at least one alias looks like a managed package ID (starts with 0Ho)
    managed_ids = [v for v in aliases.values() if str(v).startswith("0Ho")]
    if not managed_ids:
        issues.append(
            "No managed package IDs (starting with '0Ho') found in 'packageAliases'. "
            "Run 'sf package create --package-type Managed' and add the resulting ID."
        )

    return issues


def check_dependency_aliases(data: dict) -> list[str]:
    """Check that dependency package names resolve in packageAliases."""
    issues: list[str] = []
    aliases = data.get("packageAliases", {})
    dirs = data.get("packageDirectories", [])

    for entry in dirs:
        label = entry.get("package") or "unknown"
        dependencies = entry.get("dependencies", [])
        for dep in dependencies:
            dep_package = dep.get("package", "")
            if not dep_package:
                continue
            # Dependencies may be listed as "PackageName" or "PackageName@version"
            # Check if the base name exists as an alias prefix
            found = any(
                alias == dep_package or alias.startswith(dep_package + "@")
                for alias in aliases
            )
            if not found:
                issues.append(
                    f"Dependency '{dep_package}' declared in package '{label}' "
                    "does not have a matching entry in 'packageAliases'. "
                    "Add the resolved version ID to packageAliases before building."
                )

    return issues


def check_scratch_org_definition(project_dir: Path) -> list[str]:
    """Check that a scratch org definition file exists at the conventional path."""
    issues: list[str] = []
    scratch_def = project_dir / "config" / "project-scratch-def.json"

    if not scratch_def.exists():
        issues.append(
            f"Scratch org definition file not found at {scratch_def}. "
            "A scratch org definition (config/project-scratch-def.json) is required "
            "to create development scratch orgs and to run package version tests. "
            "Create this file with the features your package requires."
        )
        return issues

    try:
        defn = json.loads(scratch_def.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(
            f"config/project-scratch-def.json is not valid JSON: {exc}"
        )
        return issues

    if not defn.get("edition"):
        issues.append(
            "config/project-scratch-def.json is missing an 'edition' field. "
            "Specify the Salesforce edition to use for scratch orgs "
            "(e.g., 'Developer', 'Enterprise')."
        )

    return issues


def check_source_api_version(data: dict) -> list[str]:
    """Warn if sourceApiVersion is below the minimum for 2GP promotion (API 64)."""
    issues: list[str] = []
    raw = data.get("sourceApiVersion", "")
    try:
        version = float(str(raw))
    except ValueError:
        issues.append(
            f"'sourceApiVersion' value '{raw}' in sfdx-project.json is not a valid "
            "number. Set it to the current API version (e.g., '63.0')."
        )
        return issues

    if version < 57:
        issues.append(
            f"'sourceApiVersion' is {raw}. The minimum API version for converting "
            "or creating promotable 2GP managed package versions is 57 (Spring '23). "
            "Update 'sourceApiVersion' to at least 57.0."
        )
    return issues


def run_checks(project_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    all_issues: list[str] = []

    data, load_issues = load_sfdx_project(project_dir)
    all_issues.extend(load_issues)

    if data is None:
        return all_issues

    all_issues.extend(check_namespace(data))
    all_issues.extend(check_package_directories(data))
    all_issues.extend(check_package_aliases(data))
    all_issues.extend(check_dependency_aliases(data))
    all_issues.extend(check_scratch_org_definition(project_dir))
    all_issues.extend(check_source_api_version(data))

    return all_issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()

    if not project_dir.is_dir():
        print(f"ISSUE: Project directory not found: {project_dir}")
        return 1

    issues = run_checks(project_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
