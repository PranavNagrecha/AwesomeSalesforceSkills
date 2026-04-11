#!/usr/bin/env python3
"""Checker script for Data Cloud Data Streams skill.

Validates a Salesforce metadata directory for common Data Cloud data stream
configuration issues, including:
  - Missing Individual DMO mappings in data stream metadata
  - Missing Contact Point DMO mappings (required for identity resolution)
  - Ingestion API configurations that reference delete operations
  - Identity resolution ruleset count exceeding the org limit of 2

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_data_streams.py [--help]
    python3 check_data_cloud_data_streams.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import json
import re
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def _read_text(path: Path) -> str:
    """Return file contents as a string, or empty string on error."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_identity_ruleset_count(manifest_dir: Path) -> list[str]:
    """Warn if more than 2 identity resolution ruleset files are found.

    Data Cloud enforces a hard org-level limit of 2 identity resolution
    rulesets. Exceeding this in metadata indicates the design exceeds the
    platform limit.
    """
    issues: list[str] = []

    # Look for common identity resolution ruleset metadata file patterns.
    # Salesforce DX projects may use .json or .xml for these artifacts.
    ruleset_patterns = [
        "*.identityResolutionProcedure",
        "*.identityResolutionProcedure-meta.xml",
        "*IdentityResolutionRuleset*.json",
        "*identity_resolution*.json",
        "*identity_resolution*.xml",
    ]

    found: list[Path] = []
    for pattern in ruleset_patterns:
        found.extend(_find_files(manifest_dir, pattern))

    # Deduplicate by resolved path
    unique = list({f.resolve(): f for f in found}.values())

    if len(unique) > 2:
        paths = ", ".join(str(p.relative_to(manifest_dir)) for p in unique[:5])
        issues.append(
            f"Found {len(unique)} identity resolution ruleset file(s) — "
            f"Data Cloud allows a maximum of 2 per org. "
            f"Files: {paths}"
        )

    return issues


def check_ingestion_api_delete_mode(manifest_dir: Path) -> list[str]:
    """Detect Ingestion API payloads or configurations that reference delete mode.

    The Data Cloud Ingestion API supports only 'append' and 'upsert' modes.
    A 'delete' mode specification indicates an unsupported operation.
    """
    issues: list[str] = []

    # Search JSON and Python/JS integration files for delete mode references
    target_extensions = ["*.json", "*.py", "*.js", "*.ts", "*.yaml", "*.yml"]
    delete_pattern = re.compile(
        r'"mode"\s*:\s*"delete"'
        r'|'
        r"'mode'\s*:\s*'delete'"
        r'|'
        r'mode\s*=\s*["\']delete["\']',
        re.IGNORECASE,
    )

    for ext in target_extensions:
        for fpath in _find_files(manifest_dir, ext):
            content = _read_text(fpath)
            if delete_pattern.search(content):
                rel = fpath.relative_to(manifest_dir)
                issues.append(
                    f"Potential Ingestion API delete mode found in {rel} — "
                    "the Data Cloud Ingestion API does not support 'delete' operations. "
                    "Use the Data Cloud bulk delete facility instead."
                )

    return issues


def check_individual_dmo_mapping(manifest_dir: Path) -> list[str]:
    """Check data stream mapping files for Individual DMO configuration.

    Looks for JSON/XML mapping files and warns if a mapping that mentions
    'Individual' does not also reference a Contact Point or Party Identification
    DMO, which is required for identity resolution.
    """
    issues: list[str] = []

    mapping_patterns = [
        "*dataStreamMapping*.json",
        "*DataStreamMapping*.json",
        "*dmo_mapping*.json",
        "*DmoMapping*.json",
        "*dataStreamDef*.json",
    ]

    for pattern in mapping_patterns:
        for fpath in _find_files(manifest_dir, pattern):
            content = _read_text(fpath)
            if not content:
                continue

            has_individual = bool(
                re.search(r'"Individual"', content, re.IGNORECASE)
                or re.search(r'IndividualDmo', content, re.IGNORECASE)
            )
            has_contact_point = bool(
                re.search(r'ContactPoint', content, re.IGNORECASE)
                or re.search(r'Contact_Point', content, re.IGNORECASE)
                or re.search(r'"ContactPointEmail"', content, re.IGNORECASE)
                or re.search(r'"ContactPointPhone"', content, re.IGNORECASE)
            )
            has_party_id = bool(
                re.search(r'PartyIdentification', content, re.IGNORECASE)
                or re.search(r'Party_Identification', content, re.IGNORECASE)
            )

            if has_individual and not (has_contact_point or has_party_id):
                rel = fpath.relative_to(manifest_dir)
                issues.append(
                    f"Data stream mapping {rel} references Individual DMO but no "
                    "Contact Point DMO or Party Identification DMO mapping was found. "
                    "Identity resolution rulesets cannot be created without at least "
                    "one Contact Point or Party Identification DMO mapping."
                )

    return issues


def check_party_identification_id_misuse(manifest_dir: Path) -> list[str]:
    """Detect mappings that assign an external field to Party Identification ID.

    The 'Party Identification ID' field is a Data Cloud internal system key.
    External IDs (loyalty numbers, ERP IDs) must be mapped to 'Identification Number'
    instead. Mapping to 'Party Identification ID' causes data corruption.
    """
    issues: list[str] = []

    # Pattern: a source field being mapped to "Party Identification ID"
    # This can appear in various mapping JSON shapes.
    bad_pattern = re.compile(
        r'["\']Party\s*Identification\s*ID["\']',
        re.IGNORECASE,
    )

    for fpath in _find_files(manifest_dir, "*.json"):
        content = _read_text(fpath)
        if bad_pattern.search(content):
            rel = fpath.relative_to(manifest_dir)
            issues.append(
                f"Possible 'Party Identification ID' mapping in {rel}. "
                "This field is a Data Cloud internal system key — do not map "
                "external IDs to it. Use 'Identification Number' for external "
                "identifiers such as loyalty IDs or ERP customer numbers."
            )

    return issues


def check_calculated_insight_base_object(manifest_dir: Path) -> list[str]:
    """Warn if Calculated Insight SQL queries reference raw DLO objects rather than
    Unified Individual as the base.

    Calculated Insights for segmentation should be anchored to the
    UnifiedIndividual__dlm object to ensure metrics are tied to merged profiles.
    """
    issues: list[str] = []

    ci_patterns = ["*CalculatedInsight*.sql", "*calculated_insight*.sql"]

    for pattern in ci_patterns:
        for fpath in _find_files(manifest_dir, pattern):
            content = _read_text(fpath)
            if not content:
                continue

            has_unified_individual = bool(
                re.search(r'UnifiedIndividual', content, re.IGNORECASE)
            )
            has_from_clause = bool(re.search(r'\bFROM\b', content, re.IGNORECASE))

            if has_from_clause and not has_unified_individual:
                rel = fpath.relative_to(manifest_dir)
                issues.append(
                    f"Calculated Insight SQL in {rel} does not reference "
                    "UnifiedIndividual__dlm as the base object. Segmentation "
                    "insights should be anchored to the Unified Individual DMO "
                    "to ensure metrics are computed against merged profiles, "
                    "not raw DLO records."
                )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata directory for common Data Cloud "
            "data stream configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_data_cloud_data_streams(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_identity_ruleset_count(manifest_dir))
    issues.extend(check_ingestion_api_delete_mode(manifest_dir))
    issues.extend(check_individual_dmo_mapping(manifest_dir))
    issues.extend(check_party_identification_id_misuse(manifest_dir))
    issues.extend(check_calculated_insight_base_object(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_cloud_data_streams(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
