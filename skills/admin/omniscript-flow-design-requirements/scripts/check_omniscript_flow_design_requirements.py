#!/usr/bin/env python3
"""Checker script for OmniScript Flow Design Requirements skill.

Validates OmniScript requirements documents for structural completeness:
- Navigate Action documented
- At least one Step element specified
- Data source bindings (Pre-Step and Post-Step) documented
- Conditional View Block groupings present (not field-level conditions)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omniscript_flow_design_requirements.py [--help]
    python3 check_omniscript_flow_design_requirements.py --requirements-file path/to/requirements.md
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check OmniScript requirements document for structural completeness.",
    )
    parser.add_argument(
        "--requirements-file",
        default=None,
        help="Path to the OmniScript requirements markdown file.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_requirements_document(file_path: Path) -> list[str]:
    """Check an OmniScript requirements markdown document for common structural gaps."""
    issues: list[str] = []

    if not file_path.exists():
        issues.append(f"Requirements file not found: {file_path}")
        return issues

    content = file_path.read_text(encoding="utf-8")
    lower = content.lower()

    # Check for Navigate Action documentation
    if "navigate action" not in lower and "navigate_action" not in lower:
        issues.append(
            "MISSING Navigate Action: Requirements document does not mention a Navigate Action. "
            "Every OmniScript requires a Navigate Action to complete. "
            "Document the Navigate Action type and destination."
        )

    # Check for Step documentation
    if not re.search(r"step\s*[1-9]|step #|step inventory", lower):
        issues.append(
            "MISSING Step inventory: No Step elements documented. "
            "At least one Step element is required in every OmniScript."
        )

    # Check for Pre-Step or Post-Step action documentation
    has_pre_post = (
        "pre-step" in lower or "post-step" in lower
        or "pre step" in lower or "post step" in lower
    )
    if not has_pre_post:
        issues.append(
            "MISSING Pre/Post Step timing: Data source actions should specify Pre-Step or Post-Step timing. "
            "Pre-Step loads data before the user sees the screen; Post-Step fires after the user clicks Next."
        )

    # Check for data source documentation
    has_data_source = any(
        term in lower for term in [
            "dataraptor", "integration procedure", "remote action", "data source"
        ]
    )
    if not has_data_source:
        issues.append(
            "MISSING data sources: No DataRaptor, Integration Procedure, or Remote Action documented. "
            "Every OmniScript requires at least two data source bindings."
        )

    # Check for Conditional View / Block notation (branching)
    # If the doc mentions 'if' or 'condition' but lacks conditional view / block notation, warn
    has_conditions = re.search(r"\bif\b|\bwhen\b|\bbranch", lower)
    has_block_notation = (
        "conditional view" in lower or "block" in lower
        or "%fieldname" in lower or "block name" in lower
    )
    if has_conditions and not has_block_notation:
        issues.append(
            "POSSIBLE Screen Flow bleed: Document mentions conditional logic but does not use "
            "OmniScript Conditional View / Block container notation. "
            "OmniScript branching requires Conditional View set on Block containers, "
            "not Decision elements or field-level conditions."
        )

    # Check for external API mentions with DataRaptor (incorrect)
    if re.search(r"dataraptor.*(?:api|http|external|callout|rest|soap)", lower):
        issues.append(
            "INCORRECT data source: Requirements mention DataRaptor for external API calls. "
            "DataRaptors cannot make HTTP callouts. Use an Integration Procedure with an HTTP Action element."
        )

    return issues


def check_metadata_dir(manifest_dir: Path) -> list[str]:
    """Check Salesforce metadata directory for OmniScript-related issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        return issues

    # Look for OmniScript XML metadata files
    omniscript_files = list(manifest_dir.rglob("*.omniscript-meta.xml")) + list(
        manifest_dir.rglob("OmniScript*.xml")
    )

    for sf in omniscript_files:
        content = sf.read_text(encoding="utf-8", errors="ignore")
        # Check for Navigate Action in deployed OmniScripts
        if "NavigateAction" not in content and "navigate_action" not in content.lower():
            issues.append(
                f"{sf.name}: OmniScript metadata does not contain a NavigateAction element. "
                "Activation will fail without a Navigate Action."
            )

    return issues


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    if args.requirements_file:
        req_file = Path(args.requirements_file)
        issues.extend(check_requirements_document(req_file))

    manifest_dir = Path(args.manifest_dir)
    issues.extend(check_metadata_dir(manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
