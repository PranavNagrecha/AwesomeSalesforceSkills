#!/usr/bin/env python3
"""Checker script for Agentforce Service AI Setup skill.

Inspects Salesforce metadata retrieved via sfdx/sf CLI project structure
to identify common Einstein for Service setup issues: missing permission sets,
missing Lightning components on case record pages, and incomplete feature
prerequisite configurations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agentforce_service_ai_setup.py [--help]
    python3 check_agentforce_service_ai_setup.py --manifest-dir path/to/metadata
    python3 check_agentforce_service_ai_setup.py --manifest-dir . --verbose
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Permission set API names that indicate Einstein for Service access
EINSTEIN_SERVICE_PERMISSION_SETS = {
    "ServiceCloudEinstein",
    "EinsteinForService",
    "EinsteinAgent",
}

# Lightning component API names expected on Case record pages
# for Einstein for Service features to be visible to agents
EINSTEIN_SERVICE_COMPONENTS = {
    "EinsteinCaseClassification",
    "ArticleRecommendations",
    "EinsteinArticleRecommendations",
    "SuggestedReplies",
    "EinsteinSuggestedReplies",
}

# Salesforce XML namespaces commonly found in metadata files
SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_xml_files(directory: Path, pattern: str) -> list[Path]:
    """Return all XML files matching a glob pattern under directory."""
    return sorted(directory.rglob(pattern))


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def _strip_ns(tag: str) -> str:
    """Remove XML namespace from a tag string."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _get_text(element: ET.Element, tag: str) -> str:
    """Return the text content of the first child element with the given tag."""
    child = element.find(f".//{{{SF_NAMESPACE}}}{tag}")
    if child is not None and child.text:
        return child.text.strip()
    # Try without namespace
    child = element.find(f".//{tag}")
    if child is not None and child.text:
        return child.text.strip()
    return ""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_permission_set_assignments(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Check whether Einstein for Service permission set definitions exist.

    Looks for PermissionSet metadata files. Warns if none of the expected
    Einstein for Service permission sets are found — this is a signal that
    agents may not have access to Einstein features.
    """
    issues: list[str] = []
    ps_dir = manifest_dir / "force-app" / "main" / "default" / "permissionsets"
    if not ps_dir.exists():
        # Try alternative SFDX layout
        ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        if verbose:
            print(f"INFO: No permissionsets directory found at {ps_dir}. Skipping permission set checks.")
        return issues

    found_ps_names: set[str] = set()
    for ps_file in _find_xml_files(ps_dir, "*.permissionset-meta.xml"):
        name = ps_file.stem.replace(".permissionset-meta", "")
        found_ps_names.add(name)

    overlap = found_ps_names & EINSTEIN_SERVICE_PERMISSION_SETS
    if not overlap:
        issues.append(
            "No Einstein for Service permission sets found in permissionsets/ directory. "
            f"Expected one of: {sorted(EINSTEIN_SERVICE_PERMISSION_SETS)}. "
            "Agents will not see Einstein features without a Service Cloud Einstein or "
            "Einstein for Service permission set assigned."
        )
    elif verbose:
        print(f"INFO: Found Einstein permission sets: {sorted(overlap)}")

    return issues


def check_case_page_layouts_for_einstein_components(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Check Lightning record pages for Case object for Einstein component placement.

    Scans FlexiPage metadata for case-related pages and checks whether
    Einstein for Service components are present on the layout.
    """
    issues: list[str] = []

    # SFDX standard layout
    flexipage_dir = manifest_dir / "force-app" / "main" / "default" / "flexipages"
    if not flexipage_dir.exists():
        flexipage_dir = manifest_dir / "flexipages"
    if not flexipage_dir.exists():
        if verbose:
            print("INFO: No flexipages directory found. Skipping Lightning component checks.")
        return issues

    case_pages: list[Path] = []
    for fp_file in _find_xml_files(flexipage_dir, "*.flexipage-meta.xml"):
        name_lower = fp_file.name.lower()
        if "case" in name_lower:
            case_pages.append(fp_file)

    if not case_pages:
        if verbose:
            print("INFO: No case-related FlexiPage files found. Skipping Einstein component placement checks.")
        return issues

    for page_path in case_pages:
        root = _parse_xml_safe(page_path)
        if root is None:
            issues.append(f"Could not parse FlexiPage XML: {page_path}")
            continue

        # Collect all component names referenced on this page
        component_names: set[str] = set()
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if tag == "componentName" and elem.text:
                # Component names are prefixed, e.g. "runtime_service_einstein:caseClassification"
                short_name = elem.text.strip().split(":")[-1]
                component_names.add(short_name)
                component_names.add(elem.text.strip())

        found_einstein = component_names & EINSTEIN_SERVICE_COMPONENTS
        if not found_einstein:
            issues.append(
                f"Case page '{page_path.name}' does not contain any Einstein for Service "
                f"Lightning components. Expected one or more of: "
                f"{sorted(EINSTEIN_SERVICE_COMPONENTS)}. "
                "Agents will not see classification suggestions or article recommendations "
                "even if Einstein features are enabled in Setup."
            )
        elif verbose:
            print(f"INFO: Found Einstein components on {page_path.name}: {sorted(found_einstein)}")

    return issues


def check_for_auto_populate_mode(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Warn if any EinsteinClassificationApp metadata sets autoPopulate to true.

    Auto-populate mode propagates incorrect classifications silently.
    Suggestion mode is safer for initial deployments.
    """
    issues: list[str] = []

    # Einstein Classification App metadata is stored in aiApplications/ or similar
    # Scan any XML files for autoPopulate elements
    for xml_file in manifest_dir.rglob("*.xml"):
        root = _parse_xml_safe(xml_file)
        if root is None:
            continue
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if tag == "autoPopulate" and elem.text and elem.text.strip().lower() == "true":
                issues.append(
                    f"autoPopulate=true found in {xml_file.name}. "
                    "Auto-populate mode propagates Case Classification errors silently — "
                    "agents may not notice incorrect field values. Consider 'suggestion' mode "
                    "for initial deployments until model accuracy is validated above 85%."
                )

    if verbose and not issues:
        print("INFO: No autoPopulate=true configuration found. Suggestion mode assumed.")

    return issues


def check_knowledge_settings(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Check whether Salesforce Knowledge is referenced in org settings.

    Article Recommendations and Service Replies require Knowledge to be
    enabled and articles to be published.
    """
    issues: list[str] = []

    settings_dir = manifest_dir / "force-app" / "main" / "default" / "settings"
    if not settings_dir.exists():
        settings_dir = manifest_dir / "settings"
    if not settings_dir.exists():
        if verbose:
            print("INFO: No settings directory found. Skipping Knowledge settings check.")
        return issues

    knowledge_settings_file = settings_dir / "Knowledge.settings-meta.xml"
    if not knowledge_settings_file.exists():
        issues.append(
            "Knowledge.settings-meta.xml not found in settings/. "
            "Salesforce Knowledge must be enabled for Einstein Article Recommendations "
            "and Service Replies to function. Verify Knowledge is enabled in Setup > "
            "Knowledge Settings."
        )
    else:
        root = _parse_xml_safe(knowledge_settings_file)
        if root is not None:
            enabled_text = _get_text(root, "enableKnowledge")
            if enabled_text.lower() == "false":
                issues.append(
                    "Knowledge.settings-meta.xml has enableKnowledge=false. "
                    "Article Recommendations and Service Replies require Knowledge "
                    "to be enabled with published articles."
                )
            elif verbose:
                print("INFO: Knowledge appears to be enabled in settings.")

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_agentforce_service_ai_setup(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Run all checks and return a consolidated list of issues."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_permission_set_assignments(manifest_dir, verbose=verbose))
    issues.extend(check_case_page_layouts_for_einstein_components(manifest_dir, verbose=verbose))
    issues.extend(check_for_auto_populate_mode(manifest_dir, verbose=verbose))
    issues.extend(check_knowledge_settings(manifest_dir, verbose=verbose))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce org metadata for common Einstein for Service AI setup issues: "
            "missing permission sets, missing Lightning components on Case record pages, "
            "auto-populate mode risks, and Knowledge configuration."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce SFDX project or metadata (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Print informational messages in addition to warnings.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_agentforce_service_ai_setup(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No Einstein for Service setup issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
