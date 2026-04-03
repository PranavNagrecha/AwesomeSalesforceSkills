#!/usr/bin/env python3
"""Check schedule-triggered Flow metadata for common scope and reliability issues."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


SCHEDULE_MARKERS = ("<schedule>", "frequency", "scheduled", "scheduledpaths", "scheduletriggered")
RISKY_TAGS = {"recordLookups", "recordCreates", "recordUpdates", "recordDeletes", "actionCalls", "subflows"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check scheduled flows for broad scope, weak fault handling, and batch-style design smells.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(element: ET.Element, name: str) -> str:
    for child in element:
        if local_name(child.tag) == name and child.text:
            return child.text.strip()
    return ""


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def looks_scheduled(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in SCHEDULE_MARKERS)


def check_scheduled_flows(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        raw_text = flow_path.read_text(encoding="utf-8", errors="ignore")
        if not looks_scheduled(raw_text):
            continue

        root = parse_xml(flow_path)
        if root is None:
            issues.append(f"{flow_path}: unable to parse flow metadata.")
            continue

        lower = raw_text.lower()
        if "<filters>" not in lower and "<filterlogic>" not in lower:
            issues.append(
                f"{flow_path}: scheduled flow appears to have no obvious filter metadata; review whether the record scope is too broad."
            )

        loop_count = sum(1 for element in root.iter() if local_name(element.tag) == "loops")
        risky_count = sum(1 for element in root.iter() if local_name(element.tag) in RISKY_TAGS)
        if loop_count and risky_count >= 3:
            issues.append(
                f"{flow_path}: scheduled flow contains {loop_count} loop(s) and {risky_count} data or action elements; review whether the workload belongs in Batch Apex."
            )

        for element in root.iter():
            if local_name(element.tag) not in {"actionCalls", "subflows"}:
                continue
            label = child_text(element, "label") or child_text(element, "name") or "<unnamed element>"
            has_fault = any(local_name(child.tag) == "faultConnector" for child in element)
            if not has_fault:
                issues.append(
                    f"{flow_path}: scheduled element `{label}` has no fault connector; background automation should fail observably."
                )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_scheduled_flows(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
