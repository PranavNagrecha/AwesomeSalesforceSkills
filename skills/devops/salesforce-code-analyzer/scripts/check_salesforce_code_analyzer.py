#!/usr/bin/env python3
"""Checker script for Salesforce Code Analyzer skill.

Validates that a Salesforce DX project is correctly configured for
Salesforce Code Analyzer v5 usage in CI and AppExchange contexts.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_salesforce_code_analyzer.py [--help]
    python3 check_salesforce_code_analyzer.py --manifest-dir path/to/project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce DX project for Salesforce Code Analyzer v5 "
            "configuration issues and common anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


def check_legacy_sfdx_scanner_commands(manifest_dir: Path) -> list[str]:
    """Detect v4 legacy 'sfdx scanner:run' commands in CI workflow files and scripts."""
    issues: list[str] = []
    legacy_pattern = re.compile(r"sfdx\s+scanner[:\s]", re.IGNORECASE)

    # Check GitHub Actions workflows
    github_dir = manifest_dir / ".github" / "workflows"
    if github_dir.exists():
        for yml_file in github_dir.glob("*.yml"):
            try:
                content = yml_file.read_text(encoding="utf-8")
                if legacy_pattern.search(content):
                    issues.append(
                        f"[v4-legacy] {yml_file.relative_to(manifest_dir)} contains "
                        f"'sfdx scanner:run' (v4 command, retired Aug 2025). "
                        f"Replace with 'sf code-analyzer run'."
                    )
            except OSError:
                pass

    # Check shell scripts and Makefiles at project root
    for script_glob in ("*.sh", "Makefile", "Jenkinsfile", "*.groovy"):
        for script_file in manifest_dir.glob(script_glob):
            try:
                content = script_file.read_text(encoding="utf-8")
                if legacy_pattern.search(content):
                    issues.append(
                        f"[v4-legacy] {script_file.name} contains 'sfdx scanner' "
                        f"(v4 syntax). Replace with 'sf code-analyzer run'."
                    )
            except OSError:
                pass

    return issues


def check_code_analyzer_yml(manifest_dir: Path) -> list[str]:
    """Check for presence and basic validity of code-analyzer.yml config file."""
    issues: list[str] = []
    config_file = manifest_dir / "code-analyzer.yml"

    if not config_file.exists():
        issues.append(
            "[config-missing] No code-analyzer.yml found at project root. "
            "Create this file to enforce consistent scan settings across "
            "developers and CI. Without it, every invocation depends on "
            "manually-specified CLI flags."
        )
        return issues

    try:
        content = config_file.read_text(encoding="utf-8")
    except OSError:
        issues.append(f"[config-unreadable] Cannot read {config_file}.")
        return issues

    # Warn if node_modules is not excluded
    if "node_modules" not in content:
        issues.append(
            "[config-exclusion] code-analyzer.yml does not appear to exclude "
            "'node_modules'. Add it under 'global.exclude' to prevent RetireJS "
            "from scanning development dependencies that are not deployed."
        )

    # Warn if graph-engine is enabled by default (performance concern)
    if re.search(r"graph-engine\s*:\s*\n\s+enabled\s*:\s*true", content):
        issues.append(
            "[config-graph-engine] code-analyzer.yml enables graph-engine by "
            "default. Graph Engine is memory-intensive and slow on large codebases. "
            "Consider enabling it only in dedicated security pipeline stages."
        )

    return issues


def check_suppress_warnings_patterns(manifest_dir: Path) -> list[str]:
    """Detect overly-broad @SuppressWarnings('PMD') without rule names in Apex."""
    issues: list[str] = []
    # Match @SuppressWarnings('PMD') or @SuppressWarnings("PMD") without a dot
    blanket_pattern = re.compile(
        r"@SuppressWarnings\s*\(\s*['\"]PMD['\"]\s*\)",
        re.IGNORECASE,
    )

    apex_dirs = [
        manifest_dir / "force-app" / "main" / "default" / "classes",
        manifest_dir / "force-app" / "main" / "default" / "triggers",
    ]

    for apex_dir in apex_dirs:
        if not apex_dir.exists():
            continue
        for apex_file in apex_dir.rglob("*.cls"):
            try:
                content = apex_file.read_text(encoding="utf-8")
                matches = blanket_pattern.findall(content)
                if matches:
                    issues.append(
                        f"[blanket-suppress] {apex_file.relative_to(manifest_dir)} "
                        f"uses @SuppressWarnings('PMD') without a specific rule name "
                        f"({len(matches)} occurrence(s)). Replace with the specific "
                        f"rule name, e.g. @SuppressWarnings('PMD.ApexCRUDViolation'), "
                        f"and add a justification comment."
                    )
            except OSError:
                pass

    return issues


def check_ci_severity_threshold(manifest_dir: Path) -> list[str]:
    """Warn if GitHub Actions workflows run Code Analyzer without --severity-threshold."""
    issues: list[str] = []
    github_dir = manifest_dir / ".github" / "workflows"

    if not github_dir.exists():
        return issues

    code_analyzer_pattern = re.compile(r"sf\s+code-analyzer\s+run", re.IGNORECASE)
    threshold_pattern = re.compile(r"--severity-threshold", re.IGNORECASE)

    for yml_file in github_dir.glob("*.yml"):
        try:
            content = yml_file.read_text(encoding="utf-8")
            if code_analyzer_pattern.search(content) and not threshold_pattern.search(content):
                issues.append(
                    f"[no-threshold] {yml_file.relative_to(manifest_dir)} runs "
                    f"'sf code-analyzer run' without '--severity-threshold'. "
                    f"Without this flag the command always exits 0 and never "
                    f"fails the build. Add '--severity-threshold 2' for a "
                    f"Critical/High gate."
                )
        except OSError:
            pass

    return issues


def check_salesforce_code_analyzer(manifest_dir: Path) -> list[str]:
    """Run all checks and return a consolidated list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_legacy_sfdx_scanner_commands(manifest_dir))
    issues.extend(check_code_analyzer_yml(manifest_dir))
    issues.extend(check_suppress_warnings_patterns(manifest_dir))
    issues.extend(check_ci_severity_threshold(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_salesforce_code_analyzer(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
