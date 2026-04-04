#!/usr/bin/env python3
"""Checker script for Unlocked Package Development skill.

Validates sfdx-project.json for unlocked package configuration correctness.
Checks package directories, aliases, namespace consistency, dependency
declarations, and version number format.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_unlocked_package_development.py [--help]
    python3 check_unlocked_package_development.py --project-dir /path/to/sfdx/project
    python3 check_unlocked_package_development.py --project-dir . --verbose
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# Salesforce ID patterns
PACKAGE_ID_RE = re.compile(r"^0Ho[a-zA-Z0-9]{15}$")
VERSION_ID_RE = re.compile(r"^04t[a-zA-Z0-9]{15}$")
# Version number: major.minor.patch.build or major.minor.patch.NEXT / LATEST
VERSION_NUMBER_RE = re.compile(
    r"^\d+\.\d+\.\d+\.(NEXT|LATEST|\d+)$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate sfdx-project.json for unlocked package configuration issues. "
            "Checks package directories, aliases, namespace consistency, "
            "dependency declarations, and version number format."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print details about each check, including passing checks.",
    )
    return parser.parse_args()


def load_sfdx_project(project_dir: Path) -> tuple[dict | None, list[str]]:
    """Load and parse sfdx-project.json. Returns (data, issues)."""
    issues: list[str] = []
    project_file = project_dir / "sfdx-project.json"

    if not project_file.exists():
        issues.append(
            f"sfdx-project.json not found in '{project_dir}'. "
            "Run this checker from the root of a Salesforce DX project."
        )
        return None, issues

    try:
        with project_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        issues.append(f"sfdx-project.json is not valid JSON: {exc}")
        return None, issues

    return data, issues


def check_namespace(data: dict, issues: list[str], verbose: bool) -> None:
    """Check namespace field is present and well-formed."""
    namespace = data.get("namespace")
    if namespace is None:
        issues.append(
            "Missing 'namespace' field in sfdx-project.json. "
            "Set to \"\" for namespace-less or to your registered namespace string."
        )
    elif not isinstance(namespace, str):
        issues.append(
            f"'namespace' must be a string, got {type(namespace).__name__}."
        )
    elif verbose:
        if namespace == "":
            print("  [OK] namespace: namespace-less (empty string)")
        else:
            print(f"  [OK] namespace: '{namespace}'")


def check_source_api_version(data: dict, issues: list[str], verbose: bool) -> None:
    """Check sourceApiVersion is present."""
    api_version = data.get("sourceApiVersion")
    if not api_version:
        issues.append(
            "Missing 'sourceApiVersion' in sfdx-project.json. "
            "Set to the API version matching your target Salesforce release (e.g., '63.0')."
        )
    elif verbose:
        print(f"  [OK] sourceApiVersion: {api_version}")


def check_package_directories(
    data: dict, issues: list[str], verbose: bool
) -> list[str]:
    """
    Check packageDirectories entries for required fields and valid formats.
    Returns a list of declared package names.
    """
    package_dirs = data.get("packageDirectories", [])
    declared_packages: list[str] = []

    if not isinstance(package_dirs, list):
        issues.append("'packageDirectories' must be an array.")
        return declared_packages

    if not package_dirs:
        issues.append(
            "'packageDirectories' is empty. "
            "Add at least one entry with 'path', 'package', and 'versionNumber'."
        )
        return declared_packages

    default_count = 0

    for idx, entry in enumerate(package_dirs):
        prefix = f"packageDirectories[{idx}]"

        if not isinstance(entry, dict):
            issues.append(f"{prefix} must be an object.")
            continue

        # Required: path
        path = entry.get("path")
        if not path:
            issues.append(f"{prefix}: Missing required 'path' field.")
        elif verbose:
            print(f"  [OK] {prefix}.path: '{path}'")

        # Required for package entries: package name
        package_name = entry.get("package")
        if package_name:
            declared_packages.append(package_name)
            if verbose:
                print(f"  [OK] {prefix}.package: '{package_name}'")

            # versionNumber required when package is declared
            version_number = entry.get("versionNumber")
            if not version_number:
                issues.append(
                    f"{prefix} ('{package_name}'): Missing 'versionNumber'. "
                    "Use format 'major.minor.patch.NEXT' (e.g., '1.0.0.NEXT')."
                )
            elif not VERSION_NUMBER_RE.match(str(version_number)):
                issues.append(
                    f"{prefix} ('{package_name}'): 'versionNumber' value '{version_number}' "
                    "is not valid. Use format 'major.minor.patch.NEXT' or "
                    "'major.minor.patch.LATEST' or 'major.minor.patch.N'."
                )
            elif verbose:
                print(f"  [OK] {prefix}.versionNumber: '{version_number}'")

        # Check dependencies array format
        deps = entry.get("dependencies")
        if deps is not None:
            if not isinstance(deps, list):
                issues.append(f"{prefix}: 'dependencies' must be an array.")
            else:
                for dep_idx, dep in enumerate(deps):
                    dep_prefix = f"{prefix}.dependencies[{dep_idx}]"
                    if not isinstance(dep, dict):
                        issues.append(f"{dep_prefix} must be an object.")
                        continue
                    dep_pkg = dep.get("package")
                    dep_ver = dep.get("versionNumber")
                    if not dep_pkg:
                        issues.append(
                            f"{dep_prefix}: Missing 'package' key. "
                            "Must match an alias in 'packageAliases'."
                        )
                    if not dep_ver:
                        issues.append(
                            f"{dep_prefix}: Missing 'versionNumber'. "
                            "Use format like '1.2.0.LATEST' or '1.2.0.3'."
                        )
                    if dep_pkg and dep_ver and verbose:
                        print(
                            f"  [OK] {dep_prefix}: {dep_pkg}@{dep_ver}"
                        )

        # Check default flag
        if entry.get("default"):
            default_count += 1

    if default_count == 0:
        issues.append(
            "No packageDirectory has 'default': true. "
            "Exactly one directory must be marked as default."
        )
    elif default_count > 1:
        issues.append(
            f"Multiple packageDirectories ({default_count}) have 'default': true. "
            "Exactly one directory must be the default."
        )
    elif verbose:
        print(f"  [OK] Exactly one default packageDirectory.")

    return declared_packages


def check_package_aliases(
    data: dict,
    declared_packages: list[str],
    issues: list[str],
    verbose: bool,
) -> None:
    """
    Check packageAliases for required entries and valid ID formats.
    Verifies that every declared package name has a corresponding 0Ho... alias.
    """
    aliases: dict = data.get("packageAliases", {})

    if not isinstance(aliases, dict):
        issues.append("'packageAliases' must be an object.")
        return

    if not aliases and declared_packages:
        issues.append(
            "'packageAliases' is empty but packageDirectories declare packages. "
            "Run 'sf package create' to register each package and capture its 0Ho... ID here."
        )
        return

    # Each declared package name must have a matching 0Ho... entry
    for pkg_name in declared_packages:
        if pkg_name not in aliases:
            issues.append(
                f"packageAliases is missing an entry for package '{pkg_name}'. "
                "Run 'sf package create --name \"{pkg_name}\" ...' and add the returned "
                "0Ho... ID to packageAliases."
            )
        else:
            alias_value = aliases[pkg_name]
            if not isinstance(alias_value, str):
                issues.append(
                    f"packageAliases['{pkg_name}'] must be a string ID, "
                    f"got {type(alias_value).__name__}."
                )
            elif not PACKAGE_ID_RE.match(alias_value):
                issues.append(
                    f"packageAliases['{pkg_name}'] value '{alias_value}' does not look like "
                    "a Package ID (expected 0Ho... with 18 characters). "
                    "Package IDs start with '0Ho'."
                )
            elif verbose:
                print(f"  [OK] packageAliases['{pkg_name}']: {alias_value} (0Ho...)")

    # Check version aliases — entries with @ in the key should have 04t... values
    for alias_key, alias_value in aliases.items():
        if "@" in alias_key:
            if not isinstance(alias_value, str):
                issues.append(
                    f"packageAliases['{alias_key}'] must be a string version ID."
                )
            elif not VERSION_ID_RE.match(alias_value):
                issues.append(
                    f"packageAliases['{alias_key}'] value '{alias_value}' does not look like "
                    "a Package Version ID (expected 04t... with 18 characters). "
                    "Version IDs start with '04t'."
                )
            elif verbose:
                print(
                    f"  [OK] packageAliases['{alias_key}']: {alias_value} (04t...)"
                )


def check_dependency_aliases(
    data: dict, issues: list[str], verbose: bool
) -> None:
    """
    Verify that all dependency package aliases declared in packageDirectories
    are present in packageAliases.
    """
    aliases: dict = data.get("packageAliases", {})
    package_dirs = data.get("packageDirectories", [])

    if not isinstance(package_dirs, list) or not isinstance(aliases, dict):
        return

    for idx, entry in enumerate(package_dirs):
        if not isinstance(entry, dict):
            continue
        deps = entry.get("dependencies", [])
        if not isinstance(deps, list):
            continue
        pkg_name = entry.get("package", f"[{idx}]")
        for dep in deps:
            if not isinstance(dep, dict):
                continue
            dep_pkg = dep.get("package")
            if dep_pkg and dep_pkg not in aliases:
                issues.append(
                    f"Package '{pkg_name}' declares dependency on '{dep_pkg}', "
                    f"but '{dep_pkg}' is not in packageAliases. "
                    "Add the dependency's package ID or version ID to packageAliases."
                )
            elif dep_pkg and dep_pkg in aliases and verbose:
                print(
                    f"  [OK] Dependency alias '{dep_pkg}' resolved in packageAliases."
                )


def check_definition_files(
    data: dict, project_dir: Path, issues: list[str], verbose: bool
) -> None:
    """Check that any definitionFile paths declared in packageDirectories exist."""
    package_dirs = data.get("packageDirectories", [])
    if not isinstance(package_dirs, list):
        return

    for idx, entry in enumerate(package_dirs):
        if not isinstance(entry, dict):
            continue
        def_file = entry.get("definitionFile")
        if def_file:
            def_path = project_dir / def_file
            if not def_path.exists():
                issues.append(
                    f"packageDirectories[{idx}].definitionFile '{def_file}' does not exist "
                    f"at '{def_path}'. "
                    "Create the scratch org definition file or correct the path."
                )
            elif verbose:
                print(
                    f"  [OK] packageDirectories[{idx}].definitionFile exists: '{def_file}'"
                )


def check_package_directories_exist(
    data: dict, project_dir: Path, issues: list[str], verbose: bool
) -> None:
    """Check that declared package source directories exist on disk."""
    package_dirs = data.get("packageDirectories", [])
    if not isinstance(package_dirs, list):
        return

    for idx, entry in enumerate(package_dirs):
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if path:
            full_path = project_dir / path
            if not full_path.exists():
                issues.append(
                    f"packageDirectories[{idx}].path '{path}' does not exist at '{full_path}'. "
                    "Create the directory or correct the path in sfdx-project.json."
                )
            elif verbose:
                print(f"  [OK] packageDirectories[{idx}].path exists: '{path}'")


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()
    verbose = args.verbose

    if verbose:
        print(f"Checking unlocked package configuration in: {project_dir}\n")

    data, issues = load_sfdx_project(project_dir)
    if data is None:
        for issue in issues:
            print(f"ISSUE: {issue}")
        return 1

    # Run all checks
    check_namespace(data, issues, verbose)
    check_source_api_version(data, issues, verbose)
    declared_packages = check_package_directories(data, issues, verbose)
    check_package_aliases(data, declared_packages, issues, verbose)
    check_dependency_aliases(data, issues, verbose)
    check_definition_files(data, project_dir, issues, verbose)
    check_package_directories_exist(data, project_dir, issues, verbose)

    if verbose:
        print()

    if not issues:
        print("No issues found. sfdx-project.json looks well-formed for unlocked package development.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
