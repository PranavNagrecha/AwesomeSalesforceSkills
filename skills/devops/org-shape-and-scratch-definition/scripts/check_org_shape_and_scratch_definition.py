#!/usr/bin/env python3
"""Checker script for Org Shape And Scratch Definition skill.

Validates project-scratch-def.json files for common issues:
- Deprecated orgPreferences usage
- Invalid or misspelled feature names
- Conflicting sourceOrg + edition
- Missing settings structure
- Release field awareness

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_org_shape_and_scratch_definition.py --file path/to/project-scratch-def.json
    python3 check_org_shape_and_scratch_definition.py --manifest-dir path/to/config/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Known valid feature names (case-sensitive) from official Salesforce documentation.
# This is not exhaustive but covers the most commonly used features.
KNOWN_FEATURES: set[str] = {
    "API",
    "AnalyticsCRMAnalyticsPlusPlatform",
    "AuthorApex",
    "CallCenter",
    "Chatbot",
    "Communities",
    "ContactsToMultipleAccounts",
    "ContractApprovals",
    "CascadeDelete",
    "CustomerSelfService",
    "DebugApex",
    "DefaultWorkflowUser",
    "DependencyManagement",
    "DevelopmentWave",
    "EinsteinAnalyticsPlus",
    "EinsteinBuilderFree",
    "EnableSetPasswordInApi",
    "EntitlementProcess",
    "EventRelayFeedback",
    "ExternalSharing",
    "FieldAuditTrail",
    "FieldService",
    "FlowBuilderPlus",
    "ForceComPlatform",
    "Interaction",
    "Knowledge",
    "LightningComponentBundle",
    "LightningExperienceThemes",
    "LightningScheduler",
    "LightningServiceConsole",
    "LiveAgent",
    "Macros",
    "MultiCurrency",
    "Pardot",
    "PathAssistant",
    "PersonAccounts",
    "PlatformEncryption",
    "ProcessBuilder",
    "RecordTypes",
    "SalesConsole",
    "SalesforceIdentity",
    "ServiceCloud",
    "ServiceConsole",
    "SiteDotCom",
    "Sites",
    "StateAndCountryPicklist",
    "Territory2",
    "Workflow",
}

# Features known to be excluded from Org Shape capture.
ORG_SHAPE_EXCLUDED_FEATURES: set[str] = {
    "MultiCurrency",
    "PersonAccounts",
}

# Known valid settings top-level keys (Metadata API settings types).
KNOWN_SETTINGS_TYPES: set[str] = {
    "accountSettings",
    "activitiesSettings",
    "addressSettings",
    "apexSettings",
    "campaignSettings",
    "caseSettings",
    "chatterSettings",
    "communitiesSettings",
    "companySettings",
    "contractSettings",
    "emailAdministrationSettings",
    "enhancedNotesSettings",
    "entitlementSettings",
    "eventSettings",
    "fileUploadAndDownloadSecuritySettings",
    "flowSettings",
    "forecastingSettings",
    "ideasSettings",
    "industriesSettings",
    "knowledgeSettings",
    "languageSettings",
    "leadConvertSettings",
    "lightningExperienceSettings",
    "liveAgentSettings",
    "macroSettings",
    "mobileSettings",
    "nameSettings",
    "notificationsSettings",
    "opportunitySettings",
    "orderSettings",
    "orgPreferenceSettings",
    "pardotSettings",
    "pathAssistantSettings",
    "predictionBuilderSettings",
    "privacySettings",
    "productSettings",
    "quoteSettings",
    "searchSettings",
    "securitySettings",
    "sharingSettings",
    "socialProfileSettings",
    "territory2Settings",
    "trialOrgSettings",
    "userEngagementSettings",
    "userInterfaceSettings",
    "userManagementSettings",
    "voiceSettings",
}

VALID_EDITIONS: set[str] = {
    "Developer",
    "Enterprise",
    "Group",
    "Professional",
    "Partner Developer",
    "Partner Enterprise",
    "Partner Group",
    "Partner Professional",
}

VALID_RELEASES: set[str] = {"Previous", "Preview"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check scratch org definition files for common issues.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--file",
        default=None,
        help="Path to a specific project-scratch-def.json file.",
    )
    group.add_argument(
        "--manifest-dir",
        default=".",
        help="Directory to search for project-scratch-def.json files (default: cwd).",
    )
    return parser.parse_args()


def find_def_files(manifest_dir: Path) -> list[Path]:
    """Find all scratch org definition files in the given directory tree."""
    results: list[Path] = []
    for p in manifest_dir.rglob("*.json"):
        if "scratch" in p.name.lower() and "def" in p.name.lower():
            results.append(p)
    # Also check common conventional name
    direct = manifest_dir / "project-scratch-def.json"
    if direct.exists() and direct not in results:
        results.append(direct)
    return results


def check_definition(file_path: Path) -> list[str]:
    """Validate a single scratch org definition file. Returns list of issues."""
    issues: list[str] = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        issues.append(f"{file_path}: Invalid JSON — {e}")
        return issues
    except OSError as e:
        issues.append(f"{file_path}: Cannot read file — {e}")
        return issues

    if not isinstance(data, dict):
        issues.append(f"{file_path}: Top-level value must be a JSON object, got {type(data).__name__}")
        return issues

    # Check for deprecated orgPreferences
    if "orgPreferences" in data:
        issues.append(
            f"{file_path}: Uses deprecated 'orgPreferences' — migrate to 'settings' block. "
            "orgPreferences has been deprecated since Winter '20 and may be silently ignored."
        )

    # Check sourceOrg + edition conflict
    has_source_org = "sourceOrg" in data
    has_edition = "edition" in data
    if has_source_org and has_edition:
        issues.append(
            f"{file_path}: Both 'sourceOrg' and 'edition' are set. "
            "When using Org Shape, omit 'edition' — it is inferred from the source org."
        )

    # Validate edition value
    if has_edition:
        edition = data["edition"]
        if edition not in VALID_EDITIONS:
            issues.append(
                f"{file_path}: Edition '{edition}' is not a recognized value. "
                f"Valid editions: {', '.join(sorted(VALID_EDITIONS))}"
            )

    # Validate features
    features = data.get("features", [])
    if isinstance(features, list):
        for feat in features:
            if not isinstance(feat, str):
                issues.append(f"{file_path}: Feature value must be a string, got {type(feat).__name__}: {feat}")
                continue
            if feat not in KNOWN_FEATURES:
                # Check for case mismatch
                lower_map = {k.lower(): k for k in KNOWN_FEATURES}
                if feat.lower() in lower_map:
                    issues.append(
                        f"{file_path}: Feature '{feat}' has incorrect casing. "
                        f"Did you mean '{lower_map[feat.lower()]}'? Feature names are case-sensitive."
                    )
                else:
                    issues.append(
                        f"{file_path}: Feature '{feat}' is not in the known features list. "
                        "Verify spelling against official Salesforce documentation."
                    )

        # Warn about Org Shape excluded features not declared
        if has_source_org:
            declared_features = set(features)
            for excl in ORG_SHAPE_EXCLUDED_FEATURES:
                if excl not in declared_features:
                    issues.append(
                        f"{file_path}: Uses Org Shape but does not declare '{excl}' in features. "
                        f"Org Shape does not capture {excl} — add it explicitly if your source org uses it."
                    )

    # Validate settings keys
    settings = data.get("settings", {})
    if isinstance(settings, dict):
        for key in settings:
            if key not in KNOWN_SETTINGS_TYPES:
                issues.append(
                    f"{file_path}: Settings key '{key}' is not a recognized Metadata API settings type. "
                    "Verify the type name against the Metadata API reference."
                )

    # Check release field
    release = data.get("release")
    if release is not None and release not in VALID_RELEASES:
        issues.append(
            f"{file_path}: Release value '{release}' is not valid. "
            f"Valid values: {', '.join(sorted(VALID_RELEASES))}"
        )

    return issues


def check_org_shape_and_scratch_definition(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Directory not found: {manifest_dir}")
        return issues

    def_files = find_def_files(manifest_dir)
    if not def_files:
        issues.append(f"No scratch org definition files found in {manifest_dir}")
        return issues

    for def_file in def_files:
        issues.extend(check_definition(def_file))

    return issues


def main() -> int:
    args = parse_args()

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"ISSUE: File not found: {file_path}")
            return 1
        issues = check_definition(file_path)
    else:
        manifest_dir = Path(args.manifest_dir)
        issues = check_org_shape_and_scratch_definition(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
