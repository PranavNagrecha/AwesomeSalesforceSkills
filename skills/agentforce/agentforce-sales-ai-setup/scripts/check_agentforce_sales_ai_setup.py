#!/usr/bin/env python3
"""Checker script for Agentforce Sales AI Setup skill.

Checks Salesforce metadata and configuration relevant to Einstein for Sales setup.
Detects common misconfigurations and prerequisite gaps before or after enablement.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_agentforce_sales_ai_setup.py [--help]
    python3 check_agentforce_sales_ai_setup.py --manifest-dir path/to/metadata
    python3 check_agentforce_sales_ai_setup.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Einstein for Sales setup issues. "
            "Detects missing prerequisites, license-dependent features, and "
            "common configuration anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_opportunity_score_field_on_layout(manifest_dir: Path) -> list[str]:
    """Check that the Opportunity Score field is on at least one Opportunity page layout."""
    issues: list[str] = []
    layout_dir = manifest_dir / "layouts"
    if not layout_dir.exists():
        return issues  # no layouts deployed — skip silently

    opp_layouts = list(layout_dir.glob("Opportunity-*.layout-meta.xml"))
    if not opp_layouts:
        return issues  # no opportunity layouts present — skip

    score_field_found = False
    for layout_file in opp_layouts:
        try:
            tree = ET.parse(layout_file)
            root = tree.getroot()
            # Strip namespace for simplicity
            xml_text = layout_file.read_text(encoding="utf-8")
            if "Opportunity_Score" in xml_text or "OpportunityScore" in xml_text:
                score_field_found = True
                break
        except ET.ParseError:
            issues.append(
                f"Could not parse layout file: {layout_file.name} — check for XML errors."
            )

    if opp_layouts and not score_field_found:
        issues.append(
            "Opportunity Score field (Opportunity_Score__c) does not appear in any "
            "Opportunity page layout. Add it so reps can see scores after model training. "
            "(Setup > Object Manager > Opportunity > Page Layouts)"
        )
    return issues


def check_forecasting_enabled_in_settings(manifest_dir: Path) -> list[str]:
    """Check ForecastingSettings metadata for Collaborative Forecasting enablement."""
    issues: list[str] = []
    settings_dir = manifest_dir / "settings"
    if not settings_dir.exists():
        return issues

    forecasting_file = settings_dir / "Forecasting.settings-meta.xml"
    if not forecasting_file.exists():
        # If the settings file is absent, we cannot confirm state.
        issues.append(
            "Forecasting.settings-meta.xml not found in metadata. "
            "Cannot confirm Collaborative Forecasting is enabled. "
            "Verify manually: Setup > Forecasts Settings > Enable Forecasting. "
            "Collaborative Forecasting is required for Pipeline Inspection AI insights."
        )
        return issues

    try:
        xml_text = forecasting_file.read_text(encoding="utf-8")
        if "<enableForecasts>false</enableForecasts>" in xml_text:
            issues.append(
                "Forecasting.settings-meta.xml has <enableForecasts>false</enableForecasts>. "
                "Collaborative Forecasting is disabled. Pipeline Inspection AI insights will "
                "not appear until Collaborative Forecasting is enabled. "
                "(Setup > Forecasts Settings > Enable Forecasting)"
            )
    except OSError:
        issues.append(
            f"Could not read {forecasting_file.name} — check file permissions."
        )
    return issues


def check_einstein_permission_sets_assigned(manifest_dir: Path) -> list[str]:
    """Check that Einstein for Sales permission sets are present in metadata."""
    issues: list[str] = []
    perm_sets_dir = manifest_dir / "permissionsets"
    if not perm_sets_dir.exists():
        return issues  # no permission sets in this metadata slice — skip

    perm_set_files = list(perm_sets_dir.glob("*.permissionset-meta.xml"))
    perm_set_names = {f.stem.replace(".permissionset-meta", "") for f in perm_set_files}

    # Look for Einstein for Sales permission set patterns (names vary by org/edition)
    einstein_sales_patterns = ["EinsteinForSales", "Einstein_For_Sales", "SalesInsights"]
    found_einstein_ps = any(
        any(pattern.lower() in name.lower() for pattern in einstein_sales_patterns)
        for name in perm_set_names
    )

    if perm_set_files and not found_einstein_ps:
        issues.append(
            "No Einstein for Sales permission set found in deployed permission sets. "
            "Users need the Einstein for Sales permission set assigned to see Opportunity "
            "Scores and Pipeline Inspection AI features. "
            "Check Setup > Permission Sets for 'Einstein for Sales'."
        )
    return issues


def check_no_sandbox_score_expectation_in_docs(manifest_dir: Path) -> list[str]:
    """Warn if any UAT or test doc in this metadata dir mentions sandbox score validation."""
    issues: list[str] = []
    # Scan any markdown or text files in the directory for risky phrasing
    doc_files = list(manifest_dir.glob("**/*.md")) + list(manifest_dir.glob("**/*.txt"))
    risky_phrases = [
        "verify scores in sandbox",
        "test opportunity scoring in sandbox",
        "opportunity score in sandbox",
        "scores appear in sandbox",
    ]
    for doc_file in doc_files[:50]:  # limit scan to avoid large repo traversals
        try:
            content = doc_file.read_text(encoding="utf-8", errors="ignore").lower()
            for phrase in risky_phrases:
                if phrase in content:
                    issues.append(
                        f"{doc_file.name}: Contains '{phrase}' — Opportunity Scoring model "
                        "does not train in sandboxes. Scores will never appear in a sandbox. "
                        "Remove this from acceptance criteria or mark as explicitly expected behavior."
                    )
                    break
        except OSError:
            pass
    return issues


def check_generative_email_dependency_documented(manifest_dir: Path) -> list[str]:
    """Check if email composition is referenced without the Generative AI license note."""
    issues: list[str] = []
    doc_files = list(manifest_dir.glob("**/*.md")) + list(manifest_dir.glob("**/*.txt"))
    email_composition_phrases = [
        "generate email",
        "ai email composition",
        "einstein email composition",
        "generative email",
    ]
    license_note_phrases = [
        "generative ai",
        "einstein generative",
        "einstein gpt",
        "separate license",
    ]
    for doc_file in doc_files[:50]:
        try:
            content = doc_file.read_text(encoding="utf-8", errors="ignore").lower()
            mentions_composition = any(p in content for p in email_composition_phrases)
            mentions_license = any(p in content for p in license_note_phrases)
            if mentions_composition and not mentions_license:
                issues.append(
                    f"{doc_file.name}: Mentions Einstein email composition but does not "
                    "reference the Einstein Generative AI license requirement. "
                    "Email composition requires a SEPARATE Einstein Generative AI license "
                    "beyond the base Einstein for Sales add-on. Add a license note."
                )
        except OSError:
            pass
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def check_agentforce_sales_ai_setup(manifest_dir: Path) -> list[str]:
    """Run all Einstein for Sales setup checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_opportunity_score_field_on_layout(manifest_dir))
    issues.extend(check_forecasting_enabled_in_settings(manifest_dir))
    issues.extend(check_einstein_permission_sets_assigned(manifest_dir))
    issues.extend(check_no_sandbox_score_expectation_in_docs(manifest_dir))
    issues.extend(check_generative_email_dependency_documented(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_agentforce_sales_ai_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
