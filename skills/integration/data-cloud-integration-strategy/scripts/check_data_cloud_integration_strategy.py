#!/usr/bin/env python3
"""Checker script for Data Cloud Integration Strategy skill.

Checks org metadata or configuration relevant to Data Cloud Integration Strategy.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_integration_strategy.py [--help]
    python3 check_data_cloud_integration_strategy.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Data Cloud Integration Strategy configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_data_cloud_integration_strategy(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for Python/integration code that claims streaming Ingestion API is real-time
    code_files = list(manifest_dir.rglob("*.py")) + list(manifest_dir.rglob("*.js"))
    for code_file in code_files:
        try:
            text = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect references to sub-minute streaming latency assumptions
        if "ingest" in text.lower() and "real-time" in text.lower():
            issues.append(
                f"{code_file}: Contains 'real-time' near 'ingest' — "
                "Data Cloud Ingestion API streaming is near-real-time (~3 min async), not real-time."
            )

    # Check for OpenAPI schema files in the manifest for Ingestion API connectors
    yaml_files = list(manifest_dir.rglob("*.yaml")) + list(manifest_dir.rglob("*.yml"))
    for yaml_file in yaml_files:
        try:
            text = yaml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Check for engagement-category objects without DateTime field
        if "engagement" in text.lower() and "DateTime" not in text and "datetime" not in text.lower():
            issues.append(
                f"{yaml_file}: Ingestion API schema for engagement-category object may be missing "
                "required DateTime field — engagement DSOs require a DateTime field."
            )

    # Check CSV files for compliance issues (large files > 150MB warning)
    import os
    csv_files = list(manifest_dir.rglob("*.csv"))
    for csv_file in csv_files:
        try:
            size_mb = os.path.getsize(csv_file) / (1024 * 1024)
        except OSError:
            continue
        if size_mb > 150:
            issues.append(
                f"{csv_file}: CSV file is {size_mb:.1f} MB — exceeds 150 MB per-file limit "
                "for Data Cloud Bulk Ingestion API. Split into smaller files."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_cloud_integration_strategy(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
