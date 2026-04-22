#!/usr/bin/env python3
"""Checker script for Deployment Automation Architecture skill.

Scans a repo for pipeline hygiene issues:
- Production deploy job without a preceding validation (check-only) step
- Pipeline manifests that wildcard-deploy Profile metadata
- Destructive changes implied by repo deletions without a destructiveChanges manifest

Usage:
    python3 check_deployment_automation_architecture.py [--repo-dir path/to/repo]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PROD_DEPLOY_PAT = re.compile(
    r"(?im)sf(dx)?\s+(project\s+)?deploy(\s+start)?\s+.*(--target-org\s+prod|--targetusername\s+prod|TargetOrg=prod)"
)
CHECK_ONLY_PAT = re.compile(r"(?i)(--dry-run|checkOnly|--check-only|dry-run\s*:\s*true)")
PROFILE_WILDCARD_PAT = re.compile(r"<name>Profile</name>[\s\S]{0,200}<members>\*</members>")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check deployment automation hygiene.")
    parser.add_argument("--repo-dir", default=".", help="Root directory of the repo.")
    return parser.parse_args()


def iter_pipeline_files(root: Path):
    roots = []
    for name in (".github/workflows", "ci", "pipelines", ".azure-pipelines"):
        candidate = root / name
        if candidate.exists():
            roots.append(candidate)
    for r in roots:
        for ext in ("*.yml", "*.yaml"):
            yield from r.rglob(ext)


def check_prod_without_validation(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_pipeline_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if PROD_DEPLOY_PAT.search(text) and not CHECK_ONLY_PAT.search(text):
            issues.append(
                f"{path.relative_to(root)}: production deploy without preceding check-only/validation"
            )
    return issues


def check_profile_wildcards(root: Path) -> list[str]:
    issues: list[str] = []
    for manifest in root.rglob("package.xml"):
        try:
            text = manifest.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if PROFILE_WILDCARD_PAT.search(text):
            issues.append(
                f"{manifest.relative_to(root)}: wildcard Profile deploy; scope with specific members"
            )
    return issues


def check_destructive_coverage(root: Path) -> list[str]:
    issues: list[str] = []
    destructive_files = list(root.rglob("destructiveChanges*.xml"))
    git_dir = root / ".git"
    if not git_dir.exists():
        return issues
    if not destructive_files:
        for tag in ("destructive", "delete"):
            for path in iter_pipeline_files(root):
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if tag in text.lower() and "destructiveChanges" not in text:
                    issues.append(
                        f"{path.relative_to(root)}: pipeline references '{tag}' but no destructiveChanges manifest exists"
                    )
                    break
    return issues


def main() -> int:
    args = parse_args()
    repo_dir = Path(args.repo_dir)
    if not repo_dir.exists():
        print(f"ERROR: repo directory not found: {repo_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_prod_without_validation(repo_dir))
    issues.extend(check_profile_wildcards(repo_dir))
    issues.extend(check_destructive_coverage(repo_dir))

    if not issues:
        print("No deployment automation issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
