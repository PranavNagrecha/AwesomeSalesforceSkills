#!/usr/bin/env python3
"""Checker script for Copado Essentials skill.

Checks a Salesforce metadata project directory for issues that commonly occur
when operating a Copado Essentials pipeline. Detects patterns described in
references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_copado_essentials.py [--help]
    python3 check_copado_essentials.py --manifest-dir path/to/metadata
    python3 check_copado_essentials.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata project for issues relevant to "
            "Copado Essentials pipeline operation."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_copado_package_presence(manifest_dir: Path) -> list[str]:
    """Warn when Copado managed-package metadata files are found in the project.

    Copado Essentials is a managed package and should not have its metadata
    committed to source control. copado__ prefixed files indicate someone
    may have retrieved Copado managed metadata and accidentally committed it.
    """
    issues: list[str] = []
    copado_files = list(manifest_dir.rglob("copado__*"))
    if copado_files:
        sample = [str(f.relative_to(manifest_dir)) for f in copado_files[:5]]
        issues.append(
            f"Found {len(copado_files)} file(s) with 'copado__' prefix in the metadata "
            f"tree. Copado managed-package metadata should not be committed to source "
            f"control — it is installed from AppExchange. "
            f"Sample: {', '.join(sample)}"
        )
    return issues


def check_flow_api_version(manifest_dir: Path) -> list[str]:
    """Warn when Flow metadata files carry an API version older than 50.0.

    Flows with API versions older than 50.0 (Winter 21) may behave differently
    on re-deployment in newer orgs and can cause silent promotion failures
    when Copado uses the Metadata API to deploy them.
    """
    issues: list[str] = []

    # Support both MDAPI layout and DX layout
    flow_dirs = [
        manifest_dir / "flows",
        manifest_dir / "force-app" / "main" / "default" / "flows",
    ]

    for flow_dir in flow_dirs:
        if not flow_dir.exists():
            continue
        for flow_file in flow_dir.rglob("*.flow-meta.xml"):
            try:
                tree = ET.parse(flow_file)
                root = tree.getroot()
                ns_match = re.match(r"\{(.+?)\}", root.tag)
                ns = f"{{{ns_match.group(1)}}}" if ns_match else ""
                api_version_el = root.find(f"{ns}apiVersion")
                if api_version_el is not None and api_version_el.text:
                    try:
                        api_ver = float(api_version_el.text)
                        if api_ver < 50.0:
                            issues.append(
                                f"Flow '{flow_file.name}' has API version {api_ver:.1f} "
                                f"(< 50.0). Copado promotions use the Metadata API; old "
                                f"Flow API versions may cause re-deployment failures. "
                                f"Bump to the current API version."
                            )
                    except ValueError:
                        pass
            except ET.ParseError:
                issues.append(
                    f"Flow file '{flow_file.name}' could not be parsed as XML. "
                    f"Malformed Flow XML will cause Copado promotion failures."
                )
    return issues


def check_for_in_progress_git_merge(manifest_dir: Path) -> list[str]:
    """Warn when a git merge is in progress that was not initiated by Copado.

    MERGE_HEAD in .git/ indicates an uncommitted merge. If this targets an
    environment branch (develop, staging, main), it desynchronizes Copado
    pipeline state.
    """
    issues: list[str] = []
    git_dir = _find_git_dir(manifest_dir)
    if git_dir is None:
        return issues

    merge_head = git_dir / "MERGE_HEAD"
    if merge_head.exists():
        issues.append(
            "A git merge is in progress (MERGE_HEAD found in .git/). "
            "If this merge targets an environment branch (develop, staging, main) "
            "and was NOT initiated by Copado, it will desynchronize pipeline state. "
            "Either complete the merge through Copado's promotion workflow, "
            "or abort it with 'git merge --abort'."
        )
    return issues


def check_package_xml_for_copado_types(manifest_dir: Path) -> list[str]:
    """Warn when package.xml or destructiveChanges.xml reference Copado managed types.

    Deploying Copado managed metadata via a user story conflicts with the
    installed managed package version in the target org.
    """
    issues: list[str] = []
    pkg_candidates = (
        list(manifest_dir.rglob("package.xml"))
        + list(manifest_dir.rglob("destructiveChanges.xml"))
        + list(manifest_dir.rglob("destructiveChangesPost.xml"))
    )

    for pkg_file in pkg_candidates:
        try:
            content = pkg_file.read_text(encoding="utf-8", errors="replace")
            copado_refs = re.findall(r"copado__\w+", content)
            if copado_refs:
                unique_refs = sorted(set(copado_refs))
                issues.append(
                    f"'{pkg_file.name}' references {len(unique_refs)} Copado managed "
                    f"component(s): {', '.join(unique_refs[:5])}"
                    f"{'...' if len(unique_refs) > 5 else ''}. "
                    f"Deploying Copado managed metadata via a user story will conflict "
                    f"with the installed managed package. Remove these from the manifest."
                )
        except OSError:
            pass
    return issues


def check_branch_name_convention(manifest_dir: Path) -> list[str]:
    """If a .git directory is present, check the current branch name.

    Branches with special characters cause Copado to fail silently when
    attempting to link user stories to branches. The Copado convention is
    feature/{user-story-reference} with no special characters.
    """
    issues: list[str] = []
    git_dir = _find_git_dir(manifest_dir)
    if git_dir is None:
        return issues

    head_file = git_dir / "HEAD"
    if not head_file.exists():
        return issues

    try:
        head_content = head_file.read_text(encoding="utf-8").strip()
    except OSError:
        return issues

    match = re.match(r"ref: refs/heads/(.+)", head_content)
    if not match:
        return issues  # detached HEAD

    branch_name = match.group(1)

    if branch_name.startswith("feature/"):
        identifier = branch_name[len("feature/"):]
        invalid_chars = re.findall(r"[ ~^:?*\[\\]", identifier)
        if invalid_chars:
            issues.append(
                f"Current branch '{branch_name}' contains characters that are invalid "
                f"in Git branch names: {sorted(set(invalid_chars))}. "
                f"Copado derives the User Story branch from the reference field; "
                f"special characters cause silent branch creation failures. "
                f"Rename to use only alphanumeric characters, hyphens, and underscores "
                f"(e.g., feature/US-2024-042)."
            )
    return issues


def _find_git_dir(start: Path) -> Path | None:
    """Walk up directory tree to find a .git directory."""
    candidate = start.resolve()
    for _ in range(7):
        if (candidate / ".git").is_dir():
            return candidate / ".git"
        parent = candidate.parent
        if parent == candidate:
            break
        candidate = parent
    return None


def check_copado_essentials(manifest_dir: Path) -> list[str]:
    """Run all Copado Essentials checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_copado_package_presence(manifest_dir))
    issues.extend(check_flow_api_version(manifest_dir))
    issues.extend(check_for_in_progress_git_merge(manifest_dir))
    issues.extend(check_package_xml_for_copado_types(manifest_dir))
    issues.extend(check_branch_name_convention(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_copado_essentials(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
