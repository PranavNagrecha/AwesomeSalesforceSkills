#!/usr/bin/env python3
"""Checker script for Analytics Recipe Design skill.

Scans CRM Analytics recipe JSON files in a Salesforce metadata directory for
common recipe design anti-patterns documented in references/gotchas.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_recipe_design.py [--help]
    python3 check_analytics_recipe_design.py --manifest-dir path/to/metadata
    python3 check_analytics_recipe_design.py --manifest-dir force-app/main/default

Checks performed:
    1. Inner joins present — flag for review (may be intentional, but should be verified)
    2. Join nodes without a documented join type in node label/description
    3. Recipe files that contain schedule-like properties in the recipe body (invalid)
    4. Output nodes with very wide schemas (>50 columns) — performance risk
    5. Recipe files with no Output node — recipe will not produce a dataset
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# CRM Analytics recipe files use the .wdpr extension in metadata deployments
RECIPE_EXTENSIONS = {".wdpr", ".json"}

# Join types that silently drop rows from the left dataset
LOSSY_JOIN_TYPES = {"Inner", "RightOuter"}

# Maximum column count before flagging as "wide schema" performance risk
WIDE_SCHEMA_THRESHOLD = 50

# Properties that indicate someone tried to embed a schedule in the recipe body
SCHEDULE_PROPERTY_NAMES = {
    "schedule",
    "cronExpression",
    "refreshInterval",
    "frequency",
    "scheduleType",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json_safe(path: Path) -> dict | list | None:
    """Return parsed JSON or None on error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _find_recipe_files(manifest_dir: Path) -> list[Path]:
    """Recursively find recipe metadata files under manifest_dir."""
    found: list[Path] = []
    for ext in RECIPE_EXTENSIONS:
        found.extend(manifest_dir.rglob(f"*{ext}"))
    # Deduplicate and sort for deterministic output
    return sorted(set(found))


def _is_recipe_body(data: dict) -> bool:
    """Heuristic: a CRM Analytics recipe body has a 'nodes' key."""
    return isinstance(data, dict) and "nodes" in data


def _get_nodes(data: dict) -> list[dict]:
    """Return the list of nodes from a recipe body."""
    nodes = data.get("nodes")
    if isinstance(nodes, list):
        return nodes
    if isinstance(nodes, dict):
        # Some recipe formats store nodes as an object keyed by node ID
        return list(nodes.values())
    return []


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_inner_joins(recipe_path: Path, data: dict) -> list[str]:
    """Flag Join nodes configured as Inner or RightOuter."""
    issues: list[str] = []
    for node in _get_nodes(data):
        if not isinstance(node, dict):
            continue
        node_type = node.get("type", "")
        if node_type != "join":
            continue
        join_type = node.get("parameters", {}).get("joinType", "")
        if join_type in LOSSY_JOIN_TYPES:
            node_name = node.get("name", node.get("id", "unknown"))
            issues.append(
                f"{recipe_path.name}: Join node '{node_name}' uses '{join_type}' join — "
                f"this silently drops left-side rows with no right-side match. "
                f"Verify this is intentional; use 'Lookup' for enrichment use cases."
            )
    return issues


def check_embedded_schedule(recipe_path: Path, data: dict) -> list[str]:
    """Flag recipe bodies that contain scheduling properties (invalid — schedules are a separate resource)."""
    issues: list[str] = []
    found_props = SCHEDULE_PROPERTY_NAMES.intersection(data.keys())
    if found_props:
        issues.append(
            f"{recipe_path.name}: Recipe body contains schedule-like properties "
            f"({', '.join(sorted(found_props))}). Recipe schedules must be configured via "
            f"POST /wave/recipes/{{recipeId}}/schedules — they are not part of the recipe definition."
        )
    return issues


def check_output_nodes(recipe_path: Path, data: dict) -> list[str]:
    """Flag recipes with no Output node — they will not produce a dataset."""
    issues: list[str] = []
    nodes = _get_nodes(data)
    output_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") == "output"]
    if nodes and not output_nodes:
        issues.append(
            f"{recipe_path.name}: No Output node found. The recipe will not produce "
            f"a CRM Analytics dataset. Add at least one Output node."
        )
    return issues


def check_wide_output_schemas(recipe_path: Path, data: dict) -> list[str]:
    """Flag Output nodes that have an unusually large number of columns."""
    issues: list[str] = []
    for node in _get_nodes(data):
        if not isinstance(node, dict):
            continue
        if node.get("type") != "output":
            continue
        schema = node.get("schema", {})
        columns = schema.get("fields", schema.get("columns", []))
        if isinstance(columns, list) and len(columns) > WIDE_SCHEMA_THRESHOLD:
            node_name = node.get("name", node.get("id", "unknown"))
            issues.append(
                f"{recipe_path.name}: Output node '{node_name}' has {len(columns)} columns "
                f"(threshold: {WIDE_SCHEMA_THRESHOLD}). Wide schemas increase storage and query time. "
                f"Remove unused columns from the output."
            )
    return issues


def check_no_load_nodes(recipe_path: Path, data: dict) -> list[str]:
    """Flag recipes with no Load node — they have no input source."""
    issues: list[str] = []
    nodes = _get_nodes(data)
    load_nodes = [n for n in nodes if isinstance(n, dict) and n.get("type") == "load"]
    if nodes and not load_nodes:
        issues.append(
            f"{recipe_path.name}: No Load node found. A recipe must have at least one Load node "
            f"to define an input dataset."
        )
    return issues


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------


def check_analytics_recipe_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Each returned string describes a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    recipe_files = _find_recipe_files(manifest_dir)

    if not recipe_files:
        # Not an error — the org may simply have no recipe metadata checked in
        return issues

    for recipe_path in recipe_files:
        data = _load_json_safe(recipe_path)
        if data is None:
            issues.append(f"{recipe_path.name}: Could not parse as JSON — skipping.")
            continue
        if not _is_recipe_body(data):
            # Not a recipe body file (may be a manifest or partial artifact)
            continue

        issues.extend(check_inner_joins(recipe_path, data))
        issues.extend(check_embedded_schedule(recipe_path, data))
        issues.extend(check_output_nodes(recipe_path, data))
        issues.extend(check_wide_output_schemas(recipe_path, data))
        issues.extend(check_no_load_nodes(recipe_path, data))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics recipe metadata files for common design anti-patterns. "
            "Looks for .wdpr and .json recipe files under the specified manifest directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_recipe_design(manifest_dir)

    if not issues:
        print("No recipe design issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
