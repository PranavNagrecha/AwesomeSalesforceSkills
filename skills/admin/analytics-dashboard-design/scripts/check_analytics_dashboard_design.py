#!/usr/bin/env python3
"""Checker script for CRM Analytics Dashboard Design skill.

Checks CRM Analytics dashboard JSON for common design anti-patterns.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_dashboard_design.py [--help]
    python3 check_analytics_dashboard_design.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check CRM Analytics dashboard JSON for common anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_dashboard_json(dashboard_file: Path) -> list[str]:
    """Check a dashboard JSON file for common design anti-patterns."""
    issues: list[str] = []

    try:
        content = dashboard_file.read_text(encoding="utf-8")
        data = json.loads(content)
    except (json.JSONDecodeError, OSError):
        return issues

    if not isinstance(data, dict):
        return issues

    dashboard_name = dashboard_file.stem
    steps = data.get("steps", {})
    widgets = data.get("widgets", {})

    # Check for SAQL steps using SQL-like syntax
    for step_name, step_data in steps.items():
        if not isinstance(step_data, dict):
            continue
        saql = step_data.get("query", "") or step_data.get("saql", "")
        if isinstance(saql, str) and re.search(r"\bSELECT\b", saql, re.IGNORECASE):
            issues.append(
                f"Dashboard '{dashboard_name}', step '{step_name}': "
                "Appears to use SQL SELECT syntax in a SAQL step. "
                "SAQL uses 'q = load ... ; q = group ... ; q = foreach ...' syntax, not SQL."
            )

    # Check for widgets with both columnMap and binding syntax (potential columnMap bug)
    for widget_name, widget_data in widgets.items():
        if not isinstance(widget_data, dict):
            continue

        column_map = widget_data.get("columnMap", {})
        parameters = widget_data.get("parameters", {})

        # Check if widget has columnMap with binding references nearby
        widget_str = json.dumps(widget_data)
        has_binding = "{{cell(" in widget_str
        has_column_map = bool(column_map) and isinstance(column_map, dict)

        if has_binding and has_column_map:
            issues.append(
                f"Dashboard '{dashboard_name}', widget '{widget_name}': "
                "Widget has both a binding ({{cell(...)}} syntax) and a static columnMap. "
                "If the binding changes the measure or grouping column, the chart may silently "
                "render wrong data. Consider replacing columnMap with 'columns': []."
            )

    return issues


def check_analytics_dashboard_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check analytics/wave metadata dashboard files
    for dashboard_file in manifest_dir.rglob("*.dashboard"):
        issues.extend(check_dashboard_json(dashboard_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_dashboard_design(manifest_dir)

    if not issues:
        print("No CRM Analytics dashboard design issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
