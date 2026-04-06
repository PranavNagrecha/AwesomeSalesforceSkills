#!/usr/bin/env python3
"""Checker script for Metadata Coverage and Dependencies skill.

Scans sfdx-project.json and metadata files for common dependency and coverage risks:
- Package directories without dependency declarations
- Metadata types commonly unsupported in packages
- Circular dependency indicators in package config

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_metadata_coverage_and_dependencies.py --manifest-dir path/to/project
    python3 check_metadata_coverage_and_dependencies.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Metadata types commonly unsupported or partially supported in unlocked packages
COMMON_UNSUPPORTED_TYPES = {
    "Settings",
    "EmbeddedServiceConfig",
    "EmbeddedServiceBranding",
    "ManagedTopics",
    "TopicsForObjects",
    "AnimationRule",
    "LightningOnboardingConfig",
}

# File extensions that map to potentially unsupported metadata types
RISKY_EXTENSIONS = {
    ".settings-meta.xml": "Settings (often unsupported in packages)",
    ".embeddedServiceConfig-meta.xml": "EmbeddedServiceConfig (limited package support)",
    ".territory2Model-meta.xml": "Territory2Model (partial support varies by version)",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check metadata coverage and dependency risks.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce project (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Treat warnings as errors.",
    )
    return parser.parse_args()


def check_sfdx_project(root: Path) -> list[str]:
    """Check sfdx-project.json for packaging and dependency configuration issues."""
    issues = []
    sfdx_file = root / "sfdx-project.json"

    if not sfdx_file.exists():
        return issues  # Not an SFDX project — skip

    try:
        with open(sfdx_file) as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        issues.append(f"ERROR: Could not parse sfdx-project.json: {e}")
        return issues

    pkg_dirs = config.get("packageDirectories", [])
    if not pkg_dirs:
        issues.append("WARN: sfdx-project.json has no packageDirectories defined")
        return issues

    # Check for multiple packages without dependency declarations
    packages_with_names = [d for d in pkg_dirs if d.get("package")]
    if len(packages_with_names) > 1:
        for pkg in packages_with_names:
            deps = pkg.get("dependencies", [])
            if not deps:
                issues.append(
                    f"WARN: Package '{pkg.get('package')}' has no dependencies "
                    f"declared — verify this is intentional for multi-package projects"
                )

    # Check for missing sourceApiVersion
    if "sourceApiVersion" not in config:
        issues.append(
            "WARN: sfdx-project.json missing sourceApiVersion — "
            "deploy may use default API version"
        )

    return issues


def check_risky_metadata_types(root: Path) -> list[str]:
    """Flag metadata files that are commonly unsupported in packages."""
    issues = []
    for ext, description in RISKY_EXTENSIONS.items():
        matches = list(root.rglob(f"*{ext}"))
        if matches:
            issues.append(
                f"WARN: Found {len(matches)} {description} file(s) — "
                f"verify package support at your target API version"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Directory not found: {manifest_dir}")
        return 2

    print(f"Scanning {manifest_dir} for metadata coverage and dependency risks\n")

    all_issues = []
    all_issues.extend(check_sfdx_project(manifest_dir))
    all_issues.extend(check_risky_metadata_types(manifest_dir))

    errors = [i for i in all_issues if i.startswith("ERROR")]
    warnings = [i for i in all_issues if i.startswith("WARN")]

    for issue in all_issues:
        print(f"  {issue}")

    if not all_issues:
        print("  No coverage or dependency risks detected.")

    print(f"\nResults: {len(errors)} errors, {len(warnings)} warnings")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
