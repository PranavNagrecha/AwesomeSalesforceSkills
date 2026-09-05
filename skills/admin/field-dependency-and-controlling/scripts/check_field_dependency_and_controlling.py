#!/usr/bin/env python3
"""Checker for the Field Dependency and Controlling skill.

Validates dependent-picklist metadata in a retrieved/authored manifest directory.
Handles both SFDX decomposed source (``objects/<Obj>/fields/<F>.field-meta.xml``)
and MDAPI ``objects/<Obj>.object`` files.

Checks (all grounded in the Metadata API Developer Guide, Summer '26 / v62):

  1. Every ``<controllingField>`` names a field that exists on the same object and
     whose ``<type>`` is Picklist or Checkbox. "A controlling field can be a
     checkbox or picklist field" (api_meta.txt:45843-45845).
  2. Every ``<controllingFieldValue>`` exists in the controlling field's value set.
     For a Checkbox controller the only legal literals are ``checked`` and
     ``unchecked`` (api_meta.txt:79250-79258) - ``true``/``false`` is the common
     and silent failure.
  3. Dependent values that no controlling value enables are reported: they are
     unreachable in the UI even though they deploy cleanly.
  4. Where the object has record types that list the dependent field, every
     dependent value the matrix enables must also appear in that record type's
     ``picklistValues``; availability is the intersection
     (api_meta.txt:45051-45052).
  5. (Retained) A dependent picklist with no validation rule naming both fields is
     unenforced on every non-UI write path - the dependency filter is browser
     JavaScript only (apexdev.txt:15404-15406).

Exit status: 0 when no ERROR-level findings, 1 otherwise. WARNs never fail the run.

Usage:
    python3 check_field_dependency_and_controlling.py --manifest-dir force-app/main/default
    python3 check_field_dependency_and_controlling.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}
NS_URI = "http://soap.sforce.com/2006/04/metadata"

CHECKBOX_LITERALS = {"checked", "unchecked"}
CONTROLLER_TYPES = {"Picklist", "Checkbox"}


# --------------------------------------------------------------------------- #
# ElementTree helpers.
#
# A leaf Element is falsy, so ``el.find(a) or el.find(b)`` silently discards a
# real match. Everything below tests ``is not None`` explicitly.
# --------------------------------------------------------------------------- #

def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def child(el, *names):
    """First direct child matching any of *names*, namespaced or not. None if absent."""
    if el is None:
        return None
    for name in names:
        found = el.find(f"sf:{name}", NS)
        if found is not None:
            return found
        found = el.find(name)
        if found is not None:
            return found
    return None


def children(el, *names):
    """All direct children matching any of *names*, namespaced or not."""
    out = []
    if el is None:
        return out
    for name in names:
        out.extend(el.findall(f"sf:{name}", NS))
        out.extend(el.findall(name))
    return out


def text_of(el, *names, default: str = "") -> str:
    node = child(el, *names)
    if node is None or node.text is None:
        return default
    return node.text.strip()


def texts_of(el, *names) -> list[str]:
    return [n.text.strip() for n in children(el, *names) if n is not None and n.text]


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #

class FieldInfo:
    """One CustomField, however it was serialised."""

    def __init__(self, name: str, ftype: str, source: str, element) -> None:
        self.name = name
        self.type = ftype
        self.source = source
        self.element = element

    @property
    def value_set(self):
        return child(self.element, "valueSet")

    @property
    def controlling_field(self) -> str:
        return text_of(self.value_set, "controllingField")

    @property
    def value_set_name(self) -> str:
        """Global value set reference, if the field inherits its values."""
        return text_of(self.value_set, "valueSetName")

    def own_values(self) -> list[str]:
        """fullNames declared in this field's own valueSetDefinition."""
        definition = child(self.value_set, "valueSetDefinition")
        if definition is None:
            return []
        return [text_of(v, "fullName") for v in children(definition, "value") if text_of(v, "fullName")]

    def pairs(self) -> list[tuple[str, str]]:
        """(controllingFieldValue, valueName) pairs from every valueSettings block."""
        out: list[tuple[str, str]] = []
        vs = self.value_set
        if vs is None:
            return out
        for block in children(vs, "valueSettings"):
            dependent = text_of(block, "valueName")
            for controlling in texts_of(block, "controllingFieldValue", "controllingFieldValues"):
                out.append((controlling, dependent))
        return out

    def has_value_settings(self) -> bool:
        return bool(children(self.value_set, "valueSettings"))

    def legal_controller_values(self) -> set[str] | None:
        """Values this field can present as a controller, or None if unknowable here."""
        if self.type == "Checkbox":
            return set(CHECKBOX_LITERALS)
        if self.value_set_name:
            return None  # values live in a GlobalValueSet outside this file
        own = self.own_values()
        return set(own) if own else None


class ObjectInfo:
    def __init__(self, name: str, root: Path) -> None:
        self.name = name
        self.root = root
        self.fields: dict[str, FieldInfo] = {}
        # record type -> field name -> set of values
        self.record_types: dict[str, dict[str, set[str]]] = {}
        self.validation_rule_text: str = ""


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #

def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _parse(path: Path):
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def load_objects(root: Path) -> dict[str, ObjectInfo]:
    objects: dict[str, ObjectInfo] = {}

    def obj(name: str) -> ObjectInfo:
        if name not in objects:
            objects[name] = ObjectInfo(name, root)
        return objects[name]

    # --- SFDX decomposed source -------------------------------------------- #
    for field_xml in sorted(root.rglob("*.field-meta.xml")):
        el = _parse(field_xml)
        if el is None or strip_ns(el.tag) != "CustomField":
            continue
        fields_dir = field_xml.parent
        object_dir = fields_dir.parent if fields_dir.name == "fields" else fields_dir
        name = text_of(el, "fullName") or field_xml.name.split(".")[0]
        obj(object_dir.name).fields[name] = FieldInfo(
            name, text_of(el, "type"), _rel(field_xml, root), el
        )

    for rt_xml in sorted(root.rglob("*.recordType-meta.xml")):
        el = _parse(rt_xml)
        if el is None or strip_ns(el.tag) != "RecordType":
            continue
        rt_dir = rt_xml.parent
        object_dir = rt_dir.parent if rt_dir.name == "recordTypes" else rt_dir
        rt_name = text_of(el, "fullName") or rt_xml.name.split(".")[0]
        obj(object_dir.name).record_types[rt_name] = _record_type_map(el)

    for vr_xml in sorted(root.rglob("*.validationRule-meta.xml")):
        vr_dir = vr_xml.parent
        object_dir = vr_dir.parent if vr_dir.name == "validationRules" else vr_dir
        try:
            obj(object_dir.name).validation_rule_text += vr_xml.read_text(
                encoding="utf-8", errors="ignore"
            )
        except OSError:
            continue

    # --- MDAPI single-file objects ----------------------------------------- #
    for object_xml in sorted(list(root.rglob("*.object")) + list(root.rglob("*.object-meta.xml"))):
        el = _parse(object_xml)
        if el is None or strip_ns(el.tag) != "CustomObject":
            continue
        name = object_xml.name.split(".")[0]
        info = obj(name)
        for fel in children(el, "fields"):
            fname = text_of(fel, "fullName")
            if fname and fname not in info.fields:
                info.fields[fname] = FieldInfo(
                    fname, text_of(fel, "type"), _rel(object_xml, root), fel
                )
        for rtel in children(el, "recordTypes"):
            rt_name = text_of(rtel, "fullName")
            if rt_name and rt_name not in info.record_types:
                info.record_types[rt_name] = _record_type_map(rtel)
        for vrel in children(el, "validationRules"):
            info.validation_rule_text += ET.tostring(vrel, encoding="unicode")

    return objects


def _record_type_map(rt_el) -> dict[str, set[str]]:
    """RecordType -> {picklist field name: {value fullNames}}."""
    out: dict[str, set[str]] = {}
    for pv in children(rt_el, "picklistValues"):
        field_name = text_of(pv, "picklist")
        if not field_name:
            continue
        values = {
            text_of(v, "fullName")
            for v in children(pv, "values")
            if text_of(v, "fullName")
        }
        out.setdefault(field_name, set()).update(values)
    return out


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

class Finding:
    def __init__(self, level: str, where: str, message: str) -> None:
        self.level = level
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.level}: {self.where}: {self.message}"


def check_object(info: ObjectInfo) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    pair_total = 0

    for field in sorted(info.fields.values(), key=lambda f: f.name):
        controlling_name = field.controlling_field
        has_settings = field.has_value_settings()

        if not controlling_name and not has_settings:
            continue

        where = f"{info.name}.{field.name} ({field.source})"

        if has_settings and not controlling_name:
            findings.append(Finding(
                "ERROR", where,
                "valueSettings present but no <controllingField> - the pairs are inert and "
                "the field behaves as an ordinary independent picklist",
            ))
            continue

        if not has_settings:
            findings.append(Finding(
                "ERROR", where,
                f"declares <controllingField>{controlling_name}</controllingField> but no "
                "valueSettings - the matrix is empty, so every dependent value is unreachable",
            ))
            continue

        pairs = field.pairs()
        pair_total += len(pairs)

        # --- Check 1: the controller exists and is a legal type ------------- #
        controller = info.fields.get(controlling_name)
        if controller is None:
            findings.append(Finding(
                "ERROR", where,
                f"<controllingField>{controlling_name}</controllingField> does not resolve to a "
                f"field on {info.name} in this manifest. Note controllingField is relative to the "
                "object - it must not carry an Object__c. prefix",
            ))
        elif controller.type and controller.type not in CONTROLLER_TYPES:
            findings.append(Finding(
                "ERROR", where,
                f"controlling field {controlling_name} is <type>{controller.type}</type>; "
                "only Picklist or Checkbox may control a dependent picklist "
                "(api_meta.txt:45843-45845)",
            ))

        # --- Check 2: every controllingFieldValue is real ------------------- #
        legal = controller.legal_controller_values() if controller is not None else None
        if controller is not None and controller.type == "Checkbox":
            for controlling_value, dependent_value in pairs:
                if controlling_value not in CHECKBOX_LITERALS:
                    findings.append(Finding(
                        "ERROR", where,
                        f"controllingFieldValue '{controlling_value}' (for value "
                        f"'{dependent_value}') is not legal for the Checkbox controller "
                        f"{controlling_name}; use 'checked' or 'unchecked' "
                        "(api_meta.txt:79250-79258)",
                    ))
        elif legal is not None:
            for controlling_value, dependent_value in pairs:
                if controlling_value not in legal:
                    findings.append(Finding(
                        "ERROR", where,
                        f"controllingFieldValue '{controlling_value}' (for value "
                        f"'{dependent_value}') is not in {controlling_name}'s value set "
                        f"{sorted(legal)} - the pair deploys but enables nothing",
                    ))
        elif controller is not None and controller.value_set_name:
            findings.append(Finding(
                "WARN", where,
                f"controlling field {controlling_name} inherits global value set "
                f"'{controller.value_set_name}'; its values are not in this manifest, so "
                "controllingFieldValue spellings could not be checked",
            ))

        # --- Check 3: dependent values no controlling value enables --------- #
        declared = field.own_values()
        enabled = {dependent for _, dependent in pairs}
        if declared:
            orphans = [v for v in declared if v not in enabled]
            for value in orphans:
                findings.append(Finding(
                    "ERROR", where,
                    f"dependent value '{value}' is not enabled for any controlling value - "
                    "it can never be selected in the UI",
                ))
            unknown = sorted(v for v in enabled if v and v not in set(declared))
            for value in unknown:
                findings.append(Finding(
                    "ERROR", where,
                    f"valueSettings names '{value}' but that value is not in this field's "
                    "valueSetDefinition",
                ))
        elif field.value_set_name:
            findings.append(Finding(
                "WARN", where,
                f"field inherits global value set '{field.value_set_name}', so unreachable "
                "dependent values could not be checked from this manifest",
            ))

        # --- Check 4: record types must carry the dependent values ---------- #
        for rt_name, rt_map in sorted(info.record_types.items()):
            if field.name not in rt_map:
                continue  # this record type does not constrain the dependent field
            rt_values = rt_map[field.name]
            controller_rt_values = rt_map.get(controlling_name)
            for controlling_value, dependent_value in sorted(set(pairs)):
                if controller_rt_values is not None and controlling_value not in controller_rt_values:
                    continue  # controller value unavailable here; pair is moot by design
                if dependent_value and dependent_value not in rt_values:
                    findings.append(Finding(
                        "ERROR", where,
                        f"record type '{rt_name}' offers controlling value "
                        f"'{controlling_value}' but omits dependent value "
                        f"'{dependent_value}' from its picklistValues - availability is the "
                        "intersection of record type and matrix (api_meta.txt:45051-45052)",
                    ))

        # --- Check 5: nothing enforces the matrix off the browser ----------- #
        vr_text = info.validation_rule_text
        if not (field.name in vr_text and controlling_name in vr_text):
            findings.append(Finding(
                "WARN", where,
                f"no validation rule in this manifest references both '{field.name}' and "
                f"'{controlling_name}'. The dependency filter is browser JavaScript only "
                "(apexdev.txt:15404-15406), so Data Loader, Bulk API, REST and Apex DML can "
                "write any combination",
            ))

    return findings, pair_total


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate dependent-picklist metadata in a manifest directory."
    )
    parser.add_argument(
        "--manifest-dir", default=".",
        help="Root of the metadata to scan (e.g. force-app/main/default).",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat WARN findings as failures.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: directory not found: {root}", file=sys.stderr)
        return 1

    objects = load_objects(root)
    if not objects:
        print(f"No object metadata found under {root}.")
        return 0

    all_findings: list[Finding] = []
    dependent_fields = 0
    pair_total = 0

    for info in sorted(objects.values(), key=lambda o: o.name):
        findings, pairs = check_object(info)
        all_findings.extend(findings)
        pair_total += pairs
        dependent_fields += sum(
            1 for f in info.fields.values() if f.controlling_field or f.has_value_settings()
        )

    errors = [f for f in all_findings if f.level == "ERROR"]
    warns = [f for f in all_findings if f.level == "WARN"]

    for finding in all_findings:
        stream = sys.stderr if finding.level == "ERROR" else sys.stdout
        print(finding, file=stream)

    print(
        f"\nScanned {len(objects)} object(s); {dependent_fields} dependent picklist(s); "
        f"{pair_total} enabled pair(s). "
        f"{len(errors)} error(s), {len(warns)} warning(s)."
    )
    if pair_total:
        print(
            "Compare the pair count against the Setup Field Dependencies grid - a deploy can add "
            "pairs but never remove one (api_meta.txt:45855-45858)."
        )

    if errors or (args.strict and warns):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
