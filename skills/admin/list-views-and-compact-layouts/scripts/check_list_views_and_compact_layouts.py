#!/usr/bin/env python3
"""Static review of list-view, compact-layout, and search-layout metadata.

Reads a Salesforce DX source tree (``force-app/main/default`` or any directory
above ``objects/``) and reports the browse-and-scan problems that are cheap to
find in XML and expensive to find in production.

Checks implemented
------------------
1.  Broad public working surface: ``filterScope`` = ``Everything`` with no
    ``filters`` and no ``booleanFilter``.
2.  Public list view (no ``sharedTo`` element at all) carrying more columns
    than a triage surface can use.  Metadata API Developer Guide, ``SharedTo``:
    the element "is included in the metadata for shared and private list views"
    and "isn't in the metadata for public list views" -- absence means public.
3.  ``filterScope`` / ``queue`` mismatch, and ``filterScope`` values outside the
    guide's ``FilterScope`` enumeration.
4.  ``booleanFilter`` referring to a filter line number that does not exist.
5.  Compact layout that is too long, or that names a field whose type the
    guide lists as unsupported (text area, long text area, rich text area,
    multi-select picklist).  Field types are resolved from
    ``objects/<Object>/fields/*.field-meta.xml`` when those files are present;
    otherwise only the count is checked.
6.  Compact layout that no ``compactLayoutAssignment`` references, at the
    object level or on any record type.

Manifest member form (CL-MEM-01 .. CL-MEM-02)
---------------------------------------------
Everything that lives inside an object takes an object-qualified package.xml
member.  The Metadata API Developer Guide (v62 PDF) states it for ``ListView``
-- "Note the objectName.listViewUniqueName syntax in the <members> field"
(api_meta L2318), sample ``<members>Account.AccountTeam</members>``
(api_meta L2305) -- and for ``CustomField`` (api_meta L2287).  It states it
nowhere for ``CompactLayout``: that topic gives only the containment rule,
"Compact layouts are defined as part of the custom object, standard object, or
external object definition" (api_meta L43086-43088), and wildcard support
(api_meta L43199-43201).  The object-qualified form for ``CompactLayout`` is
therefore seeded from a deploy, not from documentation:

  CL-MEM-01  ERROR   A ``<members>`` value under ``<name>CompactLayout</name>``
                     or ``<name>ListView</name>`` that contains no ``.`` and is
                     not ``*``, while a matching
                     ``objects/<Object>/compactLayouts/<name>`` (or
                     ``listViews/<name>``) file exists in the scanned tree.
                     Deploy message: "An object 'Case_Intake' of type
                     CompactLayout was named in package.xml, but was not found
                     in zipped directory".  A bare member whose file is *not* in
                     the tree is left alone -- it may be declared for metadata
                     that lives in another step.
  CL-MEM-02  WARN    A compact layout file that no package.xml in the tree
                     declares.  WARN, not ERROR: the manifest may legitimately
                     live outside the scanned scope.  Skipped entirely when the
                     tree holds no package.xml at all (there is then nothing to
                     be missing from), and satisfied by ``<members>*</members>``,
                     which ``CompactLayout`` supports.

CL-MEM-01 is verified by ``sf project deploy start --manifest ... --dry-run``
against a Summer '26 developer org on 2026-09-09 -- see
examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md, "Mock deploy #3".
The identical tree deployed with ``--source-dir`` validated 12/12 and the CLI
derived the member as ``CompactLayout Case.Case_Intake``, which is why
``--source-dir`` runs never surface this defect: that flag builds the member
list from the files instead of reading it.  UNVERIFIED (2026-09-11): only the
``CompactLayout`` half was exercised against an org; ``ListView`` is covered on
the documented member form alone, and no error text is claimed for it.

Also keeps the original sprawl heuristics: too many list views on one object,
and an object with several list views but no compact layout at all.

Severities and exit codes:
  ERROR                 deploy-breaking; exit 1
  WARN / INFO           review; printed, exit 0 (exit 1 under ``--strict``,
                        which promotes WARN and INFO to failures)
  missing --manifest-dir  single ERROR line, exit 1
  nothing to check        single WARN line, exit 0

stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

# FilterScope enumeration, Metadata API Developer Guide (v62), ListView.
VALID_FILTER_SCOPES = {
    "everything",
    "mine",
    "mineandmygroups",
    "assignedtome",
    "queue",
    "delegated",
    "myterritory",
    "myteamterritory",
    "team",
    "salesteam",
    "scopingrule",
}

# CompactLayout, Metadata API Developer Guide (v62): "Compact layouts support
# all field types except: text area, long text area, rich text area,
# multi-select picklist."  CustomField `type` enumeration names for those.
UNSUPPORTED_COMPACT_FIELD_TYPES = {
    "textarea": "text area",
    "longtextarea": "long text area",
    "html": "rich text area",
    "multiselectpicklist": "multi-select picklist",
}

MAX_TRIAGE_COLUMNS = 10
MAX_COMPACT_FIELDS = 10
MAX_LIST_VIEWS_PER_OBJECT = 15

_FILTER_INDEX_RE = re.compile(r"\d+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check list views, compact layouts, and their assignments for "
            "usability and deployability problems."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on WARN and INFO findings as well as ERROR.",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def child_elements(root: ET.Element, name: str) -> list[ET.Element]:
    """Every descendant (and the root itself) whose local tag name matches."""
    return [element for element in root.iter() if local_name(element.tag) == name]


def child_texts(root: ET.Element, name: str) -> list[str]:
    return [(element.text or "").strip() for element in child_elements(root, name)]


def first_text(root: ET.Element, name: str) -> str:
    """Text of the first matching descendant, or '' when there is none.

    Deliberately not written as ``root.find(a) or root.find(b)``: an
    ElementTree element with no children is falsy, so ``or`` would discard a
    perfectly good match.  Every test here is an explicit ``is not None``.
    """
    for element in root.iter():
        if local_name(element.tag) == name:
            return (element.text or "").strip()
    return ""


def has_element(root: ET.Element, name: str) -> bool:
    for element in root.iter():
        if local_name(element.tag) == name:
            return True
    return False


def object_name_from_child_metadata(path: Path) -> str:
    """``objects/Case/listViews/X.listView-meta.xml`` -> ``Case``."""
    parents = path.parents
    if len(parents) >= 2:
        return parents[1].name
    return "unknown-object"


def layout_api_name(path: Path, root: ET.Element | None) -> str:
    if root is not None:
        full_name = first_text(root, "fullName")
        if full_name:
            return full_name
    return path.name.split(".")[0]


def load_field_types(object_dir: Path) -> dict[str, str]:
    """Map lowercase field API name -> lowercase CustomField ``type``."""
    field_types: dict[str, str] = {}
    fields_dir = object_dir / "fields"
    if not fields_dir.is_dir():
        return field_types
    for field_path in sorted(fields_dir.glob("*.field-meta.xml")):
        root = parse_xml(field_path)
        if root is None:
            continue
        api_name = first_text(root, "fullName") or field_path.name.split(".")[0]
        field_type = first_text(root, "type")
        if api_name and field_type:
            field_types[api_name.lower()] = field_type.lower()
    return field_types


def check_list_view(path: Path, root: ET.Element) -> list[str]:
    issues: list[str] = []

    columns = child_texts(root, "columns")
    filter_blocks = child_elements(root, "filters")
    boolean_filter = first_text(root, "booleanFilter")
    filter_scope = first_text(root, "filterScope")
    queue = first_text(root, "queue")
    is_public = not has_element(root, "sharedTo")

    scope_key = filter_scope.lower()

    # 3a. filterScope must be one of the documented enumeration values.
    if filter_scope and scope_key not in VALID_FILTER_SCOPES:
        issues.append(
            f"ERROR {path}: filterScope '{filter_scope}' is not in the documented "
            "FilterScope enumeration (Everything, Mine, MineAndMyGroups, AssignedToMe, "
            "Queue, Delegated, MyTerritory, MyTeamTerritory, Team, SalesTeam, ScopingRule)."
        )
    if not filter_scope:
        issues.append(
            f"ERROR {path}: filterScope is missing; the Metadata API guide marks it required on ListView."
        )

    # 1. Broad, unfiltered, all-records view.
    if scope_key == "everything" and not filter_blocks and not boolean_filter:
        visibility = "public" if is_public else "shared"
        issues.append(
            f"WARN {path}: {visibility} list view scoped to Everything with no filters; "
            "this is an all-records browse surface. Narrow it or restrict it to an admin audience."
        )

    # 2. Public view with a dense column set.
    if is_public and len(columns) > MAX_TRIAGE_COLUMNS:
        issues.append(
            f"INFO {path}: public list view (no sharedTo element) exposes {len(columns)} columns; "
            f"a triage surface rarely needs more than {MAX_TRIAGE_COLUMNS}."
        )
    elif len(columns) > MAX_TRIAGE_COLUMNS:
        issues.append(
            f"INFO {path}: list view exposes {len(columns)} columns; review whether the triage surface is too dense."
        )

    # 3b. Queue scope and queue element must agree.
    if scope_key == "queue" and not queue:
        issues.append(
            f"ERROR {path}: filterScope is Queue but no <queue> element names the queue developer name."
        )
    if queue and scope_key != "queue":
        issues.append(
            f"WARN {path}: <queue>{queue}</queue> is set but filterScope is '{filter_scope}'; "
            "the queue is ignored unless the scope is Queue."
        )

    # 4. booleanFilter indices must resolve to real filter line items.
    if boolean_filter:
        if not filter_blocks:
            issues.append(
                f"ERROR {path}: booleanFilter '{boolean_filter}' is set but the view has no <filters> line items."
            )
        else:
            referenced = {int(n) for n in _FILTER_INDEX_RE.findall(boolean_filter)}
            dangling = sorted(n for n in referenced if n < 1 or n > len(filter_blocks))
            if dangling:
                issues.append(
                    f"ERROR {path}: booleanFilter '{boolean_filter}' references filter line "
                    f"{dangling} but the view defines {len(filter_blocks)}; "
                    "booleanFilter indexes <filters> blocks by document order."
                )
            unreferenced = sorted(
                n for n in range(1, len(filter_blocks) + 1) if n not in referenced
            )
            if unreferenced:
                issues.append(
                    f"WARN {path}: filter line {unreferenced} is never referenced by "
                    f"booleanFilter '{boolean_filter}'; the clause is inert."
                )

    return issues


def check_compact_layout(path: Path, root: ET.Element, field_types: dict[str, str]) -> list[str]:
    issues: list[str] = []
    fields = [name for name in child_texts(root, "fields") if name]

    if not fields:
        issues.append(f"WARN {path}: compact layout defines no fields.")

    if len(fields) > MAX_COMPACT_FIELDS:
        issues.append(
            f"WARN {path}: compact layout exposes {len(fields)} fields; the highlights panel and "
            f"mobile card truncate from the end, so keep it near the top {MAX_COMPACT_FIELDS}."
        )

    if field_types:
        for field_name in fields:
            field_type = field_types.get(field_name.lower())
            if field_type in UNSUPPORTED_COMPACT_FIELD_TYPES:
                issues.append(
                    f"ERROR {path}: field '{field_name}' is a "
                    f"{UNSUPPORTED_COMPACT_FIELD_TYPES[field_type]}; compact layouts support all "
                    "field types except text area, long text area, rich text area, and "
                    "multi-select picklist. This deploy will fail."
                )
    else:
        issues.append(
            f"INFO {path}: no objects/<Object>/fields/*.field-meta.xml files were found, so the "
            "unsupported-field-type check (text area, long text area, rich text area, "
            "multi-select picklist) was skipped; only the field count was checked."
        )

    return issues


# package.xml <name> -> (source sub-directory, human label).  Both of these types
# live inside the object, so an enumerated member is <Object>.<Name>.
NESTED_MEMBER_TYPES = {
    "CompactLayout": "compactLayouts",
    "ListView": "listViews",
}

# What each half of CL-MEM-01 actually rests on.  Only the CompactLayout case was
# run against an org; the ListView case rests on the documented member form.
MEMBER_EVIDENCE = {
    "CompactLayout": (
        "A manifest deploy fails with \"An object '{member}' of type CompactLayout was named "
        "in package.xml, but was not found in zipped directory\" -- verified by "
        "`sf project deploy start --manifest ... --dry-run` against a Summer '26 developer org "
        "on 2026-09-09 (examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md, "
        "Mock deploy #3)."
    ),
    "ListView": (
        "The guide documents the member form as objectName.listViewUniqueName "
        "(api_meta L2318, sample <members>Account.AccountTeam</members> at L2305). "
        "UNVERIFIED (2026-09-11): the bare-member ListView case was not exercised against an "
        "org, so no deploy error text is claimed for it."
    ),
}


def types_blocks(root: ET.Element) -> list[tuple[str, list[str]]]:
    """``[(type name, [member, ...]), ...]`` from a parsed package.xml root."""
    blocks: list[tuple[str, list[str]]] = []
    for types_element in root.iter():
        if local_name(types_element.tag) != "types":
            continue
        type_name = ""
        members: list[str] = []
        for child in types_element:
            tag = local_name(child.tag)
            text = (child.text or "").strip()
            if tag == "name" and not type_name:
                type_name = text
            elif tag == "members" and text:
                members.append(text)
        if type_name:
            blocks.append((type_name, members))
    return blocks


def check_manifest_members(
    manifest_dir: Path,
    compact_layouts: dict[str, dict[str, Path]],
    list_views: dict[str, dict[str, Path]],
) -> list[str]:
    """CL-MEM-01 / CL-MEM-02: package.xml members for object-nested types.

    ``compact_layouts`` / ``list_views`` map object name -> {api name: file}.
    """
    issues: list[str] = []
    index = {"CompactLayout": compact_layouts, "ListView": list_views}

    package_paths = sorted(manifest_dir.rglob("package.xml"))
    if not package_paths:
        if compact_layouts:
            issues.append(
                f"INFO {manifest_dir}: no package.xml found in the tree, so the manifest "
                "member-form checks (CL-MEM-01, CL-MEM-02) were skipped. Run the checker "
                "over the directory that holds the manifest to exercise them."
            )
        return issues

    # (type, object, layout/view name) lowercased, for anything a manifest declares.
    declared: set[tuple[str, str, str]] = set()
    wildcarded: set[str] = set()

    for package_path in package_paths:
        root = parse_xml(package_path)
        if root is None:
            issues.append(f"ERROR {package_path}: unable to parse package.xml.")
            continue
        for type_name, members in types_blocks(root):
            if type_name not in NESTED_MEMBER_TYPES:
                continue
            by_object = index[type_name]
            for member in members:
                if member == "*":
                    wildcarded.add(type_name)
                    continue
                if "." in member:
                    object_name, _, api_name = member.partition(".")
                    declared.add((type_name, object_name.lower(), api_name.lower()))
                    continue
                # Bare member. Only a problem when the file it names is really here.
                owners = [
                    object_name
                    for object_name, entries in sorted(by_object.items())
                    if member.lower() in {name.lower() for name in entries}
                ]
                if not owners:
                    continue
                for object_name in owners:
                    declared.add((type_name, object_name.lower(), member.lower()))
                suggestion = " or ".join(f"{owner}.{member}" for owner in owners)
                issues.append(
                    f"ERROR CL-MEM-01 {package_path}: <members>{member}</members> under "
                    f"<name>{type_name}</name> is not object-qualified, but "
                    f"objects/{owners[0]}/{NESTED_MEMBER_TYPES[type_name]}/{member} is in this "
                    f"tree. Use <members>{suggestion}</members>. "
                    f"{MEMBER_EVIDENCE[type_name].format(member=member)} A --source-dir deploy "
                    "derives the member from the file instead of reading it, so it passes and "
                    "never catches this."
                )

    # CL-MEM-02: a compact layout nothing in the tree declares.
    if "CompactLayout" not in wildcarded:
        for object_name, layouts in sorted(compact_layouts.items()):
            for api_name, layout_path in sorted(layouts.items()):
                key = ("CompactLayout", object_name.lower(), api_name.lower())
                if key in declared:
                    continue
                issues.append(
                    f"WARN CL-MEM-02 {layout_path}: no package.xml in this tree declares "
                    f"<members>{object_name}.{api_name}</members> under "
                    "<name>CompactLayout</name>. A manifest deploy will not ship it. WARN, not "
                    "ERROR: the manifest that declares it may live outside the scanned scope."
                )

    return issues


def check_list_views_and_compact_layouts(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"ERROR Manifest directory not found: {manifest_dir}"]

    object_list_views: dict[str, list[Path]] = defaultdict(list)
    object_list_view_names: dict[str, dict[str, Path]] = defaultdict(dict)
    object_compact_layouts: dict[str, dict[str, Path]] = defaultdict(dict)
    object_assignments: dict[str, set[str]] = defaultdict(set)
    field_type_cache: dict[Path, dict[str, str]] = {}

    for list_view_path in sorted(manifest_dir.rglob("*.listView-meta.xml")):
        object_name = object_name_from_child_metadata(list_view_path)
        object_list_views[object_name].append(list_view_path)

        root = parse_xml(list_view_path)
        if root is None:
            issues.append(f"ERROR {list_view_path}: unable to parse list view metadata.")
            continue
        object_list_view_names[object_name][layout_api_name(list_view_path, root)] = list_view_path
        issues.extend(check_list_view(list_view_path, root))

    for compact_layout_path in sorted(manifest_dir.rglob("*.compactLayout-meta.xml")):
        object_name = object_name_from_child_metadata(compact_layout_path)
        object_dir = compact_layout_path.parents[1]

        root = parse_xml(compact_layout_path)
        if root is None:
            issues.append(f"ERROR {compact_layout_path}: unable to parse compact layout metadata.")
            continue

        object_compact_layouts[object_name][layout_api_name(compact_layout_path, root)] = (
            compact_layout_path
        )

        if object_dir not in field_type_cache:
            field_type_cache[object_dir] = load_field_types(object_dir)
        issues.extend(
            check_compact_layout(compact_layout_path, root, field_type_cache[object_dir])
        )

    # compactLayoutAssignment lives on the CustomObject and on each RecordType.
    for object_path in sorted(manifest_dir.rglob("*.object-meta.xml")):
        root = parse_xml(object_path)
        if root is None:
            issues.append(f"ERROR {object_path}: unable to parse object metadata.")
            continue
        object_name = object_path.name.split(".")[0]
        for assigned in child_texts(root, "compactLayoutAssignment"):
            if assigned:
                object_assignments[object_name].add(assigned)

    for record_type_path in sorted(manifest_dir.rglob("*.recordType-meta.xml")):
        root = parse_xml(record_type_path)
        if root is None:
            continue
        object_name = object_name_from_child_metadata(record_type_path)
        for assigned in child_texts(root, "compactLayoutAssignment"):
            if assigned:
                object_assignments[object_name].add(assigned)

    # 6. Unassigned compact layouts.
    for object_name, layouts in sorted(object_compact_layouts.items()):
        assigned = object_assignments.get(object_name, set())
        for layout_name, layout_path in sorted(layouts.items()):
            if layout_name not in assigned:
                issues.append(
                    f"WARN {layout_path}: compact layout '{layout_name}' is not named by any "
                    f"compactLayoutAssignment on {object_name} or on any of its record types; "
                    "it will not render anywhere."
                )

    # CL-MEM-01 / CL-MEM-02: package.xml member form for object-nested types.
    issues.extend(
        check_manifest_members(manifest_dir, object_compact_layouts, object_list_view_names)
    )

    # Sprawl heuristics.
    for object_name, list_views in sorted(object_list_views.items()):
        if len(list_views) > MAX_LIST_VIEWS_PER_OBJECT:
            issues.append(
                f"INFO {object_name}: found {len(list_views)} list views in source; "
                "review for public view sprawl and near-duplicate working queues "
                "(note that queues auto-create a list view each)."
            )
        if len(list_views) >= 3 and not object_compact_layouts.get(object_name):
            issues.append(
                f"INFO {object_name}: has {len(list_views)} list views but no compact layout in "
                "source; the highlights panel and mobile card are running on the system default."
            )

    return issues


def coverage_note(manifest_dir: Path) -> str | None:
    """Say so when there was nothing of this type to check.

    Silence and a pass look identical to a build step's acceptance test, so an
    empty manifest gets a printed warning. It does not change the exit code:
    plenty of packages legitimately contain neither list views nor compact
    layouts.
    """
    if not manifest_dir.exists():
        return None
    if any(manifest_dir.rglob("*.listView-meta.xml")) or any(
        manifest_dir.rglob("*.compactLayout-meta.xml")
    ):
        return None
    return (
        f"WARN: no ListView or CompactLayout files found under --manifest-dir "
        f"({manifest_dir}); looked for *.listView-meta.xml and "
        "*.compactLayout-meta.xml anywhere beneath it. Nothing was checked."
    )


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        sys.exit(1)

    issues = check_list_views_and_compact_layouts(manifest_dir)

    note = coverage_note(manifest_dir)
    if note:
        print(note)

    if not issues:
        print("No issues found.")
        return 0

    print(f"Issues found ({len(issues)}):")
    for issue in issues:
        print(f"  ISSUE: {issue}")

    errors = [issue for issue in issues if issue.startswith("ERROR")]
    soft = [issue for issue in issues if not issue.startswith("ERROR")]
    if errors:
        print(f"{len(errors)} ERROR finding(s); this source will not deploy as written.")
        return 1
    if soft and args.strict:
        print(f"--strict: {len(soft)} WARN/INFO finding(s) promoted to a failure.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
