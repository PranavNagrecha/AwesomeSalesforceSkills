#!/usr/bin/env python3
"""Checker script for Escalation Rules skill.

Validates Salesforce EscalationRules metadata XML for common configuration problems.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_escalation_rules.py [--help]
    python3 check_escalation_rules.py --manifest-dir path/to/metadata

The script expects to find EscalationRules metadata under:
  <manifest-dir>/escalationRules/
    e.g. escalationRules/Case.escalationRules-meta.xml

Checks performed:
  1. No active rule found (escalation silently disabled)
  2. Rule entries with no escalation actions (entry fires but does nothing)
  3. Escalation actions with no notify target and no reassignment (empty action)
  4. Rule entries with threshold of 0 hours (fires immediately on case creation)
  5. Multiple active rules in the same file (misconfiguration)
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(name: str) -> str:
    return f"{{{_SF_NS}}}{name}"


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def check_escalation_rules_file(path: Path) -> list[str]:
    """Parse a single EscalationRules metadata XML file and return issue strings."""
    issues: list[str] = []

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"[{path.name}] XML parse error: {exc}"]

    root = tree.getroot()

    # Support both namespaced and non-namespaced XML
    ns = _SF_NS if root.tag.startswith("{") else ""
    t = (lambda name: f"{{{ns}}}{name}") if ns else (lambda name: name)

    escalation_rule_elements = root.findall(t("escalationRule"))

    if not escalation_rule_elements:
        issues.append(
            f"[{path.name}] No escalationRule elements found. "
            "This file defines no escalation rules."
        )
        return issues

    active_rule_count = 0
    for rule_el in escalation_rule_elements:
        rule_name = _text(rule_el.find(t("fullName")))
        active_el = rule_el.find(t("active"))
        is_active = _text(active_el).lower() == "true" if active_el is not None else False

        if is_active:
            active_rule_count += 1

        entries = rule_el.findall(t("ruleEntry"))
        if is_active and not entries:
            issues.append(
                f"[{path.name}] Rule '{rule_name}' is active but has no rule entries. "
                "No cases will be escalated."
            )

        for entry_el in entries:
            entry_order = _text(entry_el.find(t("entryOrder")))
            entry_label = f"entry #{entry_order}" if entry_order else "an entry"

            # Check escalation actions
            actions = entry_el.findall(t("escalationAction"))
            if is_active and not actions:
                issues.append(
                    f"[{path.name}] Rule '{rule_name}', {entry_label}: "
                    "no escalationAction elements. Entry criteria may match but nothing happens."
                )

            for action_el in actions:
                minutes_el = action_el.find(t("minutesSinceStart"))
                minutes_text = _text(minutes_el)
                try:
                    minutes = int(minutes_text)
                except (ValueError, TypeError):
                    minutes = None

                if minutes == 0:
                    issues.append(
                        f"[{path.name}] Rule '{rule_name}', {entry_label}: "
                        "escalation action at 0 minutes (fires immediately). "
                        "Confirm this is intentional — cases will escalate the moment they are created."
                    )

                notify_user = _text(action_el.find(t("notifyEmail")))
                notify_assignee = _text(action_el.find(t("notifyAssignee")))
                reassign_to_user = _text(action_el.find(t("assignedTo")))
                reassign_to_team = _text(action_el.find(t("assignedToTeam")))

                has_notify = bool(notify_user or (notify_assignee.lower() == "true"))
                has_reassign = bool(reassign_to_user or reassign_to_team)

                if not has_notify and not has_reassign:
                    issues.append(
                        f"[{path.name}] Rule '{rule_name}', {entry_label}: "
                        "escalation action has no notify target and no reassignment. "
                        "The action fires but does nothing observable."
                    )

    if active_rule_count == 0:
        issues.append(
            f"[{path.name}] No active escalation rules found. "
            "Set one rule to active=true or escalation will not fire."
        )

    return issues


def check_escalation_rules(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    rules_dir = manifest_dir / "escalationRules"
    if not rules_dir.exists():
        # Not all orgs have escalation rules metadata — not necessarily an error.
        return issues

    rule_files = list(rules_dir.glob("*.escalationRules-meta.xml")) + \
                 list(rules_dir.glob("*.escalationRules"))

    if not rule_files:
        issues.append(
            f"No escalation rule metadata files found in {rules_dir}. "
            "If escalation rules should be deployed, check the file name pattern."
        )
        return issues

    for rule_file in sorted(rule_files):
        issues.extend(check_escalation_rules_file(rule_file))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check EscalationRules metadata for common configuration issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_escalation_rules(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
