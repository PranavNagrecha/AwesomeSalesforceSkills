#!/usr/bin/env python3
"""Checker script for Data Cloud Calculated Insights skill.

Validates SQL definitions and configuration for Calculated Insights against
known platform constraints: character limit, GROUP BY completeness, schedule
cadence, insight count limits, and Streaming Insight source compatibility.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_calculated_insights.py --help
    python3 check_data_cloud_calculated_insights.py --sql "SELECT ... FROM ... GROUP BY ..."
    python3 check_data_cloud_calculated_insights.py --sql-file path/to/insight.sql
    python3 check_data_cloud_calculated_insights.py --schedule 2h
    python3 check_data_cloud_calculated_insights.py --insight-count 298 --streaming-count 19
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Platform limits (sourced from official Salesforce documentation)
SQL_CHAR_LIMIT = 131_021
SQL_TIMEOUT_MINUTES = 120  # 2-hour execution timeout
MAX_TOTAL_INSIGHTS = 300
MAX_STREAMING_INSIGHTS = 20
MAX_DIMENSIONS_PER_INSIGHT = 10
MAX_MEASURES_PER_INSIGHT = 50
VALID_SCHEDULE_CADENCES = {"6h", "12h", "24h", "6", "12", "24"}
VALID_STREAMING_SOURCES = {
    "mobile_web_sdk",
    "web_sdk",
    "mobile_sdk",
    "marketing_cloud_personalization",
    "mcp_personalization",
    "interaction_studio",
}

# Patterns for detecting common anti-patterns in SQL
MISSING_WHERE_PATTERN = re.compile(
    r"\bSELECT\b.+\bFROM\b.+(?<!\bWHERE\b)",
    re.IGNORECASE | re.DOTALL,
)
AGGREGATION_FUNCTIONS = re.compile(
    r"\b(COUNT|SUM|AVG|MIN|MAX)\s*\(",
    re.IGNORECASE,
)
GROUP_BY_PATTERN = re.compile(r"\bGROUP\s+BY\b", re.IGNORECASE)
RENAME_LANGUAGE_PATTERN = re.compile(
    r"\brename\b.*(measure|dimension|insight|metric)",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Data Cloud Calculated Insights SQL and configuration "
            "against known platform constraints."
        ),
    )
    parser.add_argument(
        "--sql",
        default=None,
        help="Calculated Insight SQL string to validate.",
    )
    parser.add_argument(
        "--sql-file",
        default=None,
        help="Path to a file containing the Calculated Insight SQL.",
    )
    parser.add_argument(
        "--schedule",
        default=None,
        help=(
            "Proposed schedule cadence to validate. "
            "Valid values: 6h, 12h, 24h (or 6, 12, 24)."
        ),
    )
    parser.add_argument(
        "--insight-count",
        type=int,
        default=None,
        help="Current total insight count in the org (Calculated + Streaming).",
    )
    parser.add_argument(
        "--streaming-count",
        type=int,
        default=None,
        help="Current Streaming Insight count in the org.",
    )
    parser.add_argument(
        "--streaming-source",
        default=None,
        help=(
            "Proposed Streaming Insight source type to validate. "
            "Valid values: mobile_web_sdk, marketing_cloud_personalization, etc."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help=(
            "Root directory of Salesforce metadata to scan for "
            "insight-related anti-patterns in config files."
        ),
    )
    return parser.parse_args()


def check_sql(sql: str) -> list[str]:
    """Validate a Calculated Insight SQL string against platform constraints."""
    issues: list[str] = []

    # Check character limit
    char_count = len(sql)
    if char_count > SQL_CHAR_LIMIT:
        issues.append(
            f"SQL exceeds the {SQL_CHAR_LIMIT:,}-character platform limit "
            f"(current length: {char_count:,} characters). "
            "Reduce query complexity or split into multiple insights."
        )
    elif char_count > SQL_CHAR_LIMIT * 0.9:
        issues.append(
            f"SQL is approaching the {SQL_CHAR_LIMIT:,}-character limit "
            f"({char_count:,} characters, {char_count / SQL_CHAR_LIMIT:.0%} of limit). "
            "Consider simplifying before adding more measures."
        )

    # Check for GROUP BY when aggregation functions are present
    has_aggregation = bool(AGGREGATION_FUNCTIONS.search(sql))
    has_group_by = bool(GROUP_BY_PATTERN.search(sql))

    if has_aggregation and not has_group_by:
        issues.append(
            "SQL contains aggregation functions (COUNT/SUM/AVG/MIN/MAX) but no GROUP BY clause. "
            "Calculated Insights require GROUP BY for all non-aggregated columns. "
            "Every dimension must appear in both the SELECT and the GROUP BY."
        )

    # Check for missing WHERE clause (performance anti-pattern for large DMOs)
    if not re.search(r"\bWHERE\b", sql, re.IGNORECASE):
        issues.append(
            "SQL has no WHERE clause. For large fact DMOs, an unbounded scan risks "
            "exceeding the 2-hour execution timeout. Add a date filter "
            "(e.g., WHERE event_date__c >= DATEADD(DAY, -730, CURRENT_DATE)) "
            "unless all-time data is genuinely required and the volume is small."
        )

    # Warn if no aggregation and no GROUP BY (might be a dimension-only insight or mistake)
    if not has_aggregation and not has_group_by:
        issues.append(
            "SQL contains no aggregation functions and no GROUP BY. "
            "A valid Calculated Insight must define at least one measure using "
            "COUNT, SUM, AVG, MIN, or MAX with a GROUP BY clause for dimensions."
        )

    return issues


def check_schedule(cadence: str) -> list[str]:
    """Validate a proposed schedule cadence."""
    issues: list[str] = []
    cadence_normalized = cadence.strip().lower().replace(" ", "")
    if cadence_normalized not in VALID_SCHEDULE_CADENCES:
        issues.append(
            f"Schedule cadence '{cadence}' is not valid. "
            "Calculated Insights support exactly three cadences: "
            "every 6 hours, every 12 hours, or every 24 hours. "
            "Hourly, sub-hour, and custom cron schedules are not supported."
        )
    return issues


def check_insight_counts(
    total_count: int | None,
    streaming_count: int | None,
) -> list[str]:
    """Validate org insight counts against platform limits."""
    issues: list[str] = []

    if total_count is not None:
        if total_count >= MAX_TOTAL_INSIGHTS:
            issues.append(
                f"Org total insight count ({total_count}) has reached or exceeded "
                f"the platform limit of {MAX_TOTAL_INSIGHTS} (Calculated + Streaming combined). "
                "No new insights can be created until existing ones are deleted."
            )
        elif total_count >= MAX_TOTAL_INSIGHTS - 10:
            issues.append(
                f"Org total insight count ({total_count}) is within 10 of the "
                f"{MAX_TOTAL_INSIGHTS}-insight platform limit. "
                "Perform a lifecycle review and delete stale insights before adding more."
            )

    if streaming_count is not None:
        if streaming_count >= MAX_STREAMING_INSIGHTS:
            issues.append(
                f"Org Streaming Insight count ({streaming_count}) has reached or exceeded "
                f"the platform limit of {MAX_STREAMING_INSIGHTS}. "
                "No new Streaming Insights can be created until existing ones are deleted."
            )
        elif streaming_count >= MAX_STREAMING_INSIGHTS - 3:
            issues.append(
                f"Org Streaming Insight count ({streaming_count}) is within 3 of the "
                f"{MAX_STREAMING_INSIGHTS}-insight limit. "
                "Review active Streaming Insights and decommission any tied to completed campaigns."
            )

    return issues


def check_streaming_source(source: str) -> list[str]:
    """Validate a proposed Streaming Insight source type."""
    issues: list[str] = []
    source_normalized = source.strip().lower().replace(" ", "_").replace("-", "_")
    if source_normalized not in VALID_STREAMING_SOURCES:
        issues.append(
            f"Streaming Insight source '{source}' is not a supported source type. "
            "Streaming Insights only support: Mobile/Web SDK and "
            "Marketing Cloud Personalization (formerly Interaction Studio). "
            "For Ingestion API, CRM Connector, S3, or MuleSoft sources, "
            "use a Calculated Insight (batch SQL) instead."
        )
    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Scan a metadata directory for Calculated Insight anti-patterns."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for any .json or .xml files that might contain insight configurations
    config_files = list(manifest_dir.rglob("*.json")) + list(manifest_dir.rglob("*.xml"))

    for config_file in config_files:
        try:
            content = config_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Check for rename language (impossible operation — flag for review)
        if RENAME_LANGUAGE_PATTERN.search(content):
            issues.append(
                f"{config_file}: Contains language about renaming a measure or dimension. "
                "Calculated Insight measure/dimension API names are immutable after creation. "
                "Review this file — a delete-and-recreate may be required."
            )

        # Check for invalid schedule cadences in config
        schedule_matches = re.findall(
            r'"schedule"\s*:\s*"([^"]+)"', content, re.IGNORECASE
        )
        for match in schedule_matches:
            normalized = match.strip().lower().replace(" ", "")
            if normalized and normalized not in VALID_SCHEDULE_CADENCES:
                issues.append(
                    f"{config_file}: Schedule value '{match}' is not a valid cadence. "
                    "Valid values are: 6h, 12h, 24h."
                )

    return issues


def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    # Resolve SQL from argument or file
    sql_content: str | None = None
    if args.sql:
        sql_content = args.sql
    elif args.sql_file:
        sql_path = Path(args.sql_file)
        if not sql_path.exists():
            print(f"ERROR: SQL file not found: {sql_path}", file=sys.stderr)
            return 2
        sql_content = sql_path.read_text(encoding="utf-8")

    if sql_content:
        all_issues.extend(check_sql(sql_content))

    if args.schedule:
        all_issues.extend(check_schedule(args.schedule))

    if args.insight_count is not None or args.streaming_count is not None:
        all_issues.extend(
            check_insight_counts(args.insight_count, args.streaming_count)
        )

    if args.streaming_source:
        all_issues.extend(check_streaming_source(args.streaming_source))

    if args.manifest_dir:
        all_issues.extend(check_manifest_dir(Path(args.manifest_dir)))

    if not any(
        [
            sql_content,
            args.schedule,
            args.insight_count is not None,
            args.streaming_count is not None,
            args.streaming_source,
            args.manifest_dir,
        ]
    ):
        print(
            "No inputs provided. Run with --help to see available checks.",
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
