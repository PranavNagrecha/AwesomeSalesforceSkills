#!/usr/bin/env python3
"""Checker script for FSL Territory Data Setup skill.

Scans CSV data files for common FSL territory migration issues:
- ServiceTerritoryMember missing EffectiveStartDate
- ServiceTerritoryMember missing TerritoryType
- ServiceTerritory records exceeding recommended 50-member limit

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_territory_data_setup.py [--help]
    python3 check_fsl_territory_data_setup.py --manifest-dir path/to/data-extracts
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

_TERRITORY_MEMBER_LIMIT = 50  # recommended max resources per territory


def check_fsl_territory_data_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    csv_files = list(manifest_dir.rglob("*.csv"))
    if not csv_files:
        return issues

    for csv_file in csv_files:
        fname_lower = csv_file.name.lower()

        # Check ServiceTerritoryMember CSVs
        if "serviceterritorymember" in fname_lower or "territory_member" in fname_lower or "stm" in fname_lower:
            try:
                with csv_file.open(encoding="utf-8-sig", errors="replace") as f:
                    reader = csv.DictReader(f)
                    headers = [h.lower() for h in (reader.fieldnames or [])]

                    rel = csv_file.relative_to(manifest_dir)

                    # Check for EffectiveStartDate column
                    if not any("effectivestartdate" in h or "effective_start" in h for h in headers):
                        issues.append(
                            f"{rel}: ServiceTerritoryMember file missing EffectiveStartDate column. "
                            "EffectiveStartDate is required on all ServiceTerritoryMember records."
                        )

                    # Check for TerritoryType column
                    if not any("territorytype" in h or "territory_type" in h for h in headers):
                        issues.append(
                            f"{rel}: ServiceTerritoryMember file missing TerritoryType column. "
                            "Always set TerritoryType explicitly (Primary/Secondary/Relocation). "
                            "Omitting defaults to Primary, which misclassifies contractors."
                        )

                    # Count members per territory (heuristic)
                    territory_counts: dict[str, int] = {}
                    for row in reader:
                        tid = row.get("ServiceTerritoryId") or row.get("serviceterritoryid") or ""
                        if tid:
                            territory_counts[tid] = territory_counts.get(tid, 0) + 1

                    for tid, count in territory_counts.items():
                        if count > _TERRITORY_MEMBER_LIMIT:
                            issues.append(
                                f"{rel}: Territory {tid!r} has {count} members in this file, "
                                f"exceeding the recommended limit of {_TERRITORY_MEMBER_LIMIT}. "
                                "Territories over 50 resources cause FSL optimization timeouts."
                            )

            except (OSError, csv.Error):
                continue

        # Check ServiceTerritory CSVs for External ID
        if "serviceterritory" in fname_lower and "member" not in fname_lower:
            try:
                with csv_file.open(encoding="utf-8-sig", errors="replace") as f:
                    reader = csv.DictReader(f)
                    headers = [h.lower() for h in (reader.fieldnames or [])]
                    rel = csv_file.relative_to(manifest_dir)

                    has_ext_id = any(
                        any(p in h for p in ("legacy", "external", "__c")) for h in headers
                    )
                    if not has_ext_id:
                        issues.append(
                            f"{rel}: ServiceTerritory file may be missing an External ID column. "
                            "Add a Legacy_Id__c field for safe upsert and child territory parent lookups."
                        )
            except (OSError, csv.Error):
                continue

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSL territory data CSV files for common migration issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing migration CSV files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_territory_data_setup(manifest_dir)

    if not issues:
        print("No FSL Territory Data Setup issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
