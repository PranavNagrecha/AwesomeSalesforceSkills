#!/usr/bin/env python3
"""Checker script for FSC Action Plans skill.

Validates Salesforce metadata related to FSC Action Plans:
- Detects ActionPlanTemplate XML with suspicious item counts (near the 75-task limit)
- Warns if TaskDeadlineType is missing or set to an unexpected value
- Warns if TargetEntityType is missing (required for FSC object templates)
- Detects template names that lack a version suffix (versioning convention check)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_action_plans.py [--help]
    python3 check_fsc_action_plans.py --manifest-dir path/to/force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce hard limit for ActionPlanItem records per plan
ACTION_PLAN_ITEM_LIMIT = 75

# Warning threshold — flag templates approaching the limit
ACTION_PLAN_ITEM_WARN_THRESHOLD = 65

# FSC-specific TargetEntityType values that indicate FSC dependency
FSC_TARGET_ENTITY_TYPES = {
    "FinancialAccount",
    "FinancialGoal",
    "InsurancePolicy",
    "ResidentialLoanApplication",
    "PersonLifeEvent",
    "BusinessMilestone",
}

# Valid TaskDeadlineType values
VALID_DEADLINE_TYPES = {"Calendar", "BusinessDays"}

# Version suffix pattern — templates should include v1, v2, etc.
import re
VERSION_PATTERN = re.compile(r"v\d+", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC Action Plan template metadata for common configuration issues. "
            "Pass the root of a Salesforce metadata directory (e.g., force-app/main/default)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_action_plan_template_files(manifest_dir: Path) -> list[Path]:
    """Return all .actionPlanTemplate-meta.xml files under manifest_dir."""
    return list(manifest_dir.rglob("*.actionPlanTemplate-meta.xml"))


def check_template_file(template_path: Path) -> list[str]:
    """Run all checks on a single ActionPlanTemplate metadata file.

    Returns a list of issue strings. Each issue is human-readable and actionable.
    """
    issues: list[str] = []
    filename = template_path.name

    try:
        tree = ET.parse(template_path)
    except ET.ParseError as exc:
        issues.append(f"{filename}: XML parse error — {exc}")
        return issues

    root = tree.getroot()

    # Strip namespace prefix if present (Salesforce XML uses xmlns)
    def tag(name: str) -> str:
        # ElementTree represents namespaced tags as {namespace}localname
        for child in root.iter():
            local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if local == name:
                return child.tag
        return name

    def find_text(element_name: str) -> str | None:
        """Find first matching element text, namespace-aware."""
        for child in root.iter():
            local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if local == element_name:
                return (child.text or "").strip()
        return None

    def find_all(element_name: str) -> list[ET.Element]:
        """Find all matching elements, namespace-aware."""
        results = []
        for child in root.iter():
            local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if local == element_name:
                results.append(child)
        return results

    # --- Check 1: TargetEntityType presence ---
    target_entity_type = find_text("targetEntityType")
    if not target_entity_type:
        issues.append(
            f"{filename}: Missing <targetEntityType> — "
            "templates must specify a target object (e.g., FinancialAccount, Account)."
        )
    elif target_entity_type in FSC_TARGET_ENTITY_TYPES:
        # FSC object — emit an informational note (not a hard error)
        pass  # Valid FSC target; no issue

    # --- Check 2: TaskDeadlineType presence and validity ---
    deadline_type = find_text("taskDeadlineType")
    if not deadline_type:
        issues.append(
            f"{filename}: Missing <taskDeadlineType> — "
            "set to 'Calendar' or 'BusinessDays'. Note: BusinessDays skips weekends only, not org holidays."
        )
    elif deadline_type not in VALID_DEADLINE_TYPES:
        issues.append(
            f"{filename}: Unexpected <taskDeadlineType> value '{deadline_type}'. "
            f"Valid values: {sorted(VALID_DEADLINE_TYPES)}."
        )

    # --- Check 3: Template item count vs. 75-task limit ---
    items = find_all("actionPlanTemplateItem")
    item_count = len(items)
    if item_count > ACTION_PLAN_ITEM_LIMIT:
        issues.append(
            f"{filename}: Template has {item_count} items, which EXCEEDS the "
            f"Salesforce hard limit of {ACTION_PLAN_ITEM_LIMIT} tasks per Action Plan. "
            "Plan launches from this template will fail. Split into sequenced phase templates."
        )
    elif item_count >= ACTION_PLAN_ITEM_WARN_THRESHOLD:
        issues.append(
            f"{filename}: Template has {item_count} items — approaching the "
            f"{ACTION_PLAN_ITEM_LIMIT}-task hard limit. "
            "Consider splitting into phase templates before adding more tasks."
        )

    # --- Check 4: Each item must have a non-negative DaysFromStart ---
    for item in items:
        subject_el = None
        days_el = None
        for child in item:
            local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if local == "subject":
                subject_el = child
            elif local == "daysFromStart":
                days_el = child

        subject = (subject_el.text or "").strip() if subject_el is not None else "(unknown)"
        if days_el is None:
            issues.append(
                f"{filename}: Item '{subject}' is missing <daysFromStart>. "
                "All template items require a non-negative integer offset from plan start date."
            )
        else:
            try:
                days = int((days_el.text or "").strip())
                if days < 0:
                    issues.append(
                        f"{filename}: Item '{subject}' has negative <daysFromStart> ({days}). "
                        "Negative offsets are not supported — use 0 for same-day tasks."
                    )
            except ValueError:
                issues.append(
                    f"{filename}: Item '{subject}' has non-integer <daysFromStart> value "
                    f"'{days_el.text}'. Must be a non-negative integer."
                )

    # --- Check 5: Template name versioning convention ---
    template_name = find_text("name") or filename
    if not VERSION_PATTERN.search(template_name):
        issues.append(
            f"{filename}: Template name '{template_name}' does not include a version suffix "
            "(e.g., 'v1', 'v2'). The recommended convention is '[Use Case] v[N]' to support "
            "the clone-and-republish versioning workflow."
        )

    return issues


def check_fsc_action_plans(manifest_dir: Path) -> list[str]:
    """Run all FSC Action Plan checks against the metadata directory.

    Returns a list of issue strings found across all template files.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    template_files = find_action_plan_template_files(manifest_dir)

    if not template_files:
        # Not necessarily an error — just informational
        issues.append(
            "No .actionPlanTemplate-meta.xml files found under the manifest directory. "
            "If this org uses Action Plans, ensure the metadata has been retrieved."
        )
        return issues

    for template_path in sorted(template_files):
        file_issues = check_template_file(template_path)
        issues.extend(file_issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsc_action_plans(manifest_dir)

    if not issues:
        print("No FSC Action Plan issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
