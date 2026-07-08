#!/usr/bin/env python3
"""Checker script for Record Triggered Flow Patterns skill."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

SAVE_PHASES = ("RecordBeforeSave", "RecordAfterSave")


def _start_block(text: str) -> str:
    match = re.search(r"<start>(.*?)</start>", text, re.DOTALL)
    return match.group(1) if match else ""


def _tag_value(text: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else None


def _trigger_order(text: str) -> int | None:
    """triggerOrder may sit on the Flow or inside <start>; search the whole file."""
    raw = _tag_value(text, "triggerOrder")
    if raw is None or not raw.isdigit():
        return None
    return int(raw)


def check_trigger_order(
    phases: dict[tuple[str, str], list[tuple[Path, int | None]]],
) -> list[str]:
    """Trigger order only sequences flows within one object + save phase.

    Salesforce runs values 1-1,000 ascending, then flows with no value in
    created-date order, then values 1,001-2,000 ascending. Mixing set and
    unset values in one phase therefore produces an ordering almost nobody
    intends, and ties fall back to alphabetical API name.
    """
    issues: list[str] = []

    for (sobject, phase), flows in sorted(phases.items()):
        if len(flows) < 2:
            continue

        ordered = [(path, order) for path, order in flows if order is not None]
        unordered = [path for path, order in flows if order is None]

        if ordered and unordered:
            names = ", ".join(str(path) for path in sorted(unordered))
            issues.append(
                f"{sobject} ({phase}): {len(flows)} flows in this phase, but these have no triggerOrder: {names}. "
                "Unset flows run between the 1-1,000 and 1,001-2,000 bands, not last; set a value on every flow in the phase."
            )
        elif not ordered:
            issues.append(
                f"{sobject} ({phase}): {len(flows)} flows in this phase and none set triggerOrder; "
                "run order falls back to created date. Consolidate, or assign explicit values spaced in tens."
            )

        by_value: dict[int, list[Path]] = defaultdict(list)
        for path, order in ordered:
            by_value[order].append(path)
        for value, paths in sorted(by_value.items()):
            if len(paths) > 1:
                names = ", ".join(str(path) for path in sorted(paths))
                issues.append(
                    f"{sobject} ({phase}): triggerOrder {value} is shared by {names}. "
                    "Ties resolve alphabetically by API name, so renaming a flow silently reorders execution."
                )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Record Triggered Flow Patterns configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_record_triggered_flow_patterns(manifest_dir: Path) -> list[str]:
    issues: list[str] = []
    phases: dict[tuple[str, str], list[tuple[Path, int | None]]] = defaultdict(list)

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        text = flow_path.read_text(encoding="utf-8", errors="ignore")
        if "RecordBeforeSave" not in text and "RecordAfterSave" not in text:
            continue

        start = _start_block(text)
        sobject = _tag_value(start, "object")
        trigger_type = _tag_value(start, "triggerType")
        if sobject and trigger_type in SAVE_PHASES:
            phases[(sobject, trigger_type)].append((flow_path, _trigger_order(text)))

        if "RecordAfterSave" in text and "<recordUpdates>" in text and "$Record" in text:
            issues.append(
                f"{flow_path}: after-save flow appears to update the triggering record; review for recursion and consider before-save if only same-record fields change."
            )

        if "RecordBeforeSave" in text:
            forbidden = ("<recordCreates>", "<recordDeletes>", "<actionCalls>", "<subflows>")
            if any(marker in text for marker in forbidden):
                issues.append(
                    f"{flow_path}: before-save flow contains creates, deletes, action calls, or subflows; verify the design belongs in after-save or Apex."
                )

        if not re.search(r"(Record__Prior|PriorValue|ISCHANGED|isChanged)", text):
            issues.append(
                f"{flow_path}: record-triggered flow has no obvious prior-value or changed-field logic; confirm the start criteria are not broader than the business event."
            )

    issues.extend(check_trigger_order(phases))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_record_triggered_flow_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
