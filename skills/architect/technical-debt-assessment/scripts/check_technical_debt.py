#!/usr/bin/env python3
"""Technical Debt Assessment — Static Metadata Checker.

Scans a Salesforce project directory for technical debt indicators:

1. Flow metadata files (.flow-meta.xml) with status=Draft and isTemplate=false
   — stale unpublished flows that accumulate version count without ever activating.
2. Flow metadata files with status=Inactive and label/name suggesting they are
   not archived intentionally — candidate inactive versions to clean up.
3. Apex class files (.cls) that appear to be test classes with no assert/Assert
   statements — coverage theater (tests that run but assert nothing).
4. Apex trigger files (.trigger) with direct DML or SOQL in the trigger body
   — logic not delegated to a handler class (maintainability debt).
5. Apex files containing possible hardcoded Salesforce record IDs (15 or 18 char
   string literals starting with 0 — common ID prefix pattern).
6. Flow metadata files referencing deprecated API versions below 50.0.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_technical_debt.py [--project-dir PATH]

If --project-dir is omitted, the current directory is scanned.

Output:
    DEBT [severity]: <finding description>

Severity levels:
    CRITICAL  — likely causing active system instability
    HIGH      — actively degrades maintainability or will block future work
    MEDIUM    — technical hygiene debt
    LOW       — cosmetic or minor
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FLOW_NS = 'http://soap.sforce.com/2006/04/metadata'

# Salesforce record IDs start with a digit (0xx key prefix pattern).
# This matches 15- or 18-character string literals starting with 0.
SF_ID_PATTERN = re.compile(
    r"""(?<![A-Za-z0-9_])['"]0[A-Za-z0-9]{14}(?:[A-Za-z0-9]{3})?['"](?![A-Za-z0-9_])"""
)

# DML statements directly in trigger body (heuristic — not inside a method call)
TRIGGER_DIRECT_DML = re.compile(r'\b(?:insert|update|delete|upsert|merge)\s+\w', re.IGNORECASE)
TRIGGER_DIRECT_SOQL = re.compile(r'\[SELECT\b', re.IGNORECASE)

# Assert/assertion patterns in test classes
ASSERT_PATTERN = re.compile(
    r'\b(?:System\.assert(?:Equals|NotEquals|Throws)?|Assert\.(?:are|is|that|fail|is))\s*\(',
    re.IGNORECASE,
)
TEST_CLASS_ANNOTATION = re.compile(r'@isTest|@IsTest', re.IGNORECASE)
TEST_METHOD_ANNOTATION = re.compile(r'@isTest|testMethod', re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_apex_comments(source: str) -> str:
    """Remove block and line comments from Apex source (best-effort)."""
    source = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)
    source = re.sub(r'//[^\n]*', '', source)
    return source


def _flow_tag(root: ET.Element, tag: str) -> str | None:
    """Return text content of a direct child tag in the Flow XML namespace."""
    el = root.find(f'{{{FLOW_NS}}}{tag}')
    return el.text if el is not None else None


# ---------------------------------------------------------------------------
# Checkers
# ---------------------------------------------------------------------------

def check_flow_file(path: Path) -> list[tuple[str, str]]:
    """
    Returns list of (severity, message) tuples for debt found in a Flow XML file.
    """
    findings: list[tuple[str, str]] = []

    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        findings.append(('MEDIUM', f"{path}: XML parse error — {exc}; file may be corrupted"))
        return findings

    root = tree.getroot()

    status = _flow_tag(root, 'status')
    label = _flow_tag(root, 'label') or path.stem
    is_template_el = root.find(f'{{{FLOW_NS}}}isTemplate')
    is_template = is_template_el is not None and (is_template_el.text or '').lower() == 'true'

    # --- Draft flows that are not templates ---
    if status == 'Draft' and not is_template:
        findings.append((
            'MEDIUM',
            f"{path}: Flow '{label}' has status=Draft and is not a template — "
            "this is a stale unpublished version that contributes to the org's "
            "2,000 Flow version limit without providing any active automation; "
            "either activate it or delete it"
        ))

    # --- Inactive flows (version accumulation) ---
    if status == 'Inactive':
        findings.append((
            'LOW',
            f"{path}: Flow '{label}' has status=Inactive — confirm this is intentionally "
            "retained as a rollback reference; if not, delete it to free up version quota "
            "(org limit: 2,000 Flow versions total)"
        ))

    # --- Check for deprecated API version in flow ---
    api_version_el = root.find(f'{{{FLOW_NS}}}apiVersion')
    if api_version_el is not None and api_version_el.text:
        try:
            api_ver = float(api_version_el.text)
            if api_ver < 50.0:
                findings.append((
                    'HIGH',
                    f"{path}: Flow '{label}' uses API version {api_version_el.text} "
                    "(below v50.0 / Winter '21) — upgrade to current API version to avoid "
                    "deprecated platform behavior and upcoming end-of-life enforcement"
                ))
        except ValueError:
            pass

    return findings


def check_apex_file(path: Path) -> list[tuple[str, str]]:
    """
    Returns list of (severity, message) tuples for debt found in an Apex file.
    """
    findings: list[tuple[str, str]] = []

    try:
        raw = path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        findings.append(('MEDIUM', f"{path}: cannot read — {exc}"))
        return findings

    source_clean = _strip_apex_comments(raw)

    # --- Hardcoded Salesforce record IDs ---
    lines = raw.splitlines()
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip comment lines
        if stripped.startswith('//') or stripped.startswith('*'):
            continue
        for match in SF_ID_PATTERN.finditer(line):
            candidate = match.group(0).strip("'\"")
            if len(candidate) in (15, 18):
                findings.append((
                    'HIGH',
                    f"{path}:{i}: Possible hardcoded Salesforce record ID '{candidate}' — "
                    "hardcoded IDs are org-specific and break sandbox refreshes and cross-org "
                    "deployments; move to Custom Metadata or a dynamic lookup"
                ))

    # --- Apex trigger: logic directly in trigger body ---
    if path.suffix == '.trigger':
        if TRIGGER_DIRECT_DML.search(source_clean):
            findings.append((
                'HIGH',
                f"{path}: DML statement found directly in trigger body — delegate to a "
                "handler class for bulkification, testability, and single-entry-point "
                "enforcement; logic embedded in triggers cannot be unit tested in isolation"
            ))
        if TRIGGER_DIRECT_SOQL.search(source_clean):
            findings.append((
                'HIGH',
                f"{path}: SOQL query found directly in trigger body — move to a handler "
                "class; inline SOQL in triggers is harder to bulkify and cannot be "
                "independently tested"
            ))

    # --- Test classes with no assertions (coverage theater) ---
    if path.suffix == '.cls' and TEST_CLASS_ANNOTATION.search(raw):
        has_test_methods = bool(TEST_METHOD_ANNOTATION.search(raw))
        has_assertions = bool(ASSERT_PATTERN.search(raw))
        if has_test_methods and not has_assertions:
            findings.append((
                'MEDIUM',
                f"{path}: Test class contains test methods but no Assert/System.assert "
                "calls — this is coverage theater: it may satisfy the 75% deployment "
                "threshold without actually verifying any behavior; add assertions to "
                "make the tests meaningful"
            ))

    return findings


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_flow_files(root_dir: Path) -> list[Path]:
    return [p for p in root_dir.rglob('*.flow-meta.xml') if p.is_file()]


def find_apex_files(root_dir: Path) -> list[Path]:
    return [p for p in root_dir.rglob('*') if p.suffix in {'.cls', '.trigger'} and p.is_file()]


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

SEVERITY_ORDER = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}

MANUAL_CHECKS = """
Manual checks required (cannot be detected from local metadata alone):
------------------------------------------------------------------------
1. AUTOMATION OVERLAP
   - In Setup → Flows, list all active Record-Triggered Flows per object.
   - In Setup → Process Builder, check for any Active process flows.
   - In Setup → Workflow Rules, check for any Active rules.
   - Compare: do any two automations on the same object respond to the same
     trigger event AND write to the same field or send the same email?
     → If yes: Critical or High finding depending on consequence.

2. FLOW VERSION COUNT
   - Setup → Flows → View All Flow Versions.
   - Or via Tooling API: SELECT count() FROM FlowVersion
   - If count > 1,800 (of the 2,000 limit): High finding — version cleanup required
     before new Flows can be deployed.

3. APEX CODE COVERAGE
   - Run: sfdx force:apex:test:run --resultformat json
   - Identify classes with 0% coverage that have executable lines.
   - Classes at 0% with no test touching them are dead code candidates.
   - Classes with tests that have no assertions (see static check above) are
     coverage theater candidates.

4. ACTIVE PROCESS BUILDER FLOWS
   - Setup → Process Builder → filter by Status = Active.
   - Any active Process Builder is executing legacy automation.
   - Check for overlap with any current Record-Triggered Flows on the same object.

5. PERMISSION SET HYGIENE
   - Query: SELECT Id, Name, Description FROM PermissionSet WHERE IsOwnedByProfile = false
   - For each permission set, check: SELECT count() FROM PermissionSetAssignment
     WHERE PermissionSetId = '<id>'
   - Permission sets with 0 assignments are unused; document as Low finding.

6. BROAD PROFILE PERMISSIONS
   - Profiles with PermissionsViewAllData = true or PermissionsModifyAllData = true
     beyond System Administrator should be documented as security debt indicators.
   - Query: SELECT Name, PermissionsViewAllData, PermissionsModifyAllData FROM Profile
     WHERE PermissionsViewAllData = true OR PermissionsModifyAllData = true
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan a Salesforce project directory for static technical debt indicators: "
            "stale Flow versions, deprecated API usage, hardcoded IDs in Apex, "
            "trigger handler anti-patterns, and test classes with no assertions."
        )
    )
    parser.add_argument(
        '--project-dir',
        default='.',
        help='Root of the Salesforce project to scan (default: current directory).',
    )
    parser.add_argument(
        '--severity',
        choices=['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
        default=None,
        help='Filter output to findings at this severity or above.',
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()

    if not project_dir.exists():
        print(f"ERROR: Directory not found: {project_dir}")
        return 1

    print(f"Scanning: {project_dir}")
    print()

    flow_files = find_flow_files(project_dir)
    apex_files = find_apex_files(project_dir)

    if not flow_files and not apex_files:
        print("No .flow-meta.xml, .cls, or .trigger files found.")
        print("If you intended to scan a Salesforce project, verify the --project-dir path.")
        print()
        print(MANUAL_CHECKS)
        return 0

    all_findings: list[tuple[str, str]] = []

    for flow_file in sorted(flow_files):
        all_findings.extend(check_flow_file(flow_file))

    for apex_file in sorted(apex_files):
        all_findings.extend(check_apex_file(apex_file))

    # Apply severity filter
    min_severity = SEVERITY_ORDER.get(args.severity or 'LOW', 3)
    filtered = [
        (sev, msg) for sev, msg in all_findings
        if SEVERITY_ORDER.get(sev, 99) <= min_severity
    ]

    # Sort by severity then message
    filtered.sort(key=lambda x: (SEVERITY_ORDER.get(x[0], 99), x[1]))

    if not filtered:
        print(
            f"No static debt indicators found across "
            f"{len(flow_files)} Flow file(s) and {len(apex_files)} Apex file(s)."
        )
    else:
        counts: dict[str, int] = {}
        for sev, msg in filtered:
            counts[sev] = counts.get(sev, 0) + 1
            print(f"DEBT [{sev}]: {msg}")

        print()
        print(f"--- Summary ---")
        print(
            f"Scanned {len(flow_files)} Flow file(s) and "
            f"{len(apex_files)} Apex file(s). "
            f"Found {len(filtered)} finding(s):"
        )
        for sev in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'):
            if sev in counts:
                print(f"  {sev}: {counts[sev]}")

    print()
    print(MANUAL_CHECKS)

    return 1 if any(SEVERITY_ORDER.get(s, 99) <= 1 for s, _ in filtered) else 0


if __name__ == '__main__':
    sys.exit(main())
