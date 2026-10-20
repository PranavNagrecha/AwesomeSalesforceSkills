#!/usr/bin/env python3
"""Checker script for Sharing Recalculation Performance skill.

Checks Salesforce metadata for sharing recalculation risk patterns:
- Criteria-based sharing rules (SharingCriteriaRule, element sharingCriteriaRules with
  criteriaItems, api_meta 264 L132843, L132857-132865) on commonly high-churn fields
- Objects with Apex sharing reasons but no sharingRecalculations/className entry
  (SharingRecalculation, api_meta 264 L47714-47720)

Both rules are advisory (WARN): the claims behind them are Help-level and UNVERIFIED
(2026-10-20) against the corpus. Earlier versions of this script read the wrong
elements and could not match real metadata: filterItems instead of criteriaItems, and a
per-reason recalculateClassName element that SharingReason does not have (it has only
fullName and label, api_meta 264 L47656-47664).

Exit codes: ERROR findings (unparseable XML, missing --manifest-dir) exit 1 always; WARN
findings exit 0 unless --strict is given. A directory with no sharing rules or object
files prints one WARN and exits 0.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sharing_recalculation_performance.py [--help]
    python3 check_sharing_recalculation_performance.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Fields that are commonly updated in bulk. Using them in criteria-based sharing rules is
# a review item, not a documented limit (UNVERIFIED (2026-10-20)).
HIGH_CHURN_FIELDS = {
    "Status",
    "Stage",
    "StageName",
    "Rating",
    "Priority",
    "LeadSource",
    "AccountSource",
    "ForecastCategoryName",
}

SF_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for sharing recalculation performance risks. "
            "Looks for criteria-based sharing rules on high-churn fields and objects with "
            "Apex sharing reasons but no sharing recalculation class."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN findings to exit 1 (ERROR always exits 1).",
    )
    return parser.parse_args()


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def _text(parent: ET.Element, name: str) -> str:
    child = parent.find(_tag(name))
    if child is not None and child.text:
        return child.text.strip()
    return ""


def _load(path: Path, findings: list[str]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(f"ERROR: could not parse {path.name}: {exc}")
        return None


def sharing_rule_files(manifest_dir: Path) -> list[Path]:
    root = manifest_dir / "sharingRules"
    if not root.exists():
        return []
    return sorted(set(root.glob("*.sharingRules")) | set(root.glob("*.sharingRules-meta.xml")))


def object_files(manifest_dir: Path) -> list[Path]:
    root = manifest_dir / "objects"
    if not root.exists():
        return []
    return sorted(set(root.glob("*.object")) | set(root.glob("*/*.object-meta.xml")))


def check_sharing_rules(manifest_dir: Path) -> list[str]:
    findings: list[str] = []
    for xml_file in sharing_rule_files(manifest_dir):
        root = _load(xml_file, findings)
        if root is None:
            continue
        object_name = xml_file.name.split(".")[0]
        for rule in root.findall(_tag("sharingCriteriaRules")):
            rule_label = _text(rule, "label") or _text(rule, "fullName") or "(no label)"
            items = rule.findall(_tag("criteriaItems")) + rule.findall(_tag("filterItems"))
            for item in items:
                bare_field = _text(item, "field").split(".")[-1]
                if bare_field in HIGH_CHURN_FIELDS:
                    findings.append(
                        f"WARN: criteria-based sharing rule '{rule_label}' on {object_name} uses "
                        f"high-churn field '{bare_field}'. Bulk updates to this field may be "
                        f"expensive to re-evaluate (UNVERIFIED (2026-10-20): Help-level, not in the "
                        f"corpus). Consider a role- or group-based rule."
                    )
    return findings


def check_apex_sharing_reasons(manifest_dir: Path) -> list[str]:
    findings: list[str] = []
    for obj_file in object_files(manifest_dir):
        root = _load(obj_file, findings)
        if root is None:
            continue
        if obj_file.name.endswith(".object-meta.xml"):
            object_name = obj_file.parent.name
            sibling = obj_file.parent
        else:
            object_name = obj_file.stem
            sibling = None

        reasons = [_text(r, "fullName") or "(unnamed)" for r in root.findall(_tag("sharingReasons"))]
        has_class = any(_text(r, "className") for r in root.findall(_tag("sharingRecalculations")))
        if sibling is not None:
            for reason_file in sorted((sibling / "sharingReasons").glob("*.sharingReason-meta.xml")):
                reasons.append(reason_file.name.split(".")[0])
            recalcs_dir = sibling / "sharingRecalculations"
            if recalcs_dir.is_dir() and any(recalcs_dir.iterdir()):
                has_class = True
        if reasons and not has_class:
            findings.append(
                f"WARN: {object_name} has Apex sharing reason(s) {', '.join(sorted(set(reasons)))} "
                f"but no sharingRecalculations/className entry. Associate a Database.Batchable "
                f"class in the object's Apex Sharing Recalculations (apexdev 264 L13054-13055, "
                f"L13346-13351; api_meta 264 L47714-47720). That its absence silently deletes "
                f"Apex share rows is UNVERIFIED (2026-10-20)."
            )
    return findings


def check_sharing_recalculation_performance(manifest_dir: Path) -> list[str]:
    findings: list[str] = []

    if not manifest_dir.exists():
        findings.append(f"ERROR: Manifest directory not found: {manifest_dir}")
        return findings

    if not sharing_rule_files(manifest_dir) and not object_files(manifest_dir):
        findings.append(
            f"WARN: no sharingRules/ or objects/ metadata under {manifest_dir}; nothing to check"
        )
        return findings

    findings.extend(check_sharing_rules(manifest_dir))
    findings.extend(check_apex_sharing_reasons(manifest_dir))
    return findings


def main() -> int:
    args = parse_args()
    findings = check_sharing_recalculation_performance(Path(args.manifest_dir))

    if not findings:
        print("No sharing recalculation performance issues found.")
        return 0

    for finding in findings:
        print(finding)

    if any(f.startswith("ERROR:") for f in findings):
        sys.exit(1)
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
