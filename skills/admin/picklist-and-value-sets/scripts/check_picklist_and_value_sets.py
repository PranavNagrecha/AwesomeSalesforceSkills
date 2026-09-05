#!/usr/bin/env python3
"""Checker for the Picklist and Value Sets skill.

Scans a Salesforce DX source tree for picklist metadata and reports findings at
three severities. Every check cites the statement in the Metadata API Developer
Guide (Summer '26 / v62) that makes it a defect rather than a style preference;
the line numbers are into the extracted text used by
``references/metadata-examples.md``.

Files scanned
    globalValueSets/*.globalValueSet-meta.xml       -> <GlobalValueSet>
    standardValueSets/*.standardValueSet-meta.xml   -> <StandardValueSet>
    objects/<Obj>/fields/<F>.field-meta.xml         -> <CustomField>
    objects/<Obj>/<Obj>.object-meta.xml             -> <CustomObject> (embedded <fields>)

ERROR
    Duplicate ``fullName`` inside one value set.
        Values are keyed by fullName; a duplicate makes the deploy ambiguous.
    More than one value flagged ``default``.
        "Only one item in a picklist can be designated as the default"
        (apexrefguide.txt:193684-193686).
    A ``valueSet`` carrying both ``valueSetName`` and ``valueSetDefinition``.
        "A ValueSet component has either a valueSetDefinition or a valueName
        specified, but never both" (api_meta.txt:43710-43713).
    An ``OpportunityStage`` value with no ``probability`` or no
    ``forecastCategory``; or a ``forecastCategory`` outside the documented enum
    Omitted / Pipeline / BestCase / Forecast / Closed (api_meta.txt:47578-47586,
    47593-47596).
    A picklist field with neither values nor a global value set.
    A ``description`` over 255 characters (api_meta.txt:47517-47520,
    79368-79370).
    More than 1,000 values in one set: "A global value set can have up to 1,000
    total values, including inactive values" (api_meta.txt:79363-79367).

WARN
    ``restricted`` false or absent on a field that names a global value set.
        "A custom picklist that uses a global value set is restricted"
        (api_meta.txt:43704-43711) - say so in the file so the diff shows it.
    A ``GlobalValueSet`` with no ``masterLabel`` ("Required", api_meta.txt:79371)
    or no ``customValue`` ("Requires at least one value", api_meta.txt:79363).
    A ``StandardValueSet`` with no ``standardValue``: "this array must contain at
    least one picklist value. Otherwise, you receive an error"
    (api_meta.txt:130771-130772).
    A ``valueSettings`` entry whose ``valueName`` is not a value of the field.
    A multi-select picklist over 500 values.

INFO
    Two or more picklist fields on one object with identical local value lists
    (a global value set candidate).
    A field naming a global value set that is not present in the scanned tree.

Usage
    python3 check_picklist_and_value_sets.py --manifest-dir force-app/main/default
    python3 check_picklist_and_value_sets.py --manifest-dir . --min-severity WARN

Exit code is 1 when any finding at or above ``--min-severity`` is reported.
Stdlib only.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SEVERITIES = ("INFO", "WARN", "ERROR")

# Documented limits, each with the guide statement behind it.
MAX_VALUES_PER_SET = 1000        # api_meta.txt:79363-79367
MAX_MULTISELECT_VALUES = 500     # Salesforce Help KB 000386685 (see well-architected.md)
MAX_DESCRIPTION_CHARS = 255      # api_meta.txt:47517-47520, 79368-79370

# api_meta.txt:47578-47586 - the enum is closed.
FORECAST_CATEGORIES = {"Omitted", "Pipeline", "BestCase", "Forecast", "Closed"}

# api_meta.txt:142674 - Opportunity.StageName is the OpportunityStage value set.
STAGE_VALUE_SET = "OpportunityStage"

PICKLIST_TYPES = {"Picklist", "MultiselectPicklist"}

Finding = tuple[str, str]


# --------------------------------------------------------------------------
# ElementTree helpers
#
# A leaf Element is falsy, so `el.find(a) or el.find(b)` silently discards a
# real match. Every lookup below tests `is not None`.
# --------------------------------------------------------------------------

def _local(tag: str) -> str:
    """Strip any XML namespace from a tag name."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child(parent: ET.Element | None, name: str) -> ET.Element | None:
    """First direct child named `name`, namespace-insensitive, or None."""
    if parent is None:
        return None
    for element in parent:
        if _local(element.tag) == name:
            return element
    return None


def children(parent: ET.Element | None, name: str) -> list[ET.Element]:
    """All direct children named `name`, namespace-insensitive."""
    if parent is None:
        return []
    return [element for element in parent if _local(element.tag) == name]


def text_of(parent: ET.Element | None, name: str) -> str | None:
    """Stripped text of the first direct child named `name`, or None."""
    element = child(parent, name)
    if element is None or element.text is None:
        return None
    return element.text.strip()


def is_true(parent: ET.Element | None, name: str) -> bool:
    value = text_of(parent, name)
    return value is not None and value.lower() == "true"


# --------------------------------------------------------------------------
# Shared value-list checks
# --------------------------------------------------------------------------

def check_value_list(
    label: str,
    value_elements: list[ET.Element],
    findings: list[Finding],
) -> list[str]:
    """Run the checks common to every kind of value set.

    Returns the list of `fullName` strings found, for callers that need it.
    """
    names: list[str] = []
    seen: set[str] = set()
    defaults: list[str] = []

    for value in value_elements:
        full_name = text_of(value, "fullName")
        if full_name is None:
            findings.append(("ERROR", f"{label}: a value has no <fullName>."))
            continue

        names.append(full_name)
        if full_name in seen:
            findings.append(
                (
                    "ERROR",
                    f"{label}: duplicate value fullName '{full_name}'. "
                    "Values are keyed by fullName; a duplicate makes the deploy ambiguous.",
                )
            )
        seen.add(full_name)

        if is_true(value, "default"):
            defaults.append(full_name)

        description = text_of(value, "description")
        if description is not None and len(description) > MAX_DESCRIPTION_CHARS:
            findings.append(
                (
                    "ERROR",
                    f"{label}: description on value '{full_name}' is {len(description)} "
                    f"characters; the documented limit is {MAX_DESCRIPTION_CHARS} "
                    "(api_meta.txt:47517-47520).",
                )
            )

    if len(defaults) > 1:
        findings.append(
            (
                "ERROR",
                f"{label}: {len(defaults)} values are marked default ({', '.join(sorted(defaults))}). "
                "Only one item in a picklist can be the default "
                "(apexrefguide.txt:193684-193686).",
            )
        )

    if len(names) > MAX_VALUES_PER_SET:
        findings.append(
            (
                "ERROR",
                f"{label}: {len(names)} values, over the documented ceiling of "
                f"{MAX_VALUES_PER_SET} including inactive values (api_meta.txt:79363-79367).",
            )
        )

    return names


# --------------------------------------------------------------------------
# GlobalValueSet
# --------------------------------------------------------------------------

def check_global_value_set(path: Path, root: ET.Element, findings: list[Finding]) -> str:
    """Check one .globalValueSet-meta.xml. Returns its developer name."""
    developer_name = path.name.split(".")[0]
    label = f"GlobalValueSet {developer_name}"

    if text_of(root, "masterLabel") is None:
        findings.append(
            ("WARN", f"{label}: no <masterLabel>. The guide marks it Required (api_meta.txt:79371).")
        )

    values = children(root, "customValue")
    if not values:
        findings.append(
            (
                "WARN",
                f"{label}: no <customValue> elements. A global value set "
                "'requires at least one value' (api_meta.txt:79363). Deploying this file "
                "deactivates every value the org currently has (api_meta.txt:47482-47483).",
            )
        )

    check_value_list(label, values, findings)

    description = text_of(root, "description")
    if description is not None and len(description) > MAX_DESCRIPTION_CHARS:
        findings.append(
            (
                "ERROR",
                f"{label}: description is {len(description)} characters; the documented "
                f"limit is {MAX_DESCRIPTION_CHARS} (api_meta.txt:79368-79370).",
            )
        )

    return developer_name


# --------------------------------------------------------------------------
# StandardValueSet
# --------------------------------------------------------------------------

def check_standard_value_set(path: Path, root: ET.Element, findings: list[Finding]) -> None:
    """Check one .standardValueSet-meta.xml."""
    set_name = text_of(root, "fullName") or path.name.split(".")[0]
    label = f"StandardValueSet {set_name}"

    values = children(root, "standardValue")
    if not values:
        findings.append(
            (
                "WARN",
                f"{label}: no <standardValue> elements. 'When you deploy a StandardValueSet, "
                "this array must contain at least one picklist value. Otherwise, you receive "
                "an error' (api_meta.txt:130771-130772).",
            )
        )

    check_value_list(label, values, findings)

    for value in values:
        full_name = text_of(value, "fullName")
        if full_name is None:
            continue

        forecast = text_of(value, "forecastCategory")
        if forecast is not None and forecast not in FORECAST_CATEGORIES:
            findings.append(
                (
                    "ERROR",
                    f"{label}: value '{full_name}' has forecastCategory '{forecast}', which is "
                    "outside the documented enum "
                    f"({', '.join(sorted(FORECAST_CATEGORIES))}) (api_meta.txt:47578-47586).",
                )
            )

        if set_name != STAGE_VALUE_SET:
            continue

        # api_meta.txt:47578-47586, 47593-47596 - both are stage-specific and both
        # are optional in the schema, so the deploy will not catch a missing one.
        missing = []
        if forecast is None:
            missing.append("forecastCategory")
        if text_of(value, "probability") is None:
            missing.append("probability")
        if missing:
            findings.append(
                (
                    "ERROR",
                    f"{label}: stage '{full_name}' is missing {' and '.join(missing)}. "
                    "The deploy succeeds and the stage is then uncategorised in the forecast "
                    "(api_meta.txt:47578-47586, 47593-47596).",
                )
            )


# --------------------------------------------------------------------------
# CustomField picklists
# --------------------------------------------------------------------------

def check_picklist_field(
    label: str,
    field: ET.Element,
    findings: list[Finding],
) -> tuple[str | None, tuple[str, ...] | None]:
    """Check one <CustomField> or embedded <fields> element.

    Returns (referenced global value set name, sorted local value tuple).
    """
    field_type = text_of(field, "type")
    if field_type not in PICKLIST_TYPES:
        return None, None

    value_set = child(field, "valueSet")
    if value_set is None:
        # API 37.0 and earlier used <picklist>; nothing here applies to it.
        if child(field, "picklist") is None:
            findings.append(
                (
                    "ERROR",
                    f"{label}: type is {field_type} but the field has no <valueSet>. "
                    "Add a <valueSetDefinition> or a <valueSetName>.",
                )
            )
        return None, None

    gvs_name = text_of(value_set, "valueSetName")
    definition = child(value_set, "valueSetDefinition")

    if gvs_name is not None and definition is not None:
        findings.append(
            (
                "ERROR",
                f"{label}: <valueSet> carries both <valueSetName> and <valueSetDefinition>. "
                "'A ValueSet component has either a valueSetDefinition or a valueName "
                "specified, but never both' (api_meta.txt:43710-43713).",
            )
        )

    if gvs_name is None and definition is None:
        findings.append(
            (
                "ERROR",
                f"{label}: <valueSet> has neither <valueSetName> nor <valueSetDefinition>, "
                "so the field has no values.",
            )
        )

    if gvs_name is not None and not is_true(value_set, "restricted"):
        findings.append(
            (
                "WARN",
                f"{label}: references global value set '{gvs_name}' but <restricted> is not "
                "true. 'A custom picklist that uses a global value set is restricted' "
                "(api_meta.txt:43704-43711) - state it explicitly so the intent survives a diff.",
            )
        )

    local_values = children(definition, "value") if definition is not None else []
    names = check_value_list(label, local_values, findings)

    if (
        field_type == "MultiselectPicklist"
        and len(names) > MAX_MULTISELECT_VALUES
    ):
        findings.append(
            (
                "WARN",
                f"{label}: multi-select picklist has {len(names)} values, over the "
                f"{MAX_MULTISELECT_VALUES} maximum (Salesforce Help KB 000386685; see "
                "references/well-architected.md).",
            )
        )

    # valueSettings must reference values this field actually has.
    if names:
        known = set(names)
        for setting in children(value_set, "valueSettings"):
            value_name = text_of(setting, "valueName")
            if value_name is not None and value_name not in known:
                findings.append(
                    (
                        "WARN",
                        f"{label}: <valueSettings> maps '{value_name}', which is not a value "
                        "of this field. Dependency mappings added over the Metadata API "
                        "cannot be removed over it (api_meta.txt:45873-45875).",
                    )
                )

    local_key = tuple(sorted(names)) if names and gvs_name is None else None
    return gvs_name, local_key


# --------------------------------------------------------------------------
# Traversal
# --------------------------------------------------------------------------

def object_name_from_path(path: Path) -> str:
    parts = path.parts
    if "objects" in parts:
        index = parts.index("objects")
        if index + 1 < len(parts):
            return parts[index + 1]
    return "Unknown"


def check_picklist_and_value_sets(manifest_dir: Path) -> list[Finding]:
    findings: list[Finding] = []

    if not manifest_dir.exists():
        return [("ERROR", f"Manifest directory not found: {manifest_dir}")]

    global_sets: set[str] = set()
    referenced_sets: dict[str, list[str]] = {}
    local_value_lists: dict[str, dict[tuple[str, ...], list[str]]] = {}

    paths = sorted(
        set(manifest_dir.rglob("*.globalValueSet-meta.xml"))
        | set(manifest_dir.rglob("*.standardValueSet-meta.xml"))
        | set(manifest_dir.rglob("*.field-meta.xml"))
        | set(manifest_dir.rglob("*.object-meta.xml"))
    )

    scanned = 0
    for path in paths:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            findings.append(("ERROR", f"{path}: XML parse error: {exc}"))
            continue

        scanned += 1
        root_tag = _local(root.tag)

        if root_tag == "GlobalValueSet":
            global_sets.add(check_global_value_set(path, root, findings))

        elif root_tag == "StandardValueSet":
            check_standard_value_set(path, root, findings)

        elif root_tag == "CustomField":
            object_name = object_name_from_path(path)
            field_name = path.name.split(".")[0]
            label = f"{object_name}.{field_name}"
            gvs_name, local_key = check_picklist_field(label, root, findings)
            if gvs_name is not None:
                referenced_sets.setdefault(gvs_name, []).append(label)
            if local_key is not None and len(local_key) >= 2:
                local_value_lists.setdefault(object_name, {}).setdefault(
                    local_key, []
                ).append(field_name)

        elif root_tag == "CustomObject":
            object_name = path.name.split(".")[0]
            for field in children(root, "fields"):
                field_name = text_of(field, "fullName") or "<unnamed>"
                label = f"{object_name}.{field_name}"
                gvs_name, local_key = check_picklist_field(label, field, findings)
                if gvs_name is not None:
                    referenced_sets.setdefault(gvs_name, []).append(label)
                if local_key is not None and len(local_key) >= 2:
                    local_value_lists.setdefault(object_name, {}).setdefault(
                        local_key, []
                    ).append(field_name)

    # Cross-file: a field points at a global set the tree does not contain.
    if global_sets:
        for gvs_name, fields in sorted(referenced_sets.items()):
            if gvs_name in global_sets:
                continue
            findings.append(
                (
                    "INFO",
                    f"Global value set '{gvs_name}' is referenced by {', '.join(sorted(fields))} "
                    "but is not in this tree. Retrieve it before deploying, and check the "
                    "'__gvs' suffix on sets created in API 57.0 or later "
                    "(api_meta.txt:79419-79421).",
                )
            )

    # Cross-file: identical local value lists on one object.
    for object_name, buckets in sorted(local_value_lists.items()):
        for value_key, field_names in sorted(buckets.items()):
            if len(field_names) >= 2:
                findings.append(
                    (
                        "INFO",
                        f"{object_name}: fields {', '.join(sorted(field_names))} define identical "
                        f"local value lists ({len(value_key)} values). A GlobalValueSet keeps them "
                        "from drifting (api_meta.txt:79344-79346).",
                    )
                )

    if scanned == 0:
        findings.append(
            (
                "INFO",
                f"No picklist metadata found under {manifest_dir}. Expected "
                "globalValueSets/, standardValueSets/, or objects/*/fields/.",
            )
        )

    return findings


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce picklist metadata: global value sets, standard value sets, "
            "and picklist custom fields in DX source format."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the DX source tree to scan (default: current directory).",
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
    findings = check_picklist_and_value_sets(Path(args.manifest_dir))

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
