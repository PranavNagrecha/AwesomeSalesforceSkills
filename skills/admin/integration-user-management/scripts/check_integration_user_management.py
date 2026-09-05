#!/usr/bin/env python3
"""Checker for integration-user metadata: API-only profiles and their permission sets.

Stdlib only — no pip dependencies.

Reads a Salesforce metadata tree (``profiles/`` and ``permissionsets/``) and reports
configurations that break, over-privilege, or silently disable an integration user.

Checks
------
1. Permission set grants ``ApiEnabled``. Without it the integration user cannot call
   the API at all, and the Minimum Access base profile grants nothing.
2. Permission set does not enable an elevated user permission (ModifyAllData,
   ViewAllData, AuthorApex, ManageUsers, ModifyMetadata, ViewAllUsers) or an
   object-level ``modifyAllRecords`` / ``viewAllRecords`` escape, unless the config
   file allows that exact permission for that exact permission set.
3. Permission set does not set ``hasActivationRequired`` to true — a session-activated
   permission set cannot help a headless client-credentials or JWT flow.
4. Profile login hours are complete: every day carries both a Start and an End, the
   Start does not exceed the End, values are evenly divisible by 60, and no weekday is
   left open when the others are restricted.
5. Profile declares at least one well-formed ``loginIpRanges`` entry.
6. Profile ``userLicense`` is one the config file lists as API-capable.

Configuration
-------------
Optional JSON file (default: ``<manifest-dir>/integration-user-config.json``,
override with ``--config``)::

    {
      "integrationProfiles": ["SVC_Integration_API_Only"],
      "integrationPermissionSets": ["MuleSoft_Order_Sync"],
      "apiCapableUserLicenses": ["Salesforce", "Salesforce Platform"],
      "allowedElevatedPermissions": {"Data_Archive_Integration": ["ViewAllData"]},
      "requireLoginIpRanges": true
    }

With no config file the checker falls back to matching file names against
integration-sounding keywords, so it stays useful on an unconfigured repo.

Usage
-----
    python3 check_integration_user_management.py --manifest-dir force-app/main/default
    python3 check_integration_user_management.py --manifest-dir . --config ./iu.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

ELEVATED_USER_PERMISSIONS = (
    "ModifyAllData",
    "ViewAllData",
    "AuthorApex",
    "ManageUsers",
    "ModifyMetadata",
    "ViewAllUsers",
)

DEFAULT_API_CAPABLE_LICENSES = (
    "Salesforce",
    "Salesforce Platform",
    "Salesforce Integration",
)

INTEGRATION_KEYWORDS = (
    "integration",
    "api",
    "middleware",
    "etl",
    "mulesoft",
    "boomi",
    "informatica",
    "svc_",
    "service_account",
)


# --------------------------------------------------------------------------- #
# XML helpers
#
# NEVER write `el.find(a) or el.find(b)`: an ElementTree Element with no children
# is falsy even when it exists, so that idiom silently discards real elements.
# Everything below tests `is not None` explicitly.
# --------------------------------------------------------------------------- #

def strip_ns(root: ET.Element) -> str:
    """Return the '{namespace}' prefix used by this document, or ''."""
    if root.tag.startswith("{"):
        return root.tag.split("}")[0] + "}"
    return ""


def child_text(parent: ET.Element, ns: str, tag: str) -> str | None:
    """Text of a single child element, or None when the child is absent or empty."""
    found = parent.find(f"{ns}{tag}")
    if found is None:
        return None
    if found.text is None:
        return None
    return found.text.strip()


def child_bool(parent: ET.Element, ns: str, tag: str) -> bool:
    """True only when the child element exists and its text is exactly 'true'."""
    text = child_text(parent, ns, tag)
    return text is not None and text.lower() == "true"


def enabled_user_permissions(root: ET.Element, ns: str) -> set[str]:
    """Names of userPermissions entries whose <enabled> is true."""
    enabled: set[str] = set()
    for perm in root.findall(f"{ns}userPermissions"):
        name = child_text(perm, ns, "name")
        if name is not None and child_bool(perm, ns, "enabled"):
            enabled.add(name)
    return enabled


def parse_metadata_file(path: Path) -> tuple[ET.Element, str] | None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None
    return root, strip_ns(root)


def api_name(path: Path) -> str:
    """'MyProfile.profile-meta.xml' -> 'MyProfile'."""
    name = path.name
    for suffix in (
        ".profile-meta.xml",
        ".permissionset-meta.xml",
        ".profile",
        ".permissionset",
    ):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def looks_like_integration(name: str) -> bool:
    lowered = name.lower()
    return any(keyword in lowered for keyword in INTEGRATION_KEYWORDS)


def metadata_files(directory: Path, suffixes: Iterable[str]) -> list[Path]:
    found: list[Path] = []
    if not directory.is_dir():
        return found
    for suffix in suffixes:
        found.extend(sorted(directory.glob(f"*{suffix}")))
    return found


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

class Config:
    def __init__(self, data: dict) -> None:
        self.profiles = [str(x) for x in data.get("integrationProfiles", [])]
        self.permission_sets = [
            str(x) for x in data.get("integrationPermissionSets", [])
        ]
        licenses = data.get("apiCapableUserLicenses")
        self.api_capable_licenses = (
            [str(x) for x in licenses] if licenses else list(DEFAULT_API_CAPABLE_LICENSES)
        )
        allowed = data.get("allowedElevatedPermissions", {}) or {}
        self.allowed_elevated = {
            str(k): {str(v) for v in vs} for k, vs in allowed.items()
        }
        self.require_login_ip_ranges = bool(data.get("requireLoginIpRanges", True))
        self.explicit = bool(self.profiles or self.permission_sets)

    def selects_profile(self, name: str) -> bool:
        if self.profiles:
            return name in self.profiles
        return looks_like_integration(name)

    def selects_permission_set(self, name: str) -> bool:
        if self.permission_sets:
            return name in self.permission_sets
        return looks_like_integration(name)

    def allows(self, owner: str, permission: str) -> bool:
        return permission in self.allowed_elevated.get(owner, set())


def load_config(manifest_dir: Path, config_path: Path | None) -> tuple[Config, list[str]]:
    notes: list[str] = []
    path = config_path if config_path is not None else manifest_dir / "integration-user-config.json"
    if not path.is_file():
        if config_path is not None:
            notes.append(f"Config file not found: {path}. Falling back to name matching.")
        return Config({}), notes
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        notes.append(f"Could not read config {path} ({exc}). Falling back to name matching.")
        return Config({}), notes
    if not isinstance(data, dict):
        notes.append(f"Config {path} is not a JSON object. Falling back to name matching.")
        return Config({}), notes
    return Config(data), notes


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

def check_permission_set(path: Path, root: ET.Element, ns: str, config: Config) -> list[str]:
    name = api_name(path)
    issues: list[str] = []

    enabled = enabled_user_permissions(root, ns)

    if "ApiEnabled" not in enabled:
        issues.append(
            f"PermissionSet '{name}': no enabled 'ApiEnabled' userPermissions entry. "
            "An API-only base profile grants no API access on its own, so the integration "
            "user cannot authenticate to the API through this permission set."
        )

    for permission in ELEVATED_USER_PERMISSIONS:
        if permission in enabled and not config.allows(name, permission):
            issues.append(
                f"PermissionSet '{name}': '{permission}' is enabled. Grant it only with a "
                "documented justification, then add it to allowedElevatedPermissions in "
                "integration-user-config.json so this check records the decision."
            )

    for obj_perm in root.findall(f"{ns}objectPermissions"):
        obj = child_text(obj_perm, ns, "object") or "(unnamed object)"
        for escape in ("modifyAllRecords", "viewAllRecords"):
            if child_bool(obj_perm, ns, escape):
                token = f"{escape}:{obj}"
                if not config.allows(name, token):
                    issues.append(
                        f"PermissionSet '{name}': objectPermissions for '{obj}' sets "
                        f"<{escape}>true</{escape}>, which overrides sharing for every record "
                        f"of that object. Allow it explicitly as '{token}' in "
                        "allowedElevatedPermissions if it is genuinely required."
                    )

    if child_bool(root, ns, "hasActivationRequired"):
        issues.append(
            f"PermissionSet '{name}': <hasActivationRequired>true</hasActivationRequired>. "
            "A session-activated permission set requires an associated active session, so it "
            "grants nothing to a headless client-credentials or JWT bearer flow."
        )

    return issues


def check_profile_login_hours(name: str, root: ET.Element, ns: str) -> list[str]:
    issues: list[str] = []
    blocks = root.findall(f"{ns}loginHours")
    if not blocks:
        return issues

    for block in blocks:
        if len(list(block)) == 0:
            # An explicitly empty <loginHours/> removes prior restrictions on purpose.
            continue

        configured_days: list[str] = []
        for day in WEEKDAYS:
            start = child_text(block, ns, f"{day}Start")
            end = child_text(block, ns, f"{day}End")

            if start is None and end is None:
                continue
            configured_days.append(day)

            if start is None or end is None:
                issues.append(
                    f"Profile '{name}': loginHours for {day} has only "
                    f"{'an end' if start is None else 'a start'}. A start requires a matching "
                    "end for the same day, or the deploy is rejected."
                )
                continue

            try:
                start_min, end_min = int(start), int(end)
            except ValueError:
                issues.append(
                    f"Profile '{name}': loginHours for {day} is not numeric "
                    f"(start='{start}', end='{end}'). Values are minutes since midnight."
                )
                continue

            if start_min % 60 or end_min % 60:
                issues.append(
                    f"Profile '{name}': loginHours for {day} ({start_min}-{end_min}) is not "
                    "evenly divisible by 60. Only whole hours are accepted."
                )
            if start_min > end_min:
                issues.append(
                    f"Profile '{name}': loginHours for {day} starts at {start_min} and ends at "
                    f"{end_min}. Start cannot be greater than end for a day."
                )

        missing = [day for day in WEEKDAYS if day not in configured_days]
        if configured_days and missing:
            issues.append(
                f"Profile '{name}': loginHours restricts {len(configured_days)} of 7 days and "
                f"leaves {', '.join(missing)} unconfigured. An integration retry that fires on an "
                "unconfigured day is rejected as a login failure, not as a permission error. "
                "Cover all seven days, or remove the restriction with an empty <loginHours/>."
            )

    return issues


def check_profile(path: Path, root: ET.Element, ns: str, config: Config) -> list[str]:
    name = api_name(path)
    issues: list[str] = []

    enabled = enabled_user_permissions(root, ns)
    for permission in ELEVATED_USER_PERMISSIONS:
        if permission in enabled and not config.allows(name, permission):
            issues.append(
                f"Profile '{name}': '{permission}' is enabled. An integration profile should be "
                "an empty anchor; put justified grants on a permission set instead."
            )

    license_name = child_text(root, ns, "userLicense")
    if license_name is None:
        issues.append(
            f"Profile '{name}': no <userLicense> element. The license decides which permissions "
            "the profile can carry, so state it explicitly in source."
        )
    elif license_name not in config.api_capable_licenses:
        issues.append(
            f"Profile '{name}': userLicense '{license_name}' is not in apiCapableUserLicenses "
            f"({', '.join(config.api_capable_licenses)}). Either the integration user is on the "
            "wrong license, or the config file needs to list this one."
        )

    ip_ranges = root.findall(f"{ns}loginIpRanges")
    if not ip_ranges:
        if config.require_login_ip_ranges:
            issues.append(
                f"Profile '{name}': no <loginIpRanges> entry. Without an IP allowlist, stolen "
                "integration credentials work from anywhere. Set requireLoginIpRanges to false "
                "in the config file if the middleware genuinely has no stable egress range."
            )
    else:
        for index, ip_range in enumerate(ip_ranges, start=1):
            start = child_text(ip_range, ns, "startAddress")
            end = child_text(ip_range, ns, "endAddress")
            if start is None or end is None:
                issues.append(
                    f"Profile '{name}': loginIpRanges entry {index} is missing "
                    f"{'startAddress' if start is None else 'endAddress'}. Both are required."
                )

    issues.extend(check_profile_login_hours(name, root, ns))
    return issues


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #

def check_integration_user_management(
    manifest_dir: Path, config_path: Path | None = None
) -> tuple[list[str], list[str]]:
    """Return (issues, notes) for the metadata under manifest_dir."""
    if not manifest_dir.exists():
        return ([f"Manifest directory not found: {manifest_dir}"], [])

    config, notes = load_config(manifest_dir, config_path)
    if not config.explicit:
        notes.append(
            "No integrationProfiles / integrationPermissionSets configured; selecting files "
            "whose names contain " + ", ".join(INTEGRATION_KEYWORDS) + "."
        )

    issues: list[str] = []
    examined = 0

    for path in metadata_files(
        manifest_dir / "permissionsets", (".permissionset", ".permissionset-meta.xml")
    ):
        if not config.selects_permission_set(api_name(path)):
            continue
        parsed = parse_metadata_file(path)
        if parsed is None:
            issues.append(f"Could not parse permission set: {path}")
            continue
        examined += 1
        issues.extend(check_permission_set(path, parsed[0], parsed[1], config))

    for path in metadata_files(manifest_dir / "profiles", (".profile", ".profile-meta.xml")):
        if not config.selects_profile(api_name(path)):
            continue
        parsed = parse_metadata_file(path)
        if parsed is None:
            issues.append(f"Could not parse profile: {path}")
            continue
        examined += 1
        issues.extend(check_profile(path, parsed[0], parsed[1], config))

    if examined == 0:
        notes.append(
            f"No integration profiles or permission sets found under {manifest_dir}. "
            "Check --manifest-dir, or name the files in integration-user-config.json."
        )

    return issues, notes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check integration-user profile and permission set metadata.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata tree, containing profiles/ and "
        "permissionsets/ (default: current directory).",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to integration-user-config.json "
        "(default: <manifest-dir>/integration-user-config.json).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    config_path = Path(args.config) if args.config else None

    issues, notes = check_integration_user_management(manifest_dir, config_path)

    for note in notes:
        print(f"NOTE: {note}")

    if not issues:
        print("No integration user management issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
