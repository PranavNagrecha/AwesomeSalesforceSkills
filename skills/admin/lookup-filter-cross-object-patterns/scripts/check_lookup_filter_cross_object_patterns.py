#!/usr/bin/env python3
"""Lint ``lookupFilter`` blocks in Salesforce DX field metadata.

Reads ``objects/*/fields/*.field-meta.xml`` from a DX tree (or from explicit
paths) and reports structural problems in each field's ``<lookupFilter>``
element. Stdlib only; safe in pre-commit / CI.

Grounding for the structural rules, from the Metadata API Developer Guide's
``LookupFilter`` and ``FilterItem`` tables (api_meta.txt:43860-43924):

* ``LookupFilter`` has exactly seven fields: ``active``, ``booleanFilter``,
  ``description``, ``errorMessage``, ``filterItems``, ``infoMessage``,
  ``isOptional``. ``active``, ``filterItems`` and ``isOptional`` are marked
  Required.
* "You can have up to 10 FilterItems per lookup filter."
* ``valueField`` "specifies if the final column in the filter contains a field
  or a field value" - it is the alternative to ``value``, not a companion.
* ``FilterOperation`` is a closed enum with no functions.

Checks
------
ERROR   Active filter with zero ``filterItems`` (``filterItems`` is Required).
ERROR   A ``filterItems`` entry carrying both ``value`` and ``valueField``.
ERROR   A ``filterItems`` entry with no ``field`` or no ``operation``.
ERROR   ``booleanFilter`` referencing an item index that does not exist.
ERROR   More than 10 ``filterItems`` in one filter.
ERROR   An ``operation`` outside the documented ``FilterOperation`` enum.
ERROR   A function call in a filter value (``TRIM(``, ``IF(`` ...); the
        grammar is field / operator / field-or-value only.
WARN    Required filter (``isOptional`` false) with no ``errorMessage``.
WARN    ``valueField`` that does not start with ``$Source.``.
WARN    ``$Source.`` path with more than two segments (two-hop traversal).
INFO    Optional filter (``isOptional`` true) with no ``infoMessage``.

Exit code: 1 if any ERROR or WARN was reported, else 0. INFO lines are
advisory and do not fail the run unless ``--strict`` is passed.

Usage
-----
    python3 check_lookup_filter_cross_object_patterns.py --manifest-dir force-app/main/default
    python3 check_lookup_filter_cross_object_patterns.py path/to/Field__c.field-meta.xml
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SUFFIX = ".field-meta.xml"
MAX_FILTER_ITEMS = 10  # api_meta.txt:43883-43884

# api_meta.txt:43903-43916
FILTER_OPERATIONS = {
    "equals",
    "notEqual",
    "lessThan",
    "greaterThan",
    "lessOrEqual",
    "greaterOrEqual",
    "contains",
    "notContain",
    "startsWith",
    "includes",
    "excludes",
    "within",
}

FUNC_CALL = re.compile(
    r"\b(TRIM|UPPER|LOWER|TEXT|IF|CASE|VALUE|DATE|MID|ISBLANK|ISNULL|TODAY|NOW)\s*\("
)
INDEX_TOKEN = re.compile(r"\d+")


def local(tag: str) -> str:
    """Strip the ``{namespace}`` prefix ElementTree keeps on every tag."""
    return tag.rsplit("}", 1)[-1]


def child(element: ET.Element, name: str) -> ET.Element | None:
    """Return the first direct child with local name ``name``, or None.

    Written as an explicit loop because a leaf Element is falsy, so
    ``a.find(x) or a.find(y)`` silently discards a real, empty element.
    """
    for candidate in element:
        if local(candidate.tag) == name:
            return candidate
    return None


def children(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in element if local(c.tag) == name]


def text_of(element: ET.Element, name: str) -> str | None:
    """Text of the first ``name`` child, or None when the child is absent.

    An element that is present but empty returns "" - which is a different
    answer from None, and the checks below rely on the difference.
    """
    found = child(element, name)
    if found is None:
        return None
    return (found.text or "").strip()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint lookupFilter blocks in Salesforce DX field metadata."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Field metadata files or directories to scan.",
    )
    parser.add_argument(
        "--manifest-dir",
        help="Salesforce DX source root, e.g. force-app/main/default.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also fail the run on INFO-level notes.",
    )
    return parser.parse_args(argv)


def collect_files(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.extend(sorted(path.rglob("*" + SUFFIX)))
        elif path.name.endswith(SUFFIX):
            found.append(path)
    # Deduplicate while keeping order.
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in found:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def audit_filter(path: Path, field_name: str, lf: ET.Element) -> list[str]:
    findings: list[str] = []
    where = f"{path}: {field_name}"

    active = (text_of(lf, "active") or "").lower()
    is_optional_raw = text_of(lf, "isOptional")
    is_optional = (is_optional_raw or "").lower() == "true"
    items = children(lf, "filterItems")

    if active != "true" and active != "false":
        findings.append(
            f"ERROR {where}: lookupFilter has no <active> value; "
            "active is a Required boolean (api_meta.txt:43865-43866)"
        )
    if is_optional_raw is None:
        findings.append(
            f"ERROR {where}: lookupFilter has no <isOptional> value; "
            "isOptional is a Required boolean (api_meta.txt:43890-43891)"
        )

    if active == "true" and not items:
        findings.append(
            f"ERROR {where}: active lookupFilter has zero <filterItems>; "
            "filterItems is Required, so this filter constrains nothing"
        )

    if len(items) > MAX_FILTER_ITEMS:
        findings.append(
            f"ERROR {where}: {len(items)} filterItems; the documented cap is "
            f"{MAX_FILTER_ITEMS} per lookup filter (api_meta.txt:43883-43884)"
        )

    for position, item in enumerate(items, start=1):
        item_where = f"{where} filterItems[{position}]"
        field = text_of(item, "field")
        operation = text_of(item, "operation")
        value = text_of(item, "value")
        value_field = text_of(item, "valueField")

        if not field:
            findings.append(f"ERROR {item_where}: no <field>")
        if not operation:
            findings.append(f"ERROR {item_where}: no <operation>")
        elif operation not in FILTER_OPERATIONS:
            findings.append(
                f"ERROR {item_where}: operation '{operation}' is not in the "
                "FilterOperation enum (api_meta.txt:43903-43916)"
            )

        if value is not None and value_field is not None:
            findings.append(
                f"ERROR {item_where}: carries both <value> and <valueField>; "
                "valueField is the alternative to value, not a companion "
                "(api_meta.txt:43922-43924)"
            )
        elif value is None and value_field is None:
            findings.append(
                f"ERROR {item_where}: has neither <value> nor <valueField>, "
                "so the comparison has no right-hand side"
            )

        for candidate in (value, value_field):
            if candidate and FUNC_CALL.search(candidate):
                findings.append(
                    f"ERROR {item_where}: function call in '{candidate}'; the "
                    "filter grammar is field / operator / field-or-value only"
                )

        if value_field:
            if not value_field.startswith("$Source."):
                findings.append(
                    f"WARN {item_where}: valueField '{value_field}' does not "
                    "start with '$Source.'; the right-hand side of a "
                    "cross-object filter names a field on the record being "
                    "edited"
                )
            else:
                segments = value_field[len("$Source.") :].split(".")
                if len(segments) > 2:
                    findings.append(
                        f"WARN {item_where}: valueField '{value_field}' "
                        "traverses more than one relationship; flatten the "
                        "path with a formula field on the first parent"
                    )

    boolean_filter = text_of(lf, "booleanFilter")
    if boolean_filter:
        referenced = {int(token) for token in INDEX_TOKEN.findall(boolean_filter)}
        for index in sorted(referenced):
            if index < 1 or index > len(items):
                findings.append(
                    f"ERROR {where}: booleanFilter '{boolean_filter}' "
                    f"references item {index}, but the filter has "
                    f"{len(items)} filterItems; the numbers index items by "
                    "document position"
                )
        missing = {n for n in range(1, len(items) + 1)} - referenced
        if referenced and missing:
            findings.append(
                f"WARN {where}: booleanFilter '{boolean_filter}' never "
                f"references item(s) {sorted(missing)}; those conditions are "
                "carried in the file but not in the logic"
            )

    if not is_optional and is_optional_raw is not None:
        if not text_of(lf, "errorMessage"):
            findings.append(
                f"WARN {where}: required filter (isOptional false) with no "
                "<errorMessage>; the user is rejected and told nothing "
                "(api_meta.txt:43872)"
            )
    elif is_optional:
        if not text_of(lf, "infoMessage"):
            findings.append(
                f"INFO {where}: optional filter with no <infoMessage>; the "
                "picker is silently shortened with no explanation "
                "(api_meta.txt:43886-43888)"
            )

    return findings


def audit_file(path: Path) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"ERROR {path}: not well-formed XML ({exc})"]
    except OSError as exc:
        return [f"ERROR {path}: cannot read ({exc})"]

    field_name = text_of(root, "fullName") or path.name[: -len(SUFFIX)]

    findings: list[str] = []
    # Decomposed DX form: <CustomField> with one lookupFilter.
    # Bundled form: <CustomObject> with many <fields> entries.
    if local(root.tag) == "CustomObject":
        for field in children(root, "fields"):
            name = text_of(field, "fullName") or "<unnamed field>"
            for lf in children(field, "lookupFilter"):
                findings.extend(audit_filter(path, name, lf))
    else:
        for lf in children(root, "lookupFilter"):
            findings.extend(audit_filter(path, field_name, lf))
    return findings


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    targets = [Path(p) for p in args.paths]
    if args.manifest_dir:
        root = Path(args.manifest_dir)
        if not root.exists():
            print(f"ERROR: --manifest-dir not found: {root}", file=sys.stderr)
            return 1
        targets.append(root)
    if not targets:
        print(
            "ERROR: provide one or more paths, or --manifest-dir",
            file=sys.stderr,
        )
        return 1

    files = collect_files(targets)
    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    failing = [f for f in findings if f.startswith(("ERROR", "WARN"))]
    notes = [f for f in findings if f.startswith("INFO")]

    for line in findings:
        stream = sys.stdout if line.startswith("INFO") else sys.stderr
        print(line, file=stream)

    print(
        f"[lookup-filter-cross-object-patterns] scanned {len(files)} field "
        f"metadata file(s); {len(failing)} finding(s), {len(notes)} note(s)."
    )

    if failing:
        return 1
    if notes and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    if main() != 0:
        sys.exit(1)
    sys.exit(0)
