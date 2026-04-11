#!/usr/bin/env python3
"""Checker script for NPSP Custom Rollups (CRLP) skill.

Validates CRLP-related custom metadata in a Salesforce metadata directory for
common configuration problems documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_npsp_custom_rollups.py [--help]
    python3 check_npsp_custom_rollups.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# CRLP custom metadata file name patterns
ROLLUP_PATTERN = re.compile(r"Customizable_Rollup__mdt\.", re.IGNORECASE)
FILTER_GROUP_PATTERN = re.compile(r"Customizable_Rollup_Filter_Group__mdt\.", re.IGNORECASE)
FILTER_RULES_PATTERN = re.compile(r"Customizable_Rollup_Filter_Rules__mdt\.", re.IGNORECASE)

# Maximum allowed filter group label length (NPSP enforces 40 chars)
FILTER_GROUP_NAME_LIMIT = 40

# NPSP legacy rollup field name prefixes — used to detect references in formula fields
LEGACY_ROLLUP_FIELD_PREFIXES = (
    "npo02__TotalOppAmount__c",
    "npo02__LastCloseDate__c",
    "npo02__NumberOfClosedOpps__c",
    "npo02__TotalOppAmountLastYear__c",
    "npo02__OppAmountLastNDays__c",
    "npo02__OppAmountThisYear__c",
    "npo02__LastMembershipDate__c",
    "npo02__MembershipEndDate__c",
)

# PMM objects — CRLP should not target these
PMM_OBJECTS = (
    "ServiceDelivery__c",
    "ProgramEngagement__c",
    "Service__c",
    "Program__c",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check NPSP CRLP custom metadata for common configuration issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_metadata_files(manifest_dir: Path, pattern: re.Pattern) -> list[Path]:
    """Return all .xml files under manifest_dir whose name matches pattern."""
    results = []
    for xml_file in manifest_dir.rglob("*.xml"):
        if pattern.search(xml_file.name):
            results.append(xml_file)
    return sorted(results)


def extract_xml_value(content: str, tag: str) -> str | None:
    """Return the text content of the first occurrence of <tag>...</tag>, or None."""
    match = re.search(rf"<{tag}>(.*?)</{tag}>", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def check_filter_group_name_lengths(manifest_dir: Path) -> list[str]:
    """Check that all Filter Group labels are 40 characters or fewer."""
    issues: list[str] = []
    filter_group_files = find_metadata_files(manifest_dir, FILTER_GROUP_PATTERN)

    for fg_file in filter_group_files:
        try:
            content = fg_file.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"Could not read {fg_file}: {exc}")
            continue

        label = extract_xml_value(content, "label")
        if label and len(label) > FILTER_GROUP_NAME_LIMIT:
            issues.append(
                f"Filter group name too long ({len(label)} chars, limit {FILTER_GROUP_NAME_LIMIT}): "
                f'"{label}" in {fg_file.name}'
            )
        master_label = extract_xml_value(content, "masterLabel")
        if master_label and len(master_label) > FILTER_GROUP_NAME_LIMIT:
            issues.append(
                f"Filter group masterLabel too long ({len(master_label)} chars, limit {FILTER_GROUP_NAME_LIMIT}): "
                f'"{master_label}" in {fg_file.name}'
            )

    return issues


def check_rollup_definitions_for_pmm_objects(manifest_dir: Path) -> list[str]:
    """Warn if any Rollup Definition targets PMM objects (unsupported by CRLP)."""
    issues: list[str] = []
    rollup_files = find_metadata_files(manifest_dir, ROLLUP_PATTERN)

    for rollup_file in rollup_files:
        try:
            content = rollup_file.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"Could not read {rollup_file}: {exc}")
            continue

        for pmm_obj in PMM_OBJECTS:
            if pmm_obj in content:
                issues.append(
                    f"Rollup Definition {rollup_file.name} references PMM object '{pmm_obj}'. "
                    "CRLP does not support PMM objects — use standard roll-up summary fields or "
                    "scheduled Apex for PMM aggregation."
                )

    return issues


def check_rollup_definitions_have_store_field(manifest_dir: Path) -> list[str]:
    """Warn if any Rollup Definition is missing a Result Field (store field) value."""
    issues: list[str] = []
    rollup_files = find_metadata_files(manifest_dir, ROLLUP_PATTERN)

    for rollup_file in rollup_files:
        try:
            content = rollup_file.read_text(encoding="utf-8")
        except OSError as exc:
            issues.append(f"Could not read {rollup_file}: {exc}")
            continue

        # CRLP metadata uses <resultField> or <Result_Field__c> tags depending on API version
        has_result_field = bool(
            extract_xml_value(content, "resultField")
            or extract_xml_value(content, "Result_Field__c")
        )
        if not has_result_field:
            issues.append(
                f"Rollup Definition {rollup_file.name} appears to be missing a result/store field. "
                "Verify the definition has a target field configured."
            )

    return issues


def check_formula_fields_for_legacy_rollup_references(manifest_dir: Path) -> list[str]:
    """Warn if formula fields reference legacy NPSP rollup fields that CRLP may have zeroed."""
    issues: list[str] = []
    formula_dir = manifest_dir / "objects"
    if not formula_dir.exists():
        return issues

    for xml_file in formula_dir.rglob("*.fieldDefinition-meta.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8")
        except OSError:
            continue
        # Only check formula fields
        if "<type>Formula</type>" not in content:
            continue
        for legacy_field in LEGACY_ROLLUP_FIELD_PREFIXES:
            if legacy_field in content:
                issues.append(
                    f"Formula field {xml_file.name} references legacy NPSP rollup field "
                    f"'{legacy_field}'. If CRLP is enabled without an equivalent rollup definition, "
                    "this field will return stale or zero values. Verify a CRLP rollup definition "
                    "populates this field."
                )

    return issues


def check_npsp_custom_rollups(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_filter_group_name_lengths(manifest_dir))
    issues.extend(check_rollup_definitions_for_pmm_objects(manifest_dir))
    issues.extend(check_rollup_definitions_have_store_field(manifest_dir))
    issues.extend(check_formula_fields_for_legacy_rollup_references(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_npsp_custom_rollups(manifest_dir)

    if not issues:
        print("No CRLP configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
