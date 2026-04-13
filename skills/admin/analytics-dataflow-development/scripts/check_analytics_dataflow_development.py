#!/usr/bin/env python3
"""Checker script for Analytics Dataflow Development skill.

Scans CRM Analytics dataflow JSON files (.wdf) for common structural anti-patterns
documented in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_dataflow_development.py [--help]
    python3 check_analytics_dataflow_development.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics dataflow JSON files (.wdf) for common structural "
            "anti-patterns: filter-after-augment, missing sfdcRegister, invalid "
            "augment join-type parameters, and sfdcRegister mode parameters."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or wave/ directory (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Node graph helpers
# ---------------------------------------------------------------------------

def _build_source_map(nodes: dict) -> dict[str, str]:
    """Return a mapping of node_name -> source_node_name for single-source nodes."""
    source_map: dict[str, str] = {}
    for node_name, node_def in nodes.items():
        if not isinstance(node_def, dict):
            continue
        params = node_def.get("parameters", {})
        source = params.get("source")
        if isinstance(source, str):
            source_map[node_name] = source
    return source_map


def _ancestors(node_name: str, source_map: dict[str, str], visited: set | None = None) -> set[str]:
    """Return all ancestor node names for a given node by traversing source_map."""
    if visited is None:
        visited = set()
    parent = source_map.get(node_name)
    if parent and parent not in visited:
        visited.add(parent)
        _ancestors(parent, source_map, visited)
    return visited


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_filter_after_augment(nodes: dict, dataflow_name: str) -> list[str]:
    """Detect Filter nodes whose upstream path passes through an Augment node."""
    issues: list[str] = []
    source_map = _build_source_map(nodes)

    augment_nodes = {
        name for name, defn in nodes.items()
        if isinstance(defn, dict) and defn.get("action") == "augment"
    }

    filter_nodes = {
        name for name, defn in nodes.items()
        if isinstance(defn, dict) and defn.get("action") == "filter"
    }

    for filter_node in filter_nodes:
        ancestors = _ancestors(filter_node, source_map)
        bad_augments = ancestors & augment_nodes
        if bad_augments:
            issues.append(
                f"[{dataflow_name}] Filter node '{filter_node}' is placed AFTER Augment "
                f"node(s) {sorted(bad_augments)} — move Filter before Augment to reduce "
                f"row count before the join (anti-pattern: filter-after-augment)."
            )
    return issues


def check_augment_join_type_param(nodes: dict, dataflow_name: str) -> list[str]:
    """Detect Augment nodes with invalid joinType/join_type parameters."""
    issues: list[str] = []
    invalid_keys = {"joinType", "join_type", "type", "jointype"}

    for node_name, node_def in nodes.items():
        if not isinstance(node_def, dict):
            continue
        if node_def.get("action") != "augment":
            continue
        params = node_def.get("parameters", {})
        found = invalid_keys & set(params.keys())
        if found:
            issues.append(
                f"[{dataflow_name}] Augment node '{node_name}' has unsupported parameter(s) "
                f"{sorted(found)}. Augment is left-join-only; there is no join-type parameter. "
                f"Remove these keys or use Recipes for multi-join-type support."
            )
    return issues


def check_sfdc_register_mode_param(nodes: dict, dataflow_name: str) -> list[str]:
    """Detect sfdcRegister nodes with unsupported mode/append parameters."""
    issues: list[str] = []
    invalid_keys = {"mode", "appendMode", "upsertMode", "incremental", "incrementalField", "append_mode"}

    for node_name, node_def in nodes.items():
        if not isinstance(node_def, dict):
            continue
        if node_def.get("action") != "sfdcRegister":
            continue
        params = node_def.get("parameters", {})
        found = invalid_keys & set(params.keys())
        if found:
            issues.append(
                f"[{dataflow_name}] sfdcRegister node '{node_name}' has unsupported parameter(s) "
                f"{sorted(found)}. sfdcRegister always performs a full overwrite — there is no "
                f"append, upsert, or incremental mode. Remove these keys."
            )
    return issues


def check_missing_sfdc_register(nodes: dict, dataflow_name: str) -> list[str]:
    """Warn if no sfdcRegister node is present — the dataflow produces no output dataset."""
    issues: list[str] = []
    register_nodes = [
        name for name, defn in nodes.items()
        if isinstance(defn, dict) and defn.get("action") == "sfdcRegister"
    ]
    if not register_nodes:
        issues.append(
            f"[{dataflow_name}] No sfdcRegister node found. The dataflow produces no registered "
            f"dataset. Ensure at least one sfdcRegister node is present as the terminal node."
        )
    return issues


def check_compute_expression_aggregates(nodes: dict, dataflow_name: str) -> list[str]:
    """Detect computeExpression nodes with SAQL aggregate functions (should use computeRelative)."""
    issues: list[str] = []
    aggregate_hints = ["sum(", "count(", "max(", "min(", "avg(", "rank(", "cumsum(", "rsum("]

    for node_name, node_def in nodes.items():
        if not isinstance(node_def, dict):
            continue
        if node_def.get("action") != "computeExpression":
            continue
        params = node_def.get("parameters", {})
        computed_fields = params.get("computedFields", [])
        for field in computed_fields:
            if not isinstance(field, dict):
                continue
            expr = field.get("saqlExpression", "").lower()
            found_agg = [agg for agg in aggregate_hints if agg in expr]
            if found_agg:
                field_name = field.get("name", "<unknown>")
                issues.append(
                    f"[{dataflow_name}] computeExpression node '{node_name}', field '{field_name}' "
                    f"uses aggregate-like function(s) {found_agg} in saqlExpression. "
                    f"computeExpression is row-level only and does not support aggregation. "
                    f"Use computeRelative for window/partition expressions."
                )
    return issues


def check_no_filter_before_augment(nodes: dict, dataflow_name: str) -> list[str]:
    """Warn when an Augment node's left source is a raw sfdcDigest (no filter in between)."""
    issues: list[str] = []
    source_map = _build_source_map(nodes)

    augment_nodes = {
        name: defn for name, defn in nodes.items()
        if isinstance(defn, dict) and defn.get("action") == "augment"
    }

    digest_nodes = {
        name for name, defn in nodes.items()
        if isinstance(defn, dict) and defn.get("action") in ("sfdcDigest", "digest", "edgemart")
    }

    filter_nodes = {
        name for name, defn in nodes.items()
        if isinstance(defn, dict) and defn.get("action") == "filter"
    }

    for aug_name, aug_def in augment_nodes.items():
        left_source = aug_def.get("parameters", {}).get("left")
        if not left_source:
            continue
        # Walk ancestors of the left input; if we hit a digest before hitting any filter, warn
        ancestors = _ancestors(aug_name, source_map)
        left_ancestors = _ancestors(left_source, source_map) | {left_source}
        direct_digest_path = left_ancestors & digest_nodes
        filter_on_path = left_ancestors & filter_nodes
        if direct_digest_path and not filter_on_path:
            issues.append(
                f"[{dataflow_name}] Augment node '{aug_name}' left input '{left_source}' has "
                f"no Filter node between sfdcDigest and Augment. Consider adding a Filter node "
                f"before the join to reduce row count and improve performance."
            )
    return issues


# ---------------------------------------------------------------------------
# Dataflow file scanner
# ---------------------------------------------------------------------------

def check_dataflow_file(wdf_path: Path) -> list[str]:
    """Parse a single .wdf dataflow JSON file and run all checks."""
    issues: list[str] = []
    try:
        text = wdf_path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"Could not read {wdf_path}: {exc}")
        return issues

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        issues.append(f"[{wdf_path.name}] Invalid JSON — dataflow file cannot be parsed: {exc}")
        return issues

    if not isinstance(data, dict):
        issues.append(f"[{wdf_path.name}] Unexpected top-level type {type(data).__name__}; expected dict.")
        return issues

    dataflow_name = wdf_path.stem
    nodes = data

    issues.extend(check_filter_after_augment(nodes, dataflow_name))
    issues.extend(check_augment_join_type_param(nodes, dataflow_name))
    issues.extend(check_sfdc_register_mode_param(nodes, dataflow_name))
    issues.extend(check_missing_sfdc_register(nodes, dataflow_name))
    issues.extend(check_compute_expression_aggregates(nodes, dataflow_name))
    issues.extend(check_no_filter_before_augment(nodes, dataflow_name))

    return issues


def check_analytics_dataflow_development(manifest_dir: Path) -> list[str]:
    """Scan all .wdf dataflow files under manifest_dir and return all issues found."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    wdf_files = list(manifest_dir.rglob("*.wdf"))
    if not wdf_files:
        # Also check for dataflow JSON in common Analytics metadata paths
        wave_dir = manifest_dir / "wave"
        json_files = list(wave_dir.rglob("*.json")) if wave_dir.exists() else []
        if not json_files:
            issues.append(
                f"No .wdf dataflow files found under {manifest_dir}. "
                f"If this is a fresh project, no checks apply yet."
            )
            return issues
        for jf in json_files:
            issues.extend(check_dataflow_file(jf))
        return issues

    for wdf_path in sorted(wdf_files):
        issues.extend(check_dataflow_file(wdf_path))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_dataflow_development(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
