#!/usr/bin/env python3
"""Checker script for Permission Set Deployment Ordering skill.

Scans a Salesforce metadata directory for common permission set deployment issues:
- Permission sets that might conflict with ConnectedApps in the same directory
- Permission set groups whose constituent permission sets are not present locally

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_permission_set_deployment_ordering.py [--help]
    python3 check_permission_set_deployment_ordering.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Permission Set deployment metadata for ordering and safety issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_xml_files(manifest_dir: Path, suffix: str) -> list[Path]:
    return list(manifest_dir.rglob(f"*{suffix}"))


def get_xml_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def check_connected_app_pset_conflict(manifest_dir: Path) -> list[str]:
    """Warn if ConnectedApp and PermissionSet referencing it are in same directory."""
    issues: list[str] = []

    connected_apps = find_xml_files(manifest_dir, ".connectedApp-meta.xml")
    connected_app_names = {p.name.replace(".connectedApp-meta.xml", "") for p in connected_apps}

    if not connected_app_names:
        return issues

    pset_files = find_xml_files(manifest_dir, ".permissionset-meta.xml")
    psg_files = find_xml_files(manifest_dir, ".permissionsetgroup-meta.xml")

    ns = "{http://soap.sforce.com/2006/04/metadata}"

    for pset_file in pset_files:
        try:
            tree = ET.parse(pset_file)
            root = tree.getroot()
            # Check applicationVisibilities for ConnectedApp references
            for app_vis in root.findall(f"{ns}applicationVisibilities"):
                app_elem = app_vis.find(f"{ns}application")
                if app_elem is not None:
                    app_name = get_xml_text(app_elem)
                    if app_name in connected_app_names:
                        issues.append(
                            f"CONFLICT: {pset_file.name} references ConnectedApp '{app_name}' "
                            f"which is also in this package. Deploy ConnectedApp first in a "
                            f"separate batch, then deploy this PermissionSet."
                        )
        except ET.ParseError:
            issues.append(f"PARSE_ERROR: Could not parse {pset_file}")

    for psg_file in psg_files:
        try:
            tree = ET.parse(psg_file)
            root = tree.getroot()
            for app_vis in root.findall(f"{ns}applicationVisibilities"):
                app_elem = app_vis.find(f"{ns}application")
                if app_elem is not None:
                    app_name = get_xml_text(app_elem)
                    if app_name in connected_app_names:
                        issues.append(
                            f"CONFLICT: {psg_file.name} references ConnectedApp '{app_name}' "
                            f"which is also in this package. Deploy ConnectedApp first in a "
                            f"separate batch, then deploy this PermissionSetGroup."
                        )
        except ET.ParseError:
            issues.append(f"PARSE_ERROR: Could not parse {psg_file}")

    return issues


def check_psg_constituent_sets_present(manifest_dir: Path) -> list[str]:
    """Warn if a PSG references constituent PSets not present in the same directory."""
    issues: list[str] = []

    psg_files = find_xml_files(manifest_dir, ".permissionsetgroup-meta.xml")
    pset_files = find_xml_files(manifest_dir, ".permissionset-meta.xml")
    local_pset_names = {p.name.replace(".permissionset-meta.xml", "") for p in pset_files}

    ns = "{http://soap.sforce.com/2006/04/metadata}"

    for psg_file in psg_files:
        try:
            tree = ET.parse(psg_file)
            root = tree.getroot()
            psg_name = psg_file.name.replace(".permissionsetgroup-meta.xml", "")
            for member in root.findall(f"{ns}permissionSets"):
                ps_name = get_xml_text(member)
                if ps_name and ps_name not in local_pset_names:
                    issues.append(
                        f"PSG_ORDERING: PermissionSetGroup '{psg_name}' references constituent "
                        f"PermissionSet '{ps_name}' which is NOT in this deployment package. "
                        f"Ensure '{ps_name}' already exists in the target org, or deploy it in "
                        f"a prior batch before deploying the PSG."
                    )
        except ET.ParseError:
            issues.append(f"PARSE_ERROR: Could not parse {psg_file}")

    return issues


def check_permission_set_deployment_ordering(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_connected_app_pset_conflict(manifest_dir))
    issues.extend(check_psg_constituent_sets_present(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_permission_set_deployment_ordering(manifest_dir)

    if not issues:
        print("No permission set deployment ordering issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
