#!/usr/bin/env python3
"""Checker script for Large Data Volume Architecture skill.

Scans Salesforce metadata for LDV risk signals: very wide custom objects,
heavy sharing rule counts, and SOQL patterns on custom objects that may lack
selective indexed predicates.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_large_data_volume_architecture.py [--help]
    python3 check_large_data_volume_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check metadata for large data volume architecture risk signals.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _strip_ns(tag: str) -> str:
    return re.sub(r"\{[^}]+\}", "", tag)


def _find_elements(root: ET.Element, local_name: str) -> list[ET.Element]:
    results: list[ET.Element] = []
    for elem in root.iter():
        if _strip_ns(elem.tag) == local_name:
            results.append(elem)
    return results


def check_wide_custom_objects(manifest_dir: Path, field_warn: int = 75) -> list[str]:
    """Flag custom objects with very large field counts (wide-row / join cost)."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    for obj_dir in objects_dir.iterdir():
        if not obj_dir.is_dir():
            continue
        if not obj_dir.name.endswith("__c"):
            continue
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue
        n_fields = sum(1 for _ in fields_dir.glob("*.field-meta.xml"))
        if n_fields >= field_warn:
            issues.append(
                f"{obj_dir.name} declares {n_fields} custom fields. "
                f"Very wide objects increase join cost on LDV paths; evaluate column "
                f"pruning, skinny tables (supported types only), or archival boundaries."
            )
    return issues


def check_sharing_rule_weight(manifest_dir: Path, threshold: int = 12) -> list[str]:
    """Warn when any object accumulates many criteria/owner sharing rules."""
    issues: list[str] = []
    sharing_dir = manifest_dir / "sharingRules"
    if not sharing_dir.exists():
        return issues

    for sharing_file in sharing_dir.glob("*.sharingRules-meta.xml"):
        try:
            tree = ET.parse(sharing_file)
            root = tree.getroot()
            rules = _find_elements(root, "sharingOwnerRules") + _find_elements(
                root, "sharingCriteriaRules"
            )
            if len(rules) >= threshold:
                issues.append(
                    f"{sharing_file.name}: {len(rules)} sharing rules. "
                    f"High rule counts amplify sharing recalculation cost at LDV scale."
                )
        except ET.ParseError:
            issues.append(f"Could not parse sharing rules file: {sharing_file}")
    return issues


def check_soql_custom_object_selectivity(manifest_dir: Path) -> list[str]:
    """Heuristic: SOQL on __c objects filtering only on custom fields."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    triggers_dir = manifest_dir / "triggers"
    indexed = re.compile(
        r"(Id|OwnerId|Name|CreatedDate|SystemModstamp|LastModifiedDate|RecordTypeId)\s*[=<>!]",
        re.IGNORECASE,
    )
    soql_pattern = re.compile(
        r"\[SELECT\s+.+?\s+FROM\s+(\w+__c)\s+WHERE\s+(\w+\s*=)",
        re.IGNORECASE | re.DOTALL,
    )

    for check_dir in (classes_dir, triggers_dir):
        if not check_dir.exists():
            continue
        for ext in ("*.cls", "*.trigger"):
            for src in check_dir.glob(ext):
                try:
                    content = src.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for match in soql_pattern.finditer(content):
                    window = content[match.start() : min(match.end() + 240, len(content))]
                    if not indexed.search(window):
                        issues.append(
                            f"{src.name}: SOQL on {match.group(1)} may rely on a "
                            f"non-indexed predicate near '{match.group(2).strip()}' without "
                            f"a standard indexed field conjunction — verify selectivity for LDV."
                        )
    return issues


def check_large_data_volume_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_wide_custom_objects(manifest_dir))
    issues.extend(check_sharing_rule_weight(manifest_dir))
    issues.extend(check_soql_custom_object_selectivity(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_large_data_volume_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
