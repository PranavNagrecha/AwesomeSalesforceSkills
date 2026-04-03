#!/usr/bin/env python3
"""Check Flow screen metadata and related LWCs for common UX issues."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


VALIDATE_RE = re.compile(r"\bvalidate\s*\(", re.IGNORECASE)
SET_CUSTOM_VALIDITY_RE = re.compile(r"\bsetCustomValidity\s*\(", re.IGNORECASE)
REPORT_VALIDITY_RE = re.compile(r"\breportValidity\s*\(", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check screen flows and related custom components for common UX issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or source tree (default: current directory).",
    )
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_xml(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError:
        return None


def find_component_texts(screen_element: ET.Element) -> list[str]:
    names: list[str] = []
    for child in screen_element.iter():
        if local_name(child.tag) == "componentName" and child.text:
            names.append(child.text.strip())
    return names


def find_lwc_js(root: Path, component_name: str) -> Path | None:
    bare_name = component_name.split(":")[-1]
    for candidate in root.rglob(f"{bare_name}.js"):
        return candidate
    return None


def check_screen_flows(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    risky_tags = {"recordCreates", "recordUpdates", "recordDeletes"}

    for flow_path in sorted(manifest_dir.rglob("*.flow-meta.xml")):
        root = parse_xml(flow_path)
        if root is None:
            issues.append(f"{flow_path}: unable to parse flow metadata.")
            continue

        screens = [element for element in root.iter() if local_name(element.tag) == "screens"]
        if not screens:
            continue

        if len(screens) > 4:
            issues.append(
                f"{flow_path}: contains {len(screens)} screens; review whether the interview has become too fragmented."
            )

        if any(local_name(element.tag) in risky_tags for element in root.iter()):
            issues.append(
                f"{flow_path}: screen flow contains record mutation elements; review whether commit timing is appropriately late in the interview."
            )

        for screen in screens:
            for component_name in find_component_texts(screen):
                js_path = find_lwc_js(manifest_dir, component_name)
                if js_path is None:
                    issues.append(
                        f"{flow_path}: custom screen component `{component_name}` was referenced but no matching JS file was found for validation review."
                    )
                    continue
                text = js_path.read_text(encoding="utf-8", errors="ignore")
                if not (VALIDATE_RE.search(text) and (SET_CUSTOM_VALIDITY_RE.search(text) or REPORT_VALIDITY_RE.search(text))):
                    issues.append(
                        f"{js_path}: custom Flow screen component may be missing part of the Flow validation contract (`validate`, `setCustomValidity`, or `reportValidity`)."
                    )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_screen_flows(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
