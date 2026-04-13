#!/usr/bin/env python3
"""Checker script for Analytics Data Architecture skill.

Inspects Salesforce metadata (dataflow JSON, Recipe JSON, and manifest files)
for common CRM Analytics data architecture anti-patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_data_architecture.py [--help]
    python3 check_analytics_data_architecture.py --manifest-dir path/to/metadata
    python3 check_analytics_data_architecture.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Platform limits sourced from CRM Analytics Limits documentation
DATAFLOW_RUN_WINDOW_LIMIT = 60          # max combined dataflow+recipe runs per rolling 24h
DATASET_ROW_CAP = 2_000_000_000        # 2 billion rows per dataset (org allocation-dependent)
DATASET_ROW_WARN_THRESHOLD = 0.80      # warn at 80% of row cap

# External warehouse connection types that CANNOT appear in dataflow JSON
INVALID_DATAFLOW_CONNECTORS = {
    "snowflake", "bigquery", "redshift", "external", "remote_connection",
    "externaldata", "external_source",
}

# SAQL patterns that indicate runtime join (should be pushed to ELT layer)
SAQL_RUNTIME_JOIN_PATTERNS = ["cogroup"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_json_files(root: Path, suffix: str) -> list[Path]:
    """Return all JSON files under root matching the given suffix pattern."""
    return list(root.rglob(f"*{suffix}"))


def _load_json(path: Path) -> dict | list | None:
    """Load JSON from path; return None on parse error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_dataflow_external_connectors(manifest_dir: Path) -> list[str]:
    """Flag dataflow JSON files that reference external warehouse connector types.

    Snowflake, BigQuery, and Redshift must be configured as Remote Connections
    in Data Manager — not embedded in dataflow JSON.
    """
    issues: list[str] = []
    dataflow_files = _iter_json_files(manifest_dir, "-dataflow.json")
    # Also match files under analyticsDataflow/ metadata directory
    dataflow_files += list(manifest_dir.rglob("analyticsDataflow/*.json"))

    seen: set[Path] = set()
    for path in dataflow_files:
        if path in seen:
            continue
        seen.add(path)

        data = _load_json(path)
        if not isinstance(data, dict):
            continue

        for node_name, node_body in data.items():
            if not isinstance(node_body, dict):
                continue
            action = str(node_body.get("action", "")).lower()
            if action in INVALID_DATAFLOW_CONNECTORS:
                issues.append(
                    f"[{path.name}] Node '{node_name}' uses action '{action}' — "
                    f"external warehouse connectors (Snowflake, BigQuery, Redshift) "
                    f"must be configured as Remote Connections in Data Manager, "
                    f"not in dataflow JSON. (ref: gotchas.md#gotcha-3)"
                )

    return issues


def check_recipe_incremental_claim(manifest_dir: Path) -> list[str]:
    """Warn if Recipe JSON contains 'incremental' in node configuration.

    Recipes do not support native incremental loads. Any incremental-sounding
    configuration in a Recipe JSON is either a no-op or a misconfiguration.
    """
    issues: list[str] = []
    recipe_files = _iter_json_files(manifest_dir, "-recipe.json")
    recipe_files += list(manifest_dir.rglob("analyticsRecipe/*.json"))

    seen: set[Path] = set()
    for path in recipe_files:
        if path in seen:
            continue
        seen.add(path)

        raw = path.read_text(encoding="utf-8", errors="replace")
        if "incremental" in raw.lower():
            issues.append(
                f"[{path.name}] Recipe JSON contains 'incremental' — "
                f"CRM Analytics Recipes do NOT support native incremental loads. "
                f"Every Recipe run reprocesses the full input dataset. "
                f"Implement the snapshot-join technique to simulate incremental behavior. "
                f"(ref: gotchas.md#gotcha-1)"
            )

    return issues


def check_saql_runtime_joins(manifest_dir: Path) -> list[str]:
    """Flag SAQL files or dashboard JSON containing runtime cogroup (join) patterns.

    Joins should be pushed into the ELT layer (dataflow Augment or Recipe Join),
    not performed at SAQL query time.
    """
    issues: list[str] = []
    # SAQL files (.saql) and dashboard JSON (which may embed SAQL)
    candidate_files = (
        list(manifest_dir.rglob("*.saql"))
        + list(manifest_dir.rglob("analyticsDashboard/*.json"))
        + list(manifest_dir.rglob("*-dashboard.json"))
    )

    seen: set[Path] = set()
    for path in candidate_files:
        if path in seen:
            continue
        seen.add(path)

        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for pattern in SAQL_RUNTIME_JOIN_PATTERNS:
            if pattern in raw:
                issues.append(
                    f"[{path.name}] Contains SAQL '{pattern}' — runtime joins in SAQL "
                    f"execute on every user interaction and do not scale. "
                    f"Move joins into the dataflow (Augment transformation) or Recipe "
                    f"(Join node) to compute once per refresh cycle. "
                    f"(ref: llm-anti-patterns.md#anti-pattern-4)"
                )
                break  # one warning per file is sufficient

    return issues


def check_run_schedule_count(manifest_dir: Path) -> list[str]:
    """Count scheduled dataflow and Recipe runs; warn if total approaches 60.

    Reads schedule metadata from analyticsDataflow and analyticsRecipe JSON
    files and counts distinct schedules. This is a heuristic — it detects
    files with schedule definitions, not actual run frequency.
    """
    issues: list[str] = []
    schedule_count = 0
    scheduled_files: list[str] = []

    candidate_files = (
        list(manifest_dir.rglob("analyticsDataflow/*.json"))
        + list(manifest_dir.rglob("-dataflow.json"))
        + list(manifest_dir.rglob("analyticsRecipe/*.json"))
        + list(manifest_dir.rglob("-recipe.json"))
    )

    seen: set[Path] = set()
    for path in candidate_files:
        if path in seen:
            continue
        seen.add(path)

        data = _load_json(path)
        if not isinstance(data, dict):
            continue

        # Look for schedule definitions anywhere in the JSON
        raw = path.read_text(encoding="utf-8", errors="replace")
        if "schedule" in raw.lower() and ("hourly" in raw.lower() or "daily" in raw.lower() or "cron" in raw.lower()):
            schedule_count += 1
            scheduled_files.append(path.name)

    warn_threshold = int(DATAFLOW_RUN_WINDOW_LIMIT * 0.75)  # warn at 75% (45 jobs)
    if schedule_count >= warn_threshold:
        issues.append(
            f"Found {schedule_count} scheduled dataflow/Recipe definitions. "
            f"The platform allows {DATAFLOW_RUN_WINDOW_LIMIT} combined runs per rolling 24-hour window "
            f"(not a calendar-day reset). At this schedule density, the run budget may be "
            f"exhausted. Audit refresh frequency and consolidate low-priority jobs. "
            f"Scheduled files: {', '.join(scheduled_files[:10])}"
            + (" (and more...)" if len(scheduled_files) > 10 else "")
            + f". (ref: gotchas.md#gotcha-2)"
        )

    return issues


def check_single_unbounded_dataset(manifest_dir: Path) -> list[str]:
    """Warn if a dataflow or Recipe writes to a single dataset with no apparent time filter.

    This is a heuristic check: if a dataflow JSON has no 'filter' or 'sfdcDigest'
    time-range parameter and writes to a single output, it may be loading unbounded
    history into one dataset — a 2-billion-row cap risk.
    """
    issues: list[str] = []
    dataflow_files = (
        list(manifest_dir.rglob("analyticsDataflow/*.json"))
        + list(manifest_dir.rglob("-dataflow.json"))
    )

    seen: set[Path] = set()
    for path in dataflow_files:
        if path in seen:
            continue
        seen.add(path)

        data = _load_json(path)
        if not isinstance(data, dict):
            continue

        has_filter = False
        has_sfdcdigest = False
        register_count = 0

        for node_name, node_body in data.items():
            if not isinstance(node_body, dict):
                continue
            action = str(node_body.get("action", "")).lower()
            if action == "filter":
                has_filter = True
            if action == "sfdigest" or action == "sfdcdigest":
                has_sfdcdigest = True
                # Check for date-based filter in parameters
                params = node_body.get("parameters", {})
                if isinstance(params, dict):
                    fields = params.get("fields", [])
                    if any(
                        isinstance(f, dict) and "date" in str(f.get("name", "")).lower()
                        for f in fields
                    ):
                        has_filter = True
            if action == "register":
                register_count += 1

        if has_sfdcdigest and not has_filter and register_count == 1:
            issues.append(
                f"[{path.name}] Dataflow reads Salesforce objects with no apparent filter "
                f"and writes to a single dataset. If this object has large or unbounded row "
                f"counts, consider adding a time-window filter in the ELT layer to avoid "
                f"approaching the 2-billion-row per-dataset cap. "
                f"(ref: llm-anti-patterns.md#anti-pattern-6)"
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics metadata for data architecture anti-patterns.\n\n"
            "Checks performed:\n"
            "  1. Dataflow JSON with invalid external connector nodes (Snowflake/BigQuery/Redshift)\n"
            "  2. Recipe JSON claiming incremental load support\n"
            "  3. SAQL files with runtime joins (cogroup) that should be in ELT layer\n"
            "  4. High scheduled run count approaching the 60-run rolling window limit\n"
            "  5. Dataflows with unbounded dataset loads (2-billion-row cap risk)\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_analytics_data_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_dataflow_external_connectors(manifest_dir))
    issues.extend(check_recipe_incremental_claim(manifest_dir))
    issues.extend(check_saql_runtime_joins(manifest_dir))
    issues.extend(check_run_schedule_count(manifest_dir))
    issues.extend(check_single_unbounded_dataset(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_data_architecture(manifest_dir)

    if not issues:
        print("No CRM Analytics data architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found. Review references/gotchas.md and references/llm-anti-patterns.md for remediation guidance.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
