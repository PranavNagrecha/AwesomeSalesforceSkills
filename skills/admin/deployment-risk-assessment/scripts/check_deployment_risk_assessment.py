#!/usr/bin/env python3
"""Checker script for Deployment Risk Assessment skill.

Scans a Salesforce metadata directory for components and configuration patterns
that indicate high deployment risk or missing rollback preparation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_deployment_risk_assessment.py [--help]
    python3 check_deployment_risk_assessment.py --manifest-dir path/to/metadata
    python3 check_deployment_risk_assessment.py --manifest-dir path/to/metadata --strict
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ---------------------------------------------------------------------------
# Metadata types that are HIGH risk by default (any presence triggers a warning
# unless the practitioner has explicitly acknowledged and documented the risk)
# ---------------------------------------------------------------------------
HIGH_RISK_METADATA_DIRS = {
    "permissionsets": "PermissionSet",
    "profiles": "Profile",
    "sharingrules": "SharingRules",
    "connectedapps": "ConnectedApp",
    "authproviders": "AuthProvider",
    "externalcredentials": "ExternalCredential",
    "namedcredentials": "NamedCredential",
}

# Flow types that are high risk when present on high-volume standard objects
HIGH_RISK_FLOW_TRIGGER_OBJECTS = {
    "Opportunity",
    "Lead",
    "Case",
    "Account",
    "Contact",
    "Order",
    "Quote",
}

# Metadata file extensions to scan
METADATA_EXTENSIONS = {".permissionset", ".profile", ".sharingrules", ".connectedapp",
                        ".flow", ".trigger", ".cls", ".namedCredential", ".authprovider"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for high-risk deployment components "
            "and missing rollback preparation indicators."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Exit with code 1 if any HIGH-risk components are found, "
            "regardless of whether rollback assets are documented."
        ),
    )
    return parser.parse_args()


def _find_files_by_extension(root: Path, extensions: set[str]) -> list[Path]:
    """Recursively find files matching any of the given extensions."""
    found: list[Path] = []
    for dirpath, _dirs, filenames in os.walk(root):
        for filename in filenames:
            suffix = Path(filename).suffix.lower()
            if suffix in extensions:
                found.append(Path(dirpath) / filename)
    return found


def check_high_risk_metadata_types(manifest_dir: Path) -> list[str]:
    """Detect HIGH-risk metadata types present in the manifest."""
    issues: list[str] = []
    for subdir_name, metadata_type in HIGH_RISK_METADATA_DIRS.items():
        target = manifest_dir / subdir_name
        if target.is_dir():
            components = [f.name for f in target.iterdir() if f.is_file()
                          and not f.name.startswith(".")]
            if components:
                component_list = ", ".join(sorted(components)[:5])
                more = f" (+{len(components) - 5} more)" if len(components) > 5 else ""
                issues.append(
                    f"HIGH-RISK: {metadata_type} components found: {component_list}{more}. "
                    f"Classify these as HIGH risk. Confirm pre-retrieve backup exists "
                    f"before the deployment window opens."
                )
    return issues


def check_flows_for_bulk_risk(manifest_dir: Path) -> list[str]:
    """Detect Record-Triggered Flows on high-volume objects."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.is_dir():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        try:
            tree = ET.parse(flow_file)
            root = tree.getroot()
            # Strip namespace if present
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            process_type = root.findtext(f"{ns}processType", "")
            trigger_type = root.findtext(f"{ns}triggerType", "")
            object_elem = root.findtext(f"{ns}triggerOrder", "")

            # Look for the object the flow triggers on
            start_elem = root.find(f"{ns}start")
            obj_name = ""
            if start_elem is not None:
                obj_name = start_elem.findtext(f"{ns}object", "") or ""

            is_record_triggered = (
                process_type in {"AutoLaunchedFlow", ""}
                and trigger_type in {"RecordBeforeSave", "RecordAfterSave", "RecordBeforeDelete", ""}
                and obj_name in HIGH_RISK_FLOW_TRIGGER_OBJECTS
            )
            if is_record_triggered and obj_name:
                issues.append(
                    f"HIGH-RISK: Flow '{flow_file.stem}' triggers on '{obj_name}' "
                    f"(a high-volume standard object). Classify as HIGH risk. "
                    f"Validate at production data volumes before deploying. "
                    f"Consider a feature flag gate if activation timing is uncertain."
                )
        except ET.ParseError:
            issues.append(
                f"PARSE-ERROR: Could not parse flow file '{flow_file.name}'. "
                f"Confirm the file is valid XML before deploying."
            )

    return issues


def check_for_destructive_changes(manifest_dir: Path) -> list[str]:
    """Warn if no destructive change manifest is present when high-risk types exist."""
    issues: list[str] = []
    destructive_files = list(manifest_dir.glob("destructiveChanges*.xml"))
    destructive_files += list(manifest_dir.glob("**/destructiveChanges*.xml"))

    high_risk_present = any(
        (manifest_dir / subdir).is_dir()
        for subdir in HIGH_RISK_METADATA_DIRS
    )

    if high_risk_present and not destructive_files:
        issues.append(
            "ROLLBACK-GAP: HIGH-risk components detected but no destructiveChanges.xml found. "
            "If rollback requires removing components added by this release, "
            "author and test destructiveChanges.xml in a sandbox before the window opens."
        )
    return issues


def check_backup_signal(manifest_dir: Path) -> list[str]:
    """Look for evidence of a pre-retrieve backup (common naming conventions)."""
    issues: list[str] = []
    parent = manifest_dir.parent

    # Check for a sibling directory named .rollback-backup or rollback-backup
    backup_indicators = [
        parent / ".rollback-backup",
        parent / "rollback-backup",
        parent / "backup",
        manifest_dir / ".rollback-backup",
    ]
    has_backup = any(p.is_dir() and any(p.iterdir()) for p in backup_indicators if p.exists())

    if not has_backup:
        issues.append(
            "ROLLBACK-GAP: No pre-retrieve backup directory found adjacent to the manifest. "
            "For org-based deployments, capture a production retrieve before the window opens: "
            "sf project retrieve start --metadata <types> --target-org production "
            "--output-dir .rollback-backup/$(date +%Y-%m-%d-%H%M)"
        )
    return issues


def check_package_xml_for_risk_summary(manifest_dir: Path) -> list[str]:
    """Parse package.xml and flag if it contains HIGH-risk metadata types."""
    issues: list[str] = []
    package_xml = manifest_dir / "package.xml"
    if not package_xml.is_file():
        return issues

    try:
        tree = ET.parse(package_xml)
        root = tree.getroot()
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        high_risk_found: list[str] = []
        for type_elem in root.findall(f"{ns}types"):
            name_elem = type_elem.find(f"{ns}name")
            if name_elem is not None and name_elem.text:
                type_name = name_elem.text.strip()
                if type_name in {
                    "PermissionSet", "Profile", "SharingRules", "ConnectedApp",
                    "AuthProvider", "ExternalCredential", "NamedCredential",
                }:
                    members = [
                        m.text.strip()
                        for m in type_elem.findall(f"{ns}members")
                        if m.text
                    ]
                    high_risk_found.append(f"{type_name}: {', '.join(members[:3])}")

        if high_risk_found:
            issues.append(
                f"PACKAGE-XML HIGH-RISK: package.xml includes high-risk metadata types: "
                + "; ".join(high_risk_found)
                + ". Each must be explicitly classified before the deployment window opens."
            )
    except ET.ParseError:
        issues.append(
            "PARSE-ERROR: Could not parse package.xml. "
            "Confirm the file is valid XML before deploying."
        )

    return issues


def check_deployment_risk_assessment(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_high_risk_metadata_types(manifest_dir))
    issues.extend(check_flows_for_bulk_risk(manifest_dir))
    issues.extend(check_for_destructive_changes(manifest_dir))
    issues.extend(check_backup_signal(manifest_dir))
    issues.extend(check_package_xml_for_risk_summary(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_deployment_risk_assessment(manifest_dir)

    if not issues:
        print("No deployment risk issues found.")
        return 0

    high_risk_count = sum(1 for i in issues if i.startswith("HIGH-RISK") or i.startswith("PACKAGE-XML HIGH-RISK"))
    gap_count = sum(1 for i in issues if i.startswith("ROLLBACK-GAP"))

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(
        f"\nSummary: {len(issues)} issue(s) found — "
        f"{high_risk_count} high-risk component warning(s), "
        f"{gap_count} rollback preparation gap(s).",
        file=sys.stderr,
    )

    if args.strict and high_risk_count > 0:
        return 1

    # Return 1 only for rollback gaps (actionable blockers); high-risk is advisory
    return 1 if gap_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
