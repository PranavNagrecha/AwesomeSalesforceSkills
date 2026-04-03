#!/usr/bin/env python3
"""Checker script for Flow For Experience Cloud skill."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow For Experience Cloud configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_flow_for_experience_cloud(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    experience_files = list(manifest_dir.rglob("*"))
    has_lwr_runtime = False
    for candidate in experience_files:
        if not candidate.is_file():
            continue
        text = candidate.read_text(encoding="utf-8", errors="ignore").lower()
        if "lwr" in text and ("experience" in str(candidate).lower() or "site" in str(candidate).lower()):
            has_lwr_runtime = True
            break

    custom_screen_flows = []
    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        text = flow_path.read_text(encoding="utf-8", errors="ignore")
        if "<screens>" in text and "<componentName>" in text:
            custom_screen_flows.append(flow_path)

    if has_lwr_runtime and custom_screen_flows:
        issues.append(
            "LWR site markers were found alongside screen flows that appear to use custom components; review `lightning-flow` compatibility before exposing these flows in Experience Cloud."
        )

    guest_profiles = sorted(manifest_dir.rglob("*Guest*.profile-meta.xml"))
    for profile_path in guest_profiles:
        text = profile_path.read_text(encoding="utf-8", errors="ignore")
        if "<classAccesses>" in text or "<objectPermissions>" in text:
            issues.append(
                f"{profile_path}: guest profile grants Apex or object access; review every Experience Cloud flow that depends on this profile as a public-surface security decision."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_flow_for_experience_cloud(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
