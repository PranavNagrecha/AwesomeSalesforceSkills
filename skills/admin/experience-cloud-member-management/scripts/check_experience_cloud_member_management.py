#!/usr/bin/env python3
"""Checker script for Experience Cloud Member Management skill.

Validates Salesforce metadata related to Experience Cloud member management:
- Network membership: every <profile> / <permissionSet> named in
  networkMemberGroups must resolve to a file in the manifest, because those
  two elements are the whole of site membership
  (Metadata API Developer Guide, Network: "The profiles and permission sets
  that have access to the site. Users with these profiles or permission sets
  are members of the site.")
- Self-registration: selfRegistration true implies selfRegProfile set, since
  "This value is used only if selfRegistration is enabled for the site"
- External profiles whose name implies a portal but whose userLicense is not
  an external licence
- External-user load CSVs: required User columns present, and no UserType
  column (User.UserType has no Create/Update property - Object Reference)
- Offboarding checklist JSON completeness
- Apex classes implementing a fabricated self-registration handler shape
  (registerUser / Auth.SelfRegistrationContext), which will not compile

Uses stdlib only - no pip dependencies.

Usage:
    python3 check_experience_cloud_member_management.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXTERNAL_LICENSE_NAMES = {
    "CustomerCommunity",
    "CustomerCommunityPlus",
    "PRM",          # Partner Community
    "ExternalIdentity",
    "Communities",  # legacy label sometimes present in older orgs
}

# Auth.RegistrationHandler and Auth.ConfigurableSelfRegHandler are BOTH current
# and serve different entry points (Auth. Provider JIT vs the site's own
# self-registration page), so implementing either one is legitimate and is not
# flagged. What is never legitimate is the fabricated shape LLMs emit:
# a `registerUser` method taking an `Auth.SelfRegistrationContext`. Neither
# identifier exists in the Auth namespace.
# https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_interface_Auth_ConfigurableSelfRegHandler.htm
CONFIG_SELF_REG_PATTERN = re.compile(
    r"implements\s+Auth\s*\.\s*ConfigurableSelfRegHandler\b",
    re.IGNORECASE,
)

# Identifiers that do not exist on any Salesforce Auth interface.
#
# `registerUser` on its own is NOT a fabrication signal — it is an ordinary
# English method name and a user's own private helper may legitimately be
# called that. Only flag it when it is bound to the Auth namespace, i.e. when
# its first parameter is an Auth.* type. That is the fabricated interface
# shape; a standalone helper named registerUser() is left alone.
FABRICATED_HANDLER_PATTERNS = (
    (re.compile(r"Auth\s*\.\s*SelfRegistrationContext\b"),
     "references 'Auth.SelfRegistrationContext', which is not a Salesforce "
     "class"),
    (re.compile(r"\bregisterUser\s*\(\s*(?:final\s+)?Auth\s*\.\s*\w+"),
     "declares 'registerUser(Auth....)', which is not a method on any "
     "Auth registration interface"),
)

# XML namespace used by Salesforce metadata
SF_NS = "http://soap.sforce.com/2006/04/metadata"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ns(tag: str) -> str:
    """Return a namespace-qualified XML tag for Salesforce metadata."""
    return f"{{{SF_NS}}}{tag}"


def _find_text(element: ET.Element, tag: str) -> str:
    """Return the text of the first matching child element, or ''."""
    child = element.find(_ns(tag))
    if child is None:
        child = element.find(tag)  # fallback: no namespace
    return (child.text or "").strip() if child is not None else ""


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_profiles(manifest_dir: Path) -> list[str]:
    """Check profile XML files for license type issues."""
    issues: list[str] = []
    profiles_dir = manifest_dir / "profiles"
    if not profiles_dir.exists():
        return issues

    for profile_path in profiles_dir.glob("*.profile-meta.xml"):
        try:
            tree = ET.parse(profile_path)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"Profile XML parse error in {profile_path.name}: {exc}")
            continue

        user_license = _find_text(root, "userLicense")
        profile_name = profile_path.stem.replace(".profile-meta", "")

        # Flag profiles that appear to be community profiles but have no external license
        name_lower = profile_name.lower()
        looks_like_community = any(
            kw in name_lower
            for kw in ("community", "partner", "customer", "portal", "external")
        )
        if looks_like_community and user_license and user_license not in EXTERNAL_LICENSE_NAMES:
            issues.append(
                f"Profile '{profile_name}' name suggests an external community profile "
                f"but has user license '{user_license}'. "
                f"External profiles must use one of: {sorted(EXTERNAL_LICENSE_NAMES)}."
            )

    return issues


def _findall(element, tag):
    """All matching children, namespaced or not.

    Never use `a.find(x) or a.find(y)` on ElementTree: an Element with no
    children is falsy, so a real-but-empty match is silently discarded.
    """
    found = element.findall(_ns(tag))
    if not found:
        found = element.findall(tag)
    return found


def _manifest_names(manifest_dir: Path) -> tuple[set[str], set[str]]:
    """Return (profile names, permission set API names) present in the manifest."""
    profiles = {
        path.name[: -len(".profile-meta.xml")]
        for path in (manifest_dir / "profiles").glob("*.profile-meta.xml")
    }
    profiles |= {
        path.stem for path in (manifest_dir / "profiles").glob("*.profile")
    }
    permsets = {
        path.name[: -len(".permissionset-meta.xml")]
        for path in (manifest_dir / "permissionsets").glob("*.permissionset-meta.xml")
    }
    permsets |= {
        path.stem for path in (manifest_dir / "permissionsets").glob("*.permissionset")
    }
    return profiles, permsets


def check_networks(manifest_dir: Path) -> list[str]:
    """Check Network metadata membership and self-registration configuration.

    Element names come from the Metadata API Developer Guide, Network type:
    networkMemberGroups (with <profile> / <permissionSet> children, per the
    guide's own sample definition), selfRegistration, selfRegProfile.
    """
    issues: list[str] = []
    networks_dir = manifest_dir / "networks"
    if not networks_dir.exists():
        return issues

    known_profiles, known_permsets = _manifest_names(manifest_dir)
    manifest_has_profiles = (manifest_dir / "profiles").exists()
    manifest_has_permsets = (manifest_dir / "permissionsets").exists()

    network_paths = sorted(networks_dir.glob("*.network-meta.xml")) or sorted(
        networks_dir.glob("*.network")
    )
    for network_path in network_paths:
        try:
            root = ET.parse(network_path).getroot()
        except ET.ParseError as exc:
            issues.append(f"Network XML parse error in {network_path.name}: {exc}")
            continue

        network_name = network_path.name.split(".")[0]

        member_groups = _findall(root, "networkMemberGroups")
        if not member_groups:
            issues.append(
                f"Network '{network_name}' has no networkMemberGroups element. "
                "Membership is conferred only by the profiles and permission sets "
                "listed there; without it the site has no members."
            )

        named_profiles: list[str] = []
        named_permsets: list[str] = []
        for group in member_groups:
            named_profiles += [
                (el.text or "").strip() for el in _findall(group, "profile")
            ]
            named_permsets += [
                (el.text or "").strip() for el in _findall(group, "permissionSet")
            ]

        if member_groups and not named_profiles and not named_permsets:
            issues.append(
                f"Network '{network_name}' has an empty networkMemberGroups block. "
                "Add at least one <profile> or <permissionSet> child."
            )

        # Cross-check every named member group against the manifest. Only
        # complain when the corresponding directory exists, so a Network-only
        # deployment against an org that already holds the profiles is not
        # flagged.
        if manifest_has_profiles:
            for name in named_profiles:
                if name and name not in known_profiles:
                    issues.append(
                        f"Network '{network_name}' networkMemberGroups names profile "
                        f"'{name}', which is not in the manifest's profiles/ directory. "
                        "The Network deploy fails if the profile does not already "
                        "exist in the target org."
                    )
        if manifest_has_permsets:
            for name in named_permsets:
                if name and name not in known_permsets:
                    issues.append(
                        f"Network '{network_name}' networkMemberGroups names permission "
                        f"set '{name}', which is not in the manifest's permissionsets/ "
                        "directory. The Network deploy fails if the permission set does "
                        "not already exist in the target org."
                    )

        # selfRegistration true => selfRegProfile required.
        self_reg_enabled = _find_text(root, "selfRegistration").lower() == "true"
        self_reg_profile = _find_text(root, "selfRegProfile")
        if self_reg_enabled and not self_reg_profile:
            issues.append(
                f"Network '{network_name}' has selfRegistration enabled but no "
                "selfRegProfile. Self-registered users have no profile to be "
                "assigned, so registration cannot complete."
            )
        if self_reg_enabled and self_reg_profile and manifest_has_profiles:
            if self_reg_profile not in known_profiles:
                issues.append(
                    f"Network '{network_name}' selfRegProfile is '{self_reg_profile}', "
                    "which is not in the manifest's profiles/ directory."
                )
        if self_reg_enabled and self_reg_profile and named_profiles:
            if self_reg_profile not in named_profiles:
                issues.append(
                    f"Network '{network_name}' selfRegProfile '{self_reg_profile}' is "
                    "not listed in networkMemberGroups. Self-registered users would be "
                    "created on a profile that does not confer site membership."
                )
        if not self_reg_enabled and self_reg_profile:
            issues.append(
                f"Network '{network_name}' sets selfRegProfile but selfRegistration is "
                "not true. The value is ignored: it is read only when self-registration "
                "is enabled."
            )

    return issues


# User columns required on an external-user insert. Every one is marked
# Required in the Object Reference User field table, except ContactId, which
# is what makes the user contact-based (and whose Contact must have an
# AccountId or an error occurs).
REQUIRED_USER_CSV_COLUMNS = (
    "ContactId",
    "ProfileId",
    "Username",
    "Email",
    "Alias",
    "LastName",
    "CommunityNickname",
    "TimeZoneSidKey",
    "LocaleSidKey",
    "LanguageLocaleKey",
    "EmailEncodingKey",
)

# Columns that cannot be written on User at all.
NON_WRITABLE_USER_COLUMNS = {
    "usertype": (
        "User.UserType has no Create or Update property - it is derived from the "
        "profile's user license and cannot be set on insert"
    ),
    "accountid": (
        "User.AccountId is read-only (Filter, Group, Nillable, Sort only) - link the "
        "user to an account through ContactId instead"
    ),
    "islicensed": "not a User field",
}


def _looks_like_user_load(header: list[str]) -> bool:
    lowered = {h.strip().lower() for h in header}
    return "username" in lowered and ("profileid" in lowered or "profile" in lowered)


def check_user_csvs(manifest_dir: Path) -> list[str]:
    """Lint external-user load CSVs found anywhere under the manifest directory."""
    issues: list[str] = []
    for csv_path in sorted(manifest_dir.rglob("*.csv")):
        try:
            with csv_path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
                reader = csv.reader(fh)
                try:
                    header = next(reader)
                except StopIteration:
                    continue
                if not _looks_like_user_load(header):
                    continue
                rows = list(reader)
        except OSError:
            continue

        present = {h.strip().lower(): h.strip() for h in header}

        for column in REQUIRED_USER_CSV_COLUMNS:
            if column.lower() not in present:
                issues.append(
                    f"External-user CSV '{csv_path.name}' is missing required column "
                    f"'{column}'. The insert is rejected without it."
                )

        for lowered, reason in NON_WRITABLE_USER_COLUMNS.items():
            if lowered in present:
                issues.append(
                    f"External-user CSV '{csv_path.name}' maps column "
                    f"'{present[lowered]}', which cannot be written: {reason}."
                )

        # Row-level checks that do not need an org connection.
        username_idx = header.index(present.get("username", "Username")) if "username" in present else None
        seen_usernames: dict[str, int] = {}
        for line_no, row in enumerate(rows, start=2):
            if username_idx is None or username_idx >= len(row):
                continue
            username = row[username_idx].strip()
            if not username:
                issues.append(
                    f"External-user CSV '{csv_path.name}' line {line_no} has an empty "
                    "Username. Username is required and must be unique across all orgs."
                )
                continue
            if username != username.lower():
                issues.append(
                    f"External-user CSV '{csv_path.name}' line {line_no} Username "
                    f"'{username}' is not all lowercase. The Object Reference requires "
                    "the value to be in the form of an email address using all "
                    "lowercase characters."
                )
            if "@" not in username:
                issues.append(
                    f"External-user CSV '{csv_path.name}' line {line_no} Username "
                    f"'{username}' is not in email form."
                )
            if username.lower() in seen_usernames:
                issues.append(
                    f"External-user CSV '{csv_path.name}' line {line_no} repeats "
                    f"Username '{username}' from line {seen_usernames[username.lower()]}. "
                    "Usernames are globally unique; the duplicate insert is rejected."
                )
            else:
                seen_usernames[username.lower()] = line_no

    return issues


# Keys an offboarding checklist must carry. The record-reassignment and
# username keys exist because a User can never be deleted and the Username
# stays reserved across all orgs.
OFFBOARDING_REQUIRED_KEYS = {
    "username": "which user is being offboarded",
    "contactId": "the contact the external user hangs off",
    "recordsReassignedTo": "where owned records go BEFORE deactivation",
    "deactivated": "the IsActive = false step itself",
    "membershipGroupsReviewed": (
        "whether the site's NetworkMemberGroup rows still need this profile "
        "or permission set"
    ),
    "usernameRetired": (
        "acknowledgement that the Username is permanently burned and cannot be "
        "reused if the person returns"
    ),
}


def check_offboarding_checklists(manifest_dir: Path) -> list[str]:
    """Check offboarding checklist JSON files for completeness."""
    issues: list[str] = []
    candidates = [
        path
        for path in sorted(manifest_dir.rglob("*.json"))
        if "offboard" in path.name.lower()
    ]
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"Offboarding checklist '{path.name}' is not valid JSON: {exc}")
            continue

        entries = data if isinstance(data, list) else [data]
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                issues.append(
                    f"Offboarding checklist '{path.name}' entry {index} is not an object."
                )
                continue
            label = entry.get("username") or f"entry {index}"
            for key, why in OFFBOARDING_REQUIRED_KEYS.items():
                if key not in entry:
                    issues.append(
                        f"Offboarding checklist '{path.name}' ({label}) is missing "
                        f"'{key}' - {why}."
                    )
            if entry.get("deactivated") and not entry.get("recordsReassignedTo"):
                issues.append(
                    f"Offboarding checklist '{path.name}' ({label}) records the user as "
                    "deactivated but names no reassignment target. Reassign owned "
                    "records before deactivating; the User record can never be deleted."
                )

    return issues


# Auth.ConfigurableSelfRegHandler declares exactly one method:
#   global Id createUser(Id accountId, Id profileId,
#                        Map<SObjectField, String> registrationAttributes,
#                        String password)
CONFIG_SELF_REG_CREATE_USER = re.compile(
    r"\bId\s+createUser\s*\(", re.IGNORECASE
)


def check_apex_handlers(manifest_dir: Path) -> list[str]:
    """Detect Apex registration handlers with impossible (non-compiling) signatures."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for apex_path in classes_dir.glob("*.cls"):
        try:
            source = apex_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for pattern, description in FABRICATED_HANDLER_PATTERNS:
            if pattern.search(source):
                issues.append(
                    f"Apex class '{apex_path.name}' {description}. "
                    "Auth.ConfigurableSelfRegHandler declares only "
                    "'global Id createUser(Id accountId, Id profileId, "
                    "Map<SObjectField, String> registrationAttributes, "
                    "String password)'."
                )

        if CONFIG_SELF_REG_PATTERN.search(source) and not CONFIG_SELF_REG_CREATE_USER.search(source):
            issues.append(
                f"Apex class '{apex_path.name}' implements "
                "'Auth.ConfigurableSelfRegHandler' but does not declare a "
                "createUser method returning Id. The interface requires "
                "'global Id createUser(Id accountId, Id profileId, "
                "Map<SObjectField, String> registrationAttributes, "
                "String password)'."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_experience_cloud_member_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_profiles(manifest_dir))
    issues.extend(check_networks(manifest_dir))
    issues.extend(check_user_csvs(manifest_dir))
    issues.extend(check_offboarding_checklists(manifest_dir))
    issues.extend(check_apex_handlers(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Experience Cloud member management issues: "
            "unresolvable networkMemberGroups entries, self-registration gaps, "
            "profile-license mismatches, external-user CSV column errors, "
            "incomplete offboarding checklists, and Apex registration handlers "
            "with signatures that cannot compile."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_member_management(manifest_dir)

    if not issues:
        print("No Experience Cloud member management issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
