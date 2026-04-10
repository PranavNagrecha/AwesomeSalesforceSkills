#!/usr/bin/env python3
"""Checker script for Historical Order Migration (CPQ Legacy Data Upload) skill.

Validates CSV files prepared for CPQ Legacy Data Upload against the common failure modes
documented in references/gotchas.md. Uses stdlib only — no pip dependencies.

Checks performed:
  1. SBQQ__Quote__c CSV: Status=Approved and Primary=true required on all rows
  2. SBQQ__Quote__c CSV: SBQQ__StartDate__c and SBQQ__EndDate__c present
  3. SBQQ__Subscription__c CSV: required renewal fields present and non-empty
  4. SBQQ__Asset__c CSV: RootId and RevisedAsset mutual exclusivity
  5. SBQQ__Asset__c CSV: detects rows where both fields are non-null (silent corruption risk)
  6. General: warns if a batch_size config file or comment indicates batch size > 1

Usage:
    python3 check_historical_order_migration.py --help
    python3 check_historical_order_migration.py --quotes quotes.csv
    python3 check_historical_order_migration.py --subscriptions subs.csv
    python3 check_historical_order_migration.py --assets assets.csv
    python3 check_historical_order_migration.py \\
        --quotes quotes.csv --subscriptions subs.csv --assets assets.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Required field definitions
# ---------------------------------------------------------------------------

SUBSCRIPTION_REQUIRED_FIELDS = [
    "SBQQ__Contract__c",
    "SBQQ__Product__c",
    "SBQQ__StartDate__c",
    "SBQQ__EndDate__c",
    "SBQQ__Quantity__c",
    "SBQQ__NetPrice__c",
    "SBQQ__RegularPrice__c",
]

QUOTE_REQUIRED_STATUS = "Approved"
QUOTE_REQUIRED_PRIMARY = "true"


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------


def _read_csv(path: Path) -> Tuple[List[str], List[dict]]:
    """Return (headers, rows) from a CSV file. Rows are plain dicts."""
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        headers = list(reader.fieldnames or [])
    return headers, rows


def _col(row: dict, *candidates: str) -> str:
    """Return the value of the first matching column name (case-insensitive)."""
    lower_row = {k.lower(): v for k, v in row.items()}
    for candidate in candidates:
        val = lower_row.get(candidate.lower(), "")
        if val:
            return val.strip()
    return ""


# ---------------------------------------------------------------------------
# Individual checkers
# ---------------------------------------------------------------------------


def check_quotes_csv(path: Path) -> List[str]:
    """Check SBQQ__Quote__c CSV for required Legacy Data Upload field values."""
    issues: List[str] = []
    if not path.exists():
        issues.append(f"QUOTES CSV not found: {path}")
        return issues

    headers, rows = _read_csv(path)
    if not rows:
        issues.append(f"QUOTES CSV is empty: {path}")
        return issues

    # Check that required columns exist
    header_lower = {h.lower() for h in headers}
    for required_col in ("sbqq__status__c", "sbqq__primary__c"):
        if required_col not in header_lower:
            issues.append(
                f"QUOTES CSV missing required column '{required_col}' — "
                f"all quotes must have Status=Approved and Primary=true for Legacy Data Upload"
            )

    for i, row in enumerate(rows, start=2):  # row 1 is header
        status = _col(row, "SBQQ__Status__c")
        primary = _col(row, "SBQQ__Primary__c")

        if status and status != QUOTE_REQUIRED_STATUS:
            issues.append(
                f"QUOTES CSV row {i}: SBQQ__Status__c='{status}' — "
                f"must be 'Approved' for CPQ Legacy Data Upload (renewal engine ignores non-Approved quotes)"
            )

        if primary and primary.lower() not in ("true", "1", "yes"):
            issues.append(
                f"QUOTES CSV row {i}: SBQQ__Primary__c='{primary}' — "
                f"must be 'true' for CPQ Legacy Data Upload (renewal engine ignores non-Primary quotes)"
            )

        for date_col in ("SBQQ__StartDate__c", "SBQQ__EndDate__c"):
            val = _col(row, date_col)
            if not val:
                issues.append(
                    f"QUOTES CSV row {i}: '{date_col}' is empty — "
                    f"required for CPQ subscription term calculation"
                )

    return issues


def check_subscriptions_csv(path: Path) -> List[str]:
    """Check SBQQ__Subscription__c CSV for fields required by CPQ renewal engine."""
    issues: List[str] = []
    if not path.exists():
        issues.append(f"SUBSCRIPTIONS CSV not found: {path}")
        return issues

    headers, rows = _read_csv(path)
    if not rows:
        issues.append(f"SUBSCRIPTIONS CSV is empty: {path}")
        return issues

    header_lower = {h.lower() for h in headers}
    for required_col in SUBSCRIPTION_REQUIRED_FIELDS:
        if required_col.lower() not in header_lower:
            issues.append(
                f"SUBSCRIPTIONS CSV missing required column '{required_col}' — "
                f"this field drives CPQ renewal quote line generation"
            )

    for i, row in enumerate(rows, start=2):
        for field in SUBSCRIPTION_REQUIRED_FIELDS:
            val = _col(row, field)
            if not val:
                issues.append(
                    f"SUBSCRIPTIONS CSV row {i}: '{field}' is empty — "
                    f"required for CPQ renewal quote generation"
                )

        # Check that StartDate < EndDate where both present
        start = _col(row, "SBQQ__StartDate__c")
        end = _col(row, "SBQQ__EndDate__c")
        if start and end and start >= end:
            issues.append(
                f"SUBSCRIPTIONS CSV row {i}: StartDate '{start}' is not before EndDate '{end}' — "
                f"invalid subscription term will cause renewal date errors"
            )

    return issues


def check_assets_csv(path: Path) -> List[str]:
    """Check SBQQ__Asset__c CSV for Root Id / Revised Asset mutual exclusivity."""
    issues: List[str] = []
    if not path.exists():
        issues.append(f"ASSETS CSV not found: {path}")
        return issues

    headers, rows = _read_csv(path)
    if not rows:
        # Assets are optional — empty is acceptable
        return issues

    header_lower = {h.lower() for h in headers}
    has_root = "sbqq__rootid__c" in header_lower
    has_revised = "sbqq__revisedasset__c" in header_lower

    if not has_root and not has_revised:
        # Neither column present — no mutual exclusivity check possible
        return issues

    mutual_exclusivity_violations = 0
    for i, row in enumerate(rows, start=2):
        root_id = _col(row, "SBQQ__RootId__c")
        revised = _col(row, "SBQQ__RevisedAsset__c")

        if root_id and revised:
            mutual_exclusivity_violations += 1
            if mutual_exclusivity_violations <= 10:  # cap individual row messages
                issues.append(
                    f"ASSETS CSV row {i}: both SBQQ__RootId__c='{root_id}' and "
                    f"SBQQ__RevisedAsset__c='{revised}' are populated — "
                    f"CRITICAL: this silently corrupts amendment chains; "
                    f"SBQQ__RootId__c must be null when SBQQ__RevisedAsset__c is set"
                )

    if mutual_exclusivity_violations > 10:
        issues.append(
            f"ASSETS CSV: {mutual_exclusivity_violations} total rows have both "
            f"SBQQ__RootId__c and SBQQ__RevisedAsset__c populated (showing first 10 only) — "
            f"fix all rows before loading"
        )

    return issues


def check_no_bulk_batch_size_warning(manifest_dir: Path) -> List[str]:
    """
    Warn if any loader config file in the manifest directory suggests a batch size > 1
    for CPQ objects. Looks for Data Loader process-conf.xml style files.
    """
    issues: List[str] = []
    config_files = list(manifest_dir.glob("**/*.xml")) + list(manifest_dir.glob("**/*.properties"))
    for cfg_file in config_files:
        try:
            content = cfg_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Heuristic: if file references SBQQ objects and a batch size > 1
        if any(token in content for token in ("SBQQ__Subscription", "SBQQ__Asset", "SBQQ__Quote")):
            import re
            batch_matches = re.findall(r"batchSize[^0-9]*(\d+)", content, re.IGNORECASE)
            for match in batch_matches:
                if int(match) > 1:
                    issues.append(
                        f"Config file '{cfg_file}' references CPQ objects and has batchSize={match} — "
                        f"CPQ Legacy Data Upload requires batchSize=1 for all CPQ objects"
                    )
    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate CSV files for CPQ Legacy Data Upload (Historical Order Migration). "
            "Checks SBQQ__Quote__c, SBQQ__Subscription__c, and SBQQ__Asset__c CSVs "
            "against the requirements documented in references/gotchas.md."
        ),
    )
    parser.add_argument(
        "--quotes",
        metavar="FILE",
        help="Path to SBQQ__Quote__c CSV prepared for Legacy Data Upload.",
    )
    parser.add_argument(
        "--subscriptions",
        metavar="FILE",
        help="Path to SBQQ__Subscription__c CSV prepared for Legacy Data Upload.",
    )
    parser.add_argument(
        "--assets",
        metavar="FILE",
        help="Path to SBQQ__Asset__c CSV prepared for Legacy Data Upload.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        metavar="DIR",
        help="Directory to scan for loader config files (batch size check). Default: current directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    all_issues: List[str] = []

    if args.quotes:
        all_issues.extend(check_quotes_csv(Path(args.quotes)))

    if args.subscriptions:
        all_issues.extend(check_subscriptions_csv(Path(args.subscriptions)))

    if args.assets:
        all_issues.extend(check_assets_csv(Path(args.assets)))

    manifest_dir = Path(args.manifest_dir)
    if manifest_dir.exists():
        all_issues.extend(check_no_bulk_batch_size_warning(manifest_dir))

    if not all_issues:
        print("No issues found. CSV files appear valid for CPQ Legacy Data Upload.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(all_issues)} issue(s) found. Resolve all before loading.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
