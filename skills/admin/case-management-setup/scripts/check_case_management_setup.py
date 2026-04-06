#!/usr/bin/env python3
"""Checker script for Case Management Setup skill.

Inspects Salesforce metadata (retrieved via sfdx/sf force:source:retrieve or
equivalent) for common case management configuration issues.

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
    """Return all XML files under base/subdir with the given suffix."""
    target = base / subdir
    if not target.is_dir():
        return []
    return sorted(target.rglob(f"*{suffix}"))


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
        issues.append(
            "No case assignment rule metadata found. "
            "Auto-response rules will NOT fire without an active assignment rule."
        )
        return issues

    active_rules = 0
    for path in case_rule_files:
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse assignment rule file: {path}")
            continue

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
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse escalation rule file: {path}")
            continue

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

            assigned_to = text(entry, "assignedTo")
            notify_template = text(entry, "template")
            if not assigned_to and not notify_template:
                issues.append(
                    f"Escalation rule '{path.stem}', entry {i}: "
                    "No assignedTo user/queue and no notification template. "
                    "This escalation entry will match cases but take no action."
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
        root = xml_root(path)
        if root is None:
            issues.append(f"Could not parse auto-response rule file: {path}")
            continue

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

    # CaseSettings contains Email-to-Case configuration
    settings_paths = list((manifest_dir / "settings").glob("Case.settings") if
                          (manifest_dir / "settings").is_dir() else [])
    if not settings_paths:
        settings_paths = list(manifest_dir.rglob("Case.settings"))

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

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_case_management_setup(manifest_dir, verbose=args.verbose)

    if not issues:
        print("No case management setup issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
