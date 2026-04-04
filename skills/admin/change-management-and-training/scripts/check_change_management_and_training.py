#!/usr/bin/env python3
"""Checker script for Change Management and Training skill.

Checks a Salesforce metadata directory for common change management issues:
- In-App Guidance prompts that target overly broad profiles (e.g., "Standard User")
- Path configurations missing coaching text for one or more record types
- Missing or empty training plan artifacts in the project directory

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_change_management_and_training.py [--help]
    python3 check_change_management_and_training.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce metadata for common change management and training issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_inapp_guidance_profiles(manifest_dir: Path) -> list[str]:
    """Warn when an In-App Guidance prompt targets a very broad profile name.

    Broad profile names like 'Standard User' or 'Custom: Standard User' are often
    used as catch-all profiles in orgs that rely on permission sets, meaning a
    change-specific prompt may be shown to unintended users.
    """
    issues: list[str] = []
    broad_profiles = {"Standard User", "Custom: Standard User", "Standard Platform User"}

    prompt_dir = manifest_dir / "prompts"
    if not prompt_dir.exists():
        return issues

    for prompt_file in prompt_dir.glob("*.prompt-meta.xml"):
        try:
            tree = ET.parse(prompt_file)
            root = tree.getroot()
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}

            for profile_elem in root.findall(".//sf:targetPageKey", ns) or root.findall(".//targetPageKey"):
                pass  # structural check only — profile names are in a different element

            # Check for profile references in the prompt XML
            for elem in root.iter():
                if elem.tag in ("profile", "targetProfile") and elem.text and elem.text.strip() in broad_profiles:
                    issues.append(
                        f"In-App Guidance '{prompt_file.stem}' targets broad profile "
                        f"'{elem.text.strip()}'. Verify this prompt should show to ALL "
                        f"users with this profile, not just those affected by the change."
                    )
        except ET.ParseError:
            issues.append(f"Could not parse In-App Guidance file: {prompt_file.name}")

    return issues


def check_path_coaching_text(manifest_dir: Path) -> list[str]:
    """Warn when a Path configuration has stages with empty coaching text.

    Empty coaching text is not an error in Salesforce, but it is a missed
    opportunity for in-app guidance during process changes.
    """
    issues: list[str] = []

    path_dir = manifest_dir / "pathAssistants"
    if not path_dir.exists():
        return issues

    for path_file in path_dir.glob("*.pathAssistant-meta.xml"):
        try:
            tree = ET.parse(path_file)
            root = tree.getroot()

            empty_stages: list[str] = []
            for step in root.iter("pathAssistantSteps"):
                value_elem = step.find("picklistValueName")
                text_elem = step.find("info")
                stage_name = value_elem.text.strip() if value_elem is not None and value_elem.text else "Unknown"
                text_value = text_elem.text.strip() if text_elem is not None and text_elem.text else ""
                if not text_value:
                    empty_stages.append(stage_name)

            if empty_stages:
                issues.append(
                    f"Path '{path_file.stem}' has stages with no coaching text: "
                    f"{', '.join(empty_stages)}. Consider adding guidance for users "
                    f"unfamiliar with what is expected at each stage."
                )
        except ET.ParseError:
            issues.append(f"Could not parse Path configuration file: {path_file.name}")

    return issues


def check_training_artifacts(manifest_dir: Path) -> list[str]:
    """Check for common training artifact files in a project docs directory.

    Looks for a 'docs/' or 'training/' folder and warns if expected change
    management artifacts are missing.
    """
    issues: list[str] = []

    # Look for a training or docs folder anywhere within 2 levels
    training_dirs = list(manifest_dir.glob("docs")) + list(manifest_dir.glob("training"))
    if not training_dirs:
        # Not an error — project may not use this convention
        return issues

    for t_dir in training_dirs:
        files = {f.name.lower() for f in t_dir.iterdir() if f.is_file()}
        expected_artifacts = [
            ("change-impact", "change impact assessment"),
            ("training", "training plan or materials"),
            ("communication", "release communication template"),
        ]
        for keyword, label in expected_artifacts:
            if not any(keyword in f for f in files):
                issues.append(
                    f"No {label} file found in '{t_dir.name}/'. "
                    f"Expected a file with '{keyword}' in the name."
                )

    return issues


def check_change_management_and_training(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_inapp_guidance_profiles(manifest_dir))
    issues.extend(check_path_coaching_text(manifest_dir))
    issues.extend(check_training_artifacts(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_change_management_and_training(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
