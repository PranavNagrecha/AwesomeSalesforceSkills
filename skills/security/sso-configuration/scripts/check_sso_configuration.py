#!/usr/bin/env python3
"""check_sso_configuration.py — SSO metadata shape checker.

Scans a Salesforce metadata directory for SamlSsoConfig (.samlssoconfig) and
AuthProvider (.authprovider) components and reports configurations that cannot
work, or that are documented as one-way / legacy choices.

ERROR rules map to a documented field constraint in the Metadata API Developer
Guide. ADVISORY rules cover documented-but-legal choices that are rarely
intended, plus a small number of judgement calls; each rule's text says which
of the two it is:

  SamlSsoConfig  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_samlssoconfig.htm
  AuthProvider   https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_authproviders.htm

Severities:
  ERROR    the configuration is invalid or cannot authenticate anyone. Exit 1.
  ADVISORY a documented legacy or default value that is almost never intended.
           Reported, but only fails the run under --strict.

Uses stdlib only — no pip dependencies. Python 3.8+.

Usage:
    python3 check_sso_configuration.py --manifest-dir force-app/main/default
    python3 check_sso_configuration.py --manifest-dir . --strict
    python3 check_sso_configuration.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ERROR = "ERROR"
ADVISORY = "ADVISORY"

# SamlSsoConfig enumerations, as documented.
SAML_IDENTITY_TYPES = {"Username", "FederationId", "UserId"}
SAML_IDENTITY_LOCATIONS = {"SubjectNameId", "Attribute"}
SAML_VERSIONS = {"SAML1_1", "SAML2_0"}
SIGNATURE_METHODS = {"RSA-SHA1", "RSA-SHA256"}
SLO_BINDINGS = {"RedirectBinding", "PostBinding"}

# AuthProviderType enumeration, as documented.
AUTH_PROVIDER_TYPES = {
    "Apple", "Bitbucket", "Custom", "Facebook", "GitHub", "Google", "Janrain",
    "LinkedIn", "Microsoft", "MicrosoftACS", "MuleSoft", "OpenIdConnect",
    "Salesforce", "Slack", "Twitter",
}

# Hosts that always sit behind an authenticated Salesforce session. A browser
# reaching errorUrl has just failed to authenticate, so these cannot render.
AUTHENTICATED_SALESFORCE_HOSTS = (
    ".my.salesforce.com", ".lightning.force.com", ".visualforce.com",
    ".my.salesforce-setup.com", ".content.force.com",
)

# Hosts that MAY be anonymous (Experience Cloud sites, Salesforce Sites). The
# Metadata API names "a public site Visualforce page" as an acceptable errorUrl,
# so these cannot be rejected on hostname alone - only flagged for verification.
MAYBE_PUBLIC_SALESFORCE_HOSTS = (
    ".force.com", ".site.com", ".salesforce-sites.com", ".sfdcsites.com",
    ".salesforce.com",
)

# The documented default of SamlSsoConfig.logoutUrl.
DEFAULT_LOGOUT_URL = "https://salesforce.com"

# Where the two component types live, in both MDAPI and SFDX layouts.
SAML_DIRS = ("samlssoconfigs", "force-app/main/default/samlssoconfigs")
AUTHPROVIDER_DIRS = ("authproviders", "force-app/main/default/authproviders")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce SSO metadata (SamlSsoConfig, AuthProvider) for "
            "configurations that cannot authenticate anyone, and for documented "
            "legacy or one-way settings."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce project or metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat ADVISORY findings as failures too.",
    )
    return parser.parse_args()


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def read_fields(path: Path) -> "dict[str, str] | None":
    """Flatten a metadata XML file's top-level elements into {tag: text}.

    Returns None when the file cannot be parsed, so the caller can report the
    parse failure rather than silently skipping a component.
    """
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    fields: "dict[str, str]" = {}
    for child in root:
        tag = strip_ns(child.tag)
        text = (child.text or "").strip()
        if tag not in fields:
            fields[tag] = text
    return fields


def is_true(value: str) -> bool:
    return value.strip().lower() == "true"


def classify_error_url(url: str) -> str:
    """Classify an errorUrl as 'authenticated', 'maybe-public' or 'external'.

    The Metadata API requires errorUrl to be publicly accessible and offers
    "a public site Visualforce page" as an example of one that is. So the
    discriminator is anonymous reachability, not Salesforce ownership of the
    host: only hosts that ALWAYS require a session are a hard error.
    """
    lowered = url.strip().lower()
    if not lowered:
        return "external"
    if not lowered.startswith(("http://", "https://")):
        # "The URL can be absolute or relative." A relative URL resolves against
        # a Salesforce host, so it needs the same anonymous-access check.
        return "maybe-public"
    host = lowered.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]
    if any(host.endswith(suffix) for suffix in AUTHENTICATED_SALESFORCE_HOSTS):
        return "authenticated"
    if any(host.endswith(suffix) for suffix in MAYBE_PUBLIC_SALESFORCE_HOSTS):
        return "maybe-public"
    return "external"


def check_saml_config(name: str, f: "dict[str, str]") -> "list[tuple[str, str]]":
    """Rules for one SamlSsoConfig component."""
    out: "list[tuple[str, str]]" = []

    version = f.get("samlVersion", "")
    if version and version not in SAML_VERSIONS:
        out.append((ERROR, f"{name}: samlVersion '{version}' is not one of {sorted(SAML_VERSIONS)}."))
    elif version == "SAML1_1":
        out.append((ADVISORY, f"{name}: samlVersion is SAML1_1. Fields documented "
                              "'For SAML 2.0 only' (loginUrl, logoutUrl, oauthTokenEndpoint) "
                              "will not apply. Use SAML2_0 for new configurations."))

    mapping = f.get("identityMapping", "")
    if not mapping:
        out.append((ERROR, f"{name}: identityMapping is missing. Salesforce cannot resolve "
                           "the assertion subject to a User record."))
    elif mapping not in SAML_IDENTITY_TYPES:
        out.append((ERROR, f"{name}: identityMapping '{mapping}' is not a SamlIdentityType "
                           f"value {sorted(SAML_IDENTITY_TYPES)}. Setup labels such as "
                           "'Federation ID' are not valid metadata values."))

    location = f.get("identityLocation", "")
    if location and location not in SAML_IDENTITY_LOCATIONS:
        out.append((ERROR, f"{name}: identityLocation '{location}' is not a "
                           f"SamlIdentityLocationType value {sorted(SAML_IDENTITY_LOCATIONS)}."))
    if location == "Attribute" and not f.get("attributeName"):
        out.append((ADVISORY, f"{name}: identityLocation is Attribute but attributeName is empty. "
                              "The Metadata API does not mark attributeName Required here, so "
                              "this is a judgement call - but an attribute-located identity with "
                              "nothing named is almost always incomplete. Confirm against the "
                              "identity provider."))

    if not f.get("validationCert"):
        out.append((ERROR, f"{name}: validationCert is missing. Without the identity provider's "
                           "signing certificate no inbound assertion can be validated."))

    if f.get("samlJitHandlerId") and not f.get("executionUserId"):
        out.append((ERROR, f"{name}: samlJitHandlerId is set but executionUserId is empty. "
                           "The Apex handler needs a run-as user holding Manage Users."))

    # The Metadata API attaches a prerequisite to userProvisioning: "Specify
    # Federation ID for the identityMapping value to use this feature." With no
    # handler that is standard JIT, which the platform cannot perform - a hard
    # error. With a handler, the Apex resolves identity itself and the config
    # still authenticates, so the documented mismatch is reported but does not
    # meet this script's ERROR bar ("cannot authenticate anyone").
    if is_true(f.get("userProvisioning", "")) and mapping and mapping != "FederationId":
        doc = ('The Metadata API documents this feature as requiring Federation ID: '
               '"Specify Federation ID for the identityMapping value to use this feature."')
        if f.get("samlJitHandlerId"):
            out.append((ADVISORY, f"{name}: userProvisioning is true with identityMapping "
                                  f"'{mapping}'. {doc} An Apex JIT handler is set, so the handler "
                                  "must resolve identity itself - confirm that is deliberate."))
        else:
            out.append((ERROR, f"{name}: userProvisioning is true but identityMapping is "
                               f"'{mapping}' and no samlJitHandlerId is set. {doc}"))

    error_url = f.get("errorUrl", "")
    if error_url:
        kind = classify_error_url(error_url)
        if kind == "authenticated":
            out.append((ERROR, f"{name}: errorUrl ({error_url}) is on a host that always requires "
                               "an authenticated Salesforce session. It is reached by a browser "
                               "that has just failed to authenticate, so the login error becomes "
                               "a redirect loop. The Metadata API requires errorUrl to be "
                               "publicly accessible."))
        elif kind == "maybe-public":
            out.append((ADVISORY, f"{name}: errorUrl ({error_url}) is Salesforce-hosted or "
                                  "relative. That is permitted - the Metadata API names 'a public "
                                  "site Visualforce page' as an example - but only if guest access "
                                  "is actually enabled. Open it in a session-free browser to "
                                  "confirm before relying on it."))

    logout_url = f.get("logoutUrl", "")
    if logout_url.rstrip("/").lower() == DEFAULT_LOGOUT_URL:
        out.append((ADVISORY, f"{name}: logoutUrl is still the documented default "
                              f"'{DEFAULT_LOGOUT_URL}'. Users clicking Logout land on a generic "
                              "page while the identity provider session stays live."))

    method = f.get("requestSignatureMethod", "")
    if method and method not in SIGNATURE_METHODS:
        out.append((ERROR, f"{name}: requestSignatureMethod '{method}' is not one of "
                           f"{sorted(SIGNATURE_METHODS)}."))
    elif method == "RSA-SHA1":
        out.append((ADVISORY, f"{name}: requestSignatureMethod is RSA-SHA1. Use RSA-SHA256 "
                              "unless the identity provider has a documented limitation."))

    binding = f.get("singleLogoutBinding", "")
    if binding and binding not in SLO_BINDINGS:
        out.append((ERROR, f"{name}: singleLogoutBinding '{binding}' is not one of "
                           f"{sorted(SLO_BINDINGS)}."))

    if not f.get("loginUrl") and version != "SAML1_1":
        out.append((ADVISORY, f"{name}: loginUrl is empty, so SP-initiated login is not "
                              "configured. Deep links and email links will not return the "
                              "user to the requested record."))

    return out


def check_auth_provider(name: str, f: "dict[str, str]") -> "list[tuple[str, str]]":
    """Rules for one AuthProvider component."""
    out: "list[tuple[str, str]]" = []

    if not f.get("friendlyName"):
        out.append((ERROR, f"{name}: friendlyName is missing and is documented Required."))

    provider_type = f.get("providerType", "")
    if not provider_type:
        out.append((ERROR, f"{name}: providerType is missing and is documented Required."))
    elif provider_type not in AUTH_PROVIDER_TYPES:
        out.append((ERROR, f"{name}: providerType '{provider_type}' is not an AuthProviderType "
                           f"value {sorted(AUTH_PROVIDER_TYPES)}."))

    if provider_type == "OpenIdConnect":
        for required in ("authorizeUrl", "tokenUrl", "userInfoUrl"):
            if not f.get(required):
                out.append((ERROR, f"{name}: providerType OpenIdConnect requires {required}."))
        if "sendClientCredentialsInHeader" not in f:
            out.append((ERROR, f"{name}: providerType OpenIdConnect requires "
                               "sendClientCredentialsInHeader."))
        if not f.get("idTokenIssuer"):
            out.append((ADVISORY, f"{name}: idTokenIssuer is empty. The Metadata API does not "
                                  "mark it Required, but it is 'the source of the authentication "
                                  "token in https: URI format' that the returned id_token is "
                                  "validated against."))

    handler = f.get("registrationHandler", "")
    flow = f.get("flow", "")
    if handler and flow:
        out.append((ERROR, f"{name}: both registrationHandler and flow are set. The Metadata API "
                           "documents these as mutually exclusive — use one."))
    if (handler or flow) and not f.get("executionUser"):
        out.append((ERROR, f"{name}: a registration handler is configured but executionUser is "
                           "empty. The handler runs as that user, who must hold Manage Users."))
    if flow and not f.get("flowDefaultProfile"):
        out.append((ADVISORY, f"{name}: a flow registration handler is configured without "
                              "flowDefaultProfile. The Metadata API does not mark it Required, "
                              "but it is the default profile new users are assigned - leaving it "
                              "unset puts that assignment entirely on the flow."))

    if is_true(f.get("includeOrgIdInIdentifier", "")):
        out.append((ADVISORY, f"{name}: includeOrgIdInIdentifier is enabled. This is documented "
                              "as not disableable once enabled — confirm it is intended before "
                              "deploying to an org that already has third-party account links."))

    secret = f.get("consumerSecret", "")
    if len(secret) > 24 and not secret.startswith("***"):
        out.append((ADVISORY, f"{name}: consumerSecret carries a long literal value. Salesforce "
                              "exports this field as a placeholder; a real secret in source "
                              "control should be [REDACTED] and injected at deploy time."))

    return out


def collect_files(base: Path, subdirs: "tuple[str, ...]", suffix: str) -> "list[Path]":
    found: "list[Path]" = []
    for subdir in subdirs:
        candidate = base / subdir
        if candidate.is_dir():
            found.extend(sorted(candidate.glob(f"*{suffix}*.xml")))
            found.extend(sorted(candidate.glob(f"*{suffix}")))
    # De-duplicate while preserving order.
    seen: "set[Path]" = set()
    unique: "list[Path]" = []
    for path in found:
        if path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


def run(manifest_dir: Path) -> "tuple[list[tuple[str, str]], int]":
    findings: "list[tuple[str, str]]" = []

    saml_files = collect_files(manifest_dir, SAML_DIRS, ".samlssoconfig")
    provider_files = collect_files(manifest_dir, AUTHPROVIDER_DIRS, ".authprovider")

    for path in saml_files:
        fields = read_fields(path)
        if fields is None:
            findings.append((ERROR, f"{path.name}: file is not parseable XML."))
            continue
        findings.extend(check_saml_config(path.name, fields))

    for path in provider_files:
        fields = read_fields(path)
        if fields is None:
            findings.append((ERROR, f"{path.name}: file is not parseable XML."))
            continue
        findings.extend(check_auth_provider(path.name, fields))

    return findings, len(saml_files) + len(provider_files)


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 1

    findings, checked = run(manifest_dir)

    if checked == 0:
        print(
            "No SamlSsoConfig (.samlssoconfig) or AuthProvider (.authprovider) components "
            f"found under {manifest_dir}. Nothing to check.\n"
            "Retrieve them first, e.g.:\n"
            "  sf project retrieve start -m SamlSsoConfig -m AuthProvider"
        )
        return 0

    errors = [msg for sev, msg in findings if sev == ERROR]
    advisories = [msg for sev, msg in findings if sev == ADVISORY]

    for msg in errors:
        print(f"ERROR: {msg}", file=sys.stderr)
    for msg in advisories:
        print(f"ADVISORY: {msg}", file=sys.stderr)

    print(
        f"\nChecked {checked} component(s): {len(errors)} error(s), "
        f"{len(advisories)} advisory(ies)."
    )

    if errors:
        return 1
    if advisories and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
