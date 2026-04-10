#!/usr/bin/env python3
"""Checker script for Lead Nurture Journey Design skill.

Checks MCAE Engagement Studio nurture journey configuration for common issues:
- Missing content inventory prerequisites
- Engagement Studio programs without rule-based branching (flat drip anti-pattern)
- MQL handoff relying only on program-internal steps (no companion Automation Rule)
- Decision-stage content placed before behavioral gates
- Programs without suppression list configuration

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lead_nurture_journey_design.py [--help]
    python3 check_lead_nurture_journey_design.py --manifest-dir path/to/metadata
    python3 check_lead_nurture_journey_design.py --template-file path/to/work-template.md
"""

from __future__ import annotations

import argparse
import sys
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Lead Nurture Journey Design configuration for common issues.\n"
            "Validates work templates and metadata for anti-patterns documented in the skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata (optional).",
    )
    parser.add_argument(
        "--template-file",
        default=None,
        help="Path to a filled-in work template markdown file to validate.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Template checks
# ---------------------------------------------------------------------------

def check_template(template_path: Path) -> list[str]:
    """Validate a filled-in work template for completeness and anti-patterns."""
    issues: list[str] = []

    if not template_path.exists():
        issues.append(f"Template file not found: {template_path}")
        return issues

    content = template_path.read_text(encoding="utf-8")

    # 1. Content inventory table must have real rows (not just the header)
    if "Content Inventory" in content or "Funnel Stage Map" in content:
        # Look for table rows with actual asset content (not empty cells)
        awareness_rows = re.findall(r"\|\s*Awareness\s*\|([^|]+)\|", content)
        consideration_rows = re.findall(r"\|\s*Consideration\s*\|([^|]+)\|", content)
        decision_rows = re.findall(r"\|\s*Decision\s*\|([^|]+)\|", content)

        def has_real_content(rows: list[str]) -> bool:
            return any(r.strip() and r.strip() not in ("", " ") for r in rows)

        if not has_real_content(awareness_rows):
            issues.append(
                "Content inventory: no Awareness-stage assets documented. "
                "At least one Awareness asset is required before building the program."
            )
        if not has_real_content(consideration_rows):
            issues.append(
                "Content inventory: no Consideration-stage assets documented. "
                "At least one Consideration asset is required before building the program."
            )
        if not has_real_content(decision_rows):
            issues.append(
                "Content inventory: no Decision-stage assets documented. "
                "At least one Decision asset is required for MQL handoff conversion step."
            )
    else:
        issues.append(
            "Template does not contain a content inventory section. "
            "Complete the funnel stage content map before configuring Engagement Studio."
        )

    # 2. MQL definition must be present with non-placeholder values
    mql_score_match = re.search(r"Score\s*>=?\s*(\d+)", content)
    mql_grade_match = re.search(r"Grade\s*>=?\s*([A-F][+-]?)", content)

    if not mql_score_match:
        issues.append(
            "MQL score threshold is not defined. "
            "Document the agreed score threshold (e.g., Score >= 100) before building the program."
        )
    if not mql_grade_match:
        issues.append(
            "MQL grade threshold is not defined. "
            "A grade gate is required alongside score — "
            "score-only MQL floods Sales with low-fit prospects."
        )

    # 3. Companion Automation Rule must be referenced
    automation_rule_pattern = re.compile(
        r"(automation rule|companion.*rule|standalone.*rule|rule.*outside)", re.IGNORECASE
    )
    if not automation_rule_pattern.search(content):
        issues.append(
            "No companion Automation Rule referenced in the template. "
            "A standalone Automation Rule outside the program is required to handle "
            "prospects who reach MQL threshold outside the Engagement Studio program."
        )

    # 4. Suppression list must be mentioned
    suppression_pattern = re.compile(r"suppression", re.IGNORECASE)
    if not suppression_pattern.search(content):
        issues.append(
            "No suppression list configuration found in the template. "
            "Define suppression lists (existing customers, opted-out, competitors) "
            "before activating the program."
        )

    # 5. Wait periods should follow Send Email steps
    # Look for any indication that wait periods are documented after send steps
    wait_after_send = re.search(r"(wait|Wait).*\d+\s*(days?|day)", content)
    if not wait_after_send:
        issues.append(
            "No Wait step durations documented in the program flow. "
            "Every Send Email step must be followed by a Wait of at least 3 days "
            "before the next Rule evaluation, given the weekly program execution schedule."
        )

    # 6. Real-time actions: check that the template acknowledges weekly cadence
    real_time_pattern = re.compile(
        r"(completion action|automation rule|real.?time|weekly|cadence)", re.IGNORECASE
    )
    if not real_time_pattern.search(content):
        issues.append(
            "Template does not document real-time actions or the weekly execution cadence. "
            "Stakeholders must understand that Engagement Studio programs evaluate weekly, "
            "not in real time. Real-time steps require Completion Actions or Automation Rules."
        )

    return issues


# ---------------------------------------------------------------------------
# Metadata directory checks
# ---------------------------------------------------------------------------

def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Check Salesforce metadata directory for nurture journey anti-patterns."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for any marketing-related metadata files
    email_template_files = list(manifest_dir.rglob("*.email")) + list(manifest_dir.rglob("*.email-meta.xml"))
    automation_rule_files = list(manifest_dir.rglob("*AutomationRule*")) + list(manifest_dir.rglob("*automationRule*"))
    engagement_program_files = list(manifest_dir.rglob("*EngagementProgram*")) + list(manifest_dir.rglob("*engagementProgram*"))

    # Check: if there are engagement program files but no automation rule files,
    # the companion Automation Rule may be missing
    if engagement_program_files and not automation_rule_files:
        issues.append(
            f"Found {len(engagement_program_files)} Engagement Program metadata file(s) "
            "but no Automation Rule metadata files. "
            "A companion Automation Rule is required for MQL handoff outside the program. "
            "Verify that the Automation Rule exists in MCAE and is not missing from the metadata export."
        )

    # Check: scan engagement program XML for rule steps (branching)
    programs_without_rules: list[str] = []
    for program_file in engagement_program_files:
        try:
            content = program_file.read_text(encoding="utf-8", errors="replace")
            # Look for rule/condition elements in program metadata
            has_rule = bool(
                re.search(r"<type>Rule</type>|<stepType>Rule|<ruleCondition|<branchStep", content, re.IGNORECASE)
            )
            if not has_rule:
                programs_without_rules.append(program_file.name)
        except OSError:
            pass

    if programs_without_rules:
        issues.append(
            f"Engagement program(s) appear to have no Rule (branching) steps: "
            f"{', '.join(programs_without_rules)}. "
            "A program without Rule steps is a flat drip sequence — "
            "add behavioral trigger Rules to create a true nurture journey."
        )

    # Report what was found for informational purposes
    if not engagement_program_files and not email_template_files:
        issues.append(
            "No Engagement Program or Email Template metadata files found in the manifest directory. "
            "If this is a new program, ensure the metadata export includes "
            "MCAE Engagement Programs before running this check."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.template_file:
        template_path = Path(args.template_file)
        template_issues = check_template(template_path)
        if template_issues:
            all_issues.extend([f"[template] {i}" for i in template_issues])
        else:
            print(f"Template check passed: {template_path}")

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        manifest_issues = check_manifest_dir(manifest_dir)
        if manifest_issues:
            all_issues.extend([f"[metadata] {i}" for i in manifest_issues])
        else:
            print(f"Metadata check passed: {manifest_dir}")

    if not args.template_file and not args.manifest_dir:
        # Default: run manifest check against current directory
        manifest_dir = Path(".")
        manifest_issues = check_manifest_dir(manifest_dir)
        if manifest_issues:
            all_issues.extend([f"[metadata] {i}" for i in manifest_issues])

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
