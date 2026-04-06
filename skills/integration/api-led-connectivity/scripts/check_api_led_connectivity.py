#!/usr/bin/env python3
"""Checker script for API-Led Connectivity skill.

Scans project metadata and documentation for common API-led connectivity
architecture issues: missing layer justifications, direct backend calls
bypassing System APIs, and misconfigured Named Credentials.

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_api_led_connectivity.py [--help]
    python3 check_api_led_connectivity.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check API-Led Connectivity architecture metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_named_credentials(manifest_dir: Path) -> list[Path]:
    """Find all Named Credential metadata files."""
    patterns = [
        "namedCredentials/*.namedCredential-meta.xml",
        "namedCredentials/*.namedCredential",
        "**/namedCredentials/*.namedCredential-meta.xml",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(manifest_dir.glob(pattern))
    return files


def find_external_services(manifest_dir: Path) -> list[Path]:
    """Find all External Service registration metadata files."""
    patterns = [
        "externalServiceRegistrations/*.externalServiceRegistration-meta.xml",
        "**/externalServiceRegistrations/*.externalServiceRegistration-meta.xml",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(manifest_dir.glob(pattern))
    return files


def find_apex_classes(manifest_dir: Path) -> list[Path]:
    """Find all Apex class files."""
    patterns = [
        "classes/*.cls",
        "**/classes/*.cls",
    ]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(manifest_dir.glob(pattern))
    return files


def check_direct_backend_callouts(apex_files: list[Path]) -> list[str]:
    """Detect Apex callouts that appear to call backend systems directly
    rather than through an API layer (heuristic).
    """
    issues: list[str] = []
    # Patterns that suggest direct backend calls (not through Named Credentials)
    direct_call_patterns = [
        re.compile(r"HttpRequest\b.*?setEndpoint\s*\(\s*['\"]https?://(?!login\.salesforce|test\.salesforce)", re.DOTALL),
        re.compile(r"req\.setEndpoint\s*\(\s*['\"]https?://(?!login\.salesforce|test\.salesforce)"),
    ]

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Check for hardcoded endpoints (not using Named Credentials)
        if "setEndpoint" in content and "callout:" not in content.lower():
            for pattern in direct_call_patterns:
                matches = pattern.findall(content)
                if matches:
                    issues.append(
                        f"{apex_file.name}: Contains hardcoded HTTP endpoint instead of "
                        f"Named Credential (callout:). This bypasses the API layer pattern. "
                        f"Use Named Credentials to route through managed API endpoints."
                    )
                    break

    return issues


def check_named_credential_auth(nc_files: list[Path]) -> list[str]:
    """Check Named Credentials for insecure auth patterns."""
    issues: list[str] = []

    for nc_file in nc_files:
        try:
            tree = ET.parse(nc_file)
            root = tree.getroot()
        except (ET.ParseError, OSError):
            issues.append(f"{nc_file.name}: Could not parse Named Credential XML.")
            continue

        # Strip namespace for easier element access
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Check for password-based auth (less secure than OAuth/JWT)
        protocol_elem = root.find(f"{ns}principalType")
        if protocol_elem is not None and protocol_elem.text == "NamedUser":
            auth_protocol = root.find(f"{ns}authProtocol")
            if auth_protocol is not None and auth_protocol.text == "Password":
                issues.append(
                    f"{nc_file.name}: Uses password-based authentication. "
                    f"For API-led connectivity, prefer OAuth 2.0 or JWT Bearer "
                    f"to avoid credential rotation issues across API layers."
                )

    return issues


def check_external_service_schema_size(es_files: list[Path]) -> list[str]:
    """Warn if External Service schema files appear large."""
    issues: list[str] = []
    SIZE_WARNING_THRESHOLD = 80_000  # chars, warn before hitting ~100K limit

    for es_file in es_files:
        try:
            content = es_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if len(content) > SIZE_WARNING_THRESHOLD:
            issues.append(
                f"{es_file.name}: External Service registration is {len(content):,} characters. "
                f"Salesforce has a ~100,000 character limit on OpenAPI specs for External Services. "
                f"Consider pruning unused operations to stay within the limit."
            )

    return issues


def check_api_led_connectivity(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Find relevant metadata files
    nc_files = find_named_credentials(manifest_dir)
    es_files = find_external_services(manifest_dir)
    apex_files = find_apex_classes(manifest_dir)

    if not nc_files and not es_files and not apex_files:
        issues.append(
            "No Named Credentials, External Services, or Apex classes found. "
            "Cannot perform API-led connectivity checks without integration metadata."
        )
        return issues

    # Run checks
    issues.extend(check_direct_backend_callouts(apex_files))
    issues.extend(check_named_credential_auth(nc_files))
    issues.extend(check_external_service_schema_size(es_files))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_api_led_connectivity(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
