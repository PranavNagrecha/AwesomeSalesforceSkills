#!/usr/bin/env python3
"""Checker script for FlexCard Requirements skill.

Validates FlexCard requirements documents for structural completeness:
- Data source types specified for all data fields
- Card state templates with condition expressions documented
- Action requirements with action types specified
- Build dependency order present for nested cards

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_flexcard_requirements.py [--help]
    python3 check_flexcard_requirements.py --requirements-file path/to/requirements.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FlexCard requirements document for structural completeness.",
    )
    parser.add_argument(
        "--requirements-file",
        default=None,
        help="Path to the FlexCard requirements markdown file.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_requirements_document(file_path: Path) -> list[str]:
    """Check a FlexCard requirements markdown document for common structural gaps."""
    issues: list[str] = []

    if not file_path.exists():
        issues.append(f"Requirements file not found: {file_path}")
        return issues

    content = file_path.read_text(encoding="utf-8")
    lower = content.lower()

    # Check for data source type specification
    valid_sources = [
        "soql", "dataraptor", "integration procedure", "apex", "streaming"
    ]
    has_data_source = any(s in lower for s in valid_sources)
    if not has_data_source:
        issues.append(
            "MISSING data source type: Requirements do not specify a data source type "
            "(SOQL, DataRaptor, Integration Procedure, Apex, or Streaming). "
            "Every FlexCard must have a documented data source type."
        )

    # Check for action type specification
    valid_actions = [
        "navigation", "omniscript launch", "apex action", "dataraptor action",
        "custom lwc", "action type"
    ]
    has_action_type = any(a in lower for a in valid_actions)
    # Only warn if the doc mentions buttons or actions
    has_actions_mentioned = re.search(r"\baction\b|\bbutton\b|\bclick\b", lower)
    if has_actions_mentioned and not has_action_type:
        issues.append(
            "MISSING action type: Requirements mention user actions but do not specify "
            "action types (Navigation, OmniScript Launch, Apex, DataRaptor, Custom LWC). "
            "Each action must have a documented type."
        )

    # Check for card state documentation
    has_state_mention = re.search(
        r"state template|card state|conditional layout|different (?:layout|view)", lower
    )
    has_state_condition = re.search(r"\{.*\}\s*==|\{.*\}\s*!=|condition expression", lower)
    if has_state_mention and not has_state_condition:
        issues.append(
            "MISSING card state conditions: Requirements mention conditional layouts or "
            "card states but do not specify condition expressions. "
            "Card state templates require explicit condition expressions (e.g., {Status__c} == 'Active')."
        )

    # Check for nested component dependency documentation
    has_nested = re.search(
        r"child (?:flexcard|card)|nested card|embedded flexcard|embed.*card", lower
    )
    has_dependency = re.search(
        r"activation (?:order|dependency)|build (?:order|dependency)|must be active", lower
    )
    if has_nested and not has_dependency:
        issues.append(
            "MISSING activation dependency: Requirements specify nested or child FlexCards "
            "but do not document the activation dependency order. "
            "Child FlexCards must be activated before the parent card can be activated."
        )

    # Check for SOQL used for aggregated/computed fields (warning)
    if re.search(r"count|sum|aggregate|computed|calculated", lower) and "soql" in lower:
        # Check if IP is also mentioned for those fields
        if "integration procedure" not in lower and "apex" not in lower:
            issues.append(
                "POSSIBLE incorrect data source: Requirements mention aggregated or computed "
                "fields and specify SOQL as the data source without Integration Procedure or Apex. "
                "Aggregated fields typically require Integration Procedure or Apex data sources."
            )

    return issues


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.requirements_file:
        req_file = Path(args.requirements_file)
        issues.extend(check_requirements_document(req_file))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
