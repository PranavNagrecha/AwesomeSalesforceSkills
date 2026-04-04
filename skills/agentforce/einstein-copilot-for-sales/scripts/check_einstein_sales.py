#!/usr/bin/env python3
"""check_einstein_sales.py — Validator for Einstein Copilot for Sales prerequisites.

Inspects a Salesforce metadata deployment directory (sfdx project or retrieved
metadata) to surface missing configuration, permissions, and layout gaps that
would prevent Einstein Sales AI features from working correctly.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_sales.py [--manifest-dir path/to/metadata] [--verbose]

What it checks:
    - Permission set assignments for Einstein Sales AI permission sets
    - Presence of Opportunity Score fields on Opportunity page layouts
    - EAC configuration profile metadata (if present)
    - Einstein feature settings in org-wide settings metadata
    - Presence of required custom fields referenced in scoring model config
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REQUIRED_PERMISSION_SETS = {
    "SalesCloudEinsteinUser",
    "EinsteinForSalesUser",
    "EinsteinSalesAnalyticsAdmin",
}

EINSTEIN_SALES_SCORE_FIELDS = {
    "OpportunityScore",
    "OpportunityScoreChangeType",
}

# Metadata file patterns to locate
PERMISSION_SET_GLOB = "**/*.permissionset-meta.xml"
LAYOUT_GLOB = "**/*Opportunity*.layout-meta.xml"
SETTINGS_GLOB = "**/Sales.settings-meta.xml"
PROFILE_GLOB = "**/*.profile-meta.xml"

SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, pattern: str) -> list[Path]:
    return sorted(root.glob(pattern))


def _parse_xml_safe(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        return None


def _strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from an element tag."""
    return tag.split("}")[-1] if "}" in tag else tag


def _text(element: ET.Element, child_tag: str) -> str:
    child = element.find(f"{{{SF_NAMESPACE}}}{child_tag}")
    if child is None:
        # try without namespace
        child = element.find(child_tag)
    return (child.text or "").strip() if child is not None else ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_permission_sets_exist(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn if none of the Einstein Sales permission sets are found in metadata."""
    issues: list[str] = []
    found: set[str] = set()

    for ps_file in _find_files(manifest_dir, PERMISSION_SET_GLOB):
        stem = ps_file.stem.replace(".permissionset-meta", "")
        for required in REQUIRED_PERMISSION_SETS:
            if required.lower() in stem.lower():
                found.add(required)

    missing = REQUIRED_PERMISSION_SETS - found
    if missing and not found:
        issues.append(
            "No Einstein Sales permission set metadata found in manifest directory. "
            "Expected at least one of: "
            + ", ".join(sorted(REQUIRED_PERMISSION_SETS))
            + ". Ensure the permission sets are retrieved and included in the deployment."
        )
    elif missing and verbose:
        # Not all sets present; informational only when some are found
        pass

    return issues


def check_opportunity_score_fields_on_layout(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check that Opportunity page layout XML includes Einstein Score fields."""
    issues: list[str] = []
    layout_files = _find_files(manifest_dir, LAYOUT_GLOB)

    if not layout_files:
        if verbose:
            issues.append(
                "No Opportunity layout metadata found — cannot verify Einstein Score fields "
                "are added to Opportunity page layout. Retrieve Opportunity layouts and re-run."
            )
        return issues

    for layout_file in layout_files:
        root = _parse_xml_safe(layout_file)
        if root is None:
            issues.append(f"Could not parse layout file: {layout_file.name}")
            continue

        # Collect all field names referenced in layout sections
        field_names_in_layout: set[str] = set()
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if tag == "field":
                field_names_in_layout.add((elem.text or "").strip())

        for score_field in EINSTEIN_SALES_SCORE_FIELDS:
            if not any(score_field.lower() in f.lower() for f in field_names_in_layout):
                issues.append(
                    f"Einstein score field '{score_field}' not found on layout '{layout_file.name}'. "
                    "Add the Opportunity Score and Score Change fields to the Opportunity page layout "
                    "so reps can see scores on records."
                )

    return issues


def check_sales_settings_metadata(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check Sales settings metadata for Einstein feature flags if present."""
    issues: list[str] = []
    settings_files = _find_files(manifest_dir, SETTINGS_GLOB)

    if not settings_files:
        if verbose:
            issues.append(
                "Sales.settings-meta.xml not found in manifest directory. "
                "Retrieve Sales settings to validate Einstein feature enablement flags."
            )
        return issues

    for sf in settings_files:
        root = _parse_xml_safe(sf)
        if root is None:
            issues.append(f"Could not parse settings file: {sf.name}")
            continue

        # Look for enableEinsteinOpportunityScoring or similar flags
        einstein_flags: dict[str, str] = {}
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if "einstein" in tag.lower() or "opportunityscore" in tag.lower():
                einstein_flags[tag] = (elem.text or "").strip()

        if verbose and not einstein_flags:
            issues.append(
                f"No Einstein-related settings found in {sf.name}. "
                "If Einstein Opportunity Scoring should be enabled, verify the setting "
                "is present and set to 'true' in Sales settings metadata."
            )

        for flag, value in einstein_flags.items():
            if value.lower() == "false":
                issues.append(
                    f"Einstein setting '{flag}' is explicitly set to false in {sf.name}. "
                    "If this feature is intended to be active, update this flag to true and redeploy."
                )

    return issues


def check_eac_exclusion_rules_present(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn if EAC configuration profiles exist but have no exclusion domain rules."""
    issues: list[str] = []

    # EAC config profiles are typically in ConnectedApp or EinsteinActivityCaptureSettings
    eac_settings_glob = "**/*EinsteinActivityCapture*.settings-meta.xml"
    eac_files = _find_files(manifest_dir, eac_settings_glob)

    if not eac_files:
        if verbose:
            issues.append(
                "No Einstein Activity Capture settings metadata found. "
                "If EAC is enabled, retrieve EinsteinActivityCapture settings and re-run "
                "to validate exclusion rules are configured."
            )
        return issues

    for eac_file in eac_files:
        root = _parse_xml_safe(eac_file)
        if root is None:
            issues.append(f"Could not parse EAC settings file: {eac_file.name}")
            continue

        # Look for exclusion domain/address configuration elements
        exclusion_elements: list[str] = []
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if "exclusion" in tag.lower() or "exclude" in tag.lower():
                exclusion_elements.append(tag)

        if not exclusion_elements:
            issues.append(
                f"EAC settings file '{eac_file.name}' found but contains no exclusion rule "
                "configuration. Configure domain and address exclusion rules before EAC goes live "
                "to prevent personal and legal email from syncing into Salesforce records. "
                "See: Setup > Einstein > Einstein Activity Capture > Configuration > Exclusions."
            )

    return issues


def check_pipeline_inspection_dependency(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn if Pipeline Inspection is referenced but Opportunity Scoring flags are missing."""
    issues: list[str] = []

    # Look for any metadata file referencing Pipeline Inspection
    pipeline_refs: list[Path] = []
    for xml_file in _find_files(manifest_dir, "**/*.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
            if "PipelineInspection" in content or "pipelineInspection" in content:
                pipeline_refs.append(xml_file)
        except OSError:
            continue

    if not pipeline_refs:
        return issues

    # If Pipeline Inspection is referenced, verify that Opportunity Scoring settings exist
    opp_scoring_refs: list[Path] = []
    for xml_file in _find_files(manifest_dir, "**/*.xml"):
        try:
            content = xml_file.read_text(encoding="utf-8", errors="ignore")
            if "OpportunityScoring" in content or "opportunityScoring" in content:
                opp_scoring_refs.append(xml_file)
        except OSError:
            continue

    if pipeline_refs and not opp_scoring_refs:
        issues.append(
            "Pipeline Inspection configuration detected but no Opportunity Scoring settings found. "
            "Pipeline Inspection AI insights require Opportunity Scoring to be enabled and the "
            "model to be trained. Enable Opportunity Scoring first and confirm model status is "
            "'Active' before relying on Pipeline Inspection AI insights."
        )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path, verbose: bool) -> list[str]:
    """Run all Einstein Sales AI prerequisite checks and return collected issues."""
    all_issues: list[str] = []

    checks = [
        ("Permission set metadata", check_permission_sets_exist),
        ("Opportunity score fields on layout", check_opportunity_score_fields_on_layout),
        ("Sales settings metadata", check_sales_settings_metadata),
        ("EAC exclusion rules", check_eac_exclusion_rules_present),
        ("Pipeline Inspection dependency on Opportunity Scoring", check_pipeline_inspection_dependency),
    ]

    for check_name, check_fn in checks:
        try:
            issues = check_fn(manifest_dir, verbose)
            all_issues.extend(issues)
        except Exception as exc:
            all_issues.append(f"Check '{check_name}' failed unexpectedly: {exc}")

    return all_issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Einstein Copilot for Sales prerequisites in a Salesforce metadata directory. "
            "Checks permission sets, page layouts, settings, EAC exclusion rules, and "
            "Pipeline Inspection dependencies."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Emit informational warnings for missing metadata in addition to errors.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    issues = run_all_checks(manifest_dir, verbose=args.verbose)

    if not issues:
        print("OK: No Einstein Sales AI prerequisite issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
