#!/usr/bin/env python3
"""Checker script for Auto-Launched Flow Patterns skill.

Scans a Salesforce DX project directory for common auto-launched Flow
invocation anti-patterns:

  1. Flow.Interview.createInterview() called inside a for-loop in Apex
     (causes SOQL/DML governor limit multiplication in bulk contexts).
  2. Auto-launched Flow metadata files that have DML elements without
     a faultConnector defined (unhandled faults propagate as FlowException).
  3. Flow API names used in Apex that do not match any Flow metadata file
     found in the manifest directory (stale or mismatched API names).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_auto_launched_flow_patterns.py [--help]
    python3 check_auto_launched_flow_patterns.py --manifest-dir path/to/sfdx/project
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FLOW_INTERVIEW_PATTERN = re.compile(
    r"Flow\.Interview\.createInterview\s*\(\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)

# Salesforce Flow metadata XML namespace
FLOW_NS = "http://soap.sforce.com/2006/04/metadata"

# Element local names that perform DML and should have a faultConnector
DML_ELEMENT_TYPES = {
    "recordCreates",
    "recordUpdates",
    "recordDeletes",
    "apexPluginCalls",
    "actionCalls",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ns(tag: str) -> str:
    """Return a fully-qualified XML tag for the Salesforce Flow namespace."""
    return f"{{{FLOW_NS}}}{tag}"


def find_files(root: Path, glob: str) -> list[Path]:
    return sorted(root.rglob(glob))


# ---------------------------------------------------------------------------
# Check 1: Flow.Interview called inside a for-loop in Apex
# ---------------------------------------------------------------------------

def check_apex_loop_invocations(manifest_dir: Path) -> list[str]:
    """Return issues where Flow.Interview.createInterview is inside a for-loop."""
    issues: list[str] = []

    for apex_file in find_files(manifest_dir, "*.cls"):
        source = apex_file.read_text(encoding="utf-8", errors="replace")

        # Detect for-loop blocks that contain Flow.Interview calls.
        # Strategy: find for( ... ) { ... } blocks and check if
        # Flow.Interview.createInterview appears within them.
        # This is a heuristic — brace-counting scanner.
        lines = source.splitlines()
        in_for_loop = False
        brace_depth_at_for = 0
        current_depth = 0
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Track brace depth
            current_depth += stripped.count("{") - stripped.count("}")

            # Detect for-loop opener
            if re.search(r"\bfor\s*\(", stripped):
                in_for_loop = True
                brace_depth_at_for = current_depth

            if in_for_loop:
                if FLOW_INTERVIEW_PATTERN.search(stripped):
                    issues.append(
                        f"{apex_file}:{lineno}: Flow.Interview.createInterview() "
                        f"appears to be inside a for-loop. This multiplies SOQL/DML "
                        f"by record count and will hit governor limits in bulk contexts. "
                        f"Pass a collection variable and call start() once instead."
                    )
                # Exit for-loop scope when depth returns to pre-for level
                if current_depth < brace_depth_at_for:
                    in_for_loop = False

    return issues


# ---------------------------------------------------------------------------
# Check 2: DML elements in auto-launched Flows without a faultConnector
# ---------------------------------------------------------------------------

def check_flow_fault_connectors(manifest_dir: Path) -> list[str]:
    """Return issues for auto-launched Flow metadata missing fault connectors on DML elements."""
    issues: list[str] = []

    for flow_file in find_files(manifest_dir, "*.flow-meta.xml"):
        try:
            tree = ET.parse(flow_file)
        except ET.ParseError as exc:
            issues.append(f"{flow_file}: XML parse error — {exc}")
            continue

        root = tree.getroot()

        # Only check auto-launched flows (processType = AutoLaunchedFlow)
        process_type_el = root.find(_ns("processType"))
        if process_type_el is None or process_type_el.text != "AutoLaunchedFlow":
            continue

        for element_type in DML_ELEMENT_TYPES:
            for element in root.findall(_ns(element_type)):
                name_el = element.find(_ns("name"))
                element_name = name_el.text if name_el is not None else "<unnamed>"
                fault_connector = element.find(_ns("faultConnector"))
                if fault_connector is None:
                    issues.append(
                        f"{flow_file}: Element '{element_name}' ({element_type}) "
                        f"has no faultConnector. Unhandled faults propagate as "
                        f"System.FlowException and roll back the calling transaction. "
                        f"Add a Fault path that logs {{!$Flow.FaultMessage}}."
                    )

    return issues


# ---------------------------------------------------------------------------
# Check 3: Flow API names in Apex that do not match deployed Flow metadata
# ---------------------------------------------------------------------------

def check_flow_api_name_references(manifest_dir: Path) -> list[str]:
    """Return issues where Apex references a Flow API name with no matching metadata file."""
    issues: list[str] = []

    # Collect all deployed Flow API names from metadata filenames
    deployed_flow_names: set[str] = set()
    for flow_file in find_files(manifest_dir, "*.flow-meta.xml"):
        # Filename pattern: <FlowApiName>.flow-meta.xml
        api_name = flow_file.name.replace(".flow-meta.xml", "")
        deployed_flow_names.add(api_name)

    if not deployed_flow_names:
        # No Flow metadata found — skip this check (may not be an SFDX project)
        return issues

    for apex_file in find_files(manifest_dir, "*.cls"):
        source = apex_file.read_text(encoding="utf-8", errors="replace")
        for match in FLOW_INTERVIEW_PATTERN.finditer(source):
            referenced_name = match.group(1)
            if referenced_name not in deployed_flow_names:
                line_num = source[: match.start()].count("\n") + 1
                issues.append(
                    f"{apex_file}:{line_num}: Flow API name '{referenced_name}' "
                    f"referenced in Flow.Interview.createInterview() does not match "
                    f"any Flow metadata file found under '{manifest_dir}'. "
                    f"API names are case-sensitive. Verify the exact name in Setup > Flows."
                )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce DX project for auto-launched Flow invocation "
            "anti-patterns: loop invocations, missing fault connectors, and "
            "stale Flow API name references."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


def check_auto_launched_flow_patterns(manifest_dir: Path) -> list[str]:
    """Return all issues found across all checks."""
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    issues: list[str] = []
    issues.extend(check_apex_loop_invocations(manifest_dir))
    issues.extend(check_flow_fault_connectors(manifest_dir))
    issues.extend(check_flow_api_name_references(manifest_dir))
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_auto_launched_flow_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
