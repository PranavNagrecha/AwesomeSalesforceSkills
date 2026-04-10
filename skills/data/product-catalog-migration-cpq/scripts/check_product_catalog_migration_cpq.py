#!/usr/bin/env python3
"""Checker script for Product Catalog Migration CPQ skill.

Validates a CPQ catalog migration plan or metadata export directory for common
issues: missing wave dependencies, objects in wrong load order, missing external
ID field declarations, and incomplete PriceAction/PriceRule pairing indicators.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_product_catalog_migration_cpq.py [--help]
    python3 check_product_catalog_migration_cpq.py --manifest-dir path/to/metadata
    python3 check_product_catalog_migration_cpq.py --csv-dir path/to/load/csvs
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Wave dependency model
# ---------------------------------------------------------------------------

# Maps each SBQQ object to the minimum wave it can appear in.
# Objects not listed are not CPQ catalog objects and are ignored.
WAVE_MAP: dict[str, int] = {
    "Pricebook2": 1,
    "SBQQ__DiscountCategory__c": 1,
    "Product2": 2,
    "SBQQ__PriceRule__c": 2,
    "PricebookEntry": 3,
    "SBQQ__DiscountSchedule__c": 3,
    "SBQQ__DiscountTier__c": 3,
    "SBQQ__ProductOption__c": 4,
    "SBQQ__PriceAction__c": 4,
    "SBQQ__ConfigurationAttribute__c": 5,
    "SBQQ__OptionConstraint__c": 5,
}

# Objects that must NOT appear in the same file as objects from an earlier wave.
WAVE_4_OBJECTS = {"SBQQ__ProductOption__c", "SBQQ__PriceAction__c"}
WAVE_5_OBJECTS = {"SBQQ__ConfigurationAttribute__c", "SBQQ__OptionConstraint__c"}
WAVE_2_OBJECTS = {"Product2", "SBQQ__PriceRule__c"}

# FK columns that reference Product2 (self-referencing — require two-pass)
PRODUCT2_SELF_REF_FIELDS = {
    "SBQQ__UpgradeTarget__c",
    "SBQQ__UpgradeTargetProduct__c",
}

# FK columns that must use relationship notation, not raw Salesforce IDs
# (18-char alphanumeric IDs starting with 0 are source-org IDs)
SBQQ_FK_COLUMNS = {
    "SBQQ__PriceRule__c",
    "SBQQ__ConfiguredSKU__c",
    "SBQQ__Product__c",
    "SBQQ__DiscountCategory__c",
    "SBQQ__DiscountSchedule__c",
    "SBQQ__ConstrainedOption__c",
    "SBQQ__ConstrainingOption__c",
    "SBQQ__ProductOption__c",
}

SALESFORCE_ID_PATTERN_LEN = 18  # 18-char SF IDs
SALESFORCE_ID_PREFIX_CHARS = {"0"}  # SF IDs start with '0'


def _looks_like_salesforce_id(value: str) -> bool:
    """Return True if value looks like a raw Salesforce record ID."""
    return (
        len(value) in (15, 18)
        and value[:1] in SALESFORCE_ID_PREFIX_CHARS
        and value.isalnum()
    )


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_csv_files(csv_dir: Path) -> list[str]:
    """Check CSV load files in csv_dir for CPQ migration anti-patterns."""
    issues: list[str] = []

    csv_files = list(csv_dir.glob("*.csv"))
    if not csv_files:
        issues.append(
            f"No CSV files found in {csv_dir}. "
            "Expected load wave files (e.g., wave1_pricebook2.csv)."
        )
        return issues

    for csv_file in sorted(csv_files):
        file_issues = _check_single_csv(csv_file)
        issues.extend(f"[{csv_file.name}] {issue}" for issue in file_issues)

    # Cross-file wave ordering check
    wave_ordering_issues = _check_wave_ordering_across_files(csv_files)
    issues.extend(wave_ordering_issues)

    return issues


def _check_single_csv(csv_file: Path) -> list[str]:
    """Check a single CSV file for CPQ migration issues."""
    issues: list[str] = []

    try:
        with csv_file.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)
    except Exception as exc:
        return [f"Could not parse CSV: {exc}"]

    if not headers:
        return ["CSV has no headers."]

    # Detect objects present in this file (by header column patterns)
    detected_objects = _detect_objects_from_headers(headers)

    # Check 1: Self-referencing Product2 fields in same file as Product2 inserts
    if "Product2" in detected_objects or _file_appears_to_target("Product2", csv_file):
        for self_ref_field in PRODUCT2_SELF_REF_FIELDS:
            if self_ref_field in headers:
                # Check if any rows have non-null values
                populated = [
                    r for r in rows if r.get(self_ref_field, "").strip()
                ]
                if populated:
                    issues.append(
                        f"Self-referencing Product2 field '{self_ref_field}' is populated "
                        f"in {len(populated)} rows. Self-references require a two-pass load "
                        f"(INSERT without this field, then UPDATE with it). "
                        f"Single-pass inserts fail when the referenced product is in the same job."
                    )

    # Check 2: Raw Salesforce IDs in FK columns (should use relationship notation)
    for fk_col in SBQQ_FK_COLUMNS:
        if fk_col in headers:
            raw_id_rows = [
                i + 2  # account for header row (1-indexed)
                for i, r in enumerate(rows)
                if _looks_like_salesforce_id(r.get(fk_col, "").strip())
            ]
            if raw_id_rows:
                sample = raw_id_rows[:3]
                issues.append(
                    f"FK column '{fk_col}' contains raw Salesforce IDs on rows {sample} "
                    f"(and {len(raw_id_rows) - len(sample)} more). "
                    f"Use relationship notation instead: "
                    f"'{fk_col[:-1]}r.Migration_ExternalId__c' to resolve FKs across orgs."
                )

    # Check 3: Wave 5 objects mixed with Wave 4 objects in same file
    wave4_present = detected_objects & WAVE_4_OBJECTS
    wave5_present = detected_objects & WAVE_5_OBJECTS
    if wave4_present and wave5_present:
        issues.append(
            f"Wave 4 objects ({sorted(wave4_present)}) and Wave 5 objects "
            f"({sorted(wave5_present)}) appear in the same file. "
            f"OptionConstraint and ConfigurationAttribute require all ProductOption "
            f"records to be committed first. Load them in separate completed jobs."
        )

    # Check 4: Wave 2 objects mixed with Wave 4 or Wave 5 objects
    wave2_present = detected_objects & WAVE_2_OBJECTS
    if wave2_present and (wave4_present or wave5_present):
        later = wave4_present | wave5_present
        issues.append(
            f"Wave 2 objects ({sorted(wave2_present)}) and Wave 4/5 objects "
            f"({sorted(later)}) appear in the same file. "
            f"These must be in separate completed jobs due to FK dependency ordering."
        )

    return issues


def _detect_objects_from_headers(headers: list[str]) -> set[str]:
    """Infer which CPQ objects a CSV targets based on column names."""
    detected: set[str] = set()
    header_set = set(headers)

    if "SBQQ__ConfiguredSKU__c" in header_set or "SBQQ__Product__c" in header_set:
        detected.add("SBQQ__ProductOption__c")
    if "SBQQ__PriceRule__c" in header_set and "SBQQ__Type__c" in header_set:
        detected.add("SBQQ__PriceAction__c")
    if "SBQQ__ConstrainedOption__c" in header_set:
        detected.add("SBQQ__OptionConstraint__c")
    if "SBQQ__ConfigurationAttribute__c" in header_set or (
        "SBQQ__Product__c" in header_set and "SBQQ__TargetObject__c" in header_set
    ):
        detected.add("SBQQ__ConfigurationAttribute__c")
    if "IsActive" in header_set and "ProductCode" in header_set:
        detected.add("Product2")
    if "SBQQ__DiscountUnit__c" in header_set:
        detected.add("SBQQ__DiscountSchedule__c")
    if "SBQQ__DiscountSchedule__c" in header_set and "SBQQ__LowerBound__c" in header_set:
        detected.add("SBQQ__DiscountTier__c")
    if "SBQQ__ConditionsMet__c" in header_set:
        detected.add("SBQQ__PriceRule__c")
    if "SBQQ__Code__c" in header_set and "SBQQ__DiscountSchedule__c" not in header_set:
        detected.add("SBQQ__DiscountCategory__c")

    return detected


def _file_appears_to_target(object_name: str, csv_file: Path) -> bool:
    """Heuristic: does the filename suggest this object?"""
    name_lower = csv_file.stem.lower().replace("-", "_").replace(" ", "_")
    object_lower = object_name.lower().replace("sbqq__", "").replace("__c", "")
    return object_lower in name_lower


def _check_wave_ordering_across_files(csv_files: list[Path]) -> list[str]:
    """Check that file naming suggests correct wave ordering."""
    issues: list[str] = []

    # Look for files with wave number prefixes (e.g., wave1_, wave2_, etc.)
    wave_files: dict[int, list[Path]] = {}
    for f in csv_files:
        stem = f.stem.lower()
        for wave_num in range(1, 6):
            if stem.startswith(f"wave{wave_num}") or stem.startswith(f"wave_{wave_num}"):
                wave_files.setdefault(wave_num, []).append(f)
                break

    if not wave_files:
        # No wave-numbered files — can't check ordering
        return issues

    # Check that Wave 5 files exist only if Wave 4 files exist
    if 5 in wave_files and 4 not in wave_files:
        issues.append(
            "Wave 5 files found but no Wave 4 files. "
            "ConfigurationAttribute and OptionConstraint require ProductOption (Wave 4) to load first."
        )

    if 4 in wave_files and 2 not in wave_files:
        issues.append(
            "Wave 4 files found but no Wave 2 files. "
            "ProductOption requires Product2 (Wave 2) to exist before insert."
        )

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Check a Salesforce metadata directory for CPQ migration indicators."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for any SBQQ-related metadata that suggests CPQ is installed
    sbqq_files = list(manifest_dir.rglob("SBQQ__*"))
    if not sbqq_files:
        issues.append(
            "No SBQQ__ metadata files found in manifest directory. "
            "Confirm the Salesforce CPQ managed package is installed in the target org."
        )

    # Check for external ID field definitions on SBQQ objects
    field_files = list(manifest_dir.rglob("*.field-meta.xml"))
    external_id_objects: set[str] = set()
    for ff in field_files:
        # Check if this field is an external ID on an SBQQ object
        if "SBQQ__" in str(ff):
            try:
                content = ff.read_text(encoding="utf-8")
                if "<externalId>true</externalId>" in content:
                    external_id_objects.add(ff.parent.parent.name)
            except OSError:
                pass

    if not external_id_objects and sbqq_files:
        issues.append(
            "No External ID fields found on SBQQ objects in the metadata manifest. "
            "External ID fields are required for cross-org FK resolution via relationship notation. "
            "Add a custom External ID field (e.g., Migration_ExternalId__c) to each SBQQ object."
        )

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CPQ product catalog migration configuration for common issues: "
            "wave dependency ordering, self-referencing Product2 fields, raw Salesforce IDs "
            "in FK columns, and missing External ID fields."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata export to check for CPQ setup.",
    )
    parser.add_argument(
        "--csv-dir",
        default=None,
        help="Directory containing bulk load CSV files to check for wave ordering and FK patterns.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        issues.extend(check_manifest_dir(manifest_dir))

    if args.csv_dir:
        csv_dir = Path(args.csv_dir)
        issues.extend(check_csv_files(csv_dir))

    if not args.manifest_dir and not args.csv_dir:
        # Default: check current directory for both patterns
        cwd = Path(".")
        issues.extend(check_manifest_dir(cwd))
        if list(cwd.glob("*.csv")):
            issues.extend(check_csv_files(cwd))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
