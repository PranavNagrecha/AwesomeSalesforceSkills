#!/usr/bin/env python3
"""Checker for the Activity and Task Patterns skill.

Scans a metadata tree (source or MDAPI layout) for the failure modes documented
in ../references/gotchas.md.

Apex checks
    A1  Query against the abstract Activity object
    A2  DML on ActivityHistory / OpenActivity, by literal name or via a declared
        List<ActivityHistory> / List<OpenActivity> variable (read-only projections;
        object_reference.txt L23515-L23516, L191459-L191460 list describeSObjects() as their only
        supported call)
    A3  Loop-DML on Task / Event
    A4  Polymorphic What.<field> access without TYPEOF
    A5  Bare `insert`/`update` of a Task/Event collection with no
        Database.insert(..., allOrNone=false) / DMLOptions.optAllOrNone anywhere
        in the file (gotchas.md Gotcha 6; apexdev.txt L7566-L7586)

Metadata checks
    M1  ActivitiesSettings: non-boolean value on a boolean element, and any
        attempt to set allowUsersToRelateMultipleContactsToTasksAndEvents, which
        has been read-only in every API version since v36.0
        (api_meta.txt L109382-L109391)
    M2  CustomObject: report whether enableActivities is present/true, since it
        is what makes the object a legal WhatId target
    M3  Task/Event/Activity custom fields: the field must be authored under
        Activity (it lands on both children), must not be a Lookup whose
        referenceTo is Task or Event, and must carry a <type>
    M4  Permission sets / profiles: fieldPermissions that name Task.<field> but
        not Event.<field> (or vice versa). A missing entry is treated as FLS
        disabled, so a one-sided deploy silently strips access
        (object_reference.txt L278589-L278598)

Usage:
    python3 check_activity_and_task_patterns.py [--manifest-dir path/to/metadata]

Exit status: 0 when no issues are found, 1 otherwise. Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "http://soap.sforce.com/2006/04/metadata"
NS = {"md": MD_NS}

# --------------------------------------------------------------------------- #
# Apex patterns
# --------------------------------------------------------------------------- #

FROM_ACTIVITY = re.compile(r"\bFROM\s+Activity\b", re.IGNORECASE)
DML_READONLY = re.compile(
    r"\b(insert|update|upsert|delete)\s+\w*(ActivityHistory|OpenActivity)", re.IGNORECASE
)
LOOP_TASK_DML = re.compile(
    r"for\s*\([^)]*\)\s*\{[^}]*\binsert\s+new\s+(Task|Event)\b", re.DOTALL | re.IGNORECASE
)
WHAT_WITHOUT_TYPEOF = re.compile(
    r"What\.(Name|Industry|Amount|StageName|[A-Za-z_]+__c)", re.IGNORECASE
)
# `List<Task> tasks` / `List<ActivityHistory> ah` -- declaration of a typed
# collection, so DML on the variable can be attributed to the sObject.
COLLECTION_DECL = re.compile(
    r"\b(?:List|Set)\s*<\s*(Task|Event|ActivityHistory|OpenActivity)\s*>\s*"
    r"([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
# `insert tasks;` -- a bare DML verb applied to a single identifier.
BARE_DML = re.compile(
    r"^\s*(insert|update|upsert|delete)\s+([A-Za-z_][A-Za-z0-9_]*)\s*;",
    re.MULTILINE,
)
PARTIAL_SUCCESS = re.compile(
    r"optAllOrNone\s*=\s*false"
    r"|Database\.(?:insert|update|upsert)\s*\([^;]*?,\s*false",
    re.IGNORECASE | re.DOTALL,
)
READONLY_SOBJECTS = {"activityhistory", "openactivity"}
WRITABLE_ACTIVITY_SOBJECTS = {"task", "event"}

# --------------------------------------------------------------------------- #
# ActivitiesSettings
# --------------------------------------------------------------------------- #

# Boolean elements documented in api_meta.txt L109379-L109532.
ACTIVITIES_SETTINGS_BOOLEANS = {
    "allowUsersToRelateMultipleContactsToTasksAndEvents",
    "autoRelateEventAttendees",
    "enableActivityReminders",
    "enableCalendarHomeLWC",
    "enableClickCreateEvents",
    "enableDragAndDropScheduling",
    "enableEmailTracking",
    "enableFlowTaskNotifsViaApex",
    "enableGroupTasks",
    "enableHideChildEventsPreference",
    "enableListViewScheduling",
    "enableLogNote",
    "enableMLSingleClientProfile",
    "enableMultidayEvents",
    "enableRecurringEvents",
    "enableRecurringTasks",
    "enableRollUpActivToContactsAcct",
    "enableSidebarCalendarShortcut",
    "enableSimpleTaskCreateUI",
    "enableTimelineCompDateSort",
    "enableUNSTaskDelegatedToNotifications",
    "enableUserListViewCalendars",
    "showCustomLogoMeetingRequests",
    "showEventDetailsMultiUserCalendar",
    "showHomePageHoverLinksForEvents",
    "showMyTasksHoverLinks",
}
ACTIVITIES_SETTINGS_STRINGS = {"meetingRequestsLogo", "fullName"}
READ_ONLY_SETTING = "allowUsersToRelateMultipleContactsToTasksAndEvents"

ACTIVITY_OBJECTS = {"task", "event", "activity"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Task/Event/Activity metadata and Apex anti-patterns."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the metadata tree (default: current directory).",
    )
    return parser.parse_args()


# --------------------------------------------------------------------------- #
# ElementTree helpers
#
# A leaf Element is falsy, so `el.find(a) or el.find(b)` silently returns the
# wrong thing. Every lookup below goes through these.
# --------------------------------------------------------------------------- #


def child(el, *tags):
    """First child matching any of *tags*, tested with `is not None`."""
    for tag in tags:
        found = el.find(f"md:{tag}", NS)
        if found is not None:
            return found
        found = el.find(tag)
        if found is not None:
            return found
    return None


def text_of(el, *tags, default: str = "") -> str:
    found = child(el, *tags)
    if found is None or found.text is None:
        return default
    return found.text.strip()


def local(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def parse_xml(path: Path):
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        return exc
    except OSError:
        return None


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- #
# Apex
# --------------------------------------------------------------------------- #


def iter_apex(root: Path):
    for pattern in ("*.cls", "*.trigger"):
        for path in root.rglob(pattern):
            yield path


def line_of(text: str, index: int) -> int:
    return text[:index].count("\n") + 1


def check_apex(root: Path) -> list[str]:
    issues: list[str] = []
    for path in iter_apex(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        name = rel(path, root)

        for m in FROM_ACTIVITY.finditer(text):
            issues.append(
                f"{name}:{line_of(text, m.start())}: A1 query FROM Activity; "
                f"Activity is abstract - query Task or Event"
            )

        for m in DML_READONLY.finditer(text):
            issues.append(
                f"{name}:{line_of(text, m.start())}: A2 DML on {m.group(2)}; "
                f"it supports describeSObjects() only - update the underlying Task/Event"
            )

        for m in LOOP_TASK_DML.finditer(text):
            issues.append(
                f"{name}:{line_of(text, m.start())}: A3 insert new {m.group(1)} inside a loop; "
                f"collect into a List and write once"
            )

        if "TYPEOF" not in text.upper():
            for m in WHAT_WITHOUT_TYPEOF.finditer(text):
                issues.append(
                    f"{name}:{line_of(text, m.start())}: A4 What.{m.group(1)} without TYPEOF; "
                    f"only Id and Type are readable on a polymorphic parent"
                )
                break

        # Resolve declared collection variables to their sObject so bare DML can
        # be attributed. `List<Task> tasks` -> {"tasks": "task"}.
        declared: dict[str, str] = {}
        for m in COLLECTION_DECL.finditer(text):
            declared[m.group(2)] = m.group(1)

        has_partial = PARTIAL_SUCCESS.search(text) is not None

        for m in BARE_DML.finditer(text):
            verb, var = m.group(1), m.group(2)
            sobj = declared.get(var)
            if sobj is None:
                continue
            kind = sobj.lower()
            line = line_of(text, m.start())

            # A2 (variable form): DML on a read-only projection.
            if kind in READONLY_SOBJECTS:
                issues.append(
                    f"{name}:{line}: A2 {verb} on '{var}' (List<{sobj}>); "
                    f"ActivityHistory/OpenActivity support describeSObjects() only - "
                    f"update the underlying Task or Event"
                )
                continue

            # A5: bare DML on a Task/Event collection with no partial-success
            # form anywhere in the file.
            if kind in WRITABLE_ACTIVITY_SOBJECTS and verb.lower() != "delete" and not has_partial:
                issues.append(
                    f"{name}:{line}: A5 bare '{verb} {var}' on a {sobj} collection "
                    f"with no partial-success form; use Database.{verb.lower()}(records, "
                    f"dmlOptions, accessLevel) with optAllOrNone=false and "
                    f"EmailHeader.triggerUserEmail=false"
                )

    return issues


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #


def check_activities_settings(root: Path) -> list[str]:
    issues: list[str] = []
    for path in root.rglob("*.settings*"):
        if not path.is_file():
            continue
        parsed = parse_xml(path)
        name = rel(path, root)
        if isinstance(parsed, ET.ParseError):
            issues.append(f"{name}: M1 not well-formed XML: {parsed}")
            continue
        if parsed is None or local(parsed.tag) != "ActivitiesSettings":
            continue

        for el in list(parsed):
            tag = local(el.tag)
            value = (el.text or "").strip()

            if tag == READ_ONLY_SETTING:
                issues.append(
                    f"{name}: M1 <{tag}> is present; it has been read-only in every API "
                    f"version since v36.0, so the deploy succeeds and changes nothing. "
                    f"Shared Activities is a Setup-only, one-way org change"
                )
                continue

            if tag in ACTIVITIES_SETTINGS_BOOLEANS:
                if value not in ("true", "false"):
                    issues.append(
                        f"{name}: M1 <{tag}> is '{value}'; must be exactly 'true' or 'false'"
                    )
            elif tag in ACTIVITIES_SETTINGS_STRINGS:
                if not value:
                    issues.append(f"{name}: M1 <{tag}> is empty")
            else:
                issues.append(
                    f"{name}: M1 <{tag}> is not a documented ActivitiesSettings field; "
                    f"check it against the Metadata API guide before deploying"
                )

        if not list(parsed):
            issues.append(f"{name}: M1 ActivitiesSettings file has no settings elements")

    return issues


def check_custom_objects(root: Path) -> list[str]:
    """M2 - report enableActivities on every custom object file found."""
    issues: list[str] = []
    for path in list(root.rglob("*.object")) + list(root.rglob("*.object-meta.xml")):
        parsed = parse_xml(path)
        name = rel(path, root)
        if isinstance(parsed, ET.ParseError):
            issues.append(f"{name}: M2 not well-formed XML: {parsed}")
            continue
        if parsed is None or local(parsed.tag) != "CustomObject":
            continue

        obj = path.name.split(".")[0]
        if not obj.endswith("__c"):
            continue  # standard object override; enableActivities is not settable there

        flag = child(parsed, "enableActivities")
        if flag is None:
            issues.append(
                f"{name}: M2 custom object has no <enableActivities>; it cannot be a "
                f"Task/Event WhatId until that is true (omitting it leaves the org value "
                f"in place, which is easy to mistake for 'enabled')"
            )
        elif (flag.text or "").strip() not in ("true", "false"):
            issues.append(
                f"{name}: M2 <enableActivities> is '{(flag.text or '').strip()}'; "
                f"must be 'true' or 'false'"
            )

    return issues


def _field_files(root: Path):
    for path in root.rglob("*.field-meta.xml"):
        yield path


def check_activity_fields(root: Path) -> list[str]:
    """M3 - custom fields on Task/Event/Activity."""
    issues: list[str] = []
    for path in _field_files(root):
        parent = path.parent.parent.name  # objects/<Object>/fields/<Field>.field-meta.xml
        if parent.lower() not in ACTIVITY_OBJECTS:
            continue

        parsed = parse_xml(path)
        name = rel(path, root)
        if isinstance(parsed, ET.ParseError):
            issues.append(f"{name}: M3 not well-formed XML: {parsed}")
            continue
        if parsed is None or local(parsed.tag) != "CustomField":
            continue

        field = text_of(parsed, "fullName") or path.name.split(".")[0]
        ftype = text_of(parsed, "type")

        if parent.lower() in ("task", "event"):
            other = "Event" if parent.lower() == "task" else "Task"
            issues.append(
                f"{name}: M3 custom field '{field}' is authored under {parent}; "
                f"Activity custom fields land on Task AND {other} and share field-level "
                f"security - author it under objects/Activity/fields/ instead"
            )

        if not ftype:
            issues.append(f"{name}: M3 custom field '{field}' has no <type>")

        if ftype in ("Lookup", "MasterDetail"):
            target = text_of(parsed, "referenceTo")
            if target.lower() in ("task", "event", "activity"):
                issues.append(
                    f"{name}: M3 '{field}' is a {ftype} with referenceTo={target}. "
                    f"UNVERIFIED (2026-09-05): neither the Metadata API guide nor the "
                    f"Object Reference states that Task/Event cannot be a custom lookup "
                    f"target - the Object Reference documents only the reverse direction "
                    f"(LookedUpFromActivity lists custom lookups FROM an activity). "
                    f"Verify against your org's describe before shipping this"
                )

    return issues


def check_shared_fls(root: Path) -> list[str]:
    """M4 - fieldPermissions on one of Task/Event but not the other."""
    issues: list[str] = []
    patterns = ("*.permissionset-meta.xml", "*.profile-meta.xml", "*.permissionset", "*.profile")
    seen: set[Path] = set()
    for pattern in patterns:
        for path in root.rglob(pattern):
            if path in seen:
                continue
            seen.add(path)

            parsed = parse_xml(path)
            name = rel(path, root)
            if isinstance(parsed, ET.ParseError):
                issues.append(f"{name}: M4 not well-formed XML: {parsed}")
                continue
            if parsed is None:
                continue
            if local(parsed.tag) not in ("PermissionSet", "Profile"):
                continue

            task_fields: set[str] = set()
            event_fields: set[str] = set()
            for perm in parsed.findall("md:fieldPermissions", NS) or parsed.findall(
                "fieldPermissions"
            ):
                full = text_of(perm, "field")
                if "." not in full:
                    continue
                obj, _, fld = full.partition(".")
                if obj.lower() == "task":
                    task_fields.add(fld)
                elif obj.lower() == "event":
                    event_fields.add(fld)

            for fld in sorted(task_fields - event_fields):
                issues.append(
                    f"{name}: M4 fieldPermissions names Task.{fld} but not Event.{fld}. "
                    f"Task and Event share field-level security and a missing entry is "
                    f"treated as FLS disabled, so this deploy can strip Event access"
                )
            for fld in sorted(event_fields - task_fields):
                issues.append(
                    f"{name}: M4 fieldPermissions names Event.{fld} but not Task.{fld}. "
                    f"Task and Event share field-level security and a missing entry is "
                    f"treated as FLS disabled, so this deploy can strip Task access"
                )

    return issues


# --------------------------------------------------------------------------- #


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    issues += check_apex(root)
    issues += check_activities_settings(root)
    issues += check_custom_objects(root)
    issues += check_activity_fields(root)
    issues += check_shared_fls(root)

    if not issues:
        print("No Activity/Task anti-patterns detected.")
        return 0
    for issue in issues:
        print(f"ISSUE: {issue}", file=sys.stderr)
    print(f"{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
