#!/usr/bin/env python3
"""Checker script for Einstein Activity Capture Setup skill.

Validates Salesforce metadata for common EAC configuration issues:
- PermissionSetLicense assignment files referencing EAC PSL
- EAC Configuration profile metadata presence
- Presence of excluded domain configuration
- Private Activities flag review
- Named Credential for Org-Level OAuth

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_einstein_activity_capture_setup.py [--manifest-dir path/to/metadata]
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
            "Check Einstein Activity Capture Setup configuration and metadata "
            "for common issues. Scans a Salesforce DX project or metadata "
            "manifest directory for EAC-related configuration problems."
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

def _strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from a tag string."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _get_ns(root_tag: str) -> str:
    """Return '{namespace}' prefix or empty string."""
    if root_tag.startswith("{"):
        return root_tag.split("}")[0] + "}"
    return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_manifest_dir_exists(manifest_dir: Path) -> list[str]:
    """Return an issue if the manifest directory does not exist."""
    issues: list[str] = []
    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
    return issues


def check_eac_permission_set_license_assignment(manifest_dir: Path) -> list[str]:
    """
    Look for PermissionSet XML files that appear EAC-related and verify
    they reference the Einstein Activity Capture PSL.
    """
    issues: list[str] = []

    ps_files = list(manifest_dir.rglob("*.permissionset-meta.xml"))
    if not ps_files:
        return issues

    for ps_file in ps_files:
        try:
            tree = ET.parse(ps_file)
            root = tree.getroot()
            ns = _get_ns(root.tag)

            label_el = root.find(f"{ns}label")
            name = ps_file.stem.replace(".permissionset", "")
            label = label_el.text if label_el is not None else ""

            is_eac_related = any(
                kw in name.lower() or kw in label.lower()
                for kw in ("einstein", "eac", "activity_capture", "activitycapture")
            )

            if is_eac_related:
                psl_elements = root.findall(f".//{ns}permissionSetLicenseAssignments")
                psl_names = [
                    el.find(f"{ns}permissionSetLicense").text
                    for el in psl_elements
                    if el.find(f"{ns}permissionSetLicense") is not None
                ]
                eac_psl_present = any(
                    "EinsteinActivityCapture" in (n or "") or "einstein_activity" in (n or "").lower()
                    for n in psl_names
                )
                if not eac_psl_present:
                    issues.append(
                        f"Permission set '{name}' appears EAC-related but does not "
                        f"reference the 'Einstein Activity Capture' PSL. "
                        f"PSL assignment is required before users can sync. ({ps_file})"
                    )
        except ET.ParseError as exc:
            issues.append(f"Could not parse permission set file {ps_file}: {exc}")

    return issues


def check_eac_configuration_profiles_present(manifest_dir: Path) -> list[str]:
    """
    Look for EAC Configuration profile metadata files. Returns an informational
    note if none are found, since Configuration is often managed via Setup UI only.
    """
    issues: list[str] = []

    eac_meta_patterns = [
        "*.einsteinActivitySettings-meta.xml",
        "*EAC*.customMetadata-meta.xml",
        "*EinsteinActivityCapture*.customMetadata-meta.xml",
        "*ActivityCapture*.customMetadata-meta.xml",
    ]

    found_any = False
    for pattern in eac_meta_patterns:
        if list(manifest_dir.rglob(pattern)):
            found_any = True
            break

    if not found_any:
        issues.append(
            "INFO: No EAC Configuration profile metadata files found in manifest. "
            "If EAC is in use, consider tracking Configuration profile metadata in "
            "version control for auditability. EAC Configuration profiles can be "
            "deployed via Metadata API (EinsteinActivitySettings type)."
        )

    return issues


def check_eac_excluded_domains_configured(manifest_dir: Path) -> list[str]:
    """
    Parse any found EAC configuration metadata files and check whether
    excluded domains are configured.
    """
    issues: list[str] = []

    eac_config_files: list[Path] = []
    for pattern in [
        "*.einsteinActivitySettings-meta.xml",
        "*ActivityCapture*.customMetadata-meta.xml",
    ]:
        eac_config_files.extend(manifest_dir.rglob(pattern))

    for config_file in eac_config_files:
        try:
            tree = ET.parse(config_file)
            root = tree.getroot()
            ns = _get_ns(root.tag)

            excluded_domains = root.findall(f".//{ns}excludedDomain")
            excluded_addresses = root.findall(f".//{ns}excludedEmailAddress")

            if not excluded_domains and not excluded_addresses:
                issues.append(
                    f"EAC Configuration file '{config_file.name}' has no excluded "
                    f"domains or email addresses configured. "
                    f"This means ALL email communications will sync to Salesforce. "
                    f"Review with Legal/Compliance before deploying — add exclusions "
                    f"for competitor domains, legal counsel, HR vendors, and executive accounts."
                )
        except ET.ParseError as exc:
            issues.append(f"Could not parse EAC configuration file {config_file}: {exc}")

    return issues


def check_eac_private_activities_flag(manifest_dir: Path) -> list[str]:
    """
    Check EAC Configuration metadata for Private Activities setting.
    If privateActivities is not explicitly set, flag for review.
    """
    issues: list[str] = []

    eac_config_files: list[Path] = []
    for pattern in [
        "*.einsteinActivitySettings-meta.xml",
        "*ActivityCapture*.customMetadata-meta.xml",
    ]:
        eac_config_files.extend(manifest_dir.rglob(pattern))

    for config_file in eac_config_files:
        try:
            tree = ET.parse(config_file)
            root = tree.getroot()
            ns = _get_ns(root.tag)

            private_el = root.find(f".//{ns}privateActivities")
            if private_el is None:
                issues.append(
                    f"EAC Configuration file '{config_file.name}' does not explicitly "
                    f"set 'privateActivities'. Confirm whether Private Activities mode "
                    f"is required for this user group (e.g. executives). "
                    f"Default is disabled — activities are visible to all users with "
                    f"record access."
                )
        except ET.ParseError as exc:
            issues.append(f"Could not parse EAC configuration file {config_file}: {exc}")

    return issues


def check_named_credential_for_org_level_oauth(manifest_dir: Path) -> list[str]:
    """
    If any EAC Configuration references Org-Level OAuth, verify that a Named
    Credential for Microsoft 365 / AAD is present in the manifest.
    """
    issues: list[str] = []

    eac_config_files: list[Path] = []
    for pattern in [
        "*.einsteinActivitySettings-meta.xml",
        "*ActivityCapture*.customMetadata-meta.xml",
    ]:
        eac_config_files.extend(manifest_dir.rglob(pattern))

    for config_file in eac_config_files:
        try:
            tree = ET.parse(config_file)
            root = tree.getroot()
            ns = _get_ns(root.tag)

            auth_type_el = root.find(f".//{ns}authType")
            if auth_type_el is not None and "org" in (auth_type_el.text or "").lower():
                nc_files = list(manifest_dir.rglob("*.namedCredential-meta.xml"))
                eac_nc = [
                    f for f in nc_files
                    if any(
                        kw in f.stem.lower()
                        for kw in ("eac", "einstein", "activity", "microsoft", "azure", "m365")
                    )
                ]
                if not eac_nc:
                    issues.append(
                        f"EAC Configuration '{config_file.name}' uses Org-Level OAuth "
                        f"but no Named Credential for Microsoft 365 / Azure AD was found "
                        f"in the manifest. Ensure the AAD app consent is complete and "
                        f"the Named Credential is tracked in version control."
                    )
        except ET.ParseError as exc:
            issues.append(f"Could not parse EAC configuration file {config_file}: {exc}")

    return issues


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def check_einstein_activity_capture_setup(manifest_dir: Path) -> list[str]:
    """Run all EAC setup checks and return a consolidated list of issues."""
    issues: list[str] = []

    existence_issues = check_manifest_dir_exists(manifest_dir)
    if existence_issues:
        return existence_issues

    issues.extend(check_eac_permission_set_license_assignment(manifest_dir))
    issues.extend(check_eac_configuration_profiles_present(manifest_dir))
    issues.extend(check_eac_excluded_domains_configured(manifest_dir))
    issues.extend(check_eac_private_activities_flag(manifest_dir))
    issues.extend(check_named_credential_for_org_level_oauth(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_einstein_activity_capture_setup(manifest_dir)

    if not issues:
        print("No EAC configuration issues found.")
        return 0

    info_issues = [i for i in issues if i.startswith("INFO:")]
    error_issues = [i for i in issues if not i.startswith("INFO:")]

    for issue in error_issues:
        print(f"ISSUE: {issue}")

    for issue in info_issues:
        print(f"{issue}")

    return 1 if error_issues else 0


if __name__ == "__main__":
    sys.exit(main())
