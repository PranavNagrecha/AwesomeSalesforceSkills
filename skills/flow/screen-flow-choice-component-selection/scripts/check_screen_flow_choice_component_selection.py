#!/usr/bin/env python3
"""Checker for Screen Flow choice-component selection anti-patterns.

Parses Flow metadata (``*.flow-meta.xml`` / ``*.flow``) and flags two documented
selection mistakes that Flow Builder does not surface at design time:

1. A multi-value choice component whose selection is referenced by a Loop or
   Transform element. The Checkbox Group, Choice Lookup, and Multi-Select
   Picklist components are incompatible with Transform and Loop elements
   (Multi-Select Resource and Screen Field Considerations for Flows). The
   Loop/Transform can't iterate the selection; redesign around a Data Table
   over a record collection instead.

2. A single-select component (Radio Buttons or Picklist) with a large number of
   *static* choices, where Choice Lookup's typeahead ("search for and select one
   option from a set of choices") would scan far better.

Stdlib only — no pip dependencies.

Usage:
    python3 check_screen_flow_choice_component_selection.py [--manifest-dir DIR]
                                                            [--max-choices N]
    python3 check_screen_flow_choice_component_selection.py --help

Exit code is 0 when no issues are found, 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# fieldType values (and ComponentInstance extensionName substrings) whose
# selection cannot feed a Loop or Transform element.
LOOP_INCOMPATIBLE_FIELDTYPES = {
    "MultiSelectPicklist": "Multi-Select Picklist",
    "MultiSelectCheckboxes": "Checkbox Group",
}
LOOP_INCOMPATIBLE_EXTENSIONS = {
    "choicelookup": "Choice Lookup",
}

# Single-select components whose large static choice lists suggest Choice Lookup.
SINGLE_SELECT_FIELDTYPES = {
    "RadioButtons": "Radio Buttons",
    "DropdownBox": "Picklist",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Screen Flow metadata for choice-component selection "
            "anti-patterns (Loop/Transform incompatibility, oversized "
            "single-select lists)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--max-choices",
        type=int,
        default=25,
        help=(
            "Warn when a Radio Buttons or Picklist field has more than this many "
            "static choices and Choice Lookup would scan better (default: 25)."
        ),
    )
    return parser.parse_args()


def _local(tag: str) -> str:
    """Return the local (namespace-stripped) name of an XML tag."""
    return tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str) -> str | None:
    for child in element:
        if _local(child.tag) == name:
            text = (child.text or "").strip()
            return text or None
    return None


def _iter_local(root: ET.Element, name: str):
    """Yield every descendant (and root) whose local tag name matches ``name``."""
    for element in root.iter():
        if _local(element.tag) == name:
            yield element


def _screen_fields(root: ET.Element):
    """Yield ``fields`` elements that look like screen fields.

    A screen field carries a ``fieldType`` (or an ``extensionName`` for the
    ComponentInstance-based components). This avoids matching unrelated
    ``fields`` tags elsewhere in the document.
    """
    for element in _iter_local(root, "fields"):
        has_type = any(
            _local(child.tag) in ("fieldType", "extensionName") for child in element
        )
        if has_type:
            yield element


def _classify_incompatible(field: ET.Element) -> str | None:
    """Return a friendly component name if the field can't feed Loop/Transform."""
    field_type = _child_text(field, "fieldType")
    if field_type in LOOP_INCOMPATIBLE_FIELDTYPES:
        return LOOP_INCOMPATIBLE_FIELDTYPES[field_type]
    extension = (_child_text(field, "extensionName") or "").lower()
    for needle, label in LOOP_INCOMPATIBLE_EXTENSIONS.items():
        if needle in extension:
            return label
    return None


def _descendant_texts(element: ET.Element) -> set[str]:
    texts: set[str] = set()
    for node in element.iter():
        if node.text:
            value = node.text.strip()
            if value:
                texts.add(value)
    return texts


def _references_field(texts: set[str], field_name: str) -> bool:
    """True if any reference text names the field or a member of it."""
    for text in texts:
        if text == field_name or text.startswith(field_name + "."):
            return True
    return False


def check_flow_file(path: Path, max_choices: int) -> list[str]:
    issues: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"{path}: could not parse XML ({exc})"]

    # Only screen flows have screen fields; a non-screen flow simply yields none.
    process_type = _child_text(root, "processType")

    incompatible: dict[str, str] = {}  # field name -> component label
    for field in _screen_fields(root):
        name = _child_text(field, "name")
        if not name:
            continue

        label = _classify_incompatible(field)
        if label:
            incompatible[name] = label

        field_type = _child_text(field, "fieldType")
        if field_type in SINGLE_SELECT_FIELDTYPES:
            choice_count = sum(
                1 for child in field if _local(child.tag) == "choiceReferences"
            )
            if choice_count > max_choices:
                issues.append(
                    f"{path}: {SINGLE_SELECT_FIELDTYPES[field_type]} field "
                    f"'{name}' has {choice_count} static choices "
                    f"(> {max_choices}); consider Choice Lookup for a "
                    f"searchable single-select list."
                )

    if incompatible:
        for holder_tag in ("loops", "transforms"):
            for holder in _iter_local(root, holder_tag):
                holder_name = _child_text(holder, "name") or "(unnamed)"
                texts = _descendant_texts(holder)
                for field_name, label in incompatible.items():
                    if _references_field(texts, field_name):
                        issues.append(
                            f"{path}: {holder_tag[:-1].capitalize()} "
                            f"'{holder_name}' references {label} field "
                            f"'{field_name}'. That component is incompatible "
                            f"with Loop and Transform elements — use a Data "
                            f"Table over a record collection instead."
                        )

    if process_type and process_type != "Flow" and issues:
        # Keep the finding but note it isn't a screen flow (unexpected).
        issues = [f"{i} [processType={process_type}]" for i in issues]

    return issues


def check_screen_flow_choice_component_selection(
    manifest_dir: Path, max_choices: int
) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    flow_files = sorted(
        set(manifest_dir.rglob("*.flow-meta.xml")) | set(manifest_dir.rglob("*.flow"))
    )
    if not flow_files:
        return [f"No Flow metadata (*.flow-meta.xml) found under {manifest_dir}"]

    for path in flow_files:
        issues.extend(check_flow_file(path, max_choices))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_screen_flow_choice_component_selection(manifest_dir, args.max_choices)

    # "No Flow metadata found" is informational, not a failure.
    if len(issues) == 1 and issues[0].startswith("No Flow metadata"):
        print(issues[0])
        return 0

    if not issues:
        print("No choice-component selection issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
