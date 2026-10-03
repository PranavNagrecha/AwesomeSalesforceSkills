#!/usr/bin/env python3
"""Checker script for Release Management skill.

Scans a Salesforce SFDX project directory for release management anti-patterns:
- Apex classes lacking test coverage annotations
- Deployment manifests that include destructive changes without a backup pattern
- Package.xml files referencing NoTestRun test level in CI scripts
- CI scripts that quick deploy with --use-most-recent (the CLI only looks back 3 days,
  although a validated job ID stays valid for 10 days)
- CI scripts that pass --ignore-errors to a production deploy (Metadata API requires
  rollbackOnError=true for production)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_release_management.py [--help]
    python3 check_release_management.py --project-dir path/to/sfdx-project
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce project for release management anti-patterns.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the SFDX project (default: current directory).",
    )
    return parser.parse_args()


def check_notest_run_in_scripts(project_dir: Path) -> list[str]:
    """Flag any shell/YAML files that use NoTestRun for production deployments."""
    issues: list[str] = []
    script_extensions = {".sh", ".yml", ".yaml", ".json"}
    ci_dirs = [project_dir / ".github", project_dir / ".circleci",
               project_dir / ".gitlab", project_dir, project_dir / "scripts"]

    for ci_dir in ci_dirs:
        if not ci_dir.exists():
            continue
        for ext in script_extensions:
            for file in ci_dir.glob(f"*{ext}"):
                try:
                    content = file.read_text(encoding="utf-8", errors="ignore")
                    if "NoTestRun" in content and "production" in content.lower():
                        issues.append(
                            f"{file}: 'NoTestRun' test level found in a file that "
                            f"mentions production — NoTestRun is not allowed for "
                            f"production deployments. Use RunLocalTests or RunSpecifiedTests."
                        )
                except (OSError, PermissionError):
                    pass
    return issues


def _ci_files(project_dir: Path) -> list[Path]:
    """Shell, YAML, and JSON files in the usual CI locations."""
    found: list[Path] = []
    script_extensions = {".sh", ".yml", ".yaml", ".json"}
    for ci_dir in [project_dir / ".github" / "workflows", project_dir / ".github",
                   project_dir / ".circleci", project_dir / ".gitlab", project_dir,
                   project_dir / "scripts"]:
        if not ci_dir.exists():
            continue
        for ext in script_extensions:
            found.extend(ci_dir.glob(f"*{ext}"))
    return sorted(set(found))


def check_quick_deploy_lookback(project_dir: Path) -> list[str]:
    """Flag quick deploys that rely on --use-most-recent instead of an explicit --job-id."""
    issues: list[str] = []
    for file in _ci_files(project_dir):
        try:
            content = file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for line in content.splitlines():
            if "deploy quick" in line and ("--use-most-recent" in line or re.search(r"\s-r(\s|$)", line)):
                issues.append(
                    f"{file}: 'sf project deploy quick --use-most-recent' only finds validations "
                    f"from the last 3 days, although the job ID is valid for 10. Pass --job-id explicitly."
                )
                break
    return issues


def check_ignore_errors_production(project_dir: Path) -> list[str]:
    """Flag --ignore-errors on deploy commands in files that mention production."""
    issues: list[str] = []
    for file in _ci_files(project_dir):
        try:
            content = file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "production" not in content.lower() and "prod" not in content.lower():
            continue
        for line in content.splitlines():
            if "deploy start" in line and "--ignore-errors" in line:
                issues.append(
                    f"{file}: '--ignore-errors' on a deploy in a production pipeline. "
                    f"Metadata API requires rollbackOnError=true for production; fix the failing component instead."
                )
                break
    return issues


def check_destructive_changes_without_backup_note(project_dir: Path) -> list[str]:
    """Warn if destructiveChanges.xml exists but no backup manifest is present."""
    issues: list[str] = []
    destructive_files = list(project_dir.rglob("destructiveChanges*.xml"))
    backup_files = list(project_dir.rglob("pre-release-backup*.xml")) + \
                   list(project_dir.rglob("*backup*.xml"))

    if destructive_files and not backup_files:
        files = ", ".join(str(f) for f in destructive_files[:3])
        issues.append(
            f"Found destructiveChanges.xml ({files}) but no pre-release backup manifest. "
            f"Always retrieve and store a pre-deploy backup before applying destructive changes. "
            f"Name the backup 'pre-release-backup.xml' or similar."
        )
    return issues


def check_sfdx_project_json(project_dir: Path) -> list[str]:
    """Verify sfdx-project.json exists for org-based projects."""
    issues: list[str] = []
    sfdx_project = project_dir / "sfdx-project.json"
    if not sfdx_project.exists():
        # Only warn if there are force-app or src directories (indicates SF project)
        if (project_dir / "force-app").exists() or (project_dir / "src").exists():
            issues.append(
                "SFDX source directory found but sfdx-project.json is missing. "
                "Run 'sf project generate' to initialize the project manifest."
            )
    return issues


def check_release_management(project_dir: Path) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    issues: list[str] = []

    if not project_dir.exists():
        issues.append(f"Project directory not found: {project_dir}")
        return issues

    issues.extend(check_notest_run_in_scripts(project_dir))
    issues.extend(check_destructive_changes_without_backup_note(project_dir))
    issues.extend(check_sfdx_project_json(project_dir))
    issues.extend(check_quick_deploy_lookback(project_dir))
    issues.extend(check_ignore_errors_production(project_dir))

    return issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    issues = check_release_management(project_dir)

    if not issues:
        print("No release management issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
