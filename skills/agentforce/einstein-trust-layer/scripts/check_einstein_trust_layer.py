#!/usr/bin/env python3
"""Checker script for Einstein Trust Layer skill.

Validates Salesforce metadata for common Einstein Trust Layer misconfigurations.
Uses stdlib only — no pip dependencies.

Checks performed:
  - EinsteinSettings metadata: generativeAiEnabled flag present
  - Prompt templates: verifies expected structure in promptTemplates/ directory
  - Warns if no audit trail configuration file is found
  - Warns if data masking-related settings cannot be confirmed from metadata

Usage:
    python3 check_einstein_trust_layer.py [--help]
    python3 check_einstein_trust_layer.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Einstein Trust Layer configuration and metadata for common issues.\n\n"
            "Pass the root of a Salesforce DX project or an unzipped metadata retrieve "
            "as --manifest-dir. The script looks for EinsteinSettings, prompt templates, "
            "and related configuration files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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

def find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return sorted(root.rglob(pattern))


def read_xml_root(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on error."""
    try:
        tree = ET.parse(str(path))
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Remove XML namespace prefix from a tag string."""
    return tag.split("}")[-1] if "}" in tag else tag


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_einstein_settings(manifest_dir: Path) -> list[str]:
    """Check EinsteinSettings metadata for expected Trust Layer flags."""
    issues: list[str] = []
    settings_files = find_files(manifest_dir, "EinsteinSettings.settings-meta.xml")
    if not settings_files:
        issues.append(
            "No EinsteinSettings metadata file found. "
            "Cannot verify Einstein Generative AI is enabled. "
            "Expected path: settings/EinsteinSettings.settings-meta.xml"
        )
        return issues

    for path in settings_files:
        root = read_xml_root(path)
        if root is None:
            issues.append(f"Could not parse EinsteinSettings file: {path}")
            continue

        # Look for generativeAiEnabled or enableEinsteinGPTForSalesforce
        tags = {strip_ns(child.tag): child.text for child in root.iter()}
        generative_flag = tags.get("enableEinsteinGPTForSalesforce") or tags.get("generativeAiEnabled")
        if generative_flag is None:
            issues.append(
                f"{path}: Einstein Generative AI flag not found in EinsteinSettings. "
                "Confirm 'enableEinsteinGPTForSalesforce' is present and set to 'true'."
            )
        elif generative_flag.strip().lower() != "true":
            issues.append(
                f"{path}: Einstein Generative AI does not appear to be enabled "
                f"(found value: '{generative_flag.strip()}'). "
                "Einstein Trust Layer requires Generative AI to be turned on."
            )

    return issues


def check_prompt_templates(manifest_dir: Path) -> list[str]:
    """Check prompt templates for basic structural completeness."""
    issues: list[str] = []
    template_files = find_files(manifest_dir, "*.promptTemplate-meta.xml")

    if not template_files:
        # Not an error — org may not use Prompt Builder
        return issues

    for path in template_files:
        root = read_xml_root(path)
        if root is None:
            issues.append(f"Could not parse prompt template file: {path}")
            continue

        tags = {strip_ns(child.tag): child.text for child in root.iter()}

        # Warn if no templateBody or templateVersions element found
        has_body = "templateBody" in tags or "templateVersions" in tags
        if not has_body:
            issues.append(
                f"{path}: Prompt template appears to have no body or version content. "
                "Verify the template is fully defined — empty templates cannot be tested "
                "for data masking coverage."
            )

        # Warn if template references sensitive field patterns without masking note
        template_text = " ".join(str(v) for v in tags.values() if v)
        pii_indicators = ["ssn", "social security", "creditcard", "credit_card", "passport"]
        found_pii = [p for p in pii_indicators if p in template_text.lower()]
        if found_pii:
            issues.append(
                f"{path}: Prompt template text contains possible PII-related field references "
                f"({', '.join(found_pii)}). Confirm data masking is enabled and these fields "
                "are covered by the configured masking categories."
            )

    return issues


def check_for_audit_trail_config(manifest_dir: Path) -> list[str]:
    """Warn if no audit trail or Einstein feedback configuration is detectable."""
    issues: list[str] = []

    # Look for any data stream or Einstein feedback-related metadata
    feedback_files = (
        find_files(manifest_dir, "*EinsteinFeedback*")
        + find_files(manifest_dir, "*AuditTrail*")
        + find_files(manifest_dir, "*einstein*audit*")
    )
    feedback_files = [f for f in feedback_files if f.suffix not in {".py", ".md"}]

    if not feedback_files:
        issues.append(
            "No Einstein audit trail or feedback configuration files detected in the metadata. "
            "Ensure the Einstein Trust Layer audit trail is explicitly enabled in Setup "
            "(Setup > Einstein Setup > Go to Einstein Trust Layer > Audit Trail toggle). "
            "Audit trail is not active by default and is not retroactive — "
            "interactions before enablement are not logged."
        )

    return issues


def check_for_data360_dependency(manifest_dir: Path) -> list[str]:
    """Warn if Data 360 / Customer Data Platform related metadata is absent."""
    issues: list[str] = []

    cdp_files = (
        find_files(manifest_dir, "*.dataConnector-meta.xml")
        + find_files(manifest_dir, "*.cdpObjectDefinition-meta.xml")
        + find_files(manifest_dir, "*.dataStreamDefinition-meta.xml")
    )

    if not cdp_files:
        issues.append(
            "No Data 360 / Data Cloud metadata found. "
            "Einstein Trust Layer requires Data 360 to be provisioned for audit trail functionality. "
            "If this org uses Einstein Trust Layer features, confirm Data 360 is provisioned "
            "even if no Data Cloud objects are deployed in this metadata package."
        )

    return issues


def check_connected_apps_for_llm_gateway(manifest_dir: Path) -> list[str]:
    """Check connected apps for potential external LLM provider integrations."""
    issues: list[str] = []
    connected_app_files = find_files(manifest_dir, "*.connectedApp-meta.xml")

    llm_provider_indicators = ["openai", "anthropic", "vertex", "azureopenai", "bedrock", "cohere"]

    for path in connected_app_files:
        root = read_xml_root(path)
        if root is None:
            continue

        app_text = path.read_text(encoding="utf-8", errors="replace").lower()
        found_providers = [p for p in llm_provider_indicators if p in app_text]
        if found_providers:
            issues.append(
                f"{path}: Connected app may reference an external LLM provider "
                f"({', '.join(found_providers)}). "
                "Confirm this integration routes through the Einstein Trust Layer LLM gateway "
                "rather than bypassing it with a direct callout. "
                "Direct callouts to LLM providers bypass all Trust Layer controls."
            )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_einstein_trust_layer(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_einstein_settings(manifest_dir))
    issues.extend(check_prompt_templates(manifest_dir))
    issues.extend(check_for_audit_trail_config(manifest_dir))
    issues.extend(check_for_data360_dependency(manifest_dir))
    issues.extend(check_connected_apps_for_llm_gateway(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_einstein_trust_layer(manifest_dir)

    if not issues:
        print("No Einstein Trust Layer configuration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
        print()

    print(f"{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
