#!/usr/bin/env python3
"""
check_security_incident_response.py

Static checker for Salesforce Security Incident Response readiness.

Inspects a Salesforce metadata manifest directory for:
- LoginAnomaly Transaction Security Policy configuration
- Connected App refresh token policies
- Event log retention posture (free tier vs Shield/Event Monitoring add-on)

Usage:
    python3 check_security_incident_response.py --manifest-dir /path/to/metadata

The manifest directory should contain unpacked Salesforce metadata in the
standard DX source format (sfdx-project.json or force-app layout), or a
standard metadata API retrieve layout with transactionSecurityPolicies/,
connectedApps/, and settings/ directories.

No external dependencies required (stdlib only).
"""

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SALESFORCE_METADATA_NS = "http://soap.sforce.com/2006/04/metadata"

TRANSACTION_SECURITY_POLICY_DIRS = [
    "transactionSecurityPolicies",
    "force-app/main/default/transactionSecurityPolicies",
]

CONNECTED_APP_DIRS = [
    "connectedApps",
    "force-app/main/default/connectedApps",
]

SETTINGS_DIRS = [
    "settings",
    "force-app/main/default/settings",
]

# Known enforcement action values in Transaction Security Policy metadata
ENFORCEMENT_ACTIONS_BLOCKING = {"Block", "EndSession", "TwoFactor"}
ENFORCEMENT_ACTIONS_NOTIFY_ONLY = {"Notification"}

# Event Monitoring license indicators in Security Settings
EVENT_MONITORING_SETTING_FIELDS = [
    "enableEventLogFile",
    "enableEventMonitoring",
]

# Acceptable refresh token validity policies for Connected Apps (more restrictive = better)
# Salesforce valid values: Infinite, Zero (= immediate revoke after access token expiry),
# SpecificLifetime, or any named policy
REFRESH_TOKEN_POLICIES_PERMISSIVE = {"Infinite"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(base_dir: Path, subdirs: list, extension: str) -> list[Path]:
    """Search known metadata subdirectory candidates for files with a given extension."""
    found = []
    for subdir in subdirs:
        candidate = base_dir / subdir
        if candidate.is_dir():
            found.extend(candidate.glob(f"**/*{extension}"))
    return found


def parse_xml_root(path: Path):
    """Parse an XML file and return (root, namespace_prefix). Returns (None, '') on error."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # Strip namespace for tag matching if present
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0].lstrip("{")
            return root, f"{{{ns}}}"
        return root, ""
    except ET.ParseError as e:
        return None, ""


def get_text(element, tag: str, ns: str = "", default: str = "") -> str:
    """Get text of a direct child element, with optional namespace prefix."""
    child = element.find(f"{ns}{tag}")
    if child is not None and child.text:
        return child.text.strip()
    return default


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_login_anomaly_policy(manifest_dir: Path) -> list[str]:
    """
    Check whether a Transaction Security Policy for LoginAnomaly events exists
    and has a blocking or notification enforcement action.

    Returns a list of finding strings.
    """
    findings = []
    policy_files = find_files(manifest_dir, TRANSACTION_SECURITY_POLICY_DIRS, ".policy-meta.xml")

    if not policy_files:
        # Try legacy metadata layout: .transactionSecurityPolicy
        policy_files = find_files(manifest_dir, TRANSACTION_SECURITY_POLICY_DIRS, ".transactionSecurityPolicy-meta.xml")

    if not policy_files:
        findings.append(
            "WARNING: No Transaction Security Policy metadata files found. "
            "Cannot verify LoginAnomaly policy configuration. "
            "If the org has Salesforce Shield, a LoginAnomaly policy with at minimum "
            "a Notification action is recommended."
        )
        return findings

    login_anomaly_policies = []

    for policy_file in policy_files:
        root, ns = parse_xml_root(policy_file)
        if root is None:
            findings.append(f"WARNING: Could not parse {policy_file.name} — skipping.")
            continue

        # Check event type referenced in policy
        event_type = get_text(root, "eventType", ns)
        if not event_type:
            # Try nested under resourceName or eventCondition
            for elem in root.iter(f"{ns}resourceName"):
                if elem.text and "LoginAnomaly" in elem.text:
                    event_type = "LoginAnomaly"
                    break

        if event_type and "LoginAnomaly" in event_type:
            login_anomaly_policies.append(policy_file)

            # Check enforcement action
            action = get_text(root, "action", ns)
            if not action:
                # Try nested actionType
                for elem in root.iter(f"{ns}actionType"):
                    if elem.text:
                        action = elem.text.strip()
                        break

            enabled = get_text(root, "active", ns, "true")

            if enabled.lower() == "false":
                findings.append(
                    f"WARNING [{policy_file.name}]: LoginAnomaly Transaction Security Policy "
                    f"is INACTIVE. Policy will not fire until activated."
                )
            elif action in ENFORCEMENT_ACTIONS_BLOCKING:
                findings.append(
                    f"OK [{policy_file.name}]: LoginAnomaly policy active with blocking action '{action}'."
                )
            elif action in ENFORCEMENT_ACTIONS_NOTIFY_ONLY:
                findings.append(
                    f"OK [{policy_file.name}]: LoginAnomaly policy active with Notification action. "
                    f"Consider upgrading to Block or EndSession for higher-risk orgs."
                )
            elif action:
                findings.append(
                    f"INFO [{policy_file.name}]: LoginAnomaly policy active with action '{action}'. "
                    f"Verify this action is appropriate for the org's IR posture."
                )
            else:
                findings.append(
                    f"WARNING [{policy_file.name}]: LoginAnomaly policy found but enforcement action "
                    f"could not be determined from metadata. Manual verification required."
                )

    if not login_anomaly_policies:
        findings.append(
            "WARNING: No Transaction Security Policy for LoginAnomaly event type found in manifest. "
            "If the org has Salesforce Shield, configure a LoginAnomaly policy with at minimum "
            "a Notification action to alert admins of ML-flagged suspicious logins. "
            "Without this policy, LoginAnomaly events are recorded but no admin alert fires."
        )

    return findings


def check_connected_app_refresh_token_policies(manifest_dir: Path) -> list[str]:
    """
    Check Connected App metadata for overly permissive refresh token policies.

    Returns a list of finding strings.
    """
    findings = []
    app_files = find_files(manifest_dir, CONNECTED_APP_DIRS, ".connectedApp-meta.xml")

    if not app_files:
        findings.append(
            "INFO: No Connected App metadata files found in manifest. "
            "If Connected Apps are defined in the org, retrieve their metadata "
            "and re-run this check to validate refresh token policies."
        )
        return findings

    for app_file in app_files:
        root, ns = parse_xml_root(app_file)
        if root is None:
            findings.append(f"WARNING: Could not parse {app_file.name} — skipping.")
            continue

        app_name = get_text(root, "label", ns) or app_file.stem

        # Refresh token policy is nested in oauthConfig > refreshTokenValidityMetric
        # or in a refreshTokenPolicy element
        refresh_token_validity = ""
        oauth_config = root.find(f"{ns}oauthConfig")
        if oauth_config is not None:
            refresh_token_validity = get_text(oauth_config, "refreshTokenValidityMetric", ns)
            if not refresh_token_validity:
                refresh_token_validity = get_text(oauth_config, "refreshTokenPolicy", ns)

        if not refresh_token_validity:
            findings.append(
                f"INFO [{app_name}]: Refresh token policy not found in metadata. "
                f"Default is Infinite lifetime. Verify in Setup > Connected Apps "
                f"and configure a specific expiry for non-interactive integrations."
            )
        elif refresh_token_validity in REFRESH_TOKEN_POLICIES_PERMISSIVE:
            findings.append(
                f"WARNING [{app_name}]: Refresh token policy is '{refresh_token_validity}' (never expires). "
                f"Consider configuring a specific lifetime (e.g., 7 days for user-facing apps, "
                f"or 'Immediately expire refresh token' for server-to-server flows using "
                f"client_credentials grant). Infinite tokens extend attacker dwell time "
                f"if the token is compromised."
            )
        else:
            findings.append(
                f"OK [{app_name}]: Refresh token policy is '{refresh_token_validity}'."
            )

        # Check for IP relaxation (overly permissive = higher risk)
        ip_relaxation = ""
        if oauth_config is not None:
            ip_relaxation = get_text(oauth_config, "ipRelaxation", ns)

        if ip_relaxation and ip_relaxation.lower() in {"relaxedipranges", "relaxed"}:
            findings.append(
                f"WARNING [{app_name}]: Connected App has relaxed IP restrictions. "
                f"Consider enforcing IP restrictions to reduce attack surface."
            )

    return findings


def check_event_log_retention_posture(manifest_dir: Path) -> list[str]:
    """
    Probe org settings metadata for indicators of Event Monitoring add-on or Shield.

    Returns a list of finding strings.
    """
    findings = []
    settings_files = find_files(manifest_dir, SETTINGS_DIRS, ".settings-meta.xml")

    # Also look for SecuritySettings specifically
    security_settings_files = []
    for settings_file in settings_files:
        if "Security" in settings_file.name:
            security_settings_files.append(settings_file)

    shield_indicators_found = []

    for settings_file in security_settings_files:
        root, ns = parse_xml_root(settings_file)
        if root is None:
            continue

        for field in EVENT_MONITORING_SETTING_FIELDS:
            value = get_text(root, field, ns)
            if value.lower() == "true":
                shield_indicators_found.append(f"{field}=true in {settings_file.name}")

        # Check for Shield-specific settings
        for elem in root.iter():
            tag = elem.tag.replace(ns, "") if ns else elem.tag
            if "shield" in tag.lower() or "eventmonitoring" in tag.lower():
                if elem.text and elem.text.strip().lower() == "true":
                    shield_indicators_found.append(f"{tag}=true in {settings_file.name}")

    if shield_indicators_found:
        findings.append(
            f"OK: Event Monitoring indicators found in org settings: "
            f"{'; '.join(shield_indicators_found)}. "
            f"30-day EventLogFile retention and extended event types likely available."
        )
    else:
        findings.append(
            "WARNING: No Event Monitoring or Shield license indicators found in org settings metadata. "
            "Org may be on free-tier Event Monitoring: 5 event types, 1-day retention only. "
            "In a security incident, EventLogFile records may expire within 24 hours of the attack. "
            "Always download EventLogFile CSVs as the FIRST IR action. "
            "Free-tier fallback forensic sources: LoginHistory (6-month retention), "
            "SetupAuditTrail (180-day retention)."
        )

    if not settings_files:
        findings.append(
            "INFO: No org settings metadata found in manifest. "
            "Cannot determine Event Monitoring license posture from static analysis. "
            "Query EventLogFile in the org to confirm available event types and retention window."
        )

    return findings


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(all_findings: dict[str, list[str]]) -> int:
    """Print findings report. Returns exit code (0 = no warnings, 1 = warnings present)."""
    has_warnings = False
    total_findings = 0

    print()
    print("=" * 70)
    print("  Security Incident Response Readiness Check")
    print("=" * 70)

    for check_name, findings in all_findings.items():
        print(f"\n[{check_name}]")
        if not findings:
            print("  No findings.")
        for finding in findings:
            total_findings += 1
            if finding.startswith("WARNING"):
                has_warnings = True
                print(f"  {finding}")
            elif finding.startswith("OK"):
                print(f"  {finding}")
            else:
                print(f"  {finding}")

    print()
    print("-" * 70)
    print(f"Total findings: {total_findings}")
    if has_warnings:
        print("Result: WARNINGS present — review findings above before relying on this org for IR.")
        print()
        print("Reminder: In Salesforce IR, preserve evidence BEFORE containment.")
        print("Free-tier orgs have 1-day EventLogFile retention — download logs immediately.")
    else:
        print("Result: No blocking warnings detected.")
    print("=" * 70)
    print()

    return 1 if has_warnings else 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for security incident response readiness: "
            "LoginAnomaly Transaction Security Policy, Connected App refresh token policies, "
            "and Event Monitoring license posture."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        required=True,
        help="Path to a Salesforce metadata manifest directory (DX source format or classic retrieve layout).",
    )
    args = parser.parse_args()

    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: --manifest-dir '{manifest_dir}' does not exist or is not a directory.", file=sys.stderr)
        sys.exit(2)

    all_findings = {
        "LoginAnomaly Transaction Security Policy": check_login_anomaly_policy(manifest_dir),
        "Connected App Refresh Token Policies": check_connected_app_refresh_token_policies(manifest_dir),
        "Event Log Retention Posture": check_event_log_retention_posture(manifest_dir),
    }

    exit_code = print_report(all_findings)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
