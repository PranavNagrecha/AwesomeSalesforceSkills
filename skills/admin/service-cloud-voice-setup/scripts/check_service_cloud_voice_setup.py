#!/usr/bin/env python3
"""Checker script for Service Cloud Voice Setup skill.

Checks Salesforce metadata for common Service Cloud Voice configuration issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_service_cloud_voice_setup.py [--help]
    python3 check_service_cloud_voice_setup.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Service Cloud Voice Setup configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file, returning None on any parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def check_call_center_definitions(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if callcenter.xml definitions are present alongside a Voice setup.

    Presence of Call Center definition files suggests Open CTI patterns that
    conflict with or duplicate Service Cloud Voice configuration.
    """
    call_center_dir = manifest_dir / "callCenters"
    if call_center_dir.is_dir():
        xml_files = list(call_center_dir.glob("*.xml"))
        if xml_files:
            issues.append(
                f"Found {len(xml_files)} Call Center definition file(s) in callCenters/. "
                "Service Cloud Voice (Amazon Connect) does not use Call Center definitions. "
                "Verify these are not leftover Open CTI artifacts that may conflict with voice routing."
            )


def check_permission_sets_for_voice(manifest_dir: Path, issues: list[str]) -> None:
    """Check that Service Cloud Voice permission sets exist.

    Looks for permission set metadata files with 'Voice' in the name.
    Does not validate assignment — only checks that the metadata is present.
    """
    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.is_dir():
        return

    ps_files = list(ps_dir.glob("*.permissionset-meta.xml"))
    if not ps_files:
        return

    voice_ps_names = [
        f.stem.replace(".permissionset-meta", "")
        for f in ps_files
        if "voice" in f.name.lower()
    ]

    if not voice_ps_names:
        issues.append(
            "No permission sets with 'voice' in the name found in permissionsets/. "
            "Service Cloud Voice requires 'Service Cloud Voice' and optionally "
            "'Service Cloud Voice Transcription' permission sets to be assigned to agents and supervisors."
        )


def check_omnichannel_service_channels(manifest_dir: Path, issues: list[str]) -> None:
    """Check for a VoiceCall service channel in Omni-Channel metadata.

    A missing VoiceCall service channel suggests the provisioning wizard
    did not complete successfully or the channel was manually deleted.
    """
    channels_dir = manifest_dir / "serviceChannels"
    if not channels_dir.is_dir():
        return

    channel_files = list(channels_dir.glob("*.serviceChannel-meta.xml"))
    if not channel_files:
        return

    has_voice_channel = False
    for cf in channel_files:
        root = _parse_xml_safe(cf)
        if root is None:
            continue
        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        # relatedEntity element contains the SObject type for the channel
        related_entity = root.find(".//relatedEntity", ns)
        if related_entity is None:
            # try without namespace
            related_entity = root.find(".//relatedEntity")
        if related_entity is not None and related_entity.text == "VoiceCall":
            has_voice_channel = True
            break

    if channel_files and not has_voice_channel:
        issues.append(
            "No Omni-Channel service channel with relatedEntity 'VoiceCall' found. "
            "Service Cloud Voice provisioning should create a VoiceCall service channel automatically. "
            "If voice setup is in progress, this may indicate an incomplete provisioning wizard run."
        )


def check_for_lambda_in_contact_flows(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if contact flow metadata references Lambda for basic routing.

    Custom Lambda invocations in contact flows for simple IVR scenarios
    (business hours, basic menus) indicate over-engineering. This check
    looks for Lambda ARN patterns in any flow XML files in the metadata.
    """
    flows_dir = manifest_dir / "flows"
    if not flows_dir.is_dir():
        return

    lambda_pattern = "arn:aws:lambda"
    suspicious_flows: list[str] = []

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if lambda_pattern in content:
            suspicious_flows.append(flow_file.name)

    if suspicious_flows:
        issues.append(
            f"Found {len(suspicious_flows)} flow file(s) referencing AWS Lambda ARNs: "
            f"{', '.join(suspicious_flows[:5])}{'...' if len(suspicious_flows) > 5 else ''}. "
            "Lambda is appropriate for data dips to external systems. Verify these flows "
            "are not using Lambda for scenarios that Amazon Connect contact flow blocks handle natively "
            "(business hours checks, queue routing, simple IVR menus)."
        )


def check_custom_domain_in_settings(manifest_dir: Path, issues: list[str]) -> None:
    """Check for MyDomain settings metadata indicating a custom domain is configured.

    Service Cloud Voice requires My Domain to be deployed for the softphone
    OAuth callback to work correctly.
    """
    settings_dir = manifest_dir / "settings"
    if not settings_dir.is_dir():
        return

    my_domain_file = settings_dir / "MyDomain.settings-meta.xml"
    if not my_domain_file.exists():
        # Settings may not be in metadata export; not an error, just informational
        return

    root = _parse_xml_safe(my_domain_file)
    if root is None:
        return

    # Look for the domain name element — if empty or missing, domain may not be configured
    domain_name = root.find(".//{http://soap.sforce.com/2006/04/metadata}domainName")
    if domain_name is None:
        domain_name = root.find(".//domainName")

    if domain_name is None or not (domain_name.text or "").strip():
        issues.append(
            "MyDomain settings found but domainName appears empty. "
            "Service Cloud Voice requires My Domain to be deployed to all users. "
            "Verify Setup > My Domain is configured and deployed."
        )


def check_service_cloud_voice_setup(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    check_call_center_definitions(manifest_dir, issues)
    check_permission_sets_for_voice(manifest_dir, issues)
    check_omnichannel_service_channels(manifest_dir, issues)
    check_for_lambda_in_contact_flows(manifest_dir, issues)
    check_custom_domain_in_settings(manifest_dir, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_service_cloud_voice_setup(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
