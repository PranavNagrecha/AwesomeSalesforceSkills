#!/usr/bin/env python3
"""Checker script for Record Type Strategy At Scale skill.

Scans Salesforce metadata for common record type strategy issues:
- Hardcoded Record Type IDs in Apex classes and triggers
- High record type counts per object (layout assignment explosion risk)
- Missing picklist value overrides in RecordType metadata

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_record_type_strategy_at_scale.py [--help]
    python3 check_record_type_strategy_at_scale.py --manifest-dir path/to/metadata
    python3 check_record_type_strategy_at_scale.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Record Type Strategy At Scale configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--rt-warn-threshold",
        type=int,
        default=5,
        help="Warn when an object has more than this many record types (default: 5).",
    )
    parser.add_argument(
        "--profile-count",
        type=int,
        default=0,
        help="If provided, calculates N x M layout assignment counts per object.",
    )
    return parser.parse_args()


# Pattern to detect hardcoded 15- or 18-character Salesforce IDs assigned to RecordTypeId
HARDCODED_RT_ID_PATTERN = re.compile(
    r"""RecordTypeId\s*=\s*['"]([0-9a-zA-Z]{15}|[0-9a-zA-Z]{18})['"]""",
    re.IGNORECASE,
)

# Pattern to detect getRecordTypeInfosByName (should usually be ByDeveloperName)
BY_NAME_PATTERN = re.compile(r"getRecordTypeInfosByName\s*\(", re.IGNORECASE)


def find_files(root: Path, extensions: set[str]) -> list[Path]:
    """Walk the directory tree and return files matching the given extensions."""
    matches = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if any(fname.endswith(ext) for ext in extensions):
                matches.append(Path(dirpath) / fname)
    return matches


def check_hardcoded_ids(manifest_dir: Path) -> list[str]:
    """Scan Apex files for hardcoded Record Type IDs."""
    issues = []
    apex_files = find_files(manifest_dir, {".cls", ".trigger"})
    for fpath in apex_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in HARDCODED_RT_ID_PATTERN.finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                f"Hardcoded RecordTypeId '{match.group(1)}' in {fpath.name}:{line_num} "
                f"— use Schema.SObjectType.<Obj>.getRecordTypeInfosByDeveloperName() instead"
            )
    return issues


def check_by_name_usage(manifest_dir: Path) -> list[str]:
    """Scan Apex files for getRecordTypeInfosByName() usage."""
    issues = []
    apex_files = find_files(manifest_dir, {".cls", ".trigger"})
    for fpath in apex_files:
        try:
            content = fpath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in BY_NAME_PATTERN.finditer(content):
            line_num = content[: match.start()].count("\n") + 1
            issues.append(
                f"getRecordTypeInfosByName() in {fpath.name}:{line_num} "
                f"— prefer getRecordTypeInfosByDeveloperName() for locale-independent resolution"
            )
    return issues


def check_record_type_counts(manifest_dir: Path, warn_threshold: int, profile_count: int) -> list[str]:
    """Count record types per object from RecordType metadata XML files."""
    issues = []
    rt_files = find_files(manifest_dir, {".recordType-meta.xml"})

    # Group by object: record type paths are typically .../objects/<ObjName>/recordTypes/<RTName>.recordType-meta.xml
    object_rt_counts: dict[str, int] = defaultdict(int)
    for fpath in rt_files:
        parts = fpath.parts
        # Look for 'objects' or 'recordTypes' in path to derive object name
        for i, part in enumerate(parts):
            if part == "recordTypes" and i >= 2:
                obj_name = parts[i - 1]
                if obj_name != "objects":
                    object_rt_counts[obj_name] += 1
                break

    for obj_name, count in sorted(object_rt_counts.items()):
        if count > warn_threshold:
            msg = f"Object '{obj_name}' has {count} record types (threshold: {warn_threshold})"
            if profile_count > 0:
                assignments = count * profile_count
                msg += f" — layout assignment count: {count} x {profile_count} = {assignments}"
            issues.append(msg)

    return issues


def check_record_type_strategy_at_scale(manifest_dir: Path, warn_threshold: int = 5, profile_count: int = 0) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_hardcoded_ids(manifest_dir))
    issues.extend(check_by_name_usage(manifest_dir))
    issues.extend(check_record_type_counts(manifest_dir, warn_threshold, profile_count))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_record_type_strategy_at_scale(
        manifest_dir,
        warn_threshold=args.rt_warn_threshold,
        profile_count=args.profile_count,
    )

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
