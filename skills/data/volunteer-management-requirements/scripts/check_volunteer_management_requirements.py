#!/usr/bin/env python3
"""Checker script for Volunteer Management Requirements skill.

Checks org metadata or configuration relevant to volunteer management in Salesforce nonprofits.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_volunteer_management_requirements.py --manifest-dir <path>
    python3 check_volunteer_management_requirements.py --soql-output <soql_json_file>

Exit codes:
    0 — no issues found
    1 — one or more warnings or errors found
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def check_v4s_namespace_in_soql(path: Path) -> list[str]:
    """Scan .cls and .trigger files for V4S object references missing the GW_Volunteers__ prefix."""
    issues = []
    v4s_objects_bare = [
        "Volunteer_Hours__c",
        "Volunteer_Shift__c",
        "Volunteer_Job__c",
        "Volunteer_Campaign__c",
    ]
    pattern_correct_prefix = re.compile(r"GW_Volunteers__Volunteer_")

    apex_files = list(path.glob("**/*.cls")) + list(path.glob("**/*.trigger"))
    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for obj in v4s_objects_bare:
            # Look for bare object names not preceded by GW_Volunteers__
            matches = re.findall(rf"(?<!GW_Volunteers__){re.escape(obj)}", content)
            if matches:
                issues.append(
                    f"WARN: {apex_file.name} references '{obj}' without 'GW_Volunteers__' "
                    f"namespace prefix ({len(matches)} occurrence(s)). "
                    f"V4S objects require fully qualified API names."
                )
    return issues


def check_dpe_dependency_in_flow(path: Path) -> list[str]:
    """Warn if a Flow reads TotalVolunteerHours__c in a record-triggered flow on a hours object."""
    issues = []
    flow_files = list(path.glob("**/*.flow-meta.xml")) + list(path.glob("**/*.flow"))
    total_hours_pattern = re.compile(r"TotalVolunteerHours__c", re.IGNORECASE)
    hours_trigger_pattern = re.compile(r"VolunteerHoursLog|Volunteer_Hours", re.IGNORECASE)

    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if total_hours_pattern.search(content) and hours_trigger_pattern.search(content):
            issues.append(
                f"WARN: {flow_file.name} appears to read TotalVolunteerHours__c in a flow "
                f"that also references a volunteer hours object. In NPC, TotalVolunteerHours__c "
                f"is a DPE-computed field — reading it in the same flow that inserts hours will "
                f"return a stale value. Decouple recognition checks from the hours insert event."
            )
    return issues


def check_platform_consistency(soql_output: Path) -> list[str]:
    """If a SOQL output JSON is provided, check for mixed V4S and NPC volunteer object usage."""
    issues = []
    if not soql_output.exists():
        return issues

    try:
        data = json.loads(soql_output.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        issues.append(f"ERROR: Could not parse SOQL output file: {exc}")
        return issues

    has_v4s = any("GW_Volunteers__" in str(row) for row in data.get("records", []))
    has_npc = any("VolunteerInitiative__c" in str(row) or "JobPositionAssignment__c" in str(row)
                  for row in data.get("records", []))

    if has_v4s and has_npc:
        issues.append(
            "ERROR: SOQL output contains both V4S (GW_Volunteers__ namespace) and NPC-native "
            "volunteer objects. These two platforms must not be mixed in the same data process. "
            "Confirm which platform the org uses and remove references to the other."
        )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate volunteer management configuration for NPSP/NPC orgs."
    )
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=Path("."),
        help="Root directory of Salesforce metadata to scan (default: current directory)",
    )
    parser.add_argument(
        "--soql-output",
        type=Path,
        default=None,
        help="Optional JSON file containing SOQL query results for platform consistency check",
    )
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.manifest_dir.exists():
        all_issues.extend(check_v4s_namespace_in_soql(args.manifest_dir))
        all_issues.extend(check_dpe_dependency_in_flow(args.manifest_dir))
    else:
        all_issues.append(f"ERROR: Manifest directory not found: {args.manifest_dir}")

    if args.soql_output:
        all_issues.extend(check_platform_consistency(args.soql_output))

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    print("OK: No volunteer management configuration issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
