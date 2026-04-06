#!/usr/bin/env python3
"""Checker script for High Volume Sales Data Architecture skill.

Scans Salesforce metadata for indicators of data skew risk, missing archival
patterns, and non-selective query patterns in sales objects.
Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_high_volume_sales_data_architecture.py [--help]
    python3 check_high_volume_sales_data_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check High Volume Sales Data Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag."""
    return re.sub(r"\{[^}]+\}", "", tag)


def _find_elements(root: ET.Element, local_name: str) -> list[ET.Element]:
    """Find all elements matching a local name regardless of namespace."""
    results = []
    for elem in root.iter():
        if _strip_ns(elem.tag) == local_name:
            results.append(elem)
    return results


def check_sharing_rules(manifest_dir: Path) -> list[str]:
    """Check for excessive sharing rules on Account and Opportunity."""
    issues: list[str] = []
    sharing_dir = manifest_dir / "sharingRules"
    if not sharing_dir.exists():
        return issues

    for obj_name in ("Account", "Opportunity"):
        sharing_file = sharing_dir / f"{obj_name}.sharingRules-meta.xml"
        if not sharing_file.exists():
            continue
        try:
            tree = ET.parse(sharing_file)
            root = tree.getroot()
            rules = _find_elements(root, "sharingOwnerRules") + _find_elements(root, "sharingCriteriaRules")
            if len(rules) > 10:
                issues.append(
                    f"{obj_name} has {len(rules)} sharing rules. "
                    f"High rule count increases sharing recalculation cost on skewed ownership. "
                    f"Review whether ownership redistribution can reduce rule count."
                )
        except ET.ParseError:
            issues.append(f"Could not parse sharing rules file: {sharing_file}")

    return issues


def check_big_object_presence(manifest_dir: Path) -> list[str]:
    """Check whether an archival Big Object exists for Opportunity."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    big_object_pattern = re.compile(r"(?i)archiv.*opportunit.*__b", re.IGNORECASE)
    found_archival_big_object = False

    for item in objects_dir.iterdir():
        if big_object_pattern.search(item.name):
            found_archival_big_object = True
            break

    # Also check top-level for .object-meta.xml files
    for item in manifest_dir.rglob("*__b.object-meta.xml"):
        if "opportunit" in item.name.lower() or "archiv" in item.name.lower():
            found_archival_big_object = True
            break

    # This is advisory, not a hard failure -- only flag if Opportunity object exists
    opp_dir = objects_dir / "Opportunity"
    if opp_dir.exists() and not found_archival_big_object:
        issues.append(
            "No archival Big Object found for Opportunity data. "
            "Consider creating an Archived_Opportunity__b Big Object for long-term "
            "storage of closed historical Opportunities."
        )

    return issues


def check_soql_selectivity_patterns(manifest_dir: Path) -> list[str]:
    """Scan Apex classes for non-selective query patterns on sales objects."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    # Pattern: SOQL on Opportunity or Account with a single custom field filter
    # and no indexed field conjunction
    soql_pattern = re.compile(
        r"\[SELECT\s+.+?\s+FROM\s+(Opportunity|Account)\s+WHERE\s+(\w+__c\s*=)",
        re.IGNORECASE | re.DOTALL,
    )
    indexed_fields = re.compile(
        r"(Id|Name|OwnerId|CreatedDate|SystemModstamp|CloseDate|AccountId|LastModifiedDate)\s*[=<>!]",
        re.IGNORECASE,
    )

    for cls_file in classes_dir.glob("*.cls"):
        try:
            content = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for match in soql_pattern.finditer(content):
            full_where = content[match.start():min(match.end() + 200, len(content))]
            # Check if the WHERE clause includes at least one indexed field
            if not indexed_fields.search(full_where):
                issues.append(
                    f"{cls_file.name}: SOQL on {match.group(1)} filters only on "
                    f"custom field '{match.group(2).strip()}' without an indexed field conjunction. "
                    f"This may be non-selective on high-volume tables."
                )

    return issues


def check_owner_assignment_patterns(manifest_dir: Path) -> list[str]:
    """Detect patterns that assign all records to a single integration user."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    triggers_dir = manifest_dir / "triggers"

    dirs_to_check = [d for d in [classes_dir, triggers_dir] if d.exists()]
    if not dirs_to_check:
        return issues

    # Look for hardcoded OwnerId assignment to a single user in batch contexts
    owner_assign_pattern = re.compile(
        r"\.\s*OwnerId\s*=\s*['\"]005[A-Za-z0-9]{12,15}['\"]",
    )

    for check_dir in dirs_to_check:
        for source_file in check_dir.glob("*.cls"):
            try:
                content = source_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            matches = owner_assign_pattern.findall(content)
            if len(matches) > 0:
                issues.append(
                    f"{source_file.name}: Hardcoded OwnerId assignment detected. "
                    f"Assigning records to a single user risks ownership skew. "
                    f"Use territory-based queues or dynamic assignment instead."
                )

    return issues


def check_high_volume_sales_data_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sharing_rules(manifest_dir))
    issues.extend(check_big_object_presence(manifest_dir))
    issues.extend(check_soql_selectivity_patterns(manifest_dir))
    issues.extend(check_owner_assignment_patterns(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_high_volume_sales_data_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
