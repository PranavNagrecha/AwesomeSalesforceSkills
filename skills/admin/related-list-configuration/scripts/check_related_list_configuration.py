#!/usr/bin/env python3
"""Checker for Related List Configuration on Page Layouts and Lightning Pages.

Parses Salesforce metadata under ``force-app/main/default/`` and emits
specific issues in related-list configuration:

  - related lists with more than 10 columns (silent drop on classic component)
  - related lists with an unsortable ``sortField`` (cross-object formula or
    long-text candidates, picked by name heuristic)
  - per-record-type Page Layout drift — same object, divergent related-list
    sets across layouts with no description note documenting intent
  - Lightning FlexiPages that rely on ``Related List - Single`` components
    referencing a relationship not present on the corresponding Page Layout

Stdlib only.

Usage::

    python3 check_related_list_configuration.py \\
        --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}

MAX_CLASSIC_COLUMNS = 10

UNSORTABLE_FIELD_NAME_HINTS = (
    "Description",
    "Comments",
    "Notes",
    "Body",
    "LongText",
    "RichText",
)

UNSORTABLE_SUFFIXES = (
    "__rt",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Detect related-list configuration issues in a Salesforce "
            "metadata tree."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default="force-app/main/default",
        help=(
            "Root directory containing layouts/, flexipages/, objects/. "
            "Default: force-app/main/default"
        ),
    )
    return parser.parse_args()


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _findall_text(elem: ET.Element, tag: str) -> List[str]:
    return [c.text or "" for c in elem.iter() if _local(c.tag) == tag]


def _parse_layout(path: Path) -> Dict:
    """Return a dict describing the layout's related lists.

    Shape::

        {
            "object": "Account",
            "name": "Account-Account Sales Layout",
            "description": "...",
            "related_lists": [
                {
                    "relationship": "Contacts",
                    "fields": ["NAME", "TITLE", ...],
                    "sort_field": "LastModifiedDate",
                    "sort_order": "Desc",
                },
                ...
            ],
        }
    """
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return {"error": f"unparseable layout {path}: {exc}"}
    root = tree.getroot()
    name = path.stem
    object_name = name.split("-", 1)[0] if "-" in name else "?"

    description = ""
    for desc in root.iter():
        if _local(desc.tag) == "description":
            description = desc.text or ""
            break

    related: List[Dict] = []
    for rl in root.iter():
        if _local(rl.tag) != "relatedLists":
            continue
        rel_name = ""
        sort_field = ""
        sort_order = ""
        fields: List[str] = []
        for child in rl:
            tag = _local(child.tag)
            if tag == "relatedList":
                rel_name = child.text or ""
            elif tag == "sortField":
                sort_field = child.text or ""
            elif tag == "sortOrder":
                sort_order = child.text or ""
            elif tag == "fields":
                fields.append(child.text or "")
        if rel_name:
            related.append(
                {
                    "relationship": rel_name,
                    "fields": fields,
                    "sort_field": sort_field,
                    "sort_order": sort_order,
                }
            )

    return {
        "object": object_name,
        "name": name,
        "description": description,
        "related_lists": related,
    }


def _check_column_count(layout: Dict) -> List[str]:
    issues: List[str] = []
    for rl in layout.get("related_lists", []):
        n = len(rl.get("fields") or [])
        if n > MAX_CLASSIC_COLUMNS:
            issues.append(
                f"Layout {layout['name']!r} related list "
                f"{rl['relationship']!r} has {n} columns — "
                f"classic Related Lists component silently drops everything "
                f"after column 10. Trim or migrate to Enhanced Related Lists."
            )
    return issues


def _looks_unsortable(field: str) -> bool:
    if not field:
        return False
    if "." in field:
        return True
    lower = field.lower()
    for hint in UNSORTABLE_FIELD_NAME_HINTS:
        if hint.lower() in lower:
            return True
    for suffix in UNSORTABLE_SUFFIXES:
        if field.endswith(suffix):
            return True
    return False


def _check_sort_field(layout: Dict) -> List[str]:
    issues: List[str] = []
    for rl in layout.get("related_lists", []):
        sf = rl.get("sort_field") or ""
        if sf and _looks_unsortable(sf):
            reason = (
                "cross-object formula"
                if "." in sf
                else "likely long-text / non-sortable field"
            )
            issues.append(
                f"Layout {layout['name']!r} related list "
                f"{rl['relationship']!r} sort_field={sf!r} looks unsortable "
                f"({reason}); the configured sort will silently fall back to "
                f"default sort at render."
            )
    return issues


def _check_layout_drift(
    layouts_by_object: Dict[str, List[Dict]],
) -> List[str]:
    issues: List[str] = []
    for obj, layouts in layouts_by_object.items():
        if len(layouts) < 2:
            continue
        # Compare related-list sets pairwise; flag divergence not
        # documented in the description.
        baseline_rel = set(
            rl["relationship"] for rl in layouts[0]["related_lists"]
        )
        for other in layouts[1:]:
            other_rel = set(
                rl["relationship"] for rl in other["related_lists"]
            )
            diff_missing = baseline_rel - other_rel
            diff_extra = other_rel - baseline_rel
            if not (diff_missing or diff_extra):
                continue
            desc_documents = (
                "INTENTIONAL" in other.get("description", "").upper()
                or "INTENTIONAL"
                in layouts[0].get("description", "").upper()
            )
            if desc_documents:
                continue
            diffs = []
            if diff_missing:
                diffs.append(f"missing in {other['name']!r}: {sorted(diff_missing)}")
            if diff_extra:
                diffs.append(f"extra in {other['name']!r}: {sorted(diff_extra)}")
            issues.append(
                f"Object {obj!r}: related-list drift between layouts "
                f"{layouts[0]['name']!r} and {other['name']!r} — "
                f"{'; '.join(diffs)}. No layout description documents the "
                f"intent (look for 'INTENTIONAL' in the description)."
            )
    return issues


def _parse_flexipage_related_lists(path: Path) -> List[Tuple[str, str]]:
    """Return list of (flexipage_name, related_list_relationship)."""
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return []
    root = tree.getroot()
    fp_name = path.stem
    out: List[Tuple[str, str]] = []
    # FlexiPage uses ItemInstances with componentName attribute.
    for ci in root.iter():
        if _local(ci.tag) != "componentName":
            continue
        comp = (ci.text or "").lower()
        if "relatedlist" not in comp:
            continue
        # Find sibling "relatedListApiName" or properties block
        parent = None
        # Walk back up to find the nearest property block
        # ET does not give parent pointers; do a re-pass:
    # Simpler pass: iterate all itemInstance / componentInstance
    for ci in root.iter():
        if _local(ci.tag) != "componentInstance":
            continue
        comp_name = ""
        rel_api = ""
        for child in ci.iter():
            t = _local(child.tag)
            if t == "componentName":
                comp_name = (child.text or "")
            elif t == "name" and (child.text or "") in {
                "relatedListApiName",
                "relatedListName",
            }:
                # Sibling <value> carries the relationship
                # Sibling tag iteration order is reliable in ET on append.
                pass
            elif t == "value":
                # Heuristic: last <value> before component end is the rel
                # api name when comp is RelatedListSingle.
                v = (child.text or "")
                if v and rel_api == "":
                    rel_api = v
        if comp_name and "relatedlist" in comp_name.lower() and rel_api:
            out.append((fp_name, rel_api))
    return out


def check_related_list_configuration(manifest_dir: Path) -> List[str]:
    issues: List[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    layouts_dir = manifest_dir / "layouts"
    flexipages_dir = manifest_dir / "flexipages"

    layouts_by_object: Dict[str, List[Dict]] = {}
    if layouts_dir.exists():
        for layout_path in sorted(layouts_dir.glob("*.layout-meta.xml")):
            layout = _parse_layout(layout_path)
            if "error" in layout:
                issues.append(layout["error"])
                continue
            layouts_by_object.setdefault(layout["object"], []).append(layout)
            issues.extend(_check_column_count(layout))
            issues.extend(_check_sort_field(layout))
        issues.extend(_check_layout_drift(layouts_by_object))

    if flexipages_dir.exists():
        # Build set of (object, relationship) covered by layouts
        layout_relationships: Dict[str, set] = {}
        for obj, layouts in layouts_by_object.items():
            rels = set()
            for layout in layouts:
                for rl in layout["related_lists"]:
                    rels.add(rl["relationship"])
            layout_relationships[obj] = rels

        for fp_path in sorted(flexipages_dir.glob("*.flexipage-meta.xml")):
            fp_rels = _parse_flexipage_related_lists(fp_path)
            for fp_name, rel_api in fp_rels:
                # Derive object from FlexiPage convention: <Object>_Record_Page
                obj_guess = fp_name.split("_", 1)[0]
                rels = layout_relationships.get(obj_guess)
                if rels is None:
                    continue
                if rel_api not in rels:
                    issues.append(
                        f"FlexiPage {fp_name!r} references Related List "
                        f"{rel_api!r} but no Page Layout for object "
                        f"{obj_guess!r} exposes that relationship — the "
                        f"component will render empty or fall back to a "
                        f"different list."
                    )

    if not (layouts_dir.exists() or flexipages_dir.exists()):
        issues.append(
            "No layouts/ or flexipages/ directory under "
            f"{manifest_dir} — nothing to check."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_related_list_configuration(manifest_dir)

    if not issues:
        print("No related-list configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
