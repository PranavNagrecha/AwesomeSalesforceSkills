#!/usr/bin/env python3
"""Checker script for Continuous Integration Testing skill.

Scans a Salesforce project directory for CI/CD configuration files and validates
that test execution, coverage enforcement, and result reporting are configured
correctly.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_continuous_integration_testing.py [--help]
    python3 check_continuous_integration_testing.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CI testing configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


def find_ci_files(root: Path) -> list[Path]:
    """Find CI/CD configuration files in the project."""
    ci_patterns = [
        ".github/workflows/*.yml",
        ".github/workflows/*.yaml",
        ".gitlab-ci.yml",
        "Jenkinsfile",
        "azure-pipelines.yml",
        "bitbucket-pipelines.yml",
        ".circleci/config.yml",
    ]
    found: list[Path] = []
    for pattern in ci_patterns:
        found.extend(root.glob(pattern))
    return found


def check_legacy_sfdx_commands(content: str, filepath: str) -> list[str]:
    """Check for deprecated sfdx force:* command syntax."""
    issues: list[str] = []
    legacy_pattern = re.compile(r"sfdx\s+force:", re.IGNORECASE)
    for i, line in enumerate(content.splitlines(), 1):
        if legacy_pattern.search(line):
            issues.append(
                f"{filepath}:{i} — uses legacy 'sfdx force:' syntax. "
                f"Migrate to 'sf' CLI v2 commands."
            )
    return issues


def check_test_level_specified(content: str, filepath: str) -> list[str]:
    """Check that deploy/test commands specify an explicit test level."""
    issues: list[str] = []
    deploy_pattern = re.compile(
        r"sf\s+project\s+deploy\s+(start|validate)", re.IGNORECASE
    )
    test_level_pattern = re.compile(r"--test-level", re.IGNORECASE)

    for i, line in enumerate(content.splitlines(), 1):
        if deploy_pattern.search(line) and not test_level_pattern.search(line):
            # Check if --test-level appears on a continuation line
            # (multiline commands with backslash)
            context_start = max(0, i - 1)
            context_end = min(len(content.splitlines()), i + 5)
            context_block = "\n".join(content.splitlines()[context_start:context_end])
            if not test_level_pattern.search(context_block):
                issues.append(
                    f"{filepath}:{i} — 'sf project deploy' without explicit "
                    f"--test-level. Relying on default behavior is risky."
                )
    return issues


def check_wait_flag(content: str, filepath: str) -> list[str]:
    """Check that async test commands include --wait."""
    issues: list[str] = []
    test_run_pattern = re.compile(r"sf\s+apex\s+run\s+test", re.IGNORECASE)
    wait_pattern = re.compile(r"--wait", re.IGNORECASE)
    sync_pattern = re.compile(r"--synchronous", re.IGNORECASE)

    for i, line in enumerate(content.splitlines(), 1):
        if test_run_pattern.search(line):
            context_start = max(0, i - 1)
            context_end = min(len(content.splitlines()), i + 5)
            context_block = "\n".join(content.splitlines()[context_start:context_end])
            if not wait_pattern.search(context_block) and not sync_pattern.search(
                context_block
            ):
                issues.append(
                    f"{filepath}:{i} — 'sf apex run test' without --wait or "
                    f"--synchronous. Tests will run async and the pipeline "
                    f"will not wait for results."
                )
    return issues


def check_coverage_enforcement(content: str, filepath: str) -> list[str]:
    """Check for coverage threshold enforcement beyond just --code-coverage."""
    issues: list[str] = []
    has_code_coverage_flag = bool(re.search(r"--code-coverage", content))
    has_coverage_check = bool(
        re.search(
            r"(coverage|threshold|min[_-]?coverage|check[_-]?coverage)",
            content,
            re.IGNORECASE,
        )
    )

    if has_code_coverage_flag and not has_coverage_check:
        issues.append(
            f"{filepath} — uses --code-coverage flag but has no visible "
            f"coverage threshold enforcement. The flag collects coverage "
            f"but does not enforce a minimum."
        )
    return issues


def check_hardcoded_credentials(content: str, filepath: str) -> list[str]:
    """Check for hardcoded credentials in CI configuration."""
    issues: list[str] = []
    credential_patterns = [
        (r"password\s*[:=]\s*['\"][^'\"]+['\"]", "hardcoded password"),
        (r"security[_-]?token\s*[:=]\s*['\"][^'\"]+['\"]", "hardcoded security token"),
        (r"client[_-]?secret\s*[:=]\s*['\"][A-Za-z0-9]+", "hardcoded client secret"),
        (r"consumer[_-]?key\s*[:=]\s*['\"][A-Za-z0-9]+", "hardcoded consumer key"),
    ]
    for pattern, desc in credential_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                f"{filepath}:{line_num} — possible {desc} found. "
                f"Use CI platform secrets instead."
            )
    return issues


def check_run_all_tests_in_org(content: str, filepath: str) -> list[str]:
    """Warn if RunAllTestsInOrg is used as the default test level."""
    issues: list[str] = []
    if re.search(r"RunAllTestsInOrg", content):
        issues.append(
            f"{filepath} — uses RunAllTestsInOrg. This runs managed package "
            f"tests that may cause flaky failures. Use RunLocalTests unless "
            f"you have an explicit reason for managed package test execution."
        )
    return issues


def check_junit_output(content: str, filepath: str) -> list[str]:
    """Check that test results are captured in a machine-readable format."""
    issues: list[str] = []
    has_test_run = bool(re.search(r"sf\s+apex\s+run\s+test", content))
    has_result_format = bool(re.search(r"--result-format", content))

    if has_test_run and not has_result_format:
        issues.append(
            f"{filepath} — runs Apex tests but does not specify "
            f"--result-format for machine-readable output. Add "
            f"--result-format junit for CI dashboard integration."
        )
    return issues


def check_continuous_integration_testing(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Project directory not found: {manifest_dir}")
        return issues

    ci_files = find_ci_files(manifest_dir)

    if not ci_files:
        issues.append(
            "No CI/CD configuration files found. Looked for GitHub Actions, "
            "GitLab CI, Jenkinsfile, Azure Pipelines, Bitbucket Pipelines, "
            "and CircleCI configs."
        )
        return issues

    for ci_file in ci_files:
        try:
            content = ci_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            issues.append(f"Could not read {ci_file}: {e}")
            continue

        filepath = str(ci_file.relative_to(manifest_dir))

        issues.extend(check_legacy_sfdx_commands(content, filepath))
        issues.extend(check_test_level_specified(content, filepath))
        issues.extend(check_wait_flag(content, filepath))
        issues.extend(check_coverage_enforcement(content, filepath))
        issues.extend(check_hardcoded_credentials(content, filepath))
        issues.extend(check_run_all_tests_in_org(content, filepath))
        issues.extend(check_junit_output(content, filepath))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_continuous_integration_testing(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
