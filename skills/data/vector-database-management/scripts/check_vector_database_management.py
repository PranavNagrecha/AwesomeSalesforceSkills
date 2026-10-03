#!/usr/bin/env python3
"""Checker script for Vector Database Management skill.

Checks org metadata relevant to Data Cloud search indexes (vector stores).
Uses stdlib only, no pip dependencies.

Rules and the Summer '26 (262) source each one encodes:
  WARN  No DataStreamDefinition retrieved. The search index's source object is fed by a
        data stream whose refresh mode (Incremental, Upsert, Full Refresh) decides freshness.
        Data Cloud guide, "Data Stream Settings and Refresh Modes."
  WARN  A DataStreamDefinition with dataExtractMethods FULL_REFRESH. Full Refresh deletes
        and replaces all data each cycle. Same source; Metadata API, DataStreamDefinition.
  WARN  No DataSpaceDefinition retrieved. A search index is defined in a data space.
        Data Cloud guide, "Retrievers" and "Manage Search Indexes."
  WARN  Field references whose names match personal-data patterns. Every chunked field is
        copied into the chunk DMO. Data Cloud guide, "Chunk and Index Data Model Objects."
  WARN  More than one distinct embedding model reference. The embedding model is view-only
        after creation. Data Cloud guide, "Edit Search Index Configurations."

Usage:
    python3 check_vector_database_management.py [--help]
    python3 check_vector_database_management.py --manifest-dir path/to/metadata
    python3 check_vector_database_management.py --self-test
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# ─── PII field name patterns (case-insensitive substring match) ───────────────
# Expand this list to match org naming conventions.
PII_FIELD_PATTERNS: list[str] = [
    "email",
    "phone",
    "ssn",
    "social_security",
    "birthdate",
    "dob",
    "taxid",
    "tax_id",
    "creditcard",
    "credit_card",
    "passport",
    "nationalid",
    "national_id",
    "healthrecord",
    "health_record",
    "firstname",
    "first_name",
    "lastname",
    "last_name",
    "fullname",
    "full_name",
]

# Metadata type names expected for Data Cloud vector index setups
REQUIRED_METADATA_TYPES: list[str] = [
    "DataStreamDefinition",
    "DataSpaceDefinition",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Vector Database Management issues:\n"
            "  - DataStreamDefinition presence (required for vector index refresh)\n"
            "  - DataSpaceDefinition presence (required for Data Cloud)\n"
            "  - PII field names that may be included in a vector index\n"
            "  - Potential embedding model change risk\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument("--self-test", action="store_true", help="Run against scripts/fixtures/good and bad.")
    return parser.parse_args()


# ─── Individual checks ────────────────────────────────────────────────────────

def check_data_stream_definition(manifest_dir: Path) -> list[str]:
    """Warn if no DataStreamDefinition metadata files are found in the manifest."""
    issues: list[str] = []
    # DataStreamDefinition files live under dataStreamDefinitions/ with .dataStreamDefinition extension
    candidates = list(manifest_dir.rglob("*.dataStreamDefinition")) + list(manifest_dir.rglob("*.dataStreamDefinition-meta.xml"))
    if not candidates:
        issues.append(
            "No DataStreamDefinition metadata found in the manifest. "
            "The data stream feeding the search index's source object sets its refresh mode "
            "(Incremental, Upsert, or Full Refresh) and schedule, which decide index freshness. "
            "Ensure it is included in the package.xml and retrieved before configuring "
            "the vector index refresh cadence."
        )
    return issues


def check_data_space_definition(manifest_dir: Path) -> list[str]:
    """Warn if no DataSpaceDefinition metadata files are found in the manifest."""
    issues: list[str] = []
    candidates = list(manifest_dir.rglob("*.dataSpaceDefinition")) + list(manifest_dir.rglob("*.dataSpaceDefinition-meta.xml"))
    if not candidates:
        issues.append(
            "No DataSpaceDefinition metadata found in the manifest. "
            "A search index is defined in a data space and tied to one data model object. "
            "Confirm Data Cloud is provisioned and retrieve DataSpaceDefinition metadata."
        )
    return issues


def check_pii_fields_in_metadata(manifest_dir: Path) -> list[str]:
    """Scan metadata XML for field names matching known PII patterns.

    This is a heuristic scan — it flags field name strings that match PII
    patterns in any XML metadata file. Review each flagged field to determine
    whether it is included in a vector index field list.
    """
    issues: list[str] = []
    xml_files = list(manifest_dir.rglob("*.xml"))

    flagged: list[tuple[str, str, str]] = []  # (file, line_content, matched_pattern)

    for xml_file in xml_files:
        try:
            text = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            line_lower = line.lower()
            # Only inspect lines that look like field references
            if "<field>" not in line_lower and "fieldname" not in line_lower and "<name>" not in line_lower:
                continue
            for pattern in PII_FIELD_PATTERNS:
                if pattern in line_lower:
                    flagged.append((str(xml_file.relative_to(manifest_dir)), line.strip(), pattern))
                    break  # one pattern match per line is enough

    if flagged:
        issues.append(
            f"Found {len(flagged)} field reference(s) in metadata that match PII name patterns. "
            "Every chunked field is copied into the chunk DMO and embedded. Keep personal-data "
            "fields out of search index chunking (UNVERIFIED 2026-10-03: whether retrievers "
            "enforce source field-level security). Confirm these fields are not chunked:"
        )
        for relative_path, line_content, pattern in flagged[:20]:  # cap at 20 to avoid noise
            issues.append(f"  [{pattern}] {relative_path}: {line_content[:120]}")
        if len(flagged) > 20:
            issues.append(f"  ... and {len(flagged) - 20} more. Run with a narrower --manifest-dir to reduce scope.")

    return issues


def check_embedding_model_change_risk(manifest_dir: Path) -> list[str]:
    """Warn if multiple distinct embedding model references are found.

    If more than one embedding model name appears across vector index metadata,
    this may indicate a model migration is in progress — which requires a full
    index rebuild. This is a heuristic and may produce false positives.
    """
    issues: list[str] = []
    xml_files = list(manifest_dir.rglob("*.xml"))

    model_references: dict[str, list[str]] = {}  # model_name -> [files]

    for xml_file in xml_files:
        try:
            text = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for line in text.splitlines():
            line_lower = line.lower()
            if "embeddingmodel" in line_lower or "embedding_model" in line_lower:
                # Extract the text content between tags as a rough model name
                stripped = line.strip()
                rel = str(xml_file.relative_to(manifest_dir))
                model_references.setdefault(stripped, []).append(rel)

    if len(model_references) > 1:
        issues.append(
            "Multiple distinct embedding model references found across metadata files. "
            "The embedding model is view-only after a search index is created; a model change "
            "means a new index built in parallel, a retriever cutover, then deleting the old one. "
            "Distinct references found:"
        )
        for ref, files in list(model_references.items())[:10]:
            issues.append(f"  {ref[:100]}  (in: {', '.join(files[:3])})")

    return issues


def check_full_refresh_streams(manifest_dir: Path) -> list[str]:
    """Warn on data streams that replace all data each cycle."""
    issues: list[str] = []
    for path in sorted(manifest_dir.rglob("*.dataStreamDefinition")) + sorted(manifest_dir.rglob("*.dataStreamDefinition-meta.xml")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "<dataExtractMethods>FULL_REFRESH</dataExtractMethods>" in text.replace(" ", ""):
            issues.append(
                f"{path.relative_to(manifest_dir)} uses FULL_REFRESH; each cycle deletes and replaces all data. "
                "Use Incremental or Upsert where the connector allows."
            )
    return issues


# ─── Main orchestrator ────────────────────────────────────────────────────────

def check_vector_database_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_data_stream_definition(manifest_dir))
    issues.extend(check_full_refresh_streams(manifest_dir))
    issues.extend(check_data_space_definition(manifest_dir))
    issues.extend(check_pii_fields_in_metadata(manifest_dir))
    issues.extend(check_embedding_model_change_risk(manifest_dir))

    return issues


def self_test() -> int:
    base = Path(__file__).resolve().parent / "fixtures"
    good, bad = base / "good", base / "bad"
    if not good.is_dir() or not bad.is_dir():
        print("ERROR: fixtures/good or fixtures/bad is missing")
        return 1
    good_issues = check_vector_database_management(good)
    bad_issues = check_vector_database_management(bad)
    failures = 0
    if good_issues:
        failures += 1
        print(f"ERROR: self-test: fixtures/good produced {good_issues}")
    for expected in ("FULL_REFRESH", "match PII name patterns", "embedding model"):
        if not any(expected in issue for issue in bad_issues):
            failures += 1
            print(f"ERROR: self-test: fixtures/bad did not report '{expected}'")
    if failures:
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()
    manifest_dir = Path(args.manifest_dir)
    issues = check_vector_database_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
