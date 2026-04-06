#!/usr/bin/env python3
"""Checker script for In-App Guidance and Walkthroughs skill.

Validates Salesforce In-App Guidance metadata exported from an org.
Checks for common misconfigurations including walkthrough step count limits,
active walkthrough slot usage, missing audience targeting, and targeted
prompt anchor documentation gaps.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_in_app_guidance_and_walkthroughs.py [--help]
    python3 check_in_app_guidance_and_walkthroughs.py --manifest-dir path/to/metadata
    python3 check_in_app_guidance_and_walkthroughs.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce In-App Guidance limits (as of Spring '25)
FREE_TIER_WALKTHROUGH_LIMIT = 3
RECOMMENDED_MAX_STEPS = 5
HARD_MAX_STEPS = 10

# Metadata folder names for In-App Guidance
PROMPT_METADATA_FOLDERS = [
    "prompts",
    "inAppGuidance",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check In-App Guidance metadata for common misconfigurations.\n"
            "Point --manifest-dir at the root of a Salesforce metadata deployment "
            "(e.g. force-app/main/default or a SFDX project root)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print issues as WARNs and exit 0 even if issues are found.",
    )
    return parser.parse_args()


def find_prompt_files(manifest_dir: Path) -> list[Path]:
    """Find all In-App Guidance / prompt metadata XML files under manifest_dir."""
    prompt_files: list[Path] = []
    for folder_name in PROMPT_METADATA_FOLDERS:
        folder = manifest_dir / folder_name
        if folder.is_dir():
            prompt_files.extend(folder.rglob("*.prompt-meta.xml"))
            prompt_files.extend(folder.rglob("*.prompt"))
            prompt_files.extend(folder.rglob("*.xml"))
    # Also search recursively from root for .prompt-meta.xml files
    prompt_files.extend(manifest_dir.rglob("*.prompt-meta.xml"))
    # Deduplicate while preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in prompt_files:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def parse_prompt_metadata(xml_path: Path) -> dict:
    """Parse a single prompt metadata XML file and return a structured dict.

    Returns a dict with keys:
        name, prompt_type, steps, is_walkthrough, audience_profiles,
        has_description, is_active, raw_path
    """
    result: dict = {
        "name": xml_path.stem.replace(".prompt-meta", "").replace(".prompt", ""),
        "prompt_type": None,
        "steps": [],
        "is_walkthrough": False,
        "audience_profiles": [],
        "has_description": False,
        "is_active": False,
        "raw_path": str(xml_path),
        "parse_error": None,
    }

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Strip XML namespace if present
        def strip_ns(tag: str) -> str:
            if "}" in tag:
                return tag.split("}")[1]
            return tag

        def find_text(element: ET.Element, tag: str) -> str | None:
            child = element.find(f".//{tag}")
            if child is None:
                # Try without namespace match
                for el in element.iter():
                    if strip_ns(el.tag) == tag:
                        return el.text
                return None
            return child.text

        # Check if this is a walkthrough (has multiple steps or promptType = walkthrough)
        prompt_type_el = find_text(root, "promptType")
        if prompt_type_el:
            result["prompt_type"] = prompt_type_el.strip()
            result["is_walkthrough"] = "walkthrough" in prompt_type_el.lower()

        # Count steps
        steps = [el for el in root.iter() if strip_ns(el.tag) in ("step", "promptStep", "steps")]
        result["steps"] = steps
        if len(steps) > 1:
            result["is_walkthrough"] = True

        # Collect audience profiles
        profiles = []
        for el in root.iter():
            if strip_ns(el.tag) in ("profile", "audienceProfile", "targetProfile"):
                if el.text:
                    profiles.append(el.text.strip())
        result["audience_profiles"] = profiles

        # Check for description
        desc = find_text(root, "description")
        result["has_description"] = bool(desc and desc.strip())

        # Check active status
        active_el = find_text(root, "isActive")
        if active_el is not None:
            result["is_active"] = active_el.strip().lower() == "true"
        else:
            # Default assumption: if file exists in deployment it is intended to be active
            result["is_active"] = True

    except ET.ParseError as exc:
        result["parse_error"] = str(exc)

    return result


def check_walkthroughs(prompts: list[dict]) -> list[str]:
    """Check walkthrough-specific rules and return issue strings."""
    issues: list[str] = []

    walkthroughs = [p for p in prompts if p["is_walkthrough"]]
    active_walkthroughs = [p for p in walkthroughs if p["is_active"]]

    # Check active walkthrough count against free tier limit
    if len(active_walkthroughs) > FREE_TIER_WALKTHROUGH_LIMIT:
        issues.append(
            f"LIMIT: {len(active_walkthroughs)} active walkthroughs found — "
            f"free tier allows {FREE_TIER_WALKTHROUGH_LIMIT}. "
            f"Additional walkthroughs require a Sales Enablement license. "
            f"Active walkthroughs: {[p['name'] for p in active_walkthroughs]}"
        )

    # Check step count per walkthrough
    for prompt in walkthroughs:
        step_count = len(prompt["steps"])
        if step_count > HARD_MAX_STEPS:
            issues.append(
                f"ERROR: Walkthrough '{prompt['name']}' has {step_count} steps — "
                f"hard maximum is {HARD_MAX_STEPS}. Reduce step count."
            )
        elif step_count > RECOMMENDED_MAX_STEPS:
            issues.append(
                f"WARN: Walkthrough '{prompt['name']}' has {step_count} steps — "
                f"Salesforce recommends max {RECOMMENDED_MAX_STEPS} for acceptable completion rates. "
                f"Consider splitting into two shorter walkthroughs."
            )

    return issues


def check_audience_targeting(prompts: list[dict]) -> list[str]:
    """Check that prompts have audience profiles configured."""
    issues: list[str] = []
    for prompt in prompts:
        if not prompt["audience_profiles"]:
            issues.append(
                f"WARN: Prompt '{prompt['name']}' has no audience profiles configured — "
                f"it will display to all Lightning Experience users. "
                f"Set at least one profile to scope the audience."
            )
    return issues


def check_targeted_prompt_descriptions(prompts: list[dict]) -> list[str]:
    """Check that targeted prompts have a description documenting the anchor element."""
    issues: list[str] = []
    for prompt in prompts:
        if prompt["prompt_type"] and "targeted" in str(prompt["prompt_type"]).lower():
            if not prompt["has_description"]:
                issues.append(
                    f"WARN: Targeted prompt '{prompt['name']}' has no description — "
                    f"document the anchor UI element in the description field. "
                    f"If the anchor is removed from the page layout, the prompt will silently stop rendering."
                )
    return issues


def check_parse_errors(prompts: list[dict]) -> list[str]:
    """Return issues for any files that failed to parse."""
    issues: list[str] = []
    for prompt in prompts:
        if prompt["parse_error"]:
            issues.append(
                f"ERROR: Could not parse metadata file for '{prompt['name']}': {prompt['parse_error']}"
            )
    return issues


def check_in_app_guidance_and_walkthroughs(manifest_dir: Path) -> list[str]:
    """Run all In-App Guidance checks and return a list of issue strings.

    Each returned string describes a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    prompt_files = find_prompt_files(manifest_dir)

    if not prompt_files:
        # Not an error — the org may have no custom In-App Guidance metadata
        # or the metadata may not be in this deployment package
        return []

    prompts = [parse_prompt_metadata(f) for f in prompt_files]

    issues.extend(check_parse_errors(prompts))
    issues.extend(check_walkthroughs(prompts))
    issues.extend(check_audience_targeting(prompts))
    issues.extend(check_targeted_prompt_descriptions(prompts))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_in_app_guidance_and_walkthroughs(manifest_dir)

    if not issues:
        print("No In-App Guidance issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    if args.warn_only:
        return 0

    # Exit 1 only if any ERROR-level issues exist
    has_errors = any(
        issue.startswith("ISSUE: ERROR") or issue.startswith("ISSUE: LIMIT")
        for issue in issues
    )
    return 1 if has_errors else 0


if __name__ == "__main__":
    sys.exit(main())
