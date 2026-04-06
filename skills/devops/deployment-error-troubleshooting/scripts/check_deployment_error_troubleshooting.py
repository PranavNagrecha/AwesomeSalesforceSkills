#!/usr/bin/env python3
"""Checker script for the deployment-error-troubleshooting skill.

Scans a Salesforce metadata project directory for common deployment-error
risk factors: API version mismatches, missing test classes for deployed Apex,
and deployment script mistakes.

Stdlib only — no pip dependencies required.

Usage:
    python3 check_deployment_error_troubleshooting.py --manifest-dir path/to/project
    python3 check_deployment_error_troubleshooting.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce project for common deployment-error risk factors.\n"
            "Scans metadata XML files, sfdx-project.json, and deployment scripts."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project (default: current directory).",
    )
    return parser.parse_args()


def check_api_version_consistency(root: Path) -> list[str]:
    """Check that all -meta.xml files use the same API version."""
    issues: list[str] = []
    meta_files = list(root.rglob("*-meta.xml"))
    if not meta_files:
        return issues

    versions: dict[str, list[str]] = {}
    api_version_pattern = re.compile(r"<apiVersion>([\d.]+)</apiVersion>")

    for meta_file in meta_files:
        try:
            content = meta_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        match = api_version_pattern.search(content)
        if match:
            version = match.group(1)
            versions.setdefault(version, []).append(str(meta_file))

    if len(versions) > 1:
        version_summary = ", ".join(
            f"{v} ({len(files)} file{'s' if len(files) != 1 else ''})"
            for v, files in sorted(versions.items())
        )
        issues.append(
            f"API version inconsistency: found {len(versions)} different API versions "
            f"across {len(meta_files)} metadata files: {version_summary}. "
            "Mixed API versions can cause UNSUPPORTED_API_VERSION errors when deploying "
            "to an org on an older release. Standardize all -meta.xml files to one version."
        )

    # Check against sfdx-project.json if present
    sfdx_project = root / "sfdx-project.json"
    if sfdx_project.exists() and versions:
        try:
            project_config = json.loads(sfdx_project.read_text(encoding="utf-8"))
            source_api = project_config.get("sourceApiVersion", "")
            if source_api:
                meta_versions = set(versions.keys())
                if source_api not in meta_versions and meta_versions:
                    issues.append(
                        f"sfdx-project.json sourceApiVersion ({source_api}) does not match "
                        f"the API version(s) in metadata files ({', '.join(sorted(meta_versions))}). "
                        "This mismatch can cause unexpected deployment behavior."
                    )
        except (json.JSONDecodeError, OSError):
            pass

    return issues


def check_apex_test_coverage(root: Path) -> list[str]:
    """Check that every Apex class has a plausible corresponding test class."""
    issues: list[str] = []
    classes_dir_candidates = list(root.rglob("classes"))
    if not classes_dir_candidates:
        return issues

    apex_classes: set[str] = set()
    test_classes: set[str] = set()

    for classes_dir in classes_dir_candidates:
        if not classes_dir.is_dir():
            continue
        for cls_file in classes_dir.glob("*.cls"):
            name = cls_file.stem
            try:
                content = cls_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if re.search(r"@[Ii]s[Tt]est", content):
                test_classes.add(name.lower())
            else:
                apex_classes.add(name)

    # Check for classes without any plausible test class
    uncovered: list[str] = []
    for cls_name in sorted(apex_classes):
        lower = cls_name.lower()
        plausible_tests = [
            f"{lower}test",
            f"{lower}_test",
            f"test{lower}",
            f"test_{lower}",
        ]
        if not any(t in test_classes for t in plausible_tests):
            uncovered.append(cls_name)

    if uncovered and len(uncovered) <= 20:
        names = ", ".join(uncovered[:10])
        suffix = "..." if len(uncovered) > 10 else ""
        issues.append(
            f"No test class found for {len(uncovered)} Apex class(es): "
            f"{names}{suffix}. "
            "Missing test coverage will cause deployment failures with RunSpecifiedTests "
            "(per-class 75%) or RunLocalTests (org-wide 75% + trigger 1%)."
        )
    elif uncovered:
        issues.append(
            f"No test class found for {len(uncovered)} Apex class(es). "
            "This is a deployment risk — coverage failures are the most common "
            "cause of blocked production deployments."
        )

    return issues


def check_deploy_scripts(root: Path) -> list[str]:
    """Scan shell scripts and CI configs for common deployment command mistakes."""
    issues: list[str] = []
    script_files = (
        list(root.rglob("*.sh"))
        + list(root.rglob("*.bash"))
        + list(root.rglob("*.yml"))
        + list(root.rglob("*.yaml"))
    )

    rollback_flag_pattern = re.compile(r"--rollback-on-error")
    no_test_prod_pattern = re.compile(
        r"sf\s+project\s+deploy\s+start.*--test-level\s+NoTestRun"
    )

    for script_file in script_files:
        try:
            content = script_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        try:
            rel = script_file.relative_to(root)
        except ValueError:
            rel = script_file

        # Check for nonexistent --rollback-on-error flag
        if rollback_flag_pattern.search(content):
            issues.append(
                f"[{rel}] WARNING: Uses --rollback-on-error flag which does not exist "
                "in sf CLI. The rollbackOnError option is a Metadata API parameter, "
                "not a CLI flag. This command will fail."
            )

        # Check for NoTestRun targeting production (heuristic)
        if no_test_prod_pattern.search(content):
            if "production" in content.lower() or "prod" in str(rel).lower():
                issues.append(
                    f"[{rel}] WARNING: Deploy command uses NoTestRun in what appears to be "
                    "a production deployment context. Production deployments containing Apex "
                    "require at least RunLocalTests."
                )

    return issues


def check_deployment_error_troubleshooting(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the project directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Project directory not found: {manifest_dir}")
        return issues

    issues.extend(check_api_version_consistency(manifest_dir))
    issues.extend(check_apex_test_coverage(manifest_dir))
    issues.extend(check_deploy_scripts(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_deployment_error_troubleshooting(manifest_dir)

    if not issues:
        print("No deployment-error risk factors found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
