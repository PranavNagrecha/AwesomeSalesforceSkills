#!/usr/bin/env python3
"""Checker script for Data Cloud Ingestion API skill.

Validates Ingestion API schema files and integration code for common issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_ingestion_api.py --schema-dir <path>
    python3 check_data_cloud_ingestion_api.py --manifest-dir <path>

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

import argparse
import re
import sys
from pathlib import Path


def check_schema_files(schema_dir: Path) -> list[str]:
    """Validate OpenAPI schema YAML files for Ingestion API requirements."""
    issues = []
    yaml_files = list(schema_dir.glob("**/*.yaml")) + list(schema_dir.glob("**/*.yml"))

    for schema_file in yaml_files:
        try:
            content = schema_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Skip non-OpenAPI files
        if "openapi" not in content.lower():
            continue

        # Check for Engagement category objects missing date-time field
        if "Engagement" in content or "engagement" in content:
            if "date-time" not in content and "dateTime" not in content:
                issues.append(
                    f"ERROR: {schema_file.name} appears to define an Engagement-category object "
                    f"but does not include a field with format: date-time. "
                    f"Engagement objects require a DateTime field for Data Cloud schema registration."
                )

        # Check for cdp_ingest_api scope mention if Connected App setup is described
        if "ConnectedApp" in content or "clientId" in content or "client_id" in content:
            if "cdp_ingest_api" not in content:
                issues.append(
                    f"WARN: {schema_file.name} references Connected App configuration but does not "
                    f"mention cdp_ingest_api OAuth scope. "
                    f"The cdp_ingest_api scope is required for Ingestion API authentication."
                )

    return issues


def check_bulk_delta_pattern(path: Path) -> list[str]:
    """Warn if code suggests bulk ingestion with delta/incremental files."""
    issues = []
    delta_patterns = [
        re.compile(r"delta|incremental|changed.since|new.records", re.IGNORECASE),
    ]
    bulk_pattern = re.compile(r"bulk.*job|ingest.*job|/jobs", re.IGNORECASE)

    for code_file in list(path.glob("**/*.py")) + list(path.glob("**/*.js")) + list(path.glob("**/*.cls")):
        try:
            content = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if bulk_pattern.search(content) and any(p.search(content) for p in delta_patterns):
            issues.append(
                f"WARN: {code_file.name} appears to use bulk ingestion with delta/incremental file logic. "
                f"Data Cloud Bulk Ingestion uses full-replace semantics — uploading only delta records "
                f"will delete all existing records not in the file. "
                f"Use streaming ingestion for incremental updates."
            )
    return issues


def check_oauth_scope(path: Path) -> list[str]:
    """Warn if Connected App configuration uses api scope without cdp_ingest_api."""
    issues = []
    for code_file in list(path.glob("**/*.py")) + list(path.glob("**/*.js")) + list(path.glob("**/*.yaml")):
        try:
            content = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "scope" in content and "api" in content:
            if "cdp_ingest_api" not in content and ("ingestion" in content.lower() or "ingest" in content.lower()):
                issues.append(
                    f"WARN: {code_file.name} appears to configure OAuth scope for an ingestion integration "
                    f"but does not include cdp_ingest_api scope. "
                    f"Tokens without cdp_ingest_api will receive 401 Unauthorized on Ingestion API endpoints."
                )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Data Cloud Ingestion API schema and integration code."
    )
    parser.add_argument("--schema-dir", type=Path, default=None,
                        help="Directory containing OpenAPI YAML schema files to validate")
    parser.add_argument("--manifest-dir", type=Path, default=None,
                        help="Directory containing integration code to scan")
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.schema_dir and args.schema_dir.exists():
        all_issues.extend(check_schema_files(args.schema_dir))
    elif args.schema_dir:
        all_issues.append(f"ERROR: Schema directory not found: {args.schema_dir}")

    if args.manifest_dir and args.manifest_dir.exists():
        all_issues.extend(check_bulk_delta_pattern(args.manifest_dir))
        all_issues.extend(check_oauth_scope(args.manifest_dir))
    elif args.manifest_dir:
        all_issues.append(f"ERROR: Manifest directory not found: {args.manifest_dir}")

    if not args.schema_dir and not args.manifest_dir:
        print("INFO: No input provided. Use --schema-dir or --manifest-dir.")
        return 0

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    print("OK: No Data Cloud Ingestion API issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
