#!/usr/bin/env python3
"""Checker script for DevOps Center Pipeline skill.

Validates Salesforce project metadata structure for common DevOps Center
anti-patterns and configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_devops_center_pipeline.py [--help]
    python3 check_devops_center_pipeline.py --manifest-dir path/to/metadata
    python3 check_devops_center_pipeline.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce project metadata for DevOps Center pipeline "
            "anti-patterns and common configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


def check_for_sfdx_config(project_root: Path) -> list[str]:
    """Warn if sfdx-project.json exists but no .devops-center config is present.

    A project with sfdx-project.json is structured for CLI deployments.
    If it is also being managed by DevOps Center, there is a risk of mixed
    deployment paths causing source tracking drift.
    """
    issues: list[str] = []
    sfdx_config = project_root / "sfdx-project.json"
    if sfdx_config.exists():
        issues.append(
            "sfdx-project.json found: confirm that SFDX CLI deployments (sf project deploy start) "
            "are NOT being used alongside DevOps Center for the same orgs. Mixing CLI deploys with "
            "DevOps Center-managed pipeline orgs causes source tracking drift. "
            "See references/gotchas.md — Anti-Pattern: Mixing SFDX CLI Deployments."
        )
    return issues


def check_profiles_in_metadata(manifest_dir: Path) -> list[str]:
    """Flag profile metadata files.

    Profiles are a common source of merge conflicts in DevOps Center pipelines
    because every permission change touches the profile XML. Teams should
    consider using Permission Sets instead of Profiles for feature-level access.
    """
    issues: list[str] = []
    profile_dir = manifest_dir / "profiles"
    if profile_dir.is_dir():
        profiles = list(profile_dir.glob("*.profile-meta.xml"))
        if profiles:
            issues.append(
                f"Found {len(profiles)} Profile metadata file(s) in {profile_dir}. "
                "Profile XML files are a frequent source of merge conflicts in DevOps Center "
                "pipelines because many changes touch the same profile. Consider consolidating "
                "access changes into Permission Sets to reduce bundle-merge conflicts."
            )
    return issues


def check_named_credential_metadata(manifest_dir: Path) -> list[str]:
    """Check for Named Credential metadata.

    Named Credentials used for GitHub connectivity in DevOps Center are
    environment-specific. If Named Credential XML is checked into source,
    ensure endpoint URLs and auth settings are correct for each pipeline stage.
    """
    issues: list[str] = []
    nc_dir = manifest_dir / "namedCredentials"
    if nc_dir.is_dir():
        ncs = list(nc_dir.glob("*.namedCredential-meta.xml"))
        if ncs:
            issues.append(
                f"Found {len(ncs)} Named Credential metadata file(s). "
                "Named Credentials are environment-specific. Ensure that endpoint URLs "
                "and authentication settings are appropriate for each DevOps Center pipeline "
                "stage org. Do not use production endpoint values in sandbox-stage credentials."
            )
    return issues


def check_connected_app_metadata(manifest_dir: Path) -> list[str]:
    """Check Connected App metadata for OAuth scope issues.

    DevOps Center uses a Connected App for GitHub authentication. Connected Apps
    in metadata can have their scopes changed, which can break the pipeline
    GitHub integration if the required scopes are removed.
    """
    issues: list[str] = []
    ca_dir = manifest_dir / "connectedApps"
    if not ca_dir.is_dir():
        return issues

    ns = "http://soap.sforce.com/2006/04/metadata"
    for ca_file in ca_dir.glob("*.connectedApp-meta.xml"):
        try:
            tree = ET.parse(ca_file)
            root = tree.getroot()
            # Check for oauthConfig element — DevOps Center connected apps must have it
            oauth_config = root.find(f"{{{ns}}}oauthConfig")
            if oauth_config is None:
                issues.append(
                    f"Connected App '{ca_file.name}' has no oauthConfig element. "
                    "If this Connected App is used for DevOps Center's GitHub integration, "
                    "missing OAuth configuration will break the pipeline GitHub connection."
                )
        except ET.ParseError as exc:
            issues.append(
                f"Could not parse Connected App metadata '{ca_file.name}': {exc}. "
                "Malformed XML may cause deployment failures."
            )
    return issues


def check_permission_set_metadata(manifest_dir: Path) -> list[str]:
    """Verify DevOps Center permission sets are not being overridden.

    DevOps Center ships with managed permission sets (DevOps Center Admin,
    DevOps Center User). If unmanaged permission sets in the project share the
    same API name, they can overwrite the managed ones on deployment, breaking
    access to DevOps Center.
    """
    issues: list[str] = []
    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.is_dir():
        return issues

    # DevOps Center managed permission set prefixes
    reserved_names = {"sf_devops__DevOpsCenterAdmin", "sf_devops__DevOpsCenterUser"}
    for ps_file in ps_dir.glob("*.permissionset-meta.xml"):
        stem = ps_file.stem.replace(".permissionset-meta", "")
        if stem in reserved_names:
            issues.append(
                f"Permission Set '{ps_file.name}' uses a name reserved for DevOps Center's "
                "managed package (sf_devops namespace). Deploying an unmanaged permission set "
                "with this name will conflict with the managed package and may break DevOps Center access."
            )
    return issues


def check_devops_center_pipeline(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check project root (one level up from manifest_dir if manifest_dir is a source path)
    project_root = manifest_dir
    while project_root.parent != project_root:
        if (project_root / "sfdx-project.json").exists():
            break
        project_root = project_root.parent

    issues.extend(check_for_sfdx_config(project_root))
    issues.extend(check_profiles_in_metadata(manifest_dir))
    issues.extend(check_named_credential_metadata(manifest_dir))
    issues.extend(check_connected_app_metadata(manifest_dir))
    issues.extend(check_permission_set_metadata(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_devops_center_pipeline(manifest_dir)

    if not issues:
        print("No DevOps Center pipeline issues found.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, start=1):
        print(f"[{i}] {issue}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
