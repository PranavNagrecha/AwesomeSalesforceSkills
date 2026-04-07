#!/usr/bin/env python3
"""Checker script for Data Extension Design skill.

Scans a directory of Marketing Cloud Data Extension definition files
(JSON or CSV-manifest style) for common design problems documented
in this skill's gotchas and anti-patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_extension_design.py [--help]
    python3 check_data_extension_design.py --manifest-dir path/to/de/definitions
    python3 check_data_extension_design.py --manifest-dir . --format json

The checker looks for:
  - DE definitions (JSON files) in the manifest directory
  - Markdown or text files containing DE schema descriptions
  - Any file referencing common anti-patterns by keyword
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DE_EXTENSIONS = {".json", ".md", ".txt"}

# Non-PK fields that are commonly used as query filters — flag these for
# indexing review if found in WHERE clauses or Lookup calls.
COMMON_NON_PK_FILTER_FIELDS = re.compile(
    r"\b(SegmentCode|RegionCode|ProductCategory|ProductInterest|Status|Tier|Type)\b",
    re.IGNORECASE,
)

# Patterns indicating a WHERE clause on a potentially non-PK field
SQL_WHERE_PATTERN = re.compile(
    r"\bWHERE\b.{0,200}",
    re.IGNORECASE | re.DOTALL,
)

# Patterns indicating Email Address send relationship mapping
EMAIL_SEND_RELATIONSHIP = re.compile(
    r"(send.?relationship|maps.?to).{0,100}email.?address",
    re.IGNORECASE,
)

# Patterns indicating ResetRetentionPeriodOnImport is not mentioned alongside retention config
RETENTION_PERIOD_PATTERN = re.compile(
    r"(retention|retentionPeriod|deleteAfter)",
    re.IGNORECASE,
)
RESET_RETENTION_PATTERN = re.compile(
    r"ResetRetentionPeriodOnImport",
    re.IGNORECASE,
)

# Pattern for Date-only primary key
DATE_ONLY_PK = re.compile(
    r'"type"\s*:\s*"[Dd]ate".*?"isPrimaryKey"\s*:\s*true',
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def find_de_files(manifest_dir: Path) -> list[Path]:
    """Return all DE definition files in the manifest directory."""
    files: list[Path] = []
    for ext in DE_EXTENSIONS:
        files.extend(manifest_dir.rglob(f"*{ext}"))
    return sorted(files)


# ---------------------------------------------------------------------------
# JSON DE definition checks
# ---------------------------------------------------------------------------


def check_json_de(file_path: Path, content: str) -> list[str]:
    """Check a JSON DE definition file for common design problems."""
    issues: list[str] = []

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Not valid JSON — skip JSON-specific checks
        return issues

    # Extract fields array (common schema formats)
    fields = data.get("fields", data.get("columns", data.get("Fields", [])))
    if not isinstance(fields, list):
        return issues

    # --- PK checks ---
    pk_fields = [
        f for f in fields
        if f.get("isPrimaryKey") or f.get("IsPrimaryKey") or f.get("primaryKey")
    ]

    if len(pk_fields) > 3:
        issues.append(
            f"{file_path.name}: More than 3 primary key fields defined "
            f"({len(pk_fields)} found). Marketing Cloud supports a maximum of 3 PK columns."
        )

    # Date-only PK check
    date_pk_fields = [
        f for f in pk_fields
        if str(f.get("type", f.get("Type", ""))).lower() == "date"
    ]
    if len(date_pk_fields) > 0 and len(pk_fields) == 1:
        issues.append(
            f"{file_path.name}: Date field '{date_pk_fields[0].get('name', 'unknown')}' "
            "is the sole primary key. Marketing Cloud does not allow a Date field as the "
            "only primary key. Add a second PK field or store the date as Text."
        )

    # --- Column count check ---
    if len(fields) > 200:
        issues.append(
            f"{file_path.name}: DE has {len(fields)} columns. Performance degrades "
            "significantly above ~200 columns. Consider splitting into multiple DEs "
            "with a shared SubscriberKey."
        )

    # --- Sendable DE checks ---
    is_sendable = (
        data.get("isSendable")
        or data.get("IsSendable")
        or data.get("sendable")
    )
    send_relationship = (
        data.get("sendRelationship")
        or data.get("SendRelationship")
        or data.get("send_relationship")
    )

    if is_sendable and not send_relationship:
        issues.append(
            f"{file_path.name}: DE is marked sendable but no Send Relationship is defined. "
            "A sendable DE requires exactly one Send Relationship mapping a field to "
            "SubscriberKey or Email Address in All Subscribers."
        )

    if send_relationship:
        # Check if mapped to Email Address instead of SubscriberKey
        target = str(send_relationship.get("subscriberFieldName", "")).lower()
        if "email" in target and "subscriberkey" not in target:
            issues.append(
                f"{file_path.name}: Send Relationship is mapped to Email Address. "
                "This causes subscriber deduplication issues when contacts have multiple "
                "email addresses. Prefer mapping to Subscriber Key instead."
            )

    # --- Data retention checks ---
    retention = (
        data.get("dataRetentionPolicy")
        or data.get("DataRetentionPolicy")
        or data.get("retention")
    )
    if retention:
        reset_key = (
            retention.get("resetRetentionPeriodOnImport")
            or retention.get("ResetRetentionPeriodOnImport")
        )
        if reset_key is None:
            issues.append(
                f"{file_path.name}: Data retention is configured but "
                "'ResetRetentionPeriodOnImport' is not explicitly set. "
                "The default is false — rows expire from creation date even if "
                "regularly imported via upsert. Set this explicitly based on import pattern."
            )

    return issues


# ---------------------------------------------------------------------------
# Text / Markdown file checks
# ---------------------------------------------------------------------------


def check_text_file(file_path: Path, content: str) -> list[str]:
    """Check a text or Markdown file for common DE design anti-patterns."""
    issues: list[str] = []

    # Check for Email Address send relationship in prose/config
    if EMAIL_SEND_RELATIONSHIP.search(content):
        issues.append(
            f"{file_path.name}: Possible Send Relationship mapped to Email Address. "
            "Prefer Subscriber Key mapping for stable subscriber identity."
        )

    # Check for retention config without ResetRetentionPeriodOnImport
    if RETENTION_PERIOD_PATTERN.search(content) and not RESET_RETENTION_PATTERN.search(content):
        issues.append(
            f"{file_path.name}: File references data retention but does not mention "
            "'ResetRetentionPeriodOnImport'. Verify this setting is explicitly configured."
        )

    # Check for SQL WHERE on common non-PK fields without indexing note
    where_matches = SQL_WHERE_PATTERN.findall(content)
    for where_clause in where_matches:
        field_matches = COMMON_NON_PK_FILTER_FIELDS.findall(where_clause)
        if field_matches and "index" not in where_clause.lower():
            issues.append(
                f"{file_path.name}: SQL WHERE clause filters on "
                f"{set(field_matches)} — these are likely non-PK fields. "
                "Confirm a custom index exists (via Salesforce Support ticket) "
                "before using this pattern on large DEs."
            )

    return issues


# ---------------------------------------------------------------------------
# Main checker
# ---------------------------------------------------------------------------


def check_data_extension_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in DE definition files."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    de_files = find_de_files(manifest_dir)

    if not de_files:
        # Not an error — the directory may not contain DE files
        return issues

    for file_path in de_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            issues.append(f"{file_path.name}: Could not read file — {exc}")
            continue

        if file_path.suffix == ".json":
            issues.extend(check_json_de(file_path, content))
        else:
            issues.extend(check_text_file(file_path, content))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Marketing Cloud Data Extension definition files for common "
            "design problems: PK composition, Send Relationship mapping, "
            "data retention configuration, column count, and indexing risks."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Directory containing DE definition files (JSON, MD, or TXT). Default: current directory.",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_data_extension_design(manifest_dir)

    if not issues:
        print("No Data Extension design issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
