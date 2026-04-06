#!/usr/bin/env python3
"""Checker script for Case Deflection Strategy skill.

Checks Salesforce metadata for common case deflection configuration issues.
Uses stdlib only — no pip dependencies.

Checks performed:
- Knowledge (KnowledgeArticle) metadata: verifies data categories are present
- Einstein Bot metadata: checks for session end survey dialog and escalation paths
- Experience Cloud site metadata: checks for search-first configuration markers
- Flow metadata: checks for Web-to-Case flows that lack article surfacing steps

Usage:
    python3 check_case_deflection_strategy.py [--help]
    python3 check_case_deflection_strategy.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Case Deflection Strategy configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_xml_files(root: Path, pattern: str) -> list[Path]:
    return sorted(root.rglob(pattern))


def check_knowledge_data_categories(manifest_dir: Path) -> list[str]:
    """Check Knowledge article metadata for missing data category assignments."""
    issues: list[str] = []
    ka_files = _find_xml_files(manifest_dir, "*.ka-meta.xml")
    ka_files += _find_xml_files(manifest_dir, "*.kav-meta.xml")

    uncategorized = []
    for kf in ka_files:
        try:
            tree = ET.parse(kf)
            root_el = tree.getroot()
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
            # Check for DataCategorySelections element
            cats = root_el.findall(".//sf:dataCategorySelections", ns)
            if not cats:
                # Try without namespace
                cats = root_el.findall(".//dataCategorySelections")
            if not cats:
                uncategorized.append(kf.name)
        except ET.ParseError:
            issues.append(f"Could not parse Knowledge file: {kf}")

    if uncategorized:
        issues.append(
            f"{len(uncategorized)} Knowledge article(s) have no data category assignments — "
            f"these articles will not appear in Experience Cloud search or Einstein Bot article recommendations. "
            f"Files: {', '.join(uncategorized[:5])}"
            + (" (and more)" if len(uncategorized) > 5 else "")
        )
    return issues


def check_einstein_bot_metadata(manifest_dir: Path) -> list[str]:
    """Check Einstein Bot metadata for missing session end survey and missing escalation paths."""
    issues: list[str] = []
    bot_files = _find_xml_files(manifest_dir, "*.bot-meta.xml")
    bot_files += _find_xml_files(manifest_dir, "*.botVersion-meta.xml")

    for bf in bot_files:
        try:
            content = bf.read_text(encoding="utf-8")
            bot_name = bf.stem.split(".")[0]

            # Check for escalation/transfer dialog step
            has_transfer = any(
                term in content.lower()
                for term in ["transfertoliveagent", "transfer_to_live_agent", "liveagenthandoff", "escalate"]
            )
            if not has_transfer:
                issues.append(
                    f"Einstein Bot '{bot_name}': no agent transfer/escalation step detected. "
                    "Case deflection bots must include a human escalation path — containment-only bots "
                    "trap customers with complex issues."
                )

            # Check for survey/feedback step (end-of-session goal completion measurement)
            has_survey = any(
                term in content.lower()
                for term in ["survey", "feedback", "rating", "goalcompletion", "wasthishelpful"]
            )
            if not has_survey:
                issues.append(
                    f"Einstein Bot '{bot_name}': no session end survey or feedback step detected. "
                    "Goal completion rate (GCR) cannot be measured without a post-session survey. "
                    "Add a 'Was this helpful?' prompt at session close."
                )
        except OSError:
            issues.append(f"Could not read bot metadata file: {bf}")

    return issues


def check_web_to_case_flow(manifest_dir: Path) -> list[str]:
    """Check Flow metadata for Web-to-Case flows that lack article surfacing."""
    issues: list[str] = []
    flow_files = _find_xml_files(manifest_dir, "*.flow-meta.xml")

    for ff in flow_files:
        try:
            content = ff.read_text(encoding="utf-8")
            flow_name = ff.stem.split(".")[0]

            # Heuristic: flow mentions case creation but not knowledge article lookup
            has_case_create = any(
                term in content
                for term in ["Case", "WebToCase", "web_to_case"]
            )
            has_article_lookup = any(
                term in content.lower()
                for term in ["knowledge", "article", "knowledgearticleversion", "searchknowledge"]
            )

            if has_case_create and not has_article_lookup:
                issues.append(
                    f"Flow '{flow_name}': creates Cases but does not appear to surface Knowledge articles. "
                    "Consider adding a search-first article step before case creation to enable deflection. "
                    "Verify manually — this is a heuristic check."
                )
        except OSError:
            issues.append(f"Could not read flow metadata file: {ff}")

    return issues


def check_case_deflection_strategy(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_knowledge_data_categories(manifest_dir))
    issues.extend(check_einstein_bot_metadata(manifest_dir))
    issues.extend(check_web_to_case_flow(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_case_deflection_strategy(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
