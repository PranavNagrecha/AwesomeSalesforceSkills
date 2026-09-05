#!/usr/bin/env python3
"""Checker for org-wide settings metadata (Org Setup And Configuration skill).

Lints a retrieved Salesforce metadata tree before it is deployed:

  settings/Security.settings-meta.xml   session, password, network access, login-as
  settings/MyDomain.settings-meta.xml   My Domain routing and enhanced-domain signal
  cspTrustedSites/*.cspTrustedSite-meta.xml
  package.xml                           duplicate Settings members

Every enum list and default below is taken from the Metadata API Developer Guide
(Summer '26 / v66 PDF), sections `SecuritySettings` (with its `SessionSettings`,
`PasswordPolicies`, `NetworkAccess`/`IpRange` subtypes), `MyDomainSettings` and
`CspTrustedSite`. Thresholds that are NOT in the guide are labelled as heuristics
where they are declared.

Stdlib only. Exits 1 when any finding is reported, 0 when the tree is clean.

Usage:
    python3 check_org_setup_and_configuration.py [--manifest-dir PATH]

--manifest-dir is the root of the metadata project, e.g. force-app/main/default.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

# --- Guide-documented enum members (SecuritySettings > SessionSettings / PasswordPolicies) ---
SESSION_TIMEOUT_MINUTES = {
    "FifteenMinutes": 15,
    "ThirtyMinutes": 30,
    "SixtyMinutes": 60,
    "NinetyMinutes": 90,      # API 58.0+
    "TwoHours": 120,
    "FourHours": 240,
    "EightHours": 480,
    "TwelveHours": 720,
    "TwentyFourHours": 1440,  # API 38.0+
}
MAX_LOGIN_ATTEMPTS = {"NoLimit", "ThreeAttempts", "FiveAttempts", "TenAttempts"}
LOCKOUT_INTERVALS = {"FifteenMinutes", "ThirtyMinutes", "SixtyMinutes", "Forever"}
PASSWORD_COMPLEXITY = {
    "NoRestriction",
    "AlphaNumeric",
    "SpecialCharacters",
    "UpperLowerCaseNumeric",
    "UpperLowerCaseNumericSpecialCharacters",
    "Any3UpperLowerCaseNumericSpecialCharacters",
}
PASSWORD_EXPIRATION = {"Never", "ThirtyDays", "SixtyDays", "NinetyDays", "SixMonths", "OneYear"}

# Guide: minimumPasswordLength "can contain from 5 to 50 characters (default is 8)".
PASSWORD_LENGTH_MIN_ALLOWED = 5
PASSWORD_LENGTH_MAX_ALLOWED = 50
PASSWORD_LENGTH_PLATFORM_DEFAULT = 8

# HEURISTIC, not a platform limit: anything longer than TwoHours is flagged so the
# choice is deliberate. TwoHours is the value this skill recommends as a baseline.
SESSION_TIMEOUT_HEURISTIC_MAX_MINUTES = 120

# MyDomainSettings.myDomainSuffix values that mean enhanced domains are ON.
ENHANCED_DOMAIN_SUFFIXES = {"MySalesforce", "OrgLevelCertificate"}

# CspTrustedSite grant fields (API 59.0+: at least one must be true).
CSP_GRANT_FIELDS = (
    "isApplicableToConnectSrc",
    "isApplicableToFontSrc",
    "isApplicableToFrameSrc",
    "isApplicableToImgSrc",
    "isApplicableToMediaSrc",
    "isApplicableToStyleSrc",
    "canAccessCamera",
    "canAccessMicrophone",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def child(element, name):
    """Return the named child Element, or None.

    Never write `a.find(x) or a.find(y)`: an Element with no children is falsy
    even when it exists, so `or` silently discards a real match. Test identity.
    """
    if element is None:
        return None
    found = element.find(_tag(name))
    if found is not None:
        return found
    return element.find(name)  # tolerate a namespace-stripped file


def text_of(element, name, default=""):
    node = child(element, name)
    if node is None:
        return default
    if node.text is None:
        return default
    return node.text.strip()


def is_true(element, name):
    return text_of(element, name).lower() == "true"


def has_child(element, name):
    return child(element, name) is not None


def local_name(element) -> str:
    return element.tag.split("}")[-1]


def find_settings_file(manifest_dir: Path, feature: str):
    """Locate <feature>.settings(-meta.xml) under a settings/ directory."""
    candidates = [
        manifest_dir / "settings" / f"{feature}.settings-meta.xml",
        manifest_dir / "settings" / f"{feature}.settings",
        manifest_dir / f"{feature}.settings-meta.xml",
        manifest_dir / f"{feature}.settings",
    ]
    for path in candidates:
        if path.is_file():
            return path
    matches = sorted(manifest_dir.rglob(f"{feature}.settings-meta.xml"))
    if matches:
        return matches[0]
    matches = sorted(manifest_dir.rglob(f"{feature}.settings"))
    if matches:
        return matches[0]
    return None


def parse_xml(path: Path, findings: list):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(("ERROR", f"{path}: XML does not parse ({exc})."))
        return None


# ---------------------------------------------------------------------------
# Check 1-4: Security.settings
# ---------------------------------------------------------------------------

def check_security_settings(manifest_dir: Path, findings: list) -> None:
    path = find_settings_file(manifest_dir, "Security")
    if path is None:
        findings.append((
            "INFO",
            "No Security.settings file found under settings/. Retrieve it before editing: "
            'sf project retrieve start --metadata "Settings:Security" '
            "-- deploying a hand-written file replaces the org's networkAccess ipRanges list.",
        ))
        return

    root = parse_xml(path, findings)
    if root is None:
        return
    rel = path.name

    session = child(root, "sessionSettings")
    passwords = child(root, "passwordPolicies")
    network = child(root, "networkAccess")

    # --- session timeout ---
    if session is not None:
        timeout = text_of(session, "sessionTimeout")
        if timeout and timeout not in SESSION_TIMEOUT_MINUTES:
            findings.append((
                "ERROR",
                f"{rel}: sessionTimeout '{timeout}' is not a documented enum member. "
                f"Valid values: {', '.join(sorted(SESSION_TIMEOUT_MINUTES))}. "
                "This value fails the deploy; sessionTimeout is an enum, not a number of minutes.",
            ))
        elif timeout:
            minutes = SESSION_TIMEOUT_MINUTES[timeout]
            if minutes > SESSION_TIMEOUT_HEURISTIC_MAX_MINUTES:
                findings.append((
                    "WARN",
                    f"{rel}: sessionTimeout is {timeout} ({minutes} minutes), longer than the "
                    f"{SESSION_TIMEOUT_HEURISTIC_MAX_MINUTES}-minute review threshold this checker "
                    "applies as a heuristic (not a platform limit). Confirm the long timeout is a "
                    "deliberate, recorded decision rather than an inherited default.",
                ))

        # --- lock sessions to IP ---
        if is_true(session, "lockSessionsToIp"):
            findings.append((
                "INFO",
                f"{rel}: lockSessionsToIp is true. Sessions are invalidated whenever the source IP "
                "changes, which breaks users on cellular data, shifting VPN egress, or NAT pools. "
                "Confirm the mobile population can tolerate it (see references/gotchas.md gotcha 2).",
            ))

        # --- timeout warning / forced logout pairing ---
        if is_true(session, "disableTimeoutWarning") and is_true(session, "forceLogoutOnSessionTimeout"):
            findings.append((
                "INFO",
                f"{rel}: disableTimeoutWarning is true while forceLogoutOnSessionTimeout is true. "
                "Users are returned to the login page at timeout with no prior warning. "
                "disableTimeoutWarning=true means NO warning (the field name is inverted).",
            ))

        # --- MFA org switch ---
        if has_child(session, "enableMFADirectUILoginOptIn") and not is_true(session, "enableMFADirectUILoginOptIn"):
            findings.append((
                "WARN",
                f"{rel}: enableMFADirectUILoginOptIn is false. Direct username/password UI logins are "
                "not required to present an additional verification method org-wide.",
            ))

        # --- deprecated / removed fields ---
        if has_child(session, "requireHttps"):
            findings.append((
                "INFO",
                f"{rel}: requireHttps is present. The guide records this field as available in API "
                "version 40.0 to 60.0 only, and states the option 'is enabled by default for security "
                "reasons and can't be disabled'. It is not a lever on a current API version.",
            ))
        if has_child(session, "enableRequireHttpsConnection"):
            findings.append((
                "WARN",
                f"{rel}: enableRequireHttpsConnection is deprecated in API version 47.0 and later. Remove it.",
            ))

    # --- admin login-as ---
    if is_true(root, "enableAdminLoginAsAnyUser"):
        findings.append((
            "WARN",
            f"{rel}: enableAdminLoginAsAnyUser is true ('Administrators Can Log in as Any User'). "
            "The platform default is false. Every admin can assume any user's session without that "
            "user granting access; confirm this is an accepted, documented risk.",
        ))
    if is_true(root, "canUsersGrantLoginAccess"):
        findings.append((
            "INFO",
            f"{rel}: canUsersGrantLoginAccess is true, so end users can grant login access to Support "
            "themselves. Set false to restrict granting to admins with Manage Users.",
        ))

    # --- password policies ---
    if passwords is not None:
        raw_len = text_of(passwords, "minimumPasswordLength")
        if raw_len:
            try:
                length = int(raw_len)
            except ValueError:
                findings.append((
                    "ERROR",
                    f"{rel}: minimumPasswordLength '{raw_len}' is not a number. The guide defines it as "
                    f"a string containing {PASSWORD_LENGTH_MIN_ALLOWED} to {PASSWORD_LENGTH_MAX_ALLOWED} "
                    f"(default {PASSWORD_LENGTH_PLATFORM_DEFAULT}).",
                ))
            else:
                if length < PASSWORD_LENGTH_MIN_ALLOWED or length > PASSWORD_LENGTH_MAX_ALLOWED:
                    findings.append((
                        "ERROR",
                        f"{rel}: minimumPasswordLength is {length}, outside the documented range "
                        f"{PASSWORD_LENGTH_MIN_ALLOWED}-{PASSWORD_LENGTH_MAX_ALLOWED}.",
                    ))
                elif length < PASSWORD_LENGTH_PLATFORM_DEFAULT:
                    findings.append((
                        "WARN",
                        f"{rel}: minimumPasswordLength is {length}, below the platform default of "
                        f"{PASSWORD_LENGTH_PLATFORM_DEFAULT}. The guide permits "
                        f"{PASSWORD_LENGTH_MIN_ALLOWED}-{PASSWORD_LENGTH_MAX_ALLOWED}, so this deploys, "
                        "but it weakens the org below the shipped baseline.",
                    ))

        attempts = text_of(passwords, "maxLoginAttempts")
        if attempts and attempts not in MAX_LOGIN_ATTEMPTS:
            findings.append((
                "ERROR",
                f"{rel}: maxLoginAttempts '{attempts}' is not a documented enum member. "
                f"Valid values: {', '.join(sorted(MAX_LOGIN_ATTEMPTS))}. It is an enum, not an integer.",
            ))
        elif attempts == "NoLimit":
            findings.append((
                "WARN",
                f"{rel}: maxLoginAttempts is NoLimit. No lockout applies after repeated failed logins.",
            ))

        interval = text_of(passwords, "lockoutInterval")
        if interval and interval not in LOCKOUT_INTERVALS:
            findings.append((
                "ERROR",
                f"{rel}: lockoutInterval '{interval}' is not a documented enum member. "
                f"Valid values: {', '.join(sorted(LOCKOUT_INTERVALS))}.",
            ))

        complexity = text_of(passwords, "complexity")
        if complexity and complexity not in PASSWORD_COMPLEXITY:
            findings.append((
                "ERROR",
                f"{rel}: complexity '{complexity}' is not a documented enum member. "
                f"Valid values: {', '.join(sorted(PASSWORD_COMPLEXITY))}.",
            ))
        elif complexity == "NoRestriction":
            findings.append((
                "WARN",
                f"{rel}: password complexity is NoRestriction, described in the guide as "
                "'no requirements and is the least secure option'.",
            ))

        expiration = text_of(passwords, "expiration")
        if expiration and expiration not in PASSWORD_EXPIRATION:
            findings.append((
                "ERROR",
                f"{rel}: expiration '{expiration}' is not a documented enum member. "
                f"Valid values: {', '.join(sorted(PASSWORD_EXPIRATION))}.",
            ))

    # --- network access ---
    if network is not None:
        ranges = [e for e in list(network) if local_name(e) == "ipRanges"]
        if not ranges:
            findings.append((
                "WARN",
                f"{rel}: networkAccess is present but contains no ipRanges. The guide states that an "
                "empty networkAccess element is the documented way to REMOVE ALL trusted IP ranges. "
                "If that is not the intent, retrieve the org's current ranges and include them.",
            ))
        seen = set()
        for entry in ranges:
            start = text_of(entry, "start")
            end = text_of(entry, "end")
            desc = text_of(entry, "description")
            if not start or not end:
                findings.append((
                    "ERROR",
                    f"{rel}: an ipRanges entry is missing start and/or end (both are required).",
                ))
                continue
            if not desc:
                findings.append((
                    "INFO",
                    f"{rel}: ipRanges {start}-{end} has no description. Use it to record which network "
                    "the range is, so a later reviewer can tell a live range from a stale one.",
                ))
            key = (start, end)
            if key in seen:
                findings.append((
                    "WARN",
                    f"{rel}: duplicate ipRanges entry {start}-{end}.",
                ))
            seen.add(key)


# ---------------------------------------------------------------------------
# Check 5: MyDomain.settings
# ---------------------------------------------------------------------------

def check_my_domain_settings(manifest_dir: Path, findings: list) -> None:
    path = find_settings_file(manifest_dir, "MyDomain")
    if path is None:
        return

    root = parse_xml(path, findings)
    if root is None:
        return
    rel = path.name

    suffix = text_of(root, "myDomainSuffix")
    if not suffix:
        findings.append((
            "INFO",
            f"{rel}: no myDomainSuffix element, so this file cannot confirm whether enhanced domains "
            "are enabled. myDomainSuffix is the only enhanced-domain signal in MyDomainSettings "
            "(MySalesforce = enhanced, MySalesforceLimited = not); there is no enhancedDomains field.",
        ))
    elif suffix not in ENHANCED_DOMAIN_SUFFIXES:
        findings.append((
            "INFO",
            f"{rel}: myDomainSuffix is '{suffix}', which is not an enhanced-domains value "
            f"({', '.join(sorted(ENHANCED_DOMAIN_SUFFIXES))}). Partitioned domains require enhanced "
            "domains, and this field is read-only in the API -- change it on the My Domain Setup page.",
        ))

    if is_true(root, "canOnlyLoginWithMyDomainUrl"):
        findings.append((
            "INFO",
            f"{rel}: canOnlyLoginWithMyDomainUrl is true. In a SANDBOX this disables the Log In action "
            "on the production Sandboxes Setup page. Keep this value per-environment, not promoted.",
        ))

    # myDomainName is read-only in the API and is present in every retrieved file, so its
    # presence alone is not a finding. It only matters when someone EDITS it expecting a
    # rename -- documented in references/gotchas.md gotcha 7 rather than flagged here.

    if has_child(root, "redirectPriorMyDomain") and not is_true(root, "redirectPriorMyDomain"):
        findings.append((
            "INFO",
            f"{rel}: redirectPriorMyDomain is false. The guide notes it resets to its default (true) "
            "whenever a new My Domain is deployed, so re-assert this value after any domain change.",
        ))


# ---------------------------------------------------------------------------
# Check 6: CspTrustedSite files
# ---------------------------------------------------------------------------

def check_csp_trusted_sites(manifest_dir: Path, findings: list) -> None:
    csp_dir = manifest_dir / "cspTrustedSites"
    if not csp_dir.is_dir():
        return

    files = sorted(list(csp_dir.glob("*.cspTrustedSite-meta.xml")) + list(csp_dir.glob("*.cspTrustedSite")))
    for path in files:
        root = parse_xml(path, findings)
        if root is None:
            continue
        rel = path.name
        endpoint = text_of(root, "endpointUrl")

        granted = [f for f in CSP_GRANT_FIELDS if is_true(root, f)]
        if not granted:
            findings.append((
                "WARN",
                f"{rel}: no isApplicableTo*/canAccess* field is true. In API version 59.0 and later the "
                "guide requires at least one to be true. On older API versions the all-false default "
                "changed twice (all directives on <= 49.0, img-src only on 50.0-58.0), so this file "
                "grants something different on every version. Set every directive explicitly.",
            ))
        elif len(granted) >= 5:
            findings.append((
                "INFO",
                f"{rel}: {len(granted)} directives granted for {endpoint or 'this site'} "
                f"({', '.join(granted)}). Grant only the directive the browser console violation named.",
            ))

        if "*" in endpoint:
            findings.append((
                "INFO",
                f"{rel}: endpointUrl '{endpoint}' uses a wildcard. The guide permits it, but the entry "
                "then trusts every matching subdomain. Prefer a specific host where one is known.",
            ))
        if endpoint and not (endpoint.startswith("https://") or endpoint.startswith("wss://")):
            findings.append((
                "WARN",
                f"{rel}: endpointUrl '{endpoint}' does not start with https:// or wss://. The guide "
                "requires https:// for a third-party API and wss:// for a WebSocket connection.",
            ))
        if "{" in endpoint or "}" in endpoint or "^" in endpoint:
            findings.append((
                "ERROR",
                f"{rel}: endpointUrl '{endpoint}' is malformed. Malformed URLs fail the syntax check, "
                "and pre-February-2025 malformed entries are excluded from generated CSP headers.",
            ))
        if not text_of(root, "description"):
            findings.append((
                "INFO",
                f"{rel}: no description. Record the business justification here so the quarterly "
                "prune can tell a live entry from a defunct integration.",
            ))


# ---------------------------------------------------------------------------
# Check 7: duplicate Settings members in package.xml
# ---------------------------------------------------------------------------

def _package_manifests(manifest_dir: Path):
    seen = []
    for candidate in (
        manifest_dir / "package.xml",
        manifest_dir.parent / "package.xml",
        manifest_dir / "manifest" / "package.xml",
        manifest_dir.parent / "manifest" / "package.xml",
    ):
        if candidate.is_file() and candidate not in seen:
            seen.append(candidate)
    return seen


def check_package_manifest(manifest_dir: Path, findings: list) -> None:
    for path in _package_manifests(manifest_dir):
        root = parse_xml(path, findings)
        if root is None:
            continue
        rel = path.name
        for types_node in [e for e in list(root) if local_name(e) == "types"]:
            name_node = child(types_node, "name")
            type_name = (name_node.text or "").strip() if name_node is not None and name_node.text else ""
            members = [
                (e.text or "").strip()
                for e in list(types_node)
                if local_name(e) == "members" and e.text
            ]
            counts = {}
            for member in members:
                counts[member] = counts.get(member, 0) + 1
            for member, count in sorted(counts.items()):
                if count > 1:
                    findings.append((
                        "WARN",
                        f"{rel}: <name>{type_name}</name> lists <members>{member}</members> {count} times. "
                        "Duplicate members make the manifest ambiguous about what is being deployed; "
                        "list each member once.",
                    ))
            if type_name == "Settings" and "*" in members and len(members) > 1:
                findings.append((
                    "WARN",
                    f"{rel}: the Settings type mixes the '*' wildcard with named members "
                    f"({', '.join(m for m in members if m != '*')}). The wildcard already means every "
                    "settings component in the org; drop it or drop the named members.",
                ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint org-wide Salesforce settings metadata before deploying it.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata project, e.g. force-app/main/default (default: .).",
    )
    return parser.parse_args()


def run(manifest_dir: Path) -> list:
    findings: list = []
    check_security_settings(manifest_dir, findings)
    check_my_domain_settings(manifest_dir, findings)
    check_csp_trusted_sites(manifest_dir, findings)
    check_package_manifest(manifest_dir, findings)
    return findings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        return 1

    findings = run(manifest_dir)

    if not findings:
        print("No issues found.")
        return 0

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for severity, message in sorted(findings, key=lambda f: order.get(f[0], 3)):
        print(f"{severity}: {message}")

    counts = {}
    for severity, _ in findings:
        counts[severity] = counts.get(severity, 0) + 1
    summary = ", ".join(f"{counts[s]} {s}" for s in ("ERROR", "WARN", "INFO") if s in counts)
    print(f"\n{len(findings)} finding(s): {summary}")
    return 1


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        sys.exit(1)
    sys.exit(0)
