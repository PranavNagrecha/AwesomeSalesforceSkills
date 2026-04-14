#!/usr/bin/env python3
"""Checker script for Analytics Kpi Definition skill.

Checks org metadata or configuration relevant to Analytics Kpi Definition.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_analytics_kpi_definition.py [--help]
    python3 check_analytics_kpi_definition.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Analytics Kpi Definition configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_kpi_register_document(file_path: Path) -> list[str]:
    """Check a KPI register markdown document for completeness."""
    issues: list[str] = []

    if not file_path.exists():
        return issues

    content = file_path.read_text(encoding="utf-8")
    lower = content.lower()

    # Check for measure/dimension type confirmation
    if "measure" not in lower or "dimension" not in lower:
        issues.append(
            f"{file_path.name}: KPI register should confirm field types (Measure vs Dimension) "
            "for each field used in formulas. CRM Analytics enforces this distinction at runtime."
        )

    # Check for target model documentation
    if "target" not in lower:
        issues.append(
            f"{file_path.name}: KPI register does not mention target values or target attainment model. "
            "If stakeholders need actual-vs-target comparison, document the targets dataset schema."
        )

    # Check for stakeholder sign-off indicator
    if "sign-off" not in lower and "approved" not in lower and "sign off" not in lower:
        issues.append(
            f"{file_path.name}: KPI register should record stakeholder sign-off before development. "
            "Add an approval/sign-off section to prevent mid-build formula disputes."
        )

    # Check for SAQL formula sketches
    if "saql" not in lower and "foreach" not in lower and "cogroup" not in lower:
        issues.append(
            f"{file_path.name}: KPI register should include SAQL formula sketches. "
            "Formula sketches validate that the metric can be expressed in SAQL before build starts."
        )

    return issues


def check_analytics_kpi_definition(manifest_dir: Path) -> list[str]:
    """Check a metadata or documentation directory for KPI definition completeness."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Directory not found: {manifest_dir}")
        return issues

    # Look for KPI register files
    kpi_files = (
        list(manifest_dir.rglob("kpi-register*"))
        + list(manifest_dir.rglob("*kpi*register*"))
        + list(manifest_dir.rglob("*analytics*kpi*"))
    )
    for kf in kpi_files:
        if kf.suffix in (".md", ".txt", ".csv"):
            issues.extend(check_kpi_register_document(kf))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_analytics_kpi_definition(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
