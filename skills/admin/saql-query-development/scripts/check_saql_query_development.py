#!/usr/bin/env python3
"""Checker script for SAQL Query Development skill.

Scans Salesforce CRM Analytics dashboard JSON files and any .saql files in the
given directory tree for common SAQL anti-patterns documented in this skill:

1. SQL/SOQL syntax used in SAQL context (SELECT, FROM, WHERE, GROUP BY, JOIN, HAVING)
2. Windowing function without an over clause (rank(), dense_rank(), row_number() missing over)
3. cogroup step followed by unqualified field references in the next foreach
4. rollup without grouping() in the same foreach
5. pigql step that also specifies a non-empty filter/limit/order on the query attribute

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_saql_query_development.py [--help]
    python3 check_saql_query_development.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# SQL keyword patterns that are invalid in SAQL
# ---------------------------------------------------------------------------
_SQL_KEYWORDS = re.compile(
    r"\b(SELECT|FROM|WHERE|GROUP\s+BY|HAVING|JOIN|INNER\s+JOIN|LEFT\s+JOIN|RIGHT\s+JOIN)\b",
    re.IGNORECASE,
)

# Windowing functions that require an over clause
_WINDOWING_FUNCS = re.compile(
    r"\b(rank|dense_rank|row_number|cume_dist|moving_average)\s*\(",
    re.IGNORECASE,
)
_OVER_CLAUSE = re.compile(r"\bover\s*\(", re.IGNORECASE)

# rollup modifier
_ROLLUP = re.compile(r"\brollup\s*\(", re.IGNORECASE)

# grouping() call
_GROUPING = re.compile(r"\bgrouping\s*\(", re.IGNORECASE)

# cogroup statement
_COGROUP = re.compile(r"\bcogroup\b", re.IGNORECASE)


def _check_saql_string(saql: str, source_label: str) -> list[str]:
    """Run pattern checks on a SAQL string. Return list of issue descriptions."""
    issues: list[str] = []

    # 1. SQL/SOQL syntax
    sql_hits = _SQL_KEYWORDS.findall(saql)
    if sql_hits:
        issues.append(
            f"{source_label}: SQL/SOQL keyword(s) found in SAQL — {set(sql_hits)}. "
            "SAQL uses pipeline assignment syntax (q = load ...; q = filter q by ...). "
            "SQL keywords cause immediate parse errors."
        )

    # 2. Windowing functions without over clause
    if _WINDOWING_FUNCS.search(saql) and not _OVER_CLAUSE.search(saql):
        issues.append(
            f"{source_label}: windowing function (rank/dense_rank/row_number/cume_dist/moving_average) "
            "found without an 'over (...)' clause. Windowing functions require 'over ([partition by ...] order by ...)'."
        )

    # 3. rollup without grouping()
    if _ROLLUP.search(saql) and not _GROUPING.search(saql):
        issues.append(
            f"{source_label}: 'rollup(...)' used without 'grouping()' in the foreach generate clause. "
            "Add grouping(<dimension>) for each rolled-up dimension so consumers can identify subtotal rows."
        )

    # 4. cogroup present — remind about qualified field references (heuristic)
    if _COGROUP.search(saql):
        # Check whether any foreach generate after cogroup uses unqualified short names
        # Heuristic: look for "generate" followed by a bare identifier (no dot) for common field names
        cogroup_pos = saql.lower().find("cogroup")
        after_cogroup = saql[cogroup_pos:]
        foreach_match = re.search(r"\bforeach\b.*?\bgenerate\b(.*?)(?:;|$)", after_cogroup, re.IGNORECASE | re.DOTALL)
        if foreach_match:
            projection = foreach_match.group(1)
            # Flag if there is no stream-qualified reference (no dot in identifiers)
            if "." not in projection:
                issues.append(
                    f"{source_label}: 'cogroup' found but the following 'foreach generate' clause "
                    "appears to use unqualified field names (no 'streamName.field' pattern). "
                    "After cogroup, reference fields as 'stream1.FieldName', 'stream2.FieldName' until "
                    "they are projected to aliases."
                )

    return issues


def _extract_saql_from_dashboard(data: dict) -> list[tuple[str, str]]:
    """Extract (label, saql_string) pairs from a dashboard JSON dict."""
    results: list[tuple[str, str]] = []
    steps = data.get("steps", {})
    if not isinstance(steps, dict):
        return results
    for step_name, step_data in steps.items():
        if not isinstance(step_data, dict):
            continue

        # Check for pigql attribute with non-trivial filter/limit/order on query
        if "pigql" in step_data and step_data.get("pigql"):
            query_attr = step_data.get("query", {})
            if isinstance(query_attr, dict):
                has_filter = bool(query_attr.get("filters") or query_attr.get("filter"))
                has_limit = query_attr.get("limit") not in (None, 0, "")
                has_order = bool(query_attr.get("orders") or query_attr.get("order"))
                if has_filter or has_limit or has_order:
                    results.append((
                        f"step '{step_name}' (pigql conflict)",
                        "PIGGYBACK_FILTER_CONFLICT: step has 'pigql' set AND non-empty filter/limit/order "
                        "on the 'query' attribute. The query attribute filter/limit/order are silently ignored "
                        "when 'pigql' is present. Move all filtering into the pigql SAQL string.",
                    ))

        # Extract SAQL string from query attribute
        query_attr = step_data.get("query", {})
        if isinstance(query_attr, dict):
            saql = query_attr.get("query", "")
            if saql and isinstance(saql, str):
                results.append((f"step '{step_name}'", saql))

        # Also check pigql SAQL string itself
        pigql = step_data.get("pigql", "")
        if pigql and isinstance(pigql, str):
            results.append((f"step '{step_name}' (pigql)", pigql))

    return results


def check_saql_query_development(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Scan dashboard JSON files
    for dashboard_file in manifest_dir.rglob("*.json"):
        try:
            text = dashboard_file.read_text(encoding="utf-8")
            data = json.loads(text)
        except (json.JSONDecodeError, OSError):
            continue

        if not isinstance(data, dict):
            continue

        # Only process files that look like dashboard definitions (have 'steps' key)
        if "steps" not in data:
            continue

        saql_pairs = _extract_saql_from_dashboard(data)
        for label, saql in saql_pairs:
            source = f"{dashboard_file.name} / {label}"
            # Special pre-formatted issues (pigql conflict) start with known prefix
            if saql.startswith("PIGGYBACK_FILTER_CONFLICT:"):
                issues.append(f"{source}: {saql}")
            else:
                issues.extend(_check_saql_string(saql, source))

    # Scan standalone .saql files
    for saql_file in manifest_dir.rglob("*.saql"):
        try:
            saql = saql_file.read_text(encoding="utf-8")
        except OSError:
            continue
        issues.extend(_check_saql_string(saql, str(saql_file)))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check CRM Analytics dashboard JSON and .saql files for common SAQL "
            "anti-patterns: SQL syntax, missing over clauses on windowing functions, "
            "rollup without grouping(), cogroup field qualification, and piggyback "
            "query filter conflicts."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory to scan for dashboard JSON and .saql files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_saql_query_development(manifest_dir)

    if not issues:
        print("No SAQL issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
