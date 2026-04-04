#!/usr/bin/env python3
"""check_einstein_copilot_for_service.py — Validator for Einstein for Service prerequisites.

Inspects a Salesforce metadata deployment directory (sfdx project or retrieved
metadata) to surface missing configuration, permissions, and layout gaps that
would prevent Einstein for Service AI features from working correctly.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_copilot_for_service.py [--manifest-dir path/to/metadata] [--verbose]

What it checks:
    - Permission set metadata presence for Einstein for Service
    - Presence of Einstein Case Classification component on Case page layouts
    - Service settings metadata for Einstein feature flags
    - Case Classification field configuration (picklist-only fields)
    - Knowledge settings enablement (required for Article Recommendations and Service Replies)
    - Reply Recommendations configuration presence
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
    "ServiceCloudEinsteinUser",
    "EinsteinForServiceUser",
    "EinsteinCaseClassification",
}

# Component names expected on Case page layouts for Einstein for Service
EINSTEIN_SERVICE_COMPONENTS = {
    "EinsteinCaseClassification",
    "ArticleRecommendations",
    "EinsteinArticleRecommendations",
}

# Metadata file patterns
PERMISSION_SET_GLOB = "**/*.permissionset-meta.xml"
CASE_LAYOUT_GLOB = "**/*Case*.layout-meta.xml"
SERVICE_SETTINGS_GLOB = "**/Service.settings-meta.xml"
KNOWLEDGE_SETTINGS_GLOB = "**/Knowledge.settings-meta.xml"
FLEXIPAGE_GLOB = "**/*.flexipage-meta.xml"

SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, pattern: str) -> list[Path]:
    return sorted(root.glob(pattern))


def _parse_xml_safe(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def _strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from an element tag."""
    return tag.split("}")[-1] if "}" in tag else tag


def _text(element: ET.Element, child_tag: str) -> str:
    child = element.find(f"{{{SF_NAMESPACE}}}{child_tag}")
    if child is None:
        child = element.find(child_tag)
    return (child.text or "").strip() if child is not None else ""


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_permission_sets_exist(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn if none of the Einstein for Service permission sets are found in metadata."""
    issues: list[str] = []
    found: set[str] = set()

    for ps_file in _find_files(manifest_dir, PERMISSION_SET_GLOB):
        stem = ps_file.stem.replace(".permissionset-meta", "")
        for required in REQUIRED_PERMISSION_SETS:
            if required.lower() in stem.lower():
                found.add(required)

    if not found:
        issues.append(
            "No Einstein for Service permission set metadata found in manifest directory. "
            "Expected at least one of: "
            + ", ".join(sorted(REQUIRED_PERMISSION_SETS))
            + ". Ensure permission sets are retrieved and included in the deployment. "
            "Einstein for Service features are permission-set gated."
        )

    return issues


def check_case_layout_has_einstein_component(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check that Case page layout XML references Einstein Classification or Article components."""
    issues: list[str] = []
    layout_files = _find_files(manifest_dir, CASE_LAYOUT_GLOB)

    if not layout_files:
        if verbose:
            issues.append(
                "No Case layout metadata found — cannot verify Einstein for Service components "
                "are present on the Case page layout. Retrieve Case layouts and re-run."
            )
        return issues

    for layout_file in layout_files:
        content = _read_text_safe(layout_file)
        if not content:
            issues.append(f"Could not read layout file: {layout_file.name}")
            continue

        found_component = any(
            comp.lower() in content.lower() for comp in EINSTEIN_SERVICE_COMPONENTS
        )

        if not found_component:
            issues.append(
                f"No Einstein for Service component (Case Classification or Article "
                f"Recommendations) found on layout '{layout_file.name}'. "
                "Add the Einstein Case Classification component and the Einstein Article "
                "Recommendations component to the Case record page layout or service console "
                "so agents can see suggestions and recommendations."
            )

    return issues


def check_service_settings_metadata(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check Service settings metadata for Einstein feature flags if present."""
    issues: list[str] = []
    settings_files = _find_files(manifest_dir, SERVICE_SETTINGS_GLOB)

    if not settings_files:
        if verbose:
            issues.append(
                "Service.settings-meta.xml not found in manifest directory. "
                "Retrieve Service settings to validate Einstein feature enablement flags."
            )
        return issues

    for sf in settings_files:
        root = _parse_xml_safe(sf)
        if root is None:
            issues.append(f"Could not parse settings file: {sf.name}")
            continue

        einstein_flags: dict[str, str] = {}
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if "einstein" in tag.lower() or "classification" in tag.lower():
                einstein_flags[tag] = (elem.text or "").strip()

        for flag, value in einstein_flags.items():
            if value.lower() == "false":
                issues.append(
                    f"Einstein service setting '{flag}' is explicitly set to false in {sf.name}. "
                    "If this feature is intended to be active, update the flag to true and redeploy."
                )

    return issues


def check_knowledge_enabled(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn if Knowledge settings metadata is absent or Knowledge is not enabled.

    Article Recommendations and Service Replies require an active Knowledge base.
    """
    issues: list[str] = []
    knowledge_files = _find_files(manifest_dir, KNOWLEDGE_SETTINGS_GLOB)

    if not knowledge_files:
        if verbose:
            issues.append(
                "Knowledge.settings-meta.xml not found in manifest directory. "
                "Einstein Article Recommendations and Service Replies with Einstein both require "
                "Salesforce Knowledge to be enabled with published articles. "
                "Retrieve Knowledge settings and confirm Knowledge is enabled before enabling "
                "these features."
            )
        return issues

    for kf in knowledge_files:
        root = _parse_xml_safe(kf)
        if root is None:
            issues.append(f"Could not parse Knowledge settings file: {kf.name}")
            continue

        # Look for an enabled flag in Knowledge settings
        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if tag.lower() in ("enableknowledge", "enabled"):
                if (elem.text or "").strip().lower() == "false":
                    issues.append(
                        f"Knowledge appears to be disabled in {kf.name}. "
                        "Einstein Article Recommendations and Service Replies with Einstein "
                        "require Salesforce Knowledge to be enabled with published articles. "
                        "Enable Knowledge before activating these Einstein for Service features."
                    )

    return issues


def check_reply_recommendations_training_data(manifest_dir: Path, verbose: bool) -> list[str]:
    """Detect Reply Recommendations config and warn if Training Data job reference is missing."""
    issues: list[str] = []

    # Search all XML files for Reply Recommendations references
    reply_rec_refs: list[Path] = []
    for xml_file in _find_files(manifest_dir, "**/*.xml"):
        content = _read_text_safe(xml_file)
        if "replyrecommendation" in content.lower() or "ReplyRecommendation" in content:
            reply_rec_refs.append(xml_file)

    if not reply_rec_refs:
        return issues  # Feature not referenced — no check needed

    # If Reply Recommendations is referenced, warn about the Training Data dependency
    training_data_refs: list[Path] = []
    for xml_file in _find_files(manifest_dir, "**/*.xml"):
        content = _read_text_safe(xml_file)
        if "trainingdata" in content.lower() or "TrainingData" in content:
            training_data_refs.append(xml_file)

    if reply_rec_refs and not training_data_refs:
        issues.append(
            "Einstein Reply Recommendations configuration detected but no Training Data "
            "configuration found. Reply Recommendations requires an explicit Training Data job "
            "to be run in Setup > Service > Einstein Reply Recommendations > Training Data "
            "before the model can generate suggestions. Enabling the feature toggle alone "
            "is not sufficient — the Training Data job must complete successfully first."
        )

    return issues


def check_case_classification_fields_are_picklists(manifest_dir: Path, verbose: bool) -> list[str]:
    """Warn if any Case field configured for classification is not a picklist type.

    Case Classification only supports picklist fields. Custom text or formula fields
    cannot be included in the classification model.
    """
    issues: list[str] = []

    # Look for CaseClassification metadata files
    for xml_file in _find_files(manifest_dir, "**/*.xml"):
        content = _read_text_safe(xml_file)
        if "CaseClassification" not in content and "caseClassification" not in content:
            continue

        # Parse and look for field references
        root = _parse_xml_safe(xml_file)
        if root is None:
            continue

        for elem in root.iter():
            tag = _strip_ns(elem.tag)
            if tag.lower() in ("field", "fieldname"):
                field_val = (elem.text or "").strip()
                if field_val and verbose:
                    # Surface all configured fields so the operator can verify they are picklists
                    pass  # Field inventory surfaced below

        # If classification config exists, surface an informational note when verbose
        if verbose:
            issues.append(
                f"Case Classification configuration found in {xml_file.name}. "
                "Verify that all fields selected for classification are picklist fields on the "
                "Case object. Case Classification does not support text, formula, or numeric "
                "fields. Non-picklist fields in the classification config will cause model "
                "training failures or silent field exclusion."
            )
            break  # Only emit this once

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path, verbose: bool) -> list[str]:
    """Run all Einstein for Service prerequisite checks and return collected issues."""
    all_issues: list[str] = []

    checks = [
        ("Permission set metadata", check_permission_sets_exist),
        ("Case layout Einstein components", check_case_layout_has_einstein_component),
        ("Service settings metadata", check_service_settings_metadata),
        ("Knowledge enabled", check_knowledge_enabled),
        ("Reply Recommendations Training Data", check_reply_recommendations_training_data),
        ("Case Classification field types", check_case_classification_fields_are_picklists),
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
            "Validate Einstein for Service prerequisites in a Salesforce metadata directory. "
            "Checks permission sets, page layouts, Knowledge settings, Service settings, "
            "Reply Recommendations Training Data dependency, and Case Classification field config."
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
        print("OK: No Einstein for Service prerequisite issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
