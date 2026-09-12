#!/usr/bin/env python3
"""Checker script for the Escalation Rules skill.

Validates Salesforce EscalationRules metadata XML against the element names and
enum values in the Metadata API Developer Guide (`EscalationRules` section:
`EscalationRule`, `RuleEntry`, `EscalationAction`). Stdlib only.

Usage:
    python3 check_escalation_rules.py --manifest-dir force-app/main/default
    python3 check_escalation_rules.py --manifest-dir .sfskills/builds/<build>/artefacts/M4-S04
    python3 check_escalation_rules.py --help

Expects the metadata under:
    <manifest-dir>/escalationRules/Case.escalationRules-meta.xml

Reassignment targets are resolved against the same manifest:
    <manifest-dir>/queues/<Name>.queue-meta.xml
    <manifest-dir>/users/<Name>.user-meta.xml

Exit code
---------
ERROR findings exit 1. WARN and INFO findings are always printed but exit 0:
a warning is a judgement call a reviewer has to make (is a 15-minute first
response really what the SLA says?), and a lint that fails the build on a
judgement call gets suppressed rather than read. Everything that means "this
package escalates nothing" is an ERROR.

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
  E7  An <assignedTo> that names a queue or user the manifest does not contain,
      while the manifest does carry queue/user metadata of that kind. Deploying
      an escalation action whose target does not exist fails at deploy time or,
      worse, silently escalates into nothing.
  E8  An active rule has no <ruleEntry>: the rule is live and nothing escalates.
  E9  An active entry has no <escalationAction>: the entry can match and nothing
      happens.
  E10 An action has <notifyCaseOwner>true</notifyCaseOwner> or a non-empty
      <notifyTo>, and no non-empty <notifyToTemplate>. Neither field carries a
      Required marker in the guide's EscalationAction table, but a dry-run
      deploy of exactly this shape fails: "EscalationRules Case:
      notifyToTemplate is required". UNVERIFIED (2026-09-12): proven live, not
      stated in the guide.

WARN (printed, exit 0)
  W0  No EscalationRules file found under --manifest-dir.
  W1  No rule in the file is active.
  W4  An action neither notifies (notifyTo / notifyEmail / notifyCaseOwner)
      nor reassigns (assignedTo) — it fires and does nothing observable.
  W5  Two actions on the same entry share a <minutesToEscalation> value.
  W6  <minutesToEscalation> below 60 or above 43200 (30 days). Both ends are
      legal metadata; both are where the hours-for-minutes transcription error
      shows up (an 8-business-hour SLA is 480, not 8).

INFO (printed, exit 0)
  I1  An entry has neither <criteriaItems> nor <formula>: a catch-all that
      matches every case. Legitimate as the last entry, a bug anywhere else.
  I2  Action count per entry, reported for review. The commonly cited ceiling of
      five actions per entry is NOT in the Metadata API guide's EscalationAction
      table and NOT in the App Limits cheat sheet, so it is reported, not enforced.
  I3  minutesToEscalation restated in hours, so an hours-for-minutes
      transcription error is visible in the lint output.
  I4  notifyToTemplate or assignedToTemplate is set but is not folder-qualified
      (<folder>/<name>). Both resolve at deploy time by folder path, the same
      way an assignedTo queue/user name resolves against the manifest (E7).
      Reported, not enforced — a template can legitimately live in a
      root-less personal folder.

Worked examples
---------------
Build a manifest from ``references/metadata-examples.md`` (the two ``escalationRules``
fences under ``escalationRules/``) and the checker exits 0 with INFO notes only::

    $ python3 check_escalation_rules.py --manifest-dir /tmp/fixture
    INFO  I2  [Case.escalationRules-meta.xml :: Support_SLA_Escalation :: entry 1] 2 ...
    WARN  W6  [... :: action 1] minutesToEscalation 15 is below 60 ...
    OK: no ERROR findings (1 warning(s), 10 info note(s)).
    $ echo $?
    0

An action that notifies the case owner with no ``notifyToTemplate`` — valid XML,
rejected only at org validation (``EscalationRules Case: notifyToTemplate is
required``), caught here before the deploy::

    $ python3 check_escalation_rules.py --manifest-dir /tmp/e10-negative
    ERROR E10  [... :: action 1] notifyCaseOwner is true but notifyToTemplate is
               empty. ... Set notifyToTemplate to a folder-qualified Classic
               email template, e.g. 'unfiled$public/Template_Name'.
    1 error(s), 0 warning(s), 2 info note(s).
    $ echo $?
    1

The hours-for-minutes transcription error, with a target that is not in the
package (``minutesToEscalation`` 8, ``assignedTo`` ``Nonexistent_Queue``,
alongside ``queues/Tier_1_Support.queue-meta.xml``)::

    $ python3 check_escalation_rules.py --manifest-dir /tmp/broken
    ERROR E7  [... :: action 1] assignedTo 'Nonexistent_Queue' (assignedToType Queue)
              is not among the 1 queue(s) in this manifest: Tier_1_Support.
    WARN  W6  [... :: action 1] minutesToEscalation 8 is below 60 ...
    1 error(s), 1 warning(s), 2 info note(s).
    $ echo $?
    1

An active rule with no entries, and an active entry with no actions::

    $ python3 check_escalation_rules.py --manifest-dir /tmp/empty-rule
    ERROR E8  [Case.escalationRules-meta.xml] rule 'Support_SLA' is active but has
              no <ruleEntry>. Nothing escalates.
    $ echo $?
    1

An empty manifest is not an error, but it is never silent::

    $ python3 check_escalation_rules.py --manifest-dir /tmp/nothing
    WARN  W0  [/tmp/nothing] no EscalationRules files found under --manifest-dir.
    $ echo $?
    0
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

# minutesToEscalation is minutes. Below an hour or above 30 days is legal metadata
# and is also exactly where an hours-for-minutes transcription error lands.
_MIN_PLAUSIBLE_MINUTES = 60
_MAX_PLAUSIBLE_MINUTES = 43200


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


def _fullname_of(path: Path) -> str:
    """Developer name of a metadata file: its <fullName>, else the file stem.

    Retrieved source files usually omit <fullName> because the file name carries
    it; hand-written ones sometimes include it. Both are accepted.
    """
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return path.name.split(".")[0]
    t = _tagger(root)
    declared = _text(root, t("fullName"))
    return declared or path.name.split(".")[0]


def index_manifest_targets(manifest_dir: Path) -> dict[str, set[str]]:
    """Return the queue and user developer names this manifest actually contains.

    An empty set means "this manifest carries no metadata of that kind", which is
    different from "the target is missing": escalation rules routinely point at
    queues that already live in the org and are not part of the change. E7 fires
    only when the manifest does carry queues (or users) and the named one is not
    among them.
    """
    queues = {
        _fullname_of(f)
        for f in manifest_dir.rglob("*.queue-meta.xml")
    }
    users = {
        _fullname_of(f)
        for f in manifest_dir.rglob("*.user-meta.xml")
    }
    return {"Queue": queues, "User": users}


def check_escalation_rules_file(
    path: Path, targets: dict[str, set[str]] | None = None
) -> list[Finding]:
    """Parse one EscalationRules metadata file and return its findings.

    ``targets`` is the index from :func:`index_manifest_targets`. Passing None
    skips E7 (nothing to resolve against).
    """
    findings: list[Finding] = []
    name = path.name
    targets = targets or {}

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
                    "ERROR", "E8", name,
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
                        "ERROR", "E9", where,
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
                    if minutes < _MIN_PLAUSIBLE_MINUTES:
                        findings.append(
                            Finding(
                                "WARN", "W6", action_where,
                                f"minutesToEscalation {minutes} is below "
                                f"{_MIN_PLAUSIBLE_MINUTES} ({_hours(minutes)}). Legal, but this "
                                "is where an hours-for-minutes transcription error lands: if the "
                                f"agreed SLA is {minutes} business hours the value is "
                                f"{minutes * 60}, not {minutes}. Confirm against the SLA.",
                            )
                        )
                    elif minutes > _MAX_PLAUSIBLE_MINUTES:
                        findings.append(
                            Finding(
                                "WARN", "W6", action_where,
                                f"minutesToEscalation {minutes} is above "
                                f"{_MAX_PLAUSIBLE_MINUTES} ({_hours(minutes)}, over 30 days). "
                                "Legal, but confirm the unit — this is minutes, not seconds.",
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

                # --- E7: does the reassignment target exist in this manifest? --
                known = targets.get(assigned_type) if assigned_type else None
                if assigned_to and known and assigned_to not in known:
                    noun = "queue" if assigned_type == "Queue" else "user"
                    findings.append(
                        Finding(
                            "ERROR", "E7", action_where,
                            f"assignedTo '{assigned_to}' (assignedToType {assigned_type}) is "
                            f"not among the {len(known)} {noun}(s) in this manifest: "
                            + ", ".join(sorted(known))
                            + ". Deploy the target with the rule, or correct the name.",
                        )
                    )

                # --- W4: does the action do anything? -----------------------
                notify_case_owner = _text(action, t("notifyCaseOwner")).lower() == "true"
                notify_to = _text(action, t("notifyTo"))
                notify_email = _text(action, t("notifyEmail"))
                notify_to_template = _text(action, t("notifyToTemplate"))
                assigned_to_template = _text(action, t("assignedToTemplate"))
                notifies = bool(notify_to or notify_email or notify_case_owner)
                if not notifies and not assigned_to:
                    findings.append(
                        Finding(
                            "WARN", "W4", action_where,
                            "action neither notifies (notifyTo / notifyEmail / "
                            "notifyCaseOwner) nor reassigns (assignedTo). It fires and does "
                            "nothing observable.",
                        )
                    )

                # --- E10: notifyToTemplate is required whenever the case owner or
                # a named user is notified. Not stated as Required in the Metadata
                # API guide's EscalationAction table (notifyCaseOwner, notifyTo,
                # notifyToTemplate all carry plain `string`/`boolean` types with no
                # Required marker), but proven live: a dry-run deploy of an action
                # with notifyCaseOwner true and no notifyToTemplate fails with
                # "EscalationRules Case: notifyToTemplate is required". -----------
                if (notify_case_owner or notify_to) and not notify_to_template:
                    trigger = (
                        "notifyCaseOwner is true" if notify_case_owner
                        else f"notifyTo is '{notify_to}'"
                    )
                    findings.append(
                        Finding(
                            "ERROR", "E10", action_where,
                            f"{trigger} but notifyToTemplate is empty. "
                            "UNVERIFIED (2026-09-12): not marked Required in the Metadata "
                            "API guide's EscalationAction table, but proven live in a "
                            "dry-run deploy: \"EscalationRules Case: notifyToTemplate is "
                            "required\". Set notifyToTemplate to a folder-qualified Classic "
                            "email template, e.g. 'unfiled$public/Template_Name'.",
                        )
                    )

                # --- I4: template names resolve at deploy time by folder path,
                # the same way an assignedTo queue/user name resolves against the
                # manifest (E7 above). An unqualified name is not wrong metadata —
                # it is reported, not enforced, because a template can legitimately
                # live in a root-less personal folder — but it is where a copy-paste
                # from a different org silently points at the wrong folder. --------
                for template_field, template_value in (
                    ("notifyToTemplate", notify_to_template),
                    ("assignedToTemplate", assigned_to_template),
                ):
                    if template_value and "/" not in template_value:
                        findings.append(
                            Finding(
                                "INFO", "I4", action_where,
                                f"{template_field} '{template_value}' is not "
                                "folder-qualified (<folder>/<name>, e.g. "
                                "'unfiled$public/Template_Name'). Deploy-time resolution "
                                "matches by folder and name; confirm this is deliberate.",
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

    rule_files = sorted(
        set(manifest_dir.rglob("*.escalationRules-meta.xml"))
        | set(manifest_dir.rglob("*.escalationRules"))
    )

    if not rule_files:
        # Not every package deploys escalation rules; absence is not a failure.
        # It is never silent either: a step that was supposed to build one and
        # built nothing must not read as a clean pass.
        return [
            Finding(
                "WARN", "W0", str(manifest_dir),
                "no EscalationRules files found under --manifest-dir (looked for "
                "*.escalationRules-meta.xml anywhere beneath it). Nothing was checked.",
            )
        ]

    targets = index_manifest_targets(manifest_dir)
    findings: list[Finding] = []
    for rule_file in rule_files:
        findings.extend(check_escalation_rules_file(rule_file, targets))
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

    if not errors:
        print(
            f"OK: no ERROR findings ({len(warnings)} warning(s), "
            f"{len(infos)} info note(s)). Warnings are judgement calls — read them."
        )
        return 0

    print(
        f"\n{len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info note(s)."
    )
    return 1


if __name__ == "__main__":
    if main() != 0:
        sys.exit(1)
    sys.exit(0)
