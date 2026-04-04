#!/usr/bin/env python3
"""Checker script for Platform Selection Guidance skill.

Scans a Salesforce project directory for common platform selection anti-patterns:

1. Aura component files present with no LWC equivalent (advisory)
2. Custom Settings with Hierarchy type where all records are at org level
   (candidate for migration to Custom Metadata Types)
3. Outbound Message metadata files present (legacy integration pattern)
4. Custom Metadata Types with fields storing 15- or 18-char Salesforce IDs
   as text (cannot be relationship fields — flags a known CMT limitation)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_platform_selection_guidance.py [--project-dir path/to/force-app]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Pattern constants
# ---------------------------------------------------------------------------

# Matches 15- or 18-character Salesforce record IDs stored as text defaults
# in metadata XML. Heuristic: a string field default value that is 15 or 18
# alphanumeric chars starting with a digit.
SF_ID_IN_XML = re.compile(
    r"""<defaultValue>0[A-Za-z0-9]{14}(?:[A-Za-z0-9]{3})?</defaultValue>"""
)

METADATA_NS = 'http://soap.sforce.com/2006/04/metadata'


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _ns(tag: str) -> str:
    return f'{{{METADATA_NS}}}{tag}'


def _find_text(element: ET.Element, tag: str) -> str:
    child = element.find(_ns(tag))
    return child.text.strip() if child is not None and child.text else ''


# ---------------------------------------------------------------------------
# Check 1: Aura components without LWC equivalents
# ---------------------------------------------------------------------------

def find_aura_components(project_dir: Path) -> list[str]:
    """Return names of Aura components found under project_dir."""
    names: list[str] = []
    for path in project_dir.rglob('*.cmp'):
        # Aura component bundles: <name>/<name>.cmp
        names.append(path.stem)
    for path in project_dir.rglob('*.app'):
        names.append(path.stem)
    return names


def find_lwc_components(project_dir: Path) -> set[str]:
    """Return names of LWC components (directories with an HTML file) under project_dir."""
    names: set[str] = set()
    for path in project_dir.rglob('*.html'):
        # LWC bundles: lwc/<componentName>/<componentName>.html
        parent = path.parent
        if path.stem == parent.name:
            names.add(path.stem)
    return names


def check_aura_vs_lwc(project_dir: Path) -> list[str]:
    """Advisory: Aura components with no LWC equivalent present."""
    advisories: list[str] = []
    aura_names = find_aura_components(project_dir)
    lwc_names = find_lwc_components(project_dir)

    for aura_name in sorted(set(aura_names)):
        # Case-insensitive comparison — Aura names may differ in casing from LWC
        lower_name = aura_name.lower()
        if not any(l.lower() == lower_name for l in lwc_names):
            advisories.append(
                f"ADVISORY: Aura component '{aura_name}' has no LWC equivalent. "
                "Aura is a legacy framework. Evaluate migrating to LWC. "
                "See architect/platform-selection-guidance for migration path guidance."
            )
    return advisories


# ---------------------------------------------------------------------------
# Check 2: Outbound Messaging metadata files (legacy integration pattern)
# ---------------------------------------------------------------------------

def check_outbound_messages(project_dir: Path) -> list[str]:
    """Flag any Outbound Message metadata files as legacy integration patterns."""
    issues: list[str] = []
    for path in project_dir.rglob('*.outboundMessage-meta.xml'):
        # Parse to get the name if possible
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            name_text = _find_text(root, 'fullName') or path.stem.replace('.outboundMessage', '')
        except ET.ParseError:
            name_text = path.name

        issues.append(
            f"ISSUE: Outbound Message '{name_text}' found at {path}. "
            "Outbound Messaging is a legacy SOAP-based pattern tied to retired Workflow Rules. "
            "Migrate to Platform Events. "
            "See architect/platform-selection-guidance for migration path."
        )
    return issues


# ---------------------------------------------------------------------------
# Check 3: Custom Metadata Type fields with Salesforce ID default values
# ---------------------------------------------------------------------------

def check_cmt_id_fields(project_dir: Path) -> list[str]:
    """Flag CMT field definitions that appear to store raw Salesforce IDs as defaults."""
    issues: list[str] = []
    for path in project_dir.rglob('*.field-meta.xml'):
        # Only care about fields under a CustomMetadata object directory
        # Path shape: .../objects/<ObjectName__mdt>/fields/<FieldName__c.field-meta.xml>
        parts = path.parts
        try:
            objects_idx = next(i for i, p in enumerate(parts) if p == 'objects')
        except StopIteration:
            continue

        object_name = parts[objects_idx + 1] if objects_idx + 1 < len(parts) else ''
        if not object_name.endswith('__mdt'):
            continue

        try:
            raw = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue

        if SF_ID_IN_XML.search(raw):
            issues.append(
                f"ADVISORY: CMT field at {path} (object: {object_name}) appears to store "
                "a Salesforce record ID as a default value. "
                "Custom Metadata Types cannot use relationship fields to standard sObjects — "
                "IDs stored as text are org-specific and will break cross-org deployments. "
                "Consider storing the record's developer name or unique API name instead, "
                "and resolving to an ID at runtime via SOQL. "
                "See architect/platform-selection-guidance Gotcha #5."
            )
    return issues


# ---------------------------------------------------------------------------
# Check 4: Workflow Rule metadata (signals Outbound Messaging / legacy usage)
# ---------------------------------------------------------------------------

def check_workflow_rules(project_dir: Path) -> list[str]:
    """Flag active Workflow Rule metadata as legacy automation carrying outbound message risk."""
    issues: list[str] = []
    for path in project_dir.rglob('*.workflow-meta.xml'):
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except ET.ParseError as exc:
            issues.append(f"ADVISORY: Cannot parse workflow file {path}: {exc}")
            continue

        # Check for outboundMessages elements inside the workflow
        outbound_els = root.findall(f'.//{_ns("outboundMessages")}')
        if outbound_els:
            issues.append(
                f"ISSUE: Workflow file {path} contains outboundMessages definitions. "
                "These are legacy SOAP-based Outbound Messages tied to Workflow Rules. "
                "Workflow Rules are retired. Migrate triggers to Record-Triggered Flow "
                "and Outbound Messages to Platform Events. "
                "See architect/platform-selection-guidance for migration path."
            )

        # Check for active workflow rules (active=true)
        for rule_el in root.findall(f'.//{_ns("rules")}'):
            active_el = rule_el.find(_ns('active'))
            if active_el is not None and active_el.text and active_el.text.strip().lower() == 'true':
                name_el = rule_el.find(_ns('fullName'))
                rule_name = name_el.text.strip() if name_el is not None and name_el.text else 'unknown'
                issues.append(
                    f"ADVISORY: Active Workflow Rule '{rule_name}' found in {path}. "
                    "Workflow Rules are retired. Treat this as migration backlog. "
                    "Replace with Record-Triggered Flow."
                )

    return issues


# ---------------------------------------------------------------------------
# Check 5: Custom Settings references in Apex (candidates for CMT migration)
# ---------------------------------------------------------------------------

def check_custom_settings_in_apex(project_dir: Path) -> list[str]:
    """Advisory: Apex files using Custom Settings getInstance() — flag as CMT migration candidates."""
    advisories: list[str] = []
    # Pattern: MySettings__c.getInstance() or MySettings__c.getValues(...)
    cs_pattern = re.compile(r'\b\w+__c\.get(?:Instance|Values|OrgDefaults)\s*\(')

    for path in project_dir.rglob('*.cls'):
        try:
            raw = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue

        # Strip comments before matching
        source = re.sub(r'/\*.*?\*/', '', raw, flags=re.DOTALL)
        source = re.sub(r'//[^\n]*', '', source)

        matches = cs_pattern.findall(source)
        if matches:
            unique = sorted(set(matches))
            advisories.append(
                f"ADVISORY: {path} uses Custom Settings access pattern(s): "
                f"{', '.join(unique)}. "
                "Evaluate whether this configuration could be migrated to Custom Metadata Types "
                "for improved deployability. Custom Settings data does not deploy via "
                "Metadata API. See architect/platform-selection-guidance for decision criteria."
            )
    return advisories


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce project for platform selection anti-patterns: "
            "Aura components without LWC equivalents, Outbound Message metadata, "
            "Custom Metadata Type fields storing raw Salesforce IDs, "
            "active Workflow Rules, and Custom Settings usage in Apex."
        )
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
        print(f"ERROR: Project directory not found: {project_dir}")
        return 1

    all_findings: list[str] = []

    all_findings.extend(check_aura_vs_lwc(project_dir))
    all_findings.extend(check_outbound_messages(project_dir))
    all_findings.extend(check_cmt_id_fields(project_dir))
    all_findings.extend(check_workflow_rules(project_dir))
    all_findings.extend(check_custom_settings_in_apex(project_dir))

    if not all_findings:
        print(
            f"No platform selection anti-patterns found under {project_dir}. "
            "Note: this checker scans for known metadata file patterns. "
            "Verify manually that configuration storage, UI framework, and integration "
            "pattern choices align with architect/platform-selection-guidance."
        )
        return 0

    for finding in all_findings:
        print(finding)

    issues = [f for f in all_findings if f.startswith('ISSUE:')]
    advisories = [f for f in all_findings if f.startswith('ADVISORY:')]
    print(
        f"\n{len(issues)} issue(s) and {len(advisories)} advisory/advisories found "
        f"under {project_dir}."
    )

    # Return non-zero only for hard issues, not advisories
    return 1 if issues else 0


if __name__ == '__main__':
    sys.exit(main())
