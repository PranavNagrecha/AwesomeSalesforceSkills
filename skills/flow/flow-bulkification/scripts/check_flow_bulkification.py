#!/usr/bin/env python3
"""Checker script for Flow Bulkification skill."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow Bulkification configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def text_of(element: ET.Element, child_name: str) -> str:
    for child in element:
        if local_name(child.tag) == child_name and child.text:
            return child.text.strip()
    return ""


def parse_flow(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def check_flow_bulkification(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    flow_paths = sorted(manifest_dir.rglob("*.flow-meta.xml"))
    for flow_path in flow_paths:
        root = parse_flow(flow_path)
        if root is None:
            issues.append(f"{flow_path}: unable to parse flow metadata.")
            continue

        loop_names = {
            text_of(elem, "name")
            for elem in root.iter()
            if local_name(elem.tag) == "loops" and text_of(elem, "name")
        }
        if not loop_names:
            continue

        risk_tags = {"recordLookups", "recordCreates", "recordUpdates", "recordDeletes", "actionCalls", "subflows"}
        risky_targets: list[str] = []

        for elem in root.iter():
            tag = local_name(elem.tag)
            name = text_of(elem, "name")
            targets = {
                child.text.strip()
                for child in elem.iter()
                if local_name(child.tag) == "targetReference" and child.text
            }
            if tag in risk_tags and name and targets & loop_names:
                risky_targets.append(f"{tag}:{name}")

        if risky_targets:
            issues.append(
                f"{flow_path}: data or action elements appear immediately after a loop ({', '.join(sorted(risky_targets))}); confirm no query, DML, Apex action, or subflow runs per iteration."
            )
            continue

        data_element_count = sum(
            1 for elem in root.iter() if local_name(elem.tag) in risk_tags
        )
        if data_element_count >= 3:
            issues.append(
                f"{flow_path}: flow contains {len(loop_names)} loop(s) and {data_element_count} data/action elements; review for hidden bulkification risks even if operations are not directly attached to the loop."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_flow_bulkification(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
