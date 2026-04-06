#!/usr/bin/env python3
"""Checker script for Data Seeding For Testing skill.

Checks org metadata or configuration relevant to Data Seeding For Testing.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_seeding_for_testing.py [--help]
    python3 check_data_seeding_for_testing.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Data Seeding For Testing configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_data_seeding_for_testing(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks Apex test classes for SeeAllData=true anti-patterns and
    sf data import tree plan JSON for ordering issues.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Apex test classes for SeeAllData=true combined with @testSetup
    classes_dir = manifest_dir / "force-app" / "main" / "default" / "classes"
    if not classes_dir.exists():
        # Try alternative paths
        for alt in ["src/classes", "classes"]:
            alt_path = manifest_dir / alt
            if alt_path.exists():
                classes_dir = alt_path
                break

    if classes_dir.exists():
        for cls_file in classes_dir.glob("*.cls"):
            try:
                content = cls_file.read_text(encoding="utf-8", errors="replace")
                has_see_all_data = "SeeAllData=true" in content
                has_test_setup = "@testSetup" in content
                if has_see_all_data and has_test_setup:
                    issues.append(
                        f"{cls_file.name}: @testSetup and SeeAllData=true are both present. "
                        "@testSetup is silently ignored when SeeAllData=true is set. "
                        "Remove SeeAllData=true and use a Test Data Factory instead."
                    )
                elif has_see_all_data and "@isTest" in content:
                    issues.append(
                        f"{cls_file.name}: SeeAllData=true detected. "
                        "This makes tests environment-dependent and breaks in scratch orgs. "
                        "Consider replacing with a @testSetup + Test Data Factory pattern."
                    )
            except OSError:
                pass

    # Check sf data import tree plan JSON for child-before-parent ordering
    for plan_file in manifest_dir.rglob("plan.json"):
        try:
            import json
            content = plan_file.read_text(encoding="utf-8", errors="replace")
            plan = json.loads(content)
            seen_objects = []
            for step in plan:
                sobject = step.get("sobject", "")
                resolve_refs = step.get("resolveRefs", False)
                save_refs = step.get("saveRefs", False)
                if resolve_refs and not seen_objects:
                    issues.append(
                        f"{plan_file}: Step for '{sobject}' has resolveRefs=true but no "
                        "prior steps have saveRefs=true. Ensure parent objects appear "
                        "before child objects in the plan array."
                    )
                seen_objects.append(sobject)
        except (OSError, Exception):
            pass

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_seeding_for_testing(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
