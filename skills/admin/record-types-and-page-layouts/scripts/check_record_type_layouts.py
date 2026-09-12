#!/usr/bin/env python3
"""Audit record type and page layout metadata for admin complexity and deploy risks.

Reads MDAPI-style `CustomObject`, `Layout`, `Profile`, and `PermissionSet` files,
plus DX-decomposed `*.recordType-meta.xml` / `*.businessProcess-meta.xml`, and
reports findings as JSON on stdout.

Checks (each grounded in the Metadata API Developer Guide, v62):

1. A `layoutAssignments` entry (or a `recordTypeVisibilities` entry) that names a
   record type whose `active` is `false`. The guide states neither Profile nor
   PermissionSet retrieves or deploys record type visibilities for inactive record
   types, so such an assignment is either stale or about to be silently dropped.
2. `businessProcess` present or absent against the guide's four-object rule:
   required on Lead, Opportunity, Solution, and Case record types; not allowed
   otherwise. Both directions are deploy failures.
3. A record type with no `recordTypeVisibilities` entry in any scanned Profile or
   PermissionSet -- nobody can select it.
4. A layout with zero `behavior` = `Required` layout items (INFO only; a layout may
   legitimately require nothing, but it is worth surfacing when a design claimed to
   enforce a field there).
5. More than 8 record types on one object (MEDIUM), more than 13 (HIGH).
6. A `layoutAssignments` entry naming a layout file that is not in the scanned tree.
7. Profile / PermissionSet references that cannot be resolved at all because the
   scanned tree holds no record types or no layouts. At a single build step's
   scope both usually live in another step, so the cross-reference in checks 1,
   3 and 6 is never actually made. That is reported as an INFO -- "N reference(s)
   unresolvable at this scope" -- so a reader can tell the difference between
   "checked and clean" and "nothing to check against". When record types ARE
   present in the scanned tree, both halves of the record-type cross-reference
   are made and a dangling one is reported LOW: a `recordTypeVisibilities`
   entry (Profile or PermissionSet) naming a record type absent from the tree,
   and a `layoutAssignments` entry's own `recordType` child doing the same --
   the latter is a distinct XML location from the `recordTypeVisibilities`
   entries and was previously left unchecked (F-19, 2026-09-11) even though it
   was already counted in the "unresolvable at this scope" INFO tally.

Layout-required standard fields (RL-REQ-01 .. RL-REQ-03). Some standard fields are
required *on the layout itself*: a Layout that omits one fails to deploy, and a
field the platform requires must also carry behavior=Required. The Metadata API
guide does not document this -- LayoutItem.behavior is presented purely as an
author's choice (api_meta L82844-82851) and the phrase "required layout field"
appears nowhere in the guide -- so the rule below is seeded from a deploy, not
from documentation:

  RL-REQ-01  ERROR     A `Case` layout (object taken from the file name, e.g.
                       `Case-Case Support Layout.layout-meta.xml`) with no
                       layoutItems/field entry for ContactId, Description, or
                       SuppliedEmail. Deploy message:
                       "Layout must contain an item for required layout field: <F>".
  RL-REQ-02  ERROR     A `Case` layout whose Status item is missing, or whose
                       behavior is anything other than Required. Deploy message:
                       "Field:Status must be Required".
  RL-REQ-03  ADVISORY  A layout for any *other* standard object whose items carry
                       none of the usual name/subject-like fields. Advisory, not
                       an error, because the per-object required set is UNVERIFIED
                       (2026-09-09): only the Case set has been exercised against
                       an org, and this rule is a heuristic stand-in, not a list.

The Case set is verified by `sf project deploy start --dry-run` against a Summer '26
developer org on 2026-09-05 -- see
examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md (runs 1-5) and the two
validated layouts under examples/builds/case-onboarding/reports/mock-deploy-fixes/.

Severities and exit codes:
  CRITICAL / ERROR / HIGH   deploy-breaking; exit 1
  MEDIUM / LOW              review; printed, exit 0
  INFO / ADVISORY           scope, discovery, and unverified-heuristic notes;
                            printed, exit 0

  0 -- no CRITICAL/HIGH finding (and no finding at all when --strict is passed)
  1 -- at least one CRITICAL/HIGH, or any finding under --strict

Usage:
    check_record_type_layouts.py --manifest-dir force-app/main/default
    check_record_type_layouts.py --manifest-dir force-app/main/default --strict
    check_record_type_layouts.py path/to/objects path/to/layouts
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


METADATA_SUFFIXES = (
    ".object-meta.xml",
    ".object",
    ".profile-meta.xml",
    ".profile",
    ".permissionset-meta.xml",
    ".permissionset",
    ".layout-meta.xml",
    ".layout",
    ".recordType-meta.xml",
    ".businessProcess-meta.xml",
)
SEVERITY_WEIGHTS = {
    "CRITICAL": 20,
    "ERROR": 20,
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 1,
    "INFO": 0,
    "ADVISORY": 0,
    "REVIEW": 0,
}

# Metadata API Developer Guide, RecordType: businessProcess "is required in record
# types for lead, opportunity, solution, and case, and not allowed otherwise".
BUSINESS_PROCESS_OBJECTS = {"lead", "opportunity", "solution", "case"}

RECORD_TYPE_COUNT_WARN = 8
RECORD_TYPE_COUNT_HIGH = 13

# RL-REQ-01 / RL-REQ-02. Verified by `sf project deploy start --dry-run` against a
# Summer '26 developer org on 2026-09-05
# (examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md, runs 1-5). Not stated
# in the Metadata API guide; do not extend this to another object without a dry run.
CASE_LAYOUT_REQUIRED_ITEMS = ("ContactId", "Description", "SuppliedEmail")
CASE_LAYOUT_REQUIRED_BEHAVIOR = "Required"
CASE_LAYOUT_REQUIRED_BEHAVIOR_FIELD = "Status"

# RL-REQ-03 heuristic only. The per-object required set is UNVERIFIED (2026-09-09),
# so this is a "does the layout carry any identifying field at all" smoke test
# rather than a claim about what a given object requires.
NAME_LIKE_FIELDS = ("Name", "Subject", "LastName", "Title", "CaseNumber")


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def find_child(element: ET.Element, child_name: str) -> ET.Element | None:
    """Return the first direct child with this local name, or None.

    Deliberately explicit: a leaf ``Element`` is falsy, so ``a.find(x) or a.find(y)``
    silently discards a real match whose element has no children.
    """
    for child in element:
        if local_name(child.tag) == child_name:
            return child
    return None


def child_text(element: ET.Element, child_name: str) -> str:
    child = find_child(element, child_name)
    if child is None:
        return ""
    return (child.text or "").strip()


def children(element: ET.Element, child_name: str) -> list[ET.Element]:
    return [child for child in element if local_name(child.tag) == child_name]


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


def object_name_for(path: Path) -> str:
    """Derive the sObject name from a metadata file path."""
    name = path.name
    if name.endswith(".object-meta.xml"):
        return name[: -len(".object-meta.xml")]
    if name.endswith(".object"):
        return name[: -len(".object")]
    # DX decomposed: objects/<Object>/recordTypes/<Name>.recordType-meta.xml
    for parent in path.parents:
        if parent.parent is not None and parent.parent.name == "objects":
            return parent.name
    return path.stem


def layout_developer_name(path: Path) -> str:
    name = path.name
    for suffix in (".layout-meta.xml", ".layout"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def layout_object_name(developer_name: str) -> str:
    """Object the layout belongs to, taken from the file-name form.

    A Layout member is `<Object>-<Layout Name>` (Metadata API guide, Layout: the
    Idea example uses `Idea-Idea Layout`), so the object is everything before the
    first hyphen. Returns "" when the name carries no hyphen and the object cannot
    be established -- callers must not guess in that case.
    """
    head, sep, _tail = developer_name.partition("-")
    if not sep:
        return ""
    return head.strip()


class Model:
    """Everything the checks need, collected in one pass."""

    def __init__(self) -> None:
        # "Case.Customer_Support" -> {"active": bool, "business_process": str, "path": Path}
        self.record_types: dict[str, dict] = {}
        # object name -> count of record types seen
        self.record_type_counts: dict[str, int] = {}
        # layout developer name ("Case-Case Customer Support") -> path
        self.layouts: dict[str, Path] = {}
        # layout developer name -> number of Required layout items
        self.layout_required_counts: dict[str, int] = {}
        # layout developer name -> {field API name: that item's behavior text ("" if unset)}
        self.layout_item_behaviors: dict[str, dict[str, str]] = {}
        # record type full names referenced by any recordTypeVisibilities entry
        self.visible_record_types: set[str] = set()
        # (source path, layout name, record type full name or "")
        self.layout_assignments: list[tuple[Path, str, str]] = []
        # (source path, record type full name, root type)
        self.visibility_entries: list[tuple[Path, str, str]] = []


def collect_record_type(model: Model, obj: str, node: ET.Element, path: Path) -> None:
    full_name = child_text(node, "fullName")
    if not full_name:
        return
    qualified = full_name if "." in full_name else f"{obj}.{full_name}"
    model.record_types[qualified] = {
        "active": child_text(node, "active").lower() != "false",
        "business_process": child_text(node, "businessProcess"),
        "path": path,
        "object": obj,
    }
    model.record_type_counts[obj] = model.record_type_counts.get(obj, 0) + 1


def collect(model: Model, path: Path, root: ET.Element) -> None:
    root_type = local_name(root.tag)

    if root_type == "CustomObject":
        obj = object_name_for(path)
        for node in children(root, "recordTypes"):
            collect_record_type(model, obj, node, path)

    elif root_type == "RecordType":
        # DX decomposed file; fullName is usually omitted and implied by the file name
        obj = object_name_for(path)
        node = root
        full_name = child_text(node, "fullName") or path.name.split(".")[0]
        qualified = full_name if "." in full_name else f"{obj}.{full_name}"
        model.record_types[qualified] = {
            "active": child_text(node, "active").lower() != "false",
            "business_process": child_text(node, "businessProcess"),
            "path": path,
            "object": obj,
        }
        model.record_type_counts[obj] = model.record_type_counts.get(obj, 0) + 1

    elif root_type == "Layout":
        dev_name = layout_developer_name(path)
        model.layouts[dev_name] = path
        required = 0
        behaviors: dict[str, str] = {}
        for section in children(root, "layoutSections"):
            for column in children(section, "layoutColumns"):
                for item in children(column, "layoutItems"):
                    behavior = child_text(item, "behavior")
                    if behavior == "Required":
                        required += 1
                    field = child_text(item, "field")
                    if field:
                        # first entry wins; a field placed twice keeps the stricter
                        # reading only if the duplicate is itself Required
                        if field not in behaviors or behavior == "Required":
                            behaviors[field] = behavior
        model.layout_required_counts[dev_name] = required
        model.layout_item_behaviors[dev_name] = behaviors

    elif root_type in {"Profile", "PermissionSet"}:
        for node in children(root, "recordTypeVisibilities"):
            rt = child_text(node, "recordType")
            if rt:
                model.visibility_entries.append((path, rt, root_type))
                if child_text(node, "visible").lower() != "false":
                    model.visible_record_types.add(rt)
        for node in children(root, "layoutAssignments"):
            layout = child_text(node, "layout")
            rt = child_text(node, "recordType")
            if layout:
                model.layout_assignments.append((path, layout, rt))


def run_checks(model: Model) -> list[str]:
    findings: list[str] = []

    # 1. assignment or visibility pointing at an inactive record type
    for path, layout, rt in model.layout_assignments:
        if rt and rt in model.record_types and not model.record_types[rt]["active"]:
            findings.append(
                f"HIGH {path}: layoutAssignment for '{layout}' names inactive record type "
                f"'{rt}' - inactive record types are not retrieved or deployed on Profile"
            )
    for path, rt, root_type in model.visibility_entries:
        if rt in model.record_types and not model.record_types[rt]["active"]:
            findings.append(
                f"MEDIUM {path}: {root_type} recordTypeVisibilities names inactive record type "
                f"'{rt}' - this entry will not deploy"
            )

    # 2. businessProcess four-object rule
    for qualified, info in sorted(model.record_types.items()):
        obj = info["object"].lower()
        has_bp = bool(info["business_process"])
        if obj in BUSINESS_PROCESS_OBJECTS and not has_bp:
            findings.append(
                f"HIGH {info['path']}: record type '{qualified}' has no businessProcess - "
                f"required on lead, opportunity, solution, and case"
            )
        elif obj not in BUSINESS_PROCESS_OBJECTS and has_bp:
            findings.append(
                f"HIGH {info['path']}: record type '{qualified}' sets businessProcess "
                f"'{info['business_process']}' - not allowed on this object"
            )

    # 3. record type nobody can select
    if model.visibility_entries:
        for qualified, info in sorted(model.record_types.items()):
            if info["active"] and qualified not in model.visible_record_types:
                findings.append(
                    f"MEDIUM {info['path']}: record type '{qualified}' is active but no scanned "
                    f"Profile or PermissionSet makes it visible"
                )

    # 4. layout with zero required fields (informational)
    for dev_name, count in sorted(model.layout_required_counts.items()):
        if count == 0:
            findings.append(
                f"INFO {model.layouts[dev_name]}: layout '{dev_name}' marks no field "
                f"behavior=Required"
            )

    # RL-REQ-01 / RL-REQ-02 / RL-REQ-03: layout-required standard fields.
    for dev_name in sorted(model.layouts):
        path = model.layouts[dev_name]
        obj = layout_object_name(dev_name)
        if not obj:
            continue
        behaviors = model.layout_item_behaviors.get(dev_name, {})

        if obj == "Case":
            missing = [f for f in CASE_LAYOUT_REQUIRED_ITEMS if f not in behaviors]
            if missing:
                findings.append(
                    f"ERROR {path}: RL-REQ-01 Case layout '{dev_name}' has no layoutItems "
                    f"entry for {', '.join(missing)} - the deploy fails with 'Layout must "
                    f"contain an item for required layout field: <field>', one field per run"
                )
            status_behavior = behaviors.get(CASE_LAYOUT_REQUIRED_BEHAVIOR_FIELD)
            if status_behavior is None:
                findings.append(
                    f"ERROR {path}: RL-REQ-02 Case layout '{dev_name}' has no "
                    f"{CASE_LAYOUT_REQUIRED_BEHAVIOR_FIELD} item - the platform requires one "
                    f"with behavior={CASE_LAYOUT_REQUIRED_BEHAVIOR}"
                )
            elif status_behavior != CASE_LAYOUT_REQUIRED_BEHAVIOR:
                findings.append(
                    f"ERROR {path}: RL-REQ-02 Case layout '{dev_name}' sets "
                    f"{CASE_LAYOUT_REQUIRED_BEHAVIOR_FIELD} behavior="
                    f"'{status_behavior or 'unset'}' - the deploy fails with "
                    f"'Field:{CASE_LAYOUT_REQUIRED_BEHAVIOR_FIELD} must be "
                    f"{CASE_LAYOUT_REQUIRED_BEHAVIOR}'. This one is not the layout-vs-field "
                    f"enforcement choice; it is a deploy precondition"
                )
        elif not obj.endswith("__c"):
            if not any(field in behaviors for field in NAME_LIKE_FIELDS):
                findings.append(
                    f"ADVISORY {path}: RL-REQ-03 standard-object layout '{dev_name}' carries "
                    f"none of {', '.join(NAME_LIKE_FIELDS)} - some standard fields are required "
                    f"on the layout itself and the deploy, not this checker, is the authority. "
                    f"Advisory only: the required set is verified for Case alone, so the set for "
                    f"'{obj}' is UNVERIFIED (2026-09-09). Discover it with "
                    f"'sf project deploy start --dry-run'"
                )

    # 5. record type count per object
    for obj, count in sorted(model.record_type_counts.items()):
        if count > RECORD_TYPE_COUNT_HIGH:
            findings.append(f"HIGH {obj}: object has {count} record types")
        elif count > RECORD_TYPE_COUNT_WARN:
            findings.append(f"MEDIUM {obj}: object has {count} record types")

    # 6. layout assignment pointing at a layout not in the tree
    if model.layouts:
        for path, layout, _rt in model.layout_assignments:
            if layout not in model.layouts:
                findings.append(
                    f"LOW {path}: layoutAssignment names layout '{layout}' which is not in the "
                    f"scanned tree - confirm it exists in the target org"
                )

    # 7. references that cannot be resolved at this scope, and dangling
    #    references that can be. Never silent: a reader must be able to tell
    #    "cross-checked and clean" from "there was nothing to cross-check".
    referenced_record_types = [rt for _path, rt, _root in model.visibility_entries]
    referenced_record_types += [rt for _path, _layout, rt in model.layout_assignments if rt]
    referenced_layouts = [layout for _path, layout, _rt in model.layout_assignments]

    if referenced_record_types and not model.record_types:
        findings.append(
            f"INFO record types: {len(referenced_record_types)} Profile/PermissionSet "
            f"record-type reference(s) unresolvable at this scope - the scanned tree holds "
            f"no record type metadata, so no reference was cross-checked. Re-run over the "
            f"tree that also carries objects/<Object>/recordTypes/ to make the check real"
        )
    elif model.record_types:
        for path, rt, root_type in model.visibility_entries:
            if rt not in model.record_types:
                findings.append(
                    f"LOW {path}: {root_type} recordTypeVisibilities names record type "
                    f"'{rt}' which is not in the scanned tree - confirm it exists in the "
                    f"target org"
                )
        for path, layout, rt in model.layout_assignments:
            if rt and rt not in model.record_types:
                findings.append(
                    f"LOW {path}: layoutAssignment for '{layout}' names record type "
                    f"'{rt}' which is not in the scanned tree - confirm it exists in the "
                    f"target org"
                )

    if referenced_layouts and not model.layouts:
        findings.append(
            f"INFO layouts: {len(referenced_layouts)} Profile layoutAssignment reference(s) "
            f"unresolvable at this scope - the scanned tree holds no layout metadata, so no "
            f"assignment was cross-checked. Re-run over the tree that also carries layouts/"
        )

    return findings


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


BLOCKING_SEVERITIES = {"CRITICAL", "ERROR", "HIGH"}


def emit_result(findings: list[str], summary: str, strict: bool = False) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))
    blocking = [item for item in normalized if item["severity"] in BLOCKING_SEVERITIES]
    if blocking:
        print(f"ERROR: {len(blocking)} deploy-breaking finding(s) detected", file=sys.stderr)
    if len(normalized) > len(blocking):
        print(
            f"WARN: {len(normalized) - len(blocking)} review/info finding(s) detected",
            file=sys.stderr,
        )
    if blocking:
        return 1
    if strict and normalized:
        print("--strict: failing on review/info findings.", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan object, record type, layout, profile, and permission set metadata "
        "for record type and page layout risks."
    )
    parser.add_argument(
        "--manifest-dir",
        action="append",
        default=[],
        help="Directory to scan recursively (for example force-app/main/default). Repeatable.",
    )
    parser.add_argument("paths", nargs="*", help="Additional files or directories to scan")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on MEDIUM/LOW/INFO/ADVISORY findings as well as CRITICAL/ERROR/HIGH.",
    )
    args = parser.parse_args()

    targets = [Path(value) for value in list(args.manifest_dir) + list(args.paths)]
    if not targets:
        parser.error("provide --manifest-dir or one or more paths")

    files = iter_metadata_files(targets)
    if not files:
        return emit_result(
            ["HIGH no object, record type, layout, profile, or permission set metadata found"],
            "Scanned 0 record-type/layout metadata file(s); no files matched the provided paths.",
            args.strict,
        )

    model = Model()
    findings: list[str] = []
    for path in files:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            findings.append(f"HIGH {path}: file is not well-formed XML ({exc})")
            continue
        collect(model, path, root)

    findings.extend(run_checks(model))

    summary = (
        f"Scanned {len(files)} metadata file(s): {len(model.record_types)} record type(s), "
        f"{len(model.layouts)} layout(s); {len(findings)} finding(s) detected."
    )
    return emit_result(findings, summary, args.strict)


if __name__ == "__main__":
    sys.exit(main())
