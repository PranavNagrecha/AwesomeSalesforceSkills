#!/usr/bin/env python3
"""Checker script for Salesforce DevOps Tooling Selection skill.

Validates that a tooling-selection decision document or comparison matrix
covers the required evaluation axes and does not contain common mistakes.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_salesforce_devops_tooling_selection.py --doc path/to/decision-doc.md
    python3 check_salesforce_devops_tooling_selection.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_AXES = [
    "hosting model",
    "team composition",
    "compliance",
    "budget",
]

KNOWN_TOOLS = [
    "gearset",
    "copado",
    "flosum",
    "autorabit",
    "blue canvas",
    "devops center",
]

SAAS_TOOLS = {"gearset", "autorabit", "blue canvas"}
NATIVE_TOOLS = {"copado", "flosum", "devops center"}

COMPLIANCE_KEYWORDS = ["soc 2", "soc2", "fedramp", "hipaa", "data residency", "gdpr"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a DevOps tooling selection document for completeness and common mistakes.",
    )
    parser.add_argument(
        "--doc",
        default=None,
        help="Path to a tooling selection decision document (Markdown).",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_decision_document(doc_path: Path) -> list[str]:
    """Validate a tooling-selection decision document for completeness."""
    issues: list[str] = []

    if not doc_path.exists():
        issues.append(f"Decision document not found: {doc_path}")
        return issues

    content = doc_path.read_text(encoding="utf-8").lower()

    # Check that required evaluation axes are mentioned
    for axis in REQUIRED_AXES:
        if axis not in content:
            issues.append(
                f"Missing evaluation axis: '{axis}'. "
                f"A complete tooling selection must address {axis}."
            )

    # Check that at least 2 tools are compared
    mentioned_tools = [t for t in KNOWN_TOOLS if t in content]
    if len(mentioned_tools) < 2:
        issues.append(
            f"Only {len(mentioned_tools)} tool(s) mentioned ({', '.join(mentioned_tools) or 'none'}). "
            f"A valid comparison requires at least 2 tools."
        )

    # Check for compliance discussion if compliance keywords appear
    has_compliance_mention = any(kw in content for kw in COMPLIANCE_KEYWORDS)
    if has_compliance_mention:
        saas_mentioned = [t for t in SAAS_TOOLS if t in content]
        hosting_discussed = "hosting" in content or "saas" in content or "native" in content
        if saas_mentioned and not hosting_discussed:
            issues.append(
                f"Compliance keywords found alongside SaaS tools ({', '.join(saas_mentioned)}) "
                f"but hosting model implications are not discussed. "
                f"SaaS tools route metadata externally — this must be addressed for regulated orgs."
            )

    # Check for specific pricing claims (potential staleness)
    price_pattern = re.compile(r"\$\d+[\d,]*(?:\.\d{2})?\s*(?:/|per)\s*(?:user|month|org)", re.IGNORECASE)
    price_matches = price_pattern.findall(content)
    if price_matches:
        issues.append(
            f"Specific pricing found: {', '.join(price_matches[:3])}. "
            f"Tool pricing changes frequently — consider replacing with ranges or 'contact vendor'."
        )

    # Check for proof-of-concept or evaluation mention
    poc_keywords = ["proof of concept", "proof-of-concept", "poc", "evaluation", "pilot", "trial"]
    if not any(kw in content for kw in poc_keywords):
        issues.append(
            "No proof-of-concept or evaluation step mentioned. "
            "Tool selection without hands-on evaluation leads to post-purchase regret."
        )

    return issues


def check_manifest_for_tooling_signals(manifest_dir: Path) -> list[str]:
    """Check metadata directory for signals of existing DevOps tooling."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check for Copado managed package presence
    copado_indicators = list(manifest_dir.rglob("*copado*"))
    if copado_indicators:
        issues.append(
            f"Found {len(copado_indicators)} Copado-related metadata file(s). "
            f"An existing Copado installation is present — factor migration cost into any tool-switch decision."
        )

    # Check for Flosum managed package presence
    flosum_indicators = list(manifest_dir.rglob("*flosum*"))
    if flosum_indicators:
        issues.append(
            f"Found {len(flosum_indicators)} Flosum-related metadata file(s). "
            f"An existing Flosum installation is present — factor migration cost into any tool-switch decision."
        )

    # Check for AutoRABIT indicators
    autorabit_indicators = list(manifest_dir.rglob("*autorabit*")) + list(manifest_dir.rglob("*codescan*"))
    if autorabit_indicators:
        issues.append(
            f"Found {len(autorabit_indicators)} AutoRABIT/CodeScan-related metadata file(s). "
            f"An existing AutoRABIT installation is present — factor migration cost into any tool-switch decision."
        )

    return issues


def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.doc:
        doc_path = Path(args.doc)
        all_issues.extend(check_decision_document(doc_path))

    manifest_dir = Path(args.manifest_dir)
    if manifest_dir.exists():
        all_issues.extend(check_manifest_for_tooling_signals(manifest_dir))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
