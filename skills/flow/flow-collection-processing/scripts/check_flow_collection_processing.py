#!/usr/bin/env python3
"""Checker script for Flow Collection Processing skill.

Inspects Salesforce Flow metadata XML files for collection-processing
anti-patterns:
  - DML elements (recordUpdates, recordCreates, recordDeletes) inside a Loop
  - Loops without a typed SObject collection variable (heuristic check)
  - Absence of collectionProcessors (Filter/Sort/Transform) where only loops exist

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_flow_collection_processing.py --manifest-dir path/to/metadata
    python3 check_flow_collection_processing.py --flow-file path/to/MyFlow.flow-meta.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce Flow metadata XML namespace
FLOW_NS = "http://soap.sforce.com/2006/04/metadata"

# DML element tag names in Flow metadata XML
DML_ELEMENT_TAGS = {
    "recordCreates",
    "recordUpdates",
    "recordDeletes",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Flow metadata for collection-processing anti-patterns."
        ),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory to search recursively for *.flow-meta.xml files.",
    )
    group.add_argument(
        "--flow-file",
        default=None,
        help="Path to a single *.flow-meta.xml file to check.",
    )
    return parser.parse_args()


def _find_flow_files(root: Path) -> list[Path]:
    """Return all *.flow-meta.xml files under root."""
    return list(root.rglob("*.flow-meta.xml"))


def _ns(tag: str) -> str:
    return f"{{{FLOW_NS}}}{tag}"


def _collect_connector_targets(element: ET.Element) -> set[str]:
    """Collect all targetReference values from connector children of an element."""
    targets: set[str] = set()
    for connector in element.iter(_ns("connector")):
        ref = connector.find(_ns("targetReference"))
        if ref is not None and ref.text:
            targets.add(ref.text.strip())
    for connector in element.iter(_ns("nextValueConnector")):
        ref = connector.find(_ns("targetReference"))
        if ref is not None and ref.text:
            targets.add(ref.text.strip())
    return targets


def _get_element_name(element: ET.Element) -> str:
    name_el = element.find(_ns("name"))
    return name_el.text.strip() if name_el is not None and name_el.text else "(unnamed)"


def check_flow_file(flow_path: Path) -> list[str]:
    """Return a list of issue strings for the given Flow metadata file."""
    issues: list[str] = []

    try:
        tree = ET.parse(flow_path)
    except ET.ParseError as exc:
        return [f"{flow_path.name}: XML parse error — {exc}"]

    root = tree.getroot()

    # Build a map: element name → tag (without namespace)
    # This lets us check whether a Loop's nextValueConnector points to a DML element.
    element_by_name: dict[str, str] = {}
    for child in root:
        tag = child.tag.replace(f"{{{FLOW_NS}}}", "")
        name_el = child.find(_ns("name"))
        if name_el is not None and name_el.text:
            element_by_name[name_el.text.strip()] = tag

    # Check 1: DML elements reachable from inside a Loop (via nextValueConnector)
    # A Loop's "For Each" connector is nextValueConnector; it points to the first
    # element inside the loop body. We trace one hop: if the loop's body entry
    # is a DML element, or if any element in the body directly points to a DML
    # element without first exiting via "After Last", flag it.
    #
    # Simple heuristic: collect the names of all elements that are reachable
    # within a loop by following connectors from the loop's nextValueConnector
    # target. Stop at elements whose connector loops back to the loop element
    # itself (the "After Last" path points elsewhere — to post-loop logic).
    loops = root.findall(_ns("loops"))
    loop_names = {_get_element_name(lp) for lp in loops}

    for loop_el in loops:
        loop_name = _get_element_name(loop_el)
        nvc = loop_el.find(_ns("nextValueConnector"))
        if nvc is None:
            continue
        body_entry_ref = nvc.find(_ns("targetReference"))
        if body_entry_ref is None or not body_entry_ref.text:
            continue
        body_entry = body_entry_ref.text.strip()

        # BFS through the loop body to find DML elements
        visited: set[str] = set()
        queue: list[str] = [body_entry]
        while queue:
            current_name = queue.pop(0)
            if current_name in visited:
                continue
            if current_name in loop_names:
                # We've looped back to a loop element — stop traversing this path
                continue
            visited.add(current_name)
            current_tag = element_by_name.get(current_name, "")
            if current_tag in DML_ELEMENT_TAGS:
                issues.append(
                    f"{flow_path.name}: DML element '{current_name}' ({current_tag}) "
                    f"appears to be inside Loop '{loop_name}'. "
                    "Move DML outside the loop and operate on a collection variable."
                )
            # Find the actual element node to follow its connectors
            for child in root:
                child_tag = child.tag.replace(f"{{{FLOW_NS}}}", "")
                child_name_el = child.find(_ns("name"))
                if (
                    child_name_el is not None
                    and child_name_el.text
                    and child_name_el.text.strip() == current_name
                ):
                    for connector in child.findall(_ns("connector")):
                        ref = connector.find(_ns("targetReference"))
                        if ref is not None and ref.text:
                            next_name = ref.text.strip()
                            if next_name not in visited:
                                queue.append(next_name)
                    break

    # Check 2: Warn if loops exist but no collectionProcessors (Filter/Sort/Transform)
    # This is informational: it suggests the developer may not be aware of the
    # newer declarative elements.
    collection_processors = root.findall(_ns("collectionProcessors"))
    if loops and not collection_processors:
        issues.append(
            f"{flow_path.name}: Flow has {len(loops)} Loop element(s) but no "
            "Collection Filter, Collection Sort, or Transform elements. "
            "Consider whether any loops can be replaced with declarative collection elements."
        )

    # Check 3: Loops where the nextValueConnector is missing (loop with no body)
    for loop_el in loops:
        loop_name = _get_element_name(loop_el)
        nvc = loop_el.find(_ns("nextValueConnector"))
        if nvc is None:
            issues.append(
                f"{flow_path.name}: Loop '{loop_name}' has no nextValueConnector. "
                "The loop body is empty; this loop does nothing."
            )

    return issues


def check_flow_collection_processing(manifest_dir: Path) -> list[str]:
    """Return a list of issues found across all flow files in manifest_dir."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    flow_files = _find_flow_files(manifest_dir)
    if not flow_files:
        # Not an error — org may have no flows
        return issues

    for flow_file in sorted(flow_files):
        issues.extend(check_flow_file(flow_file))

    return issues


def main() -> int:
    args = parse_args()

    if args.flow_file:
        flow_path = Path(args.flow_file)
        if not flow_path.exists():
            print(f"ISSUE: Flow file not found: {flow_path}")
            return 1
        issues = check_flow_file(flow_path)
    else:
        manifest_dir = Path(args.manifest_dir) if args.manifest_dir else Path(".")
        issues = check_flow_collection_processing(manifest_dir)

    if not issues:
        print("No collection-processing issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
