#!/usr/bin/env python3
"""Checker script for Experience Cloud Multi-IdP SSO skill.

Inspects Salesforce metadata in a retrieved project directory for common
multi-IdP SSO misconfigurations. Focuses on Auth Provider XML and
RegistrationHandler Apex class presence.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_multi_idp_sso.py [--help]
    python3 check_experience_cloud_multi_idp_sso.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud Multi-IdP SSO metadata for common issues: "
            "missing community parameter hints, missing RegistrationHandler, "
            "and SAML providers without Federation ID guidance."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_auth_provider_files(manifest_dir: Path) -> list[Path]:
    """Return all .authprovider metadata files under manifest_dir."""
    return list(manifest_dir.rglob("*.authprovider"))


def check_auth_provider(file: Path) -> list[str]:
    """Check a single Auth Provider metadata file for known issues."""
    issues: list[str] = []

    try:
        tree = ET.parse(file)
    except ET.ParseError as exc:
        issues.append(f"{file.name}: XML parse error — {exc}")
        return issues

    root = tree.getroot()
    # Strip namespace if present
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    def get_text(tag: str) -> str:
        el = root.find(f"{ns}{tag}")
        return el.text.strip() if el is not None and el.text else ""

    provider_type = get_text("providerType")
    registration_handler = get_text("registrationHandler")
    name = get_text("friendlyName") or file.stem

    # OIDC providers must have a RegistrationHandler
    if provider_type in ("OpenIdConnect", "CustomOAuth2"):
        if not registration_handler:
            issues.append(
                f"{name}: OIDC auth provider has no RegistrationHandler assigned. "
                "OIDC SSO cannot complete without one — assign a class implementing "
                "Auth.RegistrationHandler."
            )

    # SAML providers: remind operator to populate Federation ID
    if provider_type == "SAML2":
        issues.append(
            f"{name}: SAML auth provider detected. Verify that FederationIdentifier "
            "is populated on all affected User records before activating SSO. "
            "Use Setup > SAML Assertion Validator to confirm NameID matching."
        )

    return issues


def check_registration_handlers(manifest_dir: Path, auth_provider_files: list[Path]) -> list[str]:
    """Warn if RegistrationHandler class names referenced in auth providers are not found as Apex classes."""
    issues: list[str] = []

    # Collect referenced handler class names
    referenced_handlers: list[tuple[str, str]] = []
    for file in auth_provider_files:
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            continue
        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"
        handler_el = root.find(f"{ns}registrationHandler")
        if handler_el is not None and handler_el.text:
            referenced_handlers.append((file.stem, handler_el.text.strip()))

    if not referenced_handlers:
        return issues

    # Collect all Apex class names in manifest
    apex_files = {f.stem.lower() for f in manifest_dir.rglob("*.cls")}

    for provider_name, handler_name in referenced_handlers:
        if handler_name.lower() not in apex_files:
            issues.append(
                f"{provider_name}: RegistrationHandler '{handler_name}' is referenced "
                "but no matching .cls file found in the metadata directory. "
                "Ensure the class is included in the deployment package."
            )

    return issues


def check_community_parameter_hints(manifest_dir: Path) -> list[str]:
    """Scan LWC component HTML files for Start SSO URLs missing the community parameter."""
    issues: list[str] = []
    sso_url_fragment = "/services/auth/sso/"

    for html_file in manifest_dir.rglob("*.html"):
        try:
            content = html_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = content.splitlines()
        for lineno, line in enumerate(lines, start=1):
            if sso_url_fragment in line and "community=" not in line:
                issues.append(
                    f"{html_file.relative_to(manifest_dir)} line {lineno}: "
                    "Start SSO URL found without 'community=' parameter. "
                    "Add ?community=<site-base-url> to route the user back to the correct Experience Cloud site."
                )

    return issues


def check_experience_cloud_multi_idp_sso(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    auth_provider_files = find_auth_provider_files(manifest_dir)

    if not auth_provider_files:
        # Not necessarily an error — the user may not have retrieved auth providers
        return issues

    for apf in auth_provider_files:
        issues.extend(check_auth_provider(apf))

    issues.extend(check_registration_handlers(manifest_dir, auth_provider_files))
    issues.extend(check_community_parameter_hints(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_multi_idp_sso(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
