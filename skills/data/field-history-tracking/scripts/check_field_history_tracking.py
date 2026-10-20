#!/usr/bin/env python3
"""Checker script for Field History Tracking skill.

Analyzes a Salesforce metadata directory for field history tracking
configuration issues: ineligible field types marked trackHistory, tracked
field counts above the per-object ceiling, and objects with history enabled
but no tracked fields.

Rules and their sources (Security Implementation Guide, Summer '26, "secguide 262"):
- You can't track formula, roll-up summary or auto-number fields (secguide 262 L4797-4799).
- Without Field Audit Trail: up to 20 fields per object (secguide 262 L4795-4796, L4838);
  events and tasks: six (secguide 262 L4700). Field Audit Trail raises the ceiling:
  200 per object per secguide 262 L4836 (product guide); 60 total per sfdx_dev 264
  L4606-4607 (the scratch-org FieldAuditTrail feature). The default Field Audit Trail
  policy is not returned by Metadata API retrieve (secguide 262 L4882-4883), so a missing
  historyRetentionPolicy does not prove Field Audit Trail is off. Hence: more than 200
  tracked fields (or more than 6 on Event/Task) is an ERROR; 21-200 is a WARN that is
  valid only with Field Audit Trail (and above 60 the two sources disagree).

Exit codes: ERROR findings (unparseable XML, ineligible tracked type, tracked-field
count above the ceiling, missing --manifest-dir) exit 1 always. WARN and INFO
findings exit 0 unless --strict is given. A directory with no objects prints one
WARN and exits 0.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_field_history_tracking.py [--help]
    python3 check_field_history_tracking.py --manifest-dir path/to/force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Standard Field History Tracking limit per object (secguide 262 L4795-4796, L4838)
FHT_FIELD_LIMIT = 20
# Events and tasks (secguide 262 L4700)
ACTIVITY_FIELD_LIMIT = 6
ACTIVITY_OBJECTS = {"Event", "Task"}
# Field Audit Trail ceilings: 200 per object (secguide 262 L4836); 60 total in the
# scratch-org feature description (sfdx_dev 264 L4606-4607)
FAT_FIELD_LIMIT = 200
FAT_SCRATCH_LIMIT = 60

# Types the guide says you can't track (secguide 262 L4797-4799). Roll-up and
# auto-number are FieldType values (api_meta 264 L48107, L48129); a formula field has no
# "Formula" type, it carries a <formula> element over its return type (api_meta 264
# L45666), so formula fields are detected by that element.
HARD_INELIGIBLE_TYPES = {"Summary", "AutoNumber"}

SF_NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


def _ns(tag: str) -> str:
    return f"{{{SF_NAMESPACE}}}{tag}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Field History Tracking configuration issues. "
            "Looks for objects with history enabled, counts tracked fields per object, "
            "and flags ineligible field types marked for tracking."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce metadata source tree (default: current directory). "
             "Expects an 'objects/' subdirectory in SFDX source format.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN and INFO findings to exit 1 (ERROR always exits 1).",
    )
    return parser.parse_args()


def get_text(element: ET.Element, tag: str) -> str | None:
    child = element.find(_ns(tag))
    if child is not None and child.text:
        return child.text.strip()
    return None


def read_root(path: Path, findings: list[str]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(f"ERROR: cannot parse {path.name}: {exc}")
        return None


def check_field_history_tracking(manifest_dir: Path) -> list[str]:
    """Return a list of findings, each prefixed ERROR:, WARN: or INFO:."""
    findings: list[str] = []

    if not manifest_dir.exists():
        findings.append(f"ERROR: Manifest directory not found: {manifest_dir}")
        return findings

    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        alt = manifest_dir.parent / "objects"
        if alt.exists():
            objects_dir = alt
        else:
            findings.append(
                f"WARN: no 'objects/' directory under {manifest_dir}; nothing to check. "
                "Run from the Salesforce source root (e.g., force-app/main/default)."
            )
            return findings

    history_enabled: set[str] = set()
    fat_objects: set[str] = set()
    for obj_file in objects_dir.glob("**/*.object-meta.xml"):
        root = read_root(obj_file, findings)
        if root is None:
            continue
        obj_name = obj_file.parent.name
        enable = get_text(root, "enableHistory")
        if enable is not None and enable.lower() == "true":
            history_enabled.add(obj_name)
        if root.find(_ns("historyRetentionPolicy")) is not None:
            fat_objects.add(obj_name)

    tracked: dict[str, list[str]] = {}
    for field_file in objects_dir.glob("**/fields/*.field-meta.xml"):
        root = read_root(field_file, findings)
        if root is None:
            continue
        track = get_text(root, "trackHistory")
        if track is None or track.lower() != "true":
            continue
        field_type = get_text(root, "type")
        if root.find(_ns("formula")) is not None:
            field_type = f"formula ({field_type})"
        parts = field_file.parts
        try:
            obj_name = parts[parts.index("objects") + 1]
        except (ValueError, IndexError):
            obj_name = "unknown"
        field_name = field_file.stem.replace(".field-meta", "")
        tracked.setdefault(obj_name, []).append(field_name)
        if field_type in HARD_INELIGIBLE_TYPES or (field_type or "").startswith("formula"):
            findings.append(
                f"ERROR: [{obj_name}] Field '{field_name}' has trackHistory=true but type "
                f"'{field_type}' can't be tracked (secguide 262 L4797-4799). "
                "Remove trackHistory or change the field type."
            )

    for obj_name, fields in tracked.items():
        count = len(fields)
        if obj_name in ACTIVITY_OBJECTS:
            limit, why = ACTIVITY_FIELD_LIMIT, "events and tasks allow six (secguide 262 L4700)"
        else:
            limit, why = FAT_FIELD_LIMIT, "Field Audit Trail allows up to 200 per object (secguide 262 L4836)"
            if count > FHT_FIELD_LIMIT and count <= FAT_FIELD_LIMIT:
                policy = "has" if obj_name in fat_objects else "has no"
                findings.append(
                    f"WARN: [{obj_name}] {count} fields have trackHistory=true, above the "
                    "20-field limit without Field Audit Trail (secguide 262 L4795-4796, L4838). "
                    "Valid only if Field Audit Trail is on (200 per object, secguide 262 L4836; "
                    f"the scratch-org feature says {FAT_SCRATCH_LIMIT} total, sfdx_dev 264 "
                    f"L4606-4607). The object XML {policy} historyRetentionPolicy; the default "
                    "policy is not retrieved (secguide 262 L4882-4883), so confirm in the org."
                )
                continue
        if count > limit:
            findings.append(
                f"ERROR: [{obj_name}] {count} fields have trackHistory=true, above the "
                f"limit of {limit}: {why}. Tracked fields: {', '.join(fields)}. "
                "Reduce the list, or enable Field Audit Trail and add a historyRetentionPolicy."
            )
        elif count == limit:
            findings.append(
                f"INFO: [{obj_name}] exactly {limit} fields tracked, at the limit; "
                "no further field can be added without removing one."
            )

    for obj_name in sorted(history_enabled):
        if obj_name not in tracked:
            findings.append(
                f"WARN: [{obj_name}] enableHistory=true but no field has trackHistory=true. "
                "Track at least one field, or disable object-level history."
            )

    if not (history_enabled or tracked or fat_objects):
        findings.append(
            f"WARN: no history-enabled objects or tracked fields found under {objects_dir}; "
            "nothing to check."
        )

    return findings


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    findings = check_field_history_tracking(manifest_dir)

    if not findings:
        print("No field history tracking issues found.")
        return 0

    for finding in findings:
        print(finding)

    if any(f.startswith("ERROR:") for f in findings):
        sys.exit(1)
    if args.strict:
        sys.exit(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
