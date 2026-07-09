#!/usr/bin/env python3
"""Checker for Screen Flow choice components (Radio Button Group and friends).

Parses Salesforce Flow metadata (`*.flow-meta.xml` / `*.flow`) and validates the
choice-reference integrity that the Radio Button Group — and every other choice
component (Radio Buttons, Checkbox Group, Picklist, Multi-Select Picklist) —
depends on. Stdlib only; no pip deps.

It reports concrete, actionable issues:
  - a choice-capable screen field that references NO choices (nothing to pick)
  - a `choiceReferences` that resolves to no defined `<choices>` /
    `<dynamicChoiceSets>` (a dangling reference — deploy-time or silent failure)
  - a `defaultSelectedChoiceReference` that isn't one of the field's choices
  - a single-option radio/checkbox group (a UX smell — use a checkbox or display
    text instead)
  - choice components declared in a non-screen flow (Choice resources and screen
    components exist only in Screen Flows)

The component type, orientation, and the *Let Users Select Multiple Options*
setting are chosen in the Flow Builder screen editor and are not asserted here;
this checker validates the shared, verifiable wiring (choices <-> references).

Usage:
    python3 check_screen_flow_radio_button_group.py [--manifest-dir path]

Exit code 0 = no issues, 1 = issues found (or no flow files to check).
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# FlowScreenField fieldType values that consume a Choice resource. The Summer '26
# Radio Button Group draws its options from the same Choice family, so any field
# carrying <choiceReferences> is treated as choice-based regardless of its exact
# fieldType serialization.
CHOICE_FIELD_TYPES = {
    "RadioButtons",
    "MultiSelectCheckboxes",
    "DropdownBox",
    "MultiSelectPicklist",
}
# processType values that CAN render screen components.
SCREEN_PROCESS_TYPES = {"Flow", "Survey"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Screen Flow choice components (Radio Button Group, etc.) for wiring issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source metadata (searched recursively for flow files).",
    )
    return parser.parse_args()


def _local(tag: str) -> str:
    """Strip an XML namespace: '{ns}fields' -> 'fields'."""
    return tag.rsplit("}", 1)[-1]


def _text(elem: ET.Element, child_local: str) -> str | None:
    for child in elem:
        if _local(child.tag) == child_local:
            return (child.text or "").strip() or None
    return None


def _children(elem: ET.Element, child_local: str) -> list[ET.Element]:
    return [c for c in elem if _local(c.tag) == child_local]


def _all(root: ET.Element, local: str) -> list[ET.Element]:
    return [e for e in root.iter() if _local(e.tag) == local]


def check_flow(path: Path, issues: list[str]) -> None:
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        issues.append(f"{path}: could not parse flow metadata ({exc})")
        return

    process_type = _text(root, "processType")

    # Names that a choiceReferences value may legitimately resolve to.
    defined_choices = {
        n for c in _all(root, "choices") if (n := _text(c, "name"))
    }
    defined_dynamic = {
        n for c in _all(root, "dynamicChoiceSets") if (n := _text(c, "name"))
    }
    resolvable = defined_choices | defined_dynamic

    # All screen fields, including those nested in Section/Column containers.
    fields = _all(root, "fields")
    saw_choice_field = False

    for field in fields:
        field_name = _text(field, "name") or "(unnamed field)"
        field_type = _text(field, "fieldType")
        refs = [
            (c.text or "").strip()
            for c in _children(field, "choiceReferences")
            if (c.text or "").strip()
        ]
        is_choice_field = field_type in CHOICE_FIELD_TYPES or bool(refs)
        if not is_choice_field:
            continue
        saw_choice_field = True

        if not refs:
            issues.append(
                f"{path}: field '{field_name}' is a choice component "
                f"(fieldType={field_type}) but references no choices — nothing to select"
            )
            continue

        for ref in refs:
            if ref not in resolvable:
                issues.append(
                    f"{path}: field '{field_name}' references choice '{ref}', which is not a "
                    f"defined <choices> or <dynamicChoiceSets> in this flow (dangling reference)"
                )

        default_ref = _text(field, "defaultSelectedChoiceReference")
        if default_ref and default_ref not in refs and default_ref not in resolvable:
            issues.append(
                f"{path}: field '{field_name}' default selection '{default_ref}' is not among "
                f"its choices — the default won't resolve"
            )

        # Single static choice on a radio/checkbox group is a UX smell.
        static_refs = [r for r in refs if r in defined_choices]
        if (
            field_type in {"RadioButtons", "MultiSelectCheckboxes"}
            and len(refs) == 1
            and len(static_refs) == 1
        ):
            issues.append(
                f"{path}: field '{field_name}' is a radio/checkbox group with a single static "
                f"option — prefer a checkbox or display text for a one-option choice"
            )

    if saw_choice_field and process_type and process_type not in SCREEN_PROCESS_TYPES:
        issues.append(
            f"{path}: choice components found in a non-screen flow (processType={process_type}); "
            f"Choice resources and screen components exist only in Screen Flows"
        )


def check(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    flow_files = sorted(
        {*manifest_dir.rglob("*.flow-meta.xml"), *manifest_dir.rglob("*.flow")}
    )
    if not flow_files:
        return [f"No flow files (*.flow-meta.xml / *.flow) found under {manifest_dir} — nothing to check."]

    for path in flow_files:
        check_flow(path, issues)
    return issues


def main() -> int:
    args = parse_args()
    issues = check(Path(args.manifest_dir))
    if not issues:
        print("No issues found.")
        return 0
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
