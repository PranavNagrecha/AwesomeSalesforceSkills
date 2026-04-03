#!/usr/bin/env python3
"""Check Flow metadata for common governance and naming issues."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


GENERIC_NAME_RE = re.compile(r"(new flow|copy|test|temp|old|backup)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Flow metadata for naming, description, and operational-governance issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def first_text(root: ET.Element, name: str) -> str:
    for element in root.iter():
        if local_name(element.tag) == name and element.text:
            return element.text.strip()
    return ""


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def flow_base_name(path: Path) -> str:
    name = path.name
    suffix = ".flow-meta.xml"
    return name[:-len(suffix)] if name.endswith(suffix) else path.stem


def check_flow_governance(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        root = parse_xml(flow_path)
        if root is None:
            issues.append(f"{flow_path}: unable to parse flow metadata.")
            continue

        base_name = flow_base_name(flow_path)
        label = first_text(root, "label")
        description = first_text(root, "description")
        interview_label = first_text(root, "interviewLabel")

        if GENERIC_NAME_RE.search(base_name) or (label and GENERIC_NAME_RE.search(label)):
            issues.append(
                f"{flow_path}: generic naming detected in API name or label; review whether the flow is production-readable."
            )
        if not description:
            issues.append(
                f"{flow_path}: missing flow description; add business purpose and operational context."
            )
        if any(local_name(element.tag) == "screens" for element in root.iter()) and not interview_label:
            issues.append(
                f"{flow_path}: screen flow appears to be missing an `interviewLabel`; review runtime readability for support."
            )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_flow_governance(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
