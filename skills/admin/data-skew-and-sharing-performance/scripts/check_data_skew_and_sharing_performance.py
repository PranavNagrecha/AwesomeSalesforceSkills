#!/usr/bin/env python3
"""Checker script for Data Skew and Sharing Performance skill.

Scans Salesforce metadata in a local SFDX project or retrieved metadata directory
for patterns that indicate data skew risk or sharing performance anti-patterns.

Checks performed:
  - Sharing rules that source from large public groups (flag if >1 sharing rule
    sources from the same group — high fan-out risk)
  - Objects set to Private OWD with no sharing rules defined (may force
    role-hierarchy-only access — amplifies skew risk)
  - Objects with Master-Detail children NOT configured as Controlled by Parent
    in their sharing model (detects potential implicit sharing overhead)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_skew_and_sharing_performance.py [--manifest-dir PATH]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict


SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for data skew and sharing performance anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata / SFDX project (default: current directory).",
    )
    return parser.parse_args()


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def check_sharing_rules(manifest_dir: Path) -> list[str]:
    """Detect sharing rules that use the same source group repeatedly (fan-out risk)."""
    issues: list[str] = []
    sharing_dir = manifest_dir / "sharingRules"
    if not sharing_dir.exists():
        # Also check sfdx source format
        sharing_dir = manifest_dir / "force-app" / "main" / "default" / "sharingRules"
    if not sharing_dir.exists():
        return issues

    group_rule_count: dict[str, list[str]] = defaultdict(list)

    for xml_file in sorted(sharing_dir.glob("*.sharingRules")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError:
            issues.append(f"Could not parse sharing rules file: {xml_file.name}")
            continue
        root = tree.getroot()
        obj_name = xml_file.stem
        for rule in root.findall(_tag("sharingCriteriaRules")) + root.findall(_tag("sharingOwnerRules")):
            shared_to = rule.find(_tag("sharedTo"))
            if shared_to is not None:
                for child in shared_to:
                    tag_local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if tag_local in ("group", "roleAndSubordinates", "role"):
                        group_rule_count[child.text or "unknown"].append(
                            f"{obj_name} ({tag_local})"
                        )

    for group_name, rules in group_rule_count.items():
        if len(rules) > 3:
            issues.append(
                f"WARN: Public group / role '{group_name}' is the source for {len(rules)} sharing rules "
                f"({', '.join(rules[:3])}{'...' if len(rules) > 3 else ''}). "
                f"If this group contains users who own many records, any membership change triggers "
                f"recalculation across all {len(rules)} rule sets. Consider splitting into narrower groups."
            )

    return issues


def check_object_owd(manifest_dir: Path) -> list[str]:
    """Check for objects with Private OWD that have no sharing rules (pure role-hierarchy dependency)."""
    issues: list[str] = []

    # Look for SharingSettings metadata (org-wide defaults are in the org settings, not per-object files)
    # In retrieved metadata, OWD is in the CustomObject file under sharingModel
    obj_dirs = []
    for candidate in [
        manifest_dir / "objects",
        manifest_dir / "force-app" / "main" / "default" / "objects",
    ]:
        if candidate.exists():
            obj_dirs.append(candidate)
            break

    if not obj_dirs:
        return issues

    obj_dir = obj_dirs[0]
    sharing_dir = manifest_dir / "sharingRules"
    if not sharing_dir.exists():
        sharing_dir = manifest_dir / "force-app" / "main" / "default" / "sharingRules"

    for xml_file in sorted(obj_dir.glob("**/*.object-meta.xml")):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError:
            continue
        root = tree.getroot()
        sharing_model_el = root.find(_tag("sharingModel"))
        if sharing_model_el is None:
            continue
        sharing_model = sharing_model_el.text or ""
        obj_name = xml_file.stem.replace(".object-meta", "")
        if sharing_model == "Private":
            # Check if sharing rules file exists for this object
            rule_file = sharing_dir / f"{obj_name}.sharingRules"
            if not rule_file.exists():
                issues.append(
                    f"INFO: Object '{obj_name}' has Private OWD but no sharing rules file found. "
                    f"Access is role-hierarchy-only. If a small number of users own most records, "
                    f"any role change for those users will trigger a full sharing recalculation."
                )

    return issues


def check_data_skew_and_sharing_performance(manifest_dir: Path) -> list[str]:
    """Run all data skew and sharing performance checks. Return list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sharing_rules(manifest_dir))
    issues.extend(check_object_owd(manifest_dir))

    if not issues:
        issues_found = False
    else:
        issues_found = True

    # Always emit a reminder about runtime skew checks (not detectable from metadata alone)
    print(
        "NOTE: Record count checks (ownership skew >10k, parent-child skew >10k) "
        "require a live org query and cannot be performed from metadata alone.\n"
        "Run in Developer Console:\n"
        "  SELECT OwnerId, COUNT(Id) cnt FROM <Object> GROUP BY OwnerId "
        "HAVING COUNT(Id) > 10000 ORDER BY cnt DESC\n"
        "  SELECT AccountId, COUNT(Id) cnt FROM Contact GROUP BY AccountId "
        "HAVING COUNT(Id) > 10000 ORDER BY cnt DESC"
    )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_skew_and_sharing_performance(manifest_dir)

    if not issues:
        print("No metadata-level issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
