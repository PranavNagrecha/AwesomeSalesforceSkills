#!/usr/bin/env python3
"""Checker script for Automated Regression Testing skill.

Validates project structure and configuration for Salesforce UI regression
testing readiness. Checks for page object architecture, Shadow DOM handling,
CI pipeline integration, and common anti-patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_automated_regression_testing.py --project-dir path/to/test/project
    python3 check_automated_regression_testing.py --project-dir . --strict
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
        description="Check automated regression testing project for common issues.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the test automation project (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings in addition to errors.",
    )
    return parser.parse_args()


def find_files(root: Path, extensions: set[str], max_depth: int = 10) -> list[Path]:
    """Recursively find files with given extensions up to max_depth."""
    results: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        depth = len(Path(dirpath).relative_to(root).parts)
        if depth > max_depth:
            dirnames.clear()
            continue
        # Skip node_modules, target, .git
        dirnames[:] = [d for d in dirnames if d not in {"node_modules", "target", ".git", "dist", "build"}]
        for f in filenames:
            if any(f.endswith(ext) for ext in extensions):
                results.append(Path(dirpath) / f)
    return results


def check_shadow_dom_anti_patterns(project_dir: Path) -> list[str]:
    """Detect raw Shadow DOM traversal anti-patterns in test files."""
    issues: list[str] = []
    test_files = find_files(project_dir, {".java", ".js", ".ts", ".py"})

    shadow_root_inline = re.compile(
        r"""(executeScript|evaluate|evaluateHandle)\s*\(\s*["'].*shadowRoot""",
        re.IGNORECASE,
    )
    thread_sleep = re.compile(r"(Thread\.sleep|time\.sleep|setTimeout)\s*\(")
    hard_coded_sf_url = re.compile(
        r"""['"]https?://[a-zA-Z0-9-]+\.(sandbox\.)?my\.salesforce\.com"""
    )

    for filepath in test_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = filepath.relative_to(project_dir)

        # Check for inline shadowRoot traversal (should use page objects)
        for match in shadow_root_inline.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            issues.append(
                f"WARNING: Inline shadowRoot traversal in {rel}:{line_num} — "
                f"use UTAM page objects or a page object layer instead."
            )

        # Check for Thread.sleep / time.sleep (should use explicit waits)
        for match in thread_sleep.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            issues.append(
                f"WARNING: Fixed sleep in {rel}:{line_num} — "
                f"use explicit waits (WebDriverWait / waitFor) instead of fixed delays."
            )

        # Check for hard-coded Salesforce URLs
        for match in hard_coded_sf_url.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            issues.append(
                f"WARNING: Hard-coded Salesforce URL in {rel}:{line_num} — "
                f"resolve URLs dynamically via 'sf org display' at runtime."
            )

    return issues


def check_page_object_architecture(project_dir: Path) -> list[str]:
    """Check for presence of page object files."""
    issues: list[str] = []

    # Look for UTAM JSON page objects
    utam_files = find_files(project_dir, {".utam.json"})

    # Look for Java/JS/TS page object files (heuristic: filename contains PageObject or Page)
    page_object_pattern = re.compile(r"(page.?object|page.?model|\.page\.)", re.IGNORECASE)
    all_source = find_files(project_dir, {".java", ".js", ".ts"})
    page_object_files = [f for f in all_source if page_object_pattern.search(f.name)]

    if not utam_files and not page_object_files:
        issues.append(
            "ERROR: No page object files found (no .utam.json files and no files "
            "matching *PageObject* or *Page* naming convention). Regression tests "
            "require a page object layer for maintainability."
        )

    return issues


def check_ci_pipeline_integration(project_dir: Path) -> list[str]:
    """Check for CI pipeline configuration with test execution."""
    issues: list[str] = []

    ci_files: list[Path] = []
    # GitHub Actions
    gh_actions = project_dir / ".github" / "workflows"
    if gh_actions.exists():
        ci_files.extend(find_files(gh_actions, {".yml", ".yaml"}))
    # GitLab CI
    gitlab_ci = project_dir / ".gitlab-ci.yml"
    if gitlab_ci.exists():
        ci_files.append(gitlab_ci)
    # Jenkins
    jenkinsfile = project_dir / "Jenkinsfile"
    if jenkinsfile.exists():
        ci_files.append(jenkinsfile)
    # Azure DevOps
    azure_pipelines = project_dir / "azure-pipelines.yml"
    if azure_pipelines.exists():
        ci_files.append(azure_pipelines)

    if not ci_files:
        issues.append(
            "WARNING: No CI pipeline configuration found (.github/workflows/, "
            ".gitlab-ci.yml, Jenkinsfile, azure-pipelines.yml). Regression tests "
            "should be integrated into CI for automated execution."
        )
        return issues

    # Check if any CI file references test execution
    test_keywords = re.compile(
        r"(wdio|webdriver|selenium|playwright|provar|utam|regression|junit|test-results)",
        re.IGNORECASE,
    )
    has_test_step = False
    for ci_file in ci_files:
        try:
            content = ci_file.read_text(encoding="utf-8", errors="replace")
            if test_keywords.search(content):
                has_test_step = True
                break
        except OSError:
            continue

    if not has_test_step:
        issues.append(
            "WARNING: CI pipeline files found but none reference regression test "
            "execution (searched for wdio, webdriver, selenium, playwright, provar, "
            "utam, junit keywords). Add a regression test stage to your pipeline."
        )

    return issues


def check_hard_coded_record_ids(project_dir: Path) -> list[str]:
    """Detect hard-coded Salesforce record IDs in test files."""
    issues: list[str] = []
    test_files = find_files(project_dir, {".java", ".js", ".ts", ".py"})

    # Match 15 or 18 character Salesforce IDs with common prefixes
    sf_id_pattern = re.compile(
        r"""['"/](001|003|005|006|00Q|00D|a[0-9A-Za-z]{2})[A-Za-z0-9]{12,15}['"/]"""
    )

    for filepath in test_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = filepath.relative_to(project_dir)
        for match in sf_id_pattern.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            issues.append(
                f"WARNING: Possible hard-coded Salesforce record ID in {rel}:{line_num} "
                f"({match.group()}) — test data should be created dynamically."
            )

    return issues


def check_xpath_in_lightning_tests(project_dir: Path) -> list[str]:
    """Detect XPath usage that will fail across Shadow DOM boundaries."""
    issues: list[str] = []
    test_files = find_files(project_dir, {".java", ".js", ".ts"})

    xpath_pattern = re.compile(r"By\.xpath\s*\(")
    lightning_xpath = re.compile(
        r"""By\.xpath\s*\([^)]*lightning-|By\.xpath\s*\([^)]*one-record"""
    )

    for filepath in test_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = filepath.relative_to(project_dir)
        for match in lightning_xpath.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            issues.append(
                f"ERROR: XPath targeting Lightning component in {rel}:{line_num} — "
                f"XPath cannot cross Shadow DOM boundaries. Use UTAM page objects "
                f"or Selenium 4 getShadowRoot() instead."
            )

    return issues


def check_automated_regression_testing(project_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issues."""
    issues: list[str] = []

    if not project_dir.exists():
        issues.append(f"ERROR: Project directory not found: {project_dir}")
        return issues

    issues.extend(check_shadow_dom_anti_patterns(project_dir))
    issues.extend(check_page_object_architecture(project_dir))
    issues.extend(check_ci_pipeline_integration(project_dir))
    issues.extend(check_hard_coded_record_ids(project_dir))
    issues.extend(check_xpath_in_lightning_tests(project_dir))

    return issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()
    issues = check_automated_regression_testing(project_dir)

    if not issues:
        print("No issues found. Regression test project looks good.")
        return 0

    errors = [i for i in issues if i.startswith("ERROR:")]
    warnings = [i for i in issues if i.startswith("WARNING:")]

    for issue in issues:
        print(f"  {issue}")

    print(f"\nSummary: {len(errors)} error(s), {len(warnings)} warning(s)")

    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
