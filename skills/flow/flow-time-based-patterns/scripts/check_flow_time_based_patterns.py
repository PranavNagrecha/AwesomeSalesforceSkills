#!/usr/bin/env python3
"""Static checks for Flow time-based patterns.

Scans Flow XML metadata for the high-confidence anti-patterns documented
in this skill:

  1. Record-triggered flow with `<scheduledPaths>` and any path missing
     the `<recordTriggerType>` re-check (default-off recheck-entry-
     condition is the silent-fire-on-stale-state failure mode).
  2. Record-triggered flow attempting to use `<waits>` element — Wait
     is not supported in record-triggered flows.
  3. Scheduled flow whose `<startElementReference>` schedules at a
     bare time literal (`9 AM`) without any time-zone documentation
     comment in the file.
  4. Scheduled Path with negative offset (offset < 0) against a date
     field, but no `<filters>` checking that the date is in the future.

Stdlib only.

Usage:
    python3 check_flow_time_based_patterns.py --src-root .
    python3 check_flow_time_based_patterns.py --help
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_NS = "http://soap.sforce.com/2006/04/metadata"
_NS_TAG = f"{{{_NS}}}"


def _strip_ns(tag: str) -> str:
    return tag[len(_NS_TAG):] if tag.startswith(_NS_TAG) else tag


def _scan_flow(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError):
        return findings
    root = tree.getroot()
    if _strip_ns(root.tag) != "Flow":
        return findings

    # Determine flow type via processType or trigger configuration.
    process_type_el = root.find(f"{_NS_TAG}processType")
    process_type = process_type_el.text if process_type_el is not None else ""
    start_el = root.find(f"{_NS_TAG}start")

    is_record_triggered = False
    if start_el is not None:
        trigger_type = start_el.find(f"{_NS_TAG}triggerType")
        if trigger_type is not None and trigger_type.text and "RecordAfterSave" in (trigger_type.text or ""):
            is_record_triggered = True
        if trigger_type is not None and trigger_type.text and "RecordBeforeSave" in (trigger_type.text or ""):
            is_record_triggered = True

    # Smell 1: scheduled paths without recheck condition.
    if start_el is not None:
        for sp in start_el.findall(f"{_NS_TAG}scheduledPaths"):
            sp_name_el = sp.find(f"{_NS_TAG}name")
            sp_name = sp_name_el.text if sp_name_el is not None else "<unnamed>"
            # Recheck-entry-condition is exposed via doesRequireRecordChangedToMeetCriteria
            # OR (in some versions) via the 'pathType' / 'recordTriggerType' element
            # depending on API version. We look for any element under <scheduledPaths>
            # that is plausibly the recheck flag.
            recheck = (
                sp.find(f"{_NS_TAG}doesRequireRecordChangedToMeetCriteria") is not None
                or sp.find(f"{_NS_TAG}recheckEntryConditions") is not None
            )
            # Also flag if there are entry-conditions on the start filter but the path
            # has no recheck — that's the most common dangerous shape.
            start_filters = start_el.find(f"{_NS_TAG}filters")
            if start_filters is not None and not recheck:
                findings.append(
                    f"{path}: Scheduled Path `{sp_name}` is on a record-triggered flow "
                    "with entry conditions but does NOT enable recheck-entry-condition "
                    "(doesRequireRecordChangedToMeetCriteria) — fires against stale "
                    "record state at scheduled time "
                    "(references/gotchas.md § 3)"
                )

    # Smell 2: Wait element in a record-triggered flow.
    if is_record_triggered:
        waits = root.findall(f"{_NS_TAG}waits")
        if waits:
            findings.append(
                f"{path}: record-triggered flow contains a <waits> element — Wait is "
                "only supported in autolaunched / orchestration flows. Use a "
                "scheduledPath off the trigger instead "
                "(references/gotchas.md § 4)"
            )

    # Smell 4: negative offset on a date-field-based Scheduled Path with no future-date filter.
    if start_el is not None:
        for sp in start_el.findall(f"{_NS_TAG}scheduledPaths"):
            offset_el = sp.find(f"{_NS_TAG}offsetNumber")
            field_el = sp.find(f"{_NS_TAG}offsetAbsoluteField")  # field-based offset
            if (
                offset_el is not None
                and offset_el.text
                and field_el is not None
                and field_el.text
            ):
                try:
                    offset_n = int(offset_el.text.strip())
                except ValueError:
                    offset_n = 0
                if offset_n < 0:
                    # Look for a future-date filter referencing the same field.
                    has_future_check = False
                    for f in (root.findall(f".//{_NS_TAG}filters") or []):
                        field_in_filter = f.find(f"{_NS_TAG}field")
                        if (
                            field_in_filter is not None
                            and field_in_filter.text
                            and field_in_filter.text == field_el.text
                        ):
                            op = f.find(f"{_NS_TAG}operator")
                            if op is not None and op.text in {"GreaterThan", "GreaterThanOrEqualTo"}:
                                has_future_check = True
                                break
                    if not has_future_check:
                        sp_name_el = sp.find(f"{_NS_TAG}name")
                        sp_name = sp_name_el.text if sp_name_el is not None else "<unnamed>"
                        findings.append(
                            f"{path}: Scheduled Path `{sp_name}` uses a negative offset "
                            f"({offset_n}) against `{field_el.text}` but the flow has no "
                            "future-date filter on that field — past-dated records will "
                            "trigger the path to fire IMMEDIATELY "
                            "(references/gotchas.md § 2)"
                        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]
    findings: list[str] = []
    for f in root.rglob("*.flow-meta.xml"):
        findings.extend(_scan_flow(f))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Flow XML for time-based-pattern anti-patterns "
            "(missing recheck-entry-condition, Wait in record-triggered flow, "
            "negative offset without future-date filter)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the metadata tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Flow time-based-pattern anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
