#!/usr/bin/env python3
"""Checker script for Einstein Prediction Builder skill.

Inspects a Salesforce metadata directory for common Einstein Prediction Builder
configuration issues described in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_prediction_builder.py [--help]
    python3 check_prediction_builder.py --manifest-dir path/to/metadata
    python3 check_prediction_builder.py --manifest-dir force-app/main/default

Checks performed:
  1. Detects score fields (EinsteinScoring__ prefix) hardcoded in SOQL inside
     Apex classes — warns that these field names break if a prediction is deleted
     and recreated.
  2. Scans Flow metadata XML for EinsteinScoring field references in filter
     criteria — same breakage risk.
  3. Reports a count of Einstein Prediction-related custom fields found, to help
     practitioners track score field API names across the project.
  4. Warns if more than 8 EinsteinScoring fields are detected (approaching the
     10-active-prediction org limit).
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
    """Return all files under root with the given suffix."""
    return sorted(root.rglob(f"*{suffix}"))


def check_apex_soql_hardcoded_score_fields(root: Path) -> list[str]:
    """Warn when Apex classes contain hardcoded EinsteinScoring score field names."""
    issues: list[str] = []
    apex_files = find_files(root, ".cls")

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        matches = _APEX_SOQL_PATTERN.findall(content)
        if matches:
            unique_fields = sorted(set(matches))
            issues.append(
                f"[APEX] {apex_file.relative_to(root)}: hardcoded EPB score field(s) "
                f"detected in SOQL — {', '.join(unique_fields)}. "
                f"If the prediction is deleted and recreated, the auto-generated field "
                f"API name changes and this query will silently return null. "
                f"Document the score field API name and add a comment confirming it "
                f"matches the active prediction definition."
            )

    return issues


def check_flow_score_field_references(root: Path) -> list[str]:
    """Warn when Flow metadata references EinsteinScoring score fields in filters."""
    issues: list[str] = []
    flow_files = find_files(root, ".flow-meta.xml")

    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        matches = _FLOW_FIELD_PATTERN.findall(content)
        if matches:
            issues.append(
                f"[FLOW] {flow_file.relative_to(root)}: EPB score field reference "
                f"found in Flow filter criteria. If the prediction definition is "
                f"deleted and recreated, this reference will break silently. "
                f"Verify the score field API name matches the active prediction."
            )

    return issues


def collect_score_field_references(root: Path) -> list[str]:
    """Return unique EPB score field API names found anywhere in the metadata."""
    found: set[str] = set()

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in {".cls", ".xml", ".flow-meta.xml", ".trigger", ".page"}:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        matches = _CUSTOM_FIELD_EPB_PATTERN.findall(content)
        found.update(m.lower() for m in matches)

    return sorted(found)


def check_active_prediction_count(score_fields: list[str]) -> list[str]:
    """Warn if the number of unique score fields approaches the 10-prediction limit."""
    issues: list[str] = []
    count = len(score_fields)

    if count >= _MAX_ACTIVE_PREDICTIONS:
        issues.append(
            f"[LIMIT] {count} unique EPB score field(s) detected across metadata. "
            f"Einstein Prediction Builder has a hard limit of {_MAX_ACTIVE_PREDICTIONS} "
            f"active predictions per org. Deactivate unused predictions before "
            f"creating new ones."
        )
    elif count >= _ACTIVE_PREDICTION_WARNING_THRESHOLD:
        issues.append(
            f"[WARNING] {count} unique EPB score field(s) detected. "
            f"The org is approaching the {_MAX_ACTIVE_PREDICTIONS}-active-prediction limit. "
            f"Review and deactivate unused predictions before the limit is reached."
        )

    return issues


def check_prediction_builder(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: Hardcoded score field API names in Apex SOQL
    issues.extend(check_apex_soql_hardcoded_score_fields(manifest_dir))

    # Check 2: Score field references in Flow filter criteria
    issues.extend(check_flow_score_field_references(manifest_dir))

    # Check 3: Collect all score field references and check active prediction count
    score_fields = collect_score_field_references(manifest_dir)
    if score_fields:
        issues.extend(check_active_prediction_count(score_fields))

        # Report all discovered score field names for documentation purposes
        print(
            f"INFO: EPB score field(s) found in metadata ({len(score_fields)}): "
            + ", ".join(score_fields)
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_prediction_builder(manifest_dir)

    if not issues:
        print("No Einstein Prediction Builder issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
