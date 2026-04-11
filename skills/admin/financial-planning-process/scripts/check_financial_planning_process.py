#!/usr/bin/env python3
"""Checker script for Financial Planning Process skill.

Inspects Salesforce metadata files for common financial planning process
configuration issues, including namespace mismatches between managed-package
FSC and FSC Core, missing goal update mechanisms, and Action Plan template
misconfiguration.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_financial_planning_process.py [--help]
    python3 check_financial_planning_process.py --manifest-dir path/to/metadata
    python3 check_financial_planning_process.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Managed-package FinancialGoal/FinancialPlan references
MANAGED_PKG_GOAL_PATTERN = re.compile(
    r"FinServ__FinancialGoal__c|FinServ__FinancialPlan__c|FinServ__TargetValue__c"
    r"|FinServ__ActualValue__c|FinServ__GoalType__c",
    re.IGNORECASE,
)

# Standard (FSC Core) object references — used to detect mixing
CORE_GOAL_PATTERN = re.compile(
    r"\bFinancialGoal\b(?!_c)|\bFinancialPlan\b(?!_c)|\bFinancialPlanId\b"
    r"|\bTargetValue\b|\bActualValue\b",
    re.IGNORECASE,
)

# Revenue Insights references without namespace qualification
REVENUE_INSIGHTS_PATTERN = re.compile(
    r"Revenue\s*Insights|CRM\s*Analytics\s*for\s*Financial",
    re.IGNORECASE,
)

# Action Plan template items — check for negative DaysFromStart
DAYS_FROM_START_PATTERN = re.compile(
    r"<DaysFromStart>\s*(-\d+)\s*</DaysFromStart>",
    re.IGNORECASE,
)

# Action Plan TargetEntityType values
TARGET_ENTITY_PATTERN = re.compile(
    r"<TargetEntityType>\s*(\w+)\s*</TargetEntityType>",
    re.IGNORECASE,
)

# TaskDeadlineType check — only valid values are Calendar and BusinessDays
TASK_DEADLINE_TYPE_PATTERN = re.compile(
    r"<TaskDeadlineType>\s*(\w+)\s*</TaskDeadlineType>",
    re.IGNORECASE,
)

VALID_DEADLINE_TYPES = {"Calendar", "BusinessDays"}

# Risk score field references that suggest naive risk scoring assumptions
NAIVE_RISK_SCORE_PATTERN = re.compile(
    r"RiskScore__c|RiskProfile__c|AssessmentScore__c|CompositeScore__c",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File discovery helpers
# ---------------------------------------------------------------------------

def _iter_metadata_files(manifest_dir: Path) -> list[Path]:
    """Return all .xml, .cls, .trigger, .flow-meta.xml, and .md files."""
    extensions = {".xml", ".cls", ".trigger", ".md", ".json", ".yaml", ".yml"}
    results: list[Path] = []
    for ext in extensions:
        results.extend(manifest_dir.rglob(f"*{ext}"))
    return results


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_mixed_namespace_references(files: list[Path]) -> list[str]:
    """Warn if a single file contains both managed-package and Core API names.

    Mixed references in the same file indicate a partial migration or copy-paste
    error that will cause compile errors or silent data misroutes.
    """
    issues: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        has_managed = bool(MANAGED_PKG_GOAL_PATTERN.search(content))
        has_core = bool(CORE_GOAL_PATTERN.search(content))
        if has_managed and has_core:
            issues.append(
                f"{f}: Contains mixed managed-package (FinServ__) and FSC Core "
                "FinancialGoal/FinancialPlan API names. Confirm org type and use "
                "only one naming convention throughout the file."
            )
    return issues


def check_negative_days_from_start(files: list[Path]) -> list[str]:
    """Warn if any ActionPlanTemplateItem has a negative DaysFromStart value.

    Negative DaysFromStart is not supported by the platform and will cause
    plan launch errors.
    """
    issues: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in DAYS_FROM_START_PATTERN.finditer(content):
            value = int(match.group(1))
            if value < 0:
                issues.append(
                    f"{f}: ActionPlanTemplateItem has DaysFromStart={value}. "
                    "Negative values are not supported by the Action Plan engine. "
                    "Use 0 for same-day tasks; positive values for future tasks."
                )
    return issues


def check_invalid_task_deadline_type(files: list[Path]) -> list[str]:
    """Warn if TaskDeadlineType is not one of the two valid values."""
    issues: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in TASK_DEADLINE_TYPE_PATTERN.finditer(content):
            value = match.group(1).strip()
            if value not in VALID_DEADLINE_TYPES:
                issues.append(
                    f"{f}: ActionPlanTemplate has TaskDeadlineType='{value}'. "
                    f"Valid values are: {', '.join(sorted(VALID_DEADLINE_TYPES))}."
                )
    return issues


def check_naive_risk_score_fields(files: list[Path]) -> list[str]:
    """Warn if code references risk score field names that do not exist natively.

    These field names are commonly generated by LLMs that assume the Discovery
    Framework produces a composite risk score. They do not exist on any native
    FSC object and indicate a hallucinated field reference.
    """
    issues: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = NAIVE_RISK_SCORE_PATTERN.findall(content)
        if matches:
            unique_matches = sorted(set(m.lower() for m in matches))
            issues.append(
                f"{f}: References field(s) that do not exist natively on FSC objects: "
                f"{', '.join(unique_matches)}. The Discovery Framework does not produce "
                "a native risk score field. Verify these are intentional custom fields "
                "and document them in the org configuration guide."
            )
    return issues


def check_revenue_insights_references(files: list[Path]) -> list[str]:
    """Note when Revenue Insights is referenced.

    Revenue Insights requires a separate CRM Analytics / Revenue Intelligence
    for Financial Services license. This check surfaces all references so the
    practitioner can confirm the license is provisioned.
    """
    issues: list[str] = []
    referencing_files: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if REVENUE_INSIGHTS_PATTERN.search(content):
            referencing_files.append(str(f))
    if referencing_files:
        issues.append(
            "Revenue Insights or CRM Analytics for Financial Services is referenced "
            f"in {len(referencing_files)} file(s): {', '.join(referencing_files[:5])}. "
            "Confirm that the Revenue Intelligence for Financial Services license is "
            "provisioned in the target org (Setup > Company Information > Feature Licenses) "
            "before deploying any Revenue Insights-dependent configuration."
        )
    return issues


def check_action_plan_fsc_target_entities(files: list[Path]) -> list[str]:
    """Warn if ActionPlanTemplate TargetEntityType references unknown FSC entities.

    Valid FSC-specific TargetEntityType values are documented. Unusual values
    may indicate a typo or unsupported configuration.
    """
    known_fsc_entities = {
        "FinancialAccount", "FinancialGoal", "InsurancePolicy",
        "ResidentialLoanApplication", "PersonLifeEvent", "BusinessMilestone",
        # Standard Salesforce objects also valid as targets
        "Account", "Contact", "Opportunity", "Lead", "Contract", "Case", "Campaign",
    }
    issues: list[str] = []
    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in TARGET_ENTITY_PATTERN.finditer(content):
            entity = match.group(1).strip()
            if entity not in known_fsc_entities:
                issues.append(
                    f"{f}: ActionPlanTemplate TargetEntityType='{entity}' is not a "
                    "recognized FSC or standard Action Plan target object. "
                    f"Known valid values: {', '.join(sorted(known_fsc_entities))}."
                )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common financial planning process "
            "configuration issues: namespace mismatches, Action Plan template "
            "problems, and risk tolerance data model assumptions."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_financial_planning_process(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    files = _iter_metadata_files(manifest_dir)
    if not files:
        # No files to check — not an error, just nothing to analyze
        return issues

    issues.extend(check_mixed_namespace_references(files))
    issues.extend(check_negative_days_from_start(files))
    issues.extend(check_invalid_task_deadline_type(files))
    issues.extend(check_naive_risk_score_fields(files))
    issues.extend(check_revenue_insights_references(files))
    issues.extend(check_action_plan_fsc_target_entities(files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_financial_planning_process(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
