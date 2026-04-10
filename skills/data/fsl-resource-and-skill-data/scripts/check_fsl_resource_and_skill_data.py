#!/usr/bin/env python3
"""Checker script for FSL Resource and Skill Data skill.

Scans CSV data files for common FSL resource/skill migration issues:
- SkillLevel columns containing non-numeric values
- ServiceResourceSkill missing EffectiveStartDate
- ServiceResource missing IsCapacityBased flag when capacity CSV present

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_resource_and_skill_data.py [--help]
    python3 check_fsl_resource_and_skill_data.py --manifest-dir path/to/data-extracts
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

_SKILL_LEVEL_VALUES_TO_FLAG = {"expert", "intermediate", "beginner", "advanced", "basic", "level"}


def check_fsl_resource_and_skill_data(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    csv_files = list(manifest_dir.rglob("*.csv"))
    if not csv_files:
        return issues

    has_capacity_file = any(
        "serviceresourcecapacity" in f.name.lower() or "resource_capacity" in f.name.lower()
        for f in csv_files
    )

    for csv_file in csv_files:
        fname_lower = csv_file.name.lower()
        rel = csv_file.relative_to(manifest_dir)

        # Check ServiceResourceSkill CSVs
        if "serviceresourceskill" in fname_lower or "resource_skill" in fname_lower:
            try:
                with csv_file.open(encoding="utf-8-sig", errors="replace") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames or []
                    lower_headers = [h.lower() for h in headers]

                    # Check for EffectiveStartDate
                    if not any("effectivestartdate" in h or "effective_start" in h for h in lower_headers):
                        issues.append(
                            f"{rel}: ServiceResourceSkill file missing EffectiveStartDate column. "
                            "EffectiveStartDate is required for certification tracking."
                        )

                    # Check SkillLevel for text values
                    skill_level_col = None
                    for h in headers:
                        if "skilllevel" in h.lower() or "skill_level" in h.lower():
                            skill_level_col = h
                            break

                    if skill_level_col:
                        for i, row in enumerate(reader, start=2):
                            val = row.get(skill_level_col, "").strip().lower()
                            if val and not re.match(r'^\d+$', val):
                                if any(kw in val for kw in _SKILL_LEVEL_VALUES_TO_FLAG):
                                    issues.append(
                                        f"{rel}:row {i}: SkillLevel value '{val}' is text. "
                                        "SkillLevel must be a numeric integer (0-99999). "
                                        "Define a mapping table and transform before loading."
                                    )
                                    break  # Only report first occurrence

            except (OSError, csv.Error):
                continue

        # Check ServiceResource CSVs for IsCapacityBased when capacity file present
        if ("serviceresource" in fname_lower or "service_resource" in fname_lower) and \
           "skill" not in fname_lower and "capacity" not in fname_lower and "member" not in fname_lower:
            if has_capacity_file:
                try:
                    with csv_file.open(encoding="utf-8-sig", errors="replace") as f:
                        reader = csv.DictReader(f)
                        headers = [h.lower() for h in (reader.fieldnames or [])]
                        rel = csv_file.relative_to(manifest_dir)

                        if not any("iscapacitybased" in h or "is_capacity" in h for h in headers):
                            issues.append(
                                f"{rel}: ServiceResource file detected alongside a capacity file, "
                                "but no IsCapacityBased column found. "
                                "ServiceResourceCapacity records require IsCapacityBased = true on the parent ServiceResource."
                            )
                except (OSError, csv.Error):
                    continue

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSL resource and skill CSV files for common migration issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing migration CSV files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_resource_and_skill_data(manifest_dir)

    if not issues:
        print("No FSL Resource and Skill Data issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
