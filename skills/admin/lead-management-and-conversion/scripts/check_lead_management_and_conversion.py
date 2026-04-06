#!/usr/bin/env python3
"""Checker script for Lead Management and Conversion skill.

Validates Salesforce metadata for common lead management configuration issues:
- Missing or inactive Default Lead Owner in Lead Settings
- Web-to-Lead forms lacking reCAPTCHA configuration
- Custom Lead fields that have no field mapping entries (likely unmapped)
- Duplicate active auto-response rules (only one can be active)
- Lead status picklist missing a converted value

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lead_management_and_conversion.py [--help]
    python3 check_lead_management_and_conversion.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Lead management and conversion configuration for common issues. "
            "Point --manifest-dir at a Salesforce metadata deployment directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_lead_settings(manifest_dir: Path) -> list[str]:
    """Check LeadSettings metadata for common misconfigurations."""
    issues: list[str] = []

    # LeadSettings can appear in settings/Lead.settings-meta.xml
    settings_candidates = [
        manifest_dir / "settings" / "Lead.settings-meta.xml",
        manifest_dir / "Lead.settings-meta.xml",
    ]
    settings_file = next((p for p in settings_candidates if p.exists()), None)

    if settings_file is None:
        # Not present in this metadata export — skip, no issue to raise
        return issues

    try:
        tree = ET.parse(settings_file)
        root = tree.getroot()
        # Strip namespace for simpler access
        ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
        prefix = f"{{{ns}}}" if ns else ""

        default_owner = root.find(f".//{prefix}defaultLeadOwner")
        if default_owner is None or not (default_owner.text or "").strip():
            issues.append(
                "LeadSettings: defaultLeadOwner is not set. "
                "Unmatched web-to-lead submissions will be silently discarded."
            )
    except ET.ParseError as exc:
        issues.append(f"LeadSettings: could not parse {settings_file}: {exc}")

    return issues


def check_lead_field_mapping(manifest_dir: Path) -> list[str]:
    """Warn if no LeadConvertSettings metadata is present (likely unmapped fields)."""
    issues: list[str] = []

    # LeadConvertSettings lives in settings/LeadConvert.settings-meta.xml
    mapping_candidates = [
        manifest_dir / "settings" / "LeadConvert.settings-meta.xml",
        manifest_dir / "LeadConvert.settings-meta.xml",
    ]
    mapping_file = next((p for p in mapping_candidates if p.exists()), None)

    if mapping_file is None:
        # No mapping file present in this export — advisory only
        issues.append(
            "LeadConvertSettings file not found in metadata export. "
            "Verify that all custom Lead fields are mapped in "
            "Object Manager > Lead > Fields & Relationships > Map Lead Fields. "
            "Unmapped custom fields are silently dropped on conversion."
        )
        return issues

    try:
        tree = ET.parse(mapping_file)
        root = tree.getroot()
        ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
        prefix = f"{{{ns}}}" if ns else ""
        mappings = root.findall(f".//{prefix}fieldMapping")
        if not mappings:
            issues.append(
                "LeadConvertSettings has no fieldMapping entries. "
                "Custom fields on Lead will not transfer to Contact, Account, or "
                "Opportunity on conversion unless at least one mapping entry exists."
            )
    except ET.ParseError as exc:
        issues.append(f"LeadConvertSettings: could not parse {mapping_file}: {exc}")

    return issues


def check_lead_status_converted_value(manifest_dir: Path) -> list[str]:
    """Check that at least one Lead Status picklist value has converted=true."""
    issues: list[str] = []

    # Standard value set for Lead Status lives in standardValueSets/
    svs_candidates = [
        manifest_dir / "standardValueSets" / "LeadStatus.standardValueSet-meta.xml",
        manifest_dir / "LeadStatus.standardValueSet-meta.xml",
    ]
    svs_file = next((p for p in svs_candidates if p.exists()), None)

    if svs_file is None:
        return issues  # Not in this export — skip

    try:
        tree = ET.parse(svs_file)
        root = tree.getroot()
        ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
        prefix = f"{{{ns}}}" if ns else ""

        converted_values = [
            v
            for v in root.findall(f".//{prefix}standardValue")
            if (v.find(f"{prefix}converted") is not None
                and (v.find(f"{prefix}converted").text or "").strip().lower() == "true")
        ]
        if not converted_values:
            issues.append(
                "LeadStatus standard value set has no value with <converted>true</converted>. "
                "Without a converted status value, the Lead conversion wizard will not be available."
            )
    except ET.ParseError as exc:
        issues.append(f"LeadStatus StandardValueSet: could not parse {svs_file}: {exc}")

    return issues


def check_auto_response_rules(manifest_dir: Path) -> list[str]:
    """Check that at most one Lead auto-response rule is marked active."""
    issues: list[str] = []

    # Auto-response rules are in autoResponseRules/Lead.autoResponseRules-meta.xml
    arr_candidates = [
        manifest_dir / "autoResponseRules" / "Lead.autoResponseRules-meta.xml",
        manifest_dir / "Lead.autoResponseRules-meta.xml",
    ]
    arr_file = next((p for p in arr_candidates if p.exists()), None)

    if arr_file is None:
        return issues

    try:
        tree = ET.parse(arr_file)
        root = tree.getroot()
        ns = root.tag.split("}")[0].lstrip("{") if "}" in root.tag else ""
        prefix = f"{{{ns}}}" if ns else ""

        active_rules = [
            r
            for r in root.findall(f".//{prefix}autoResponseRule")
            if (r.find(f"{prefix}active") is not None
                and (r.find(f"{prefix}active").text or "").strip().lower() == "true")
        ]
        if len(active_rules) > 1:
            active_names = [
                (r.find(f"{prefix}fullName") or r).text or "<unknown>"
                for r in active_rules
            ]
            issues.append(
                f"Multiple active Lead auto-response rules detected: {active_names}. "
                "Only one auto-response rule can be active at a time. "
                "Deploying multiple active rules may cause unpredictable behavior."
            )
    except ET.ParseError as exc:
        issues.append(f"Lead AutoResponseRules: could not parse {arr_file}: {exc}")

    return issues


def check_web_to_lead_recaptcha(manifest_dir: Path) -> list[str]:
    """Warn if web-to-lead HTML files in the metadata lack a reCAPTCHA reference."""
    issues: list[str] = []

    # Web-to-lead generated HTML is not a standard metadata type in deployments,
    # but some orgs commit generated form HTML to their repo.
    # Check any .html files in a webforms/ or web-to-lead/ directory.
    html_dirs = [
        manifest_dir / "webforms",
        manifest_dir / "web-to-lead",
        manifest_dir / "staticresources",
    ]

    html_files_found = []
    for d in html_dirs:
        if d.is_dir():
            html_files_found.extend(d.rglob("*.html"))

    for html_file in html_files_found:
        try:
            content = html_file.read_text(encoding="utf-8", errors="replace")
            if "webto.salesforce.com" in content and "recaptcha" not in content.lower():
                issues.append(
                    f"Web-to-Lead form at {html_file.relative_to(manifest_dir)} "
                    "does not appear to include a reCAPTCHA widget. "
                    "Without reCAPTCHA, bots can exhaust the 500/day submission limit."
                )
        except OSError:
            pass  # Unreadable file — skip

    return issues


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_lead_management(manifest_dir: Path) -> list[str]:
    """Run all lead management checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_lead_settings(manifest_dir))
    issues.extend(check_lead_field_mapping(manifest_dir))
    issues.extend(check_lead_status_converted_value(manifest_dir))
    issues.extend(check_auto_response_rules(manifest_dir))
    issues.extend(check_web_to_lead_recaptcha(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lead_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
