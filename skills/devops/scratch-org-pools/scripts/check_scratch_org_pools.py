#!/usr/bin/env python3
"""Checker script for Scratch Org Pools skill.

Scans CI workflow files and CumulusCI configuration for common pool
management issues: missing fallback logic, missing prune steps,
missing cleanup, and pool sizing without limit checks.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_scratch_org_pools.py [--help]
    python3 check_scratch_org_pools.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check scratch org pool configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


def _scan_yaml_files(root: Path) -> list[Path]:
    """Find CI workflow YAML files."""
    yaml_files: list[Path] = []
    for pattern in ("*.yml", "*.yaml"):
        # Check common CI directories
        for ci_dir in (".github/workflows", ".circleci", "bitbucket-pipelines"):
            ci_path = root / ci_dir
            if ci_path.is_dir():
                yaml_files.extend(ci_path.glob(pattern))
        # Also check root for bitbucket-pipelines.yml, Jenkinsfile, etc.
        yaml_files.extend(root.glob(pattern))
    return yaml_files


def _scan_shell_scripts(root: Path) -> list[Path]:
    """Find shell scripts that might contain pool commands."""
    scripts: list[Path] = []
    for pattern in ("**/*.sh", "**/*.bash"):
        scripts.extend(root.glob(pattern))
    return scripts


def check_scratch_org_pools(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Collect all files to scan
    yaml_files = _scan_yaml_files(manifest_dir)
    shell_scripts = _scan_shell_scripts(manifest_dir)
    all_files = yaml_files + shell_scripts

    if not all_files:
        issues.append(
            "No CI workflow files (.yml/.yaml) or shell scripts found. "
            "Cannot verify pool configuration."
        )
        return issues

    pool_get_found = False
    pool_create_found = False
    pool_prune_found = False
    fallback_found = False
    delete_after_use_found = False
    sf_pool_hallucination = False

    for filepath in all_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel_path = filepath.relative_to(manifest_dir) if filepath.is_relative_to(manifest_dir) else filepath

        # Check for hallucinated sf CLI pool commands
        if re.search(r"\bsf\s+org\s+pool\b", content) or re.search(r"\bsfdx\s+force:org:pool\b", content):
            issues.append(
                f"{rel_path}: Uses 'sf org pool' or 'sfdx force:org:pool' which does not exist. "
                f"Use CumulusCI pool commands instead (cci org pool)."
            )
            sf_pool_hallucination = True

        # Track CumulusCI pool usage
        if re.search(r"\bcci\s+org\s+pool\s+get\b", content):
            pool_get_found = True

        if re.search(r"\bcci\s+org\s+pool\s+create\b", content):
            pool_create_found = True

        if re.search(r"\bcci\s+org\s+pool\s+prune\b", content):
            pool_prune_found = True

        # Check for fallback logic near pool get
        if re.search(r"\bcci\s+org\s+pool\s+get\b", content):
            # Look for if/else or || patterns indicating fallback
            if re.search(r"(if\s+cci\s+org\s+pool\s+get|cci\s+org\s+pool\s+get.*\|\||else)", content):
                fallback_found = True

        # Check for org deletion after pool get
        if re.search(r"\bcci\s+org\s+pool\s+get\b", content):
            if re.search(r"(scratch_delete|org\s+delete\s+scratch|if:\s*always)", content):
                delete_after_use_found = True

    # Report findings
    if sf_pool_hallucination:
        # Already reported per-file above
        pass

    if pool_get_found and not fallback_found:
        issues.append(
            "CI uses 'cci org pool get' but no fallback logic detected. "
            "If the pool is empty, the job will fail. Add an if/else or || fallback "
            "to create an org on demand when the pool is exhausted."
        )

    if pool_create_found and not pool_prune_found:
        issues.append(
            "Pool replenishment found ('cci org pool create') but no 'cci org pool prune' step. "
            "Always prune expired orgs before replenishing to avoid stale keychain entries."
        )

    if pool_get_found and not delete_after_use_found:
        issues.append(
            "Pool org is claimed but no deletion step found after use. "
            "Pooled orgs are single-use — delete them after the CI job completes "
            "to free active org slots."
        )

    if pool_get_found and not pool_create_found:
        issues.append(
            "CI claims from pool ('cci org pool get') but no replenishment step found. "
            "Ensure a scheduled job runs 'cci org pool create' to keep the pool filled."
        )

    # Check for cumulusci.yml
    cci_config = manifest_dir / "cumulusci.yml"
    if pool_get_found and not cci_config.exists():
        issues.append(
            "CumulusCI pool commands found but no cumulusci.yml in project root. "
            "CumulusCI requires a cumulusci.yml configuration file."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_scratch_org_pools(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
