#!/usr/bin/env python3
"""Static checks for Chatter notification tuning.

Chatter notification volume is produced by four different surfaces, and this
checker covers all four from a retrieved metadata tree plus two optional data
exports. Nothing here contacts an org. Stdlib only -- no pip dependencies.

METADATA SIDE (always checked, from --manifest-dir):
  settings/Chatter.settings-meta.xml          ChatterSettings
  settings/ChatterEmailsMD.settings-meta.xml  ChatterEmailsMDSettings
  objects/*/fields/*.field-meta.xml           trackFeedHistory (Feed Tracking)
  objects/*/*.object-meta.xml                 enableFeeds
  notificationtypes/*.notiftype-meta.xml      CustomNotificationType channels
  flows/*.flow-meta.xml                       chatterPost action calls
  classes/*.cls, triggers/*.trigger           FeedItem inserts

POLICY SIDE (checked when --policy is supplied):
  A small JSON file describing the digest policy you intend to apply, so the
  intent is reviewable in a pull request before any DML runs. Shape:

      {
        "defaultGroupNotificationFrequency": "W",
        "justification": "why anything noisier than N is acceptable here",
        "groupOverrides": [
          {"groupName": "Project-Atlas", "frequency": "D", "reason": "..."}
        ]
      }

DATA SIDE (checked when --member-csv / --group-inventory are supplied):
  A Data Loader CSV of CollaborationGroupMember rows staged for update, and a
  CollaborationGroup export used to resolve the policy's group overrides.

Usage:
    python3 check_chatter_notification_tuning.py --manifest-dir force-app/main/default

    python3 check_chatter_notification_tuning.py \\
        --manifest-dir force-app/main/default \\
        --policy notification-policy.json \\
        --group-inventory groups.csv \\
        --member-csv members_update.csv \\
        --max-tracked-fields 5

Produce the data exports with:
    sf data query --result-format csv --target-org <alias> --query \\
      "SELECT Id, Name, IsBroadcast, IsArchived FROM CollaborationGroup" > groups.csv

Checks performed
----------------
ERROR CNT-SETTINGS-ELEMENT  An element appears in Chatter.settings or
                            ChatterEmailsMD.settings that the Metadata API guide
                            does not document for that type (api_meta.txt
                            L112470-112608 and L112383-112418). Undocumented
                            elements fail the deploy rather than being ignored.
ERROR CNT-SETTINGS-BOOL     A documented element holds something other than
                            "true"/"false", or is empty. Every field in both
                            types is typed boolean.
ERROR CNT-TRACK-NO-FEEDS    A field carries trackFeedHistory=true while its
                            object does not carry enableFeeds=true. api_meta.txt
                            L43668-43672: "To set this field to true, the
                            enableFeeds field on the associated CustomObject
                            must also be true."
ERROR CNT-FREQ-VALUE        A NotificationFrequency value in the member CSV or
                            the policy is outside the documented enum. Object
                            Reference L67510-67520: the only valid values are
                            D, W, N and P. "Limited" and "L" are NOT values of
                            this field.
ERROR CNT-POLICY-GROUP      A policy groupOverrides entry names a group that is
                            not in --group-inventory, so the override would
                            silently apply to nothing.
ERROR CNT-POLICY-SHAPE      The policy JSON is unreadable, or is missing
                            defaultGroupNotificationFrequency.
WARN  CNT-POLICY-EVERYPOST  The policy sets "P" (email on every post) as the
                            org-wide default with no "justification" text. Object
                            Reference L67519-67522 documents that in sites this
                            option is disabled once more than 10,000 members
                            choose it and those members are switched to Daily --
                            a silent policy reversal you should have argued for.
WARN  CNT-SETTINGS-MISSING  Neither settings file is in the tree, so the org's
                            notification baseline is not under source control.
WARN  CNT-SETTINGS-REMOVED  allowSharingInChatterGroup is present. api_meta.txt
                            L112487-112489: "Removed. The setting of this field
                            has no effect on the org. Available in API version
                            47.0 only."
WARN  CNT-EMAIL-MASTER      enableCollaborationEmail is false while enableChatter
                            is true (api_meta.txt L112391-112392) -- every
                            per-user and per-group preference below it is inert,
                            which is usually not what a "tune the volume" change
                            intended.
WARN  CNT-TRACK-COUNT       An object tracks more than --max-tracked-fields
                            fields. Each tracked change writes a FeedItem of
                            Type TrackedChange (Object Reference L136377-136378).
WARN  CNT-NOTIFTYPE-CHANNEL A CustomNotificationType has both desktop and mobile
                            false, so it delivers nowhere. api_meta.txt
                            L41799-41812: desktop and mobile are the only
                            delivery channels; slack is reserved for future use.
WARN  CNT-FLOW-CHATTERPOST  A Flow calls actionType chatterPost (api_meta.txt
                            L68655). Migration candidate for
                            customNotificationAction (L68710).
WARN  CNT-APEX-FEEDITEM     Apex inserts a FeedItem. Review Visibility: the
                            InternalUsers default applies to RECORD posts only
                            (Object Reference L136430-136431).
INFO  CNT-DIGEST-API-ONLY   enableChatterDigestEmailsApiOnly is true -- digests
                            are sent via the API rather than on the regular
                            schedule (api_meta.txt L112386-112387). Anyone
                            debugging "digests stopped arriving" needs to know.

Exit status
-----------
1 when any ERROR or WARN finding exists, 0 otherwise. INFO notes never fail the
run; they are printed so a reviewer sees them.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "http://soap.sforce.com/2006/04/metadata"

# api_meta.txt L112470-112608 -- the complete ChatterSettings field table.
CHATTER_SETTINGS_ELEMENTS = {
    "allowChatterGroupArchiving",
    "allowRecordsInChatterGroup",
    "allowSharingInChatterGroup",
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
    "fullName",  # inherited from Metadata
}

# api_meta.txt L112383-112418 -- the complete ChatterEmailsMDSettings field table.
CHATTER_EMAILS_ELEMENTS = {
    "enableChatterDigestEmailsApiOnly",
    "enableChatterEmailAttachment",
    "enableCollaborationEmail",
    "enableDisplayAppDownloadBadges",
    "enableEmailReplyToChatter",
    "enableEmailToChatter",
    "noQnOwnNotifyOnCaseCmt",
    "noQnOwnNotifyOnRep",
    "noQnSubNotifyOnBestR",
    "noQnSubNotifyOnRep",
    "fullName",  # inherited from Metadata
}

# Object Reference L67510-67520 (CollaborationGroupMember.NotificationFrequency)
# and L295156-295172 (User.DefaultGroupNotificationFrequency).
NOTIFICATION_FREQUENCIES = {"D", "W", "N", "P"}
FREQUENCY_LABELS = {
    "D": "Daily",
    "W": "Weekly",
    "N": "Never",
    "P": "On every post",
}

FEED_INSERT_RE = re.compile(r"\binsert\s+\w*\s*FeedItem\b|\bnew\s+FeedItem\b", re.IGNORECASE)
VISIBILITY_RE = re.compile(r"\.Visibility\s*=\s*['\"]InternalUsers['\"]", re.IGNORECASE)
CHATTER_POST_ACTION_TYPE = "chatterPost"

ERROR = "ERROR"
WARN = "WARN"
INFO = "INFO"


class Finding:
    """One check result. Sorted for stable output."""

    def __init__(self, level: str, code: str, subject: str, message: str) -> None:
        self.level = level
        self.code = code
        self.subject = subject
        self.message = message

    def __str__(self) -> str:
        return f"{self.level:<5} {self.code:<22} {self.subject}: {self.message}"

    def sort_key(self) -> tuple:
        order = {ERROR: 0, WARN: 1, INFO: 2}
        return (order.get(self.level, 3), self.code, self.subject)


def tag(name: str) -> str:
    return f"{{{MDAPI_NS}}}{name}"


def child_text(element: ET.Element, name: str) -> str | None:
    """Return a child element's text, or None.

    Deliberately tests `is not None`: a leaf ElementTree Element with no children
    is falsy, so `element.find(a) or element.find(b)` silently drops real hits.
    """
    found = element.find(tag(name))
    if found is None:
        found = element.find(name)
    if found is None:
        return None
    return (found.text or "").strip()


def local_name(element: ET.Element) -> str:
    return element.tag.split("}")[-1] if "}" in element.tag else element.tag


def parse_xml(path: Path, findings: list[Finding]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(Finding(ERROR, "CNT-XML-PARSE", path.name, f"unparseable XML: {exc}"))
    except OSError as exc:
        findings.append(Finding(ERROR, "CNT-XML-READ", path.name, f"unreadable: {exc}"))
    return None


# --------------------------------------------------------------------------
# Metadata side
# --------------------------------------------------------------------------


def check_settings_file(
    path: Path,
    documented: set[str],
    type_name: str,
    findings: list[Finding],
) -> dict[str, str]:
    """Lint one .settings file: documented elements only, boolean values only."""
    values: dict[str, str] = {}
    root = parse_xml(path, findings)
    if root is None:
        return values
    for child in root:
        if not isinstance(child.tag, str):
            continue  # comment / processing instruction
        name = local_name(child)
        text = (child.text or "").strip()
        if name not in documented:
            findings.append(
                Finding(
                    ERROR,
                    "CNT-SETTINGS-ELEMENT",
                    f"{path.name}/{name}",
                    f"not a documented {type_name} element; the guide's field table lists "
                    f"{len(documented) - 1} elements plus fullName.",
                )
            )
            continue
        if name == "fullName":
            continue
        values[name] = text
        if text not in ("true", "false"):
            findings.append(
                Finding(
                    ERROR,
                    "CNT-SETTINGS-BOOL",
                    f"{path.name}/{name}",
                    f"every {type_name} field is typed boolean; got {text!r}.",
                )
            )
    return values


def check_settings(root: Path, findings: list[Finding]) -> None:
    settings_dir = root / "settings"
    chatter = settings_dir / "Chatter.settings-meta.xml"
    emails = settings_dir / "ChatterEmailsMD.settings-meta.xml"

    chatter_values: dict[str, str] = {}
    email_values: dict[str, str] = {}

    if chatter.exists():
        chatter_values = check_settings_file(
            chatter, CHATTER_SETTINGS_ELEMENTS, "ChatterSettings", findings
        )
    if emails.exists():
        email_values = check_settings_file(
            emails, CHATTER_EMAILS_ELEMENTS, "ChatterEmailsMDSettings", findings
        )

    if not chatter.exists() and not emails.exists():
        findings.append(
            Finding(
                WARN,
                "CNT-SETTINGS-MISSING",
                "settings/",
                "neither Chatter.settings-meta.xml nor ChatterEmailsMD.settings-meta.xml is "
                "in this tree; the notification baseline is not in source control.",
            )
        )
        return

    if "allowSharingInChatterGroup" in chatter_values:
        findings.append(
            Finding(
                WARN,
                "CNT-SETTINGS-REMOVED",
                "Chatter.settings/allowSharingInChatterGroup",
                "removed field with no effect on the org (API 47.0 only); drop it from the file.",
            )
        )

    if chatter_values.get("enableChatter") == "true" and email_values.get(
        "enableCollaborationEmail"
    ) == "false":
        findings.append(
            Finding(
                WARN,
                "CNT-EMAIL-MASTER",
                "ChatterEmailsMD.settings/enableCollaborationEmail",
                "false while enableChatter is true: no collaboration email notification is sent "
                "at all, so every per-user and per-group frequency below it is inert.",
            )
        )

    if email_values.get("enableChatterDigestEmailsApiOnly") == "true":
        findings.append(
            Finding(
                INFO,
                "CNT-DIGEST-API-ONLY",
                "ChatterEmailsMD.settings/enableChatterDigestEmailsApiOnly",
                "digests are sent via the API rather than on the regular schedule.",
            )
        )


def check_feed_tracking(root: Path, max_tracked: int, findings: list[Finding]) -> None:
    objects_dir = root / "objects"
    if not objects_dir.exists():
        return
    for obj_dir in sorted(p for p in objects_dir.iterdir() if p.is_dir()):
        obj_name = obj_dir.name

        # enableFeeds lives on the object file itself.
        enable_feeds: str | None = None
        for obj_file in obj_dir.glob("*.object-meta.xml"):
            obj_root = parse_xml(obj_file, findings)
            if obj_root is not None:
                enable_feeds = child_text(obj_root, "enableFeeds")
            break

        tracked: list[str] = []
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue
        for field_xml in sorted(fields_dir.glob("*.field-meta.xml")):
            field_root = parse_xml(field_xml, findings)
            if field_root is None:
                continue
            if child_text(field_root, "trackFeedHistory") == "true":
                tracked.append(field_xml.name.split(".")[0])

        if tracked and enable_feeds is not None and enable_feeds != "true":
            findings.append(
                Finding(
                    ERROR,
                    "CNT-TRACK-NO-FEEDS",
                    obj_name,
                    f"{len(tracked)} field(s) set trackFeedHistory=true but the object sets "
                    f"enableFeeds={enable_feeds!r}; the field deploy is rejected.",
                )
            )
        if len(tracked) > max_tracked:
            shown = ", ".join(tracked[:10])
            more = " ..." if len(tracked) > 10 else ""
            findings.append(
                Finding(
                    WARN,
                    "CNT-TRACK-COUNT",
                    obj_name,
                    f"{len(tracked)} tracked fields (limit {max_tracked}): {shown}{more}",
                )
            )


def check_notification_types(root: Path, findings: list[Finding]) -> None:
    nt_dir = root / "notificationtypes"
    if not nt_dir.exists():
        return
    for path in sorted(nt_dir.glob("*.notiftype-meta.xml")):
        nt_root = parse_xml(path, findings)
        if nt_root is None:
            continue
        desktop = child_text(nt_root, "desktop")
        mobile = child_text(nt_root, "mobile")
        if desktop != "true" and mobile != "true":
            findings.append(
                Finding(
                    WARN,
                    "CNT-NOTIFTYPE-CHANNEL",
                    path.name,
                    "both desktop and mobile are off, so this notification type delivers "
                    "nowhere; slack is reserved for future use.",
                )
            )


def check_flows(root: Path, findings: list[Finding]) -> None:
    flows_dir = root / "flows"
    if not flows_dir.exists():
        return
    for path in sorted(flows_dir.rglob("*.flow-meta.xml")):
        flow_root = parse_xml(path, findings)
        if flow_root is None:
            continue
        for action in flow_root.findall(f".//{tag('actionCalls')}"):
            if child_text(action, "actionType") != CHATTER_POST_ACTION_TYPE:
                continue
            name = child_text(action, "name") or "(unnamed)"
            findings.append(
                Finding(
                    WARN,
                    "CNT-FLOW-CHATTERPOST",
                    f"{path.name}/{name}",
                    "chatterPost action call; if the message is a transient alert rather than a "
                    "durable record, migrate it to customNotificationAction.",
                )
            )


def check_apex(root: Path, findings: list[Finding]) -> None:
    for sub, pattern in (("classes", "*.cls"), ("triggers", "*.trigger")):
        directory = root / sub
        if not directory.exists():
            continue
        for path in sorted(directory.rglob(pattern)):
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for index, line in enumerate(lines):
                if "FeedItem" not in line or not FEED_INSERT_RE.search(line):
                    continue
                window = "\n".join(lines[max(0, index - 30) : index + 5])
                explicit = bool(VISIBILITY_RE.search(window))
                note = (
                    "Visibility=InternalUsers set explicitly."
                    if explicit
                    else "no explicit Visibility; the InternalUsers default covers RECORD posts "
                    "only, so confirm the parent before assuming internal-only."
                )
                findings.append(
                    Finding(
                        WARN,
                        "CNT-APEX-FEEDITEM",
                        f"{path.name}:{index + 1}",
                        note,
                    )
                )


# --------------------------------------------------------------------------
# Policy side
# --------------------------------------------------------------------------


def load_group_names(path: Path, findings: list[Finding]) -> set[str]:
    names: set[str] = set()
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                for key in ("Name", "name", "GroupName"):
                    if row.get(key):
                        names.add(row[key].strip())
                        break
    except OSError as exc:
        findings.append(Finding(ERROR, "CNT-INV-READ", path.name, f"unreadable: {exc}"))
    return names


def check_policy(path: Path, group_names: set[str] | None, findings: list[Finding]) -> None:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(Finding(ERROR, "CNT-POLICY-SHAPE", path.name, f"unreadable: {exc}"))
        return
    if not isinstance(policy, dict):
        findings.append(
            Finding(ERROR, "CNT-POLICY-SHAPE", path.name, "top level must be a JSON object.")
        )
        return

    default = policy.get("defaultGroupNotificationFrequency")
    if default is None:
        findings.append(
            Finding(
                ERROR,
                "CNT-POLICY-SHAPE",
                path.name,
                "missing defaultGroupNotificationFrequency; the policy says nothing about the "
                "value new members inherit.",
            )
        )
    elif default not in NOTIFICATION_FREQUENCIES:
        findings.append(
            Finding(
                ERROR,
                "CNT-FREQ-VALUE",
                f"{path.name}/defaultGroupNotificationFrequency",
                f"{default!r} is not a documented value; valid values are "
                f"{', '.join(sorted(NOTIFICATION_FREQUENCIES))}.",
            )
        )
    elif default == "P" and not str(policy.get("justification", "")).strip():
        findings.append(
            Finding(
                WARN,
                "CNT-POLICY-EVERYPOST",
                f"{path.name}/defaultGroupNotificationFrequency",
                "'P' (on every post) as the org-wide default with no justification recorded.",
            )
        )

    overrides = policy.get("groupOverrides") or []
    if not isinstance(overrides, list):
        findings.append(
            Finding(ERROR, "CNT-POLICY-SHAPE", path.name, "groupOverrides must be a list.")
        )
        return
    for entry in overrides:
        if not isinstance(entry, dict):
            findings.append(
                Finding(
                    ERROR, "CNT-POLICY-SHAPE", path.name, f"groupOverrides entry not an object: {entry!r}"
                )
            )
            continue
        group = str(entry.get("groupName", "")).strip()
        frequency = entry.get("frequency")
        subject = f"{path.name}/groupOverrides/{group or '(unnamed)'}"
        if frequency not in NOTIFICATION_FREQUENCIES:
            findings.append(
                Finding(
                    ERROR,
                    "CNT-FREQ-VALUE",
                    subject,
                    f"{frequency!r} is not a documented value; valid values are "
                    f"{', '.join(sorted(NOTIFICATION_FREQUENCIES))}.",
                )
            )
        if frequency == "P" and not str(entry.get("reason", "")).strip():
            findings.append(
                Finding(
                    WARN,
                    "CNT-POLICY-EVERYPOST",
                    subject,
                    "'P' (on every post) for a single group with no reason recorded.",
                )
            )
        if group_names is not None and group and group not in group_names:
            findings.append(
                Finding(
                    ERROR,
                    "CNT-POLICY-GROUP",
                    subject,
                    "no CollaborationGroup with this Name in --group-inventory; the override "
                    "would apply to nothing.",
                )
            )


def check_member_csv(path: Path, findings: list[Finding]) -> None:
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            column = next(
                (c for c in columns if c.strip().lower().endswith("notificationfrequency")), None
            )
            if column is None:
                findings.append(
                    Finding(
                        ERROR,
                        "CNT-CSV-COLUMN",
                        path.name,
                        f"no NotificationFrequency column; found {', '.join(columns) or '(none)'}.",
                    )
                )
                return
            for line_no, row in enumerate(reader, start=2):
                value = (row.get(column) or "").strip()
                if value in NOTIFICATION_FREQUENCIES:
                    continue
                hint = ""
                if value.title() in FREQUENCY_LABELS.values():
                    code = next(k for k, v in FREQUENCY_LABELS.items() if v == value.title())
                    hint = f" (use the code {code!r}, not the label)"
                elif value.upper() in ("L", "LIMITED"):
                    hint = " ('Limited' is not a value of this field at all)"
                findings.append(
                    Finding(
                        ERROR,
                        "CNT-FREQ-VALUE",
                        f"{path.name}:{line_no}",
                        f"{value!r} is not a documented NotificationFrequency{hint}; valid "
                        f"values are {', '.join(sorted(NOTIFICATION_FREQUENCIES))}.",
                    )
                )
    except OSError as exc:
        findings.append(Finding(ERROR, "CNT-CSV-READ", path.name, f"unreadable: {exc}"))


# --------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--manifest-dir",
        "--root",
        dest="manifest_dir",
        default="force-app/main/default",
        help="retrieved metadata root (default: force-app/main/default)",
    )
    parser.add_argument("--policy", help="notification-policy JSON to lint")
    parser.add_argument("--group-inventory", help="CollaborationGroup CSV export")
    parser.add_argument("--member-csv", help="CollaborationGroupMember CSV staged for update")
    parser.add_argument("--max-tracked-fields", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings: list[Finding] = []

    root = Path(args.manifest_dir)
    if root.exists():
        check_settings(root, findings)
        check_feed_tracking(root, args.max_tracked_fields, findings)
        check_notification_types(root, findings)
        check_flows(root, findings)
        check_apex(root, findings)
    else:
        findings.append(
            Finding(
                WARN,
                "CNT-MANIFEST-MISSING",
                str(root),
                "metadata root not found; only the data-side checks can run.",
            )
        )

    group_names: set[str] | None = None
    if args.group_inventory:
        group_names = load_group_names(Path(args.group_inventory), findings)
    if args.policy:
        check_policy(Path(args.policy), group_names, findings)
    if args.member_csv:
        check_member_csv(Path(args.member_csv), findings)

    if not findings:
        print("No Chatter notification findings.")
        return 0

    findings.sort(key=lambda f: f.sort_key())
    for finding in findings:
        print(finding)

    failing = sum(1 for f in findings if f.level in (ERROR, WARN))
    infos = len(findings) - failing
    print(f"\n{failing} ERROR/WARN finding(s), {infos} INFO note(s).")
    if failing:
        print("See references/gotchas.md for what each code means.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
