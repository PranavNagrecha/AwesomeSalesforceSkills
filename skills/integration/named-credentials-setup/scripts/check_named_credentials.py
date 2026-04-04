#!/usr/bin/env python3
"""Checker script for Named Credentials Setup skill.

Inspects Salesforce metadata in a local directory for common Named Credential
and External Credential configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_named_credentials.py --help
    python3 check_named_credentials.py --manifest-dir path/to/force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def _text(element: ET.Element, tag: str) -> str:
    child = element.find(_tag(tag))
    return child.text.strip() if child is not None and child.text else ""


# ---------------------------------------------------------------------------
# Named Credential checks
# ---------------------------------------------------------------------------

def check_named_credentials(nc_dir: Path) -> list[str]:
    issues: list[str] = []
    nc_files = list(nc_dir.glob("*.namedCredential-meta.xml"))

    if not nc_files:
        return issues

    for nc_file in nc_files:
        try:
            tree = ET.parse(nc_file)
        except ET.ParseError as exc:
            issues.append(f"[NC] Cannot parse {nc_file.name}: {exc}")
            continue

        root = tree.getroot()
        label = _text(root, "label") or nc_file.stem
        endpoint = _text(root, "endpoint")
        protocol = _text(root, "protocol")

        # Check for trailing slash in endpoint URL
        if endpoint.endswith("/"):
            issues.append(
                f"[NC] '{label}': endpoint URL ends with a trailing slash ('{endpoint}'). "
                "Apex callouts appending a path will produce double slashes."
            )

        # Check for legacy credentials that have embedded auth (no externalCredential reference)
        # Enhanced NCs reference an External Credential; legacy ones embed auth directly.
        ext_cred_ref = _text(root, "externalCredential")
        has_embedded_auth = protocol in ("Password", "Oauth")  # legacy protocols in a single record

        if not ext_cred_ref and has_embedded_auth:
            issues.append(
                f"[NC] '{label}': appears to be a legacy Named Credential "
                f"(protocol='{protocol}', no externalCredential reference). "
                "Consider migrating to the enhanced model (External Credential + Named Credential)."
            )

        # Check for placeholder or test-looking endpoint URLs in production-looking files
        if endpoint and any(marker in endpoint.lower() for marker in ["example.com", "localhost", "todo", "placeholder"]):
            issues.append(
                f"[NC] '{label}': endpoint URL looks like a placeholder: '{endpoint}'. "
                "Verify the correct production endpoint is set."
            )

    return issues


# ---------------------------------------------------------------------------
# External Credential checks
# ---------------------------------------------------------------------------

def check_external_credentials(ec_dir: Path) -> list[str]:
    issues: list[str] = []
    ec_files = list(ec_dir.glob("*.externalCredential-meta.xml"))

    if not ec_files:
        return issues

    for ec_file in ec_files:
        try:
            tree = ET.parse(ec_file)
        except ET.ParseError as exc:
            issues.append(f"[EC] Cannot parse {ec_file.name}: {exc}")
            continue

        root = tree.getroot()
        label = _text(root, "label") or ec_file.stem
        protocol = _text(root, "protocol")

        # Check: principals section exists
        principals = root.findall(_tag("principals"))
        if not principals:
            issues.append(
                f"[EC] '{label}': no principals defined. "
                "At least one principal is required for callouts to work."
            )
            continue

        for principal in principals:
            p_name = _text(principal, "principalName") or "(unnamed)"
            p_type = _text(principal, "principalType")

            # Check: permission set assignments on each principal
            perm_sets = principal.findall(_tag("permissionSetNameBindings"))
            if not perm_sets:
                issues.append(
                    f"[EC] '{label}' / principal '{p_name}': no Permission Set bindings found. "
                    "Without Permission Set assignment, no user can make callouts through this principal. "
                    "This is the most common cause of 401 errors after Enhanced NC setup."
                )

        # Check: OAuth Authorization Code flow should have a scope defined
        if protocol == "Oauth":
            flow_type = _text(root, "oauthFlowType")
            scope = _text(root, "oauthScope")
            if flow_type == "AuthorizationCode" and not scope:
                issues.append(
                    f"[EC] '{label}': OAuth Authorization Code flow has no scope defined. "
                    "Ensure the correct scope (e.g., 'openid offline_access') is set to enable token refresh."
                )

            # Check: Per User + Authorization Code should have offline_access or equivalent for refresh
            if flow_type == "AuthorizationCode" and scope and "offline_access" not in scope.lower() and "refresh_token" not in scope.lower():
                issues.append(
                    f"[EC] '{label}': OAuth Authorization Code scope ('{scope}') does not include "
                    "offline_access or refresh_token. Without a refresh token, users will need to "
                    "re-authorize whenever the access token expires."
                )

    return issues


# ---------------------------------------------------------------------------
# Cross-reference checks
# ---------------------------------------------------------------------------

def check_cross_references(nc_dir: Path, ec_dir: Path) -> list[str]:
    issues: list[str] = []

    # Build set of known External Credential developer names
    known_ec_names: set[str] = set()
    for ec_file in ec_dir.glob("*.externalCredential-meta.xml"):
        # File name format: DeveloperName.externalCredential-meta.xml
        dev_name = ec_file.name.replace(".externalCredential-meta.xml", "")
        known_ec_names.add(dev_name)

    # Check each Named Credential references a known External Credential
    for nc_file in nc_dir.glob("*.namedCredential-meta.xml"):
        try:
            tree = ET.parse(nc_file)
        except ET.ParseError:
            continue
        root = tree.getroot()
        label = _text(root, "label") or nc_file.stem
        ext_cred_ref = _text(root, "externalCredential")

        if ext_cred_ref and known_ec_names and ext_cred_ref not in known_ec_names:
            issues.append(
                f"[XREF] Named Credential '{label}' references External Credential "
                f"'{ext_cred_ref}' which was not found in the metadata directory. "
                "Verify the developer name matches exactly (case-sensitive)."
            )

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Named Credential and External Credential metadata for common "
            "configuration issues. Inspects XML metadata files in a local directory."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 check_named_credentials.py --manifest-dir force-app/main/default
  python3 check_named_credentials.py --manifest-dir .

Expected metadata structure:
  <manifest-dir>/
  ├── namedCredentials/        *.namedCredential-meta.xml
  └── externalCredentials/     *.externalCredential-meta.xml
        """,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata tree (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    # Locate metadata subdirectories — support both MDAPI and SFDX layouts
    nc_candidates = [
        manifest_dir / "namedCredentials",
        manifest_dir / "force-app" / "main" / "default" / "namedCredentials",
    ]
    ec_candidates = [
        manifest_dir / "externalCredentials",
        manifest_dir / "force-app" / "main" / "default" / "externalCredentials",
    ]

    nc_dir = next((p for p in nc_candidates if p.is_dir()), manifest_dir)
    ec_dir = next((p for p in ec_candidates if p.is_dir()), manifest_dir)

    issues: list[str] = []
    issues.extend(check_named_credentials(nc_dir))
    issues.extend(check_external_credentials(ec_dir))
    issues.extend(check_cross_references(nc_dir, ec_dir))

    if not issues:
        print("No issues found in Named Credential / External Credential metadata.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for issue in issues:
        print(f"  ISSUE: {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
