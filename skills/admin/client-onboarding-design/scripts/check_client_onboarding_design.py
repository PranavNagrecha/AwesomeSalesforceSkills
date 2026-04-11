#!/usr/bin/env python3
"""Checker script for Client Onboarding Design skill.

Validates FSC onboarding metadata artifacts for common process design issues:
- Action Plan template task count approaching or exceeding the 75-task limit
- Published Action Plan templates that appear to have been cloned but lack
  a version indicator in their name (versioning governance issue)
- Flows or Action Plans referencing OmniStudio component names (indicates
  OmniStudio dependency that may require license confirmation)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_client_onboarding_design.py [--help]
    python3 check_client_onboarding_design.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ACTION_PLAN_TASK_LIMIT = 75
ACTION_PLAN_TASK_WARNING_THRESHOLD = 60

OMNISTUDIO_MARKERS = [
    "OmniScript",
    "FlexCard",
    "DataRaptor",
    "OmniProcess",
    "OmniInteraction",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC client onboarding design artifacts for common process "
            "design issues: Action Plan task limits, versioning governance, "
            "and OmniStudio license dependencies."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file, returning None on error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def check_action_plan_templates(manifest_dir: Path) -> list[str]:
    """Check ActionPlanTemplate metadata for task count and versioning issues."""
    issues: list[str] = []

    # ActionPlanTemplate metadata lives in force-app/.../actionPlanTemplates/
    # or a similar path depending on project structure; search broadly.
    template_dirs = list(manifest_dir.rglob("actionPlanTemplates"))
    template_files: list[Path] = []
    for d in template_dirs:
        template_files.extend(d.glob("*.actionPlanTemplate"))

    if not template_files:
        # No Action Plan template metadata found — not necessarily an error
        # (the skill may be used before metadata is deployed)
        return issues

    for template_path in template_files:
        root = _parse_xml_safe(template_path)
        if root is None:
            issues.append(
                f"Could not parse Action Plan template file: {template_path.name}"
            )
            continue

        # Count task items
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        items = root.findall(".//sf:actionPlanTemplateItems", ns) or root.findall(
            ".//actionPlanTemplateItems"
        )
        task_count = len(items)

        template_name = template_path.stem

        if task_count >= ACTION_PLAN_TASK_LIMIT:
            issues.append(
                f"Action Plan template '{template_name}' has {task_count} tasks — "
                f"this meets or exceeds the 75-task hard platform limit. "
                f"Split into phased templates to avoid plan launch failures."
            )
        elif task_count >= ACTION_PLAN_TASK_WARNING_THRESHOLD:
            issues.append(
                f"Action Plan template '{template_name}' has {task_count} tasks — "
                f"approaching the 75-task hard limit. "
                f"Review whether a phased template split is needed."
            )

        # Check for version indicator in template name
        # Convention: name should contain 'v' followed by a digit (e.g., "v1", "v2")
        import re

        if task_count > 0 and not re.search(r"[vV]\d", template_name):
            issues.append(
                f"Action Plan template '{template_name}' does not appear to include "
                f"a version indicator (e.g., 'v1', 'v2') in its name. "
                f"Versioning governance requires a named version so teams can identify "
                f"the current active version and trace the clone history."
            )

    return issues


def check_flows_for_omnistudio_dependencies(manifest_dir: Path) -> list[str]:
    """Scan Flow metadata for references to OmniStudio component names."""
    issues: list[str] = []

    flow_dirs = list(manifest_dir.rglob("flows"))
    flow_files: list[Path] = []
    for d in flow_dirs:
        flow_files.extend(d.glob("*.flow-meta.xml"))

    for flow_path in flow_files:
        try:
            content = flow_path.read_text(encoding="utf-8")
        except OSError:
            continue

        found_markers = [m for m in OMNISTUDIO_MARKERS if m in content]
        if found_markers:
            issues.append(
                f"Flow '{flow_path.stem}' references OmniStudio component(s): "
                f"{', '.join(found_markers)}. "
                f"Confirm OmniStudio is licensed in the target org before deploying. "
                f"If OmniStudio is not licensed, redesign the intake as a Screen Flow."
            )

    return issues


def check_client_onboarding_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_action_plan_templates(manifest_dir))
    issues.extend(check_flows_for_omnistudio_dependencies(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_client_onboarding_design(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
