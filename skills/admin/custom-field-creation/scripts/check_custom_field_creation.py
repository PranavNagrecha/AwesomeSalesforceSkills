#!/usr/bin/env python3
"""Checker script for the Custom Field Creation skill.

Scans a Salesforce DX source tree (or retrieved metadata) for `.field-meta.xml`
files and reports field definitions whose XML has taken a platform default that
is almost never the decision the author meant to make.

Checks, with the guide statement each one rests on
(line refs are into the Summer '26 Metadata API Developer Guide text):

  WARN  externalId without unique
        `externalId` and `unique` are independent booleans (api_meta 43402,
        43702). A non-unique external ID is a legal upsert key that fails at
        runtime: "If the external ID is matched multiple times, then a 300
        error is reported, and the record isn't created or updated"
        (REST API Developer Guide).

  WARN  no description and no inlineHelpText on a user-facing field
        `description` is "description of the field" (43360); `inlineHelpText`
        is "the content of field-level help" (43455). Different audiences.

  WARN  Picklist with neither `restricted` true nor a global `valueSetName`
        An unrestricted local picklist lets the API write values outside the
        set (44696-44699).

  INFO  Lookup with no `deleteConstraint`
        The default is not "block": "SetNull - This value is the default. If
        the lookup record is deleted, the lookup field is cleared" (43348).

  ERROR two MasterDetail fields on one object without a valid 0/1
        `relationshipOrder` pair
        "Junction objects must define one parent object as primary (0), the
        other as secondary (1) ... 0 or 1 are the only valid values" (43582).
        Skipped when the object folder holds fewer than two MasterDetail
        fields, since `relationshipOrder` is then always 0.

  INFO  Checkbox with no `defaultValue` (and the `required` + no-default case)
        A Checkbox always has a value, so `defaultValue` is the only thing
        that decides which one (43346).

  ERROR the same fullName declared in more than one file
        A copy-paste that deploys one field and silently drops the other.

Text fields whose API name ends in a categorical suffix (_Status, _Type, ...)
are also flagged, and Long Text Areas left at the 256-character minimum.

Uses stdlib only - no pip dependencies.

Exit code: 0 when clean, 1 when any finding is reported.

Usage:
    python3 check_custom_field_creation.py --manifest-dir force-app/main/default
    python3 check_custom_field_creation.py --manifest-dir . --min-severity WARN
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

# Suffixes that suggest a field holds categorical/enumerated values
# but may have been created as Text instead of Picklist
CATEGORICAL_SUFFIXES = (
    "_type",
    "_status",
    "_category",
    "_segment",
    "_tier",
    "_stage",
    "_region",
    "_reason",
    "_source",
)

# Namespace used in Salesforce field XML files
SF_NS = "http://soap.sforce.com/2006/04/metadata"

# Field types that end users read or type into, so help text earns its keep.
# System-ish types (AutoNumber, Summary, formula-backed) are excluded.
USER_FACING_TYPES = frozenset(
    {
        "Checkbox",
        "Currency",
        "Date",
        "DateTime",
        "Email",
        "Html",
        "Location",
        "LongTextArea",
        "Lookup",
        "MasterDetail",
        "MultiselectPicklist",
        "Number",
        "Percent",
        "Phone",
        "Picklist",
        "Text",
        "TextArea",
        "Time",
        "Url",
    }
)

SEVERITIES = ("INFO", "WARN", "ERROR")


def _tag(name: str) -> str:
    """Return a namespace-qualified XML tag name."""
    return f"{{{SF_NS}}}{name}"


def _text(element: ET.Element | None, name: str) -> str | None:
    """Return the stripped text of a direct child element, or None.

    Written as an explicit `is not None` chain on purpose: a leaf Element is
    falsy in ElementTree, so `root.find(a) or root.find(b)` silently discards
    a real, empty element. Never use `or` to chain finds.
    """
    if element is None:
        return None
    child = element.find(_tag(name))
    if child is None:
        return None
    if child.text is None:
        return ""
    return child.text.strip()


def _has(element: ET.Element | None, name: str) -> bool:
    """True when the element exists at all, regardless of its text."""
    if element is None:
        return False
    return element.find(_tag(name)) is not None


def _is_true(element: ET.Element | None, name: str) -> bool:
    value = _text(element, name)
    return value is not None and value.lower() == "true"


def check_field_file(field_file: Path) -> tuple[list[tuple[str, str]], dict]:
    """Parse one .field-meta.xml file.

    Returns (findings, facts) where findings is a list of (severity, message)
    and facts carries what the object-level checks need.
    """
    findings: list[tuple[str, str]] = []
    facts: dict = {"path": field_file, "full_name": None, "type": None}

    try:
        tree = ET.parse(field_file)
    except ET.ParseError as exc:
        findings.append(("ERROR", f"{field_file}: XML parse error - {exc}"))
        return findings, facts

    root = tree.getroot()

    field_api_name = field_file.name.replace(".field-meta.xml", "")
    # Typical path: .../objects/Account/fields/My_Field__c.field-meta.xml
    object_name = field_file.parents[1].name if len(field_file.parents) > 1 else "?"
    label = f"{object_name}.{field_api_name}"

    field_type = _text(root, "type") or ""
    declared_full_name = _text(root, "fullName")

    facts["full_name"] = declared_full_name or field_api_name
    facts["type"] = field_type
    facts["object"] = object_name
    facts["label"] = label
    facts["relationship_order"] = _text(root, "relationshipOrder")

    # --- Check 1: Text fields whose name reads like an enumerated category ---
    if field_type == "Text":
        lower_name = field_api_name.lower().replace("__c", "")
        for suffix in CATEGORICAL_SUFFIXES:
            bare = suffix.lstrip("_")
            if lower_name.endswith(suffix) or lower_name == bare:
                findings.append(
                    (
                        "INFO",
                        f"{label}: type is Text but the API name ends in "
                        f"'{suffix.lstrip('_')}' - consider a Picklist so the "
                        f"vocabulary is enforced rather than trained.",
                    )
                )
                break

    # --- Check 2: description / inlineHelpText on a user-facing field ---
    if field_type in USER_FACING_TYPES:
        missing = []
        if not (_text(root, "description") or ""):
            missing.append("description")
        if not (_text(root, "inlineHelpText") or ""):
            missing.append("inlineHelpText")
        if len(missing) == 2:
            findings.append(
                (
                    "WARN",
                    f"{label}: no description and no inlineHelpText. "
                    f"description is for the next admin, inlineHelpText is the "
                    f"field-level help the end user sees; neither is optional on "
                    f"a field people type into.",
                )
            )
        elif missing:
            findings.append(
                (
                    "INFO",
                    f"{label}: no {missing[0]}. "
                    f"description documents the field for admins; "
                    f"inlineHelpText documents it for users.",
                )
            )

    # --- Check 3: externalId without unique ---
    if _is_true(root, "externalId") and not _is_true(root, "unique"):
        findings.append(
            (
                "WARN",
                f"{label}: externalId is true but unique is not. "
                f"A duplicate value makes every upsert on this key return "
                f"HTTP 300 and the record is neither created nor updated. "
                f"Set unique=true, and decide caseSensitive in the same change.",
            )
        )

    # --- Check 4: Lookup with no deleteConstraint ---
    if field_type == "Lookup" and not _has(root, "deleteConstraint"):
        findings.append(
            (
                "INFO",
                f"{label}: Lookup with no deleteConstraint. "
                f"The platform default is SetNull, which blanks this field when "
                f"the parent is deleted. Write Cascade, Restrict, or SetNull "
                f"explicitly so the behaviour is a decision on the record.",
            )
        )

    # --- Check 5: unrestricted local picklist ---
    if field_type in ("Picklist", "MultiselectPicklist"):
        value_set = root.find(_tag("valueSet"))
        if value_set is None:
            findings.append(
                (
                    "WARN",
                    f"{label}: {field_type} with no valueSet element. "
                    f"Add a valueSetDefinition, or a valueSetName pointing at a "
                    f"global value set.",
                )
            )
        else:
            uses_global = bool(_text(value_set, "valueSetName"))
            if not uses_global and not _is_true(value_set, "restricted"):
                findings.append(
                    (
                        "WARN",
                        f"{label}: local {field_type} value set is not restricted. "
                        f"The API and data loads can write values outside the set, "
                        f"which is how a report grouping quietly grows a sixth row.",
                    )
                )

    # --- Check 6: Checkbox defaults ---
    if field_type == "Checkbox":
        if not _has(root, "defaultValue"):
            subject = (
                "required Checkbox with no defaultValue"
                if _is_true(root, "required")
                else "Checkbox with no defaultValue"
            )
            findings.append(
                (
                    "INFO",
                    f"{label}: {subject}. A checkbox always has a value, so "
                    f"omitting this deploys the platform's default rather than "
                    f"yours - write <defaultValue>false</defaultValue> when "
                    f"unchecked is the intent.",
                )
            )

    # --- Check 7 (retained): Long Text Area left at the minimum size ---
    if field_type == "LongTextArea":
        length_value = _text(root, "length")
        if length_value:
            try:
                if int(length_value) <= 256:
                    findings.append(
                        (
                            "INFO",
                            f"{label}: LongTextArea length is {length_value}, the "
                            f"minimum. Confirm that is the intent rather than a "
                            f"leftover default.",
                        )
                    )
            except ValueError:
                findings.append(
                    ("WARN", f"{label}: length '{length_value}' is not an integer.")
                )

    return findings, facts


def check_object_level(facts_by_object: dict) -> list[tuple[str, str]]:
    """Junction relationshipOrder check, run once per object folder."""
    findings: list[tuple[str, str]] = []

    for object_name, field_facts in sorted(facts_by_object.items()):
        masters = [f for f in field_facts if f.get("type") == "MasterDetail"]
        if len(masters) < 2:
            # relationshipOrder is always 0 outside a junction - nothing to check.
            continue
        if len(masters) > 2:
            findings.append(
                (
                    "ERROR",
                    f"{object_name}: {len(masters)} MasterDetail fields found. "
                    f"An object supports at most two; review "
                    f"{', '.join(sorted(f['label'] for f in masters))}.",
                )
            )
            continue

        orders = [f.get("relationship_order") for f in masters]
        names = ", ".join(sorted(f["label"] for f in masters))
        if any(o is None for o in orders):
            findings.append(
                (
                    "ERROR",
                    f"{object_name}: junction object with two MasterDetail fields "
                    f"but relationshipOrder is missing on at least one ({names}). "
                    f"One parent must be primary (0), the other secondary (1); "
                    f"the choice decides ownership, sharing, and delete behaviour.",
                )
            )
        elif sorted(orders) != ["0", "1"]:
            findings.append(
                (
                    "ERROR",
                    f"{object_name}: junction relationshipOrder pair is "
                    f"{sorted(orders)}, not ['0', '1'] ({names}). "
                    f"0 and 1 are the only valid values and each must be used once.",
                )
            )

    return findings


def check_duplicate_full_names(all_facts: list[dict]) -> list[tuple[str, str]]:
    """The same fullName declared in more than one file."""
    findings: list[tuple[str, str]] = []
    seen: dict[tuple[str, str], list[Path]] = defaultdict(list)

    for facts in all_facts:
        full_name = facts.get("full_name")
        if not full_name:
            continue
        seen[(facts.get("object", "?"), full_name)].append(facts["path"])

    for (object_name, full_name), paths in sorted(seen.items()):
        if len(paths) > 1:
            listed = ", ".join(str(p) for p in sorted(paths))
            findings.append(
                (
                    "ERROR",
                    f"{object_name}.{full_name}: fullName declared in "
                    f"{len(paths)} files ({listed}). "
                    f"Only one survives the deploy and which one is not defined.",
                )
            )

    return findings


def check_custom_field_creation(manifest_dir: Path) -> list[tuple[str, str]]:
    """Scan manifest_dir for .field-meta.xml files and return all findings."""
    findings: list[tuple[str, str]] = []

    if not manifest_dir.exists():
        return [("ERROR", f"Manifest directory not found: {manifest_dir}")]

    field_files = sorted(manifest_dir.rglob("*.field-meta.xml"))
    if not field_files:
        # Not a finding - the directory may be a non-DX layout.
        return findings

    all_facts: list[dict] = []
    facts_by_object: dict[str, list[dict]] = defaultdict(list)

    for field_file in field_files:
        file_findings, facts = check_field_file(field_file)
        findings.extend(file_findings)
        all_facts.append(facts)
        facts_by_object[facts.get("object", "?")].append(facts)

    findings.extend(check_object_level(facts_by_object))
    findings.extend(check_duplicate_full_names(all_facts))

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce field metadata for defaults that are almost never "
            "the intended decision. Point --manifest-dir at the root of your DX "
            "source tree or retrieved metadata directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--min-severity",
        choices=SEVERITIES,
        default="INFO",
        help="Only report findings at or above this severity (default: INFO).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = check_custom_field_creation(Path(args.manifest_dir))

    floor = SEVERITIES.index(args.min_severity)
    findings = [f for f in findings if SEVERITIES.index(f[0]) >= floor]

    if not findings:
        print("No findings.")
        return 0

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for severity, message in sorted(findings, key=lambda f: (order[f[0]], f[1])):
        print(f"{severity}: {message}")

    counts = {s: sum(1 for f in findings if f[0] == s) for s in SEVERITIES}
    print(
        f"\n{len(findings)} finding(s): "
        f"{counts['ERROR']} ERROR, {counts['WARN']} WARN, {counts['INFO']} INFO"
    )
    return 1


if __name__ == "__main__":
    if main() != 0:
        sys.exit(1)
    sys.exit(0)
