#!/usr/bin/env python3
"""Checker script for Analytics Dataset Optimization skill.

Inspects CRM Analytics dataflow JSON files and Recipe metadata in a Salesforce
DX project directory for common dataset optimization problems:

  1. Over-wide sfdcDigest nodes (field count above warning threshold)
  2. Date fields ingested without explicit type declaration (likely stored as Text)
  3. Dataflows that include all Salesforce object fields (no fields list = SELECT *)
  4. Possible epoch pre-computation opportunities (date field pairs in same sfdcDigest)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_dataset_optimization.py [--help]
    python3 check_analytics_dataset_optimization.py --manifest-dir path/to/sfdx/project
    python3 check_analytics_dataset_optimization.py --manifest-dir . --warn-field-count 100
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Fields that are almost certainly date or datetime fields by name convention.
_DATE_FIELD_SUFFIXES = (
    "Date",
    "DateTime",
    "Datetime",
    "Time",
    "date",
    "datetime",
    "time",
)
_DATE_FIELD_NAMES = {
    "CreatedDate",
    "LastModifiedDate",
    "SystemModstamp",
    "LastActivityDate",
    "CloseDate",
    "StartDate",
    "EndDate",
    "BirthDate",
    "ActivityDate",
    "DueDate",
    "EffectiveDate",
    "ServiceDate",
    "InstallDate",
    "ShipDate",
    "ExpectedRevenue",
}

DEFAULT_WARN_FIELD_COUNT = 200  # warn above this many fields in a single sfdcDigest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics dataflow JSON files for dataset optimization issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory of the Salesforce DX project or metadata directory "
            "(default: current directory). The script searches recursively for "
            "*.wf and *.json files under wave/dataflow paths."
        ),
    )
    parser.add_argument(
        "--warn-field-count",
        type=int,
        default=DEFAULT_WARN_FIELD_COUNT,
        help=(
            f"Warn when a sfdcDigest node requests more than this many fields "
            f"(default: {DEFAULT_WARN_FIELD_COUNT})."
        ),
    )
    return parser.parse_args()


def _looks_like_date_field(field_name: str) -> bool:
    """Return True if the field name looks like it holds a date or datetime value."""
    if field_name in _DATE_FIELD_NAMES:
        return True
    for suffix in _DATE_FIELD_SUFFIXES:
        if field_name.endswith(suffix) and len(field_name) > len(suffix):
            return True
    return False


def _find_dataflow_files(manifest_dir: Path) -> list[Path]:
    """Find candidate CRM Analytics dataflow JSON files in the manifest directory."""
    candidates: list[Path] = []

    # Salesforce DX project: wave/dataflow/*.wf or analytics/dataflows/
    for pattern in (
        "**/*.wf",
        "**/wave/dataflows/**/*.json",
        "**/analytics/dataflows/**/*.json",
        "**/dataflows/**/*.json",
    ):
        candidates.extend(manifest_dir.rglob(pattern.lstrip("**/")))

    # Deduplicate while preserving order
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in candidates:
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(p)
    return unique


def _check_dataflow_json(
    path: Path,
    warn_field_count: int,
) -> list[str]:
    """Analyse one dataflow JSON file and return a list of issue strings."""
    issues: list[str] = []

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        issues.append(f"{path}: invalid JSON — {exc}")
        return issues

    if not isinstance(data, dict):
        return issues  # not a standard dataflow structure; skip

    schema_nodes: dict[str, dict] = {}

    for node_name, node in data.items():
        if not isinstance(node, dict):
            continue
        action = node.get("action", "")
        params = node.get("parameters", {})

        # Collect schema nodes for cross-referencing
        if action == "schema":
            schema_nodes[node_name] = node

        if action != "sfdcDigest":
            continue

        sf_object = params.get("object", "<unknown>")
        fields = params.get("fields")

        # Check 1: No fields list at all (SELECT * equivalent)
        if fields is None:
            issues.append(
                f"{path} [{node_name}]: sfdcDigest on '{sf_object}' has no 'fields' "
                f"list — pulls ALL fields from Salesforce (SELECT * equivalent). "
                f"Audit dashboard SAQL bindings and add a whitelist of used fields."
            )
            continue  # can't do field-count or date checks without field list

        if not isinstance(fields, list):
            continue

        field_names = [
            f.get("name", "") if isinstance(f, dict) else str(f)
            for f in fields
        ]

        # Check 2: Field count above threshold
        if len(field_names) > warn_field_count:
            issues.append(
                f"{path} [{node_name}]: sfdcDigest on '{sf_object}' requests "
                f"{len(field_names)} fields (threshold: {warn_field_count}). "
                f"Audit dashboard SAQL bindings and prune unused fields."
            )

        # Check 3: Date-looking fields with no corresponding schema node
        # We can only heuristically detect this — a field named CloseDate
        # in an sfdcDigest with no schema node that references it is suspicious.
        date_field_names = [n for n in field_names if _looks_like_date_field(n)]
        if date_field_names:
            # Look for any schema node that references this sfdcDigest's fields
            has_schema = any(
                node_name in str(sn.get("parameters", {}).get("source", ""))
                for sn in schema_nodes.values()
            )
            if not has_schema:
                issues.append(
                    f"{path} [{node_name}]: sfdcDigest on '{sf_object}' includes "
                    f"date/datetime fields ({', '.join(date_field_names[:5])}"
                    + (f"... and {len(date_field_names) - 5} more" if len(date_field_names) > 5 else "")
                    + f") but no downstream 'schema' transformation node was found "
                    f"that references this node. Date fields without an explicit "
                    f"'type: Date' declaration will be stored as Text, breaking "
                    f"SAQL timeseries expressions."
                )

        # Check 4: Multiple date fields that could benefit from epoch pre-computation
        if len(date_field_names) >= 2:
            issues.append(
                f"{path} [{node_name}]: sfdcDigest on '{sf_object}' includes "
                f"{len(date_field_names)} date/datetime fields. If any pair is used "
                f"for duration math (days-to-close, age calculations), consider "
                f"pre-computing the duration as an epoch integer in a "
                f"computeExpression node to avoid repeated date_to_epoch() calls "
                f"at SAQL query time."
            )

    return issues


def check_analytics_dataset_optimization(
    manifest_dir: Path,
    warn_field_count: int = DEFAULT_WARN_FIELD_COUNT,
) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    dataflow_files = _find_dataflow_files(manifest_dir)

    if not dataflow_files:
        # Not necessarily an error — the directory might not have CRM Analytics metadata.
        return issues

    for df_path in dataflow_files:
        issues.extend(_check_dataflow_json(df_path, warn_field_count))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_dataset_optimization(
        manifest_dir,
        warn_field_count=args.warn_field_count,
    )

    if not issues:
        print("No dataset optimization issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
