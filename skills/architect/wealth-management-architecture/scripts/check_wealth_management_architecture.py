#!/usr/bin/env python3
"""Checker script for Wealth Management Architecture skill.

Validates FSC wealth management metadata configuration for common issues:
- IndustriesSettings flags for wealth management features
- Compliant Data Sharing configuration signals
- Integration pattern metadata indicators

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_wealth_management_architecture.py [--help]
    python3 check_wealth_management_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Wealth Management Architecture configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_industries_settings(manifest_dir: Path) -> Path | None:
    """Locate the IndustriesSettings metadata file."""
    candidates = [
        manifest_dir / "settings" / "Industries.settings-meta.xml",
        manifest_dir / "force-app" / "main" / "default" / "settings" / "Industries.settings-meta.xml",
    ]
    for path in candidates:
        if path.exists():
            return path
    # Recursive search as fallback
    for found in manifest_dir.rglob("Industries.settings-meta.xml"):
        return found
    return None


def check_industries_settings(settings_path: Path) -> list[str]:
    """Parse IndustriesSettings XML and check for missing or misconfigured flags."""
    issues: list[str] = []

    try:
        tree = ET.parse(settings_path)
    except ET.ParseError as exc:
        issues.append(f"Industries.settings-meta.xml parse error: {exc}")
        return issues

    root = tree.getroot()
    # Strip XML namespace for element access
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    def get_flag(name: str) -> str | None:
        el = root.find(f"{ns}{name}")
        return el.text.strip() if el is not None and el.text else None

    ai_pref = get_flag("enableWealthManagementAIPref")
    deal_mgmt = get_flag("enableDealManagement")

    if ai_pref is None:
        issues.append(
            "Industries.settings-meta.xml: enableWealthManagementAIPref is not set. "
            "AI portfolio insights will be unavailable. Add this flag and deploy via Metadata API (requires API v63.0+)."
        )
    elif ai_pref.lower() == "false":
        issues.append(
            "Industries.settings-meta.xml: enableWealthManagementAIPref is explicitly set to false. "
            "AI portfolio insights and client analysis components will not render."
        )

    if deal_mgmt is None:
        issues.append(
            "Industries.settings-meta.xml: enableDealManagement is not set. "
            "Financial Deal Management (Interaction-to-Deal junction objects) will be unavailable."
        )
    elif deal_mgmt.lower() == "false":
        issues.append(
            "Industries.settings-meta.xml: enableDealManagement is explicitly set to false. "
            "Deal pipeline tracking in advisor workspaces requires this flag to be true."
        )

    return issues


def check_source_api_version(manifest_dir: Path) -> list[str]:
    """Check sfdx-project.json for API version compatibility with wealth management flags."""
    issues: list[str] = []

    project_file_candidates = [
        manifest_dir / "sfdx-project.json",
        manifest_dir.parent / "sfdx-project.json",
    ]

    import json

    for project_file in project_file_candidates:
        if not project_file.exists():
            continue
        try:
            with open(project_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        source_api_version = data.get("sourceApiVersion", "")
        if source_api_version:
            try:
                version_float = float(source_api_version)
                if version_float < 63.0:
                    issues.append(
                        f"sfdx-project.json: sourceApiVersion is {source_api_version}. "
                        "enableWealthManagementAIPref requires API v63.0+. "
                        "Deployments using this version will silently ignore the flag."
                    )
            except ValueError:
                pass
        break  # Only check the first found file

    return issues


def check_for_bulk_api_pattern(manifest_dir: Path) -> list[str]:
    """Warn if Apex classes appear to use insert DML for financial transaction records at scale."""
    issues: list[str] = []

    # Look for Apex classes that might be doing bulk DML on financial transaction objects
    apex_dir = manifest_dir / "force-app" / "main" / "default" / "classes"
    if not apex_dir.exists():
        apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        return issues

    suspicious_patterns = [
        "FinServ__FinancialAccountTransaction__c",
        "Financial_Account_Transaction__c",
    ]

    for apex_file in apex_dir.glob("*.cls"):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for obj_name in suspicious_patterns:
            if obj_name in content and "insert " in content.lower():
                # Check if it also has any Bulk API comment/reference
                if "bulk" not in content.lower() and "job" not in content.lower():
                    issues.append(
                        f"{apex_file.name}: Contains DML insert targeting {obj_name}. "
                        "For custodian data feeds exceeding 10K records, use Bulk API 2.0 ingest jobs "
                        "rather than DML-based insertion to avoid governor limit exhaustion."
                    )
                    break  # One warning per file

    return issues


def check_wealth_management_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check 1: IndustriesSettings flags
    settings_path = find_industries_settings(manifest_dir)
    if settings_path is None:
        issues.append(
            "Industries.settings-meta.xml not found in manifest directory. "
            "FSC wealth management feature flags (enableWealthManagementAIPref, enableDealManagement) "
            "must be deployed via IndustriesSettings metadata — they cannot be set via Setup UI alone."
        )
    else:
        issues.extend(check_industries_settings(settings_path))

    # Check 2: Source API version compatibility
    issues.extend(check_source_api_version(manifest_dir))

    # Check 3: Bulk API pattern signals
    issues.extend(check_for_bulk_api_pattern(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_wealth_management_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
