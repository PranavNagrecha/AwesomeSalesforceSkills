#!/usr/bin/env python3
"""Checker script for Analytics Dataset Management skill.

Scans Salesforce metadata under a manifest directory for common CRM Analytics
dataset and dataflow configuration issues documented in this skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_dataset_management.py [--help]
    python3 check_analytics_dataset_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics dataflow and dataset configuration for common issues:\n"
            "  - Date fields missing type declaration (stored as Text)\n"
            "  - Dataflow schedule frequency and estimated quota consumption\n"
            "  - Append-mode datasets with no documented trim strategy\n"
            "  - Missing register node in dataflow definitions\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

KNOWN_DATE_FIELD_SUFFIXES = ("Date", "DateTime", "CreatedDate", "LastModifiedDate")
KNOWN_DATE_FIELD_NAMES = {
    "CloseDate", "ActivityDate", "CreatedDate", "LastModifiedDate",
    "StartDate", "EndDate", "BirthDate", "ConvertedDate",
}

# Salesforce-documented org-wide run limit per 24-hour window
DATAFLOW_RUN_QUOTA = 60
QUOTA_WARNING_THRESHOLD = 50  # warn before hitting the ceiling


def _load_json_file(path: Path) -> dict | list | None:
    """Load a JSON file and return parsed content, or None on failure."""
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _has_schema_node_for_field(dataflow_def: dict, field_name: str) -> bool:
    """Return True if any schema transformation in the dataflow declares the given field as Date."""
    for node_name, node in dataflow_def.items():
        if not isinstance(node, dict):
            continue
        if node.get("action") != "schema":
            continue
        params = node.get("parameters", {})
        fields = params.get("fields", [])
        for f in fields:
            if isinstance(f, dict) and f.get("name") == field_name and f.get("type") == "Date":
                return True
    return False


def _has_filter_or_trim_node(dataflow_def: dict) -> bool:
    """Return True if the dataflow contains any filter transformation node."""
    for node_name, node in dataflow_def.items():
        if isinstance(node, dict) and node.get("action") in ("filter", "sliceDataset"):
            return True
    return False


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_dataflow_files(manifest_dir: Path) -> list[str]:
    """Scan all *.wdf (dataflow definition) and *.json files in wave/dataflow paths."""
    issues: list[str] = []

    # CRM Analytics dataflow files are typically in wave/ or analytics/ directories
    # and have .wdf or .json extensions
    candidate_dirs = [
        manifest_dir / "wave",
        manifest_dir / "analytics",
        manifest_dir / "CRM_Analytics",
        manifest_dir,
    ]

    dataflow_files: list[Path] = []
    for candidate in candidate_dirs:
        if not candidate.is_dir():
            continue
        # .wdf files are CRM Analytics dataflow definitions
        dataflow_files.extend(candidate.rglob("*.wdf"))
        # Only pick up JSON files that are explicitly inside wave/ or analytics/ subdirectories
        # to avoid false positives on unrelated JSON files (e.g. registry skill records)
        if candidate.name.lower() in ("wave", "analytics", "crm_analytics"):
            dataflow_files.extend(candidate.rglob("*.json"))

    if not dataflow_files:
        return issues  # No dataflow files found — nothing to check

    total_estimated_daily_runs = 0

    for df_path in dataflow_files:
        dataflow_def = _load_json_file(df_path)
        if not isinstance(dataflow_def, dict):
            issues.append(
                f"Could not parse dataflow JSON: {df_path.relative_to(manifest_dir)} — "
                "verify the file is valid JSON."
            )
            continue

        rel_path = df_path.relative_to(manifest_dir)

        # Check 1: sfdcDigest nodes that pull known date fields without a schema node
        for node_name, node in dataflow_def.items():
            if not isinstance(node, dict):
                continue
            if node.get("action") != "sfdcDigest":
                continue

            params = node.get("parameters", {})
            fields_list = params.get("fields", [])
            for f in fields_list:
                fname = f.get("name", "") if isinstance(f, dict) else str(f)
                is_known_date = (
                    fname in KNOWN_DATE_FIELD_NAMES
                    or any(fname.endswith(s) for s in KNOWN_DATE_FIELD_SUFFIXES)
                )
                if is_known_date and not _has_schema_node_for_field(dataflow_def, fname):
                    issues.append(
                        f"[{rel_path}] Field '{fname}' in sfdcDigest node '{node_name}' "
                        "appears to be a Date field but has no schema transformation declaring "
                        "type='Date'. It will be stored as Text and cannot be used in "
                        "timeseries or date range filters. Add a schema node with "
                        "type='Date' and the correct format string."
                    )

        # Check 2: Dataflow has no register node (dataset will not be written)
        has_register = any(
            isinstance(n, dict) and n.get("action") in ("sfdcRegister", "register")
            for n in dataflow_def.values()
        )
        if not has_register:
            issues.append(
                f"[{rel_path}] No sfdcRegister node found in dataflow. "
                "The dataflow will execute transformations but will not write any dataset. "
                "Add a register node at the end of the pipeline."
            )

        # Check 3: Dataflow has append-mode register without any filter/trim node
        for node_name, node in dataflow_def.items():
            if not isinstance(node, dict):
                continue
            if node.get("action") not in ("sfdcRegister", "register"):
                continue
            params = node.get("parameters", {})
            mode = params.get("mode", "")
            if mode.lower() == "append" and not _has_filter_or_trim_node(dataflow_def):
                issues.append(
                    f"[{rel_path}] Register node '{node_name}' uses append mode but "
                    "no filter or sliceDataset node was found. Append-mode datasets grow "
                    "without bound toward the 500M org-wide row ceiling. Add a filter node "
                    "to restrict rows to a rolling time window (e.g., last 13 months)."
                )

        # Count this as one scheduled run per day for quota estimation
        # (conservative — real frequency depends on the schedule config)
        total_estimated_daily_runs += 1

    # Check 4: Quota estimation
    if total_estimated_daily_runs >= QUOTA_WARNING_THRESHOLD:
        issues.append(
            f"Estimated daily dataflow run count from scanned files: "
            f"{total_estimated_daily_runs}. This approaches the org-wide limit of "
            f"{DATAFLOW_RUN_QUOTA} runs per 24-hour window. Account for managed-package "
            "dataflows (Revenue Intelligence, Service Analytics, etc.) which also consume "
            "quota. Reduce frequency or combine flows if the total exceeds 55 runs/day."
        )

    return issues


def check_manifest_structure(manifest_dir: Path) -> list[str]:
    """Basic structural checks on the manifest directory."""
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
    elif not manifest_dir.is_dir():
        issues.append(f"Manifest path is not a directory: {manifest_dir}")
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_analytics_dataset_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []
    issues.extend(check_manifest_structure(manifest_dir))
    if issues:
        return issues  # Can't proceed without a valid directory
    issues.extend(check_dataflow_files(manifest_dir))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_dataset_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
