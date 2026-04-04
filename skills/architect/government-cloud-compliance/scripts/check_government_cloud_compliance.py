#!/usr/bin/env python3
"""Checker script for Government Cloud Compliance skill.

Inspects a Salesforce metadata directory for common compliance gaps in
Government Cloud deployments. Covers FedRAMP High (GovCloud Plus) and
Hyperforce GovCloud patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_government_cloud_compliance.py [--help]
    python3 check_government_cloud_compliance.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Government Cloud compliance gaps "
            "(FedRAMP High / GovCloud Plus patterns)."
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


def check_connected_apps_ip_relaxation(manifest_dir: Path) -> list[str]:
    """Flag Connected Apps that relax IP restrictions — a compliance concern in GovCloud."""
    issues: list[str] = []
    connected_app_dir = manifest_dir / "connectedApps"
    if not connected_app_dir.exists():
        return issues

    for app_file in connected_app_dir.glob("*.connectedApp-meta.xml"):
        try:
            tree = ET.parse(app_file)
            root = tree.getroot()
            ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
            # Strip namespace if present
            tag = root.tag
            namespace = ""
            if tag.startswith("{"):
                namespace = tag[1 : tag.index("}")]
                ns = {"sf": namespace}

            ip_relaxation_els = root.findall(
                f"{{{'sf'}}}" if namespace else "ipRelaxation",
                ns if namespace else {},
            )
            # Simpler: find by local name
            for el in root.iter():
                local = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                if local == "ipRelaxation" and el.text in (
                    "RELAX_ALL",
                    "RELAX_IP_RANGES",
                ):
                    issues.append(
                        f"ConnectedApp '{app_file.stem}': ipRelaxation is '{el.text}'. "
                        "In GovCloud deployments all server-to-server Connected Apps should "
                        "enforce IP restrictions (ENFORCE_IP_RANGES). Relaxing IP restrictions "
                        "violates NIST 800-53 AC-17 intent and FedRAMP access control requirements."
                    )
        except ET.ParseError as exc:
            issues.append(f"ConnectedApp '{app_file.name}': XML parse error — {exc}")

    return issues


def check_profiles_for_modify_all_data(manifest_dir: Path) -> list[str]:
    """Flag profiles that grant Modify All Data — overly broad for FedRAMP least-privilege."""
    issues: list[str] = []
    profile_dir = manifest_dir / "profiles"
    if not profile_dir.exists():
        return issues

    for profile_file in profile_dir.glob("*.profile-meta.xml"):
        try:
            tree = ET.parse(profile_file)
            root = tree.getroot()
            for el in root.iter():
                local = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                if local == "userPermissions":
                    name_el = None
                    enabled_el = None
                    for child in el:
                        child_local = (
                            child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        )
                        if child_local == "name":
                            name_el = child
                        if child_local == "enabled":
                            enabled_el = child
                    if (
                        name_el is not None
                        and name_el.text == "ModifyAllData"
                        and enabled_el is not None
                        and enabled_el.text == "true"
                    ):
                        issues.append(
                            f"Profile '{profile_file.stem}': 'ModifyAllData' is enabled. "
                            "Granting Modify All Data violates NIST 800-53 AC-6 (Least Privilege). "
                            "Review whether this profile is used by integration users and replace "
                            "with narrowly scoped permission sets."
                        )
        except ET.ParseError as exc:
            issues.append(f"Profile '{profile_file.name}': XML parse error — {exc}")

    return issues


def check_named_credentials_protocol(manifest_dir: Path) -> list[str]:
    """Flag Named Credentials that use plaintext HTTP (non-HTTPS) endpoints."""
    issues: list[str] = []
    nc_dir = manifest_dir / "namedCredentials"
    if not nc_dir.exists():
        return issues

    for nc_file in nc_dir.glob("*.namedCredential-meta.xml"):
        try:
            tree = ET.parse(nc_file)
            root = tree.getroot()
            for el in root.iter():
                local = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                if local == "endpoint" and el.text and el.text.startswith("http://"):
                    issues.append(
                        f"NamedCredential '{nc_file.stem}': endpoint uses HTTP (not HTTPS). "
                        "FedRAMP SC controls require TLS for all data in transit. "
                        "Change the endpoint to HTTPS."
                    )
        except ET.ParseError as exc:
            issues.append(f"NamedCredential '{nc_file.name}': XML parse error — {exc}")

    return issues


def check_permission_sets_for_view_all_data(manifest_dir: Path) -> list[str]:
    """Flag permission sets that grant View All Data — overly broad for FedRAMP AC-6."""
    issues: list[str] = []
    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return issues

    for ps_file in ps_dir.glob("*.permissionset-meta.xml"):
        try:
            tree = ET.parse(ps_file)
            root = tree.getroot()
            for el in root.iter():
                local = el.tag.split("}")[-1] if "}" in el.tag else el.tag
                if local == "userPermissions":
                    name_el = None
                    enabled_el = None
                    for child in el:
                        child_local = (
                            child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        )
                        if child_local == "name":
                            name_el = child
                        if child_local == "enabled":
                            enabled_el = child
                    if (
                        name_el is not None
                        and name_el.text == "ViewAllData"
                        and enabled_el is not None
                        and enabled_el.text == "true"
                    ):
                        issues.append(
                            f"PermissionSet '{ps_file.stem}': 'ViewAllData' is enabled. "
                            "Review whether this permission set is granted to non-administrator users. "
                            "ViewAllData bypasses object and record sharing controls and conflicts with "
                            "NIST 800-53 AC-3 and AC-6 least privilege requirements."
                        )
        except ET.ParseError as exc:
            issues.append(f"PermissionSet '{ps_file.name}': XML parse error — {exc}")

    return issues


def check_session_settings(manifest_dir: Path) -> list[str]:
    """Check org-wide security settings for session timeout and MFA enforcement."""
    issues: list[str] = []
    settings_dir = manifest_dir / "settings"
    if not settings_dir.exists():
        return issues

    security_settings_file = settings_dir / "Security.settings-meta.xml"
    if not security_settings_file.exists():
        issues.append(
            "Security settings file not found (settings/Security.settings-meta.xml). "
            "Cannot verify session timeout, MFA, or IP restriction settings. "
            "These are required for NIST 800-53 IA-2 and AC-11 compliance."
        )
        return issues

    try:
        tree = ET.parse(security_settings_file)
        root = tree.getroot()

        session_timeout_found = False
        require_mfa_found = False

        for el in root.iter():
            local = el.tag.split("}")[-1] if "}" in el.tag else el.tag

            # Check for session timeout (FedRAMP IA-11 re-authentication)
            if local == "sessionTimeout" and el.text:
                session_timeout_found = True
                # Common timeout values in minutes
                high_timeout_values = {
                    "TwoHours",
                    "FourHours",
                    "EightHours",
                    "TwelveHours",
                    "TwentyFourHours",
                }
                if el.text in high_timeout_values:
                    issues.append(
                        f"Security settings: sessionTimeout is '{el.text}'. "
                        "FedRAMP High (NIST 800-53 AC-11) recommends a session timeout of 15–30 minutes "
                        "for inactivity. Review whether this timeout meets your agency AO's requirements."
                    )

            # Check for MFA enforcement
            if local == "enableMultiFactorAuthenticationInUi" and el.text:
                require_mfa_found = True
                if el.text.lower() != "true":
                    issues.append(
                        "Security settings: enableMultiFactorAuthenticationInUi is not set to 'true'. "
                        "FedRAMP High IA-2(1) requires MFA for all privileged user accounts. "
                        "Enable MFA enforcement for all GovCloud Plus users."
                    )

        if not session_timeout_found:
            issues.append(
                "Security settings: sessionTimeout not found. "
                "Verify session inactivity timeout is configured per NIST 800-53 AC-11."
            )

    except ET.ParseError as exc:
        issues.append(f"Security.settings-meta.xml: XML parse error — {exc}")

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_government_cloud_compliance(manifest_dir: Path) -> list[str]:
    """Return a list of compliance issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_connected_apps_ip_relaxation(manifest_dir))
    issues.extend(check_profiles_for_modify_all_data(manifest_dir))
    issues.extend(check_named_credentials_protocol(manifest_dir))
    issues.extend(check_permission_sets_for_view_all_data(manifest_dir))
    issues.extend(check_session_settings(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_government_cloud_compliance(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
