#!/usr/bin/env python3
"""Checker script for Revenue Intelligence Setup skill.

Scans metadata for RI setup gaps and anti-patterns:
- Opportunity Field History missing on RI-critical fields
- Custom slippage/snapshot objects duplicating Pipeline Inspection
- Dashboards named like hand-rebuilt RI shipped dashboards

Usage:
    python3 check_revenue_intelligence_setup.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


RI_TRACK_FIELDS = {"Amount", "CloseDate", "StageName", "ForecastCategoryName"}
SLIPPAGE_OBJECT_PAT = re.compile(r"(?i)^(opp_?slip|pipeline_?snapshot|deal_?change).*__c$")
DASH_DUPLICATE_PAT = re.compile(r"(?i)(pipeline_?inspection|deal_?waterfall|forecast_?accuracy)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check RI configuration for common issues.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of Salesforce metadata.")
    return parser.parse_args()


def check_history_tracking(root: Path) -> list[str]:
    issues: list[str] = []
    opportunity_object = root / "objects" / "Opportunity" / "Opportunity.object-meta.xml"
    if not opportunity_object.exists():
        return issues
    try:
        text = opportunity_object.read_text(encoding="utf-8")
    except OSError:
        return issues
    if "<enableHistory>true</enableHistory>" not in text:
        issues.append(
            f"{opportunity_object.relative_to(root)}: Opportunity Field History not enabled; RI waterfall requires it"
        )
    tracked = set(re.findall(r"<trackHistory>true</trackHistory>\s*<fullName>([^<]+)</fullName>", text))
    missing = RI_TRACK_FIELDS - tracked
    if missing and "<enableHistory>true</enableHistory>" in text:
        issues.append(
            f"Opportunity Field History missing tracking on RI-critical fields: {', '.join(sorted(missing))}"
        )
    return issues


def check_slippage_duplicates(root: Path) -> list[str]:
    issues: list[str] = []
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return issues
    for child in objects_dir.iterdir():
        if child.is_dir() and SLIPPAGE_OBJECT_PAT.match(child.name):
            issues.append(
                f"Custom object {child.name} duplicates Pipeline Inspection; prefer shipped RI views"
            )
    return issues


def check_duplicate_dashboards(root: Path) -> list[str]:
    issues: list[str] = []
    dash_dir = root / "dashboards"
    if not dash_dir.exists():
        return issues
    for path in dash_dir.rglob("*.dashboard-meta.xml"):
        if DASH_DUPLICATE_PAT.search(path.stem):
            issues.append(
                f"{path.relative_to(root)}: dashboard name overlaps shipped RI asset; verify not a manual rebuild"
            )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues.extend(check_history_tracking(manifest_dir))
    issues.extend(check_slippage_duplicates(manifest_dir))
    issues.extend(check_duplicate_dashboards(manifest_dir))

    if not issues:
        print("No Revenue Intelligence setup issues detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
