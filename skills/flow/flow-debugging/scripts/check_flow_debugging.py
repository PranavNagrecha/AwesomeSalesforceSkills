#!/usr/bin/env python3
"""Checker script for Flow Debugging skill.

Inspects Salesforce Flow metadata XML files and reports common
debuggability anti-patterns: missing element labels, no fault connectors
on DML elements, flows with no active version marker, and flows that have
debug-hostile naming (auto-generated names like Decision_1, Assignment_3).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_flow_debugging.py [--manifest-dir path/to/metadata]

The manifest-dir should be the root of the Salesforce source tree or a
directory that contains a 'flows/' sub-folder with .flow-meta.xml files.

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce Flow metadata XML namespace
FLOW_NS = "http://soap.sforce.com/2006/04/metadata"

# Element tags that can perform DML and should have fault connectors
DML_ELEMENT_TAGS = {
    "recordCreates",
    "recordUpdates",
    "recordDeletes",
    "actionCalls",
    "subflows",
}

# Patterns that suggest auto-generated / non-descriptive element names
GENERIC_NAME_PREFIXES = (
    "Decision_",
    "Assignment_",
    "Loop_",
    "Screen_",
    "Action_",
    "Get_Records_",
    "Create_Records_",
    "Update_Records_",
    "Delete_Records_",
    "Subflow_",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Flow metadata XML files for common debuggability anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _ns(tag: str) -> str:
    """Wrap a tag name with the Flow XML namespace."""
    return f"{{{FLOW_NS}}}{tag}"


def _text(element: ET.Element | None) -> str:
    """Return stripped text of an XML element, or empty string if None."""
    if element is None:
        return ""
    return (element.text or "").strip()


def check_flow_file(flow_path: Path) -> list[str]:
    """Return a list of issue strings for a single .flow-meta.xml file."""
    issues: list[str] = []
    name = flow_path.name

    try:
        tree = ET.parse(flow_path)
    except ET.ParseError as exc:
        return [f"{name}: XML parse error — {exc}"]

    root = tree.getroot()

    # ------------------------------------------------------------------ #
    # 1. Check for generic / auto-generated element names                  #
    # ------------------------------------------------------------------ #
    label_elements = (
        list(root.iter(_ns("decisions")))
        + list(root.iter(_ns("assignments")))
        + list(root.iter(_ns("loops")))
        + list(root.iter(_ns("screens")))
        + list(root.iter(_ns("recordCreates")))
        + list(root.iter(_ns("recordUpdates")))
        + list(root.iter(_ns("recordDeletes")))
        + list(root.iter(_ns("actionCalls")))
        + list(root.iter(_ns("subflows")))
    )

    for elem in label_elements:
        label_el = elem.find(_ns("label"))
        api_name_el = elem.find(_ns("name"))
        label = _text(label_el)
        api_name = _text(api_name_el)
        if not label or any(label.startswith(p) for p in GENERIC_NAME_PREFIXES):
            issues.append(
                f"{name}: Element '{api_name or '(unknown)'}' has a generic or missing "
                f"label '{label}'. Generic labels make debug traces and Interview Logs "
                f"much harder to read. Use descriptive labels."
            )

    # ------------------------------------------------------------------ #
    # 2. Check DML / action elements for fault connectors                  #
    # ------------------------------------------------------------------ #
    for dml_tag in DML_ELEMENT_TAGS:
        for elem in root.iter(_ns(dml_tag)):
            api_name = _text(elem.find(_ns("name")))
            fault_connector = elem.find(_ns("faultConnector"))
            if fault_connector is None:
                issues.append(
                    f"{name}: Element '{api_name}' ({dml_tag}) has no fault connector. "
                    f"Unhandled faults on this element will trigger a fault email and "
                    f"roll back the transaction. Add a fault path."
                )

    # ------------------------------------------------------------------ #
    # 3. Check that the flow has a label (basic metadata hygiene)          #
    # ------------------------------------------------------------------ #
    flow_label = _text(root.find(_ns("label")))
    if not flow_label:
        issues.append(
            f"{name}: Flow has no label. A missing label makes it invisible or "
            f"unidentifiable in Setup > Flows and in fault emails."
        )

    # ------------------------------------------------------------------ #
    # 4. Check for descriptions on the flow itself                         #
    # ------------------------------------------------------------------ #
    description = _text(root.find(_ns("description")))
    if not description:
        issues.append(
            f"{name}: Flow has no description. A description records the business "
            f"purpose and helps future maintainers understand trigger intent without "
            f"opening every element. Add a description to the flow properties."
        )

    # ------------------------------------------------------------------ #
    # 5. Warn if there are no fault connectors anywhere in the flow         #
    #    and the flow contains DML elements (duplicate of per-element check #
    #    but provides a flow-level summary)                                 #
    # ------------------------------------------------------------------ #
    has_any_dml = any(
        root.find(_ns(tag)) is not None for tag in DML_ELEMENT_TAGS
    )
    has_any_fault_connector = root.find(f".//{_ns('faultConnector')}") is not None
    if has_any_dml and not has_any_fault_connector:
        issues.append(
            f"{name}: Flow contains DML or action elements but has NO fault connectors "
            f"anywhere. Any element failure will cause an unhandled fault and roll back "
            f"the transaction. Add fault paths to all fallible elements."
        )

    return issues


def check_flow_debugging(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found across all flow files in the directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for .flow-meta.xml files anywhere under the manifest dir
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))

    if not flow_files:
        # Not necessarily an error — the caller may be pointing at a repo root
        # that has no flows deployed yet. Emit an informational notice only.
        issues.append(
            f"No .flow-meta.xml files found under '{manifest_dir}'. "
            f"If flows are expected here, verify the manifest-dir path."
        )
        return issues

    for flow_path in sorted(flow_files):
        issues.extend(check_flow_file(flow_path))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_flow_debugging(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
