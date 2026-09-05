#!/usr/bin/env python3
"""Checker script for the Escalation Rules skill.

Validates Salesforce EscalationRules metadata XML against the element names and
enum values in the Metadata API Developer Guide (`EscalationRules` section:
`EscalationRule`, `RuleEntry`, `EscalationAction`). Stdlib only.

Usage:
    python3 check_escalation_rules.py --manifest-dir force-app/main/default
    python3 check_escalation_rules.py --help

Expects the metadata under:
    <manifest-dir>/escalationRules/Case.escalationRules-meta.xml

Findings are tagged ERROR / WARN / INFO.

ERROR (exit 1)
  E1  More than one <escalationRule> in the file has <active>true</active>.
  E2  <businessHoursSource>Static</businessHoursSource> with no <businessHours>,
      or <businessHours> on an entry whose source is not Static. The guide:
      "Specify only if businessHoursSource is set to Static."
  E3  <minutesToEscalation> missing, non-numeric, or not a positive integer.
  E4  <assignedTo> present without <assignedToType> (User | Queue), or an
      <assignedToType> that is not one of those two values.
  E5  An entry sets both <criteriaItems> and <formula>. The guide:
      "Specify either formula or criteriaItems, but not both fields."
  E6  <businessHoursSource> or <escalationStartTime> set to a value outside the
      documented enum.

WARN (exit 1)
  W1  No rule in the file is active.
  W2  An active rule has no <ruleEntry>.
  W3  An active entry has no <escalationAction>.
  W4  An action neither notifies (notifyTo / notifyEmail / notifyCaseOwner)
      nor reassigns (assignedTo) — it fires and does nothing observable.
  W5  Two actions on the same entry share a <minutesToEscalation> value.

INFO (does not fail)
  I1  An entry has neither <criteriaItems> nor <formula>: a catch-all that
      matches every case. Legitimate as the last entry, a bug anywhere else.
  I2  Action count per entry, reported for review. The commonly cited ceiling of
      five actions per entry is NOT in the Metadata API guide's EscalationAction
      table and NOT in the App Limits cheat sheet, so it is reported, not enforced.
  I3  minutesToEscalation restated in hours, so an hours-for-minutes
      transcription error is visible in the lint output.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Documented enum values (Metadata API guide, RuleEntry field table).
_BUSINESS_HOURS_SOURCES = {"None", "Case", "Static"}
_ESCALATION_START_TIMES = {"CaseCreation", "CaseLastModified"}
_ASSIGNED_TO_TYPES = {"User", "Queue"}


class Finding:
    """One check result. Severity is ERROR, WARN or INFO."""

    def __init__(self, severity: str, code: str, where: str, message: str) -> None:
        self.severity = severity
        self.code = code
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity:5} {self.code}  [{self.where}] {self.message}"


def _tagger(root: ET.Element):
    """Return a function mapping a local name to the tag used by this document.

    Handles both namespaced files (as retrieved) and bare files (hand-written).
    """
    if root.tag.startswith("{"):
        namespace = root.tag[1:].split("}", 1)[0]
        return lambda name: f"{{{namespace}}}{name}"
    return lambda name: name


def _child(parent: ET.Element, tag: str) -> ET.Element | None:
    """Return the first child with this tag, or None.

    Never write `parent.find(a) or parent.find(b)`: an Element with no children
    is falsy, so a real-but-empty element would be discarded. Presence is always
    tested with `is not None`.
    """
    found = parent.find(tag)
    return found if found is not None else None


def _text(parent: ET.Element, tag: str) -> str:
    """Text of the first child with this tag, stripped. Empty string if absent."""
    element = _child(parent, tag)
    if element is None:
        return ""
    return (element.text or "").strip()


def _has(parent: ET.Element, tag: str) -> bool:
    return _child(parent, tag) is not None


def _positive_int(raw: str) -> int | None:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _hours(minutes: int) -> str:
    if minutes % 60 == 0:
        return f"{minutes // 60}h"
    return f"{minutes / 60:.2f}h"


def check_escalation_rules_file(path: Path) -> list[Finding]:
    """Parse one EscalationRules metadata file and return its findings."""
    findings: list[Finding] = []
    name = path.name

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Finding("ERROR", "E0", name, f"XML parse error: {exc}")]

    t = _tagger(root)
    rules = root.findall(t("escalationRule"))

    if not rules:
        return [
            Finding(
                "WARN", "W1", name,
                "no <escalationRule> elements; this file defines no escalation rules.",
            )
        ]

    active_rule_names: list[str] = []

    for rule in rules:
        rule_name = _text(rule, t("fullName")) or "(unnamed rule)"
        is_active = _text(rule, t("active")).lower() == "true"
        if is_active:
            active_rule_names.append(rule_name)

        entries = rule.findall(t("ruleEntry"))
        if is_active and not entries:
            findings.append(
                Finding(
                    "WARN", "W2", name,
                    f"rule '{rule_name}' is active but has no <ruleEntry>. Nothing escalates.",
                )
            )

        for index, entry in enumerate(entries, start=1):
            where = f"{name} :: {rule_name} :: entry {index}"

            # --- E2 / E6: clock configuration -----------------------------
            source = _text(entry, t("businessHoursSource"))
            has_calendar = _has(entry, t("businessHours"))
            calendar = _text(entry, t("businessHours"))

            if source and source not in _BUSINESS_HOURS_SOURCES:
                findings.append(
                    Finding(
                        "ERROR", "E6", where,
                        f"businessHoursSource '{source}' is not one of "
                        f"{sorted(_BUSINESS_HOURS_SOURCES)}.",
                    )
                )
            elif source == "Static" and not calendar:
                findings.append(
                    Finding(
                        "ERROR", "E2", where,
                        "businessHoursSource is Static but <businessHours> is missing or "
                        "empty. The guide: specify businessHours only if businessHoursSource "
                        "is Static — and Static without it names no calendar.",
                    )
                )
            elif has_calendar and source != "Static":
                findings.append(
                    Finding(
                        "ERROR", "E2", where,
                        f"<businessHours>{calendar}</businessHours> is set but "
                        f"businessHoursSource is '{source or '(absent)'}'. The named calendar "
                        "is ignored unless the source is Static.",
                    )
                )

            start_time = _text(entry, t("escalationStartTime"))
            if start_time and start_time not in _ESCALATION_START_TIMES:
                findings.append(
                    Finding(
                        "ERROR", "E6", where,
                        f"escalationStartTime '{start_time}' is not one of "
                        f"{sorted(_ESCALATION_START_TIMES)}.",
                    )
                )

            # --- E5 / I1: criteria ----------------------------------------
            criteria = entry.findall(t("criteriaItems"))
            has_formula = _has(entry, t("formula"))

            if criteria and has_formula:
                findings.append(
                    Finding(
                        "ERROR", "E5", where,
                        "entry sets both <criteriaItems> and <formula>. The guide: specify "
                        "either formula or criteriaItems, but not both fields.",
                    )
                )
            elif not criteria and not has_formula:
                findings.append(
                    Finding(
                        "INFO", "I1", where,
                        "no <criteriaItems> and no <formula>: this entry matches every case. "
                        "Fine as the last entry; anything below it is unreachable.",
                    )
                )

            # --- actions ---------------------------------------------------
            actions = entry.findall(t("escalationAction"))
            if is_active and not actions:
                findings.append(
                    Finding(
                        "WARN", "W3", where,
                        "no <escalationAction>: the entry can match but nothing happens.",
                    )
                )

            if actions:
                findings.append(
                    Finding(
                        "INFO", "I2", where,
                        f"{len(actions)} escalation action(s) on this entry. The "
                        "five-actions-per-entry ceiling is not in the Metadata API guide or "
                        "the App Limits cheat sheet, so this is reported, not enforced.",
                    )
                )

            seen_minutes: dict[int, int] = {}

            for action_index, action in enumerate(actions, start=1):
                action_where = f"{where} :: action {action_index}"

                # --- E3 / I3: threshold ------------------------------------
                raw_minutes = _text(action, t("minutesToEscalation"))
                minutes = _positive_int(raw_minutes)
                if minutes is None:
                    shown_value = repr(raw_minutes) if raw_minutes else "missing"
                    findings.append(
                        Finding(
                            "ERROR", "E3", action_where,
                            f"minutesToEscalation is {shown_value}; it must be a "
                            "positive integer number of minutes.",
                        )
                    )
                else:
                    findings.append(
                        Finding(
                            "INFO", "I3", action_where,
                            f"minutesToEscalation {minutes} = {_hours(minutes)}. Setup shows "
                            "hours; the metadata is minutes. Confirm against the agreed SLA.",
                        )
                    )
                    if minutes in seen_minutes:
                        findings.append(
                            Finding(
                                "WARN", "W5", action_where,
                                f"same minutesToEscalation ({minutes}) as action "
                                f"{seen_minutes[minutes]} on this entry.",
                            )
                        )
                    else:
                        seen_minutes[minutes] = action_index

                # --- E4: reassignment target -------------------------------
                assigned_to = _text(action, t("assignedTo"))
                assigned_type_present = _has(action, t("assignedToType"))
                assigned_type = _text(action, t("assignedToType"))

                if assigned_to and not assigned_type:
                    findings.append(
                        Finding(
                            "ERROR", "E4", action_where,
                            f"<assignedTo>{assigned_to}</assignedTo> without a usable "
                            "<assignedToType>. Set User or Queue, or the target is ambiguous.",
                        )
                    )
                elif assigned_type and assigned_type not in _ASSIGNED_TO_TYPES:
                    findings.append(
                        Finding(
                            "ERROR", "E4", action_where,
                            f"assignedToType '{assigned_type}' is not one of "
                            f"{sorted(_ASSIGNED_TO_TYPES)}.",
                        )
                    )
                elif assigned_type_present and not assigned_to:
                    findings.append(
                        Finding(
                            "WARN", "W4", action_where,
                            "assignedToType is set but assignedTo is empty: no reassignment "
                            "happens.",
                        )
                    )

                # --- W4: does the action do anything? -----------------------
                notifies = bool(
                    _text(action, t("notifyTo"))
                    or _text(action, t("notifyEmail"))
                    or _text(action, t("notifyCaseOwner")).lower() == "true"
                )
                if not notifies and not assigned_to:
                    findings.append(
                        Finding(
                            "WARN", "W4", action_where,
                            "action neither notifies (notifyTo / notifyEmail / "
                            "notifyCaseOwner) nor reassigns (assignedTo). It fires and does "
                            "nothing observable.",
                        )
                    )

    if len(active_rule_names) > 1:
        findings.append(
            Finding(
                "ERROR", "E1", name,
                "more than one active rule in this file: "
                + ", ".join(f"'{n}'" for n in active_rule_names)
                + ". Deploy the replacement with active=false and flip the flag separately.",
            )
        )
    elif not active_rule_names:
        findings.append(
            Finding(
                "WARN", "W1", name,
                "no rule in this file is active. Nothing escalates until one is.",
            )
        )

    return findings


def check_escalation_rules(manifest_dir: Path) -> list[Finding]:
    """Return findings for every EscalationRules file under the manifest directory."""
    if not manifest_dir.exists():
        return [
            Finding("ERROR", "E0", str(manifest_dir), "manifest directory not found.")
        ]

    rules_dir = manifest_dir / "escalationRules"
    if not rules_dir.exists():
        # Not every project deploys escalation rules; absence is not a failure.
        return []

    rule_files = sorted(
        set(rules_dir.glob("*.escalationRules-meta.xml"))
        | set(rules_dir.glob("*.escalationRules"))
    )

    if not rule_files:
        return [
            Finding(
                "WARN", "W0", str(rules_dir),
                "escalationRules folder exists but holds no *.escalationRules-meta.xml file.",
            )
        ]

    findings: list[Finding] = []
    for rule_file in rule_files:
        findings.extend(check_escalation_rules_file(rule_file))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check EscalationRules metadata for configuration problems.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--quiet-info",
        action="store_true",
        help="Suppress INFO findings; print only ERROR and WARN.",
    )
    args = parser.parse_args(argv)

    findings = check_escalation_rules(Path(args.manifest_dir))

    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARN"]
    infos = [f for f in findings if f.severity == "INFO"]

    shown = errors + warnings + ([] if args.quiet_info else infos)
    for finding in shown:
        print(finding)

    if not errors and not warnings:
        print(f"OK: no ERROR or WARN findings ({len(infos)} INFO note(s)).")
        return 0

    print(
        f"\n{len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info note(s)."
    )
    return 1


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        sys.exit(1)
    sys.exit(0)
