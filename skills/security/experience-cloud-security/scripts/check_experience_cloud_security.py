#!/usr/bin/env python3
"""Checker script for Experience Cloud Security skill.

Checks org metadata or configuration relevant to Experience Cloud Security.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_security.py [--help]
    python3 check_experience_cloud_security.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Experience Cloud Security configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_experience_cloud_security(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks Apex classes accessible to Experience Cloud for without sharing usage
    and flags classes that may be invoked by guest or portal users.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Find Apex class directories
    classes_dirs = []
    for candidate in [
        manifest_dir / "force-app" / "main" / "default" / "classes",
        manifest_dir / "src" / "classes",
        manifest_dir / "classes",
    ]:
        if candidate.exists():
            classes_dirs.append(candidate)

    if not classes_dirs:
        return issues  # No Apex classes found — nothing to check

    for classes_dir in classes_dirs:
        for cls_file in classes_dir.glob("*.cls"):
            try:
                content = cls_file.read_text(encoding="utf-8", errors="replace")

                # Check for 'global without sharing' — highest risk for guest access
                if "global" in content and "without sharing" in content:
                    issues.append(
                        f"{cls_file.name}: Uses 'global without sharing'. "
                        "Global classes accessible to Experience Cloud guest or portal users "
                        "bypass all record-level security. Verify this class is not callable "
                        "by guest profile or portal users. If it is, change to 'with sharing' "
                        "or implement explicit CRUD/FLS checks."
                    )

                # Check for @RestResource on classes without 'with sharing'
                if "@RestResource" in content:
                    has_with_sharing = "with sharing" in content
                    has_without_sharing = "without sharing" in content
                    if has_without_sharing:
                        issues.append(
                            f"{cls_file.name}: @RestResource class uses 'without sharing'. "
                            "REST endpoints may be called by portal or guest users. "
                            "Consider using 'with sharing' or validating caller identity explicitly."
                        )
                    elif not has_with_sharing:
                        issues.append(
                            f"{cls_file.name}: @RestResource class has no sharing declaration "
                            "(defaults to inherited sharing). Explicitly declare 'with sharing' "
                            "if this endpoint may be called by Experience Cloud users."
                        )

            except OSError:
                pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_security(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
