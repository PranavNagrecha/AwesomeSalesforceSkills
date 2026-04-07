#!/usr/bin/env python3
"""Checker script for Marketing Cloud Data Sync skill.

Validates Marketing Cloud Connect Synchronized Data Source configuration
metadata and related Data Extension definitions for common mis-configurations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_cloud_data_sync.py [--help]
    python3 check_marketing_cloud_data_sync.py --manifest-dir path/to/metadata
    python3 check_marketing_cloud_data_sync.py --sde-field-csv path/to/sde_fields.csv

Checks performed:
  1. SDE field count per object (warns if approaching or exceeding 250-field cap)
  2. Presence of unsupported field type keywords in field lists
  3. Detects any automation config files that reference an SDE as a write target
  4. Verifies that a sendable DE (non-SDE) is defined alongside each SDE
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Known SDE names follow a convention: they end with _Salesforce or _SF by default.
# Users can override this suffix pattern with --sde-suffix.
DEFAULT_SDE_SUFFIX = "_Salesforce"

# Unsupported field type keywords that should never appear in an SDE field list.
UNSUPPORTED_FIELD_TYPES = {
    "encryptedstring",
    "blob",
    "richtextarea",
    "rta",
    "base64",
}

# Hard field cap per synchronized object.
FIELD_CAP = 250
# Warn when approaching the cap.
FIELD_CAP_WARNING_THRESHOLD = 230


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Marketing Cloud Connect Synchronized Data Source configuration "
            "for common mis-configurations (250-field cap, unsupported types, "
            "SDE write targets, missing sendable DEs)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help=(
            "Root directory of exported Marketing Cloud metadata or automation "
            "config files. Scanned for DE definitions and automation references."
        ),
    )
    parser.add_argument(
        "--sde-field-csv",
        default=None,
        help=(
            "Path to a CSV file listing SDE fields. Expected columns: "
            "ObjectName, FieldName, FieldType. "
            "One row per field. Used to check field counts and unsupported types."
        ),
    )
    parser.add_argument(
        "--sde-suffix",
        default=DEFAULT_SDE_SUFFIX,
        help=(
            f"Suffix used to identify Synchronized Data Extensions in DE name lists "
            f"(default: '{DEFAULT_SDE_SUFFIX}')."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Check: SDE field count from CSV
# ---------------------------------------------------------------------------

def check_sde_field_counts(csv_path: Path, sde_suffix: str) -> list[str]:
    """Parse an SDE field CSV and flag objects at or near the 250-field cap.

    CSV format: ObjectName, FieldName, FieldType (header row optional).
    """
    issues: list[str] = []

    if not csv_path.exists():
        issues.append(f"SDE field CSV not found: {csv_path}")
        return issues

    field_counts: dict[str, int] = {}
    unsupported_hits: list[tuple[str, str, str]] = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, start=1):
            if not row:
                continue
            # Skip header row if present
            if row_num == 1 and row[0].strip().lower() in ("objectname", "object", "object_name"):
                continue
            if len(row) < 2:
                continue

            obj_name = row[0].strip()
            field_name = row[1].strip() if len(row) > 1 else ""
            field_type = row[2].strip().lower() if len(row) > 2 else ""

            if not obj_name:
                continue

            field_counts[obj_name] = field_counts.get(obj_name, 0) + 1

            if field_type in UNSUPPORTED_FIELD_TYPES:
                unsupported_hits.append((obj_name, field_name, field_type))

    for obj, count in sorted(field_counts.items()):
        if count > FIELD_CAP:
            issues.append(
                f"FIELD_CAP_EXCEEDED: Object '{obj}' has {count} fields selected for sync "
                f"(cap is {FIELD_CAP}). Fields beyond position {FIELD_CAP} are silently excluded "
                f"— no error is shown. Reduce field selection immediately."
            )
        elif count >= FIELD_CAP_WARNING_THRESHOLD:
            issues.append(
                f"FIELD_CAP_WARNING: Object '{obj}' has {count} fields selected for sync "
                f"(cap is {FIELD_CAP}, warning at {FIELD_CAP_WARNING_THRESHOLD}). "
                f"Any future field additions risk silent exclusion."
            )

    for obj, field, ftype in unsupported_hits:
        issues.append(
            f"UNSUPPORTED_FIELD_TYPE: Object '{obj}', field '{field}' has type '{ftype}' "
            f"which is not supported by MC Connect sync. This field will be silently excluded. "
            f"Remove it from the sync selection or create a compatible shadow field in CRM."
        )

    return issues


# ---------------------------------------------------------------------------
# Check: manifest directory for SDE write targets and sendable DE presence
# ---------------------------------------------------------------------------

def check_manifest_dir(manifest_dir: Path, sde_suffix: str) -> list[str]:
    """Scan metadata/config files in manifest_dir for SDE mis-configurations."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Collect all text-based config files (JSON, XML, CSV, TXT, YAML)
    config_files = list(manifest_dir.rglob("*.json"))
    config_files += list(manifest_dir.rglob("*.xml"))
    config_files += list(manifest_dir.rglob("*.yaml"))
    config_files += list(manifest_dir.rglob("*.yml"))

    sde_names_found: set[str] = set()
    sendable_de_names_found: set[str] = set()

    for cfg_file in config_files:
        try:
            text = cfg_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        lower_text = text.lower()

        # Detect SDE names referenced in the file
        # Heuristic: look for strings ending with the SDE suffix
        for line in text.splitlines():
            stripped = line.strip().strip('"').strip("'").strip(",")
            if stripped.lower().endswith(sde_suffix.lower()):
                sde_names_found.add(stripped)

        # Detect write operations targeting an SDE
        # Common patterns: "targetDE", "destinationDataExtension", "UpsertDE", "InsertDE"
        write_target_keywords = [
            "targetde", "destination_data_extension", "destinationdataextension",
            "upsertde", "insertde", "updatede",
        ]
        for keyword in write_target_keywords:
            if keyword in lower_text:
                # Check if any SDE suffix name appears near this keyword
                for sde_name in sde_names_found:
                    if sde_name.lower() in lower_text:
                        # Rough proximity check: both keyword and SDE name appear
                        issues.append(
                            f"SDE_WRITE_TARGET_SUSPECTED: File '{cfg_file.name}' contains "
                            f"a write-operation keyword ('{keyword}') alongside a suspected SDE name "
                            f"('{sde_name}'). SDEs are read-only — verify this is not targeting "
                            f"an SDE as a write destination."
                        )
                        break

        # Detect sendable DEs (non-SDE DEs that could be valid send audiences)
        # Heuristic: "sendRelationship" or "isSendable" in config
        if "issendable" in lower_text or "sendrelationship" in lower_text:
            for line in text.splitlines():
                if "issendable" in line.lower() or "sendrelationship" in line.lower():
                    sendable_de_names_found.add(cfg_file.stem)

    # Warn if SDE names found but no sendable DE detected
    if sde_names_found and not sendable_de_names_found:
        issues.append(
            f"NO_SENDABLE_DE_DETECTED: Synchronized Data Extensions detected "
            f"({', '.join(sorted(sde_names_found))}) but no sendable Data Extension "
            f"configuration found (no 'isSendable' or 'sendRelationship' marker). "
            f"SDEs cannot be used as send audiences — a sendable DE with a Contact Builder "
            f"relationship must exist."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.sde_field_csv:
        csv_path = Path(args.sde_field_csv)
        all_issues.extend(check_sde_field_counts(csv_path, args.sde_suffix))

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_manifest_dir(manifest_dir, args.sde_suffix))

    if not args.sde_field_csv and not args.manifest_dir:
        print(
            "INFO: No inputs provided. Pass --sde-field-csv and/or --manifest-dir to run checks.\n"
            "Run with --help for usage details.",
            file=sys.stderr,
        )
        return 0

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
