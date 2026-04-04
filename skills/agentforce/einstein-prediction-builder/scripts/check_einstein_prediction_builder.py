#!/usr/bin/env python3
"""Checker script for Einstein Prediction Builder skill.

This is the canonical entry point. It delegates to check_prediction_builder.py
for all real checks. See check_prediction_builder.py for full documentation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_prediction_builder.py [--help]
    python3 check_einstein_prediction_builder.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Patterns that identify EPB score field references
_APEX_SOQL_PATTERN = re.compile(
    r"EinsteinScoring[A-Za-z0-9_]*__Score__c",
    re.IGNORECASE,
)

_FLOW_FIELD_PATTERN = re.compile(
    r"<field>EinsteinScoring[A-Za-z0-9_]*__Score__c</field>",
    re.IGNORECASE,
)

_CUSTOM_FIELD_EPB_PATTERN = re.compile(
    r"EinsteinScoring[A-Za-z0-9_]*__Score__c",
    re.IGNORECASE,
)

_MAX_ACTIVE_PREDICTIONS = 10
_ACTIVE_PREDICTION_WARNING_THRESHOLD = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Einstein Prediction Builder "
            "configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files(root: Path, suffix: str) -> list[Path]:
    return sorted(root.rglob(f"*{suffix}"))


def check_apex_soql_hardcoded_score_fields(root: Path) -> list[str]:
    issues: list[str] = []
    for apex_file in find_files(root, ".cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        matches = _APEX_SOQL_PATTERN.findall(content)
        if matches:
            unique_fields = sorted(set(matches))
            issues.append(
                f"[APEX] {apex_file.relative_to(root)}: hardcoded EPB score field(s) "
                f"in SOQL — {', '.join(unique_fields)}. "
                f"Score field API name changes if prediction is deleted and recreated. "
                f"Document the field name and confirm it matches the active prediction."
            )
    return issues


def check_flow_score_field_references(root: Path) -> list[str]:
    issues: list[str] = []
    for flow_file in find_files(root, ".flow-meta.xml"):
        try:
            content = flow_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if _FLOW_FIELD_PATTERN.search(content):
            issues.append(
                f"[FLOW] {flow_file.relative_to(root)}: EPB score field in Flow "
                f"filter — will break silently if prediction is recreated."
            )
    return issues


def collect_score_field_references(root: Path) -> list[str]:
    found: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".cls", ".xml", ".flow-meta.xml", ".trigger", ".page"}:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        found.update(m.lower() for m in _CUSTOM_FIELD_EPB_PATTERN.findall(content))
    return sorted(found)


def check_active_prediction_count(score_fields: list[str]) -> list[str]:
    issues: list[str] = []
    count = len(score_fields)
    if count >= _MAX_ACTIVE_PREDICTIONS:
        issues.append(
            f"[LIMIT] {count} unique EPB score field(s) detected. "
            f"Hard limit is {_MAX_ACTIVE_PREDICTIONS} active predictions per org. "
            f"Deactivate unused predictions before creating new ones."
        )
    elif count >= _ACTIVE_PREDICTION_WARNING_THRESHOLD:
        issues.append(
            f"[WARNING] {count} unique EPB score field(s) detected — "
            f"approaching the {_MAX_ACTIVE_PREDICTIONS}-prediction limit."
        )
    return issues


def check_einstein_prediction_builder(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_soql_hardcoded_score_fields(manifest_dir))
    issues.extend(check_flow_score_field_references(manifest_dir))

    score_fields = collect_score_field_references(manifest_dir)
    if score_fields:
        issues.extend(check_active_prediction_count(score_fields))
        print(
            f"INFO: EPB score field(s) found in metadata ({len(score_fields)}): "
            + ", ".join(score_fields)
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_einstein_prediction_builder(manifest_dir)

    if not issues:
        print("No Einstein Prediction Builder issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
