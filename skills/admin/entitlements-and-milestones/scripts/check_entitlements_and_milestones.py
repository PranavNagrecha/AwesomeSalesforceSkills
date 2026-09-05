#!/usr/bin/env python3
"""Checker script for the Entitlements and Milestones skill.

Validates Salesforce Entitlement Management metadata against the element names,
enum values and cardinality documented in the Metadata API Developer Guide
(``EntitlementProcess`` / ``EntitlementProcessMilestoneItem`` /
``EntitlementProcessMilestoneTimeTrigger`` at api_meta.txt:59069-59308,
``MilestoneType`` at 88319-88380, ``EntitlementSettings`` at 115601-115730) and
the Object Reference (``SlaProcess`` at object_reference.txt:270637-270790).
Stdlib only.

Usage:
    python3 check_entitlements_and_milestones.py --manifest-dir force-app/main/default
    python3 check_entitlements_and_milestones.py --help

Expects metadata under:
    <manifest-dir>/entitlementProcesses/*.entitlementProcess-meta.xml
    <manifest-dir>/milestoneTypes/*.milestoneType-meta.xml
    <manifest-dir>/settings/BusinessHours.settings-meta.xml   (optional)

Findings are tagged ERROR / WARN / INFO. ERROR exits 1. WARN and INFO are
always printed and exit 0, unless ``--strict`` is passed, which makes WARN exit
1 too.

ERROR (exit 1)
  E1  <minutesToComplete> missing, non-numeric, or not a positive integer. The
      guide types it int, "the number of minutes from when the case enters the
      entitlement process that the milestone occurs" (api_meta.txt:59191-59193).
  E2  Two or more process files that share a <versionMaster> both set
      <isVersionDefault>true</isVersionDefault>. Only one version of a process
      can be the default (api_meta.txt:59136-59139).
  E3  <workflowTimeTriggerUnit> outside the documented enum Minutes | Hours |
      Days (api_meta.txt:59220-59224), or <timeLength> non-numeric.
  E4  <SObjectType> outside the documented picklist Case | Work Order
      (object_reference.txt:270729-270737), or <recurrenceType> on a
      MilestoneType outside none | recursIndependently | recursChained
      (api_meta.txt:88337-88345).

WARN (printed, exit 0)
  W1  An active process (<active>true</active>) declares no <milestones>. It
      deploys, enters cases, and tracks nothing.
  W2  A <milestoneName> does not match any MilestoneType file in the tree. The
      milestone definition has to exist for the process to bind to it.
  W3  A process names <businessHours> that is not a <name> in the
      BusinessHours settings file, when that file is present in the tree. Same
      check for milestone-level <businessHours>.
  W4  A milestone has no <timeTriggers> and no <successActions>: no warning,
      no violation, no completion action. Nothing observable happens.
  W5  No process file in the tree sets <isVersionDefault>true</isVersionDefault>
      for a given <versionMaster>.
  W6  A process (or a milestone override) names <businessHours> and there is no
      BusinessHours settings file anywhere in the tree, so the name could not be
      resolved at all. That is what a partial retrieve looks like, and what a
      build step that does not own settings/BusinessHours.settings-meta.xml
      looks like — so it is a warning about scope, not an error about the
      process. Silence would be worse: it reads as "checked and clean".

INFO (does not fail on its own)
  I1  A milestone has violation triggers (positive <timeLength>) but no warning
      trigger (negative <timeLength>): the first anybody hears about the SLA is
      the breach itself. Legal, so this is reported rather than enforced. Note
      that the sign convention makes a violation firing literally before a
      warning impossible to express -- the ordering risk is a missing warning,
      or two triggers landing on the same minute (I4).
  I2  Each trigger restated as "minutes elapsed" against the milestone target,
      so a percentage-for-offset transcription error is visible in lint output.
  I3  No entitlement process files found at all.
  I4  Two triggers on one milestone resolve to the same elapsed minute once
      units are normalised -- usually a copy-paste with the unit not updated.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Documented enums.
_TIME_UNITS = {"Minutes", "Hours", "Days"}
_SOBJECT_TYPES = {"Case", "Work Order"}
_RECURRENCE_TYPES = {"none", "recursIndependently", "recursChained"}

# Minutes per unit, for normalising timeLength.
_UNIT_MINUTES = {"Minutes": 1, "Hours": 60, "Days": 1440}


class Finding:
    """One check result. Severity is ERROR, WARN or INFO."""

    def __init__(self, severity: str, code: str, where: str, message: str) -> None:
        self.severity = severity
        self.code = code
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity:5} {self.code}  [{self.where}] {self.message}"


# ---------------------------------------------------------------------------
# XML helpers
#
# NEVER write `element.find(a) or element.find(b)`: an ElementTree element with
# no children is falsy even when it exists, so a present-but-empty element is
# silently skipped. Every accessor below tests `is not None`.
# ---------------------------------------------------------------------------

def _local(tag: str) -> str:
    """Strip any namespace from an XML tag."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    """Every direct child of element whose local name is `name`."""
    return [child for child in element if _local(child.tag) == name]


def _child(element: ET.Element, name: str) -> ET.Element | None:
    """The first direct child with local name `name`, or None."""
    found = _children(element, name)
    if not found:
        return None
    return found[0]


def _text(element: ET.Element | None) -> str:
    """Stripped text of an element, tolerating None and empty elements."""
    if element is None:
        return ""
    return (element.text or "").strip()


def _child_text(element: ET.Element, name: str) -> str:
    """Stripped text of the first child with local name `name`, or ''."""
    return _text(_child(element, name))


def _parse(path: Path) -> ET.Element | None:
    """Parse an XML file, returning the root element or None on a parse error."""
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def _files(root: Path, folder: str, suffix: str) -> list[Path]:
    """Metadata files of one type, whether or not they carry the -meta.xml tail."""
    base = root / folder
    search_root = base if base.is_dir() else root
    return sorted(
        set(search_root.rglob(f"*{suffix}-meta.xml")) | set(search_root.rglob(f"*{suffix}"))
    )


def _int_or_none(raw: str) -> int | None:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Inventory gathering
# ---------------------------------------------------------------------------

def _milestone_type_names(root: Path) -> set[str]:
    """Milestone type names available in the tree, taken from the file names."""
    names: set[str] = set()
    for path in _files(root, "milestoneTypes", ".milestoneType"):
        name = path.name
        for tail in (".milestoneType-meta.xml", ".milestoneType"):
            if name.endswith(tail):
                name = name[: -len(tail)]
                break
        names.add(name)
    return names


def _business_hours_names(root: Path) -> set[str] | None:
    """Calendar names from settings/BusinessHours.settings, or None if absent.

    None means "no settings file in this tree", which is different from "the
    file is here and contains no calendars" — only the latter is worth a WARN.
    """
    candidates = sorted(
        set(root.rglob("BusinessHours.settings-meta.xml"))
        | set(root.rglob("BusinessHours.settings"))
        | set(root.rglob("businessHours.settings-meta.xml"))
        | set(root.rglob("businessHours.settings"))
    )
    if not candidates:
        return None
    names: set[str] = set()
    for path in candidates:
        settings_root = _parse(path)
        if settings_root is None:
            continue
        for entry in _children(settings_root, "businessHours"):
            entry_name = _child_text(entry, "name")
            if entry_name:
                names.add(entry_name)
    return names


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def check_milestone_type_file(path: Path) -> list[Finding]:
    """E4: recurrenceType must be one of the three documented values."""
    findings: list[Finding] = []
    root = _parse(path)
    if root is None:
        return [Finding("ERROR", "E0", path.name, "File is not parseable XML.")]

    recurrence = _child(root, "recurrenceType")
    if recurrence is not None:
        value = _text(recurrence)
        if value not in _RECURRENCE_TYPES:
            findings.append(Finding(
                "ERROR", "E4", path.name,
                f"<recurrenceType>{value or '(empty)'}</recurrenceType> is not one of "
                f"{sorted(_RECURRENCE_TYPES)} (api_meta.txt:88337-88345).",
            ))
    return findings


def check_process_file(
    path: Path,
    milestone_types: set[str],
    business_hours: set[str] | None,
) -> tuple[list[Finding], str, bool]:
    """Check one EntitlementProcess file.

    Returns (findings, versionMaster, isVersionDefault) so the caller can run
    the cross-file default-version check.
    """
    findings: list[Finding] = []
    root = _parse(path)
    if root is None:
        return (
            [Finding("ERROR", "E0", path.name, "File is not parseable XML.")],
            "",
            False,
        )

    where = path.name
    process_name = _child_text(root, "name") or path.stem
    is_active = _child_text(root, "active").lower() == "true"
    version_master = _child_text(root, "versionMaster")
    is_default = _child_text(root, "isVersionDefault").lower() == "true"

    sobject_type = _child(root, "SObjectType")
    if sobject_type is not None:
        value = _text(sobject_type)
        if value not in _SOBJECT_TYPES:
            findings.append(Finding(
                "ERROR", "E4", where,
                f"<SObjectType>{value or '(empty)'}</SObjectType> is not one of "
                f"{sorted(_SOBJECT_TYPES)} (object_reference.txt:270729-270737).",
            ))

    process_hours = _child_text(root, "businessHours")
    if process_hours and business_hours is None:
        findings.append(Finding(
            "WARN", "W6", where,
            f"Process '{process_name}' names business hours '{process_hours}', and this tree "
            "holds no BusinessHours settings file, so the name was not resolved against "
            "anything. Either the retrieve/step scope excludes "
            "settings/BusinessHours.settings-meta.xml, or the calendar does not exist. Re-run "
            "over the tree that carries the settings file to make this a real check.",
        ))
    elif process_hours and business_hours is not None and process_hours not in business_hours:
        findings.append(Finding(
            "WARN", "W3", where,
            f"Process '{process_name}' names business hours '{process_hours}', which is not a "
            "<name> in the BusinessHours settings file in this tree. The deploy fails, or the "
            "process silently counts on a calendar you did not review.",
        ))

    milestones = _children(root, "milestones")
    if not milestones:
        if is_active:
            findings.append(Finding(
                "WARN", "W1", where,
                f"Process '{process_name}' is active but declares no <milestones>. Cases enter "
                "it and nothing is tracked.",
            ))
        return findings, version_master, is_default

    for milestone in milestones:
        findings.extend(
            _check_milestone(milestone, where, process_name, milestone_types, business_hours)
        )

    return findings, version_master, is_default


def _check_milestone(
    milestone: ET.Element,
    where: str,
    process_name: str,
    milestone_types: set[str],
    business_hours: set[str] | None,
) -> list[Finding]:
    findings: list[Finding] = []
    name = _child_text(milestone, "milestoneName") or "(unnamed)"
    label = f"{process_name} / {name}"

    # --- E1: minutesToComplete must be a positive int -----------------------
    minutes_element = _child(milestone, "minutesToComplete")
    minutes = _int_or_none(_text(minutes_element)) if minutes_element is not None else None
    if minutes_element is None:
        findings.append(Finding(
            "ERROR", "E1", where,
            f"Milestone '{label}' has no <minutesToComplete>. The guide types it int "
            "(api_meta.txt:59191-59193); without it the milestone has no target.",
        ))
    elif minutes is None:
        findings.append(Finding(
            "ERROR", "E1", where,
            f"Milestone '{label}' has a non-numeric <minutesToComplete>"
            f"='{_text(minutes_element)}'.",
        ))
    elif minutes <= 0:
        findings.append(Finding(
            "ERROR", "E1", where,
            f"Milestone '{label}' has <minutesToComplete>{minutes}</minutesToComplete>. "
            "It must be a positive number of minutes.",
        ))

    # --- W2: the milestone type must exist in the tree ----------------------
    if milestone_types and name != "(unnamed)" and name not in milestone_types:
        findings.append(Finding(
            "WARN", "W2", where,
            f"Milestone '{label}' names a milestone type that has no file under milestoneTypes/. "
            f"Known types in this tree: {sorted(milestone_types) or '(none)'}.",
        ))

    # --- W3: milestone-level calendar override ------------------------------
    override_hours = _child_text(milestone, "businessHours")
    if override_hours and business_hours is None:
        findings.append(Finding(
            "WARN", "W6", where,
            f"Milestone '{label}' overrides business hours with '{override_hours}', and this "
            "tree holds no BusinessHours settings file, so the name was not resolved against "
            "anything. Re-run over the tree that carries "
            "settings/BusinessHours.settings-meta.xml to make this a real check.",
        ))
    elif override_hours and business_hours is not None and override_hours not in business_hours:
        findings.append(Finding(
            "WARN", "W3", where,
            f"Milestone '{label}' overrides business hours with '{override_hours}', which is not "
            "a <name> in the BusinessHours settings file in this tree.",
        ))

    # --- triggers -----------------------------------------------------------
    triggers = _children(milestone, "timeTriggers")
    success_actions = _children(milestone, "successActions")

    if not triggers and not success_actions:
        findings.append(Finding(
            "WARN", "W4", where,
            f"Milestone '{label}' has neither <timeTriggers> nor <successActions>. It counts down "
            "and nothing observable happens at any point.",
        ))

    warning_offsets: list[int] = []
    violation_offsets: list[int] = []
    seen_offsets: dict[int, str] = {}

    for index, trigger in enumerate(triggers, start=1):
        trigger_label = f"{label} trigger {index}"

        unit_element = _child(trigger, "workflowTimeTriggerUnit")
        unit = _text(unit_element) if unit_element is not None else "Minutes"
        if unit_element is not None and unit not in _TIME_UNITS:
            findings.append(Finding(
                "ERROR", "E3", where,
                f"{trigger_label}: <workflowTimeTriggerUnit>{unit or '(empty)'}"
                f"</workflowTimeTriggerUnit> is not one of {sorted(_TIME_UNITS)} "
                "(api_meta.txt:59220-59224).",
            ))
            continue

        length_element = _child(trigger, "timeLength")
        length = _int_or_none(_text(length_element)) if length_element is not None else None
        if length is None:
            findings.append(Finding(
                "ERROR", "E3", where,
                f"{trigger_label}: <timeLength> is missing or non-numeric. It is an int offset "
                "from the milestone target (api_meta.txt:59213-59219).",
            ))
            continue

        offset_minutes = length * _UNIT_MINUTES.get(unit, 1)
        if offset_minutes < 0:
            warning_offsets.append(offset_minutes)
        else:
            violation_offsets.append(offset_minutes)

        if offset_minutes in seen_offsets:
            findings.append(Finding(
                "INFO", "I4", where,
                f"{trigger_label} resolves to the same offset ({offset_minutes:+d} min from "
                f"target) as {seen_offsets[offset_minutes]}. Two triggers fire on the same "
                "minute; check whether a unit was left unchanged in a copy-paste.",
            ))
        else:
            seen_offsets[offset_minutes] = f"trigger {index}"

        if minutes is not None and minutes > 0:
            elapsed = minutes + offset_minutes
            kind = "warning" if offset_minutes < 0 else "violation"
            pct = round(100.0 * elapsed / minutes, 1)
            findings.append(Finding(
                "INFO", "I2", where,
                f"{trigger_label}: {length} {unit} -> {kind} at {elapsed} min elapsed of "
                f"{minutes} ({pct}% of target).",
            ))
            if elapsed < 0:
                findings.append(Finding(
                    "WARN", "W4", where,
                    f"{trigger_label} fires before the milestone starts ({elapsed} min elapsed). "
                    "The offset is larger than the milestone target — a stale timeLength left "
                    "behind when minutesToComplete was shortened.",
                ))

    # --- I1: a breach with no advance notice --------------------------------
    if violation_offsets and not warning_offsets:
        findings.append(Finding(
            "INFO", "I1", where,
            f"Milestone '{label}' has {len(violation_offsets)} violation trigger(s) and no "
            "warning trigger (no negative <timeLength>). The first notice anyone gets is the "
            "breach.",
        ))

    return findings


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def check_entitlements_and_milestones(manifest_dir: Path) -> list[Finding]:
    """Every finding for one metadata tree."""
    if not manifest_dir.exists():
        return [Finding("ERROR", "E0", str(manifest_dir), "Manifest directory not found.")]

    findings: list[Finding] = []

    milestone_type_files = _files(manifest_dir, "milestoneTypes", ".milestoneType")
    for path in milestone_type_files:
        findings.extend(check_milestone_type_file(path))

    milestone_types = _milestone_type_names(manifest_dir)
    business_hours = _business_hours_names(manifest_dir)

    process_files = _files(manifest_dir, "entitlementProcesses", ".entitlementProcess")
    if not process_files:
        findings.append(Finding(
            "INFO", "I3", str(manifest_dir),
            "No *.entitlementProcess-meta.xml files found. If Entitlement Management is in use, "
            "at least one process should be in the package.",
        ))
        return findings

    # versionMaster -> [(file name, isVersionDefault)]
    versions: dict[str, list[tuple[str, bool]]] = {}

    for path in process_files:
        file_findings, version_master, is_default = check_process_file(
            path, milestone_types, business_hours
        )
        findings.extend(file_findings)
        versions.setdefault(version_master, []).append((path.name, is_default))

    for version_master, entries in versions.items():
        if not version_master:
            continue
        defaults = [file_name for file_name, is_default in entries if is_default]
        if len(defaults) > 1:
            findings.append(Finding(
                "ERROR", "E2", ", ".join(sorted(defaults)),
                f"versionMaster '{version_master}' has {len(defaults)} files with "
                "<isVersionDefault>true</isVersionDefault>. Exactly one version of a process is "
                "the default (api_meta.txt:59136-59139).",
            ))
        elif not defaults and len(entries) > 0:
            findings.append(Finding(
                "WARN", "W5", ", ".join(sorted(name for name, _ in entries)),
                f"versionMaster '{version_master}' has no file with "
                "<isVersionDefault>true</isVersionDefault>. New entitlements have no version to "
                "attach to.",
            ))

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Entitlement Management metadata for configuration problems.",
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
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit 1 on WARN findings as well as ERROR — use where the tree is supposed "
            "to be the complete Entitlement Management package."
        ),
    )
    args = parser.parse_args(argv)

    findings = check_entitlements_and_milestones(Path(args.manifest_dir))

    errors = [f for f in findings if f.severity == "ERROR"]
    warnings = [f for f in findings if f.severity == "WARN"]
    infos = [f for f in findings if f.severity == "INFO"]

    shown = errors + warnings + ([] if args.quiet_info else infos)
    for finding in shown:
        print(finding)

    print(
        f"\n{len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info note(s)."
    )

    if errors:
        return 1
    if args.strict and warnings:
        print(f"--strict: failing on {len(warnings)} warning(s).")
        return 1

    print("OK: no ERROR findings.")
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        sys.exit(1)
    sys.exit(0)
