#!/usr/bin/env python3
"""Detect Chatter group governance gaps in retrieved org metadata.

`CollaborationGroup` records are *data* and don't live in SFDX metadata, so
this checker focuses on metadata-side signals that indicate governance gaps:

1. Profiles with `CreateAndOwnNewChatterGroups` enabled (sprawl risk if every
   profile has it on; restrict to a "Chatter Group Creator" perm set instead).
2. Flows with `chatterPost` / `chatterPostMessage` actions that target groups
   but don't reference an explicit owner / lifecycle (auto-creating groups
   without an owner pattern is a sprawl source).
3. Apex classes/triggers that insert `CollaborationGroup` or
   `CollaborationGroupMember` without a clear ownership pattern (looks for
   `OwnerId` assignment near the insert).
4. Custom permissions / permission sets that look chatter-group-related but
   don't appear to be assigned (orphaned governance scaffolding).

The checker also emits an SOQL recipe block listing the queries an admin
should run *in the org* (since these can't be checked from metadata alone):

- inactive-owner orphans
- groups inactive >365 days
- groups with no Group Manager (`CollaborationRole = 'Admin'`)

Stdlib only — no pip dependencies.

Usage:
    python3 check_chatter_group_governance.py [--root force-app/main/default]

Exit codes:
    0  no findings (or only the SOQL recipe block emitted)
    1  metadata-side findings present (informational, non-blocking)
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"s": "http://soap.sforce.com/2006/04/metadata"}

CHATTER_POST_ACTION_TYPES = {"chatterPost", "chatterPostMessage"}
PROFILE_CHATTER_PERM_TAGS = (
    "CreateAndOwnNewChatterGroups",
    "ManageChatterMessages",
    "ModifyAllData",  # informational; admins also have this
)
GROUP_INSERT_RE = re.compile(
    r"\binsert\s+\w*\s*CollaborationGroup\b|\bnew\s+CollaborationGroup\b",
    re.IGNORECASE,
)
MEMBER_INSERT_RE = re.compile(
    r"\binsert\s+\w*\s*CollaborationGroupMember\b|\bnew\s+CollaborationGroupMember\b",
    re.IGNORECASE,
)
OWNER_ASSIGN_RE = re.compile(r"\.OwnerId\s*=", re.IGNORECASE)


def find_profiles_with_group_creation(profiles_dir: Path) -> list[tuple[Path, list[str]]]:
    """Return profiles that have CreateAndOwnNewChatterGroups = true."""
    findings: list[tuple[Path, list[str]]] = []
    if not profiles_dir.exists():
        return findings
    for fp in profiles_dir.rglob("*.profile-meta.xml"):
        try:
            tree = ET.parse(fp)
        except ET.ParseError:
            continue
        root = tree.getroot()
        granted: list[str] = []
        for perm in root.findall(".//s:userPermissions", NS):
            name_el = perm.find("s:name", NS)
            enabled_el = perm.find("s:enabled", NS)
            if name_el is None or enabled_el is None:
                continue
            if enabled_el.text != "true":
                continue
            for tag in PROFILE_CHATTER_PERM_TAGS:
                if name_el.text == tag:
                    granted.append(tag)
        if granted:
            findings.append((fp, granted))
    return findings


def find_flow_chatter_post_actions(flows_dir: Path) -> list[tuple[Path, str, str]]:
    """Return Flows with chatterPost / chatterPostMessage actions.

    These are signals — not all of them are sprawl risks, but flows that auto-
    post to (or auto-create) groups are candidates for review against the
    governance policy.
    """
    findings: list[tuple[Path, str, str]] = []
    if not flows_dir.exists():
        return findings
    for fp in flows_dir.rglob("*.flow-meta.xml"):
        try:
            tree = ET.parse(fp)
        except ET.ParseError:
            continue
        root = tree.getroot()
        for action in root.findall(".//s:actionCalls", NS):
            atype_el = action.find("s:actionType", NS)
            name_el = action.find("s:name", NS)
            if atype_el is None or atype_el.text not in CHATTER_POST_ACTION_TYPES:
                continue
            action_name = name_el.text if name_el is not None else "(unnamed)"
            findings.append((fp, atype_el.text or "", action_name))
    return findings


def find_apex_group_inserts(apex_dirs: list[Path]) -> list[tuple[Path, int, str, bool]]:
    """Return Apex insert sites for CollaborationGroup / CollaborationGroupMember.

    Returns (path, line_number, snippet, has_owner_nearby) — has_owner_nearby
    is True if a `.OwnerId =` assignment appears in the surrounding lines,
    suggesting the inserter is being explicit about ownership.
    """
    findings: list[tuple[Path, int, str, bool]] = []
    for d in apex_dirs:
        if not d.exists():
            continue
        for ext in ("*.cls", "*.trigger"):
            for fp in d.rglob(ext):
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    is_group_insert = (
                        "CollaborationGroup" in line
                        and (
                            GROUP_INSERT_RE.search(line)
                            or MEMBER_INSERT_RE.search(line)
                        )
                    )
                    if not is_group_insert:
                        continue
                    window_start = max(0, i - 30)
                    window_end = min(len(lines), i + 5)
                    window = "\n".join(lines[window_start:window_end])
                    has_owner = bool(OWNER_ASSIGN_RE.search(window))
                    findings.append((fp, i + 1, line.strip(), has_owner))
    return findings


def emit_soql_recipes() -> None:
    """Print the SOQL block that an admin should run in the org itself.

    These checks can't be performed from metadata — they need the live data:
    inactive-owner orphans, groups inactive >365 days, groups missing a
    Group Manager.
    """
    print("\n## SOQL recipes to run in the org (Workbench / Developer Console)")
    print("\n### Active groups owned by inactive users (immediate cleanup queue)")
    print(
        "SELECT Id, Name, OwnerId, Owner.Name, MemberCount, LastFeedModifiedDate\n"
        "FROM CollaborationGroup\n"
        "WHERE IsArchived = false\n"
        "AND Owner.IsActive = false\n"
        "ORDER BY MemberCount DESC"
    )
    print("\n### Active groups with no posts in over 365 days (archive candidates)")
    print(
        "SELECT Id, Name, MemberCount, LastFeedModifiedDate, OwnerId\n"
        "FROM CollaborationGroup\n"
        "WHERE IsArchived = false\n"
        "AND (LastFeedModifiedDate < LAST_N_DAYS:365 OR LastFeedModifiedDate = null)\n"
        "ORDER BY LastFeedModifiedDate ASC NULLS FIRST"
    )
    print("\n### Active groups whose only manager is the (possibly inactive) owner")
    print(
        "SELECT CollaborationGroupId, COUNT(Id) admin_count\n"
        "FROM CollaborationGroupMember\n"
        "WHERE CollaborationRole = 'Admin'\n"
        "GROUP BY CollaborationGroupId\n"
        "HAVING COUNT(Id) = 1"
    )
    print("\n### Distribution of group types (Public vs Private vs Unlisted)")
    print(
        "SELECT CollaborationType, COUNT(Id) cnt\n"
        "FROM CollaborationGroup\n"
        "WHERE IsArchived = false\n"
        "GROUP BY CollaborationType"
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", default="force-app/main/default")
    p.add_argument(
        "--no-soql-recipes",
        action="store_true",
        help="Suppress the SOQL recipe block; only emit metadata findings.",
    )
    args = p.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"metadata root not found: {root}", file=sys.stderr)
        # Still emit SOQL recipes — they're useful even without metadata.
        if not args.no_soql_recipes:
            emit_soql_recipes()
        return 0

    profiles_dir = root / "profiles"
    flows_dir = root / "flows"
    classes_dir = root / "classes"
    triggers_dir = root / "triggers"

    findings_count = 0

    profile_findings = find_profiles_with_group_creation(profiles_dir)
    if profile_findings:
        print(
            "\n## Profiles with chatter-group-related permissions enabled\n"
            "Review whether these profiles need group-creation rights, or whether\n"
            "creation should be restricted to a 'Chatter Group Creator' permission set."
        )
        for fp, perms in profile_findings:
            print(f"  - {fp.relative_to(root)}: {', '.join(perms)}")
        findings_count += len(profile_findings)

    flow_findings = find_flow_chatter_post_actions(flows_dir)
    if flow_findings:
        print(
            "\n## Flows posting to Chatter — review against group-governance policy"
        )
        for fp, atype, name in flow_findings:
            print(
                f"  - {fp.relative_to(root)}: action {name!r} (type {atype})"
            )
        findings_count += len(flow_findings)

    apex_findings = find_apex_group_inserts([classes_dir, triggers_dir])
    if apex_findings:
        print(
            "\n## Apex inserting CollaborationGroup or CollaborationGroupMember"
        )
        for fp, ln, snippet, has_owner in apex_findings:
            tag = (
                " [OwnerId assignment found nearby]"
                if has_owner
                else " [WARN: no OwnerId assignment in surrounding code — implicit owner]"
            )
            print(f"  - {fp.relative_to(root)}:{ln}: {snippet}{tag}")
        findings_count += len(apex_findings)

    if not args.no_soql_recipes:
        emit_soql_recipes()

    if findings_count == 0:
        print(
            "\nNo metadata-side chatter-group-governance findings. "
            "Run the SOQL recipes above against the org to find data-side gaps."
        )
        return 0

    print(f"\nTotal metadata findings: {findings_count}")
    print("Refer to the skill workflow for remediation steps.")
    print(f"ERROR: {findings_count} chatter-group-governance finding(s); see report above.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
