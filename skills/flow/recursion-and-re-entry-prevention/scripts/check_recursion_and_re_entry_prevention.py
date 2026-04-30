#!/usr/bin/env python3
"""Static checker for record-triggered Flow recursion risk.

Scans `force-app/.../flows/*.flow-meta.xml` and flags Flow definitions whose
entry criteria (start element filters) likely permit self-re-entry:

- Record-triggered after-save Flows whose `RecordUpdates`/`recordUpdates`
  target the same object as the trigger and write a field that appears in
  the start filter — possible self-re-entry without a state guard.
- Start filters that reference `ISCHANGED(...)` on a field the Flow itself
  updates, without a paired comparison clause (state guard).
- "Run on Create or Update" triggers with no filter conditions (likely
  over-broad and a recursion risk).

Stdlib only; XML parser is `xml.etree.ElementTree`.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Detect Flow recursion risk in record-triggered flows."
    )
    p.add_argument("--manifest-dir", default=".", help="Project root.")
    return p.parse_args()


def flow_files(root: Path) -> list[Path]:
    return list((root / "force-app").rglob("*.flow-meta.xml"))


def text(elem: ET.Element | None) -> str:
    return (elem.text or "").strip() if elem is not None else ""


def find_start(root: ET.Element) -> ET.Element | None:
    return root.find(f"{NS}start")


def find_record_update_targets(root: ET.Element, trigger_object: str) -> set[str]:
    """Return set of field API names the Flow writes back on the trigger object."""
    targets: set[str] = set()
    for ru in root.findall(f"{NS}recordUpdates"):
        # If the recordUpdates inputReference is `$Record` it targets the trigger record.
        input_ref = text(ru.find(f"{NS}inputReference"))
        obj = text(ru.find(f"{NS}object"))
        is_self = input_ref == "$Record" or obj == trigger_object
        if not is_self:
            continue
        for assignment in ru.findall(f"{NS}inputAssignments"):
            field = text(assignment.find(f"{NS}field"))
            if field:
                targets.add(field)
    return targets


def find_filter_fields(start: ET.Element) -> set[str]:
    fields: set[str] = set()
    for f in start.findall(f"{NS}filters"):
        field = text(f.find(f"{NS}field"))
        if field:
            fields.add(field)
    # formula-based filters
    formula = text(start.find(f"{NS}filterFormula"))
    if formula:
        fields.update(re.findall(r"\{!\$Record\.(\w+)\}", formula))
        # Bare ISCHANGED references
        fields.update(re.findall(r"ISCHANGED\(\s*\{!\$Record\.(\w+)\}\s*\)", formula))
    return fields


def has_state_guard(start: ET.Element, field: str) -> bool:
    """Heuristic: a filterFormula contains both ISCHANGED(field) and field <> something."""
    formula = text(start.find(f"{NS}filterFormula"))
    if not formula:
        return False
    has_ischanged = bool(re.search(rf"ISCHANGED\(\s*\{{!\$Record\.{re.escape(field)}\}}\s*\)", formula))
    has_compare = bool(re.search(rf"\{{!\$Record\.{re.escape(field)}\}}\s*<>", formula))
    return has_ischanged and has_compare


def check_flow(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"{path}: parse error — {exc}"]
    root = tree.getroot()

    start = find_start(root)
    if start is None:
        return issues

    trigger_type = text(start.find(f"{NS}triggerType"))
    if trigger_type not in {"RecordAfterSave", "RecordBeforeSave"}:
        return issues
    record_trigger_type = text(start.find(f"{NS}recordTriggerType"))  # Create / Update / CreateAndUpdate
    trigger_object = text(start.find(f"{NS}object"))

    # 1. Over-broad triggers
    has_filters = bool(start.findall(f"{NS}filters")) or bool(text(start.find(f"{NS}filterFormula")))
    if record_trigger_type in {"Update", "CreateAndUpdate"} and not has_filters:
        issues.append(
            f"{path}: record-triggered Flow on `{trigger_object}` has no entry filter. "
            "Update / CreateAndUpdate without conditions is a recursion risk."
        )

    # 2. Self-re-entry: Flow writes a field that's in its own start filter
    if trigger_object:
        written = find_record_update_targets(root, trigger_object)
        filtered = find_filter_fields(start)
        intersect = written & filtered
        for fld in intersect:
            if not has_state_guard(start, fld):
                issues.append(
                    f"{path}: Flow on `{trigger_object}` writes `{fld}` and references it in the entry filter "
                    "without a paired `<>` state guard — possible self-re-entry. "
                    "Pair ISCHANGED with a tracking-field comparison."
                )

    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not (root / "force-app").exists():
        print(f"ERROR: no force-app/ directory under {root}", file=sys.stderr)
        return 1

    issues: list[str] = []
    for f in flow_files(root):
        issues.extend(check_flow(f))

    if not issues:
        print("[recursion-and-re-entry-prevention] no issues found")
        return 0
    for i in issues:
        print(f"WARN: {i}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
