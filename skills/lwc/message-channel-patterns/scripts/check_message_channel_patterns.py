#!/usr/bin/env python3
"""Checker script for Message Channel Patterns skill.

Validates Lightning Message Channel XML metadata files in a Salesforce DX project
for common structural and configuration issues documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_message_channel_patterns.py [--manifest-dir path/to/metadata]

Examples:
    python3 check_message_channel_patterns.py --manifest-dir force-app/main/default
    python3 check_message_channel_patterns.py --manifest-dir .
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce Metadata API XML namespace for LightningMessageChannel
LMC_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"
LMC_FILE_SUFFIX = ".messageChannel-meta.xml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate LightningMessageChannel metadata files for common LMS issues. "
            "Checks isExposed, masterLabel, field names, and XML structure."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce DX project or metadata folder (default: current directory).",
    )
    return parser.parse_args()


def find_message_channel_files(manifest_dir: Path) -> list[Path]:
    """Recursively find all .messageChannel-meta.xml files under manifest_dir."""
    return list(manifest_dir.rglob(f"*{LMC_FILE_SUFFIX}"))


def validate_channel_file(channel_file: Path) -> list[str]:
    """Validate a single message channel XML file. Returns list of issue strings."""
    issues: list[str] = []
    file_label = str(channel_file)

    try:
        tree = ET.parse(channel_file)
    except ET.ParseError as exc:
        issues.append(f"{file_label}: XML parse error — {exc}")
        return issues

    root = tree.getroot()

    # Validate root tag
    expected_tag = f"{{{LMC_NAMESPACE}}}LightningMessageChannel"
    if root.tag != expected_tag:
        issues.append(
            f"{file_label}: root element is <{root.tag}>, expected <LightningMessageChannel> "
            f"with namespace {LMC_NAMESPACE}"
        )
        return issues

    def get_text(tag: str) -> str | None:
        el = root.find(f"{{{LMC_NAMESPACE}}}{tag}")
        return el.text.strip() if el is not None and el.text else None

    # --- masterLabel ---
    master_label = get_text("masterLabel")
    if not master_label:
        issues.append(
            f"{file_label}: missing or empty <masterLabel>. "
            "Every LightningMessageChannel must have a human-readable masterLabel."
        )

    # --- isExposed ---
    is_exposed_text = get_text("isExposed")
    if is_exposed_text is None:
        issues.append(
            f"{file_label}: missing <isExposed>. "
            "Set to 'false' unless cross-namespace access is intentionally required."
        )
    elif is_exposed_text.lower() not in ("true", "false"):
        issues.append(
            f"{file_label}: <isExposed> value '{is_exposed_text}' is not a valid boolean. "
            "Use 'true' or 'false'."
        )
    elif is_exposed_text.lower() == "true":
        issues.append(
            f"{file_label}: <isExposed> is 'true'. "
            "This exposes the channel to other namespaces. "
            "Verify this is intentional — AppExchange security review flags isExposed=true. "
            "If this is an internal channel, set isExposed to 'false'."
        )

    # --- lightningMessageFields ---
    fields = root.findall(f"{{{LMC_NAMESPACE}}}lightningMessageFields")
    seen_field_names: set[str] = set()

    for field_el in fields:
        field_name_el = field_el.find(f"{{{LMC_NAMESPACE}}}fieldName")
        field_name = field_name_el.text.strip() if field_name_el is not None and field_name_el.text else None

        if not field_name:
            issues.append(
                f"{file_label}: a <lightningMessageFields> block is missing a <fieldName>. "
                "Each field declaration must have a non-empty fieldName."
            )
            continue

        # Duplicate field name check
        if field_name in seen_field_names:
            issues.append(
                f"{file_label}: duplicate <fieldName> '{field_name}'. "
                "Each field name must be unique within a message channel."
            )
        seen_field_names.add(field_name)

        # Field name format: should be camelCase or snake_case; warn about __c suffix
        if field_name.endswith("__c"):
            issues.append(
                f"{file_label}: field name '{field_name}' ends with '__c'. "
                "LightningMessageChannel field names are plain strings, not API names — "
                "remove the '__c' suffix."
            )

        # Warn if no description for a field
        field_desc_el = field_el.find(f"{{{LMC_NAMESPACE}}}description")
        field_desc = field_desc_el.text.strip() if field_desc_el is not None and field_desc_el.text else None
        if not field_desc:
            issues.append(
                f"{file_label}: field '{field_name}' has no <description>. "
                "Add a description to document what this field carries in the payload."
            )

    # --- File name vs masterLabel consistency warning ---
    # File name (without suffix) should loosely match or be derivable from masterLabel
    stem = channel_file.name.replace(LMC_FILE_SUFFIX, "")
    if master_label and not (
        stem.lower().replace("-", "").replace("_", "") ==
        master_label.lower().replace(" ", "").replace("-", "").replace("_", "")
    ):
        issues.append(
            f"{file_label}: file stem '{stem}' does not match masterLabel '{master_label}'. "
            "Consider aligning the file name and masterLabel for maintainability."
        )

    return issues


def check_message_channel_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found across all message channel files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    channel_files = find_message_channel_files(manifest_dir)

    if not channel_files:
        issues.append(
            f"No {LMC_FILE_SUFFIX} files found under '{manifest_dir}'. "
            "If message channels are expected, verify the directory path and file naming convention: "
            "<channelName>.messageChannel-meta.xml"
        )
        return issues

    for channel_file in sorted(channel_files):
        file_issues = validate_channel_file(channel_file)
        issues.extend(file_issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_message_channel_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
