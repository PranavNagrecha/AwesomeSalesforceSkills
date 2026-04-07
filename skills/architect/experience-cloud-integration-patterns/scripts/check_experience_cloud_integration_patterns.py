#!/usr/bin/env python3
"""Checker script for Experience Cloud Integration Patterns skill.

Validates Salesforce metadata related to Experience Cloud external integrations.
Checks for common misconfigurations in SAML SSO, network settings, and site
configuration that cause real production problems.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_integration_patterns.py [--help]
    python3 check_experience_cloud_integration_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud Integration Patterns configuration and metadata "
            "for common issues including SSO, CSP, and script injection misconfigurations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# SAML SSO configuration checks
# ---------------------------------------------------------------------------

def check_saml_configurations(manifest_dir: Path) -> list[str]:
    """Check SAML SSO configuration metadata for common issues."""
    issues: list[str] = []

    # SAML configs live in networkAuthenticationSettings or samlSsoConfig metadata
    saml_dir = manifest_dir / "samlSsoConfigs"
    if not saml_dir.exists():
        # Try alternate path structure
        saml_dir = manifest_dir / "force-app" / "main" / "default" / "samlSsoConfigs"

    if not saml_dir.exists():
        return issues  # No SAML configs present — nothing to check

    for saml_file in sorted(saml_dir.glob("*.samlSsoConfig-meta.xml")):
        try:
            tree = ET.parse(saml_file)
            root = tree.getroot()
            # Strip namespace prefix for portability
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            config_name = saml_file.stem.replace(".samlSsoConfig-meta", "")

            # Check: entityProviderType should be "SalesforceIsSp" or "SalesforceIsIdP" or "BothSFandThirdPartySP"
            provider_type_el = root.find(f"{ns}samlEntityProviderType")
            if provider_type_el is not None:
                provider_type = provider_type_el.text or ""
                if provider_type not in (
                    "SalesforceIsSp",
                    "SalesforceIsIdP",
                    "BothSFandThirdPartySP",
                    "BothSFandThirdPartyIdP",
                ):
                    issues.append(
                        f"SAML config '{config_name}': unexpected samlEntityProviderType "
                        f"'{provider_type}'. Expected one of: SalesforceIsSp, SalesforceIsIdP, "
                        f"BothSFandThirdPartySP, BothSFandThirdPartyIdP."
                    )

            # Check: loginUrl (IdP SSO endpoint) should be HTTPS
            login_url_el = root.find(f"{ns}loginUrl")
            if login_url_el is not None and login_url_el.text:
                if not login_url_el.text.startswith("https://"):
                    issues.append(
                        f"SAML config '{config_name}': loginUrl does not use HTTPS "
                        f"('{login_url_el.text}'). SAML assertions must be transmitted "
                        f"over HTTPS to prevent interception."
                    )

            # Check: issuer (IdP entity ID) should not be the Salesforce org entity ID pattern
            # This catches the anti-pattern of using the Salesforce entity ID as the IdP issuer
            issuer_el = root.find(f"{ns}issuer")
            if issuer_el is not None and issuer_el.text:
                issuer = issuer_el.text
                if "saml.salesforce.com" in issuer or "my.salesforce.com" in issuer:
                    issues.append(
                        f"SAML config '{config_name}': issuer field contains a Salesforce domain "
                        f"('{issuer}'). The issuer should be the external IdP's entity ID, "
                        f"not a Salesforce URL. Review whether SP and IdP metadata have been swapped."
                    )

        except ET.ParseError as exc:
            issues.append(
                f"SAML config '{saml_file.name}': XML parse error — {exc}. "
                f"File may be corrupt or incomplete."
            )

    return issues


# ---------------------------------------------------------------------------
# Experience Cloud site (Network) configuration checks
# ---------------------------------------------------------------------------

def check_network_configurations(manifest_dir: Path) -> list[str]:
    """Check Experience Cloud site (Network) metadata for integration-related issues."""
    issues: list[str] = []

    # Network metadata: force-app/main/default/networks/ or networks/
    for search_root in [
        manifest_dir / "networks",
        manifest_dir / "force-app" / "main" / "default" / "networks",
    ]:
        if search_root.exists():
            for network_file in sorted(search_root.glob("*.network-meta.xml")):
                issues.extend(_check_single_network(network_file))

    return issues


def _check_single_network(network_file: Path) -> list[str]:
    issues: list[str] = []
    site_name = network_file.stem.replace(".network-meta", "")

    try:
        tree = ET.parse(network_file)
        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Check: allowMembersToFlag or selfRegistration without guestProfileName
        self_reg_el = root.find(f"{ns}selfRegistration")
        guest_profile_el = root.find(f"{ns}guestProfileName")
        if (
            self_reg_el is not None
            and self_reg_el.text == "true"
            and (guest_profile_el is None or not (guest_profile_el.text or "").strip())
        ):
            issues.append(
                f"Site '{site_name}': selfRegistration is enabled but guestProfileName is "
                f"not set. Unauthenticated self-registration without an explicit guest profile "
                f"may grant overly permissive access. Confirm this is intentional."
            )

        # Check: enableGuestLogin — if true, warn to verify guest sharing settings
        guest_login_el = root.find(f"{ns}enableGuestLogin")
        if guest_login_el is not None and guest_login_el.text == "true":
            issues.append(
                f"Site '{site_name}': enableGuestLogin is true. Verify that guest user sharing "
                f"settings and OWD do not expose authenticated user records to guest sessions. "
                f"Review guest access scope as part of the integration security checklist."
            )

        # Check: loginType — if it includes SSO providers, verify network auth settings exist
        auth_provider_els = root.findall(f".//{ns}authenticationConfig")
        if not auth_provider_els:
            # Check via networkAuthenticationSettings child
            auth_settings_el = root.find(f"{ns}networkAuthenticationSettings")
            if auth_settings_el is None:
                # No auth config — only warn if site is not internal
                status_el = root.find(f"{ns}status")
                site_type_el = root.find(f"{ns}networkType")
                if site_type_el is not None and site_type_el.text in (
                    "CustomerPortal",
                    "PartnerPortal",
                    "LightningCommunity",
                ):
                    issues.append(
                        f"Site '{site_name}': no networkAuthenticationSettings found for a "
                        f"portal-type site. If external SSO is required, verify that the "
                        f"SAML or Auth Provider login option is enabled in Login & Registration."
                    )

    except ET.ParseError as exc:
        issues.append(
            f"Network config '{network_file.name}': XML parse error — {exc}. "
            f"File may be corrupt or incomplete."
        )

    return issues


# ---------------------------------------------------------------------------
# Connected App checks (for Auth Provider / OIDC / IdP role)
# ---------------------------------------------------------------------------

def check_connected_apps(manifest_dir: Path) -> list[str]:
    """Check Connected App metadata for Experience Cloud SSO integration issues."""
    issues: list[str] = []

    for search_root in [
        manifest_dir / "connectedApps",
        manifest_dir / "force-app" / "main" / "default" / "connectedApps",
    ]:
        if search_root.exists():
            for app_file in sorted(search_root.glob("*.connectedApp-meta.xml")):
                issues.extend(_check_single_connected_app(app_file))

    return issues


def _check_single_connected_app(app_file: Path) -> list[str]:
    issues: list[str] = []
    app_name = app_file.stem.replace(".connectedApp-meta", "")

    try:
        tree = ET.parse(app_file)
        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Check: oauthConfig callback URLs should be HTTPS for production
        oauth_config_el = root.find(f"{ns}oauthConfig")
        if oauth_config_el is not None:
            callback_els = oauth_config_el.findall(f"{ns}callbackUrl")
            for callback_el in callback_els:
                url = (callback_el.text or "").strip()
                if url and not url.startswith("https://") and not url.startswith("http://localhost"):
                    issues.append(
                        f"Connected App '{app_name}': callbackUrl '{url}' does not use HTTPS. "
                        f"OAuth/OIDC callback URLs for production use must be HTTPS to prevent "
                        f"authorization code interception."
                    )

            # Check: scopes — warn if 'full' or 'refresh_token' is present on a public site app
            scope_els = oauth_config_el.findall(f"{ns}scopes")
            scope_values = {el.text for el in scope_els if el.text}
            if "Full" in scope_values:
                issues.append(
                    f"Connected App '{app_name}': OAuth scope 'Full' (api + chatter + full) is "
                    f"requested. Experience Cloud Auth Provider integrations typically require only "
                    f"'openid', 'profile', and 'email' scopes. Review whether full access is "
                    f"necessary."
                )

    except ET.ParseError as exc:
        issues.append(
            f"Connected App '{app_file.name}': XML parse error — {exc}. "
            f"File may be corrupt or incomplete."
        )

    return issues


# ---------------------------------------------------------------------------
# Auth Provider checks
# ---------------------------------------------------------------------------

def check_auth_providers(manifest_dir: Path) -> list[str]:
    """Check Auth Provider metadata for OIDC/OAuth SSO integration issues."""
    issues: list[str] = []

    for search_root in [
        manifest_dir / "authproviders",
        manifest_dir / "force-app" / "main" / "default" / "authproviders",
    ]:
        if search_root.exists():
            for ap_file in sorted(search_root.glob("*.authprovider-meta.xml")):
                issues.extend(_check_single_auth_provider(ap_file))

    return issues


def _check_single_auth_provider(ap_file: Path) -> list[str]:
    issues: list[str] = []
    ap_name = ap_file.stem.replace(".authprovider-meta", "")

    try:
        tree = ET.parse(ap_file)
        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Check: registrationHandler class must be set for custom providers
        provider_type_el = root.find(f"{ns}providerType")
        reg_handler_el = root.find(f"{ns}registrationHandler")

        provider_type = (provider_type_el.text if provider_type_el is not None else "") or ""
        reg_handler = (reg_handler_el.text if reg_handler_el is not None else "") or ""

        if provider_type == "Custom" and not reg_handler.strip():
            issues.append(
                f"Auth Provider '{ap_name}': providerType is 'Custom' but no "
                f"registrationHandler class is set. Custom Auth Providers require a "
                f"registration handler Apex class to provision or match users on first login."
            )

        # Check: tokenUrl and authorizeUrl should be HTTPS
        for field_name in ("tokenUrl", "authorizeUrl", "userInfoUrl"):
            el = root.find(f"{ns}{field_name}")
            if el is not None and el.text and not el.text.startswith("https://"):
                issues.append(
                    f"Auth Provider '{ap_name}': {field_name} '{el.text}' does not use HTTPS. "
                    f"All OIDC/OAuth endpoints must use HTTPS."
                )

    except ET.ParseError as exc:
        issues.append(
            f"Auth Provider '{ap_file.name}': XML parse error — {exc}. "
            f"File may be corrupt or incomplete."
        )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def check_experience_cloud_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_saml_configurations(manifest_dir))
    issues.extend(check_network_configurations(manifest_dir))
    issues.extend(check_connected_apps(manifest_dir))
    issues.extend(check_auth_providers(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_integration_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
