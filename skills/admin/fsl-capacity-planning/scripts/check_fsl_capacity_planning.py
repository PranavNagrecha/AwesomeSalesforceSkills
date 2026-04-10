#!/usr/bin/env python3
"""Checker script for FSL Capacity Planning skill.

Validates CSV exports of ServiceResourceCapacity and WorkCapacityLimit records
for common configuration problems — date gaps, zero-capacity records, and missing
IsCapacityBased flags.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_capacity_planning.py --help
    python3 check_fsl_capacity_planning.py --manifest-dir path/to/csv-exports

Expected CSV files (any matching name is accepted):
    *ServiceResourceCapacity*.csv
        Required columns: Id, ServiceResourceId, StartDate, EndDate, Capacity, CapacityUnit
    *WorkCapacityLimit*.csv
        Required columns: Id, ServiceTerritoryId, WorkTypeId, CapacityWindow, CapacityLimit, StartDate, EndDate
    *ServiceResource*.csv  (optional, for IsCapacityBased cross-check)
        Required columns: Id, Name, IsCapacityBased
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(value: str) -> date | None:
    """Parse an ISO-8601 date string (YYYY-MM-DD). Return None on failure."""
    value = value.strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _load_csv(path: Path) -> list[dict[str, str]]:
    """Load a CSV file and return a list of row dicts."""
    rows: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append({k.strip(): v.strip() for k, v in row.items()})
    return rows


def _find_csv(manifest_dir: Path, keyword: str) -> list[Path]:
    """Return all CSV files in manifest_dir whose name contains keyword (case-insensitive)."""
    return [
        p for p in manifest_dir.glob("*.csv")
        if keyword.lower() in p.name.lower()
    ]


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_resource_capacity_gaps(manifest_dir: Path) -> list[str]:
    """Detect date gaps between ServiceResourceCapacity records for the same resource.

    A gap of even 1 day silently prevents scheduling for that resource on that date.
    """
    issues: list[str] = []
    paths = _find_csv(manifest_dir, "ServiceResourceCapacity")
    if not paths:
        return issues  # No data to check; skip silently

    all_rows: list[dict[str, str]] = []
    for p in paths:
        all_rows.extend(_load_csv(p))

    # Group by resource ID
    by_resource: dict[str, list[tuple[date, date, str]]] = {}
    for row in all_rows:
        rid = row.get("ServiceResourceId", "").strip()
        start = _parse_date(row.get("StartDate", ""))
        end = _parse_date(row.get("EndDate", ""))
        rec_id = row.get("Id", "unknown")
        if not rid or not start or not end:
            issues.append(
                f"ServiceResourceCapacity record {rec_id}: missing ServiceResourceId, "
                "StartDate, or EndDate — record may be invalid."
            )
            continue
        by_resource.setdefault(rid, []).append((start, end, rec_id))

    for rid, periods in by_resource.items():
        # Sort by start date
        periods.sort(key=lambda t: t[0])
        for i in range(len(periods) - 1):
            current_end = periods[i][1]
            next_start = periods[i + 1][0]
            expected_next = current_end + timedelta(days=1)
            if next_start > expected_next:
                gap_start = current_end + timedelta(days=1)
                gap_end = next_start - timedelta(days=1)
                issues.append(
                    f"ServiceResourceCapacity: resource {rid} has a date gap from "
                    f"{gap_start} to {gap_end} — scheduling is silently blocked on those days."
                )

    return issues


def check_zero_capacity_records(manifest_dir: Path) -> list[str]:
    """Warn about ServiceResourceCapacity records with Capacity = 0 or blank."""
    issues: list[str] = []
    paths = _find_csv(manifest_dir, "ServiceResourceCapacity")
    if not paths:
        return issues

    for p in paths:
        for row in _load_csv(p):
            rec_id = row.get("Id", "unknown")
            capacity_raw = row.get("Capacity", "").strip()
            try:
                capacity = float(capacity_raw)
            except ValueError:
                issues.append(
                    f"ServiceResourceCapacity record {rec_id}: Capacity value "
                    f"'{capacity_raw}' is not a number — record will not enforce any cap."
                )
                continue
            if capacity <= 0:
                issues.append(
                    f"ServiceResourceCapacity record {rec_id}: Capacity is {capacity} "
                    "— zero or negative capacity makes this resource unschedulable."
                )

    return issues


def check_work_capacity_limit_zero(manifest_dir: Path) -> list[str]:
    """Warn about WorkCapacityLimit records with CapacityLimit = 0 or blank."""
    issues: list[str] = []
    paths = _find_csv(manifest_dir, "WorkCapacityLimit")
    if not paths:
        return issues

    for p in paths:
        for row in _load_csv(p):
            rec_id = row.get("Id", "unknown")
            limit_raw = row.get("CapacityLimit", "").strip()
            try:
                limit = float(limit_raw)
            except ValueError:
                issues.append(
                    f"WorkCapacityLimit record {rec_id}: CapacityLimit value "
                    f"'{limit_raw}' is not a number — record will silently block all scheduling."
                )
                continue
            if limit <= 0:
                issues.append(
                    f"WorkCapacityLimit record {rec_id}: CapacityLimit is {limit} "
                    "— a zero or negative limit silently blocks all scheduling for this territory/work type."
                )

    return issues


def check_work_capacity_limit_expired(manifest_dir: Path) -> list[str]:
    """Warn about WorkCapacityLimit records whose EndDate is in the past."""
    issues: list[str] = []
    paths = _find_csv(manifest_dir, "WorkCapacityLimit")
    if not paths:
        return issues

    today = date.today()
    for p in paths:
        for row in _load_csv(p):
            rec_id = row.get("Id", "unknown")
            end = _parse_date(row.get("EndDate", ""))
            if end and end < today:
                issues.append(
                    f"WorkCapacityLimit record {rec_id}: EndDate {end} is in the past "
                    "— this limit is no longer active. Remove or update if no longer needed."
                )

    return issues


def check_resource_capacity_without_flag(manifest_dir: Path) -> list[str]:
    """Warn if ServiceResourceCapacity records exist for resources where IsCapacityBased = false.

    Requires both ServiceResourceCapacity and ServiceResource CSV exports to be present.
    """
    issues: list[str] = []
    cap_paths = _find_csv(manifest_dir, "ServiceResourceCapacity")
    res_paths = _find_csv(manifest_dir, "ServiceResource")
    if not cap_paths or not res_paths:
        return issues  # Cannot cross-check without both files

    # Build resource flag map: Id -> IsCapacityBased
    flag_map: dict[str, str] = {}
    for p in res_paths:
        for row in _load_csv(p):
            rid = row.get("Id", "").strip()
            flag = row.get("IsCapacityBased", "").strip().lower()
            if rid:
                flag_map[rid] = flag

    # Check each capacity record
    for p in cap_paths:
        for row in _load_csv(p):
            rec_id = row.get("Id", "unknown")
            rid = row.get("ServiceResourceId", "").strip()
            if not rid:
                continue
            flag = flag_map.get(rid)
            if flag is None:
                # Resource not found in the resource CSV — skip silently
                continue
            if flag not in ("true", "1", "yes"):
                issues.append(
                    f"ServiceResourceCapacity record {rec_id}: ServiceResource {rid} "
                    "has IsCapacityBased = false — this capacity record will be silently "
                    "ignored by the FSL scheduler."
                )

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_fsl_capacity_planning(manifest_dir: Path) -> list[str]:
    """Run all FSL capacity planning checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_resource_capacity_gaps(manifest_dir))
    issues.extend(check_zero_capacity_records(manifest_dir))
    issues.extend(check_work_capacity_limit_zero(manifest_dir))
    issues.extend(check_work_capacity_limit_expired(manifest_dir))
    issues.extend(check_resource_capacity_without_flag(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSL Capacity Planning configuration from CSV exports of "
            "ServiceResourceCapacity, WorkCapacityLimit, and ServiceResource objects."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Directory containing CSV exports (default: current directory). "
            "Expects files matching *ServiceResourceCapacity*.csv, "
            "*WorkCapacityLimit*.csv, and optionally *ServiceResource*.csv."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_capacity_planning(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
