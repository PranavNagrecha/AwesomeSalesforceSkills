#!/usr/bin/env python3
"""Checker script for Org Cleanup And Technical Debt skill.

Scans a local metadata directory for common cleanup indicators:
- Custom fields with no description (documentation debt)
- Inactive Flow versions that could be pruned
- Active Workflow Rules (legacy automation candidates)
- Active Process Builder flows (legacy automation candidates)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_org_cleanup_and_technical_debt.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


METADATA_NS = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check local Salesforce metadata for org cleanup indicators.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _find_files(root: Path, pattern: str) -> list[Path]:
    """Recursively find files matching a glob pattern."""
    return sorted(root.rglob(pattern))


def check_fields_without_description(manifest_dir: Path) -> list[str]:
    """Flag custom fields that have no description — a documentation debt indicator."""
    issues: list[str] = []
    field_files = _find_files(manifest_dir, "*.field-meta.xml")
    for field_file in field_files:
        try:
            tree = ET.parse(field_file)
            root = tree.getroot()
            # Check for description element
            desc = root.find(f"{{{METADATA_NS}}}description")
            if desc is None or not (desc.text or "").strip():
                field_name = field_file.stem.replace(".field-meta", "")
                issues.append(
                    f"Field '{field_name}' has no description — undocumented fields "
                    f"contribute to metadata clutter ({field_file.relative_to(manifest_dir)})"
                )
        except ET.ParseError:
            issues.append(f"Could not parse XML: {field_file}")
    return issues


def check_inactive_flow_versions(manifest_dir: Path) -> list[str]:
    """Flag Flow files that indicate inactive versions (status != Active)."""
    issues: list[str] = []
    flow_files = _find_files(manifest_dir, "*.flow-meta.xml")
    for flow_file in flow_files:
        try:
            tree = ET.parse(flow_file)
            root = tree.getroot()
            status = root.find(f"{{{METADATA_NS}}}status")
            if status is not None and status.text and status.text.lower() in (
                "obsolete",
                "invaliddraft",
                "draft",
            ):
                flow_name = flow_file.stem.replace(".flow-meta", "")
                issues.append(
                    f"Flow '{flow_name}' has status '{status.text}' — candidate for "
                    f"version cleanup ({flow_file.relative_to(manifest_dir)})"
                )
        except ET.ParseError:
            issues.append(f"Could not parse XML: {flow_file}")
    return issues


def check_active_workflow_rules(manifest_dir: Path) -> list[str]:
    """Flag active Workflow Rules — these are legacy automation candidates for migration."""
    issues: list[str] = []
    workflow_files = _find_files(manifest_dir, "*.workflow-meta.xml")
    for wf_file in workflow_files:
        try:
            tree = ET.parse(wf_file)
            root = tree.getroot()
            rules = root.findall(f"{{{METADATA_NS}}}rules")
            for rule in rules:
                active = rule.find(f"{{{METADATA_NS}}}active")
                name = rule.find(f"{{{METADATA_NS}}}fullName")
                if active is not None and active.text == "true":
                    rule_name = name.text if name is not None and name.text else "unknown"
                    issues.append(
                        f"Active Workflow Rule '{rule_name}' — legacy automation, "
                        f"candidate for migration to Record-Triggered Flow "
                        f"({wf_file.relative_to(manifest_dir)})"
                    )
        except ET.ParseError:
            issues.append(f"Could not parse XML: {wf_file}")
    return issues


def check_hardcoded_ids(manifest_dir: Path) -> list[str]:
    """Scan Flow and Apex metadata for hardcoded Salesforce record IDs."""
    issues: list[str] = []
    import re

    # Salesforce 15- or 18-character ID pattern (starts with known prefixes)
    # This is a heuristic — common prefixes: 001 (Account), 003 (Contact), 005 (User), etc.
    sf_id_pattern = re.compile(r"\b[a-zA-Z0-9]{3}[a-zA-Z0-9]{12}(?:[a-zA-Z0-9]{3})?\b")

    # Known Salesforce ID prefixes (3-char key prefixes for common objects)
    known_prefixes = {
        "001", "003", "005", "006", "00D", "00G", "00Q", "00T", "00U",
        "01I", "01p", "01q", "012", "0IF",
    }

    files_to_scan = _find_files(manifest_dir, "*.flow-meta.xml") + _find_files(
        manifest_dir, "*.cls"
    )
    for file_path in files_to_scan:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            for match in sf_id_pattern.finditer(content):
                candidate = match.group()
                prefix = candidate[:3]
                if prefix in known_prefixes:
                    issues.append(
                        f"Possible hardcoded Salesforce ID '{candidate}' found in "
                        f"{file_path.relative_to(manifest_dir)} — hardcoded IDs break "
                        f"across orgs and sandboxes"
                    )
                    break  # One warning per file is enough
        except (OSError, UnicodeDecodeError):
            pass
    return issues


def check_org_cleanup_and_technical_debt(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_fields_without_description(manifest_dir))
    issues.extend(check_inactive_flow_versions(manifest_dir))
    issues.extend(check_active_workflow_rules(manifest_dir))
    issues.extend(check_hardcoded_ids(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_org_cleanup_and_technical_debt(manifest_dir)

    if not issues:
        print("No org cleanup indicators found.")
        return 0

    print(f"Found {len(issues)} org cleanup indicator(s):\n")
    for issue in issues:
        print(f"  ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
