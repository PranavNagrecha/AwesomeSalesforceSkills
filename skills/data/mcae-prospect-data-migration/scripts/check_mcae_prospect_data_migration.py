#!/usr/bin/env python3
"""Checker script for MCAE Prospect Data Migration skill.

Validates a CSV file intended for MCAE prospect import against the known
constraints and anti-patterns documented in this skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_mcae_prospect_data_migration.py --csv path/to/prospects.csv
    python3 check_mcae_prospect_data_migration.py --csv path/to/prospects.csv --row-limit 100000
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# MCAE default prospect fields (canonical names from the import UI)
MCAE_DEFAULT_FIELDS = {
    "email",
    "first name",
    "last name",
    "company",
    "phone",
    "title",
    "salutation",
    "website",
    "fax",
    "address one",
    "address two",
    "city",
    "state",
    "zip",
    "country",
    "department",
    "notes",
    "annual revenue",
    "employees",
    "industry",
    "years in business",
    "comments",
    "twitter",
    "linkedin",
    "facebook",
    "source",
    "source campaign",
    "opted out",
    "do not email",
    "do not call",
}

# Column names that strongly suggest engagement history data (which cannot be imported)
ENGAGEMENT_HISTORY_SIGNALS = [
    "open",
    "click",
    "form fill",
    "form submit",
    "page view",
    "visit",
    "engagement",
    "last activity",
    "activity date",
    "email sent",
    "bounce",
    "unsubscribe",
    "score",
    "grade",
    "pardot score",
    "mcae score",
    "engagement score",
    "lead score",
    "marketing score",
]

# MCAE prospect import row limit per file
MCAE_ROW_LIMIT = 100_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a CSV file intended for MCAE prospect import. "
            "Checks for engagement history columns, missing email column, "
            "duplicate emails, and row count limits."
        ),
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        help="Path to the prospect CSV file to validate.",
    )
    parser.add_argument(
        "--row-limit",
        type=int,
        default=MCAE_ROW_LIMIT,
        help=f"Maximum rows allowed per MCAE import file (default: {MCAE_ROW_LIMIT}).",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce metadata (unused by this checker; accepted for compatibility).",
    )
    return parser.parse_args()


def check_csv(csv_path: Path, row_limit: int) -> list[str]:
    """Validate the CSV file for MCAE prospect import anti-patterns.

    Returns a list of issue strings. Empty list means no issues found.
    """
    issues: list[str] = []

    if not csv_path.exists():
        issues.append(f"CSV file not found: {csv_path}")
        return issues

    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            rows = list(reader)
    except Exception as exc:
        issues.append(f"Could not read CSV file: {exc}")
        return issues

    if not headers:
        issues.append("CSV has no header row. MCAE requires column headers.")
        return issues

    headers_lower = [h.strip().lower() for h in headers]

    # Check 1: Email column must be present
    if "email" not in headers_lower:
        issues.append(
            "CRITICAL: No 'Email' column found. MCAE uses email as the sole unique key. "
            "Every prospect import CSV must include an Email column."
        )

    # Check 2: Engagement history columns that cannot be imported
    flagged_engagement_cols: list[str] = []
    for header in headers_lower:
        for signal in ENGAGEMENT_HISTORY_SIGNALS:
            if signal in header:
                flagged_engagement_cols.append(header)
                break
    if flagged_engagement_cols:
        cols_str = ", ".join(f"'{c}'" for c in flagged_engagement_cols)
        issues.append(
            f"ENGAGEMENT HISTORY WARNING: Column(s) {cols_str} appear to contain "
            "engagement or scoring data. MCAE engagement history (opens, clicks, form fills, "
            "page views, scores) CANNOT be imported via CSV. These columns will be silently "
            "dropped or, if mapped to custom fields, will have no effect on the MCAE scoring "
            "engine. Remove these columns and document the engagement history gap with stakeholders."
        )

    # Check 3: Row count limit
    row_count = len(rows)
    if row_count > row_limit:
        issues.append(
            f"ROW LIMIT EXCEEDED: CSV contains {row_count:,} rows but MCAE list import "
            f"supports a maximum of {row_limit:,} rows per file. MCAE silently truncates "
            "files that exceed this limit without reporting an error. Split this CSV into "
            f"multiple files of ≤{row_limit:,} rows each."
        )
    elif row_count == 0:
        issues.append("CSV contains no data rows (header only). Nothing to import.")

    # Check 4: Blank email values
    if "email" in headers_lower:
        email_col = headers[headers_lower.index("email")]
        blank_email_rows = [
            i + 2  # 1-indexed, +1 for header row
            for i, row in enumerate(rows)
            if not row.get(email_col, "").strip()
        ]
        if blank_email_rows:
            sample = blank_email_rows[:5]
            sample_str = ", ".join(str(r) for r in sample)
            extra = f" (and {len(blank_email_rows) - 5} more)" if len(blank_email_rows) > 5 else ""
            issues.append(
                f"BLANK EMAIL: {len(blank_email_rows)} row(s) have a blank Email value "
                f"(rows: {sample_str}{extra}). MCAE rejects rows with no email. "
                "Remove or correct these rows before import."
            )

    # Check 5: Duplicate emails
    if "email" in headers_lower:
        email_col = headers[headers_lower.index("email")]
        emails = [row.get(email_col, "").strip().lower() for row in rows if row.get(email_col, "").strip()]
        seen: set[str] = set()
        duplicates: set[str] = set()
        for email in emails:
            if email in seen:
                duplicates.add(email)
            seen.add(email)
        if duplicates:
            sample = sorted(duplicates)[:3]
            sample_str = ", ".join(f"'{e}'" for e in sample)
            extra = f" (and {len(duplicates) - 3} more)" if len(duplicates) > 3 else ""
            issues.append(
                f"DUPLICATE EMAILS: {len(duplicates)} duplicate email address(es) found "
                f"({sample_str}{extra}). MCAE uses email as the sole unique key. Duplicate rows "
                "cause unexpected record merges or field value overwrites. Deduplicate the CSV "
                "on the Email column before import."
            )

    return issues


def check_no_csv(manifest_dir: Path) -> list[str]:
    """Fallback checks when no CSV is provided — checks for CSV files in a directory."""
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Directory not found: {manifest_dir}")
        return issues

    csv_files = list(manifest_dir.glob("*.csv"))
    if not csv_files:
        issues.append(
            "No CSV files found in the specified directory. "
            "Provide a --csv path to validate a specific import file."
        )
        return issues

    # If exactly one CSV is found, validate it automatically
    if len(csv_files) == 1:
        issues.append(
            f"Found one CSV file: {csv_files[0].name}. "
            "Re-run with --csv to validate it explicitly."
        )
    else:
        files_str = ", ".join(f.name for f in csv_files[:5])
        issues.append(
            f"Found {len(csv_files)} CSV file(s) in directory ({files_str}...). "
            "Use --csv to specify which file to validate."
        )

    return issues


def main() -> int:
    args = parse_args()

    if args.csv_path:
        csv_path = Path(args.csv_path)
        issues = check_csv(csv_path, args.row_limit)
        source_desc = str(csv_path)
    else:
        manifest_dir = Path(args.manifest_dir) if args.manifest_dir else Path(".")
        issues = check_no_csv(manifest_dir)
        source_desc = str(manifest_dir)

    if not issues:
        print(f"No issues found in: {source_desc}")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
