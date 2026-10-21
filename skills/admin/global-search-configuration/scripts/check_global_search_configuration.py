#!/usr/bin/env python3
"""Static checker for global search configuration hygiene.

Scans a Salesforce metadata source tree for search configuration problems.
Element names follow the Metadata API guide (api_meta 264):

- SearchLayouts lives inside CustomObject; the search results list is
  `searchResultsAdditionalFields` (L47580), the lookup dialog list is
  `lookupDialogsAdditionalFields` (L47528); Name is implicit (L47509-47510).
    WARN  empty or absent searchResultsAdditionalFields (Name-only results)
    WARN  fewer than 2 additional search result columns (heuristic)
    WARN  more than 10 columns in a list (Help-only cap, not in the corpus)
    WARN  lookupDialogsAdditionalFields over 6 with --include-hybrid-classic
          (Help-only Classic cap)
    WARN  a custom field (__c) in a list that the object does not declare
- External objects (*__x): enableSearch not true -> WARN (search is off by
  default for new external objects, L44352).
- ExternalDataSource: customConfiguration JSON without "searchEnabled":"true"
  on SfdcOrg / OData / OData4 types -> WARN (L13818-13850).
- SynonymDictionary groups (L136400-136410):
    ERROR a group with fewer than two <terms>, a term over 50 characters, or
          no <languages> (Required)
- Any XML file that does not parse -> ERROR.

Exit codes: 1 on any ERROR or a missing --manifest-dir; WARN findings exit 0
unless --strict; a tree with no relevant files prints one WARN and exits 0.
Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"
LISTS = (
    "searchResultsAdditionalFields",
    "lookupDialogsAdditionalFields",
    "lookupPhoneDialogsAdditionalFields",
    "customTabListAdditionalFields",
    "searchFilterFields",
    "lookupFilterFields",
)
MIN_ADDITIONAL_RESULT_COLUMNS = 2
HELP_ONLY_MAX_COLUMNS = 10
HELP_ONLY_CLASSIC_LOOKUP_MAX = 6
SEARCHABLE_SOURCE_TYPES = {"SfdcOrg", "OData", "OData4"}
# Skip custom metadata types, platform events and big objects: not global-search
# targets, so an empty search layout there is noise (reviewer heuristic).
NO_SEARCH_LAYOUT_SUFFIXES = ("__mdt", "__e", "__b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit Search Layouts, external search flags and synonyms.")
    parser.add_argument("--manifest-dir", default=".", help="Root of the Salesforce metadata source tree.")
    parser.add_argument("--include-hybrid-classic", action="store_true",
                        help="Warn on lookup dialogs over the Classic 6-column cap.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    return parser.parse_args()


def _all(el: ET.Element, tag: str) -> list[ET.Element]:
    return el.findall(NS + tag) + el.findall(tag)


def _one(el: ET.Element, tag: str) -> ET.Element | None:
    found = el.find(NS + tag)
    if found is None:
        found = el.find(tag)
    return found


def _parse(path: Path, root: Path, errors: list[str]) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        errors.append(f"{path.relative_to(root)}: XML does not parse ({exc})")
        return None


def object_name(path: Path) -> str:
    for suffix in (".object-meta.xml", ".object"):
        if path.name.endswith(suffix):
            return path.name[: -len(suffix)]
    return path.stem


def declared_fields(path: Path, obj: ET.Element) -> set[str]:
    names = {p.name.removesuffix(".field-meta.xml") for p in (path.parent / "fields").glob("*.field-meta.xml")}
    for field in _all(obj, "fields"):
        full = _one(field, "fullName")
        if full is not None and full.text:
            names.add(full.text.strip())
    return names


def check_object(path: Path, root: Path, errors: list[str], warns: list[str], hybrid: bool) -> None:
    obj = _parse(path, root, errors)
    if obj is None:
        return
    name = object_name(path)
    if name.endswith(NO_SEARCH_LAYOUT_SUFFIXES):
        return
    if name.endswith("__x"):
        enable = _one(obj, "enableSearch")
        if enable is None or (enable.text or "").strip().lower() != "true":
            warns.append(f"{name}: external object enableSearch is not true; it will not appear in search")
    layouts = _one(obj, "searchLayouts")
    lists = {tag: [] for tag in LISTS}
    if layouts is not None:
        for tag in LISTS:
            lists[tag] = [(e.text or "").strip() for e in _all(layouts, tag) if (e.text or "").strip()]
    results = lists["searchResultsAdditionalFields"]
    if not results:
        warns.append(f"{name}: searchResultsAdditionalFields is empty; search results show Name only")
    elif len(results) < MIN_ADDITIONAL_RESULT_COLUMNS:
        warns.append(f"{name}: only {len(results)} search result column(s) besides Name")
    for tag, fields in lists.items():
        if len(fields) > HELP_ONLY_MAX_COLUMNS:
            warns.append(f"{name}: {tag} has {len(fields)} entries; the Help-documented cap is {HELP_ONLY_MAX_COLUMNS}")
    if hybrid and len(lists["lookupDialogsAdditionalFields"]) > HELP_ONLY_CLASSIC_LOOKUP_MAX:
        warns.append(f"{name}: lookupDialogsAdditionalFields has {len(lists['lookupDialogsAdditionalFields'])} "
                     f"entries; Classic shows the first {HELP_ONLY_CLASSIC_LOOKUP_MAX} (Help-only cap)")
    known = declared_fields(path, obj)
    if known:
        for tag, fields in lists.items():
            for field in fields:
                if field.endswith("__c") and "." not in field and field not in known:
                    warns.append(f"{name}: {tag} references {field}, which this object does not declare")


def check_data_source(path: Path, root: Path, errors: list[str], warns: list[str]) -> None:
    src = _parse(path, root, errors)
    if src is None:
        return
    src_type = (_one(src, "type").text or "").strip() if _one(src, "type") is not None else ""
    if src_type not in SEARCHABLE_SOURCE_TYPES:
        return
    raw = _one(src, "customConfiguration")
    config = {}
    if raw is not None and raw.text:
        try:
            config = json.loads(raw.text)
        except ValueError:
            warns.append(f"{path.relative_to(root)}: customConfiguration is not valid JSON")
            return
    if str(config.get("searchEnabled", "")).lower() != "true":
        warns.append(f"{path.relative_to(root)}: type {src_type} without \"searchEnabled\":\"true\"; "
                     "its external objects cannot be searched")


def check_synonyms(path: Path, root: Path, errors: list[str]) -> None:
    dictionary = _parse(path, root, errors)
    if dictionary is None:
        return
    rel = path.relative_to(root)
    for index, group in enumerate(_all(dictionary, "groups"), 1):
        terms = [(t.text or "").strip() for t in _all(group, "terms")]
        if len(terms) < 2:
            errors.append(f"{rel}: group {index} has {len(terms)} term(s); minimum is two")
        for term in terms:
            if len(term) > 50:
                errors.append(f"{rel}: group {index} term '{term[:30]}...' exceeds 50 characters")
        if not _all(group, "languages"):
            errors.append(f"{rel}: group {index} has no <languages> (Required)")


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    objects = sorted(set(root.rglob("*.object-meta.xml")) | set(root.rglob("*.object")))
    sources = sorted(set(root.rglob("*.dataSource-meta.xml")) | set(root.rglob("*.dataSource")))
    synonyms = sorted(set(root.rglob("*.synonymDictionary-meta.xml")) | set(root.rglob("*.synonymDictionary")))
    if not (objects or sources or synonyms):
        print(f"WARN: no object, dataSource or synonymDictionary files under {root}; nothing to check")
        return 0
    errors: list[str] = []
    warns: list[str] = []
    for path in objects:
        check_object(path, root, errors, warns, args.include_hybrid_classic)
    for path in sources:
        check_data_source(path, root, errors, warns)
    for path in synonyms:
        check_synonyms(path, root, errors)
    for msg in errors:
        print(f"ERROR: {msg}")
    for msg in warns:
        print(f"WARN: {msg}")
    if not errors and not warns:
        print("OK: no global search configuration issues found.")
    if errors or (warns and args.strict):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
