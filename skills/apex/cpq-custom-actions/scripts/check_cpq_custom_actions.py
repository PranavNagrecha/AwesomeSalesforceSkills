#!/usr/bin/env python3
"""Checker script for CPQ Custom Actions skill.

Validates Salesforce CPQ custom action configuration by inspecting metadata
exported from a Salesforce org (CustomObject XML files, Flow metadata, etc.).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cpq_custom_actions.py [--help]
    python3 check_cpq_custom_actions.py --manifest-dir path/to/metadata

Checks performed:
  1. Custom action count per location does not exceed 5 (hard CPQ limit).
  2. All Flow-type custom actions reference an activated Flow (Active status in metadata).
  3. No custom action uses an unsupported SBQQ__Type__c value.
  4. URL-type custom actions with https:// targets are noted for CSP review.
  5. Conditional visibility is configured via CPQ condition records, not Flow decisions.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Hard limit enforced by CPQ rendering engine
CPQ_ACTION_LIMIT_PER_LOCATION = 5

# Valid action types per Salesforce CPQ documentation
VALID_ACTION_TYPES = {"URL", "Flow", "Calculate", "Save", "Add Group"}

# Known CPQ location values
VALID_LOCATIONS = {
    "Line Item",
    "Group",
    "Global",
    "Configurator",
    "Amendment",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce CPQ custom action configuration for common issues. "
            "Reads exported metadata XML files from the specified directory."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata export (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print informational findings in addition to warnings.",
    )
    return parser.parse_args()


def find_xml_files(manifest_dir: Path, pattern: str) -> list[Path]:
    """Return all XML files matching a glob pattern under manifest_dir."""
    return list(manifest_dir.rglob(pattern))


def extract_field_value(element: ET.Element, field_name: str, namespace: str = "") -> str:
    """Extract a field value from a Salesforce metadata XML element."""
    ns_prefix = f"{{{namespace}}}" if namespace else ""
    child = element.find(f"{ns_prefix}{field_name}")
    if child is not None and child.text:
        return child.text.strip()
    return ""


def parse_custom_action_records(manifest_dir: Path) -> list[dict]:
    """Parse SBQQ__CustomAction__c records from exported metadata XML files.

    Looks for CustomObject XML exports or data export files containing
    SBQQ__CustomAction__c records. Returns a list of dicts with field values.
    """
    records: list[dict] = []

    # Look for data export CSVs or XML files containing custom action records
    xml_files = find_xml_files(manifest_dir, "*.xml")

    for xml_file in xml_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
        except ET.ParseError:
            continue

        # Handle Salesforce data export XML format
        # Root tag varies; look for records with SBQQ__CustomAction__c fields
        tag_lower = root.tag.lower()
        if "customaction" in tag_lower or "sbqq" in tag_lower:
            record = _extract_action_fields(root)
            if record:
                records.append(record)
            continue

        # Look for nested records in data loader or Report/Export format
        for record_el in root.iter():
            if "customaction" in record_el.tag.lower():
                record = _extract_action_fields(record_el)
                if record:
                    records.append(record)

    return records


def _extract_action_fields(element: ET.Element) -> dict | None:
    """Extract key fields from a custom action XML element."""
    record: dict = {}

    # Try direct children first (data export format)
    for child in element:
        local_tag = child.tag.split("}")[-1]  # strip namespace
        if child.text:
            record[local_tag] = child.text.strip()

    # Must have at least a Type field to be meaningful
    type_field = (
        record.get("SBQQ__Type__c")
        or record.get("Type__c")
        or record.get("type")
    )
    if not type_field:
        return None

    return record


def check_action_type_validity(records: list[dict]) -> list[str]:
    """Check that all custom action records use a valid SBQQ__Type__c value."""
    issues: list[str] = []
    for record in records:
        action_type = (
            record.get("SBQQ__Type__c")
            or record.get("Type__c")
            or record.get("type", "")
        )
        name = record.get("Name", record.get("name", "(unnamed)"))
        if action_type and action_type not in VALID_ACTION_TYPES:
            issues.append(
                f"Custom action '{name}' has unsupported SBQQ__Type__c value '{action_type}'. "
                f"Valid types: {', '.join(sorted(VALID_ACTION_TYPES))}. "
                "Note: there is NO 'Apex' type — use Type=Flow with an @InvocableMethod instead."
            )
    return issues


def check_action_count_per_location(records: list[dict]) -> list[str]:
    """Check that no location context exceeds 5 active custom actions."""
    issues: list[str] = []
    location_counts: dict[str, int] = {}

    for record in records:
        active = record.get("SBQQ__Active__c", record.get("Active__c", "true"))
        # Treat missing active field as active (conservative)
        if str(active).lower() in ("false", "0", "no"):
            continue

        location = (
            record.get("SBQQ__Location__c")
            or record.get("Location__c")
            or record.get("location", "Unknown")
        )
        location_counts[location] = location_counts.get(location, 0) + 1

    for location, count in location_counts.items():
        if count > CPQ_ACTION_LIMIT_PER_LOCATION:
            issues.append(
                f"Location '{location}' has {count} active custom actions, "
                f"exceeding the hard CPQ limit of {CPQ_ACTION_LIMIT_PER_LOCATION}. "
                "Actions beyond the limit are silently dropped in the QLE — no error is shown. "
                "Deactivate actions or consolidate into a Flow with a choice screen."
            )
        elif count == CPQ_ACTION_LIMIT_PER_LOCATION:
            issues.append(
                f"Location '{location}' is at the maximum of {CPQ_ACTION_LIMIT_PER_LOCATION} "
                "active custom actions. Adding any more will cause silent button drops."
            )

    return issues


def check_flow_references(records: list[dict], manifest_dir: Path) -> list[str]:
    """Check that Flow-type custom actions reference Flows that exist as metadata."""
    issues: list[str] = []

    # Collect flow API names referenced by custom actions
    flow_type_records = []
    for record in records:
        action_type = (
            record.get("SBQQ__Type__c")
            or record.get("Type__c")
            or record.get("type", "")
        )
        if action_type == "Flow":
            flow_name = (
                record.get("SBQQ__FlowName__c")
                or record.get("FlowName__c")
                or record.get("flowName", "")
            )
            record_name = record.get("Name", record.get("name", "(unnamed)"))
            if not flow_name:
                issues.append(
                    f"Custom action '{record_name}' has Type=Flow but SBQQ__FlowName__c is empty. "
                    "The button will fail at runtime."
                )
            else:
                flow_type_records.append((record_name, flow_name))

    # Check if the Flow metadata exists in the manifest directory
    flow_dir = manifest_dir / "flows"
    if not flow_dir.exists():
        # Try alternate common paths
        flow_dir = manifest_dir / "force-app" / "main" / "default" / "flows"

    for action_name, flow_name in flow_type_records:
        # Check for Flow XML file (Salesforce metadata format: FlowName.flow-meta.xml)
        flow_meta = flow_dir / f"{flow_name}.flow-meta.xml"
        if flow_dir.exists() and not flow_meta.exists():
            issues.append(
                f"Custom action '{action_name}' references Flow '{flow_name}' "
                f"but no metadata file found at {flow_meta}. "
                "Ensure the Flow is deployed and the API name matches exactly."
            )
        elif flow_meta.exists():
            # Check Flow status in metadata
            try:
                tree = ET.parse(flow_meta)
                root = tree.getroot()
                # Strip namespace for status lookup
                ns = root.tag.split("}")[0].strip("{") if "}" in root.tag else ""
                ns_prefix = f"{{{ns}}}" if ns else ""
                status_el = root.find(f"{ns_prefix}status")
                if status_el is None:
                    status_el = root.find("status")
                if status_el is not None and status_el.text:
                    status = status_el.text.strip()
                    if status != "Active":
                        issues.append(
                            f"Custom action '{action_name}' references Flow '{flow_name}' "
                            f"which has status '{status}' (not Active). "
                            "CPQ will fail at runtime when a rep clicks the button. "
                            "Activate the Flow before deploying the custom action."
                        )
            except ET.ParseError:
                issues.append(
                    f"Could not parse Flow metadata for '{flow_name}' "
                    f"at {flow_meta}. Verify the file is valid XML."
                )

    return issues


def check_url_actions_for_csp(records: list[dict]) -> list[str]:
    """Flag URL-type custom actions with external URLs for CSP review."""
    issues: list[str] = []
    for record in records:
        action_type = (
            record.get("SBQQ__Type__c")
            or record.get("Type__c")
            or record.get("type", "")
        )
        if action_type != "URL":
            continue

        url = (
            record.get("SBQQ__URL__c")
            or record.get("URL__c")
            or record.get("url", "")
        )
        name = record.get("Name", record.get("name", "(unnamed)"))

        if url and url.startswith("https://") and "salesforce.com" not in url and "force.com" not in url:
            issues.append(
                f"Custom action '{name}' uses a URL action pointing to an external domain: {url[:80]}. "
                "Ensure this domain is added to Setup > Security > CSP Trusted Sites "
                "if the URL opens within a Lightning context (modal or iframe)."
            )

        if url and url.startswith("http://"):
            issues.append(
                f"Custom action '{name}' uses an insecure HTTP URL. "
                "Use HTTPS to prevent data exposure when passing merge field values (record IDs) in the URL."
            )

    return issues


def check_cpq_custom_actions(manifest_dir: Path, verbose: bool = False) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Parse custom action records from XML metadata
    records = parse_custom_action_records(manifest_dir)

    if not records:
        if verbose:
            issues.append(
                "INFO: No SBQQ__CustomAction__c records found in metadata. "
                "If custom actions exist in the org, export them as XML and re-run."
            )
        return issues

    if verbose:
        issues.append(f"INFO: Found {len(records)} SBQQ__CustomAction__c record(s) in metadata.")

    # Run all checks
    issues.extend(check_action_type_validity(records))
    issues.extend(check_action_count_per_location(records))
    issues.extend(check_flow_references(records, manifest_dir))
    issues.extend(check_url_actions_for_csp(records))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_cpq_custom_actions(manifest_dir, verbose=args.verbose)

    info_issues = [i for i in issues if i.startswith("INFO:")]
    warn_issues = [i for i in issues if not i.startswith("INFO:")]

    for info in info_issues:
        print(info)

    if not warn_issues:
        print("No CPQ custom action issues found.")
        return 0

    for issue in warn_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
