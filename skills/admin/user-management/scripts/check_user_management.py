#!/usr/bin/env python3
"""Checker script for the User Management skill.

Two independent checks, either or both of which can run:

1. --manifest-dir  Inspects Salesforce metadata in source format for user-management
                   anti-patterns in profiles: missing login-hour restrictions, missing
                   IP ranges, sensitive user permissions, and login-hour values that
                   the Metadata API will reject.

2. --csv           Lints a user-load CSV before it touches the org. Users cannot be
                   deleted and usernames are never released, so a bad row is permanent
                   org debt -- this is the last place to catch it cheaply.

Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_user_management.py --manifest-dir force-app/main/default
    python3 check_user_management.py --csv users.csv
    python3 check_user_management.py --manifest-dir force-app/main/default --csv users.csv

Expected metadata layout:
    <manifest-dir>/
        profiles/
            *.profile-meta.xml

Grounding for the CSV rules (Object Reference, User object field table):
    - Username: "Required. ... The value for this field must be in the form of an email
      address, using all lowercase characters. It must also be unique across all
      organizations."
    - LastName, Email, Alias, TimeZoneSidKey, LocaleSidKey, EmailEncodingKey,
      LanguageLocaleKey, ProfileId: each documented "Required".
    - IsActive: "Defaulted on create" -- omitting it is legal, hence INFO not WARN.
Grounding for the login-hours rule (Metadata API Developer Guide, ProfileLoginHours):
    - "Valid values for Start: the number of minutes since midnight. Must be evenly
      divisible by 60 (full hours)." Same for End. Start can't be greater than end.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Object Reference marks each of these "Required" on User. ProfileId may instead be
# supplied as a Profile.Name relationship lookup, so either satisfies the requirement.
REQUIRED_USER_COLUMNS = (
    "Username",
    "LastName",
    "Email",
    "Alias",
    "TimeZoneSidKey",
    "LocaleSidKey",
    "EmailEncodingKey",
    "LanguageLocaleKey",
)
PROFILE_COLUMN_ALTERNATIVES = ("ProfileId", "Profile.Name", "Profile:Name")

# Deliberately loose: enough to catch "avargas" or "Ana Vargas", not an RFC validator.
_EMAIL_SHAPE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")

DANGEROUS_PERMS = {
    "ManageUsers": "can create and edit all users including admins",
    "ModifyAllData": "can read, edit, delete all records in the org",
    "ViewAllData": "can read all records in the org regardless of sharing",
    "ManageRoles": "can edit the role hierarchy",
    "ManageProfiles": "can edit profiles and permission sets",
    "AuthorApex": "can write and deploy Apex code",
    "CustomizeApplication": "can modify all configuration including security",
}


class Report:
    """Collects findings by severity.

    ERROR and WARN are blocking; INFO is advisory and never fails the run.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)

    @property
    def findings(self) -> list[str]:
        """Blocking findings only."""
        return self.errors + self.warnings

    def emit(self) -> None:
        for msg in self.errors:
            print(f"ERROR: {msg}")
        for msg in self.warnings:
            print(f"WARN:  {msg}")
        for msg in self.infos:
            print(f"INFO:  {msg}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint Salesforce user-management artefacts: profile metadata "
            "(login hours, IP ranges, sensitive permissions) and user-load CSVs "
            "(required columns, username shape, duplicate usernames)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of Salesforce metadata in source format, e.g. force-app/main/default.",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=None,
        help="Path to a user-load CSV to lint before importing.",
    )
    return parser.parse_args()


def _tag(local: str) -> str:
    return f"{{{_SF_NS}}}{local}"


def _child_text(parent: ET.Element, local: str) -> str | None:
    """Return the stripped text of a child element, or None.

    Written as an explicit ``is not None`` test on purpose: an ElementTree Element with
    no children is falsy, so ``parent.find(a) or parent.find(b)`` silently discards a
    real leaf element.
    """
    node = parent.find(_tag(local))
    if node is None:
        return None
    text = node.text
    if text is None:
        return None
    return text.strip()


# --------------------------------------------------------------------------- profiles


def check_login_hours(profile_name: str, root: ET.Element, report: Report) -> None:
    """Validate loginHours values against the Metadata API's stated constraints."""
    blocks = root.findall(_tag("loginHours"))
    if not blocks:
        report.warn(
            f"[{profile_name}] No loginHours element. If this profile previously had "
            "login-hour restrictions, note that omitting the element does NOT remove "
            "them -- deploy an explicitly empty <loginHours/> tag to clear them."
        )
        return

    for block in blocks:
        for day in _WEEKDAYS:
            start_raw = _child_text(block, f"{day}Start")
            end_raw = _child_text(block, f"{day}End")

            if (start_raw is None) != (end_raw is None):
                present = f"{day}Start" if start_raw is not None else f"{day}End"
                missing = f"{day}End" if start_raw is not None else f"{day}Start"
                report.error(
                    f"[{profile_name}] loginHours sets {present} but not {missing}. "
                    "The Metadata API requires both ends of a day to be specified."
                )
                continue

            if start_raw is None:
                continue

            values: dict[str, int] = {}
            for label, raw in ((f"{day}Start", start_raw), (f"{day}End", end_raw)):
                try:
                    minutes = int(raw)
                except (TypeError, ValueError):
                    report.error(
                        f"[{profile_name}] loginHours {label}='{raw}' is not an integer. "
                        "Values are minutes since midnight (420 = 07:00, 1320 = 22:00), "
                        "not clock times."
                    )
                    continue
                if minutes % 60 != 0:
                    report.error(
                        f"[{profile_name}] loginHours {label}={minutes} is not evenly "
                        "divisible by 60. The Metadata API requires full hours."
                    )
                if not 0 <= minutes <= 1440:
                    report.error(
                        f"[{profile_name}] loginHours {label}={minutes} is outside "
                        "0-1440 minutes since midnight."
                    )
                values[label] = minutes

            start_min = values.get(f"{day}Start")
            end_min = values.get(f"{day}End")
            if start_min is not None and end_min is not None and start_min > end_min:
                report.error(
                    f"[{profile_name}] loginHours {day}Start={start_min} is greater than "
                    f"{day}End={end_min}. Start can't be greater than end for a day."
                )


def check_profile(path: Path, report: Report) -> None:
    """Inspect a single .profile-meta.xml file."""
    profile_name = path.name
    for suffix in (".profile-meta.xml", ".profile"):
        if profile_name.endswith(suffix):
            profile_name = profile_name[: -len(suffix)]
            break

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        report.error(f"[{profile_name}] Cannot parse XML: {exc}")
        return

    root = tree.getroot()

    check_login_hours(profile_name, root, report)

    if not root.findall(_tag("loginIpRanges")):
        report.warn(
            f"[{profile_name}] No loginIpRanges defined. If this profile is used by "
            "internal employees, consider restricting login to corporate IP ranges. "
            "Note that omitting the element on a redeploy does not clear existing ranges."
        )

    for ip_range in root.findall(_tag("loginIpRanges")):
        start = _child_text(ip_range, "startAddress")
        end = _child_text(ip_range, "endAddress")
        if start is None or end is None:
            report.error(
                f"[{profile_name}] A loginIpRanges entry is missing startAddress or "
                "endAddress. Both are Required by the Metadata API."
            )

    user_license = _child_text(root, "userLicense")
    if user_license is None:
        report.info(
            f"[{profile_name}] No userLicense element. Every profile belongs to exactly "
            "one user license type; confirm the retrieve was complete before deploying."
        )

    for perm_elem in root.findall(_tag("userPermissions")):
        perm_name = _child_text(perm_elem, "name")
        enabled_raw = _child_text(perm_elem, "enabled")
        if perm_name is None or enabled_raw is None:
            continue
        if enabled_raw.lower() != "true":
            continue
        if perm_name in DANGEROUS_PERMS:
            report.warn(
                f"[{profile_name}] Sensitive permission enabled: {perm_name} "
                f"({DANGEROUS_PERMS[perm_name]}). Verify this is intentional and "
                "document the business justification."
            )


def check_profiles_dir(manifest_dir: Path, report: Report) -> None:
    """Scan all .profile-meta.xml files under manifest_dir/profiles/."""
    profiles_dir = manifest_dir / "profiles"
    if not profiles_dir.exists():
        report.info(
            f"No profiles directory at {profiles_dir}; skipping profile checks. "
            "Run 'sf project retrieve start' to export profiles."
        )
        return

    profile_files = sorted(profiles_dir.glob("*.profile-meta.xml"))
    if not profile_files:
        report.warn(
            f"Profiles directory exists at {profiles_dir} but contains no "
            "*.profile-meta.xml files. Run 'sf project retrieve start' to export profiles."
        )
        return

    for profile_file in profile_files:
        check_profile(profile_file, report)


# -------------------------------------------------------------------------- user CSVs


def check_user_csv(csv_path: Path, report: Report) -> None:
    """Lint a user-load CSV before it is imported."""
    if not csv_path.exists():
        report.error(f"CSV not found: {csv_path}")
        return

    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            fieldnames = [name.strip() for name in (reader.fieldnames or [])]
            rows = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        report.error(f"[{csv_path.name}] Cannot read CSV: {exc}")
        return

    if not fieldnames:
        report.error(f"[{csv_path.name}] CSV has no header row.")
        return

    header_set = set(fieldnames)

    # --- Check 1: required columns present -------------------------------------
    missing = [col for col in REQUIRED_USER_COLUMNS if col not in header_set]
    for col in missing:
        report.error(
            f"[{csv_path.name}] Missing required column '{col}'. The Object Reference "
            "marks this field Required on User; the load will fail on every row."
        )

    if not any(alt in header_set for alt in PROFILE_COLUMN_ALTERNATIVES):
        report.error(
            f"[{csv_path.name}] No profile column. Supply ProfileId, or a "
            "Profile.Name lookup. ProfileId is Required on User."
        )

    # --- Check 2: IsActive omitted --------------------------------------------
    if "IsActive" not in header_set:
        report.info(
            f"[{csv_path.name}] No IsActive column. The field is 'Defaulted on create', "
            "so this is legal, but stating it explicitly documents intent and makes the "
            "same file reusable as a deactivation update."
        )

    if not rows:
        report.warn(f"[{csv_path.name}] Header present but no data rows.")
        return

    # --- Checks 3-5: per-row username, alias ----------------------------------
    seen: dict[str, int] = {}
    for index, row in enumerate(rows, start=2):  # line 1 is the header
        username = (row.get("Username") or "").strip()

        if "Username" in header_set and not username:
            report.error(f"[{csv_path.name}] Line {index}: Username is empty. It is Required.")
        elif username:
            key = username.lower()
            if key in seen:
                report.error(
                    f"[{csv_path.name}] Line {index}: duplicate Username '{username}' "
                    f"(first seen on line {seen[key]}). Usernames must be unique across "
                    "ALL Salesforce orgs, and a consumed username is never released."
                )
            else:
                seen[key] = index

            if not _EMAIL_SHAPE.match(username):
                report.warn(
                    f"[{csv_path.name}] Line {index}: Username '{username}' is not in the "
                    "form of an email address. The Object Reference requires email shape."
                )
            elif username != username.lower():
                report.warn(
                    f"[{csv_path.name}] Line {index}: Username '{username}' contains "
                    "uppercase characters. The Object Reference requires all lowercase."
                )

        alias = (row.get("Alias") or "").strip()
        if "Alias" in header_set:
            if not alias:
                report.error(f"[{csv_path.name}] Line {index}: Alias is empty. It is Required.")
            elif len(alias) > 8:
                # UNVERIFIED (2026-09-04): the 8-character Alias limit is widely observed
                # but is not stated in the Object Reference, Metadata API guide or Data
                # Loader guide extracts used to build this skill. Reported as WARN, not
                # ERROR, because the limit could not be grounded.
                report.warn(
                    f"[{csv_path.name}] Line {index}: Alias '{alias}' is {len(alias)} "
                    "characters. Alias is commonly limited to 8 -- UNVERIFIED against the "
                    "Object Reference, so this is advisory. Confirm against your org."
                )

    report.info(f"[{csv_path.name}] Linted {len(rows)} row(s), {len(seen)} distinct username(s).")


# ------------------------------------------------------------------------------ main


def main() -> int:
    args = parse_args()
    report = Report()

    if args.manifest_dir is None and args.csv_path is None:
        print(
            "ERROR: nothing to check. Pass --manifest-dir, --csv, or both.",
            file=sys.stderr,
        )
        return 2

    if args.manifest_dir is not None:
        manifest_dir = Path(args.manifest_dir)
        if not manifest_dir.exists():
            report.error(f"Manifest directory not found: {manifest_dir}")
        else:
            check_profiles_dir(manifest_dir, report)

    if args.csv_path is not None:
        check_user_csv(Path(args.csv_path), report)

    report.emit()

    if report.findings:
        print(
            f"\n{len(report.errors)} error(s), {len(report.warnings)} warning(s).",
            file=sys.stderr,
        )
        return 1

    print("No blocking findings.")
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        sys.exit(1 if exit_code == 1 else exit_code)
    sys.exit(0)
