#!/usr/bin/env python3
"""Checker script for Multi-Package Development skill.

Validates sfdx-project.json for multi-package configuration correctness:
- Detects circular dependencies in the package DAG
- Validates that dependency aliases resolve in packageAliases
- Checks that exactly one packageDirectories entry is marked default
- Detects duplicate metadata paths across package directories
- Computes and reports topological install order

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_multi_package_development.py [--help]
    python3 check_multi_package_development.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check multi-package development configuration in sfdx-project.json.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing sfdx-project.json (default: current directory).",
    )
    return parser.parse_args()


def load_project_json(manifest_dir: Path) -> dict | None:
    """Load and parse sfdx-project.json."""
    project_file = manifest_dir / "sfdx-project.json"
    if not project_file.exists():
        return None
    with open(project_file, "r", encoding="utf-8") as f:
        return json.load(f)


def check_default_directory(pkg_dirs: list[dict]) -> list[str]:
    """Ensure exactly one packageDirectories entry has default: true."""
    issues: list[str] = []
    defaults = [d for d in pkg_dirs if d.get("default") is True]
    if len(defaults) == 0:
        issues.append(
            "No packageDirectories entry has 'default': true. "
            "Exactly one entry should be marked as default."
        )
    elif len(defaults) > 1:
        paths = [d.get("path", "unknown") for d in defaults]
        issues.append(
            f"Multiple packageDirectories entries have 'default': true: {paths}. "
            "Only one entry should be default."
        )
    return issues


def check_dependency_aliases(
    pkg_dirs: list[dict], aliases: dict[str, str]
) -> list[str]:
    """Check that every dependency alias resolves in packageAliases."""
    issues: list[str] = []
    for pkg_dir in pkg_dirs:
        pkg_name = pkg_dir.get("package", pkg_dir.get("path", "unknown"))
        for dep in pkg_dir.get("dependencies", []):
            dep_alias = dep.get("package", "")
            if dep_alias and dep_alias not in aliases:
                issues.append(
                    f"Package '{pkg_name}' depends on '{dep_alias}', "
                    f"but '{dep_alias}' is not in packageAliases."
                )
    return issues


def check_circular_dependencies(pkg_dirs: list[dict]) -> tuple[list[str], list[str]]:
    """Detect circular dependencies and compute topological order.

    Returns (issues, topological_order).
    """
    issues: list[str] = []

    # Build adjacency list: package -> list of packages it depends on
    pkg_names: set[str] = set()
    graph: dict[str, list[str]] = {}
    in_degree: dict[str, int] = {}

    for pkg_dir in pkg_dirs:
        pkg_name = pkg_dir.get("package")
        if not pkg_name:
            continue
        pkg_names.add(pkg_name)
        deps = [d.get("package", "") for d in pkg_dir.get("dependencies", [])]
        # Filter to deps that are also packages in this project
        # (external dependencies won't be in pkg_names)
        graph[pkg_name] = deps
        if pkg_name not in in_degree:
            in_degree[pkg_name] = 0

    # Initialize in-degrees for all known packages
    for pkg_name in pkg_names:
        if pkg_name not in in_degree:
            in_degree[pkg_name] = 0

    # Only count in-degrees for internal dependencies
    for pkg_name, deps in graph.items():
        for dep in deps:
            if dep in pkg_names:
                in_degree[dep] = in_degree.get(dep, 0)
                # Note: in_degree tracks how many packages depend ON this package
                # For topological sort, we need: how many deps does this package have
                # that are internal

    # Rebuild for Kahn's algorithm: edge from dependency -> dependent
    # in_degree[X] = number of internal packages X depends on
    adj: dict[str, list[str]] = {name: [] for name in pkg_names}
    kahn_in: dict[str, int] = {name: 0 for name in pkg_names}

    for pkg_name, deps in graph.items():
        for dep in deps:
            if dep in pkg_names:
                adj[dep].append(pkg_name)  # dep -> pkg_name (dep must come first)
                kahn_in[pkg_name] += 1

    # Kahn's algorithm
    queue: deque[str] = deque()
    for name in pkg_names:
        if kahn_in[name] == 0:
            queue.append(name)

    topo_order: list[str] = []
    while queue:
        node = queue.popleft()
        topo_order.append(node)
        for neighbor in adj.get(node, []):
            kahn_in[neighbor] -= 1
            if kahn_in[neighbor] == 0:
                queue.append(neighbor)

    if len(topo_order) != len(pkg_names):
        cycle_packages = pkg_names - set(topo_order)
        issues.append(
            f"Circular dependency detected involving packages: {sorted(cycle_packages)}. "
            "Salesforce DX requires an acyclic dependency graph."
        )

    return issues, topo_order


def check_duplicate_paths(pkg_dirs: list[dict]) -> list[str]:
    """Check for duplicate source paths across package directories."""
    issues: list[str] = []
    seen_paths: dict[str, str] = {}
    for pkg_dir in pkg_dirs:
        path = pkg_dir.get("path", "")
        pkg_name = pkg_dir.get("package", path)
        if path in seen_paths:
            issues.append(
                f"Duplicate path '{path}' used by both '{seen_paths[path]}' "
                f"and '{pkg_name}'. Each package must have a unique source directory."
            )
        else:
            seen_paths[path] = pkg_name
    return issues


def check_multi_package_development(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the project configuration."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    project = load_project_json(manifest_dir)
    if project is None:
        issues.append(
            f"sfdx-project.json not found in {manifest_dir}. "
            "Cannot validate multi-package configuration."
        )
        return issues

    pkg_dirs = project.get("packageDirectories", [])
    aliases = project.get("packageAliases", {})

    # Only relevant if there are multiple packages
    packaged_dirs = [d for d in pkg_dirs if d.get("package")]
    if len(packaged_dirs) < 2:
        issues.append(
            f"Only {len(packaged_dirs)} package(s) found in packageDirectories. "
            "Multi-package checks require 2+ packages."
        )
        return issues

    issues.extend(check_default_directory(pkg_dirs))
    issues.extend(check_dependency_aliases(pkg_dirs, aliases))

    cycle_issues, topo_order = check_circular_dependencies(pkg_dirs)
    issues.extend(cycle_issues)

    issues.extend(check_duplicate_paths(pkg_dirs))

    if not cycle_issues and topo_order:
        print(f"INFO: Topological install order: {' -> '.join(topo_order)}")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_multi_package_development(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
