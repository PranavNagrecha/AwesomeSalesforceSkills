#!/usr/bin/env python3
"""Static checks for Chatter group governance.

Chatter group governance splits across two surfaces and this checker covers both.

METADATA SIDE (always checked, from --manifest-dir):
  ChatterSettings (`settings/Chatter.settings-meta.xml`) and the Profile /
  PermissionSet files that grant the group-related user permissions.

DATA SIDE (checked when --group-inventory is supplied):
  A CSV or JSON export of `CollaborationGroup` — the group population itself,
  which is sObject data and never appears in a metadata tree.

Nothing here contacts an org. Uses stdlib only -- no pip dependencies.

Usage:
    python3 check_chatter_group_governance.py --manifest-dir force-app/main/default

    python3 check_chatter_group_governance.py \\
        --manifest-dir force-app/main/default \\
        --group-inventory groups.csv \\
        --name-prefixes Project- Team- Topic- Announce- Customer- \\
        --inactive-days 365

Produce the inventory with:
    sf data query --result-format csv --target-org <alias> --query \\
      "SELECT Id, Name, CollaborationType, OwnerId, Owner.Name, Owner.IsActive, \\
       MemberCount, LastFeedModifiedDate, IsArchived, IsAutoArchiveDisabled \\
       FROM CollaborationGroup" > groups.csv

Checks performed
----------------
ERROR CGG-SETTINGS-BOOL   A ChatterSettings element that the guide types as
                          boolean holds something other than "true"/"false",
                          or an element is empty. Such a file deploys badly or
                          not at all.
ERROR CGG-UNLISTED-UNGOV  unlistedGroupsEnabled is true but no PermissionSet or
                          Profile in the tree grants Manage Unlisted Groups.
                          Object Reference L67112-67117: Modify All Data and
                          View All Data do NOT reach unlisted groups, so nobody
                          in the org can run a complete compliance audit.
ERROR CGG-INV-ORPHAN      An active group in the inventory has an inactive or
                          missing owner. Object Reference L67378-67379: only the
                          owner or a Modify All Data holder can repoint OwnerId.
WARN  CGG-ARCHIVE-OFF     allowChatterGroupArchiving is false. Metadata API
                          L112476-112480: that disables MANUAL archiving too, so
                          the only remaining cleanup lever is delete, which
                          cascades to posts, comments, and shared files
                          (Object Reference L67402-67404).
WARN  CGG-SETTINGS-MISSING  No Chatter.settings file in the tree, so the
                          governance baseline is not under source control.
WARN  CGG-PERM-BROAD      A Profile grants the group-creation permission. Profiles
                          apply to everyone assigned; prefer a permission set.
WARN  CGG-INV-NAMING      An active group's Name matches none of the
                          --name-prefixes conventions.
WARN  CGG-INV-STALE       An active group has had no feed activity for more than
                          --inactive-days, and is not exempted via
                          IsAutoArchiveDisabled.
WARN  CGG-INV-EMPTY       An active group has no recorded feed activity at all
                          and at most one member -- a delete candidate, subject
                          to the direct member count in metadata-examples.md S6.
INFO  CGG-INV-UNLISTED    Count of unlisted groups found in the inventory, so
                          the reviewer can compare it against the number of
                          Manage Unlisted Groups holders.
INFO  CGG-GUESTS          enableInviteCsnUsers is true -- customers can be
                          invited to private groups, and CanHaveGuests is a
                          one-way flag (Apex Reference Guide L111947-111948).

Exit status
-----------
1 when any ERROR or WARN finding exists, 0 otherwise. INFO notes never fail the
run; they are printed so a reviewer sees them.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

SF_NS = "http://soap.sforce.com/2006/04/metadata"

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"

FAILING_LEVELS = (ERROR, WARN)

# Every ChatterSettings element the Metadata API Developer Guide types as
# boolean (api_meta.txt L112470-112608).
CHATTER_SETTINGS_BOOLEANS = (
    "allowChatterGroupArchiving",
    "allowRecordsInChatterGroup",
    "allowSharingInChatterGroup",  # documented as Removed; still boolean-typed
    "enableApprovalRequest",
    "enableCaseFeedRelativeTimestamps",
    "enableChatter",
    "enableChatterEmoticons",
    "enableFeedEdit",
    "enableFeedPinning",
    "enableFeedsDraftPosts",
    "enableFeedsRichText",
    "enableInviteCsnUsers",
    "enableOutOfOfficeEnabledPref",
    "enableRichLinkPreviewsInFeed",
    "enableTodayRecsInFeed",
    "unlistedGroupsEnabled",
)

# The Metadata API Developer Guide documents the <userPermissions> element shape
# but not the catalogue of permission API names, so both the observed API name
# and the run-together Setup label are matched. See the UNVERIFIED note in
# references/metadata-examples.md section 2.
GROUP_CREATION_PERMS = (
    "ChatterOwnGroups",
    "CreateAndOwnNewChatterGroups",
)
UNLISTED_PERMS = (
    "ManageUnlistedGroups",
    "ModifyUnlistedGroups",
)


class Finding:
    """One reported problem, with the level that decides the exit status."""

    def __init__(self, level: str, code: str, subject: str, message: str) -> None:
        self.level = level
        self.code = code
        self.subject = subject
        self.message = message

    def __str__(self) -> str:
        return f"{self.level} {self.code} [{self.subject}] {self.message}"


def tag(name: str) -> str:
    return f"{{{SF_NS}}}{name}"


def child_text(element: ET.Element, name: str) -> str | None:
    """Text of a direct child, or None.

    A leaf ElementTree Element is falsy, so `element.find(a) or element.find(b)`
    silently discards real matches. Every lookup in this file goes through this
    helper, which tests `is not None`.
    """
    found = element.find(tag(name))
    if found is None:
        return None
    return (found.text or "").strip()


def parse_xml(path: Path, findings: list[Finding]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(
            Finding(ERROR, "CGG-XML-PARSE", path.name, f"unparseable XML: {exc}")
        )
        return None
    except OSError as exc:
        findings.append(
            Finding(ERROR, "CGG-XML-READ", path.name, f"unreadable: {exc}")
        )
        return None


# --------------------------------------------------------------------------
# Metadata side
# --------------------------------------------------------------------------


def find_chatter_settings(root: Path) -> list[Path]:
    paths = list(root.rglob("Chatter.settings-meta.xml"))
    paths.extend(p for p in root.rglob("Chatter.settings") if p not in paths)
    return sorted(paths)


def check_chatter_settings(
    root: Path, findings: list[Finding]
) -> dict[str, str]:
    """Validate the ChatterSettings booleans; return the parsed values."""
    values: dict[str, str] = {}
    paths = find_chatter_settings(root)

    if not paths:
        findings.append(
            Finding(
                WARN,
                "CGG-SETTINGS-MISSING",
                "settings/Chatter.settings-meta.xml",
                "no Chatter.settings in the tree; the group-governance baseline "
                "(archiving on/off, unlisted groups on/off, customer invitations) "
                "is not under source control. Retrieve it with "
                "`sf project retrieve start --metadata Settings:Chatter`.",
            )
        )
        return values

    for path in paths:
        element = parse_xml(path, findings)
        if element is None:
            continue
        subject = path.name
        for name in CHATTER_SETTINGS_BOOLEANS:
            text = child_text(element, name)
            if text is None:
                continue
            if text not in ("true", "false"):
                findings.append(
                    Finding(
                        ERROR,
                        "CGG-SETTINGS-BOOL",
                        subject,
                        f"<{name}> is {text!r}; the Metadata API guide types this "
                        f"element as boolean, so it must be exactly 'true' or "
                        f"'false'.",
                    )
                )
                continue
            values[name] = text

        # Elements not in the documented boolean set are worth surfacing: they
        # are either a newer element this checker predates, or a typo that will
        # fail the deploy.
        for child in element:
            local = child.tag.split("}")[-1]
            if local not in CHATTER_SETTINGS_BOOLEANS:
                findings.append(
                    Finding(
                        WARN,
                        "CGG-SETTINGS-UNKNOWN",
                        subject,
                        f"<{local}> is not a ChatterSettings element documented in "
                        f"the v62 Metadata API guide; confirm the spelling and the "
                        f"API version before deploying.",
                    )
                )

    if values.get("allowChatterGroupArchiving") == "false":
        findings.append(
            Finding(
                WARN,
                "CGG-ARCHIVE-OFF",
                "Chatter.settings",
                "allowChatterGroupArchiving is false. That disables MANUAL "
                "archiving as well as the automatic sweep, leaving delete as the "
                "only cleanup lever -- and deleting a group also removes its "
                "files from every other location they were shared into. Exempt "
                "individual groups with CollaborationGroup.IsAutoArchiveDisabled "
                "instead of turning the feature off org-wide.",
            )
        )

    if values.get("enableInviteCsnUsers") == "true":
        findings.append(
            Finding(
                INFO,
                "CGG-GUESTS",
                "Chatter.settings",
                "enableInviteCsnUsers is true: licensed users can invite customers "
                "to private groups they own or manage. Audit CanHaveGuests per "
                "group -- once it is true it cannot be set back to false.",
            )
        )

    return values


def collect_permission_grants(
    root: Path, findings: list[Finding]
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Return (creation grants, unlisted grants), each keyed by file name."""
    creation: dict[str, list[str]] = {}
    unlisted: dict[str, list[str]] = {}

    patterns = (
        "*.permissionset-meta.xml",
        "*.permissionset",
        "*.profile-meta.xml",
        "*.profile",
    )
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(root.rglob(pattern)):
            if path in seen:
                continue
            seen.add(path)
            element = parse_xml(path, findings)
            if element is None:
                continue
            for perm in element.findall(tag("userPermissions")):
                name = child_text(perm, "name")
                enabled = child_text(perm, "enabled")
                if name is None or enabled != "true":
                    continue
                key = str(path.relative_to(root))
                if name in GROUP_CREATION_PERMS:
                    creation.setdefault(key, []).append(name)
                if name in UNLISTED_PERMS:
                    unlisted.setdefault(key, []).append(name)
    return creation, unlisted


def check_permissions(
    root: Path, settings: dict[str, str], findings: list[Finding]
) -> None:
    creation, unlisted = collect_permission_grants(root, findings)

    for source, perms in sorted(creation.items()):
        if ".profile" in source:
            findings.append(
                Finding(
                    WARN,
                    "CGG-PERM-BROAD",
                    source,
                    f"grants {', '.join(sorted(set(perms)))} on a Profile. Every "
                    f"user on this profile can create and own groups, which is the "
                    f"main driver of group sprawl. Move the grant to a named "
                    f"permission set so the holder list is reviewable.",
                )
            )

    if settings.get("unlistedGroupsEnabled") == "true" and not unlisted:
        findings.append(
            Finding(
                ERROR,
                "CGG-UNLISTED-UNGOV",
                "Chatter.settings",
                "unlistedGroupsEnabled is true but no Profile or PermissionSet in "
                "this tree grants Manage Unlisted Groups. Modify All Data and View "
                "All Data do not reach unlisted groups, so no one can produce a "
                "complete group audit. Either add an Unlisted_Group_Auditor "
                "permission set or set unlistedGroupsEnabled to false.",
            )
        )


# --------------------------------------------------------------------------
# Data side
# --------------------------------------------------------------------------


def load_inventory(path: Path, findings: list[Finding]) -> list[dict[str, str]]:
    """Read a CollaborationGroup export from CSV or JSON."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        findings.append(
            Finding(ERROR, "CGG-INV-READ", path.name, f"unreadable: {exc}")
        )
        return []

    stripped = text.lstrip()
    if stripped.startswith("[") or stripped.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            findings.append(
                Finding(ERROR, "CGG-INV-PARSE", path.name, f"bad JSON: {exc}")
            )
            return []
        if isinstance(data, dict):
            # `sf data query --json` wraps rows under result.records.
            result = data.get("result")
            if isinstance(result, dict):
                data = result.get("records", [])
            else:
                data = data.get("records", [])
        if not isinstance(data, list):
            findings.append(
                Finding(
                    ERROR,
                    "CGG-INV-PARSE",
                    path.name,
                    "JSON did not resolve to a list of group records.",
                )
            )
            return []
        return [flatten_row(row) for row in data if isinstance(row, dict)]

    rows = list(csv.DictReader(text.splitlines()))
    if not rows:
        findings.append(
            Finding(WARN, "CGG-INV-EMPTYFILE", path.name, "inventory has no rows.")
        )
    return [flatten_row(row) for row in rows]


def flatten_row(row: dict) -> dict[str, str]:
    """Normalise header spellings and flatten the nested Owner relationship."""
    flat: dict[str, str] = {}
    for key, value in row.items():
        if key is None:
            continue
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if sub_key.startswith("attributes"):
                    continue
                flat[f"{key}.{sub_key}".lower()] = "" if sub_value is None else str(sub_value)
            continue
        flat[str(key).strip().lower()] = "" if value is None else str(value)
    return flat


def get(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name.lower())
        if value is not None and value != "":
            return value
    return ""


def is_true(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes")


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    for candidate in (text, text.split("T")[0]):
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    return None


def check_inventory(
    path: Path,
    prefixes: list[str],
    inactive_days: int,
    findings: list[Finding],
) -> None:
    rows = load_inventory(path, findings)
    if not rows:
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=inactive_days)
    unlisted_count = 0

    for row in rows:
        group_id = get(row, "Id") or "(no Id)"
        name = get(row, "Name")
        subject = f"{name or group_id}"

        if is_true(get(row, "IsArchived")):
            continue

        group_type = get(row, "CollaborationType")
        if group_type.lower() == "unlisted":
            unlisted_count += 1

        owner_active = get(row, "Owner.IsActive", "OwnerIsActive", "owner_active")
        owner_id = get(row, "OwnerId")
        if not owner_id:
            findings.append(
                Finding(
                    ERROR,
                    "CGG-INV-ORPHAN",
                    subject,
                    "active group with no OwnerId in the export -- a dangling "
                    "owner reference. Repoint it as a Modify All Data holder; "
                    "the transfer UI cannot render a missing owner.",
                )
            )
        elif owner_active and not is_true(owner_active):
            findings.append(
                Finding(
                    ERROR,
                    "CGG-INV-ORPHAN",
                    subject,
                    f"active group owned by inactive user {owner_id}. Only the "
                    f"owner or a Modify All Data holder can repoint OwnerId, and "
                    f"promoting a group manager is not a transfer.",
                )
            )

        if prefixes and name and not any(name.startswith(p) for p in prefixes):
            findings.append(
                Finding(
                    WARN,
                    "CGG-INV-NAMING",
                    subject,
                    f"name matches none of the conventions {prefixes}. Prefixes "
                    f"are what make bulk archive by purpose possible; without one "
                    f"this group can only be swept by explicit Id list.",
                )
            )

        last_feed = parse_date(get(row, "LastFeedModifiedDate"))
        exempt = is_true(get(row, "IsAutoArchiveDisabled"))
        member_count = get(row, "MemberCount")

        if last_feed is None:
            try:
                members = int(member_count) if member_count else 0
            except ValueError:
                members = 0
            if member_count and members <= 1:
                findings.append(
                    Finding(
                        WARN,
                        "CGG-INV-EMPTY",
                        subject,
                        "no recorded feed activity and at most one member. Delete "
                        "candidate -- but MemberCount is a nillable rollup, so "
                        "confirm with a direct COUNT over "
                        "CollaborationGroupMember before deleting.",
                    )
                )
        elif last_feed < cutoff and not exempt:
            days = (datetime.now(timezone.utc) - last_feed).days
            findings.append(
                Finding(
                    WARN,
                    "CGG-INV-STALE",
                    subject,
                    f"no post or comment in {days} days (threshold "
                    f"{inactive_days}) and IsAutoArchiveDisabled is not set. "
                    f"Archive candidate; archive preserves posts, members, and "
                    f"files, delete does not.",
                )
            )

    if unlisted_count:
        findings.append(
            Finding(
                INFO,
                "CGG-INV-UNLISTED",
                path.name,
                f"{unlisted_count} active unlisted group(s) in the inventory. This "
                f"export was produced by a user who could see them; confirm that "
                f"at least one named compliance holder has Manage Unlisted Groups, "
                f"or future audits will silently under-report.",
            )
        )


# --------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Chatter group governance: ChatterSettings and permission "
            "metadata, plus an optional CollaborationGroup data export."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root of the Salesforce metadata source (sfdx source format or mdapi "
            "format). Default: current directory."
        ),
    )
    parser.add_argument(
        "--group-inventory",
        help=(
            "Optional CSV or JSON export of CollaborationGroup. Enables the "
            "orphan-owner, naming-convention, stale-group and empty-group checks."
        ),
    )
    parser.add_argument(
        "--name-prefixes",
        nargs="*",
        default=[],
        help=(
            "Allowed group-name prefixes, e.g. Project- Team- Topic-. Groups "
            "matching none of them are reported. Omit to skip the naming check."
        ),
    )
    parser.add_argument(
        "--inactive-days",
        type=int,
        default=365,
        help="Days without a post or comment before a group is stale. Default 365.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}")
        return 1

    findings: list[Finding] = []

    settings = check_chatter_settings(manifest_dir, findings)
    check_permissions(manifest_dir, settings, findings)

    if args.group_inventory:
        inventory_path = Path(args.group_inventory)
        if not inventory_path.exists():
            print(f"ERROR: Group inventory not found: {inventory_path}")
            return 1
        check_inventory(
            inventory_path, args.name_prefixes, args.inactive_days, findings
        )

    for level in (ERROR, WARN, INFO):
        for finding in findings:
            if finding.level == level:
                print(finding)

    failing = [f for f in findings if f.level in FAILING_LEVELS]
    notes = [f for f in findings if f.level == INFO]

    if not findings:
        print("OK: no Chatter group governance issues detected.")
        return 0

    print(f"\n{len(failing)} finding(s) at ERROR/WARN, {len(notes)} INFO note(s).")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
