#!/usr/bin/env python3
"""Static checker for Salesforce Path (``PathAssistant``) configuration.

Cross-checks every ``.pathAssistant-meta.xml`` in a retrieved metadata tree against
the record types, business processes, value sets, fields and org settings that sit
in the same tree. It answers the questions a deploy will not: does every step name
a picklist value this record type can actually show, and does every key field exist?

Checks
------
1. ``picklistValueName`` resolves to a value the record type exposes for
   ``fieldName`` (record type picklistValues -> business process values ->
   StandardValueSet / custom field valueSet, in that order).
2. Custom ``fieldNames`` (``*__c``) exist as fields on ``entityName`` in the tree.
3. ``recordTypeName`` resolves to a record type of ``entityName`` (``Master`` /
   ``__Master__`` exempt).
4. ``active`` path with zero ``pathAssistantSteps``, or a step that carries neither
   key fields nor guidance.
5. More than one path for the same ``entityName`` + ``recordTypeName`` -- the guide
   allows exactly one (Metadata API Developer Guide, PathAssistant, api_meta.txt
   L94496).
6. Guidance-text and key-field-count sanity, plus the ``PathAssistantSettings``
   preference that decides whether any of it renders.

Grounding
---------
Metadata API Developer Guide (Summer '26 / v66):
  PathAssistant fields          api_meta.txt L94510-94529, L94545-94549
  One path per record type      api_meta.txt L94496
  Missing step != absent step   api_meta.txt L94525-94526
  Preference need not be on     api_meta.txt L94498
  pathAssistantEnabled default  api_meta.txt L124222-124224
  auto-collapse default false   api_meta.txt L124216-124221
  StandardValueSet names        api_meta.txt L142674, L142581, L141982, L142923
  FlexiPage component name      api_meta.txt L67774
PDF: https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

Stdlib only -- no pip dependencies.

Usage
-----
    python3 check_path_and_guidance.py --manifest-dir force-app/main/default
    python3 check_path_and_guidance.py --manifest-dir . --strict

Exit code 1 if any ISSUE is reported, 0 otherwise. NOTE lines are advisory and do
not affect the exit code unless ``--strict`` is passed.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://soap.sforce.com/2006/04/metadata"

# Standard value set name -> "<Object>.<Field>" (api_meta.txt Appendix C).
STANDARD_VALUE_SETS = {
    "OpportunityStage": ("Opportunity", "StageName"),
    "LeadStatus": ("Lead", "Status"),
    "CaseStatus": ("Case", "Status"),
    "QuoteStatus": ("Quote", "Status"),
}
FIELD_TO_VALUE_SET = {v: k for k, v in STANDARD_VALUE_SETS.items()}

MASTER_RECORD_TYPE_NAMES = {"master", "__master__"}

# UNVERIFIED (2026-09-05): the "5 key fields per step" cap is repeated widely in
# practitioner material but appears in neither the Metadata API guide's fieldNames
# description nor the Developer Limits and Allocations Quick Reference (which has
# no Path entry at all). Reported as a NOTE, never as an ISSUE.
SOFT_MAX_KEY_FIELDS = 5

# UNVERIFIED (2026-09-05): no documented character limit for PathAssistantStep.info
# exists in the extracted guides; SfSkills content has carried both ~1,000 and
# ~5,000. This threshold is a readability heuristic, not a platform limit.
SOFT_MAX_INFO_CHARS = 5000
MIN_USEFUL_INFO_CHARS = 20

PATH_COMPONENT_NAME = "runtime_sales_pathassistant:pathAssistant"


# ---------------------------------------------------------------------------
# XML helpers -- a leaf Element is falsy, so every lookup tests `is not None`.
# ---------------------------------------------------------------------------


def _child(parent: ET.Element | None, tag: str) -> ET.Element | None:
    """First direct child named `tag`, namespaced or not. Never uses `or`."""
    if parent is None:
        return None
    found = parent.find(f"{{{NS}}}{tag}")
    if found is not None:
        return found
    found = parent.find(tag)
    if found is not None:
        return found
    return None


def _children(parent: ET.Element | None, tag: str) -> list[ET.Element]:
    """All direct children named `tag`, namespaced or not."""
    if parent is None:
        return []
    found = parent.findall(f"{{{NS}}}{tag}")
    if found:
        return found
    return parent.findall(tag)


def _descendants(parent: ET.Element | None, tag: str) -> list[ET.Element]:
    """All descendants named `tag`, namespaced or not."""
    if parent is None:
        return []
    found = parent.findall(f".//{{{NS}}}{tag}")
    if found:
        return found
    return parent.findall(f".//{tag}")


def _text(parent: ET.Element | None, tag: str) -> str:
    el = _child(parent, tag)
    if el is None:
        return ""
    if el.text is None:
        return ""
    return el.text.strip()


def _parse(path: Path, notes: list[str]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        notes.append(f"could not parse {path}: {exc}")
        return None
    except OSError as exc:
        notes.append(f"could not read {path}: {exc}")
        return None


def _find_files(root: Path, *patterns: str) -> list[Path]:
    out: list[Path] = []
    for pattern in patterns:
        out.extend(sorted(root.rglob(pattern)))
    # Deduplicate while preserving order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for item in out:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def _base_name(path: Path, *suffixes: str) -> str:
    name = path.name
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


# ---------------------------------------------------------------------------
# Index the metadata tree
# ---------------------------------------------------------------------------


class MetadataIndex:
    """Everything a PathAssistant depends on, keyed for lookup."""

    def __init__(self, root: Path, parse_notes: list[str]) -> None:
        self.root = root
        self.notes = parse_notes
        # object -> record type developer name -> {"businessProcess": str,
        #                                          "picklists": {field: set(values)}}
        self.record_types: dict[str, dict[str, dict]] = {}
        # object -> business process name -> set(values)
        self.business_processes: dict[str, dict[str, set[str]]] = {}
        # object -> set(field api names, lowercased)
        self.fields: dict[str, set[str]] = {}
        # object -> field -> set(values) from a custom picklist definition
        self.custom_picklists: dict[str, dict[str, set[str]]] = {}
        # standard value set name -> set(values)
        self.standard_value_sets: dict[str, set[str]] = {}
        # objects whose definition is present in the tree at all
        self.known_objects: set[str] = set()
        self.settings_files: list[Path] = []
        self.flexipage_components: dict[str, set[str]] = {}

        self._index_objects()
        self._index_standard_value_sets()
        self._index_settings()
        self._index_flexipages()

    # -- object definitions (source format and mdapi format) ----------------

    def _index_objects(self) -> None:
        # Source format: objects/<Entity>/{fields,recordTypes,businessProcesses}/*
        for obj_dir in _find_files(self.root, "objects/*"):
            if not obj_dir.is_dir():
                continue
            entity = obj_dir.name
            self.known_objects.add(entity)
            for field_file in _find_files(obj_dir, "fields/*.field-meta.xml", "fields/*.field"):
                self._absorb_field(entity, _parse(field_file, self.notes))
            for rt_file in _find_files(
                obj_dir, "recordTypes/*.recordType-meta.xml", "recordTypes/*.recordType"
            ):
                self._absorb_record_type(
                    entity,
                    _base_name(rt_file, ".recordType-meta.xml", ".recordType"),
                    _parse(rt_file, self.notes),
                )
            for bp_file in _find_files(
                obj_dir,
                "businessProcesses/*.businessProcess-meta.xml",
                "businessProcesses/*.businessProcess",
            ):
                self._absorb_business_process(
                    entity,
                    _base_name(bp_file, ".businessProcess-meta.xml", ".businessProcess"),
                    _parse(bp_file, self.notes),
                )

        # MDAPI format: objects/<Entity>.object with everything nested inside.
        for obj_file in _find_files(self.root, "objects/*.object", "objects/*.object-meta.xml"):
            if obj_file.is_dir():
                continue
            entity = _base_name(obj_file, ".object-meta.xml", ".object")
            self.known_objects.add(entity)
            root = _parse(obj_file, self.notes)
            if root is None:
                continue
            for field_el in _children(root, "fields"):
                self._absorb_field(entity, field_el)
            for rt_el in _children(root, "recordTypes"):
                self._absorb_record_type(entity, _text(rt_el, "fullName"), rt_el)
            for bp_el in _children(root, "businessProcesses"):
                self._absorb_business_process(entity, _text(bp_el, "fullName"), bp_el)

    def _absorb_field(self, entity: str, el: ET.Element | None) -> None:
        if el is None:
            return
        api_name = _text(el, "fullName")
        if not api_name:
            return
        self.fields.setdefault(entity, set()).add(api_name.lower())
        values: set[str] = set()
        for value_el in _descendants(el, "value"):
            full = _text(value_el, "fullName")
            if full:
                values.add(full)
        if values:
            self.custom_picklists.setdefault(entity, {})[api_name] = values

    def _absorb_record_type(self, entity: str, name: str, el: ET.Element | None) -> None:
        if el is None or not name:
            return
        picklists: dict[str, set[str]] = {}
        for pv_el in _children(el, "picklistValues"):
            field = _text(pv_el, "picklist")
            if not field:
                continue
            values = set()
            for value_el in _children(pv_el, "values"):
                full = _text(value_el, "fullName")
                if full:
                    values.add(full)
            picklists[field] = values
        self.record_types.setdefault(entity, {})[name] = {
            "businessProcess": _text(el, "businessProcess"),
            "active": _text(el, "active"),
            "picklists": picklists,
        }

    def _absorb_business_process(self, entity: str, name: str, el: ET.Element | None) -> None:
        if el is None or not name:
            return
        # An mdapi nested fullName is bare; a package.xml member is object-qualified.
        bare = name.split(".", 1)[-1]
        values = set()
        for value_el in _children(el, "values"):
            full = _text(value_el, "fullName")
            if full:
                values.add(full)
        self.business_processes.setdefault(entity, {})[bare] = values

    # -- standard value sets -------------------------------------------------

    def _index_standard_value_sets(self) -> None:
        for svs_file in _find_files(
            self.root,
            "standardValueSets/*.standardValueSet-meta.xml",
            "standardValueSets/*.standardValueSet",
        ):
            name = _base_name(svs_file, ".standardValueSet-meta.xml", ".standardValueSet")
            root = _parse(svs_file, self.notes)
            if root is None:
                continue
            values = set()
            for value_el in _children(root, "standardValue"):
                full = _text(value_el, "fullName")
                if full:
                    values.add(full)
            self.standard_value_sets[name] = values

    # -- settings ------------------------------------------------------------

    def _index_settings(self) -> None:
        self.settings_files = _find_files(
            self.root,
            "settings/PathAssistant.settings-meta.xml",
            "settings/PathAssistant.settings",
        )

    # -- flexipages ----------------------------------------------------------

    def _index_flexipages(self) -> None:
        for fp_file in _find_files(
            self.root, "flexipages/*.flexipage-meta.xml", "flexipages/*.flexipage"
        ):
            root = _parse(fp_file, self.notes)
            if root is None:
                continue
            sobject = _text(root, "sobjectType")
            if not sobject:
                continue
            names = {
                el.text.strip()
                for el in _descendants(root, "componentName")
                if el.text is not None and el.text.strip()
            }
            self.flexipage_components.setdefault(sobject, set()).update(names)

    # -- resolution ----------------------------------------------------------

    def resolve_allowed_values(self, entity: str, record_type: str, field: str):
        """Return (values, source) or (None, reason) when it cannot be resolved."""
        rt_entry = self.record_types.get(entity, {}).get(record_type)
        if rt_entry is not None:
            picklists = rt_entry["picklists"]
            if field in picklists and picklists[field]:
                return picklists[field], f"record type {entity}.{record_type} picklistValues"
            bp_name = rt_entry["businessProcess"]
            if bp_name:
                bp_values = self.business_processes.get(entity, {}).get(bp_name)
                if bp_values:
                    return bp_values, f"business process {entity}.{bp_name}"

        svs_name = FIELD_TO_VALUE_SET.get((entity, field))
        if svs_name is not None and svs_name in self.standard_value_sets:
            values = self.standard_value_sets[svs_name]
            if values:
                return values, f"StandardValueSet {svs_name}"

        custom_values = self.custom_picklists.get(entity, {}).get(field)
        if custom_values:
            return custom_values, f"custom picklist {entity}.{field}"

        return None, (
            f"no record type picklistValues, business process, StandardValueSet, or "
            f"custom picklist definition for {entity}.{field} is present in the manifest"
        )


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_paths(index: MetadataIndex, issues: list[str], notes: list[str]) -> int:
    path_files = _find_files(
        index.root, "pathAssistants/*.pathAssistant-meta.xml", "pathAssistants/*.pathAssistant"
    )
    if not path_files:
        return 0

    seen_bindings: dict[tuple[str, str], str] = {}

    for pa_file in path_files:
        name = _base_name(pa_file, ".pathAssistant-meta.xml", ".pathAssistant")
        root = _parse(pa_file, notes)
        if root is None:
            continue

        entity = _text(root, "entityName")
        field = _text(root, "fieldName")
        record_type = _text(root, "recordTypeName")
        active = _text(root, "active").lower() == "true"
        steps = _children(root, "pathAssistantSteps")

        if not entity or not field or not record_type:
            issues.append(
                f"[{name}] entityName, fieldName, and recordTypeName are all Required "
                f"(api_meta.txt L94510-94529); got entityName='{entity}' "
                f"fieldName='{field}' recordTypeName='{record_type}'."
            )
            continue

        # Check 5: one path per object + record type (api_meta.txt L94496).
        binding = (entity, record_type)
        if binding in seen_bindings:
            issues.append(
                f"[{name}] a second path targets {entity} / record type {record_type} "
                f"(already claimed by '{seen_bindings[binding]}'). Only one path can be "
                "created per record type for each object, including __Master__ "
                "(api_meta.txt L94496)."
            )
        else:
            seen_bindings[binding] = name

        # Check 3: recordTypeName resolves.
        if record_type.lower() not in MASTER_RECORD_TYPE_NAMES:
            if entity in index.known_objects:
                if record_type not in index.record_types.get(entity, {}):
                    issues.append(
                        f"[{name}] recordTypeName '{record_type}' does not resolve to a "
                        f"record type of {entity} in this manifest. The path will deploy "
                        "and bind to nothing users can see."
                    )
            else:
                notes.append(
                    f"[{name}] object {entity} is not in this manifest, so recordTypeName "
                    f"'{record_type}' could not be resolved."
                )

        # Check 4a: active path with no steps.
        if not steps:
            if active:
                issues.append(
                    f"[{name}] active=true with zero pathAssistantSteps. The chevrons still "
                    "render from the record type's picklist values, but every stage will be "
                    "blank (api_meta.txt L94525-94526)."
                )
            else:
                notes.append(f"[{name}] inactive path with no steps configured.")
            continue

        allowed, source = index.resolve_allowed_values(entity, record_type, field)
        if allowed is None:
            notes.append(f"[{name}] step names not verified: {source}.")

        seen_values: set[str] = set()
        for step in steps:
            value = _text(step, "picklistValueName")
            info = _text(step, "info")
            field_names = [
                el.text.strip()
                for el in _children(step, "fieldNames")
                if el.text is not None and el.text.strip()
            ]
            label = value if value else "(unnamed step)"

            if not value:
                issues.append(
                    f"[{name}] a step has no picklistValueName; the field is Required "
                    "(api_meta.txt L94549)."
                )
                continue

            if value in seen_values:
                issues.append(
                    f"[{name}] step '{value}' is declared more than once in the same path."
                )
            seen_values.add(value)

            # Check 1: the step names a value the record type can actually show.
            if allowed is not None and value not in allowed:
                issues.append(
                    f"[{name}] step '{value}' is not a value of {entity}.{field} per "
                    f"{source}. The chevron will not render for this step. Known values: "
                    f"{', '.join(sorted(allowed))}."
                )

            # Check 2: custom key fields exist on the entity.
            known_fields = index.fields.get(entity, set())
            for key_field in field_names:
                if not key_field.lower().endswith("__c"):
                    continue  # standard fields cannot be resolved from source alone
                if entity not in index.known_objects:
                    continue
                if key_field.lower() not in known_fields:
                    issues.append(
                        f"[{name}] step '{label}' key field '{key_field}' is not defined on "
                        f"{entity} in this manifest. fieldNames must name fields in "
                        "entityName (api_meta.txt L94545)."
                    )

            # Check 4b: a step configured with neither key fields nor guidance.
            if not field_names and not info:
                issues.append(
                    f"[{name}] step '{label}' has neither fieldNames nor info — it is an "
                    "empty step element that configures nothing. Remove it, or give it "
                    "content."
                )

            # Check 6: guidance and key-field sanity.
            if info and len(info) < MIN_USEFUL_INFO_CHARS:
                notes.append(
                    f"[{name}] step '{label}' guidance is {len(info)} characters — likely "
                    "placeholder text rather than usable guidance."
                )
            if len(info) > SOFT_MAX_INFO_CHARS:
                notes.append(
                    f"[{name}] step '{label}' guidance is {len(info)} characters. No "
                    "documented limit exists in the Metadata API guide, but guidance this "
                    "long is not read."
                )
            if len(field_names) > SOFT_MAX_KEY_FIELDS:
                notes.append(
                    f"[{name}] step '{label}' declares {len(field_names)} key fields. The "
                    f"commonly cited cap is {SOFT_MAX_KEY_FIELDS} per step; it is not stated "
                    "in the Metadata API guide, so verify against Setup > Path Settings."
                )

        # Check 6c: is anything going to render this path?
        components = index.flexipage_components.get(entity)
        if components is not None and PATH_COMPONENT_NAME not in components:
            notes.append(
                f"[{name}] no FlexiPage for {entity} in this manifest contains "
                f"<componentName>{PATH_COMPONENT_NAME}</componentName>. If the target org's "
                "record page does not already have it, nothing will render."
            )

    return len(path_files)


def check_settings(index: MetadataIndex, path_count: int, issues: list[str], notes: list[str]):
    if path_count == 0:
        return
    if not index.settings_files:
        issues.append(
            "[settings] no settings/PathAssistant.settings-meta.xml in this manifest while "
            f"{path_count} path(s) are being deployed. pathAssistantEnabled defaults to true "
            "for Enterprise Edition and false for other editions (api_meta.txt "
            "L124222-124224), and 'the preference does not need to be on to retrieve or "
            "deploy PathAssistant' (api_meta.txt L94498) — so the deploy will succeed and "
            "nothing will render in a non-EE org."
        )
        return

    for settings_file in index.settings_files:
        root = _parse(settings_file, notes)
        if root is None:
            continue
        enabled = _child(root, "pathAssistantEnabled")
        if enabled is None:
            issues.append(
                f"[{settings_file.name}] pathAssistantEnabled is absent. Assert it "
                "explicitly rather than inheriting the edition default."
            )
        elif enabled.text is None or enabled.text.strip().lower() != "true":
            issues.append(
                f"[{settings_file.name}] pathAssistantEnabled is not true. No path will "
                "render anywhere in the org."
            )

        collapse = _child(root, "canOverrideAutoPathCollapseWithUserPref")
        if collapse is None or collapse.text is None or collapse.text.strip().lower() != "true":
            notes.append(
                f"[{settings_file.name}] canOverrideAutoPathCollapseWithUserPref is not "
                "true. Default is false for all editions, and when false 'the user's path "
                "is collapsed when the page loads' (api_meta.txt L124216-124221) — the "
                "guidance you wrote will be hidden behind a click on every record."
            )

        legacy = _child(root, "pathAssistantForOpportunityEnabled")
        if legacy is not None:
            notes.append(
                f"[{settings_file.name}] pathAssistantForOpportunityEnabled is present; it "
                "is API 34.0 and earlier (api_meta.txt L124226-124228). Remove it."
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cross-check Salesforce PathAssistant metadata against the record "
        "types, value sets, fields and settings in the same manifest directory.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the retrieved metadata or the Salesforce DX project "
        "(default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero on NOTE lines as well as ISSUE lines.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.is_dir():
        print(f"ISSUE: manifest directory not found: {manifest_dir}")
        return 1

    issues: list[str] = []
    notes: list[str] = []

    index = MetadataIndex(manifest_dir, notes)
    path_count = check_paths(index, issues, notes)

    if path_count == 0:
        print(f"No PathAssistant metadata found under {manifest_dir} — nothing to check.")
        return 0

    check_settings(index, path_count, issues, notes)

    for note in notes:
        print(f"NOTE: {note}")
    for issue in issues:
        print(f"ISSUE: {issue}")

    if not issues and not notes:
        print(f"Checked {path_count} path(s): no issues found.")
    else:
        print(f"Checked {path_count} path(s): {len(issues)} issue(s), {len(notes)} note(s).")

    if issues:
        return 1
    if notes and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
