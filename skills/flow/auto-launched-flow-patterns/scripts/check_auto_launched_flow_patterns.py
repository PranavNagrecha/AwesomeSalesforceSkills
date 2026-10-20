#!/usr/bin/env python3
"""Checker script for Auto-Launched Flow Patterns skill.

Scans a Salesforce DX project directory for:
  1. Flow.Interview.createInterview() inside an Apex for-loop (each start() repeats the Flow's
     SOQL/DML against the shared 100/150 limits; apexref 262 L157938, apexdev 264 L19747, L19757).
  2. AutoLaunchedFlow metadata whose Get/Create/Update/Delete Records, action or Apex plug-in
     elements have no faultConnector (faultConnector exists on these elements, api_meta 264
     L71010, L72278, L73697, L73777, L73843, L74007).
  3. createInterview() flow names with no matching *.flow-meta.xml (apexref 262 L158086: a missing
     flow throws TypeException). Case sensitivity is undocumented, so a name that differs only
     in case is reported as a near match, not as proof of a mismatch.

Severity contract: ERROR (unparseable Flow XML, missing directory) exits 1 always. REVIEW and WARN
findings exit 0 unless --strict. An empty directory is one WARN, exit 0.

Uses stdlib only. Usage:
    python3 check_auto_launched_flow_patterns.py --manifest-dir path/to/sfdx/project [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Matches createInterview('Flow', ...) and the namespaced overload createInterview('ns', 'Flow', ...)
# (apexref 262 L158043-158049); group 2, when present, is the flow name.
FLOW_INTERVIEW_PATTERN = re.compile(
    r"Flow\.Interview\.createInterview\s*\(\s*['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?", re.MULTILINE
)
FLOW_NS = "http://soap.sforce.com/2006/04/metadata"
FAULT_ELEMENT_TYPES = ("recordLookups", "recordCreates", "recordUpdates", "recordDeletes", "apexPluginCalls", "actionCalls")


def _ns(tag: str) -> str:
    return f"{{{FLOW_NS}}}{tag}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a DX project for auto-launched Flow invocation anti-patterns.")
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the DX project (default: .).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on REVIEW/WARN findings too.")
    return parser.parse_args()


def check_apex_loop_invocations(files: list[Path]) -> list[str]:
    issues: list[str] = []
    for apex_file in files:
        in_for_loop = False
        depth_at_for = 0
        depth = 0
        for lineno, line in enumerate(apex_file.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            stripped = line.strip()
            depth += stripped.count("{") - stripped.count("}")
            if re.search(r"\bfor\s*\(", stripped):
                in_for_loop = True
                depth_at_for = depth
            if in_for_loop:
                if FLOW_INTERVIEW_PATTERN.search(stripped):
                    issues.append(
                        f"REVIEW: {apex_file}:{lineno}: createInterview() appears inside a for-loop; each start() repeats the Flow's "
                        f"SOQL/DML against the shared limits. Pass a collection variable and call start() once."
                    )
                if depth < depth_at_for:
                    in_for_loop = False
    return issues


def check_flow_fault_connectors(flow_files: list[Path], errors: list[str]) -> list[str]:
    issues: list[str] = []
    for flow_file in flow_files:
        try:
            root = ET.parse(flow_file).getroot()
        except ET.ParseError as exc:
            errors.append(f"ERROR: {flow_file}: XML parse error: {exc}")
            continue
        process_type = root.find(_ns("processType"))
        if process_type is None or (process_type.text or "").strip() != "AutoLaunchedFlow":
            continue
        for element_type in FAULT_ELEMENT_TYPES:
            for element in root.findall(_ns(element_type)):
                name_el = element.find(_ns("name"))
                name = (name_el.text or "<unnamed>") if name_el is not None else "<unnamed>"
                if element.find(_ns("faultConnector")) is None:
                    issues.append(f"REVIEW: {flow_file}: element '{name}' ({element_type}) has no faultConnector; a fault there has no handled path.")
    return issues


def check_flow_api_name_references(apex_files: list[Path], flow_files: list[Path]) -> list[str]:
    issues: list[str] = []
    deployed = {f.name.replace(".flow-meta.xml", "") for f in flow_files}
    if not deployed:
        return issues
    lowered = {n.lower(): n for n in deployed}
    for apex_file in apex_files:
        source = apex_file.read_text(encoding="utf-8", errors="replace")
        for match in FLOW_INTERVIEW_PATTERN.finditer(source):
            name = match.group(2) or match.group(1)
            if name in deployed:
                continue
            line_num = source[: match.start()].count("\n") + 1
            if name.lower() in lowered:
                issues.append(f"REVIEW: {apex_file}:{line_num}: '{name}' differs only in case from flow '{lowered[name.lower()]}'; case sensitivity is undocumented, match it exactly.")
            else:
                issues.append(f"REVIEW: {apex_file}:{line_num}: flow '{name}' has no *.flow-meta.xml under the project; a missing flow throws TypeException.")
    return issues


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir).resolve()
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    apex_files = sorted(root.rglob("*.cls"))
    flow_files = sorted(root.rglob("*.flow-meta.xml"))
    if not apex_files and not flow_files:
        print(f"WARN: no Apex classes or Flow metadata found under {root}")
        return 1 if args.strict else 0

    errors: list[str] = []
    reviews = check_apex_loop_invocations(apex_files)
    reviews += check_flow_fault_connectors(flow_files, errors)
    reviews += check_flow_api_name_references(apex_files, flow_files)
    for line in errors + reviews:
        print(line)
    if errors:
        return 1
    if reviews:
        return 1 if args.strict else 0
    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
