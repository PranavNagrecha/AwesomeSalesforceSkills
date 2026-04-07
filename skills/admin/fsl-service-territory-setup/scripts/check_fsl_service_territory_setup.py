#!/usr/bin/env python3
"""Checker script for FSL Service Territory Setup skill.

Validates Salesforce metadata exports and CSV data extracts for common
FSL service territory configuration issues documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_service_territory_setup.py [--help]
    python3 check_fsl_service_territory_setup.py --manifest-dir path/to/metadata
    python3 check_fsl_service_territory_setup.py --members-csv path/to/members.csv
    python3 check_fsl_service_territory_setup.py --territories-csv path/to/territories.csv

CSV formats expected:
    members.csv    — export of ServiceTerritoryMember with columns:
                     Id, ServiceTerritoryId, ServiceResourceId, MemberType,
                     EffectiveStartDate, EffectiveEndDate
    territories.csv — export of ServiceTerritory with columns:
                     Id, Name, IsActive, OperatingHoursId, ParentTerritoryId
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Limits from FSL documentation
# ---------------------------------------------------------------------------
MEMBERS_PER_TERRITORY_LIMIT = 50
# Note: 1,000 SA/day/territory is a runtime limit, not checkable from metadata.

RELOCATION_MEMBER_TYPE = "Relocation"
PRIMARY_MEMBER_TYPE = "Primary"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSL Service Territory configuration for common issues.\n"
            "Checks against limits and anti-patterns from references/gotchas.md."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce metadata (scans for CustomObject XML).",
    )
    parser.add_argument(
        "--members-csv",
        default=None,
        help="Path to ServiceTerritoryMember CSV export.",
    )
    parser.add_argument(
        "--territories-csv",
        default=None,
        help="Path to ServiceTerritory CSV export.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# CSV-based checks
# ---------------------------------------------------------------------------

def read_csv(path: Path) -> List[Dict[str, str]]:
    """Read a CSV file and return a list of row dicts."""
    rows = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append({k.strip(): v.strip() for k, v in row.items()})
    return rows


def check_member_csv(path: Path) -> List[str]:
    """Validate ServiceTerritoryMember records from a CSV export."""
    issues: List[str] = []

    try:
        rows = read_csv(path)
    except Exception as exc:
        issues.append(f"Could not read members CSV at {path}: {exc}")
        return issues

    if not rows:
        issues.append(f"Members CSV is empty: {path}")
        return issues

    required_columns = {"ServiceTerritoryId", "ServiceResourceId", "MemberType"}
    actual_columns = set(rows[0].keys())
    missing = required_columns - actual_columns
    if missing:
        issues.append(
            f"Members CSV missing required columns: {', '.join(sorted(missing))}. "
            f"Found: {', '.join(sorted(actual_columns))}"
        )
        return issues

    # Count members per territory (for limit check)
    territory_member_counts: Dict[str, int] = defaultdict(int)

    # Track Primary memberships per resource (should be exactly one)
    resource_primary_territories: Dict[str, List[str]] = defaultdict(list)

    relocation_missing_dates: List[str] = []

    for i, row in enumerate(rows, start=2):  # row 1 is header
        territory_id = row.get("ServiceTerritoryId", "")
        resource_id = row.get("ServiceResourceId", "")
        member_type = row.get("MemberType", "")
        start_date = row.get("EffectiveStartDate", "").strip()
        end_date = row.get("EffectiveEndDate", "").strip()
        record_id = row.get("Id", f"row {i}")

        territory_member_counts[territory_id] += 1

        if member_type == PRIMARY_MEMBER_TYPE and resource_id:
            resource_primary_territories[resource_id].append(territory_id)

        if member_type == RELOCATION_MEMBER_TYPE:
            if not start_date or not end_date:
                relocation_missing_dates.append(
                    f"  Record {record_id}: ServiceTerritoryId={territory_id}, "
                    f"ServiceResourceId={resource_id}, "
                    f"EffectiveStartDate={start_date!r}, EffectiveEndDate={end_date!r}"
                )

    # Check territory member count limit
    for territory_id, count in territory_member_counts.items():
        if count > MEMBERS_PER_TERRITORY_LIMIT:
            issues.append(
                f"Territory {territory_id} has {count} members, "
                f"exceeding the {MEMBERS_PER_TERRITORY_LIMIT}-resource limit. "
                "Split into smaller territories or audit for stale memberships."
            )
        elif count > MEMBERS_PER_TERRITORY_LIMIT * 0.8:
            issues.append(
                f"Territory {territory_id} has {count} members "
                f"(>{int(MEMBERS_PER_TERRITORY_LIMIT * 0.8)}, approaching the "
                f"{MEMBERS_PER_TERRITORY_LIMIT}-resource limit). "
                "Review for stale memberships."
            )

    # Check for resources with multiple active Primary memberships
    for resource_id, territories in resource_primary_territories.items():
        if len(territories) > 1:
            issues.append(
                f"ServiceResource {resource_id} has {len(territories)} Primary "
                f"memberships (territories: {', '.join(territories)}). "
                "Only one active Primary membership per resource is valid. "
                "End-date all but one."
            )

    # Report Relocation memberships missing dates
    if relocation_missing_dates:
        issues.append(
            f"Found {len(relocation_missing_dates)} Relocation membership(s) "
            "missing EffectiveStartDate or EffectiveEndDate — these are silently "
            "ignored by the routing engine:\n" + "\n".join(relocation_missing_dates)
        )

    return issues


def check_territory_csv(path: Path) -> List[str]:
    """Validate ServiceTerritory records from a CSV export."""
    issues: List[str] = []

    try:
        rows = read_csv(path)
    except Exception as exc:
        issues.append(f"Could not read territories CSV at {path}: {exc}")
        return issues

    if not rows:
        issues.append(f"Territories CSV is empty: {path}")
        return issues

    required_columns = {"Id", "Name", "IsActive", "OperatingHoursId"}
    actual_columns = set(rows[0].keys())
    missing = required_columns - actual_columns
    if missing:
        issues.append(
            f"Territories CSV missing required columns: {', '.join(sorted(missing))}. "
            f"Found: {', '.join(sorted(actual_columns))}"
        )
        return issues

    territories_missing_hours: List[str] = []

    for row in rows:
        is_active = row.get("IsActive", "").lower()
        if is_active not in ("true", "1", "yes"):
            continue  # only check active territories

        name = row.get("Name", row.get("Id", "unknown"))
        hours_id = row.get("OperatingHoursId", "").strip()

        if not hours_id:
            territories_missing_hours.append(f"  {name}")

    if territories_missing_hours:
        issues.append(
            f"Found {len(territories_missing_hours)} active ServiceTerritory record(s) "
            "with no OperatingHoursId. Scheduling will fail for these territories:\n"
            + "\n".join(territories_missing_hours)
        )

    return issues


# ---------------------------------------------------------------------------
# Metadata XML checks
# ---------------------------------------------------------------------------

def check_manifest_dir(manifest_dir: Path) -> List[str]:
    """Scan Salesforce metadata XML for FSL territory-related issues."""
    issues: List[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for the presence of any FSL-related permission set or feature flag
    # that suggests Field Service is not enabled.
    xml_files = list(manifest_dir.rglob("*.xml"))
    if not xml_files:
        issues.append(
            f"No XML files found under {manifest_dir}. "
            "If this is a Salesforce DX project, ensure metadata has been retrieved."
        )
        return issues

    # Look for ServiceTerritory custom fields or layouts, which indicates FSL is in use.
    fsl_territory_references = 0
    etm_territory_references: List[str] = []

    # Pattern for ETM objects in metadata (Territory2, UserTerritory2Association)
    etm_pattern = re.compile(
        r"Territory2|UserTerritory2Association|ObjectTerritory2Association|TerritoryModel",
        re.IGNORECASE,
    )
    # Pattern for FSL territory references
    fsl_pattern = re.compile(r"ServiceTerritory|ServiceTerritoryMember", re.IGNORECASE)

    for xml_file in xml_files:
        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        if fsl_pattern.search(content):
            fsl_territory_references += 1

        etm_matches = etm_pattern.findall(content)
        if etm_matches:
            etm_territory_references.append(
                f"  {xml_file.relative_to(manifest_dir)}: "
                f"found ETM references: {set(etm_matches)}"
            )

    if fsl_territory_references == 0:
        issues.append(
            "No ServiceTerritory or ServiceTerritoryMember references found in metadata. "
            "Confirm Field Service is enabled and metadata has been retrieved."
        )

    if etm_territory_references:
        issues.append(
            f"Found {len(etm_territory_references)} file(s) with Enterprise Territory "
            "Management (ETM) object references (Territory2, UserTerritory2Association, "
            "etc.). ETM and FSL ServiceTerritory are separate systems — verify that ETM "
            "references are intentional and not the result of ETM/FSL confusion:\n"
            + "\n".join(etm_territory_references[:10])
            + ("" if len(etm_territory_references) <= 10 else "\n  ... and more")
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    all_issues: List[str] = []

    ran_any_check = False

    if args.manifest_dir:
        ran_any_check = True
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_manifest_dir(manifest_dir))

    if args.members_csv:
        ran_any_check = True
        members_path = Path(args.members_csv)
        all_issues.extend(check_member_csv(members_path))

    if args.territories_csv:
        ran_any_check = True
        territories_path = Path(args.territories_csv)
        all_issues.extend(check_territory_csv(territories_path))

    if not ran_any_check:
        # Default: scan the current directory as manifest dir
        all_issues.extend(check_manifest_dir(Path(".")))

    if not all_issues:
        print("No FSL service territory issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
