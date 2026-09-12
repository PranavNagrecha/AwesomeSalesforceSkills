#!/usr/bin/env python3
"""Lint validation rule metadata for common admin mistakes.

VR-REF-01/VR-REF-02 do best-effort, offline reference resolution: a `__c`
field token (in `errorConditionFormula` or `errorDisplayField`) or a
`$Permission.X` token is checked against whatever `objects/<Object>/fields/`
or `customPermissions/` metadata the *same scan* happens to carry. Standard
fields (no `__c`) are never flagged -- there is no standard-field inventory to
check them against, and the platform, not this script, is the source of truth
for whether e.g. `Priority` exists. This is scope-dependent: point the scan at
one build step's directory and the fields it depends on usually live in a
different step, so there is nothing to resolve against -- see the INFO finding
below rather than reading that silence as "checked and clean".

VR-PICK-01 is offline-detectable too, and needs no field inventory: it flags
any field passed directly to ISBLANK()/ISNULL() that this same formula also
passes as the first argument to ISPICKVAL() -- the signature of a picklist.
Salesforce rejects ISBLANK()/ISNULL() applied directly to a picklist at
deploy time; TEXT(<field>) first is the fix. Works for standard fields (e.g.
`Priority`, `StageName`) exactly as well as `__c` fields, since it never
needs to check a field-type inventory -- it only needs the formula text.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


# `.object` is metadata format (rules embedded in <CustomObject>);
# `.object-meta.xml` and `.validationRule-meta.xml` are DX source format.
METADATA_SUFFIXES = (".object", ".object-meta.xml", ".validationRule-meta.xml")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0, "INFO": 0}

# VR-REF-01/02: a custom field token (optionally relationship-qualified, e.g.
# `Account.Region__c`) or a `$Permission.X` reference in formula text.
# Standard fields never match -- they don't end in `__c` -- which is exactly
# why they are never flagged.
FIELD_TOKEN = re.compile(r"(?:([A-Za-z_]\w*)\.)?([A-Za-z_]\w*__c)\b")
PERMISSION_TOKEN = re.compile(r"\$Permission\.([A-Za-z_]\w*)")
FIELD_META_SUFFIX = ".field-meta.xml"
CUSTOM_PERMISSION_SUFFIX = ".customPermission-meta.xml"

# Metadata API Developer Guide, ValidationRule: "As of API version 20.0,
# validation rules can't have compound fields." Uppercase; matched against the
# uppercased formula text.
COMPOUND_FIELDS = (
    "BILLINGADDRESS",
    "SHIPPINGADDRESS",
    "MAILINGADDRESS",
    "OTHERADDRESS",
    "GEOCODEACCURACY",
)

# VR-PICK-01: ISBLANK()/ISNULL() applied directly to a field that is also
# passed as the first argument of ISPICKVAL() in the same formula -- the
# offline-detectable signature of a picklist field. Proven live via
# `sf project deploy start --dry-run` (API 67.0, 2026-09-12): the org rejects
# ISBLANK()/ISNULL() applied directly to a picklist with "Field <X> is a
# picklist field. Picklist fields are only supported in certain functions."
# ISPICKVAL(), PRIORVALUE() and ISCHANGED() already accept the picklist
# directly and need no TEXT() wrapper -- see references/gotchas.md Gotcha 14.
# The dotted form (e.g. Account.Industry) is supported on both sides so a
# cross-object reference matches identically.
ISPICKVAL_FIRST_ARG = re.compile(
    r"ISPICKVAL\s*\(\s*([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*,", re.IGNORECASE
)
DIRECT_BLANK_OR_NULL = re.compile(
    r"IS(?:BLANK|NULL)\s*\(\s*([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s*\)", re.IGNORECASE
)


def find_direct_picklist_blank_calls(formula: str) -> list[str]:
    """Fields passed directly to ISBLANK()/ISNULL() that this same formula
    also passes as the first argument to ISPICKVAL() -- i.e. a picklist.
    `ISBLANK(TEXT(Field))` does not match DIRECT_BLANK_OR_NULL (the `)`
    doesn't immediately follow the identifier), so the TEXT()-wrapped, correct
    form is never flagged.
    """
    picklist_fields = {match.upper() for match in ISPICKVAL_FIRST_ARG.findall(formula)}
    if not picklist_fields:
        return []
    hits = []
    for field in DIRECT_BLANK_OR_NULL.findall(formula):
        if field.upper() in picklist_fields:
            hits.append(field)
    return hits


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, child_name: str) -> str:
    """Text of the first matching child, or "" when the child is absent.

    Deliberately loops instead of `element.find(a) or element.find(b)`:
    a childless ElementTree Element is falsy, so `or` chains on find() silently
    discard real leaf elements such as <active>false</active>.
    """
    for child in element:
        if local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return ""


def has_child(element: ET.Element, child_name: str) -> bool:
    """True when the child element is present, even if it is empty."""
    for child in element:
        if local_name(child.tag) == child_name:
            return True
    return False


@dataclass(frozen=True)
class Rule:
    full_name: str
    active: bool
    formula: str
    error_message: str
    error_display_field: str
    has_error_message_element: bool


def read_rule(element: ET.Element, fallback_name: str) -> Rule:
    return Rule(
        full_name=child_text(element, "fullName") or fallback_name,
        active=child_text(element, "active").lower() == "true",
        formula=child_text(element, "errorConditionFormula"),
        error_message=child_text(element, "errorMessage"),
        error_display_field=child_text(element, "errorDisplayField"),
        has_error_message_element=has_child(element, "errorMessage"),
    )


def iter_metadata_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.name.endswith(METADATA_SUFFIXES):
                    files.append(candidate)
        elif path.is_file() and path.name.endswith(METADATA_SUFFIXES):
            files.append(path)
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


BLOCKING_SEVERITIES = {"CRITICAL", "HIGH"}

# INFO is scope commentary, not a finding about the rule itself (e.g. "this
# object has no field inventory in this scan, so field/errorDisplayField
# references were not checked"). --strict promotes every actual finding
# (REVIEW included, unchanged) but must not fail a correct build merely
# because it was scanned one step at a time -- see the M3-S01 step-scope
# fixture, which is exactly that shape and must stay green under --strict.
NEVER_STRICT_SEVERITIES = {"INFO"}


def emit_result(findings: list[str], summary: str, strict: bool = False) -> int:
    """Print the JSON report and return the exit code.

    Exit 1 only on CRITICAL/HIGH findings (platform facts that will fail or
    misbehave at deploy or run time). MEDIUM/LOW/REVIEW are advisory and exit 0
    so a build that produced correct rules with natural formulas stays green;
    pass --strict to promote every finding to a failure, except INFO (see
    NEVER_STRICT_SEVERITIES above), which stays advisory even under --strict.
    """
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    blocking = [item for item in normalized if item["severity"] in BLOCKING_SEVERITIES]
    print(json.dumps({"score": score, "findings": normalized, "summary": summary,
                      "blocking": len(blocking)}, indent=2))
    if normalized:
        print(f"WARN: {len(normalized)} finding(s) detected ({len(blocking)} blocking)", file=sys.stderr)
    if blocking:
        return 1
    strict_eligible = [item for item in normalized if item["severity"] not in NEVER_STRICT_SEVERITIES]
    return 1 if (strict and strict_eligible) else 0


def collect_rules(path: Path) -> list[Rule]:
    """Read every ValidationRule in a file.

    Two shapes are supported: the metadata-format `.object` file, where rules
    are repeated `<validationRules>` children of `<CustomObject>`, and the DX
    source-format file whose root element is `<ValidationRule>` itself.
    """
    root = ET.parse(path).getroot()
    root_type = local_name(root.tag)
    rules: list[Rule] = []

    if root_type == "ValidationRule":
        rules.append(read_rule(root, fallback_name=path.stem))
        return rules

    if root_type != "CustomObject":
        return rules

    for child in root:
        if local_name(child.tag) == "validationRules":
            rules.append(read_rule(child, fallback_name="<unnamed rule>"))
    return rules


def object_from_objects_path(path: Path) -> str | None:
    """Object API name for a metadata file, from its `objects/<Object>/...`
    ancestor directory. Works for `.validationRule-meta.xml`, `.field-meta.xml`
    and the CustomObject-embedded `.object` / `.object-meta.xml` shapes alike,
    since all three live under that same directory in both DX and a retrieved
    metadata-format package. Falls back to the bare `<Object>.object[-meta.xml]`
    file name when there is no `objects/` ancestor (e.g. a lone file passed with
    no enclosing directory structure).
    """
    parts = path.parts
    for index, part in enumerate(parts):
        if part == "objects" and index + 1 < len(parts):
            return parts[index + 1]
    name = path.name
    if name.endswith(".object-meta.xml"):
        return name[: -len(".object-meta.xml")]
    if name.endswith(".object"):
        return name[: -len(".object")]
    return None


def collect_field_inventory(targets: list[Path]) -> tuple[dict[str, set[str]], set[str]]:
    """Best-effort custom-field inventory for VR-REF-01, built from whatever
    field metadata the scanned tree happens to carry: standalone
    `objects/<Object>/fields/*.field-meta.xml` files, and `<fields>` /
    `<CustomField>` elements embedded directly in a `.object` /
    `.object-meta.xml` CustomObject file.

    Returns `(fields_by_object, objects_with_inventory)`. Only `__c` names are
    collected in `fields_by_object` -- standard fields are never flagged, so
    nothing needs to know them. `objects_with_inventory` is presence, not
    population: an object can legitimately have a field file and zero `__c`
    fields in it, which still means "this scope can check that object", not
    "absent".
    """
    fields_by_object: dict[str, set[str]] = defaultdict(set)
    objects_with_inventory: set[str] = set()

    field_files: set[Path] = set()
    object_meta_files: set[Path] = set()
    for target in targets:
        if target.is_dir():
            field_files.update(p for p in target.rglob(f"*{FIELD_META_SUFFIX}") if p.is_file())
            object_meta_files.update(
                p for p in target.rglob("*")
                if p.is_file() and (p.name.endswith(".object-meta.xml") or p.name.endswith(".object"))
            )
        elif target.is_file():
            if target.name.endswith(FIELD_META_SUFFIX):
                field_files.add(target)
            elif target.name.endswith(".object-meta.xml") or target.name.endswith(".object"):
                object_meta_files.add(target)

    for path in sorted(field_files):
        obj = object_from_objects_path(path)
        if obj is None:
            continue
        objects_with_inventory.add(obj)
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        field_name = child_text(root, "fullName")
        if field_name.endswith("__c"):
            fields_by_object[obj].add(field_name)

    for path in sorted(object_meta_files):
        obj = object_from_objects_path(path)
        if obj is None:
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if local_name(root.tag) != "CustomObject":
            continue
        for child in root:
            if local_name(child.tag) in ("fields", "CustomField"):
                objects_with_inventory.add(obj)
                field_name = child_text(child, "fullName")
                if field_name.endswith("__c"):
                    fields_by_object[obj].add(field_name)

    return dict(fields_by_object), objects_with_inventory


def collect_custom_permission_names(targets: list[Path]) -> tuple[set[str], bool]:
    """Custom Permission API names from `customPermissions/*.customPermission-meta.xml`
    anywhere in the scanned tree, and whether a `customPermissions` directory
    exists in the tree at all -- the gate for VR-REF-02. When it does not
    exist, `$Permission` tokens are left unchecked rather than guessed at: an
    empty result would otherwise be indistinguishable from "checked, and every
    permission exists".
    """
    names: set[str] = set()
    dir_found = False
    for target in targets:
        if target.is_dir():
            if any(p.is_dir() and p.name == "customPermissions" for p in target.rglob("*")):
                dir_found = True
            for candidate in target.rglob(f"*{CUSTOM_PERMISSION_SUFFIX}"):
                if candidate.is_file():
                    names.add(candidate.name[: -len(CUSTOM_PERMISSION_SUFFIX)])
                    dir_found = True
        elif target.is_file() and target.name.endswith(CUSTOM_PERMISSION_SUFFIX):
            names.add(target.name[: -len(CUSTOM_PERMISSION_SUFFIX)])
            dir_found = True
    return names, dir_found


def audit_rule_references(
    path: Path,
    rule: Rule,
    object_name: str | None,
    fields_by_object: dict[str, set[str]],
    objects_with_inventory: set[str],
    permission_names: set[str],
    permission_dir_found: bool,
) -> tuple[list[str], bool]:
    """VR-REF-01/VR-REF-02: resolve what CAN be resolved offline.

    Returns `(findings, inventory_was_absent)`. The second value lets the
    caller fold every rule whose object had no field inventory in this scope
    into one INFO instead of one per rule, mirroring how
    admin/record-types-and-page-layouts reports an unresolvable-at-this-scope
    count rather than staying silent about a check it could not make.
    """
    findings: list[str] = []
    name = rule.full_name
    has_own_inventory = object_name is not None and object_name in objects_with_inventory

    field_tokens = set(FIELD_TOKEN.findall(rule.formula))
    if rule.error_display_field.endswith("__c"):
        field_tokens.add(("", rule.error_display_field))

    if has_own_inventory:
        for prefix, field in sorted(field_tokens):
            if prefix:
                continue  # relationship-qualified; resolved in the loop below
            if field not in fields_by_object.get(object_name, set()):
                findings.append(
                    f"HIGH {path}::{name}: VR-REF-01 references {field}, which has no "
                    f"matching field file under objects/{object_name}/fields/ in the "
                    "scanned tree"
                )

    for prefix, field in sorted(field_tokens):
        if not prefix:
            continue
        if prefix not in objects_with_inventory:
            # Foreign-object reference this scope can't verify -- skip rather
            # than guess, same as a missing customPermissions/ directory below.
            continue
        if field not in fields_by_object.get(prefix, set()):
            findings.append(
                f"HIGH {path}::{name}: VR-REF-01 formula references {prefix}.{field}, "
                f"which has no matching field file under objects/{prefix}/fields/ in "
                "the scanned tree"
            )

    if permission_dir_found:
        for permission in sorted(set(PERMISSION_TOKEN.findall(rule.formula))):
            if permission not in permission_names:
                findings.append(
                    f"HIGH {path}::{name}: VR-REF-02 formula references "
                    f"$Permission.{permission}, which has no matching "
                    f"customPermissions/{permission}{CUSTOM_PERMISSION_SUFFIX} in the "
                    "scanned tree"
                )

    return findings, not has_own_inventory


# Metadata API Developer Guide, ValidationRule: "The message must be 255
# characters or less."
ERROR_MESSAGE_MAX = 255


def audit_rule(path: Path, rule: Rule) -> list[str]:
    findings: list[str] = []
    name = rule.full_name
    upper_formula = rule.formula.upper()
    message = rule.error_message
    normalized_error = message.strip().lower()

    # --- errorMessage: required, capped at 255, and useless when generic -----
    if rule.active and not message.strip():
        findings.append(
            f"CRITICAL {path}::{name}: active rule has an empty or missing errorMessage; "
            "errorMessage is a required element and the user sees nothing actionable"
        )
    elif not rule.has_error_message_element:
        findings.append(
            f"HIGH {path}::{name}: no errorMessage element; the deploy will be rejected"
        )

    if len(message) > ERROR_MESSAGE_MAX:
        findings.append(
            f"HIGH {path}::{name}: errorMessage is {len(message)} characters; "
            f"the platform cap is {ERROR_MESSAGE_MAX}"
        )
    elif message.strip() and (len(message.strip()) < 20 or "validation error" in normalized_error):
        findings.append(
            f"MEDIUM {path}::{name}: error message is too generic to act on"
        )

    # --- $Profile.Name gating is an anti-pattern -----------------------------
    if "$PROFILE.NAME" in upper_formula:
        findings.append(
            f"HIGH {path}::{name}: formula gates on $Profile.Name; a renamed profile "
            "silently changes who the rule applies to. Use a Custom Permission"
        )

    if "$USER.ID" in upper_formula or "'005" in rule.formula or '"005' in rule.formula:
        findings.append(
            f"HIGH {path}::{name}: formula appears to reference a hardcoded User Id; "
            "it dies when that person leaves"
        )

    # --- formula correctness -------------------------------------------------
    if "PRIORVALUE(" in upper_formula and "ISNEW()" not in upper_formula:
        findings.append(
            f"HIGH {path}::{name}: PRIORVALUE is used without an ISNEW guard"
        )

    if "ISCHANGED(" in upper_formula and "ISNEW()" not in upper_formula:
        findings.append(
            f"MEDIUM {path}::{name}: ISCHANGED without an ISNEW guard also fires on insert"
        )

    if "RECORDTYPE.NAME" in upper_formula:
        findings.append(
            f"MEDIUM {path}::{name}: uses RecordType.Name; prefer RecordType.DeveloperName"
        )

    if "ISPICKVAL(RECORDTYPE.DEVELOPERNAME" in upper_formula:
        findings.append(
            f"MEDIUM {path}::{name}: RecordType.DeveloperName is text, not a picklist"
        )

    if "ISPICKVAL(" in upper_formula and "ISBLANK(" not in upper_formula:
        findings.append(
            f"REVIEW {path}::{name}: picklist logic has no explicit blank guard"
        )

    # --- VR-PICK-01: ISBLANK()/ISNULL() applied directly to a picklist -------
    for field in find_direct_picklist_blank_calls(rule.formula):
        findings.append(
            f"HIGH {path}::{name}: VR-PICK-01 applies ISBLANK()/ISNULL() directly to "
            f"{field}, which this formula also passes to ISPICKVAL() as a picklist "
            f"field -- the deploy is rejected with \"Field {field} is a picklist "
            "field. Picklist fields are only supported in certain functions.\" "
            f"(proven live via sf project deploy start --dry-run, API 67.0, "
            f"2026-09-12). Fix: wrap it in TEXT() -- ISBLANK(TEXT({field})) / "
            f"ISNULL(TEXT({field}))"
        )

    # Compound fields are not allowed in validation rules as of API version 20.0
    for compound in COMPOUND_FIELDS:
        if compound in upper_formula:
            findings.append(
                f"HIGH {path}::{name}: references the compound field {compound}; "
                "validation rules can't use compound fields (API 20.0+). "
                "Validate the component fields instead"
            )
            break

    # --- bypass guard --------------------------------------------------------
    # Custom metadata type rules (API 40.0+) fire on the metadata record save,
    # not on business-record DML, so a data-load bypass is not expected there.
    is_custom_metadata_type = "__MDT" in path.name.upper()
    if rule.active and not is_custom_metadata_type and "$PERMISSION." not in upper_formula:
        findings.append(
            f"REVIEW {path}::{name}: no custom-permission bypass detected; confirm data-load and integration strategy"
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan ValidationRule metadata for formula, bypass and error-message "
            "issues. Reads both the metadata-format `.object` shape and the DX "
            "source-format `.validationRule-meta.xml` shape. When the scanned tree "
            "also carries objects/<Object>/fields/*.field-meta.xml (or embedded "
            "<fields>/<CustomField> elements) and/or customPermissions/*.customPermission-meta.xml, "
            "also resolves `__c` field tokens, `errorDisplayField`, and `$Permission` "
            "references against that inventory (VR-REF-01/VR-REF-02). Standard fields "
            "are never flagged for VR-REF-01/02, but VR-PICK-01 (ISBLANK()/ISNULL() "
            "applied directly to a field also passed to ISPICKVAL() in the same "
            "formula -- a picklist, which does not compile without TEXT()) needs no "
            "inventory and checks standard and custom fields alike. Run over the "
            "whole build/package tree, not one step's "
            "directory, or those references come back as an advisory INFO instead of "
            "a real answer. A --manifest-dir that does not exist is a HIGH finding "
            "(exit 1). One that exists but contains no validation-rule metadata is a "
            "REVIEW advisory (exit 0; --strict promotes it to exit 1) -- an empty "
            "scan is a scope note, not a defect."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to scan (equivalent to --manifest-dir for a directory)",
    )
    parser.add_argument(
        "--manifest-dir",
        action="append",
        default=[],
        metavar="DIR",
        help=(
            "Directory to scan recursively, e.g. force-app/main/default/objects. "
            "Repeatable."
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on any finding, including MEDIUM/LOW/REVIEW advisories.",
    )
    args = parser.parse_args()

    targets = [Path(value) for value in list(args.paths) + list(args.manifest_dir)]
    if not targets:
        parser.error("provide at least one path or --manifest-dir")

    missing = [str(target) for target in targets if not target.exists()]
    if missing:
        return emit_result(
            [f"HIGH path does not exist: {', '.join(missing)}"],
            f"Scanned 0 file(s); {len(missing)} supplied path(s) do not exist.",
        )

    files = iter_metadata_files(targets)
    if not files:
        # Every supplied path exists (the missing-path branch above already
        # returned) but none of it is validation-rule metadata -- e.g. a
        # freshly scaffolded object with no rules yet, or a build step that
        # has not authored one. That is a scope note, not a defect: it does
        # not fail the build on its own (REVIEW is not in BLOCKING_SEVERITIES),
        # but --strict may still promote it (REVIEW is strict-eligible, unlike
        # INFO -- see NEVER_STRICT_SEVERITIES).
        return emit_result(
            [
                "REVIEW no validation rule metadata files found in the "
                "supplied path(s) -- an empty manifest dir is not itself a "
                "defect; pass --strict to fail the build on this"
            ],
            "Scanned 0 validation rule metadata file(s); no files matched the provided paths.",
            strict=args.strict,
        )

    findings: list[str] = []
    rule_count = 0
    # fullName -> the files it was seen in. A rule name repeated across two
    # files is either a botched source-format split or two objects fighting
    # over one name in a manifest; both deploy unpredictably.
    seen_names: dict[str, list[str]] = defaultdict(list)

    fields_by_object, objects_with_inventory = collect_field_inventory(targets)
    permission_names, permission_dir_found = collect_custom_permission_names(targets)
    inventory_absent_rule_count = 0
    inventory_absent_objects: set[str] = set()

    for path in files:
        try:
            rules = collect_rules(path)
        except ET.ParseError as exc:
            findings.append(f"CRITICAL {path}: file is not well-formed XML ({exc})")
            continue
        object_name = object_from_objects_path(path)
        for rule in rules:
            rule_count += 1
            seen_names[rule.full_name].append(str(path))
            findings.extend(audit_rule(path, rule))
            ref_findings, inventory_absent = audit_rule_references(
                path, rule, object_name, fields_by_object, objects_with_inventory,
                permission_names, permission_dir_found,
            )
            findings.extend(ref_findings)
            if inventory_absent:
                inventory_absent_rule_count += 1
                inventory_absent_objects.add(object_name or f"<unknown object: {path}>")

    if inventory_absent_rule_count:
        findings.append(
            f"INFO field references: {inventory_absent_rule_count} validation rule(s) "
            f"on {len(inventory_absent_objects)} object(s) "
            f"({', '.join(sorted(inventory_absent_objects))}) have no field inventory "
            "in this scope - field inventory absent at this scope, references "
            "unresolvable. Re-run over the tree that also carries "
            "objects/<Object>/fields/ (and customPermissions/ for $Permission "
            "tokens) to make the check real"
        )

    for full_name, sources in sorted(seen_names.items()):
        if len(sources) > 1:
            findings.append(
                f"HIGH {full_name}: duplicate rule fullName in {len(sources)} files "
                f"({', '.join(sorted(sources))})"
            )

    summary = (
        f"Scanned {rule_count} validation rule(s) across {len(files)} file(s); "
        f"{len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
