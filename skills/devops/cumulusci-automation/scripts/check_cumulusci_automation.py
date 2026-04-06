#!/usr/bin/env python3
"""Checker script for CumulusCI Automation skill.

Validates a project's cumulusci.yml for common configuration mistakes:
  - Missing or invalid class_path in task declarations
  - Options blocks placed at the flow level instead of inside steps
  - Sources pinned to 'latest' instead of a specific tag
  - JWT-unsafe auth patterns referenced in CI YAML files
  - Robot Framework suite paths that do not exist

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cumulusci_automation.py [--project-dir path/to/project]
    python3 check_cumulusci_automation.py --project-dir .
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CumulusCI automation configuration for common issues.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce/CumulusCI project (default: current directory).",
    )
    return parser.parse_args()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def check_cumulusci_yml(project_dir: Path) -> list[str]:
    """Validate cumulusci.yml for common authoring mistakes."""
    issues: list[str] = []
    cci_yml = project_dir / "cumulusci.yml"

    if not cci_yml.exists():
        issues.append(
            "cumulusci.yml not found in project directory. "
            "CumulusCI requires a cumulusci.yml at the project root."
        )
        return issues

    content = _read_text(cci_yml)
    lines = content.splitlines()

    # Check 1: class_path values must be fully qualified (contain at least one dot)
    class_path_pattern = re.compile(r"^\s+class_path:\s+(\S+)")
    for i, line in enumerate(lines, start=1):
        m = class_path_pattern.match(line)
        if m:
            value = m.group(1).strip('"\'')
            if "." not in value:
                issues.append(
                    f"cumulusci.yml line {i}: class_path '{value}' does not look like a "
                    "fully qualified Python dotted path. "
                    "Built-in tasks start with 'cumulusci.tasks.*'. "
                    "Short names like 'Deploy' are not valid."
                )

    # Check 2: Options block at flow level (4-space indent inside flows section)
    in_flows_section = False

    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if stripped.startswith("flows:") and indent == 0:
            in_flows_section = True
            continue
        if stripped and indent == 0 and not stripped.startswith("flows:"):
            in_flows_section = False

        if in_flows_section and stripped.startswith("options:") and indent == 4:
            issues.append(
                f"cumulusci.yml line {i}: 'options:' appears at the flow level (4-space indent "
                "inside the flows: section). Flow-level options blocks are not valid for overriding "
                "task options. Options must be nested inside individual step declarations: "
                "steps.<n>.options.<key>."
            )

    # Check 3: sources using 'release: latest' or mutable branch references
    release_latest = re.compile(r"^\s+release:\s+latest\s*$")
    branch_main = re.compile(r"^\s+branch:\s+(main|master|develop)\s*$")
    in_sources_section = False

    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if stripped.startswith("sources:") and indent == 0:
            in_sources_section = True
            continue
        if stripped and indent == 0 and not stripped.startswith("sources:"):
            in_sources_section = False

        if in_sources_section:
            if release_latest.match(line):
                issues.append(
                    f"cumulusci.yml line {i}: sources entry uses 'release: latest'. "
                    "This pulls the newest release on every cold run, which can cause "
                    "non-reproducible CI builds and GitHub API rate limit errors on parallel jobs. "
                    "Pin to a specific tag: 'tag: v1.2.3'."
                )
            if branch_main.match(line):
                issues.append(
                    f"cumulusci.yml line {i}: sources entry uses a mutable branch reference "
                    "(main/master/develop). Branch references are not reproducible. "
                    "Use a pinned 'tag:' for production CI pipelines."
                )

    return issues


def check_ci_files(project_dir: Path) -> list[str]:
    """Check CI YAML files for unsafe authentication patterns."""
    issues: list[str] = []

    ci_yaml_dirs = [
        project_dir / ".github" / "workflows",
        project_dir / ".circleci",
        project_dir / ".bitbucket",
    ]
    ci_files: list[Path] = []
    for ci_dir in ci_yaml_dirs:
        if ci_dir.is_dir():
            ci_files.extend(ci_dir.glob("*.yml"))
            ci_files.extend(ci_dir.glob("*.yaml"))
    for name in ["Jenkinsfile", ".travis.yml", "circle.yml"]:
        p = project_dir / name
        if p.exists():
            ci_files.append(p)

    interactive_auth = re.compile(
        r"(cci\s+org\s+connect|sf\s+org\s+login\s+web|sfdx\s+auth:web:login)"
    )
    sfdx_url_auth = re.compile(r"sf\s+org\s+login\s+sfdx-url")
    pool_sf_cmd = re.compile(r"sf\s+org\s+pool|sfdx\s+force:org:pool")

    for ci_file in ci_files:
        content = _read_text(ci_file)
        if not content:
            continue
        try:
            rel = ci_file.relative_to(project_dir)
        except ValueError:
            rel = ci_file

        for i, line in enumerate(content.splitlines(), start=1):
            if interactive_auth.search(line):
                issues.append(
                    f"{rel} line {i}: Interactive authentication command detected "
                    f"('{line.strip()}'). "
                    "Interactive auth requires a browser and cannot run in headless CI. "
                    "Use JWT authentication: sf org login jwt --client-id ... --jwt-key-file ..."
                )
            if sfdx_url_auth.search(line):
                issues.append(
                    f"{rel} line {i}: SFDX auth URL authentication detected. "
                    "Auth URLs embed refresh tokens tied to user sessions and can expire silently. "
                    "For production orgs and Dev Hubs, use JWT-based auth with a Connected App."
                )
            if pool_sf_cmd.search(line):
                issues.append(
                    f"{rel} line {i}: 'sf org pool' or 'sfdx force:org:pool' command detected. "
                    "These commands do not exist in the Salesforce CLI. "
                    "Use CumulusCI pool commands: cci org pool create/get/list/prune."
                )

    return issues


def check_robot_config(project_dir: Path) -> list[str]:
    """Check Robot Framework test paths referenced in cumulusci.yml actually exist."""
    issues: list[str] = []
    cci_yml = project_dir / "cumulusci.yml"
    if not cci_yml.exists():
        return issues

    content = _read_text(cci_yml)
    suites_pattern = re.compile(r"^\s+suites:\s+(.+)$", re.MULTILINE)
    for m in suites_pattern.finditer(content):
        suite_path_str = m.group(1).strip().strip('"\'')
        suite_path = project_dir / suite_path_str
        if not suite_path.exists():
            issues.append(
                f"Robot Framework suites path '{suite_path_str}' referenced in cumulusci.yml "
                f"does not exist at '{suite_path}'. "
                "Create the directory or correct the path in the robot task options."
            )

    return issues


def check_cumulusci_automation(project_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []
    issues.extend(check_cumulusci_yml(project_dir))
    issues.extend(check_ci_files(project_dir))
    issues.extend(check_robot_config(project_dir))
    return issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()

    if not project_dir.exists():
        print(f"ISSUE: Project directory not found: {project_dir}")
        return 1

    issues = check_cumulusci_automation(project_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
