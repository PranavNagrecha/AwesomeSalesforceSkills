#!/usr/bin/env python3
"""Check Flow metadata for common subflow reuse issues."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for common subflow contract and reuse issues.",
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


def check_subflows_and_reusability(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        root = parse_xml(flow_path)
        if root is None:
            issues.append(f"{flow_path}: unable to parse flow metadata.")
            continue

        subflows = [element for element in root.iter() if local_name(element.tag) == "subflows"]
        if not subflows:
            continue

        if len(subflows) > 3:
            issues.append(
                f"{flow_path}: contains {len(subflows)} subflow calls; review whether the flow has been over-decomposed."
            )

        for subflow in subflows:
            label = child_text(subflow, "label") or child_text(subflow, "name") or "<unnamed subflow>"
            input_count = sum(1 for child in subflow if local_name(child.tag) == "inputAssignments")
            output_count = sum(1 for child in subflow if local_name(child.tag) == "outputAssignments")
            has_fault = any(local_name(child.tag) == "faultConnector" for child in subflow)

            if input_count + output_count == 0:
                issues.append(
                    f"{flow_path}: subflow `{label}` has no explicit input or output assignments; confirm the reusable contract is intentional."
                )
            if input_count > 6 or output_count > 4:
                issues.append(
                    f"{flow_path}: subflow `{label}` has a wide contract ({input_count} inputs, {output_count} outputs); review whether the child boundary is too broad."
                )
            if not has_fault:
                issues.append(
                    f"{flow_path}: subflow `{label}` has no fault connector; review how caller failure is handled."
                )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_subflows_and_reusability(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
