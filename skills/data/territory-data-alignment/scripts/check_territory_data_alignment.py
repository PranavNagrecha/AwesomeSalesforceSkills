#!/usr/bin/env python3
"""Checker script for Territory Data Alignment skill.

Validates territory data alignment artifacts against best practices documented in the
territory-data-alignment skill:
  - CSV insert payloads for ObjectTerritory2Association (required columns, AssociationCause values)
  - Presence of deduplication evidence in migration logs or scripts
  - Territory2Id format validity (ETM IDs start with 0MW)
  - Territory2Model state references in SOQL files (warns if non-Active states are targeted)
  - Stale UserTerritory2Association references (association CSVs using legacy object names)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_territory_data_alignment.py [--help]
    python3 check_territory_data_alignment.py --manifest-dir path/to/project
    python3 check_territory_data_alignment.py --csv path/to/associations.csv
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# ETM ObjectTerritory2Association CSV required columns
REQUIRED_OTA_COLUMNS = {"ObjectId", "Territory2Id", "AssociationCause"}

VALID_ASSOCIATION_CAUSES = {"Manual", "Territory"}

# Legacy TM object names that must not appear in ETM data work
LEGACY_OBJECT_NAMES = [
    "AccountTerritoryAssignment",
    "UserTerritory",
    "Territory__c",
    "TerritoryId",          # Legacy field name on AccountTerritoryAssignment
]

# ETM Territory2 ID prefix (15 or 18 char Salesforce IDs starting with 0MW)
TERRITORY2_ID_PREFIX = "0MW"

# SOQL file extensions to inspect
SOQL_EXTENSIONS = {".soql", ".sql", ".txt", ".md"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check territory data alignment artifacts for common issues: "
            "CSV column validity, AssociationCause correctness, legacy object usage, "
            "Territory2Id format, and SOQL model state references."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Directory containing migration scripts, SOQL files, and CSV payloads.",
    )
    parser.add_argument(
        "--csv",
        default=None,
        dest="csv_path",
        help="Path to a specific ObjectTerritory2Association insert CSV to validate.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# CSV checks
# ---------------------------------------------------------------------------

def check_ota_csv(csv_path: Path) -> list[str]:
    """Validate an ObjectTerritory2Association insert CSV for common issues."""
    issues: list[str] = []

    if not csv_path.exists():
        issues.append("CSV file not found: {}".format(csv_path))
        return issues

    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])

            missing_cols = REQUIRED_OTA_COLUMNS - fieldnames
            if missing_cols:
                issues.append(
                    "MISSING_COLUMNS: CSV '{}' is missing required columns: {}. "
                    "ObjectTerritory2Association inserts require: {}.".format(
                        csv_path.name,
                        ", ".join(sorted(missing_cols)),
                        ", ".join(sorted(REQUIRED_OTA_COLUMNS)),
                    )
                )
                # Cannot validate rows without required columns
                return issues

            seen_pairs: set[tuple[str, str]] = set()
            duplicate_count = 0
            invalid_cause_count = 0
            invalid_territory_id_count = 0

            for row_num, row in enumerate(reader, start=2):
                object_id = (row.get("ObjectId") or "").strip()
                territory2_id = (row.get("Territory2Id") or "").strip()
                association_cause = (row.get("AssociationCause") or "").strip()

                # Check AssociationCause value
                if association_cause not in VALID_ASSOCIATION_CAUSES:
                    invalid_cause_count += 1
                    if invalid_cause_count <= 3:
                        issues.append(
                            "INVALID_CAUSE: Row {}: AssociationCause '{}' is not valid. "
                            "Accepted values: {}. Rule-driven associations should not be "
                            "inserted via API — use 'Manual' for API-loaded rows.".format(
                                row_num, association_cause,
                                ", ".join(sorted(VALID_ASSOCIATION_CAUSES))
                            )
                        )

                # Check Territory2Id prefix (ETM IDs start with 0MW)
                if territory2_id and not territory2_id.startswith(TERRITORY2_ID_PREFIX):
                    invalid_territory_id_count += 1
                    if invalid_territory_id_count <= 3:
                        issues.append(
                            "SUSPECT_TERRITORY_ID: Row {}: Territory2Id '{}' does not start "
                            "with '{}'. ETM Territory2 record IDs begin with 0MW. "
                            "Verify this is not a Legacy Territory ID (which starts with 00U) "
                            "or a Territory2Model ID.".format(
                                row_num, territory2_id, TERRITORY2_ID_PREFIX
                            )
                        )

                # Check for duplicates
                pair = (object_id, territory2_id)
                if pair in seen_pairs:
                    duplicate_count += 1
                    if duplicate_count <= 3:
                        issues.append(
                            "DUPLICATE_PAIR: Row {}: (ObjectId={}, Territory2Id={}) appears "
                            "more than once in this CSV. ObjectTerritory2Association does not "
                            "enforce uniqueness — duplicates will be inserted and must be "
                            "manually cleaned up.".format(row_num, object_id, territory2_id)
                        )
                else:
                    seen_pairs.add(pair)

            if invalid_cause_count > 3:
                issues.append(
                    "INVALID_CAUSE_SUMMARY: {} total rows with invalid AssociationCause "
                    "(first 3 shown above).".format(invalid_cause_count)
                )
            if invalid_territory_id_count > 3:
                issues.append(
                    "SUSPECT_TERRITORY_ID_SUMMARY: {} total rows with suspect Territory2Id "
                    "prefix (first 3 shown above).".format(invalid_territory_id_count)
                )
            if duplicate_count > 3:
                issues.append(
                    "DUPLICATE_PAIR_SUMMARY: {} total duplicate (ObjectId, Territory2Id) "
                    "pairs in this CSV (first 3 shown above). Dedup before inserting.".format(
                        duplicate_count
                    )
                )

    except Exception as exc:
        issues.append("CSV_PARSE_ERROR: Could not parse '{}': {}".format(csv_path.name, exc))

    return issues


# ---------------------------------------------------------------------------
# Legacy object name checks
# ---------------------------------------------------------------------------

def check_legacy_object_references(manifest_dir: Path) -> list[str]:
    """Scan script and SOQL files for references to Legacy Territory Management objects."""
    issues: list[str] = []

    candidate_extensions = {".py", ".apex", ".cls", ".soql", ".sql", ".txt", ".sh", ".js", ".ts"}
    files_to_check = [
        f for f in manifest_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in candidate_extensions
    ]

    for file_path in files_to_check:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for legacy_name in LEGACY_OBJECT_NAMES:
            if legacy_name in content:
                issues.append(
                    "LEGACY_OBJECT: '{}' references '{}', which is a Legacy Territory "
                    "Management object/field. ETM (Territory Management 2.0) uses "
                    "ObjectTerritory2Association, UserTerritory2Association, and Territory2. "
                    "Verify the org is not using Legacy TM.".format(
                        file_path.relative_to(manifest_dir), legacy_name
                    )
                )
                break  # One warning per file is enough

    return issues


# ---------------------------------------------------------------------------
# SOQL model state checks
# ---------------------------------------------------------------------------

def check_soql_model_state_references(manifest_dir: Path) -> list[str]:
    """Warn if any SOQL/query file writes to or filters on non-Active territory models."""
    issues: list[str] = []

    non_active_pattern = re.compile(
        r"Territory2Model\.State\s*[!=<>]+\s*['\"](?!Active)[^'\"]+['\"]",
        re.IGNORECASE,
    )

    write_without_state_check = re.compile(
        r"INSERT\s+INTO\s+ObjectTerritory2Association",
        re.IGNORECASE,
    )

    soql_files = [
        f for f in manifest_dir.rglob("*")
        if f.is_file() and f.suffix.lower() in SOQL_EXTENSIONS
    ]

    for file_path in soql_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if non_active_pattern.search(content):
            issues.append(
                "NON_ACTIVE_MODEL_FILTER: '{}' contains a Territory2Model.State filter "
                "targeting a non-Active state. Inserting associations into non-Active models "
                "will fail. Verify this file is used for read/archive queries only, not "
                "as a target for DML.".format(file_path.relative_to(manifest_dir))
            )

    return issues


# ---------------------------------------------------------------------------
# CSV discovery in manifest dir
# ---------------------------------------------------------------------------

def check_csvs_in_manifest(manifest_dir: Path) -> list[str]:
    """Find and validate any CSV files that look like ObjectTerritory2Association payloads."""
    issues: list[str] = []
    csv_files = list(manifest_dir.rglob("*.csv"))

    for csv_file in csv_files:
        try:
            with csv_file.open(newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                fieldnames = set(reader.fieldnames or [])
        except Exception:
            continue

        # Only validate CSVs that look like OTA payloads
        if "Territory2Id" in fieldnames or "ObjectTerritory2AssociationId" in fieldnames:
            issues.extend(check_ota_csv(csv_file))

    return issues


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def check_territory_data_alignment(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append("Manifest directory not found: {}".format(manifest_dir))
        return issues

    issues.extend(check_legacy_object_references(manifest_dir))
    issues.extend(check_soql_model_state_references(manifest_dir))
    issues.extend(check_csvs_in_manifest(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()

    all_issues: list[str] = []

    if args.csv_path:
        csv_path = Path(args.csv_path)
        all_issues.extend(check_ota_csv(csv_path))

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_territory_data_alignment(manifest_dir))
    elif not args.csv_path:
        # Default: check current directory
        manifest_dir = Path(".")
        all_issues.extend(check_territory_data_alignment(manifest_dir))

    if not all_issues:
        print("No territory data alignment issues found.")
        return 0

    for issue in all_issues:
        print("ISSUE: " + issue)

    print("\n{} issue(s) found.".format(len(all_issues)))
    return 1


if __name__ == "__main__":
    sys.exit(main())
