#!/usr/bin/env python3
"""Checker script for Named Credentials Setup skill.

Reads *.namedCredential-meta.xml, *.externalCredential-meta.xml and
*.permissionset-meta.xml under --manifest-dir (any layout). Stdlib only.
Premises come from Metadata API 264 (cited as meta 264 L<n>):

  ERROR  a file that does not parse.
  ERROR  ExternalCredential without authenticationProtocol or label (Required,
         L66185, L66217), with a protocol outside AwsSv4, Basic, Custom, Jwt,
         JwtExchange, NoAuthentication, Oauth, Password (L66186-66197), or a
         parameterType outside the documented list (L66295-66356).
  ERROR  NamedCredential of type PrivateEndpoint without an
         OutboundNetworkConnection parameter (L92877-92880).
  ERROR  PermissionSet externalCredentialPrincipal not in the form
         ExternalCredential-Principal (L97696-97698).
  WARN   protocol Jwt, JwtExchange, NoAuthentication or Password ("Reserved for
         future use", L66193-66197) and internal-only parameter types.
  WARN   ExternalCredential with no NamedPrincipal or PerUserPrincipal
         parameter (L66348-66350); a sequenceNumber on a PerUserPrincipal
         (only valid for NamedPrincipal, L66391); a `principal` element on a
         parameter (removed in API 58.0, L66364-66383).
  WARN   NamedCredential of type Legacy (fields deprecated in API 56.0,
         L92874-92876), SecuredEndpoint without a Url or Authentication
         parameter (L93044-93087), legacy-only elements on a non-Legacy type
         (L92679), an Authentication reference to an ExternalCredential file
         that is not in the directory, a placeholder-looking URL.
  WARN   when permission-set files are present: a principal that no
         externalCredentialPrincipalAccesses entry enables (L97687-97704).

A URL ending in "/" is not flagged: the guide's own example ends with "/"
(L93128).

Exit codes: ERROR findings exit 1 always; WARN findings exit 0 unless
--strict; a directory with none of these files prints one WARN and exits 0; a
missing directory is an ERROR and exits 1.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROTOCOLS = {"AwsSv4", "Basic", "Custom", "Jwt", "JwtExchange", "NoAuthentication", "Oauth", "Password"}
RESERVED_PROTOCOLS = {"Jwt", "JwtExchange", "NoAuthentication", "Password"}
EC_PARAM_TYPES = {
    "AdditionalRefreshStatusCode", "AuthHeader", "AuthParameter", "AuthProtocolVariant", "AuthProvider",
    "AuthProviderUrl", "AuthProviderUrlQueryParameter", "AwsStsPrincipal", "CreatedByNamespace", "CustomPrincipal",
    "ExternalAuthIdentityProvider", "GlobalNamedPrincipal", "JwtBodyClaim", "JwtHeaderClaim", "ManagedByComponent",
    "ManagedByFeature", "NamedPrincipal", "PerUserPrincipal", "PrincipalIdentityAlias", "SfHttpRequestExtensionName",
    "SigningCertificate", "SystemUserPrincipal",
}
INTERNAL_EC_PARAM_TYPES = {
    "CreatedByNamespace", "CustomPrincipal", "GlobalNamedPrincipal", "ManagedByComponent", "ManagedByFeature",
    "PrincipalIdentityAlias", "SfHttpRequestExtensionName", "SystemUserPrincipal",
}
LEGACY_ONLY = ("endpoint", "principalType", "protocol", "username", "password", "oauthScope", "authProvider")
PLACEHOLDERS = ("localhost", "todo", "placeholder")


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def kids(e: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in e if local(c.tag) == name]


def text(e: ET.Element, name: str) -> str:
    for c in kids(e, name):
        if c.text:
            return c.text.strip()
    return ""


def stem(path: Path, suffix: str) -> str:
    return path.name[: -len(suffix)]


def check_nc(path: Path, ec_names: set[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"{path}: does not parse ({exc})")]
    params = kids(root, "namedCredentialParameters")
    nc_type = text(root, "namedCredentialType") or ("Legacy" if not params else "SecuredEndpoint")
    if nc_type == "Legacy":
        out.append(("WARN", f"{path}: Legacy Named Credential; its fields are deprecated in API 56.0, plan a migration to SecuredEndpoint"))
        return out
    legacy = [n for n in LEGACY_ONLY if kids(root, n)]
    if legacy:
        out.append(("WARN", f"{path}: legacy-only element(s) {legacy} on a {nc_type} credential; they are valid only for type Legacy"))
    by_type: dict[str, list[ET.Element]] = {}
    for p in params:
        by_type.setdefault(text(p, "parameterType"), []).append(p)
    if nc_type == "PrivateEndpoint" and "OutboundNetworkConnection" not in by_type:
        out.append(("ERROR", f"{path}: PrivateEndpoint credential without an OutboundNetworkConnection parameter"))
    if nc_type == "SecuredEndpoint":
        if "Url" not in by_type:
            out.append(("WARN", f"{path}: SecuredEndpoint credential without a Url parameter"))
        if "Authentication" not in by_type:
            out.append(("WARN", f"{path}: SecuredEndpoint credential without an Authentication parameter (no External Credential reference)"))
    for p in by_type.get("Authentication", []):
        ref = text(p, "externalCredential")
        if ref and ec_names and ref not in ec_names:
            out.append(("WARN", f"{path}: Authentication parameter references External Credential '{ref}' which is not in the directory"))
    for p in by_type.get("Url", []):
        url = text(p, "parameterValue").lower()
        if any(m in url for m in PLACEHOLDERS):
            out.append(("WARN", f"{path}: URL '{url}' looks like a placeholder"))
    return out


def check_ec(path: Path) -> tuple[list[tuple[str, str]], list[str]]:
    """Return (findings, principal keys 'ECName-Principal')."""
    out: list[tuple[str, str]] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"{path}: does not parse ({exc})")], []
    ec_name = stem(path, ".externalCredential-meta.xml")
    proto = text(root, "authenticationProtocol")
    if not proto:
        out.append(("ERROR", f"{path}: authenticationProtocol is required"))
    elif proto not in PROTOCOLS:
        out.append(("ERROR", f"{path}: authenticationProtocol '{proto}' is not one of {sorted(PROTOCOLS)}"))
    elif proto in RESERVED_PROTOCOLS:
        out.append(("WARN", f"{path}: authenticationProtocol '{proto}' is 'Reserved for future use'"))
    if not text(root, "label"):
        out.append(("ERROR", f"{path}: label is required"))
    principals: list[str] = []
    for p in kids(root, "externalCredentialParameters"):
        ptype, pname = text(p, "parameterType"), text(p, "parameterName")
        if ptype and ptype not in EC_PARAM_TYPES:
            out.append(("ERROR", f"{path}: parameterType '{ptype}' is not a documented ExternalCredentialParamType"))
        elif ptype in INTERNAL_EC_PARAM_TYPES:
            out.append(("WARN", f"{path}: parameterType '{ptype}' is reserved for internal use"))
        if ptype in ("NamedPrincipal", "PerUserPrincipal"):
            principals.append(f"{ec_name}-{pname}")
            if kids(p, "principal"):
                out.append(("WARN", f"{path}: principal '{pname}' sets a `principal` element; that field is removed in API 58.0, use PermissionSet externalCredentialPrincipalAccesses"))
        if ptype == "PerUserPrincipal" and kids(p, "sequenceNumber"):
            out.append(("WARN", f"{path}: sequenceNumber on PerUserPrincipal '{pname}'; it can be set only for NamedPrincipal"))
    if not principals:
        out.append(("WARN", f"{path}: no NamedPrincipal or PerUserPrincipal parameter; no one can authenticate"))
    return out, principals


def check_ps(path: Path) -> tuple[list[tuple[str, str]], set[str]]:
    out: list[tuple[str, str]] = []
    enabled: set[str] = set()
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [("ERROR", f"{path}: does not parse ({exc})")], enabled
    for acc in kids(root, "externalCredentialPrincipalAccesses"):
        key = text(acc, "externalCredentialPrincipal")
        if "-" not in key:
            out.append(("ERROR", f"{path}: externalCredentialPrincipal '{key}' must be ExternalCredential-Principal"))
        if text(acc, "enabled").lower() == "true":
            enabled.add(key)
    return out, enabled


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Named Credential / External Credential metadata.")
    ap.add_argument("--manifest-dir", default=".", help="Root of the metadata tree (default: .).")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    args = ap.parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    ncs = sorted(root.rglob("*.namedCredential-meta.xml"))
    ecs = sorted(root.rglob("*.externalCredential-meta.xml"))
    pss = sorted(root.rglob("*.permissionset-meta.xml"))
    if not (ncs or ecs):
        print(f"WARN: no namedCredential or externalCredential files under {root}; nothing to check")
        return 0
    findings: list[tuple[str, str]] = []
    ec_names = {stem(p, ".externalCredential-meta.xml") for p in ecs}
    principals: list[tuple[Path, str]] = []
    for p in ecs:
        f, pr = check_ec(p)
        findings.extend(f)
        principals.extend((p, k) for k in pr)
    for p in ncs:
        findings.extend(check_nc(p, ec_names))
    enabled: set[str] = set()
    for p in pss:
        f, e = check_ps(p)
        findings.extend(f)
        enabled |= e
    if pss:
        for p, key in principals:
            if key not in enabled:
                findings.append(("WARN", f"{p}: principal '{key}' is not enabled by any permission set in the directory"))
    for level, msg in findings:
        print(f"{level}: {msg}")
    if not findings:
        print("No issues found in Named Credential / External Credential metadata.")
    has_error = any(lv == "ERROR" for lv, _ in findings)
    has_warn = any(lv == "WARN" for lv, _ in findings)
    return 1 if has_error or (args.strict and has_warn) else 0


if __name__ == "__main__":
    sys.exit(main())
