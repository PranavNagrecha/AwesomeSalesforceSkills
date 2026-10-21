#!/usr/bin/env python3
"""Checker for Related List Configuration on Page Layouts and Lightning Pages.

Parses Salesforce metadata under ``force-app/main/default/`` and reports:

  - related lists with more than 10 columns. The 10-column cap is Help-only
    (UNVERIFIED 2026-10-21): RelatedListItem.fields documents no cap
    (api_meta 264 L85859), so this is a WARN.
  - a ``sortField`` that looks unsortable (dotted cross-object reference or a
    long-text-sounding name) — a name heuristic, WARN.
  - per-record-type Page Layout drift — same object, divergent related-list
    sets across layouts. Layout has no description field (api_meta 264
    L85051-85153), so every divergence is reported for review (WARN).
  - FlexiPage related-list components whose relatedListApiName /
    relatedListName property names a relationship no Page Layout for that
    object exposes (WARN).

Severity: an unparseable layout or FlexiPage and a missing --manifest-dir are
ERRORs (exit 1). Every other finding is a WARN (exit 0 unless --strict). An
empty directory prints one WARN and exits 0.

Stdlib only.

Usage::

    python3 check_related_list_configuration.py \\
        --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple

MAX_CLASSIC_COLUMNS = 10

UNSORTABLE_FIELD_NAME_HINTS = (
    "Description",
    "Comments",
    "Notes",
    "Body",
    "LongText",
    "RichText",
)

UNSORTABLE_SUFFIXES = ("__rt",)

RELATED_LIST_PROPERTY_NAMES = {"relatedListApiName", "relatedListName"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect related-list configuration issues in a Salesforce metadata tree.",
    )
    parser.add_argument(
        "--manifest-dir",
        default="force-app/main/default",
        help="Root directory containing layouts/ and flexipages/. Default: force-app/main/default",
    )
    parser.add_argument("--strict", action="store_true", help="Exit 1 when any WARN is reported.")
    return parser.parse_args()


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _parse_layout(path: Path) -> Dict:
    """Return {"object", "name", "related_lists": [...]} or {"error": ...}."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return {"error": f"unparseable layout {path}: {exc}"}
    name = path.name.split(".layout")[0]
    object_name = name.split("-", 1)[0] if "-" in name else "?"

    related: List[Dict] = []
    for rl in root:
        if _local(rl.tag) != "relatedLists":
            continue
        entry = {"relationship": "", "fields": [], "sort_field": "", "sort_order": ""}
        for child in rl:
            tag = _local(child.tag)
            if tag == "relatedList":
                entry["relationship"] = child.text or ""
            elif tag == "sortField":
                entry["sort_field"] = child.text or ""
            elif tag == "sortOrder":
                entry["sort_order"] = child.text or ""
            elif tag == "fields":
                entry["fields"].append(child.text or "")
        if entry["relationship"]:
            related.append(entry)
    return {"object": object_name, "name": name, "related_lists": related}


def _check_column_count(layout: Dict) -> List[str]:
    warns: List[str] = []
    for rl in layout["related_lists"]:
        n = len(rl["fields"])
        if n > MAX_CLASSIC_COLUMNS:
            warns.append(
                f"Layout {layout['name']!r} related list {rl['relationship']!r} has {n} columns — "
                f"more than the 10-column cap Salesforce Help gives for related lists "
                f"(UNVERIFIED in the API guides); trim to 10."
            )
    return warns


def _looks_unsortable(field: str) -> bool:
    if not field:
        return False
    if "." in field:
        return True
    lower = field.lower()
    if any(h.lower() in lower for h in UNSORTABLE_FIELD_NAME_HINTS):
        return True
    return any(field.endswith(s) for s in UNSORTABLE_SUFFIXES)


def _check_sort_field(layout: Dict) -> List[str]:
    warns: List[str] = []
    for rl in layout["related_lists"]:
        sf = rl["sort_field"]
        if sf and _looks_unsortable(sf):
            reason = "dotted cross-object reference" if "." in sf else "long-text-sounding field name"
            warns.append(
                f"Layout {layout['name']!r} related list {rl['relationship']!r} sortField={sf!r} "
                f"looks unsortable ({reason}); confirm the field is sortable before relying on this sort."
            )
    return warns


def _check_layout_drift(layouts_by_object: Dict[str, List[Dict]]) -> List[str]:
    warns: List[str] = []
    for obj, layouts in layouts_by_object.items():
        if len(layouts) < 2:
            continue
        baseline = set(rl["relationship"] for rl in layouts[0]["related_lists"])
        for other in layouts[1:]:
            other_rel = set(rl["relationship"] for rl in other["related_lists"])
            missing, extra = baseline - other_rel, other_rel - baseline
            if not (missing or extra):
                continue
            diffs = []
            if missing:
                diffs.append(f"missing in {other['name']!r}: {sorted(missing)}")
            if extra:
                diffs.append(f"extra in {other['name']!r}: {sorted(extra)}")
            warns.append(
                f"Object {obj!r}: related-list drift between layouts {layouts[0]['name']!r} and "
                f"{other['name']!r} — {'; '.join(diffs)}. Confirm the divergence is intentional and "
                f"record it outside the layout (Layout has no description field)."
            )
    return warns


def _parse_flexipage_related_lists(path: Path) -> Tuple[List[Tuple[str, str]], str]:
    """Return ([(flexipage_name, related_list_api_name)], error).

    Reads each componentInstance's componentInstanceProperties and keeps the
    <value> whose sibling <name> is relatedListApiName or relatedListName.
    Other properties (e.g. relatedListComponentOverride=NONE on
    force:relatedListContainer, api_meta 264 L70339-70342) are ignored.
    """
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [], f"unparseable FlexiPage {path}: {exc}"
    fp_name = path.name.split(".flexipage")[0]
    out: List[Tuple[str, str]] = []
    for ci in root.iter():
        if _local(ci.tag) != "componentInstance":
            continue
        comp_name = "".join(c.text or "" for c in ci if _local(c.tag) == "componentName")
        if "relatedlist" not in comp_name.lower():
            continue
        for prop in ci:
            if _local(prop.tag) != "componentInstanceProperties":
                continue
            pname = "".join(kv.text or "" for kv in prop if _local(kv.tag) == "name")
            pvalue = "".join(kv.text or "" for kv in prop if _local(kv.tag) == "value")
            if pname in RELATED_LIST_PROPERTY_NAMES and pvalue:
                out.append((fp_name, pvalue))
    return out, ""


def check_related_list_configuration(manifest_dir: Path) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warns: List[str] = []
    layouts_dir = manifest_dir / "layouts"
    flexipages_dir = manifest_dir / "flexipages"

    layouts_by_object: Dict[str, List[Dict]] = {}
    for layout_path in sorted(layouts_dir.glob("*.layout-meta.xml")) if layouts_dir.is_dir() else []:
        layout = _parse_layout(layout_path)
        if "error" in layout:
            errors.append(layout["error"])
            continue
        layouts_by_object.setdefault(layout["object"], []).append(layout)
        warns.extend(_check_column_count(layout))
        warns.extend(_check_sort_field(layout))
    warns.extend(_check_layout_drift(layouts_by_object))

    layout_relationships = {
        obj: {rl["relationship"] for layout in layouts for rl in layout["related_lists"]}
        for obj, layouts in layouts_by_object.items()
    }
    for fp_path in sorted(flexipages_dir.glob("*.flexipage-meta.xml")) if flexipages_dir.is_dir() else []:
        fp_rels, err = _parse_flexipage_related_lists(fp_path)
        if err:
            errors.append(err)
            continue
        for fp_name, rel_api in fp_rels:
            obj_guess = fp_name.split("_", 1)[0]
            rels = layout_relationships.get(obj_guess)
            if rels is not None and rel_api not in rels:
                warns.append(
                    f"FlexiPage {fp_name!r} references related list {rel_api!r} but no Page Layout for "
                    f"object {obj_guess!r} in this directory exposes that relationship."
                )
    return errors, warns


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: manifest directory not found: {manifest_dir}")
        return 1
    if not (manifest_dir / "layouts").is_dir() and not (manifest_dir / "flexipages").is_dir():
        print(f"WARN: no layouts/ or flexipages/ directory under {manifest_dir} — nothing to check.")
        return 0

    errors, warns = check_related_list_configuration(manifest_dir)
    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if not errors and not warns:
        print("No related-list configuration issues found.")
    if errors:
        return 1
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
