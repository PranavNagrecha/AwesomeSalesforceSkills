#!/usr/bin/env python3
"""Checker script for Case Management Setup skill.

Inspects Salesforce metadata (retrieved via sfdx/sf force:source:retrieve or
equivalent) for common case management configuration issues.

Covers, in order: case assignment rules, escalation rules, auto-response rules,
queues, the Email-to-Case routing block, the CaseSettings org-level and webToCase
blocks, the CaseOrigin / CasePriority / CaseStatus standard value sets, the
Case support processes and record types (nested <CustomObject> form and the
DX-decomposed *.businessProcess-meta.xml / *.recordType-meta.xml form), and the
source-format stem rules CMS-STEM-01 / CMS-STEM-02.

ERROR-level rules (printed as `ERROR:`, exit 1):
  CMS-STEM-01  a decomposed *.businessProcess-meta.xml / *.recordType-meta.xml whose
               <fullName> is not exactly its file stem, or whose <fullName> holds a space.
  CMS-STEM-02  a record type whose <businessProcess> names no existing process file stem.
Everything else prints as `ISSUE:` and also exits 1.

Element names and constraints are grounded in the Metadata API Developer Guide
(CaseSettings, WebToCaseSettings, StandardValueSet, StandardValue, BusinessProcess,
RecordType) — see references/metadata-examples.md for the line citations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_case_management_setup.py --manifest-dir path/to/metadata
    python3 check_case_management_setup.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce metadata XML namespace
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Hard limit: Web-to-Case pending requests that trigger silent drops
WEB_TO_CASE_PENDING_LIMIT = 50_000

# Email body is truncated at this character count
EMAIL_BODY_TRUNCATION_LIMIT = 32_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common case management setup issues. "
            "Looks for assignment rules, escalation rules, auto-response rules, "
            "and Email-to-Case routing address configuration problems."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational notes in addition to issues.",
    )
    return parser.parse_args()


def find_xml_files(base: Path, subdir: str, suffix: str = ".xml") -> list[Path]:
    """Return all XML files with the given suffix under every `<subdir>/`
    directory at any depth below base.

    A build tree keeps each step's metadata in its own folder
    (artefacts/M3-S04/assignmentRules/...), so `base/subdir` alone would miss
    everything when the checker is pointed at the tree root; the absence
    guards already recurse, and the two must see the same files.
    """
    found: set[Path] = set()
    for directory in [base / subdir, *base.rglob(subdir)]:
        if directory.is_dir():
            found.update(directory.rglob(f"*{suffix}"))
    return sorted(found)


def rule_elements(root, child_tag: str):
    """Return the individual rule elements inside a rules wrapper.

    Metadata-format files wrap rules: <AssignmentRules><assignmentRule>...,
    <EscalationRules><escalationRule>..., <AutoResponseRules><autoResponseRule>....
    <active> and <ruleEntry> live on the inner rule, not on the wrapper, so a
    checker that reads them from the root never sees an active rule. A file
    that has no wrapper children is treated as a single rule (source-format
    single-rule shape).
    """
    if root is None:
        return []
    inner = root.findall(f"{{{SF_NS}}}{child_tag}")
    return inner if inner else [root]


def xml_root(path: Path):
    """Parse an XML file and return the root element, or None on failure."""
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Remove the Salesforce namespace prefix from a tag name."""
    return tag.replace(f"{{{SF_NS}}}", "")


def text(element, *path: str) -> str:
    """Navigate a path of child tag names and return the text of the final element."""
    current = element
    for step in path:
        if current is None:
            return ""
        current = current.find(f"{{{SF_NS}}}{step}")
    return (current.text or "").strip() if current is not None else ""


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_assignment_rules(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check case assignment rule metadata for common problems."""
    issues: list[str] = []
    notes: list[str] = []

    files = find_xml_files(manifest_dir, "assignmentRules")
    case_rule_files = [f for f in files if "Case" in f.stem or "case" in f.stem.lower()]

    if not case_rule_files:
        # Also check top-level assignmentRules.xml
        top = manifest_dir / "assignmentRules" / "Case.assignmentRules"
        if top.exists():
            case_rule_files = [top]

    if not case_rule_files:
        # Distinguish "the rules are broken" from "the rules were not retrieved".
        # A manifest that carries no assignmentRules directory at all is a partial
        # retrieve (or a package that deliberately leaves rules to a sibling
        # deployment), not a misconfiguration this checker can assert.
        if not any(manifest_dir.rglob("assignmentRules")):
            notes.append(
                "No assignmentRules directory in this manifest. Assignment-rule checks skipped. "
                "Auto-response rules will NOT fire without an active assignment rule, so verify "
                "one exists in the target org (see references/gotchas.md #1)."
            )
            if verbose:
                for note in notes:
                    print(f"NOTE: {note}")
            return issues
        issues.append(
            "assignmentRules directory is present but contains no case assignment rule. "
            "Auto-response rules will NOT fire without an active assignment rule."
        )
        return issues

    active_rules = 0
    for path in case_rule_files:
        parsed = xml_root(path)
        if parsed is None:
            issues.append(f"Could not parse assignment rule file: {path}")
            continue

        for root in rule_elements(parsed, "assignmentRule"):

            active_val = text(root, "active")
            if active_val.lower() == "true":
                active_rules += 1

            rule_entries = root.findall(f"{{{SF_NS}}}ruleEntry")
            if active_val.lower() == "true" and not rule_entries:
                issues.append(
                    f"Active assignment rule '{path.stem}' has no rule entries. "
                    "Cases will fall to the default case owner — auto-response will not fire."
                )

            # Check for a catch-all entry (entry with no criteria)
            has_catchall = False
            for entry in rule_entries:
                criteria = entry.findall(f"{{{SF_NS}}}criteriaItems")
                formula = text(entry, "booleanFilter")
                if not criteria and not formula:
                    has_catchall = True
            if active_val.lower() == "true" and rule_entries and not has_catchall:
                notes.append(
                    f"Assignment rule '{path.stem}' has no catch-all entry (entry with no criteria). "
                    "Cases that do not match any entry go to the default case owner. "
                    "Consider adding a catch-all as the last entry."
                )

    if active_rules == 0:
        issues.append(
            "No active case assignment rule found in metadata. "
            "Auto-response rules depend on the assignment rule firing — "
            "without an active rule, auto-responses will not send."
        )
    elif active_rules > 1:
        issues.append(
            f"Found {active_rules} active case assignment rules in metadata. "
            "Salesforce only allows one active rule per object. "
            "Verify which rule is actually active in the org."
        )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


def check_escalation_rules(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check escalation rule metadata for missing business hours and other issues."""
    issues: list[str] = []
    notes: list[str] = []

    # Escalation rules are stored as escalationRules/Case.escalationRules
    candidate_paths = [
        manifest_dir / "escalationRules" / "Case.escalationRules",
        manifest_dir / "escalationRules" / "case.escalationRules",
    ]
    files = [p for p in candidate_paths if p.exists()]
    if not files:
        files = find_xml_files(manifest_dir, "escalationRules")

    if not files:
        notes.append("No escalation rule metadata found. Skipping escalation checks.")
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues

    for path in files:
        parsed = xml_root(path)
        if parsed is None:
            issues.append(f"Could not parse escalation rule file: {path}")
            continue

        for root in rule_elements(parsed, "escalationRule"):

            active_val = text(root, "active")
            if active_val.lower() != "true":
                notes.append(f"Escalation rule '{path.stem}' is not active.")
                continue

            rule_entries = root.findall(f"{{{SF_NS}}}ruleEntry")
            for i, entry in enumerate(rule_entries, start=1):
                biz_hours = text(entry, "businessHours")
                if not biz_hours:
                    issues.append(
                        f"Escalation rule '{path.stem}', entry {i}: "
                        "No business hours record attached. "
                        "Without business hours, the escalation clock runs 24/7 including weekends. "
                        "Attach a business hours record to this entry."
                    )

                # Actions live on <escalationAction> children of the entry (assignedTo,
                # notifyTo, notifyToTemplate, assignedToTemplate), not on the entry itself.
                actions = entry.findall(f"{{{SF_NS}}}escalationAction")
                acting = [
                    a for a in actions
                    if text(a, "assignedTo") or text(a, "notifyTo")
                    or text(a, "notifyToTemplate") or text(a, "assignedToTemplate")
                ]
                if not actions:
                    issues.append(
                        f"Escalation rule '{path.stem}', entry {i}: "
                        "No escalationAction. This escalation entry will match cases but take no action."
                    )
                elif not acting:
                    issues.append(
                        f"Escalation rule '{path.stem}', entry {i}: "
                        "escalationAction has no assignedTo user/queue and no notification target. "
                        "This escalation entry will fire but reassign and notify nobody."
                    )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


def check_auto_response_rules(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check auto-response rule metadata."""
    issues: list[str] = []
    notes: list[str] = []

    candidate_paths = [
        manifest_dir / "autoResponseRules" / "Case.autoResponseRules",
        manifest_dir / "autoResponseRules" / "case.autoResponseRules",
    ]
    files = [p for p in candidate_paths if p.exists()]
    if not files:
        files = find_xml_files(manifest_dir, "autoResponseRules")

    if not files:
        notes.append("No auto-response rule metadata found.")
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues

    for path in files:
        parsed = xml_root(path)
        if parsed is None:
            issues.append(f"Could not parse auto-response rule file: {path}")
            continue

        for root in rule_elements(parsed, "autoResponseRule"):

            active_val = text(root, "active")
            if active_val.lower() != "true":
                continue

            rule_entries = root.findall(f"{{{SF_NS}}}ruleEntry")
            for i, entry in enumerate(rule_entries, start=1):
                template = text(entry, "template")
                if not template:
                    issues.append(
                        f"Auto-response rule '{path.stem}', entry {i}: "
                        "No email template assigned. This entry will match but send no email."
                    )
                sender_type = text(entry, "senderType")
                sender_email = text(entry, "senderEmail")
                if not sender_type and not sender_email:
                    notes.append(
                        f"Auto-response rule '{path.stem}', entry {i}: "
                        "No sender type or email configured. "
                        "Verify the 'from' address is not the Email-to-Case routing address "
                        "(which would create an email loop)."
                    )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


def check_queues(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check queue metadata for Case support and membership."""
    issues: list[str] = []
    notes: list[str] = []

    queue_files = find_xml_files(manifest_dir, "queues")
    if not queue_files:
        notes.append("No queue metadata found in manifest directory.")
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues

    for path in queue_files:
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse queue file: {path}")
            continue

        # Check that Case is in the queue's supported objects
        sobject_types = [
            el.text or ""
            for el in root.findall(f"{{{SF_NS}}}queueSobject/{{{SF_NS}}}sobjectType")
        ]
        if "Case" not in sobject_types:
            issues.append(
                f"Queue '{path.stem}' does not have 'Case' in its supported objects. "
                "Cases cannot be assigned to this queue until 'Case' is added to "
                "the queue's Supported Objects list."
            )

        # Check for at least one member
        members = root.findall(f"{{{SF_NS}}}queueMembers")
        if not members:
            notes.append(
                f"Queue '{path.stem}' has no members defined in metadata. "
                "Queues with no active members cannot be accepted from by support agents."
            )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


def check_email_to_case_routing(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check for Email-to-Case routing configuration in CaseSettings metadata."""
    issues: list[str] = []
    notes: list[str] = []

    # CaseSettings contains Email-to-Case configuration. Match both the MDAPI file
    # name (Case.settings) and the DX source-format one (Case.settings-meta.xml).
    settings_paths = _case_settings_files(manifest_dir)

    if not settings_paths:
        notes.append("Case.settings metadata not found. Cannot verify Email-to-Case configuration.")
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues

    for path in settings_paths:
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse Case.settings: {path}")
            continue

        email_routing_addresses = root.findall(
            f"{{{SF_NS}}}emailToCase/{{{SF_NS}}}routingAddresses"
        )
        for i, addr in enumerate(email_routing_addresses, start=1):
            name = text(addr, "routingName")
            email_address = text(addr, "emailAddress")
            if not email_address:
                issues.append(
                    f"Email-to-Case routing address #{i} ('{name}'): "
                    "No email address configured. This routing address cannot receive emails."
                )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


def _child(element, name):
    """Return the named child Element, or None. Never use `a.find(x) or a.find(y)`:
    a childless Element is falsy, so `or` silently discards real matches."""
    if element is None:
        return None
    found = element.find(f"{{{SF_NS}}}{name}")
    return found if found is not None else None


def _is_true(element, name: str) -> bool:
    child = _child(element, name)
    return child is not None and (child.text or "").strip().lower() == "true"


def _has(element, name: str) -> bool:
    return _child(element, name) is not None


def _case_settings_files(manifest_dir: Path) -> list[Path]:
    """Locate Case.settings / Case.settings-meta.xml anywhere in the manifest."""
    found = sorted(
        set(manifest_dir.rglob("Case.settings"))
        | set(manifest_dir.rglob("Case.settings-meta.xml"))
    )
    return found


def _standard_value_set_files(manifest_dir: Path) -> dict[str, Path]:
    """Map standard value set name -> file, for the three Case intake value sets."""
    wanted = {"CaseOrigin", "CasePriority", "CaseStatus"}
    result: dict[str, Path] = {}
    for path in manifest_dir.rglob("*.standardValueSet*"):
        if not path.is_file():
            continue
        name = path.name.split(".")[0]
        if name in wanted:
            result[name] = path
    return result


def _standard_values(root) -> list[tuple[str, bool, bool]]:
    """Return (fullName, is_default, is_closed) for each <standardValue>."""
    values = []
    for value in root.findall(f"{{{SF_NS}}}standardValue"):
        name = text(value, "fullName")
        values.append((name, _is_true(value, "default"), _is_true(value, "closed")))
    return values


def check_case_settings(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check CaseSettings: the webToCase block and the org-level intake fields.

    Grounded in Metadata API Developer Guide, CaseSettings / WebToCaseSettings.
    """
    issues: list[str] = []
    notes: list[str] = []

    files = _case_settings_files(manifest_dir)
    if not files:
        notes.append(
            "No Case.settings file in this manifest. Web-to-Case and org-level case "
            "settings checks skipped."
        )
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues

    for path in files:
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse Case.settings: {path}")
            continue

        web = _child(root, "webToCase")
        origin_declared = ""
        if web is not None and _is_true(web, "enableWebToCase"):
            origin_declared = text(web, "caseOrigin")
            if not origin_declared:
                issues.append(
                    f"{path.name}: webToCase is enabled but has no <caseOrigin>. "
                    "Web submissions will be created with no Case Origin, so no assignment "
                    "rule can tell them apart from any other channel."
                )
            if _has(web, "defaultResponseTemplate"):
                notes.append(
                    f"{path.name}: webToCase/defaultResponseTemplate is set. The guide scopes "
                    "this to Self-Service portal responses, not the customer acknowledgement. "
                    "The acknowledgement is an AutoResponseRules entry (see admin/assignment-rules)."
                )

            # Web-to-Case has no owner field of its own; the org-level fallback must exist.
            if not text(root, "defaultCaseOwner"):
                issues.append(
                    f"{path.name}: webToCase is enabled but <defaultCaseOwner> is not set. "
                    "WebToCaseSettings has no owner field, so any submission the assignment "
                    "rule does not match falls to the org default (references/gotchas.md #8)."
                )
            elif text(root, "defaultCaseOwnerType").lower() == "user":
                notes.append(
                    f"{path.name}: defaultCaseOwnerType is User. Unrouted web cases will land "
                    "on one person's record set and be invisible to the team. Prefer a Queue."
                )

        if _has(root, "defaultCaseOwner") and not text(root, "defaultCaseOwnerType"):
            issues.append(
                f"{path.name}: <defaultCaseOwner> is set without <defaultCaseOwnerType>. "
                "The platform cannot tell whether the owner is a User or a Queue."
            )

        # useSystemUserAsDefaultCaseUser=false requires defaultCaseUser.
        sys_user = _child(root, "useSystemUserAsDefaultCaseUser")
        if sys_user is not None and (sys_user.text or "").strip().lower() == "false":
            if not text(root, "defaultCaseUser"):
                issues.append(
                    f"{path.name}: useSystemUserAsDefaultCaseUser is false but "
                    "<defaultCaseUser> is empty. The guide requires a value in that case; "
                    "without it, automated case changes have no attributable user in Case History."
                )

        # Suggested Articles and Suggested Solutions are mutually exclusive.
        if _is_true(root, "enableSuggestedArticlesApplication") and _is_true(
            root, "enableSuggestedSolutions"
        ):
            issues.append(
                f"{path.name}: enableSuggestedArticlesApplication and enableSuggestedSolutions "
                "are both true. The guide states each is only valid while the other is false."
            )

        # Origin declared on the web form must exist in the deployed CaseOrigin value set.
        if origin_declared:
            svs = _standard_value_set_files(manifest_dir)
            origin_file = svs.get("CaseOrigin")
            if origin_file is not None:
                origin_root = xml_root(origin_file)
                if origin_root is not None:
                    names = [v[0] for v in _standard_values(origin_root)]
                    if origin_declared not in names:
                        issues.append(
                            f"{path.name}: webToCase/caseOrigin is '{origin_declared}' but that "
                            f"value is not in {origin_file.name} ({', '.join(names) or 'no values'}). "
                            "Deploy the value set first (references/metadata-examples.md section 1)."
                        )
            else:
                notes.append(
                    f"{path.name}: webToCase/caseOrigin is '{origin_declared}'; no "
                    "CaseOrigin standardValueSet in this manifest to verify it against."
                )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


def check_standard_value_sets(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check the CaseOrigin / CasePriority / CaseStatus standard value sets."""
    issues: list[str] = []
    notes: list[str] = []

    svs = _standard_value_set_files(manifest_dir)
    if not svs:
        notes.append(
            "No CaseOrigin / CasePriority / CaseStatus standardValueSet files in this manifest. "
            "Value-set checks skipped."
        )
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues

    for name, path in sorted(svs.items()):
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse standard value set: {path}")
            continue

        values = _standard_values(root)
        if not values:
            issues.append(
                f"{path.name}: no <standardValue> elements. The guide states a StandardValueSet "
                "deploy fails unless the array contains at least one picklist value."
            )
            continue

        defaults = [v[0] for v in values if v[1]]
        if len(defaults) > 1:
            issues.append(
                f"{path.name}: {len(defaults)} values are marked default ({', '.join(defaults)}). "
                "A picklist has one default."
            )
        elif not defaults:
            notes.append(
                f"{path.name}: no value carries <default>true</default>. CustomValue.default is "
                "documented as required and defaulting to true, so state it explicitly on each value."
            )

        if not _has(root, "sorted"):
            notes.append(
                f"{path.name}: <sorted> is absent. The guide marks it Required; omitting it "
                "leaves the display order of the status ladder to the org's current setting."
            )

        if name == "CaseStatus":
            flagged_closed = [v[0] for v in values if v[2]]
            named_closed = [v[0] for v in values if "closed" in v[0].lower()]
            if not flagged_closed and not named_closed:
                issues.append(
                    f"{path.name}: no value is marked closed and none is named like a closed "
                    "state. Case.IsClosed is driven entirely by Status, so every case in this "
                    "org would count as open forever (references/gotchas.md #10)."
                )
            elif not flagged_closed:
                notes.append(
                    f"{path.name}: closed states are inferred from names ({', '.join(named_closed)}) "
                    "because no value carries <closed>true</closed>. Confirm with the CaseStatus "
                    "SOQL query in references/metadata-examples.md section 6 — the placement of "
                    "the closed flag in a modern retrieve is marked UNVERIFIED there."
                )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


def check_case_processes_and_record_types(manifest_dir: Path, verbose: bool) -> list[str]:
    """Check Case support processes and record types, nested or DX-decomposed."""
    issues: list[str] = []
    notes: list[str] = []

    # Collect the closed-status vocabulary, if the value set travelled with the package.
    closed_names: set[str] = set()
    all_status_names: set[str] = set()
    status_file = _standard_value_set_files(manifest_dir).get("CaseStatus")
    if status_file is not None:
        status_root = xml_root(status_file)
        if status_root is not None:
            for value_name, _default, is_closed in _standard_values(status_root):
                all_status_names.add(value_name)
                if is_closed or "closed" in value_name.lower():
                    closed_names.add(value_name)

    # Nested <CustomObject> form (the shape the Metadata API guide documents) plus
    # the DX-decomposed files, so either project format is checked.
    processes: list[tuple[str, str, list[str]]] = []   # (source, name, values)
    record_types: list[tuple[str, str, str]] = []      # (source, name, businessProcess)

    object_files = [
        p for p in manifest_dir.rglob("Case.object*")
        if p.is_file() and p.suffix in (".xml", ".object")
    ]
    for path in object_files:
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse Case object file: {path}")
            continue
        for bp in root.findall(f"{{{SF_NS}}}businessProcesses"):
            processes.append(
                (
                    path.name,
                    text(bp, "fullName"),
                    [text(v, "fullName") for v in bp.findall(f"{{{SF_NS}}}values")],
                )
            )
        for rt in root.findall(f"{{{SF_NS}}}recordTypes"):
            record_types.append((path.name, text(rt, "fullName"), text(rt, "businessProcess")))

    for path in manifest_dir.rglob("*.businessProcess-meta.xml"):
        root = xml_root(path)
        if root is None:
            continue
        processes.append(
            (
                path.name,
                text(root, "fullName") or path.name.split(".")[0],
                [text(v, "fullName") for v in root.findall(f"{{{SF_NS}}}values")],
            )
        )
    for path in manifest_dir.rglob("*.recordType-meta.xml"):
        if "Case" not in str(path):
            continue
        root = xml_root(path)
        if root is None:
            continue
        record_types.append(
            (path.name, text(root, "fullName") or path.name.split(".")[0], text(root, "businessProcess"))
        )

    if not processes and not record_types:
        notes.append(
            "No Case business processes or record types in this manifest. "
            "Support-process checks skipped."
        )
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues

    process_names = {name for _src, name, _values in processes}

    for source, name, values in processes:
        if not values:
            issues.append(
                f"{source}: business process '{name}' has no <values>. A support process is a "
                "subset of the CaseStatus value set; an empty one exposes no status at all."
            )
            continue
        if all_status_names:
            unknown = [v for v in values if v and v not in all_status_names]
            if unknown:
                issues.append(
                    f"{source}: business process '{name}' references Status values that are not "
                    f"in the deployed CaseStatus value set: {', '.join(unknown)}. "
                    "Deploy the value set first (references/metadata-examples.md section 1)."
                )
        if closed_names:
            if not any(v in closed_names for v in values):
                issues.append(
                    f"{source}: business process '{name}' exposes no closed status "
                    f"(closed values available: {', '.join(sorted(closed_names))}). "
                    "Agents on a record type using it cannot close a case, and it stays open "
                    "in every report forever (references/gotchas.md #10)."
                )
        elif not any("closed" in (v or "").lower() for v in values):
            notes.append(
                f"{source}: business process '{name}' has no value that looks like a closed "
                "status, and no CaseStatus value set in this manifest to check against."
            )

    for source, name, business_process in record_types:
        if not business_process:
            issues.append(
                f"{source}: Case record type '{name}' has no <businessProcess>. The Metadata API "
                "guide makes it required for case record types; the deploy will fail."
            )
        elif process_names and business_process not in process_names:
            issues.append(
                f"{source}: Case record type '{name}' names business process "
                f"'{business_process}', which is not defined in this manifest "
                f"({', '.join(sorted(process_names)) or 'none'}). Note the guide's naming rule: "
                "inside a CustomObject the value is the bare process name, never object-qualified."
            )
        if "." in business_process:
            issues.append(
                f"{source}: Case record type '{name}' uses the object-qualified form "
                f"'{business_process}' for <businessProcess>. Inside a CustomObject definition "
                "the enclosing object supplies the entity context — use the bare process name."
            )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


# Source-format decomposition: file stem is the package member the CLI declares.
BUSINESS_PROCESS_SUFFIX = ".businessProcess-meta.xml"
RECORD_TYPE_SUFFIX = ".recordType-meta.xml"


def _decomposed_stem(path: Path, suffix: str) -> str:
    """The file stem the sf CLI turns into a package.xml member.

    `Support_Process.businessProcess-meta.xml` -> `Support_Process`. Path.stem is
    wrong here (it would return `Support_Process.businessProcess`), and splitting
    on "." loses a stem that legitimately contains one.
    """
    return path.name[: -len(suffix)]


def check_source_format_stems(manifest_dir: Path, verbose: bool) -> list[str]:
    """CMS-STEM-01 / CMS-STEM-02 — decomposed file stems must equal their <fullName>.

    In a source-format (DX) tree the CLI names each package member from the file
    stem (`Support_Process.businessProcess-meta.xml` -> member `Case.Support_Process`)
    and then resolves that member against the component's <fullName>. A file whose
    stem and <fullName> disagree declares a member nothing satisfies:

        An object 'Case.Support_Process' of type BusinessProcess was named in
        package.xml, but was not found in zipped directory

    Verified by `sf project deploy start --dry-run` against a Summer '26 developer
    org on 2026-09-05 (examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md,
    runs 5 -> 6/7). See references/metadata-examples.md section 2.1 and
    references/gotchas.md #11 — including what is NOT claimed for metadata-format
    deploys with a hand-written package.xml.
    """
    issues: list[str] = []
    notes: list[str] = []

    process_files = sorted(manifest_dir.rglob(f"*{BUSINESS_PROCESS_SUFFIX}"))
    record_type_files = sorted(manifest_dir.rglob(f"*{RECORD_TYPE_SUFFIX}"))

    if not process_files and not record_type_files:
        notes.append(
            "No decomposed *.businessProcess-meta.xml / *.recordType-meta.xml files in this "
            "tree. CMS-STEM-01 and CMS-STEM-02 apply to source format only; a nested "
            "<CustomObject> definition is unaffected."
        )
        if verbose:
            for note in notes:
                print(f"NOTE: {note}")
        return issues

    # --- CMS-STEM-01: stem must equal <fullName>, and no <fullName> may hold a space.
    for path, suffix, type_name in (
        [(f, BUSINESS_PROCESS_SUFFIX, "BusinessProcess") for f in process_files]
        + [(f, RECORD_TYPE_SUFFIX, "RecordType") for f in record_type_files]
    ):
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse {type_name} file: {path}")
            continue
        stem = _decomposed_stem(path, suffix)
        element = _child(root, "fullName")
        full_name = (element.text or "").strip() if element is not None else ""

        if element is None:
            issues.append(
                f"CMS-STEM-01 {path}: {type_name} file has no <fullName>. The CLI declares the "
                f"member from the stem ('{stem}') and there is no component name for it to "
                "resolve against; add <fullName>" + stem + "</fullName>."
            )
            continue
        if full_name != stem:
            issues.append(
                f"CMS-STEM-01 {path}: <fullName> is '{full_name}' but the file stem is '{stem}'. "
                "In source format the CLI names the package member from the stem, so the deploy "
                f"fails with \"An object '<Object>.{stem}' of type {type_name} was named in "
                "package.xml, but was not found in zipped directory\". Rename the <fullName> to "
                "the stem (put the readable wording in <description>) and update every reference."
            )
            continue
        if " " in full_name:
            issues.append(
                f"CMS-STEM-01 {path}: <fullName> '{full_name}' contains a space. A file stem "
                "carrying a space is not a safe package member; use underscores "
                f"('{full_name.replace(' ', '_')}') and keep the display wording in <description>."
            )

    # --- CMS-STEM-02: a record type's <businessProcess> must name an existing process stem.
    if process_files:
        stems = {_decomposed_stem(f, BUSINESS_PROCESS_SUFFIX) for f in process_files}
        for path in record_type_files:
            root = xml_root(path)
            if root is None:
                continue
            business_process = text(root, "businessProcess")
            if not business_process:
                continue  # absence is check_case_processes_and_record_types' finding, not this one
            if business_process not in stems:
                issues.append(
                    f"CMS-STEM-02 {path}: <businessProcess> names '{business_process}', which is "
                    f"not the stem of any *.businessProcess-meta.xml in this tree "
                    f"({', '.join(sorted(stems)) or 'none'}). The record type will deploy against "
                    "a process the package never declares. Reference the process by its file stem, "
                    "bare (never object-qualified)."
                )

    if verbose:
        for note in notes:
            print(f"NOTE: {note}")

    return issues


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------


def check_case_management_setup(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Run all case management setup checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_assignment_rules(manifest_dir, verbose))
    issues.extend(check_escalation_rules(manifest_dir, verbose))
    issues.extend(check_auto_response_rules(manifest_dir, verbose))
    issues.extend(check_queues(manifest_dir, verbose))
    issues.extend(check_email_to_case_routing(manifest_dir, verbose))
    issues.extend(check_case_settings(manifest_dir, verbose))
    issues.extend(check_standard_value_sets(manifest_dir, verbose))
    issues.extend(check_case_processes_and_record_types(manifest_dir, verbose))
    issues.extend(check_source_format_stems(manifest_dir, verbose))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_case_management_setup(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No case management setup issues found.")
        return 0

    for issue in issues:
        if issue.startswith("CMS-STEM-"):
            print(f"ERROR: {issue}")
        else:
            print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
