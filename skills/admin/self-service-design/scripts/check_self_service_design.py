#!/usr/bin/env python3
"""Checker script for Self-Service Design skill.

Audits a Salesforce metadata directory for self-service portal design
issues: missing Case Deflection component, case forms with no pre-deflection
article surfacing, and Knowledge article channel assignment gaps.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_self_service_design.py [--manifest-dir path/to/metadata]
    python3 check_self_service_design.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common self-service portal design issues: "
            "missing Case Deflection component, case submission flows without "
            "pre-deflection article surfacing, and Knowledge article channel gaps."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iter_xml_files(root: Path, suffix: str) -> list[Path]:
    """Return all files under root with the given suffix."""
    return list(root.rglob(f"*{suffix}"))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file, returning None on parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_case_deflection_component(manifest_dir: Path) -> list[str]:
    """Warn if no Experience Cloud page uses the CaseDeflection component."""
    issues: list[str] = []

    # Experience Cloud pages live in *.page-meta.xml or in digitalExperiences/
    # We look for "CaseDeflection" in any XML metadata file under the manifest.
    found = False
    xml_files = iter_xml_files(manifest_dir, ".xml")
    for xml_path in xml_files:
        try:
            content = xml_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "CaseDeflection" in content or "caseDeflection" in content:
            found = True
            break

    if not found and xml_files:
        issues.append(
            "No CaseDeflection component found in any metadata file. "
            "Add the Case Deflection component to the Experience Cloud Help Center page "
            "to measure self-service deflection rate. "
            "Reference: Deflect Cases with Self-Service — help.salesforce.com"
        )

    return issues


def check_case_creation_article_suggestions(manifest_dir: Path) -> list[str]:
    """Warn if CaseCreation components are found but article suggestions appear disabled."""
    issues: list[str] = []

    xml_files = iter_xml_files(manifest_dir, ".xml")
    case_creation_files: list[Path] = []
    for xml_path in xml_files:
        try:
            content = xml_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "CaseCreation" in content or "caseCreation" in content:
            case_creation_files.append(xml_path)

    for path in case_creation_files:
        root = parse_xml_safe(path)
        if root is None:
            continue
        xml_str = path.read_text(encoding="utf-8", errors="replace")
        # Look for patterns that suggest article suggestions are explicitly disabled.
        # The Case Creation component uses showKnowledgeSuggestions or similar flags.
        if (
            "showKnowledgeSuggestions" in xml_str
            and "false" in xml_str
        ):
            issues.append(
                f"{path}: CaseCreation component may have Knowledge article suggestions "
                "disabled (showKnowledgeSuggestions=false). Pre-deflection article "
                "surfacing requires this feature to be enabled. "
                "Reference: Deflect Cases with Self-Service — help.salesforce.com"
            )

    return issues


def check_knowledge_article_channel_assignment(manifest_dir: Path) -> list[str]:
    """Warn if Knowledge article type metadata lacks channel assignments."""
    issues: list[str] = []

    # KnowledgeArticleType metadata is in objects/ as *.object-meta.xml
    # Channel assignments appear in channelDisplayType or channelVisibility elements.
    object_files = iter_xml_files(manifest_dir, ".object-meta.xml")
    ka_files = [f for f in object_files if "Knowledge" in f.name or "Article" in f.name]

    for path in ka_files:
        root = parse_xml_safe(path)
        if root is None:
            continue
        xml_str = path.read_text(encoding="utf-8", errors="replace")

        has_channel = (
            "channelDisplayType" in xml_str
            or "channelVisibilities" in xml_str
            or "CustomerCommunity" in xml_str
            or "PublicKnowledgeBase" in xml_str
            or "PartnerCommunity" in xml_str
        )
        if not has_channel:
            issues.append(
                f"{path}: Knowledge object metadata does not include visible "
                "channel assignments (CustomerCommunity, PublicKnowledgeBase, or "
                "PartnerCommunity). Articles not assigned to the correct channel will "
                "not appear in Experience Cloud portal search results. "
                "Reference: Provide a Self-Service Help Center — Salesforce Help"
            )

    return issues


def check_experience_cloud_search_prominence(manifest_dir: Path) -> list[str]:
    """Warn if Experience Cloud pages exist but no search component is found on the landing page."""
    issues: list[str] = []

    # digitalExperiences pages are stored as JSON in digitalExperiences/ directories.
    json_files = list(manifest_dir.rglob("*.json"))
    experience_pages = [
        f for f in json_files
        if "digitalExperience" in str(f) or "experiences" in str(f).lower()
    ]

    if not experience_pages:
        return issues  # No Experience Cloud metadata present; skip check.

    # Look for a search component on any page that is likely the landing page.
    landing_page_candidates = [
        f for f in experience_pages
        if any(keyword in f.name.lower() for keyword in ["home", "landing", "index", "search"])
    ]

    search_found_on_landing = False
    for path in landing_page_candidates:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "Search" in content or "search" in content:
            search_found_on_landing = True
            break

    if landing_page_candidates and not search_found_on_landing:
        issues.append(
            "Experience Cloud landing page candidates found but no search component detected "
            "on likely landing pages. Self-service design best practice requires a prominent "
            "search bar as the primary above-the-fold element on the Help Center landing page. "
            "Reference: Deflect Cases with Self-Service — help.salesforce.com"
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_self_service_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_case_deflection_component(manifest_dir))
    issues.extend(check_case_creation_article_suggestions(manifest_dir))
    issues.extend(check_knowledge_article_channel_assignment(manifest_dir))
    issues.extend(check_experience_cloud_search_prominence(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_self_service_design(manifest_dir)

    if not issues:
        print("No self-service design issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
