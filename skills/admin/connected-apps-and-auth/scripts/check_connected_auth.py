#!/usr/bin/env python3
"""Audit connected-app, External Client App, and Named/External Credential metadata.

Two modes:

``--manifest-dir <dir>``
    Parse the retrieved or source-format metadata tree with ElementTree and check the
    configuration mistakes that deploy cleanly and then behave wrong:

    * ERROR  ``isAdminApproved`` true with neither ``permissionSetName`` nor ``profileName``
             (the app is pre-authorized for nobody).
    * ERROR  a ``callbackUrl`` value using ``http://``.
    * WARN   ``scopes`` containing ``Full`` alongside narrower scopes.
    * WARN   ``refreshTokenPolicy`` left at ``infinite``.
    * WARN   ``ipRelaxation`` set to ``BYPASS``.
    * WARN   a NamedCredential referencing an ExternalCredential that is not in the tree.
    * INFO   a server-to-server-shaped app with no ``certificate``.

``<paths...>`` (positional, unchanged)
    Text scan of arbitrary files for hardcoded secrets, direct endpoints, and
    username-password flow references. Emits the JSON envelope.

Stdlib only.

Usage:
    python3 check_connected_auth.py --manifest-dir force-app/main/default
    python3 check_connected_auth.py force-app/main/default/classes
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

TEXT_SUFFIXES = {".xml", ".json", ".cls", ".trigger", ".js", ".ts", ".md", ".txt"}
DIRECT_ENDPOINT_PATTERN = re.compile(r"setEndpoint\(\s*['\"]https?://", re.IGNORECASE)
SECRET_PATTERN = re.compile(
    r"authorization:\s*bearer\s+[A-Za-z0-9._-]+|client[_-]?secret|consumersecret|password\s*=",
    re.IGNORECASE,
)
SEVERITY_WEIGHTS = {
    "CRITICAL": 20,
    "ERROR": 20,
    "HIGH": 10,
    "WARN": 5,
    "MEDIUM": 5,
    "LOW": 1,
    "INFO": 0,
    "REVIEW": 0,
}

# Scopes that signal a headless / API integration rather than a UI app. An app carrying
# these and no certificate is probably relying on a shared secret instead of a key pair.
SERVER_TO_SERVER_SCOPES = {"api", "cdpingest", "cdpquery", "cdpprofile", "sfapiplatform"}

# Scopes that only make sense when a person is completing a login. Their presence — like
# isPkceRequired, which the guide ties to "variations of the OAuth 2.0 authorization code
# flow" — means the app is user-delegated, so a signing certificate is not expected.
USER_DELEGATED_SCOPES = {
    "openid",
    "profile",
    "email",
    "address",
    "phone",
    "basic",
    "web",
    "lightning",
    "content",
    "customapplications",
}


# --------------------------------------------------------------------------- XML helpers

def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def _find(parent: ET.Element, name: str) -> ET.Element | None:
    """Namespaced-or-bare child lookup.

    Never write ``parent.find(a) or parent.find(b)``: a leaf Element is falsy, so a
    found-but-childless node is silently discarded. Test ``is not None`` explicitly.
    """
    found = parent.find(_tag(name))
    if found is not None:
        return found
    return parent.find(name)


def _findall(parent: ET.Element, name: str) -> list[ET.Element]:
    found = parent.findall(_tag(name))
    if found:
        return found
    return parent.findall(name)


def _text(parent: ET.Element, name: str) -> str | None:
    element = _find(parent, name)
    if element is None or element.text is None:
        return None
    stripped = element.text.strip()
    return stripped or None


def _texts(parent: ET.Element, name: str) -> list[str]:
    values: list[str] = []
    for element in _findall(parent, name):
        if element.text is not None and element.text.strip():
            values.append(element.text.strip())
    return values


def _local_name(element: ET.Element) -> str:
    return element.tag.split("}")[-1]


# --------------------------------------------------------------------------- discovery

def find_metadata_files(root: Path, suffix: str) -> list[Path]:
    return sorted(path for path in root.rglob(f"*{suffix}") if path.is_file())


def collect_external_credential_names(root: Path) -> set[str]:
    """API names of every ExternalCredential in the tree (file stem before the suffix)."""
    names: set[str] = set()
    for path in find_metadata_files(root, ".externalCredential-meta.xml"):
        names.add(path.name.split(".externalCredential")[0])
    for path in find_metadata_files(root, ".externalCredential"):
        names.add(path.name.split(".externalCredential")[0])
    return names


# --------------------------------------------------------------------------- checks

def check_connected_app(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"ERROR {path}: not well-formed XML ({exc})"]

    oauth_config = _find(root, "oauthConfig")
    oauth_policy = _find(root, "oauthPolicy")

    # --- admin-approved without a grantee -----------------------------------------
    if oauth_config is not None:
        admin_approved = (_text(oauth_config, "isAdminApproved") or "false").lower() == "true"
        permission_sets = _texts(root, "permissionSetName")
        profiles = _texts(root, "profileName")
        if admin_approved and not permission_sets and not profiles:
            findings.append(
                f"ERROR {path}: isAdminApproved is true but neither permissionSetName nor "
                "profileName is set; the app is pre-authorized for nobody. Ship the access "
                "grant in the same file."
            )

        # --- Full alongside narrower scopes ---------------------------------------
        scopes = [scope.strip() for scope in _texts(oauth_config, "scopes")]
        lowered = {scope.lower() for scope in scopes}
        if "full" in lowered and len(lowered) > 1:
            others = sorted(scope for scope in scopes if scope.lower() != "full")
            findings.append(
                f"WARN {path}: scopes include Full alongside {', '.join(others)}; Full already "
                "grants all data accessible to the running user, so the narrower scopes are "
                "cosmetic. Drop Full or drop the others."
            )

        # --- http:// callback ------------------------------------------------------
        callback_raw = _text(oauth_config, "callbackUrl") or ""
        for line in callback_raw.replace("\r", "\n").split("\n"):
            candidate = line.strip()
            if candidate.lower().startswith("http://"):
                findings.append(
                    f"ERROR {path}: callbackUrl value '{candidate}' uses http://; the OAuth "
                    "redirect must be https://."
                )

        # --- server-to-server shape with no certificate ----------------------------
        certificate = _text(oauth_config, "certificate")
        client_credentials = (
            _text(oauth_config, "isClientCredentialEnabled") or "false"
        ).lower() == "true"
        pkce_required = (_text(oauth_config, "isPkceRequired") or "false").lower() == "true"
        user_delegated = bool(lowered & USER_DELEGATED_SCOPES) or pkce_required
        server_shaped = client_credentials or (
            bool(lowered & SERVER_TO_SERVER_SCOPES) and not user_delegated
        )
        if server_shaped and not certificate:
            findings.append(
                f"INFO {path}: server-to-server scopes are present but no certificate is "
                "configured; this app authenticates with a shared secret rather than a key "
                "pair. Confirm JWT bearer was ruled out deliberately."
            )

    # --- refresh token policy and IP relaxation -----------------------------------
    if oauth_policy is not None:
        refresh_policy = (_text(oauth_policy, "refreshTokenPolicy") or "").strip()
        if refresh_policy.lower() == "infinite":
            findings.append(
                f"WARN {path}: refreshTokenPolicy is 'infinite' (the platform default); the "
                "refresh token never expires unless revoked. Set specific_lifetime:<n>:DAYS "
                "or specific_inactivity:<n>:DAYS, or record why indefinite is acceptable."
            )
        ip_relaxation = (_text(oauth_policy, "ipRelaxation") or "").strip()
        if ip_relaxation.upper() == "BYPASS":
            findings.append(
                f"WARN {path}: ipRelaxation is BYPASS; the app runs without the org's IP "
                "restrictions entirely. Prefer ENFORCE with an ipRanges list."
            )

    return findings


def check_eca_policies(path: Path) -> list[str]:
    """External Client App OAuth policies — the ECA spellings of the same two risks."""
    findings: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"ERROR {path}: not well-formed XML ({exc})"]

    permitted = (_text(root, "permittedUsersPolicyType") or "").strip()
    permission_sets = _text(root, "commaSeparatedPermissionSet")
    profiles = _text(root, "commaSeparatedProfile")
    if permitted == "AdminApprovedPreAuthorized" and not permission_sets and not profiles:
        findings.append(
            f"ERROR {path}: permittedUsersPolicyType is AdminApprovedPreAuthorized but neither "
            "commaSeparatedPermissionSet nor commaSeparatedProfile is set; nobody is "
            "pre-authorized."
        )

    refresh_type = (_text(root, "refreshTokenPolicyType") or "").strip()
    if refresh_type.lower() == "infinite":
        findings.append(
            f"WARN {path}: refreshTokenPolicyType is Infinite; set SpecificLifetime or "
            "SpecificInactivity with refreshTokenValidityPeriod and refreshTokenValidityUnit."
        )

    ip_policy = (_text(root, "ipRelaxationPolicyType") or "").strip()
    if ip_policy.lower() == "bypass":
        findings.append(
            f"WARN {path}: ipRelaxationPolicyType is Bypass; the app runs without the org's "
            "IP restrictions."
        )

    return findings


def check_named_credential(path: Path, external_credentials: set[str]) -> list[str]:
    findings: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"ERROR {path}: not well-formed XML ({exc})"]

    referenced: list[str] = []
    for parameter in _findall(root, "namedCredentialParameters"):
        value = _text(parameter, "externalCredential")
        if value:
            referenced.append(value)

    for name in referenced:
        if name not in external_credentials:
            findings.append(
                f"WARN {path}: references externalCredential '{name}', which is not present in "
                "the scanned tree. Deploy the pair together or the callout has no principal."
            )

    credential_type = (_text(root, "namedCredentialType") or "").strip()
    if credential_type == "SecuredEndpoint" and not referenced:
        findings.append(
            f"WARN {path}: namedCredentialType is SecuredEndpoint but no namedCredentialParameters "
            "entry of parameterType Authentication names an externalCredential; the credential "
            "has no principal."
        )

    return findings


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    if not manifest_dir.exists():
        return [f"ERROR {manifest_dir}: manifest directory not found"]

    findings: list[str] = []
    external_credentials = collect_external_credential_names(manifest_dir)

    connected_apps = find_metadata_files(manifest_dir, ".connectedApp-meta.xml")
    connected_apps += find_metadata_files(manifest_dir, ".connectedApp")
    eca_policies = find_metadata_files(manifest_dir, ".ecaOauthPlcy-meta.xml")
    eca_policies += find_metadata_files(manifest_dir, ".ecaOauthPlcy")
    named_credentials = find_metadata_files(manifest_dir, ".namedCredential-meta.xml")
    named_credentials += find_metadata_files(manifest_dir, ".namedCredential")

    scanned = 0
    for path in sorted(set(connected_apps)):
        scanned += 1
        findings.extend(check_connected_app(path))
    for path in sorted(set(eca_policies)):
        scanned += 1
        findings.extend(check_eca_policies(path))
    for path in sorted(set(named_credentials)):
        scanned += 1
        findings.extend(check_named_credential(path, external_credentials))

    if scanned == 0:
        print(
            f"INFO: no connected app, External Client App policy, or Named Credential metadata "
            f"found under {manifest_dir}.",
            file=sys.stderr,
        )
    return findings


# --------------------------------------------------------------------------- text scan

def iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(candidate for candidate in path.rglob("*") if candidate.is_file())
        else:
            files.append(path)
    return files


def audit_file(path: Path) -> tuple[list[str], bool]:
    findings: list[str] = []
    found_named_credential = False

    if not path.exists():
        return [f"HIGH {path}: file not found"], found_named_credential
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return findings, found_named_credential

    text = path.read_text(encoding="utf-8", errors="ignore")
    lower_path = str(path).lower()

    if (
        "namedcredential" in lower_path
        or "externalcredential" in lower_path
        or path.name.endswith(".namedCredential-meta.xml")
    ):
        found_named_credential = True

    if SECRET_PATTERN.search(text):
        findings.append(
            f"HIGH {path}: possible hardcoded secret, bearer token, or password material found"
        )

    if DIRECT_ENDPOINT_PATTERN.search(text):
        findings.append(
            f"MEDIUM {path}: direct HTTPS endpoint in code; prefer Named Credentials and "
            "`callout:` references"
        )

    if re.search(r"username[- ]password|password flow", text, re.IGNORECASE):
        findings.append(
            f"HIGH {path}: username-password flow reference found; review for stronger OAuth "
            "alternative"
        )

    if re.search(r"<scope>\s*full\s*</scope>|[\s,]full[\s,]", text, re.IGNORECASE):
        findings.append(
            f"MEDIUM {path}: broad `full` OAuth scope detected; confirm least-privilege need"
        )

    return findings, found_named_credential


def run_text_scan(paths: list[str]) -> tuple[list[str], str]:
    findings: list[str] = []
    named_credential_found = False
    files = iter_files(paths)
    for path in files:
        file_findings, file_has_named_credential = audit_file(path)
        findings.extend(file_findings)
        named_credential_found = named_credential_found or file_has_named_credential

    if findings and not named_credential_found:
        findings.append(
            "LOW no Named Credential or External Credential metadata detected in scanned paths"
        )
    if not files:
        findings.append("HIGH no connected-app or auth-related files matched the provided paths")

    summary = (
        f"Scanned {len(files)} connected-app or auth-related file(s); "
        f"{len(findings)} finding(s) detected."
    )
    return findings, summary


# --------------------------------------------------------------------------- output

def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected", file=sys.stderr)
    return 1 if normalized else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check connected-app, External Client App, and Named/External Credential metadata "
            "for configuration mistakes that deploy cleanly and behave wrong."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        help=(
            "Root of the Salesforce project or retrieved metadata; runs the XML checks on "
            "connectedApp / ecaOauthPlcy / namedCredential files."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to text-scan for secrets and direct endpoints.",
    )
    args = parser.parse_args()

    if not args.manifest_dir and not args.paths:
        parser.error("provide --manifest-dir, one or more paths, or both")

    findings: list[str] = []
    summary_parts: list[str] = []

    if args.manifest_dir:
        manifest_findings = check_manifest_dir(Path(args.manifest_dir))
        findings.extend(manifest_findings)
        summary_parts.append(
            f"Metadata checks on {args.manifest_dir}: {len(manifest_findings)} finding(s)."
        )

    if args.paths:
        text_findings, text_summary = run_text_scan(args.paths)
        findings.extend(text_findings)
        summary_parts.append(text_summary)

    return emit_result(findings, " ".join(summary_parts))


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        sys.exit(1)
    sys.exit(0)
