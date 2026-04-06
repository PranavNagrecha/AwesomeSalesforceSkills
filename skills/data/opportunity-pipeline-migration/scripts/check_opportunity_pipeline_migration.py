#!/usr/bin/env python3
"""Checker script for Opportunity Pipeline Migration skill.

Validates migration CSVs and Salesforce metadata for common sequencing,
Price Book, stage history, and OpportunitySplit configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_opportunity_pipeline_migration.py [--manifest-dir path/to/metadata]
    python3 check_opportunity_pipeline_migration.py --csv-dir path/to/migration/csvs
    python3 check_opportunity_pipeline_migration.py --csv-dir . --manifest-dir ./metadata
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Column names (case-insensitive) that indicate an Opportunity CSV
OPP_ID_COLUMNS = {"legacy_opportunity_id__c", "id", "name"}
OPP_PRICEBOOK_COLUMN = "pricebook2id"

# Column names that indicate an OpportunityLineItem CSV
OLI_OPP_REF_COLUMNS = {
    "opportunityid",
    "opportunity.legacy_opportunity_id__c",
    "opportunity__r.legacy_opportunity_id__c",
}
OLI_PBE_REF_COLUMNS = {
    "pricebookentryid",
    "pricebookentry.id",
}

# Columns that indicate a stage history direct-insert attempt (wrong)
HISTORY_DIRECT_INSERT_SIGNALS = {
    "opportunityhistory",
    "opportunityfieldhistory",
}

# Columns present in a valid stage history Task CSV
TASK_STAGE_HISTORY_COLUMNS = {"whatid", "subject", "activitydate", "status"}

# OpportunitySplit required columns
SPLIT_REQUIRED_COLUMNS = {"opportunityid", "splitownerid", "splittypeid", "splitpercentage"}

# Metadata file names that signal OpportunitySplits is enabled
SPLITS_ENABLED_FILES = {"opportunitysplittype", "opportunityteammember"}

# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def _read_csv_headers(csv_file: Path) -> list[str]:
    """Return lowercased headers from the first row of a CSV file."""
    try:
        with csv_file.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
            reader = csv.reader(fh)
            headers = next(reader, [])
            return [h.strip().lower() for h in headers]
    except OSError:
        return []


def _read_csv_rows(csv_file: Path) -> list[dict[str, str]]:
    """Return all rows as dicts with lowercased keys."""
    rows: list[dict[str, str]] = []
    try:
        with csv_file.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                return rows
            for row in reader:
                rows.append({k.strip().lower(): v.strip() for k, v in row.items() if k})
    except OSError:
        pass
    return rows


def _find_csv_files(directory: Path) -> list[Path]:
    """Return all CSV files in directory (non-recursive)."""
    return sorted(directory.glob("*.csv"))


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------


def check_opportunity_csv_has_pricebook(csv_files: list[Path]) -> list[str]:
    """Warn if an Opportunity CSV is missing Pricebook2Id when OLI CSVs are present."""
    issues: list[str] = []
    opp_csvs: list[Path] = []
    oli_csvs: list[Path] = []

    for f in csv_files:
        name = f.stem.lower()
        headers = _read_csv_headers(f)
        header_set = set(headers)

        is_opp = any(col in header_set for col in OPP_ID_COLUMNS) and "stagename" in header_set
        is_oli = any(col in header_set for col in OLI_OPP_REF_COLUMNS) and any(
            col in header_set for col in OLI_PBE_REF_COLUMNS
        )
        if "opportunity" in name and "lineitem" not in name and "split" not in name:
            is_opp = True
        if "lineitem" in name or "oli" in name:
            is_oli = True

        if is_opp:
            opp_csvs.append(f)
            if OPP_PRICEBOOK_COLUMN not in header_set:
                issues.append(
                    f"{f.name}: Opportunity CSV is missing 'Pricebook2Id' column. "
                    "Pricebook2Id must be set on every Opportunity before OpportunityLineItems "
                    "can be inserted. Add Pricebook2Id to this CSV and populate it for every row."
                )
        if is_oli:
            oli_csvs.append(f)

    if oli_csvs and not opp_csvs:
        issues.append(
            "OpportunityLineItem CSV(s) detected but no Opportunity CSV found. "
            "Opportunities must be loaded before OpportunityLineItems. "
            "Verify the Opportunity CSV is present and will be loaded first."
        )

    return issues


def check_no_history_direct_insert(csv_files: list[Path], manifest_dir: Path) -> list[str]:
    """Detect any attempt to directly insert OpportunityHistory records."""
    issues: list[str] = []

    for f in csv_files:
        name = f.stem.lower()
        if "opportunityhistory" in name or "opportunityfieldhistory" in name:
            issues.append(
                f"{f.name}: This CSV appears to target OpportunityHistory or "
                "OpportunityFieldHistory, which are read-only system objects and cannot be "
                "inserted via API. Use Task records (Subject='Historical Stage: <stage>') or "
                "sequential StageName updates on the Opportunity instead."
            )

    # Also scan manifest for any metadata that references history as a load target
    if manifest_dir.exists():
        for xml_file in manifest_dir.rglob("package.xml"):
            try:
                content = xml_file.read_text(encoding="utf-8", errors="replace").lower()
                for signal in HISTORY_DIRECT_INSERT_SIGNALS:
                    if signal in content:
                        issues.append(
                            f"{xml_file.name}: References '{signal}' — confirm this is not "
                            "a data load target. OpportunityHistory and OpportunityFieldHistory "
                            "are read-only and cannot be inserted."
                        )
            except OSError:
                pass

    return issues


def check_split_csv_percentages(csv_files: list[Path]) -> list[str]:
    """Validate that OpportunitySplit CSVs have percentages summing to 100 per opportunity per SplitType."""
    issues: list[str] = []

    for f in csv_files:
        name = f.stem.lower()
        if "split" not in name and "opportunitysplit" not in name:
            continue

        headers = _read_csv_headers(f)
        header_set = set(headers)

        # Check required columns
        missing_cols = SPLIT_REQUIRED_COLUMNS - header_set
        if missing_cols:
            issues.append(
                f"{f.name}: OpportunitySplit CSV is missing required columns: "
                f"{sorted(missing_cols)}. Required: opportunityid, splitownerid, "
                "splittypeid, splitpercentage."
            )
            continue

        rows = _read_csv_rows(f)
        if not rows:
            continue

        # Aggregate percentages per (opportunityid, splittypeid)
        totals: dict[tuple[str, str], float] = {}
        bad_rows: list[int] = []
        for row_num, row in enumerate(rows, start=2):
            opp_id = row.get("opportunityid", "").strip()
            split_type = row.get("splittypeid", "").strip()
            pct_str = row.get("splitpercentage", "").strip()
            try:
                pct = float(pct_str)
            except ValueError:
                bad_rows.append(row_num)
                continue
            key = (opp_id, split_type)
            totals[key] = totals.get(key, 0.0) + pct

        if bad_rows:
            issues.append(
                f"{f.name}: Non-numeric splitpercentage values found on rows: {bad_rows[:10]}. "
                "All splitpercentage values must be numeric."
            )

        mismatched = {k: v for k, v in totals.items() if abs(v - 100.0) > 0.01}
        if mismatched:
            sample = list(mismatched.items())[:5]
            sample_str = "; ".join(
                f"opp={opp}, type={st}: {pct:.2f}%" for (opp, st), pct in sample
            )
            issues.append(
                f"{f.name}: OpportunitySplit percentages do not sum to 100% for "
                f"{len(mismatched)} opportunity/SplitType combination(s). "
                f"Sample: {sample_str}. Fix before loading to avoid validation failures."
            )

    return issues


def check_pricebook_entry_sequence(csv_files: list[Path]) -> list[str]:
    """Warn if custom PBE CSV exists without a Standard PBE CSV."""
    issues: list[str] = []
    has_standard_pbe = False
    has_custom_pbe = False

    for f in csv_files:
        name = f.stem.lower()
        headers = _read_csv_headers(f)
        header_set = set(headers)

        is_pbe = (
            "pricebookentry" in name
            or "pbe" in name
            or ("pricebook2id" in header_set and "unitprice" in header_set and "product2id" in header_set)
            or ("pricebook2id" in header_set and "unitprice" in header_set and any("product2" in h for h in header_set))
        )
        if not is_pbe:
            continue

        if "standard" in name or "std" in name:
            has_standard_pbe = True
        elif "custom" in name or "distributor" in name or "partner" in name:
            has_custom_pbe = True
        else:
            # Inspect rows to determine if standard or custom
            rows = _read_csv_rows(f)
            for row in rows[:20]:
                # Standard Pricebook2Id is org-specific; heuristic only
                has_standard_pbe = True  # cannot determine without org query; assume present
                break

    if has_custom_pbe and not has_standard_pbe:
        issues.append(
            "Custom Price Book Entry CSV detected but no Standard Price Book Entry CSV found. "
            "Salesforce requires a Standard Price Book Entry for every Product2 before a custom "
            "Price Book Entry can be created. Add a Standard PBE CSV to the migration and load "
            "it before the custom PBE CSV."
        )

    return issues


def check_task_stage_history_structure(csv_files: list[Path]) -> list[str]:
    """If a Task CSV exists for stage history, verify required columns are present."""
    issues: list[str] = []

    for f in csv_files:
        name = f.stem.lower()
        if "task" not in name and "stage_history" not in name and "stagehistory" not in name:
            continue

        headers = _read_csv_headers(f)
        header_set = set(headers)

        # Only validate if this looks like a stage history Task file
        if not any(col in header_set for col in {"whatid", "subject"}):
            continue

        missing = TASK_STAGE_HISTORY_COLUMNS - header_set
        if missing:
            issues.append(
                f"{f.name}: Task CSV for stage history is missing columns: {sorted(missing)}. "
                "Required columns for stage history Tasks: whatid, subject, activitydate, status."
            )

        # Check that Subject column values reference historical stages
        rows = _read_csv_rows(f)
        if rows:
            sample_subjects = [r.get("subject", "") for r in rows[:5] if r.get("subject")]
            has_history_label = any("historical stage" in s.lower() or "stage:" in s.lower() for s in sample_subjects)
            if not has_history_label and sample_subjects:
                issues.append(
                    f"{f.name}: Task Subject values do not appear to reference historical stages "
                    "(expected 'Historical Stage: <stage>' pattern). "
                    f"Sample subjects: {sample_subjects}. "
                    "Update Subject values so stage history Tasks are easily identifiable in reports."
                )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_opportunity_pipeline_migration(
    manifest_dir: Path, csv_dir: Path
) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists() and not csv_dir.exists():
        issues.append(
            f"Neither manifest directory ({manifest_dir}) nor CSV directory ({csv_dir}) found. "
            "Provide --manifest-dir or --csv-dir pointing to an existing directory."
        )
        return issues

    csv_files: list[Path] = []
    if csv_dir.exists():
        csv_files = _find_csv_files(csv_dir)

    issues.extend(check_opportunity_csv_has_pricebook(csv_files))
    issues.extend(check_no_history_direct_insert(csv_files, manifest_dir))
    issues.extend(check_split_csv_percentages(csv_files))
    issues.extend(check_pricebook_entry_sequence(csv_files))
    issues.extend(check_task_stage_history_structure(csv_files))

    if csv_files and not issues:
        print(f"Checked {len(csv_files)} CSV file(s). No issues found.")

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Opportunity Pipeline Migration CSVs and metadata for common issues: "
            "missing Pricebook2Id, OpportunityHistory direct insert attempts, "
            "split percentage totals, Price Book Entry sequencing, and stage history Task structure."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--csv-dir",
        default=".",
        help="Directory containing migration CSV files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    csv_dir = Path(args.csv_dir)

    issues = check_opportunity_pipeline_migration(manifest_dir, csv_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
