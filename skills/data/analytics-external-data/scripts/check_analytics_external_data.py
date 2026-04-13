#!/usr/bin/env python3
"""Checker script for Analytics External Data skill.

Validates metadata artifacts and integration patterns related to CRM Analytics
external data ingestion: External Data API (InsightsExternalData), Data Connectors,
and Live Datasets.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_external_data.py [--help]
    python3 check_analytics_external_data.py --manifest-dir path/to/metadata
    python3 check_analytics_external_data.py --json-schema path/to/metadata.json
    python3 check_analytics_external_data.py --script-dir path/to/scripts
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics external data configuration and integration scripts "
            "for common issues: missing metadata schema, wrong tool usage, Live Dataset "
            "anti-patterns, and External Data API sequencing errors."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--json-schema",
        default=None,
        help="Path to an InsightsExternalData metadata JSON file to validate.",
    )
    parser.add_argument(
        "--script-dir",
        default=None,
        help="Directory containing integration scripts to scan for anti-patterns.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Metadata JSON schema validation
# ---------------------------------------------------------------------------

VALID_FIELD_TYPES = {"Text", "Numeric", "Date", "Dimension"}

def validate_external_data_schema(schema_path: Path) -> list[str]:
    """Validate an InsightsExternalData metadata JSON file structure."""
    issues: list[str] = []

    try:
        text = schema_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Cannot read schema file {schema_path}: {exc}"]

    try:
        schema = json.loads(text)
    except json.JSONDecodeError as exc:
        return [f"Invalid JSON in {schema_path}: {exc}"]

    # Top-level structure
    if "objects" not in schema:
        issues.append(
            f"{schema_path.name}: Missing required top-level 'objects' array. "
            "InsightsExternalData MetadataJson must contain an 'objects' list."
        )
        return issues

    objects = schema["objects"]
    if not isinstance(objects, list) or len(objects) == 0:
        issues.append(
            f"{schema_path.name}: 'objects' must be a non-empty array."
        )
        return issues

    for obj_idx, obj in enumerate(objects):
        obj_name = obj.get("name", f"<object[{obj_idx}]>")

        required_obj_keys = {"connector", "fullyQualifiedName", "label", "name", "fields"}
        missing = required_obj_keys - set(obj.keys())
        if missing:
            issues.append(
                f"{schema_path.name}: Object '{obj_name}' missing required keys: "
                f"{', '.join(sorted(missing))}"
            )

        fields = obj.get("fields", [])
        if not isinstance(fields, list) or len(fields) == 0:
            issues.append(
                f"{schema_path.name}: Object '{obj_name}' has no fields defined."
            )
            continue

        for field_idx, field in enumerate(fields):
            field_name = field.get("name", f"<field[{field_idx}]>")
            field_type = field.get("type", "")

            if field_type not in VALID_FIELD_TYPES:
                issues.append(
                    f"{schema_path.name}: Field '{field_name}' in '{obj_name}' has "
                    f"unsupported type '{field_type}'. "
                    f"Valid types: {', '.join(sorted(VALID_FIELD_TYPES))}"
                )

            for required_key in ("fullyQualifiedName", "name", "label", "type"):
                if required_key not in field:
                    issues.append(
                        f"{schema_path.name}: Field '{field_name}' in '{obj_name}' "
                        f"is missing required key '{required_key}'."
                    )

    return issues


# ---------------------------------------------------------------------------
# Script anti-pattern scanning
# ---------------------------------------------------------------------------

# Pattern: using Data Loader CLI or Bulk API instead of External Data API
BULK_API_ANTI_PATTERN = re.compile(
    r"(sfdx\s+force:data:bulk|data\.loader|DataLoader|api_asynch|/services/async/)",
    re.IGNORECASE,
)

# Pattern: uploading InsightsExternalDataPart before creating InsightsExternalData header
# Heuristic: DataPart appears before InsightsExternalData in the same file
PART_BEFORE_HEADER_PATTERN = re.compile(
    r"InsightsExternalDataPart",
    re.IGNORECASE,
)
HEADER_PATTERN = re.compile(
    r"InsightsExternalData[^P]",
    re.IGNORECASE,
)

# Pattern: claiming Live Datasets refresh or are scheduled
LIVE_DATASET_REFRESH_ANTI_PATTERN = re.compile(
    r"(live.?dataset.{0,40}(refresh|schedule|sync)|"
    r"(refresh|schedule|sync).{0,40}live.?dataset)",
    re.IGNORECASE,
)

# Pattern: treating Remote Connection as data sync
REMOTE_CONNECTION_SYNC_ANTI_PATTERN = re.compile(
    r"remote.?connection.{0,50}(sync|import|load|upload|ingest)",
    re.IGNORECASE,
)


def scan_script_for_antipatterns(script_path: Path) -> list[str]:
    """Scan a single script file for External Data API anti-patterns."""
    issues: list[str] = []

    try:
        text = script_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"Cannot read {script_path}: {exc}"]

    if BULK_API_ANTI_PATTERN.search(text):
        issues.append(
            f"{script_path.name}: Possible Bulk API or Data Loader usage detected. "
            "CRM Analytics datasets cannot be populated via Bulk API or Data Loader — "
            "use the External Data API (InsightsExternalData SObject) instead."
        )

    # Check for DataPart before header — heuristic: DataPart appears on a lower line number
    lines = text.splitlines()
    first_header_line = None
    first_part_line = None
    for i, line in enumerate(lines):
        if first_header_line is None and HEADER_PATTERN.search(line):
            first_header_line = i
        if first_part_line is None and PART_BEFORE_HEADER_PATTERN.search(line):
            first_part_line = i

    if first_part_line is not None and first_header_line is None:
        issues.append(
            f"{script_path.name}: InsightsExternalDataPart referenced but no "
            "InsightsExternalData header found. The header record (with MetadataJson) "
            "must be created before any DataPart records are uploaded."
        )
    elif (
        first_part_line is not None
        and first_header_line is not None
        and first_part_line < first_header_line
    ):
        issues.append(
            f"{script_path.name}: InsightsExternalDataPart (line {first_part_line + 1}) "
            f"appears before InsightsExternalData header (line {first_header_line + 1}). "
            "Upload the header record with MetadataJson first."
        )

    if LIVE_DATASET_REFRESH_ANTI_PATTERN.search(text):
        issues.append(
            f"{script_path.name}: Text suggests a Live Dataset has a refresh or schedule. "
            "Live Datasets do NOT refresh or store data — they query the external system "
            "at runtime on every dashboard load."
        )

    if REMOTE_CONNECTION_SYNC_ANTI_PATTERN.search(text):
        issues.append(
            f"{script_path.name}: Text suggests a Remote Connection syncs or imports data. "
            "Remote Connections are credential configuration objects only. To move data, "
            "create a Recipe, Dataflow, or Live Dataset that references the Remote Connection."
        )

    return issues


def scan_script_directory(script_dir: Path) -> list[str]:
    """Scan all Python and shell scripts in a directory for anti-patterns."""
    issues: list[str] = []

    if not script_dir.exists():
        return [f"Script directory not found: {script_dir}"]

    script_files = list(script_dir.glob("**/*.py")) + list(script_dir.glob("**/*.sh"))
    if not script_files:
        return []

    for script_path in sorted(script_files):
        issues.extend(scan_script_for_antipatterns(script_path))

    return issues


# ---------------------------------------------------------------------------
# Manifest directory checks
# ---------------------------------------------------------------------------

def check_manifest_directory(manifest_dir: Path) -> list[str]:
    """Check a Salesforce metadata manifest directory for common issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for any JSON files that look like External Data metadata schemas
    schema_candidates = list(manifest_dir.glob("**/*metadata*.json")) + \
                        list(manifest_dir.glob("**/*schema*.json")) + \
                        list(manifest_dir.glob("**/*InsightsExternalData*.json"))

    for candidate in schema_candidates:
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
            data = json.loads(text)
            if "objects" in data and isinstance(data["objects"], list):
                # Looks like an External Data metadata schema — validate it
                issues.extend(validate_external_data_schema(candidate))
        except (json.JSONDecodeError, OSError):
            pass

    # Look for Python or shell scripts that integrate with External Data API
    script_files = list(manifest_dir.glob("**/*.py")) + list(manifest_dir.glob("**/*.sh"))
    for script_path in script_files:
        try:
            text = script_path.read_text(encoding="utf-8", errors="replace")
            if "InsightsExternalData" in text or "external_data" in text.lower():
                issues.extend(scan_script_for_antipatterns(script_path))
        except OSError:
            pass

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    # Validate explicit JSON schema file if provided
    if args.json_schema:
        schema_path = Path(args.json_schema)
        all_issues.extend(validate_external_data_schema(schema_path))

    # Scan explicit script directory if provided
    if args.script_dir:
        script_dir = Path(args.script_dir)
        all_issues.extend(scan_script_directory(script_dir))

    # Scan manifest directory (default or provided)
    manifest_dir = Path(args.manifest_dir)
    if manifest_dir != Path(".") or (args.json_schema is None and args.script_dir is None):
        all_issues.extend(check_manifest_directory(manifest_dir))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
