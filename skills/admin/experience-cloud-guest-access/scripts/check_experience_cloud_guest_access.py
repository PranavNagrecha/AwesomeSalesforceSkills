#!/usr/bin/env python3
"""Static checks for Experience Cloud guest access metadata.

Reads a Salesforce DX source directory and reports guest-access configuration
that is either dangerous or incomplete. Six checks, all grounded in the
Metadata API Developer Guide (see references/metadata-examples.md for the
field:line citations behind each one):

  1. ERROR  Guest profile grants viewAllRecords / modifyAllRecords /
            viewAllFields on any object. These bypass sharing "regardless of
            the sharing settings for the object", which means they bypass the
            guest sharing rule that is supposed to be the only release valve.
  2. ERROR  Guest profile enables a system permission that has no business on
            an unauthenticated user (ApiEnabled, ViewAllData, ModifyAllData,
            AuthorApex).
  3. ERROR  A sharingGuestRules entry has accessLevel other than Read.
            "For SharingGuestRule, the accessLevel field can be set only to
            Read." Anything else is a deploy failure waiting to happen.
  4. WARN   Guest profile grants allowCreate / allowEdit / allowDelete on an
            object. Create is legitimate for a public form; edit and delete
            almost never are. Objects are listed so the reviewer can judge.
  5. WARN   A guest profile allows create somewhere, but a CustomSite file in
            the same tree has no siteGuestRecordDefaultOwner -- so records the
            guest creates stay owned by the guest user.
  6. WARN   requireHttps appears in a site file (removed in API 52.0+, ignored
            in 51.0 and earlier -- it grants nothing), or a Network file turns
            on a guest-facing switch (enableGuestChatter, enableGuestFileAccess,
            enableGuestMemberVisibility).

Guest profiles are identified heuristically: the file name contains "guest",
or the profile carries a <userLicense> whose text contains "guest". Pass
--guest-profile to name additional profile files explicitly.

stdlib only. Exit code is 1 when any ERROR is reported, 0 otherwise.

Usage:
    python3 check_experience_cloud_guest_access.py --manifest-dir force-app/main/default
    python3 check_experience_cloud_guest_access.py --manifest-dir . \
        --guest-profile "Help Center Profile"
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

ERROR = "ERROR"
WARN = "WARN"

# objectPermissions elements that bypass record-level security entirely.
ESCALATING_OBJECT_PERMISSIONS = ("viewAllRecords", "modifyAllRecords", "viewAllFields")

# objectPermissions elements that grant a write path to an unauthenticated user.
WRITE_OBJECT_PERMISSIONS = ("allowCreate", "allowEdit", "allowDelete")

# userPermissions names that must never be enabled on a guest profile.
FORBIDDEN_USER_PERMISSIONS = ("ApiEnabled", "ViewAllData", "ModifyAllData", "AuthorApex")

# Network elements that expose guest-facing surface beyond the pages you designed.
NETWORK_GUEST_FLAGS = (
    "enableGuestChatter",
    "enableGuestFileAccess",
    "enableGuestMemberVisibility",
)


class Finding:
    """One reported issue."""

    def __init__(self, severity: str, source: str, message: str) -> None:
        self.severity = severity
        self.source = source
        self.message = message

    def render(self) -> str:
        return f"{self.severity}: [{self.source}] {self.message}"


# --------------------------------------------------------------------------
# ElementTree helpers
#
# A leaf Element is falsy in ElementTree, so `elem.find(a) or elem.find(b)`
# silently discards a real element that has no children. Every lookup below
# goes through these helpers and tests `is not None`.
# --------------------------------------------------------------------------


def child(parent, tag: str):
    """Return the first direct child named `tag`, or None. Never falsy-tested."""
    if parent is None:
        return None
    found = parent.find(f"{MD_NS}{tag}")
    if found is not None:
        return found
    # Tolerate files saved without the metadata namespace.
    return parent.find(tag)


def child_text(parent, tag: str, default: str = "") -> str:
    """Return the stripped text of a direct child, or `default`."""
    elem = child(parent, tag)
    if elem is None:
        return default
    if elem.text is None:
        return default
    return elem.text.strip()


def child_is_true(parent, tag: str) -> bool:
    """True only when the child exists and its text is literally 'true'."""
    return child_text(parent, tag).lower() == "true"


def children(parent, tag: str) -> list:
    """Return all direct children named `tag`, namespaced or not."""
    if parent is None:
        return []
    found = parent.findall(f"{MD_NS}{tag}")
    if found:
        return found
    return parent.findall(tag)


def parse_root(path: Path, findings: list[Finding]):
    """Parse an XML file and return its root element, or None on a parse error."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(Finding(ERROR, path.name, f"XML parse error: {exc}"))
        return None
    except OSError as exc:
        findings.append(Finding(WARN, path.name, f"could not be read: {exc}"))
        return None


def find_files(root: Path, *suffixes: str) -> list[Path]:
    """Return files matching any of the given suffixes, DX layout or MDAPI."""
    matches: list[Path] = []
    for suffix in suffixes:
        matches.extend(p for p in root.rglob(f"*{suffix}") if p.is_file())
    return sorted(set(matches))


# --------------------------------------------------------------------------
# Guest profile identification
# --------------------------------------------------------------------------


def is_guest_profile(path: Path, root, explicit: set[str]) -> bool:
    stem = path.name
    for suffix in (".profile-meta.xml", ".profile"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    if stem in explicit:
        return True
    if "guest" in stem.lower():
        return True
    return "guest" in child_text(root, "userLicense").lower()


def collect_guest_profiles(manifest_dir: Path, explicit: set[str], findings: list[Finding]):
    """Return [(path, root)] for every profile file that looks like a guest profile."""
    guest_profiles = []
    for path in find_files(manifest_dir, ".profile-meta.xml", ".profile"):
        root = parse_root(path, findings)
        if root is None:
            continue
        if is_guest_profile(path, root, explicit):
            guest_profiles.append((path, root))
    return guest_profiles


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------


def check_escalating_object_permissions(guest_profiles, findings: list[Finding]) -> None:
    """Check 1: View All / Modify All / View All Fields on a guest profile."""
    for path, root in guest_profiles:
        for perm in children(root, "objectPermissions"):
            obj = child_text(perm, "object", "(unnamed object)")
            for flag in ESCALATING_OBJECT_PERMISSIONS:
                if child_is_true(perm, flag):
                    findings.append(
                        Finding(
                            ERROR,
                            path.name,
                            f"guest profile grants <{flag}> on '{obj}'. This bypasses "
                            "record-level security regardless of the sharing settings, so "
                            "the guest sharing rule no longer limits what is published. "
                            "Set it to false and release records with sharingGuestRules.",
                        )
                    )


def check_forbidden_user_permissions(guest_profiles, findings: list[Finding]) -> None:
    """Check 2: system permissions that must stay off for an unauthenticated user."""
    for path, root in guest_profiles:
        for perm in children(root, "userPermissions"):
            name = child_text(perm, "name")
            if name in FORBIDDEN_USER_PERMISSIONS and child_is_true(perm, "enabled"):
                findings.append(
                    Finding(
                        ERROR,
                        path.name,
                        f"guest profile enables the '{name}' user permission. "
                        "Disable it: it widens the site's attack surface beyond the "
                        "pages you designed.",
                    )
                )


def check_guest_sharing_rule_access_level(manifest_dir: Path, findings: list[Finding]) -> None:
    """Check 3: sharingGuestRules accessLevel must be Read."""
    for path in find_files(manifest_dir, ".sharingRules-meta.xml", ".sharingRules"):
        root = parse_root(path, findings)
        if root is None:
            continue
        for rule in children(root, "sharingGuestRules"):
            label = child_text(rule, "fullName") or child_text(rule, "label") or "(unnamed rule)"
            access = child_text(rule, "accessLevel")
            if access == "":
                findings.append(
                    Finding(
                        ERROR,
                        path.name,
                        f"guest sharing rule '{label}' has no <accessLevel>. It is a "
                        "required field and must be Read.",
                    )
                )
            elif access != "Read":
                findings.append(
                    Finding(
                        ERROR,
                        path.name,
                        f"guest sharing rule '{label}' sets accessLevel '{access}'. For "
                        "SharingGuestRule the accessLevel field can be set only to Read; "
                        "this will not deploy.",
                    )
                )


def check_guest_write_permissions(guest_profiles, findings: list[Finding]) -> set[str]:
    """Check 4: create / edit / delete on a guest profile. Returns objects with create."""
    creatable: set[str] = set()
    for path, root in guest_profiles:
        granted: dict[str, list[str]] = {}
        for perm in children(root, "objectPermissions"):
            obj = child_text(perm, "object", "(unnamed object)")
            for flag in WRITE_OBJECT_PERMISSIONS:
                if child_is_true(perm, flag):
                    granted.setdefault(flag, []).append(obj)
                    if flag == "allowCreate":
                        creatable.add(obj)
        for flag in WRITE_OBJECT_PERMISSIONS:
            objects = granted.get(flag)
            if not objects:
                continue
            joined = ", ".join(sorted(objects))
            if flag == "allowCreate":
                detail = (
                    "Legitimate only for a public form submission. Confirm each object "
                    "is written by a form and never read back, and that the site sets "
                    "siteGuestRecordDefaultOwner."
                )
            else:
                detail = (
                    "An unauthenticated visitor should not be able to modify existing "
                    "records. Remove unless there is a documented, reviewed reason."
                )
            findings.append(
                Finding(
                    WARN,
                    path.name,
                    f"guest profile grants <{flag}> on: {joined}. {detail}",
                )
            )
    return creatable


def check_site_guest_settings(
    manifest_dir: Path, creatable: set[str], findings: list[Finding]
) -> None:
    """Checks 5 and 6a: default record owner when guests can create, and requireHttps."""
    site_files = find_files(manifest_dir, ".site-meta.xml", ".site")
    sites_missing_owner: list[str] = []

    for path in site_files:
        root = parse_root(path, findings)
        if root is None:
            continue

        owner = child_text(root, "siteGuestRecordDefaultOwner")
        if owner == "":
            sites_missing_owner.append(path.name)

        https_elem = child(root, "requireHttps")
        if https_elem is not None:
            value = child_text(root, "requireHttps")
            findings.append(
                Finding(
                    WARN,
                    path.name,
                    f"<requireHttps>{value}</requireHttps> is present but inert: the field "
                    "is removed in API version 52.0 and later, and its value is ignored in "
                    "51.0 and earlier. Remove it and get HTTPS from an HTTPS custom domain "
                    "on customWebAddresses plus redirectToCustomDomain, so the file does "
                    "not read as if a protection is in place.",
                )
            )

        if child(root, "guestProfile") is not None:
            findings.append(
                Finding(
                    WARN,
                    path.name,
                    "<guestProfile> is present but read only -- deploying it does not bind "
                    "or rebind a guest profile. Remove it so the file does not imply a "
                    "wiring that never happens.",
                )
            )

    if creatable and sites_missing_owner:
        objects = ", ".join(sorted(creatable))
        for name in sites_missing_owner:
            findings.append(
                Finding(
                    WARN,
                    name,
                    f"the guest profile allows create on {objects}, but this site has no "
                    "<siteGuestRecordDefaultOwner>. Records a guest creates will be owned "
                    "by the guest user itself. Set it to a named integration user in the "
                    "same deploy that grants allowCreate.",
                )
            )
    elif creatable and not site_files:
        findings.append(
            Finding(
                WARN,
                "(no CustomSite file)",
                f"the guest profile allows create on {', '.join(sorted(creatable))}, but no "
                "*.site-meta.xml is present in this tree, so siteGuestRecordDefaultOwner "
                "cannot be verified. Retrieve the CustomSite before deploying.",
            )
        )


def check_network_guest_flags(manifest_dir: Path, findings: list[Finding]) -> None:
    """Check 6b: site-level guest switches that are independent of profile and sharing."""
    for path in find_files(manifest_dir, ".network-meta.xml", ".network"):
        root = parse_root(path, findings)
        if root is None:
            continue
        for flag in NETWORK_GUEST_FLAGS:
            if child_is_true(root, flag):
                findings.append(
                    Finding(
                        WARN,
                        path.name,
                        f"<{flag}> is true. This is a site-level guest switch, independent "
                        "of the guest profile and of every sharing rule. Confirm it is "
                        "intentional. Note that enableGuestFileAccess is enabled "
                        "automatically when public access is turned on at the page or site "
                        "level, so a deployed false can be overwritten by the platform.",
                    )
                )


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def run_checks(manifest_dir: Path, explicit: set[str]) -> list[Finding]:
    findings: list[Finding] = []

    if not manifest_dir.exists():
        findings.append(Finding(ERROR, str(manifest_dir), "manifest directory not found."))
        return findings
    if not manifest_dir.is_dir():
        findings.append(Finding(ERROR, str(manifest_dir), "manifest path is not a directory."))
        return findings

    guest_profiles = collect_guest_profiles(manifest_dir, explicit, findings)

    check_escalating_object_permissions(guest_profiles, findings)
    check_forbidden_user_permissions(guest_profiles, findings)
    check_guest_sharing_rule_access_level(manifest_dir, findings)
    creatable = check_guest_write_permissions(guest_profiles, findings)
    check_site_guest_settings(manifest_dir, creatable, findings)
    check_network_guest_flags(manifest_dir, findings)

    if not guest_profiles:
        findings.append(
            Finding(
                WARN,
                str(manifest_dir),
                "no guest profile was identified. Profile files are matched on 'guest' in "
                "the file name or in <userLicense>; pass --guest-profile '<Name>' to name "
                "one explicitly. Object and field permission checks did not run.",
            )
        )

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Static checks for Experience Cloud guest access metadata: guest profile "
            "permissions, guest sharing rule access level, and site/network guest settings."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata source tree (default: current directory).",
    )
    parser.add_argument(
        "--guest-profile",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Profile name (without the .profile-meta.xml suffix) to treat as a guest "
            "profile. Repeat for more than one."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = run_checks(Path(args.manifest_dir), set(args.guest_profile))

    errors = [f for f in findings if f.severity == ERROR]
    warnings = [f for f in findings if f.severity == WARN]

    for finding in errors + warnings:
        print(finding.render(), file=sys.stderr)

    print(
        f"experience-cloud-guest-access: {len(errors)} error(s), {len(warnings)} warning(s)."
    )

    if errors:
        return 1
    return 0


if __name__ == "__main__":
    if main() != 0:
        sys.exit(1)
    sys.exit(0)
