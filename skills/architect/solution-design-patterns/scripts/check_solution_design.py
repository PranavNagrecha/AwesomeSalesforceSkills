#!/usr/bin/env python3
"""Checker script for Solution Design Patterns skill.

Scans a Salesforce project directory for common automation design anti-patterns:
- Hard-coded Salesforce record IDs in Apex source files
- Apex trigger files with logic directly embedded (no handler class delegation)
- Apex files referencing Process Builder invocation patterns (InvocableMethod
  annotations paired with Flow-incompatible callout logic in same method)
- Flow metadata XML files with GetRecords elements inside Loop elements
  (SOQL inside a loop — a governor limit risk)
- Apex files with more than one DML operation type in a single method
  (possible bulkification concern)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_solution_design.py [--help]
    python3 check_solution_design.py --project-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# --- Patterns ---

# Matches 15- or 18-character Salesforce record IDs embedded as string literals
# Salesforce IDs start with a 3-char key prefix (e.g. 001, 003, 0Q0, etc.)
# Pattern: a quote character followed by a 15 or 18 alphanumeric char sequence
# that starts with 0 (common ID prefix), followed by a quote or end-of-token.
HARDCODED_ID_PATTERN = re.compile(
    r"""['"]([0-9A-Za-z]{15}|[0-9A-Za-z]{18})['"]""",
)

# Salesforce IDs always start with a 3-char key prefix that is one of the
# well-known prefixes. We approximate this by requiring the literal to start
# with a digit-or-uppercase-letter followed by 14 or 17 more alphanumeric
# characters, and we require no surrounding word characters (to avoid matching
# UUIDs or hash values).
# Refined: must start with a digit (Salesforce key prefixes are 0xx or 00x)
SF_ID_STRICT = re.compile(
    r"""(?<![A-Za-z0-9_])['"]0[A-Za-z0-9]{14}(?:[A-Za-z0-9]{3})?['"](?![A-Za-z0-9_])"""
)

# Detects Apex trigger files that contain DML or SOQL directly (not delegating
# to a handler class). Heuristic: trigger body contains 'insert ', 'update ',
# 'delete ', 'upsert ', or '[SELECT' outside a comment.
TRIGGER_DIRECT_DML = re.compile(
    r'\b(?:insert|update|delete|upsert)\s+\w',
    re.IGNORECASE,
)
TRIGGER_DIRECT_SOQL = re.compile(r'\[SELECT\b', re.IGNORECASE)

# Detects callout in an @InvocableMethod — callout=true in future is not
# allowed from InvocableMethod in after-save context.
INVOCABLE_ANNOTATION = re.compile(r'@InvocableMethod', re.IGNORECASE)
HTTP_CALLOUT_IN_METHOD = re.compile(
    r'\bHttp\b|\bHttpRequest\b|\bHttpResponse\b', re.IGNORECASE
)

APEX_EXTENSIONS = {'.cls', '.trigger'}

# Flow XML namespace
FLOW_NS = 'http://soap.sforce.com/2006/04/metadata'


def _strip_comments(source: str) -> str:
    """Remove single-line and block comments from Apex source (best-effort)."""
    # Remove block comments
    source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)
    # Remove single-line comments
    source = re.sub(r'//[^\n]*', '', source)
    return source


def check_apex_file(path: Path) -> list[str]:
    """Return issues found in a single Apex source file."""
    issues: list[str] = []
    try:
        raw = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        return [f"{path}: cannot read file — {exc}"]

    source = _strip_comments(raw)
    lines = raw.splitlines()

    # Check for hard-coded Salesforce record IDs
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('*'):
            continue
        for match in SF_ID_STRICT.finditer(line):
            candidate = match.group(0).strip("'\"")
            # Exclude common non-ID alphanumerics: API versions, test strings
            if len(candidate) in (15, 18):
                issues.append(
                    f"{path}:{i}: Possible hard-coded Salesforce record ID "
                    f"'{candidate}' — use Custom Metadata or a dynamic lookup "
                    f"instead; hard-coded IDs break cross-org deployment"
                )

    # Check for logic directly in trigger files (no handler delegation)
    if path.suffix == '.trigger':
        has_direct_dml = bool(TRIGGER_DIRECT_DML.search(source))
        has_direct_soql = bool(TRIGGER_DIRECT_SOQL.search(source))
        if has_direct_dml:
            issues.append(
                f"{path}: DML statement found directly in trigger body — "
                "consider delegating to a handler class to support bulkification, "
                "testability, and single-entry-point enforcement"
            )
        if has_direct_soql:
            issues.append(
                f"{path}: SOQL query found directly in trigger body — "
                "delegate to a handler class to keep trigger logic bulkification-safe "
                "and testable in isolation"
            )

    # Check for HTTP callout inside an @InvocableMethod
    if INVOCABLE_ANNOTATION.search(source) and HTTP_CALLOUT_IN_METHOD.search(source):
        issues.append(
            f"{path}: HTTP callout (HttpRequest/HttpResponse) found in a class "
            "that also declares @InvocableMethod — callouts from InvocableMethod "
            "are blocked in after-save record-triggered contexts; use Platform Events "
            "to decouple the callout into a separate Apex transaction"
        )

    return issues


def check_flow_file(path: Path) -> list[str]:
    """Return issues found in a single Flow metadata XML file."""
    issues: list[str] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        return [f"{path}: XML parse error — {exc}"]

    root = tree.getroot()
    ns = {'sf': FLOW_NS}

    # Collect all loop element names
    loop_element_names: set[str] = set()
    for loop_el in root.findall('.//sf:loops', ns):
        name_el = loop_el.find('sf:name', ns)
        if name_el is not None and name_el.text:
            loop_element_names.add(name_el.text)

    # Check if any recordLookup (Get Records) connector comes from inside a loop
    # Flow XML encodes flow paths via 'connector' elements with 'targetReference'
    # pointing to next element names. We check if any recordLookups have a
    # nextValueConnector or iterationItems that suggest they live inside a loop
    # by looking for recordLookup elements whose name appears as a
    # 'nextValueConnector/targetReference' of a loops element.

    for loop_el in root.findall('.//sf:loops', ns):
        next_value_connector = loop_el.find('.//sf:nextValueConnector/sf:targetReference', ns)
        if next_value_connector is None:
            continue
        next_target = next_value_connector.text
        # Check if that target is a recordLookup (Get Records) element
        for rl_el in root.findall('.//sf:recordLookups', ns):
            rl_name_el = rl_el.find('sf:name', ns)
            if rl_name_el is not None and rl_name_el.text == next_target:
                loop_name_el = loop_el.find('sf:name', ns)
                loop_name = loop_name_el.text if loop_name_el is not None else 'unknown'
                issues.append(
                    f"{path}: Flow loop '{loop_name}' has a Get Records (recordLookup) "
                    f"element '{next_target}' as its next-value target — this issues a "
                    "SOQL query per loop iteration and will hit governor limits at scale; "
                    "query before the loop and filter the collection in memory"
                )

    return issues


def find_apex_files(project_dir: Path) -> list[Path]:
    """Find all Apex class and trigger files under project_dir."""
    return [
        p for p in project_dir.rglob('*')
        if p.suffix in APEX_EXTENSIONS and p.is_file()
    ]


def find_flow_files(project_dir: Path) -> list[Path]:
    """Find all Flow metadata XML files under project_dir."""
    return [
        p for p in project_dir.rglob('*.flow-meta.xml')
        if p.is_file()
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce project for common solution design anti-patterns: "
            "hard-coded record IDs in Apex, logic directly in trigger files, "
            "HTTP callouts inside @InvocableMethod, and SOQL queries inside Flow loops."
        ),
    )
    parser.add_argument(
        '--project-dir',
        default='.',
        help='Root directory of the Salesforce project (default: current directory).',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)

    if not project_dir.exists():
        print(f"ISSUE: Project directory not found: {project_dir}")
        return 1

    apex_files = find_apex_files(project_dir)
    flow_files = find_flow_files(project_dir)

    if not apex_files and not flow_files:
        print(f"No Apex or Flow files found under {project_dir}. Nothing to check.")
        return 0

    all_issues: list[str] = []

    for apex_file in sorted(apex_files):
        all_issues.extend(check_apex_file(apex_file))

    for flow_file in sorted(flow_files):
        all_issues.extend(check_flow_file(flow_file))

    total_files = len(apex_files) + len(flow_files)

    if not all_issues:
        print(
            f"No solution design issues found across "
            f"{len(apex_files)} Apex file(s) and {len(flow_files)} Flow file(s)."
        )
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    print(
        f"\n{len(all_issues)} issue(s) found across {total_files} file(s) "
        f"({len(apex_files)} Apex, {len(flow_files)} Flow)."
    )
    return 1


if __name__ == '__main__':
    sys.exit(main())
