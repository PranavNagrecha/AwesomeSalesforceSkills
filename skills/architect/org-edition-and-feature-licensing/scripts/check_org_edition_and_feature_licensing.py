#!/usr/bin/env python3
"""Checker script for Org Edition and Feature Licensing skill.

Scans Salesforce metadata for patterns that indicate edition-specific or
add-on-required features, and reports features that may not be available
in lower editions.

Checks:
- Apex classes and triggers present (requires Enterprise+)
- Flow Orchestration usage in flow metadata
- Platform Encryption configuration (requires Shield)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_org_edition_and_feature_licensing.py [--help]
    python3 check_org_edition_and_feature_licensing.py --source-dir force-app/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan metadata for edition-specific feature dependencies.",
    )
    parser.add_argument(
        "--source-dir",
        default=".",
        help="Root directory of the Salesforce source (default: current directory).",
    )
    return parser.parse_args()


def check_apex_presence(source_dir: Path) -> list[str]:
    """Warn if Apex classes or triggers are present — these require Enterprise Edition+."""
    issues: list[str] = []
    apex_classes = list(source_dir.rglob("*.cls"))
    apex_triggers = list(source_dir.rglob("*.trigger"))
    if apex_classes:
        issues.append(
            f"EDITION_REQUIREMENT: {len(apex_classes)} Apex class file(s) found — "
            f"Apex requires Enterprise Edition or higher. "
            f"Not available in Professional or Essentials Edition."
        )
    if apex_triggers:
        issues.append(
            f"EDITION_REQUIREMENT: {len(apex_triggers)} Apex trigger file(s) found — "
            f"Apex triggers require Enterprise Edition or higher."
        )
    return issues


SF_NS = "http://soap.sforce.com/2006/04/metadata"


def _tag(local: str) -> str:
    return f"{{{SF_NS}}}{local}"


def check_flow_orchestration(source_dir: Path) -> list[str]:
    """Warn if any flow metadata uses Flow Orchestration types."""
    issues: list[str] = []
    # Flow Orchestration flows have processType = Orchestrator
    for flow_file in source_dir.rglob("*.flow-meta.xml"):
        try:
            tree = ET.parse(flow_file)
            root = tree.getroot()
            process_type = root.find(_tag("processType"))
            if process_type is not None and process_type.text == "Orchestrator":
                issues.append(
                    f"EDITION_REQUIREMENT: {flow_file.name} uses Flow Orchestration "
                    f"(processType=Orchestrator) — requires Enterprise Edition+ and "
                    f"must be enabled in Setup > Process Automation Settings. "
                    f"Also requires an add-on license in some configurations."
                )
        except ET.ParseError:
            pass
    return issues


def check_platform_encryption(source_dir: Path) -> list[str]:
    """Warn if platform encryption metadata is present — requires Salesforce Shield add-on."""
    issues: list[str] = []
    encryption_files = list(source_dir.rglob("*.encryptionPolicy-meta.xml"))
    if encryption_files:
        issues.append(
            f"LICENSE_REQUIREMENT: {len(encryption_files)} Platform Encryption policy file(s) found — "
            f"Platform Encryption requires the Salesforce Shield add-on. "
            f"Not included in any base edition."
        )
    return issues


def check_edition_requirements(source_dir: Path) -> list[str]:
    """Return a list of edition/license requirement notices."""
    issues: list[str] = []

    if not source_dir.exists():
        issues.append(f"Source directory not found: {source_dir}")
        return issues

    issues.extend(check_apex_presence(source_dir))
    issues.extend(check_flow_orchestration(source_dir))
    issues.extend(check_platform_encryption(source_dir))

    return issues


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source_dir)
    issues = check_edition_requirements(source_dir)

    if not issues:
        print("No edition-specific feature dependencies detected.")
        return 0

    for issue in issues:
        print(f"INFO: {issue}")

    # Return 0 even with findings — these are informational, not errors
    return 0


if __name__ == "__main__":
    sys.exit(main())
