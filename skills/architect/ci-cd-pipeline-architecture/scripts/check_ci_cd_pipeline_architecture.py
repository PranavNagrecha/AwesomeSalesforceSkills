#!/usr/bin/env python3
"""Checker script for CI/CD Pipeline Architecture skill.

Validates a Salesforce project directory for CI/CD pipeline architecture
issues: missing CI configuration files, absence of static analysis config,
no deployment validation evidence, and missing rollback documentation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ci_cd_pipeline_architecture.py [--help]
    python3 check_ci_cd_pipeline_architecture.py --project-dir path/to/sfdx-project
    python3 check_ci_cd_pipeline_architecture.py --project-dir . --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, *patterns: str) -> list[Path]:
    """Return all files under root matching any of the given glob patterns."""
    found: list[Path] = []
    for pattern in patterns:
        found.extend(root.rglob(pattern))
    return found


def _file_contains(path: Path, *keywords: str) -> bool:
    """Return True if path contains all of the given keywords (case-insensitive)."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        return all(kw.lower() in text for kw in keywords)
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_sfdx_project_json(project_dir: Path) -> list[str]:
    """Confirm sfdx-project.json exists — required for any SFDX-based pipeline."""
    issues: list[str] = []
    sfdx_file = project_dir / "sfdx-project.json"
    if not sfdx_file.exists():
        issues.append(
            "Missing sfdx-project.json: project does not appear to be an SFDX project. "
            "A CI/CD pipeline for Salesforce requires a valid SFDX project structure."
        )
        return issues

    try:
        data = json.loads(sfdx_file.read_text(encoding="utf-8"))
        if "packageDirectories" not in data:
            issues.append(
                "sfdx-project.json is missing 'packageDirectories'. "
                "This field is required for sf project deploy to resolve source paths."
            )
    except (json.JSONDecodeError, OSError) as exc:
        issues.append(f"sfdx-project.json could not be parsed: {exc}")

    return issues


def check_ci_workflow_files(project_dir: Path) -> list[str]:
    """Check for presence of any CI workflow configuration file."""
    issues: list[str] = []

    ci_indicators = [
        # GitHub Actions
        project_dir / ".github" / "workflows",
        # GitLab CI
        project_dir / ".gitlab-ci.yml",
        # Jenkins
        project_dir / "Jenkinsfile",
        # Azure DevOps
        project_dir / "azure-pipelines.yml",
        # Bitbucket
        project_dir / "bitbucket-pipelines.yml",
        # CircleCI
        project_dir / ".circleci" / "config.yml",
        # CumulusCI
        project_dir / "cumulusci.yml",
    ]

    github_workflows = project_dir / ".github" / "workflows"
    github_files = list(github_workflows.glob("*.yml")) + list(github_workflows.glob("*.yaml")) \
        if github_workflows.is_dir() else []

    has_ci = (
        any(p.exists() for p in ci_indicators if not p.is_dir())
        or len(github_files) > 0
        or (project_dir / ".gitlab-ci.yml").exists()
        or (project_dir / "Jenkinsfile").exists()
    )

    if not has_ci:
        issues.append(
            "No CI workflow configuration found (.github/workflows/, .gitlab-ci.yml, "
            "Jenkinsfile, azure-pipelines.yml, bitbucket-pipelines.yml). "
            "A CI/CD pipeline requires at least one automated workflow configuration."
        )

    return issues


def check_static_analysis_config(project_dir: Path) -> list[str]:
    """Check for PMD or Salesforce Code Analyzer configuration."""
    issues: list[str] = []

    pmd_indicators = [
        ".pmd",
        "pmd-ruleset.xml",
        "ruleset.xml",
        ".forceignore",  # often used alongside Code Analyzer
    ]

    pmd_files = _find_files(project_dir, "*.pmd", "pmd-ruleset.xml", "ruleset.xml")
    # Also check CI workflow files for 'pmd' or 'code-analyzer' references
    workflow_files = _find_files(
        project_dir,
        "*.yml", "*.yaml", "Jenkinsfile",
    )
    ci_mentions_scan = any(
        _file_contains(f, "pmd") or _file_contains(f, "code-analyzer") or _file_contains(f, "scanner")
        for f in workflow_files
        if f.stat().st_size < 500_000  # skip large non-workflow files
    )

    if not pmd_files and not ci_mentions_scan:
        issues.append(
            "No static analysis configuration found (PMD ruleset, Salesforce Code Analyzer invocation). "
            "The Well-Architected pipeline architecture requires a static analysis gate at the "
            "feature branch → CI stage. Add a PMD ruleset file or a Code Analyzer step to CI workflows."
        )

    return issues


def check_validation_only_in_ci(project_dir: Path) -> list[str]:
    """Check that CI workflows use validation-only deploys (not blind full deploys)."""
    issues: list[str] = []

    workflow_files = _find_files(
        project_dir,
        ".github/workflows/*.yml",
        ".github/workflows/*.yaml",
        ".gitlab-ci.yml",
        "Jenkinsfile",
        "azure-pipelines.yml",
    )
    # rglob-style already handled by _find_files above but let's also do a direct search
    workflow_files += list((project_dir / ".github" / "workflows").glob("*.yml")) \
        if (project_dir / ".github" / "workflows").is_dir() else []
    workflow_files = list(set(workflow_files))  # deduplicate

    if not workflow_files:
        return issues  # No CI files; already reported in check_ci_workflow_files

    has_validate = any(
        _file_contains(f, "validate") or _file_contains(f, "checkonly") or _file_contains(f, "check-only")
        for f in workflow_files
        if f.stat().st_size < 500_000
    )

    has_full_deploy_only = all(
        _file_contains(f, "deploy") and not (
            _file_contains(f, "validate") or _file_contains(f, "checkonly")
        )
        for f in workflow_files
        if f.stat().st_size < 500_000
    )

    if workflow_files and not has_validate and has_full_deploy_only:
        issues.append(
            "CI workflow files reference deployment but do not appear to use validation-only deploys "
            "('validate', 'checkonly'). The CI gate should use 'sf project deploy validate' or "
            "'--checkonly' to avoid modifying shared sandbox state during PR validation."
        )

    return issues


def check_rollback_documentation(project_dir: Path) -> list[str]:
    """Check for any rollback runbook or documentation."""
    issues: list[str] = []

    runbook_indicators = _find_files(
        project_dir,
        "RUNBOOK*", "runbook*",
        "ROLLBACK*", "rollback*",
        "RELEASE*", "release*",
        "DEPLOY*", "deploy*",
    )
    doc_files = _find_files(project_dir, "*.md", "*.rst", "*.txt")

    has_rollback_doc = any(
        _file_contains(f, "rollback") or _file_contains(f, "revert") or _file_contains(f, "roll back")
        for f in (runbook_indicators + doc_files)
        if f.stat().st_size < 200_000
    )

    if not has_rollback_doc:
        issues.append(
            "No rollback documentation found. Salesforce declarative metadata (Flows, Page Layouts, "
            "Custom Objects) has no native rollback mechanism. A pipeline runbook must document "
            "the git-revert-and-redeploy procedure before each production deployment. "
            "Create a RUNBOOK.md or DEPLOY.md with rollback steps."
        )

    return issues


def check_apex_coverage_threshold(project_dir: Path) -> list[str]:
    """Check that CI workflows specify an Apex test coverage threshold."""
    issues: list[str] = []

    workflow_files = (
        list((project_dir / ".github" / "workflows").glob("*.yml"))
        + list((project_dir / ".github" / "workflows").glob("*.yaml"))
        if (project_dir / ".github" / "workflows").is_dir() else []
    )
    workflow_files += _find_files(project_dir, ".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml")
    workflow_files = list(set(workflow_files))

    if not workflow_files:
        return issues  # No CI files; already reported elsewhere

    has_coverage_gate = any(
        _file_contains(f, "coverage") and (
            _file_contains(f, "75") or _file_contains(f, "80") or _file_contains(f, "85") or
            _file_contains(f, "threshold") or _file_contains(f, "minimum")
        )
        for f in workflow_files
        if f.stat().st_size < 500_000
    )

    if not has_coverage_gate:
        issues.append(
            "No Apex test coverage threshold detected in CI workflow files. "
            "Salesforce requires ≥ 75% org-wide coverage for production deployment. "
            "The pipeline should enforce this threshold explicitly (recommend ≥ 85% for new classes) "
            "rather than relying on the platform to reject the deploy as a surprise late-stage failure."
        )

    return issues


def check_quick_deploy_awareness(project_dir: Path) -> list[str]:
    """Warn if production deploy step does not reference quick deploy or validation ID."""
    issues: list[str] = []

    # Only check if there appears to be a production deploy step
    workflow_files = (
        list((project_dir / ".github" / "workflows").glob("*.yml"))
        + list((project_dir / ".github" / "workflows").glob("*.yaml"))
        if (project_dir / ".github" / "workflows").is_dir() else []
    )
    if not workflow_files:
        return issues

    has_production_deploy = any(
        _file_contains(f, "production") or _file_contains(f, "prod")
        for f in workflow_files
        if f.stat().st_size < 500_000
    )

    if not has_production_deploy:
        return issues

    has_quick_deploy = any(
        _file_contains(f, "quick") or _file_contains(f, "job-id") or _file_contains(f, "jobid") or
        _file_contains(f, "deployment-id") or _file_contains(f, "deploymentid")
        for f in workflow_files
        if f.stat().st_size < 500_000
    )

    if not has_quick_deploy:
        issues.append(
            "Production deploy step found but no quick deploy usage detected (--job-id / deployment ID). "
            "Consider using 'sf project deploy quick --job-id <validated-ID>' for production to reduce "
            "the change window. Note: the validated deployment ID expires after 96 hours."
        )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_ci_cd_pipeline_architecture(
    project_dir: Path,
    strict: bool = False,
) -> list[str]:
    """Run all CI/CD pipeline architecture checks and return a list of issue strings."""
    issues: list[str] = []

    if not project_dir.exists():
        return [f"Project directory not found: {project_dir}"]

    issues.extend(check_sfdx_project_json(project_dir))
    issues.extend(check_ci_workflow_files(project_dir))
    issues.extend(check_static_analysis_config(project_dir))
    issues.extend(check_validation_only_in_ci(project_dir))
    issues.extend(check_rollback_documentation(project_dir))
    issues.extend(check_apex_coverage_threshold(project_dir))

    if strict:
        issues.extend(check_quick_deploy_awareness(project_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce project directory for CI/CD pipeline architecture issues. "
            "Validates CI workflow files, static analysis configuration, validation-only deploy usage, "
            "rollback documentation, and Apex test coverage threshold enforcement."
        ),
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce SFDX project (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Enable additional advisory checks (quick deploy usage, etc.).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()

    print(f"Checking CI/CD pipeline architecture in: {project_dir}")
    issues = check_ci_cd_pipeline_architecture(project_dir, strict=args.strict)

    if not issues:
        print("No issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:\n", file=sys.stderr)
    for i, issue in enumerate(issues, 1):
        print(f"WARN [{i}]: {issue}\n", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
