#!/usr/bin/env python3
"""Checker script for Data Migration Planning skill.

Validates a migration plan configuration (CSV or plain-text config) for common
structural issues:
  - Presence of an external_id column in each object's CSV mapping
  - Parent-before-child ordering in the migration sequence
  - Documentation of a validation rule bypass approach

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_migration_plan.py --help
    python3 check_migration_plan.py --plan-file path/to/migration_sequence.csv
    python3 check_migration_plan.py --csv-dir path/to/load/csvs/
    python3 check_migration_plan.py --plan-file migration_sequence.csv --csv-dir load_csvs/
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce data migration plan for common structural issues.\n"
            "Validates external ID column presence, parent-before-child ordering,\n"
            "and validation rule bypass documentation."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--plan-file",
        default=None,
        help=(
            "Path to the migration sequence CSV file. "
            "Expected columns: object, depends_on, bypass_documented. "
            "depends_on may be empty (no parent) or a comma-separated list of parent object names. "
            "bypass_documented must be 'yes' or 'no'."
        ),
    )
    parser.add_argument(
        "--csv-dir",
        default=None,
        help=(
            "Directory containing load CSV files (one per object). "
            "Each file is checked for the presence of an external_id column "
            "(any column whose header contains 'external_id', 'legacy_id', or ends in '__c' "
            "and is designated as the upsert key)."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Check 1: external_id column presence in load CSV files
# ---------------------------------------------------------------------------

EXTERNAL_ID_PATTERNS = (
    "external_id",
    "legacy_id",
    "externalid",
    "ext_id",
    "source_id",
)


def _looks_like_external_id_column(header: str) -> bool:
    """Return True if the column header looks like an external ID field."""
    lower = header.lower().strip()
    for pattern in EXTERNAL_ID_PATTERNS:
        if pattern in lower:
            return True
    # Salesforce External ID fields often end in __c and contain 'id' or 'key'
    if lower.endswith("__c") and ("id" in lower or "key" in lower or "legacy" in lower):
        return True
    return False


def check_csv_external_ids(csv_dir: Path) -> list[str]:
    """Check every CSV file in csv_dir for an external ID column.

    Returns a list of issue strings.
    """
    issues: list[str] = []

    if not csv_dir.exists():
        issues.append(f"CSV directory not found: {csv_dir}")
        return issues

    csv_files = list(csv_dir.glob("*.csv"))
    if not csv_files:
        issues.append(f"No CSV files found in directory: {csv_dir}")
        return issues

    for csv_file in sorted(csv_files):
        try:
            with csv_file.open(newline="", encoding="utf-8-sig") as fh:
                reader = csv.reader(fh)
                try:
                    headers = next(reader)
                except StopIteration:
                    issues.append(f"{csv_file.name}: file is empty or has no header row")
                    continue

            has_external_id = any(_looks_like_external_id_column(h) for h in headers)
            if not has_external_id:
                issues.append(
                    f"{csv_file.name}: no external ID column detected. "
                    "All load CSVs must include a column that maps to the Salesforce External ID field "
                    "(e.g., Legacy_CRM_Id__c, External_Id__c) to enable safe upsert operations. "
                    "Column headers found: " + ", ".join(headers[:10])
                    + ("..." if len(headers) > 10 else "")
                )
        except (OSError, csv.Error) as exc:
            issues.append(f"{csv_file.name}: could not read file — {exc}")

    return issues


# ---------------------------------------------------------------------------
# Check 2: parent-before-child ordering in the migration sequence
# ---------------------------------------------------------------------------

def _parse_sequence_csv(plan_file: Path) -> tuple[list[dict], list[str]]:
    """Parse the migration sequence CSV.

    Expected columns (case-insensitive): object, depends_on, bypass_documented
    depends_on: empty or comma-separated list of parent object names.

    Returns (rows, parse_issues).
    """
    parse_issues: list[str] = []
    rows: list[dict] = []

    if not plan_file.exists():
        parse_issues.append(f"Plan file not found: {plan_file}")
        return rows, parse_issues

    try:
        with plan_file.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                parse_issues.append(f"{plan_file.name}: file is empty or has no header row")
                return rows, parse_issues

            # Normalize headers to lowercase for flexible matching
            normalized_fields = [f.lower().strip() for f in reader.fieldnames]
            required = {"object", "depends_on", "bypass_documented"}
            missing = required - set(normalized_fields)
            if missing:
                parse_issues.append(
                    f"{plan_file.name}: missing required columns: {', '.join(sorted(missing))}. "
                    f"Found: {', '.join(reader.fieldnames)}"
                )
                return rows, parse_issues

            for line_num, row in enumerate(reader, start=2):
                # Normalize keys
                normalized_row = {k.lower().strip(): v.strip() for k, v in row.items() if k}
                if not normalized_row.get("object"):
                    parse_issues.append(
                        f"{plan_file.name} line {line_num}: 'object' column is blank — skipping row"
                    )
                    continue
                rows.append(normalized_row)

    except (OSError, csv.Error) as exc:
        parse_issues.append(f"{plan_file.name}: could not read file — {exc}")

    return rows, parse_issues


def check_parent_before_child_ordering(rows: list[dict]) -> list[str]:
    """Validate that every object appears after all of its declared parents.

    Returns a list of issue strings.
    """
    issues: list[str] = []
    loaded_objects: set[str] = set()

    for row in rows:
        obj = row["object"].strip()
        depends_on_raw = row.get("depends_on", "").strip()
        parents = [p.strip() for p in depends_on_raw.split(",") if p.strip()]

        for parent in parents:
            if parent.lower() == obj.lower():
                # Self-reference — skip; handled as a two-pass load
                continue
            if parent not in loaded_objects:
                issues.append(
                    f"Ordering violation: '{obj}' depends on '{parent}', "
                    f"but '{parent}' has not appeared earlier in the sequence. "
                    "Move the parent object to an earlier position in the migration sequence."
                )

        loaded_objects.add(obj)

    return issues


# ---------------------------------------------------------------------------
# Check 3: validation rule bypass documentation
# ---------------------------------------------------------------------------

def check_bypass_documentation(rows: list[dict]) -> list[str]:
    """Check that every object in the sequence documents a validation rule bypass approach.

    bypass_documented column must be 'yes' (case-insensitive).
    Returns a list of issue strings.
    """
    issues: list[str] = []

    for row in rows:
        obj = row["object"].strip()
        bypass_val = row.get("bypass_documented", "").strip().lower()
        if bypass_val not in ("yes", "true", "1", "y"):
            issues.append(
                f"'{obj}': validation rule bypass approach is not documented "
                f"(bypass_documented = '{row.get('bypass_documented', '')}', expected 'yes'). "
                "Document the bypass method (Custom Permission or temporary deactivation) "
                "for every object in the migration sequence, even if no validation rules "
                "currently exist on the object — rules may be added before migration cutover."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()

    if not args.plan_file and not args.csv_dir:
        print(
            "Usage: python3 check_migration_plan.py --plan-file <file> [--csv-dir <dir>]\n"
            "       python3 check_migration_plan.py --csv-dir <dir>\n\n"
            "Run with --help for full usage information."
        )
        return 2

    all_issues: list[str] = []

    # --- Check 1: CSV external ID columns ---
    if args.csv_dir:
        csv_dir = Path(args.csv_dir)
        print(f"Checking CSV files in: {csv_dir}")
        csv_issues = check_csv_external_ids(csv_dir)
        all_issues.extend(csv_issues)
        if not csv_issues:
            print(f"  OK — all CSV files have an external ID column")
        else:
            for issue in csv_issues:
                print(f"  ISSUE: {issue}")

    # --- Check 2 & 3: Plan file ordering and bypass documentation ---
    if args.plan_file:
        plan_file = Path(args.plan_file)
        print(f"Checking migration sequence file: {plan_file}")

        rows, parse_issues = _parse_sequence_csv(plan_file)
        all_issues.extend(parse_issues)
        for issue in parse_issues:
            print(f"  ISSUE (parse): {issue}")

        if rows:
            ordering_issues = check_parent_before_child_ordering(rows)
            all_issues.extend(ordering_issues)
            if not ordering_issues:
                print(f"  OK — parent-before-child ordering is valid for {len(rows)} objects")
            else:
                for issue in ordering_issues:
                    print(f"  ISSUE (ordering): {issue}")

            bypass_issues = check_bypass_documentation(rows)
            all_issues.extend(bypass_issues)
            if not bypass_issues:
                print(f"  OK — bypass documentation present for all {len(rows)} objects")
            else:
                for issue in bypass_issues:
                    print(f"  ISSUE (bypass): {issue}")

    # --- Summary ---
    print()
    if not all_issues:
        print("No issues found. Migration plan structure looks valid.")
        return 0

    print(f"Found {len(all_issues)} issue(s). Resolve before submitting any load jobs.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
