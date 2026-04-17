#!/usr/bin/env python3
"""Checker script for Workflow Rule to Flow Migration skill.

Scans Salesforce metadata in a local project directory for Workflow Rules that:
  - Use unsupported criteria (ISCHANGED, ISNEW, global variables) — cannot be auto-migrated
  - Have time-based actions — need Scheduled Path planning
  - Have task creation actions — require manual Flow construction
  - Are still active (not yet migrated)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_workflow_rule_to_flow_migration.py --help
    python3 check_workflow_rule_to_flow_migration.py --manifest-dir path/to/metadata
    python3 check_workflow_rule_to_flow_migration.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce Metadata API namespace for Workflow metadata
_SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Formula functions that the Migrate to Flow tool cannot translate
_UNSUPPORTED_FORMULA_FUNCTIONS = [
    "ISCHANGED(",
    "ISNEW(",
    "PRIORVALUE(",
]

# Global variable prefixes that the Migrate to Flow tool cannot translate
_GLOBAL_VARIABLE_PREFIXES = [
    "$User.",
    "$Profile.",
    "$Organization.",
    "$UserRole.",
    "$Permission.",
    "$Setup.",
    "$Label.",
    "$ObjectType.",
]

# Action types that the Migrate to Flow tool cannot convert
_UNSUPPORTED_ACTION_TAGS = {
    "tasks",  # Task creation action
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for Workflow Rules that need manual review "
            "before migration to Record-Triggered Flow."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    """Return a namespace-qualified tag name for Salesforce metadata XML."""
    return f"{{{_SF_NS}}}{local}"


def _text(element: ET.Element, local: str, default: str = "") -> str:
    """Return stripped text content of a child element, or default."""
    child = element.find(_tag(local))
    if child is not None and child.text:
        return child.text.strip()
    return default


def check_formula_for_unsupported_functions(formula: str) -> list[str]:
    """Return list of unsupported function/global-variable names found in formula."""
    found = []
    upper = formula.upper()
    for fn in _UNSUPPORTED_FORMULA_FUNCTIONS:
        if fn.upper() in upper:
            found.append(fn.rstrip("("))
    for gv in _GLOBAL_VARIABLE_PREFIXES:
        if gv.upper() in upper:
            found.append(gv.rstrip("."))
    return found


def analyse_workflow_rule(rule_file: Path) -> list[str]:
    """Analyse a single .workflow-meta.xml file and return issue descriptions."""
    issues: list[str] = []
    try:
        tree = ET.parse(rule_file)
    except ET.ParseError as exc:
        issues.append(f"[{rule_file.name}] XML parse error: {exc}")
        return issues

    root = tree.getroot()
    # The root element is <Workflow> containing <rules> children
    # Each <rules> block is a single Workflow Rule
    rules = root.findall(_tag("rules"))
    if not rules:
        # Some files wrap the single rule as the root element directly
        # when deployed as individual files
        rules = [root]

    for rule in rules:
        rule_name = _text(rule, "fullName") or rule_file.stem
        active = _text(rule, "active", "false").lower() == "true"

        if not active:
            # Skip already-inactive rules
            continue

        # --- Criteria checks ---
        criteria_items = rule.findall(_tag("criteriaItems"))
        formula_criteria = _text(rule, "formula")

        if formula_criteria:
            unsupported = check_formula_for_unsupported_functions(formula_criteria)
            if unsupported:
                issues.append(
                    f"[{rule_name}] Active rule uses unsupported formula functions "
                    f"({', '.join(unsupported)}) — Migrate to Flow tool cannot translate these. "
                    f"Manual Flow construction required with 'Changed' operator equivalent."
                )
            else:
                issues.append(
                    f"[{rule_name}] Active rule uses a formula criterion "
                    f"(non-ISCHANGED/ISNEW) — verify the Migrate to Flow tool correctly "
                    f"translates this formula. Review generated Flow entry conditions."
                )

        for ci in criteria_items:
            field = _text(ci, "field")
            value = _text(ci, "value")
            # Check if the criterion field or value contains global variable references
            for gv in _GLOBAL_VARIABLE_PREFIXES:
                if gv.upper() in field.upper() or gv.upper() in value.upper():
                    issues.append(
                        f"[{rule_name}] Active rule criterion references a global variable "
                        f"({gv.rstrip('.')}) in field '{field}' — Migrate to Flow tool "
                        f"cannot translate global variable references. Manual construction required."
                    )

        # --- Action type checks ---
        has_tasks = bool(rule.findall(_tag("tasks")))
        has_time_based = bool(rule.findall(_tag("workflowTimeTriggers")))
        has_field_updates = bool(rule.findall(_tag("actions")))  # actions includes field updates

        if has_tasks:
            issues.append(
                f"[{rule_name}] Active rule has task creation actions — "
                f"the Migrate to Flow tool does not convert tasks. "
                f"Manual Flow construction required using a Create Records element."
            )

        if has_time_based:
            issues.append(
                f"[{rule_name}] Active rule has time-based actions — "
                f"replace with a Scheduled Path on a Record-Triggered Flow. "
                f"Review the Time-Based Workflow queue (Setup → Time-Based Workflow) "
                f"before deactivating this rule to avoid dropping pending actions."
            )

        # --- Cross-object field update detection (heuristic) ---
        field_updates = rule.findall(_tag("fieldUpdates"))
        for fu in field_updates:
            fu_object = _text(fu, "object")
            rule_object = _text(rule, "sobjectType")
            if fu_object and rule_object and fu_object.upper() != rule_object.upper():
                issues.append(
                    f"[{rule_name}] Active rule has a cross-object field update "
                    f"(updates {fu_object} from {rule_object}) — "
                    f"the Migrate to Flow tool cannot convert cross-object updates. "
                    f"Manual Flow construction required with Get Records + Update Records."
                )

    return issues


def find_workflow_files(manifest_dir: Path) -> list[Path]:
    """Return all .workflow-meta.xml files under the manifest directory."""
    return sorted(manifest_dir.rglob("*.workflow-meta.xml"))


def check_workflow_rule_to_flow_migration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    workflow_files = find_workflow_files(manifest_dir)

    if not workflow_files:
        # Not an error — the org may have no Workflow Rules, or metadata was not retrieved
        return issues

    for wf_file in workflow_files:
        issues.extend(analyse_workflow_rule(wf_file))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_workflow_rule_to_flow_migration(manifest_dir)

    if not issues:
        print("No active Workflow Rule migration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(
        f"\n{len(issues)} issue(s) found. Review each rule before running the Migrate to Flow tool.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
