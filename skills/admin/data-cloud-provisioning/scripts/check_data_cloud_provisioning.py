#!/usr/bin/env python3
"""Checker script for Data Cloud Provisioning skill.

Inspects Salesforce metadata (Connected Apps, Permission Sets, Named Credentials)
for common Data Cloud provisioning anti-patterns and misconfigurations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_provisioning.py [--help]
    python3 check_data_cloud_provisioning.py --manifest-dir path/to/metadata
    python3 check_data_cloud_provisioning.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SALESFORCE_NS = "http://soap.sforce.com/2006/04/metadata"

# The OAuth scope required for Ingestion API connected apps.
REQUIRED_INGESTION_SCOPE = "cdp_ingest_api"

# Standard Data Cloud permission sets — do not use custom clones of these.
STANDARD_DC_PERMISSION_SETS = {
    "Data_Cloud_Admin",
    "DataCloudAdmin",
    "Data_Cloud_Marketing_Admin",
    "DataCloudMarketingAdmin",
    "Data_Cloud_User",
    "DataCloudUser",
    "Data_Cloud_Data_Aware_Specialist",
    "DataCloudDataAwareSpecialist",
    "Data_Cloud_Marketing_Manager",
    "DataCloudMarketingManager",
    "Data_Cloud_Marketing_Specialist",
    "DataCloudMarketingSpecialist",
}

# Patterns that suggest a permission set is a clone of a standard Data Cloud set.
DC_PERM_SET_CLONE_PATTERNS = [
    re.compile(r"data.?cloud.*(admin|user|specialist|manager)", re.IGNORECASE),
]

# Scopes that alone are insufficient for Ingestion API — caller also needs cdp_ingest_api.
INGESTION_INDICATOR_SCOPES = {
    "cdp_ingest_api",
    "cdp_api",
    "cdp_query_api",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching *pattern* under *root*, sorted."""
    return sorted(root.rglob(pattern))


def _parse_xml(path: Path) -> ElementTree.Element | None:
    """Parse an XML file and return the root element, or None on error."""
    try:
        tree = ElementTree.parse(path)
        return tree.getroot()
    except ElementTree.ParseError:
        return None


def _tag(local_name: str) -> str:
    """Return a namespace-qualified tag for Salesforce metadata XML."""
    return f"{{{SALESFORCE_NS}}}{local_name}"


def _text(element: ElementTree.Element, local_name: str) -> str:
    """Return text content of a child element, or empty string."""
    child = element.find(_tag(local_name))
    return (child.text or "").strip() if child is not None else ""


# ---------------------------------------------------------------------------
# Check: Connected Apps missing cdp_ingest_api scope
# ---------------------------------------------------------------------------

def check_connected_apps(manifest_dir: Path) -> list[str]:
    """Check Connected App metadata for missing or insufficient OAuth scopes."""
    issues: list[str] = []
    connected_app_dir = manifest_dir / "connectedApps"
    if not connected_app_dir.exists():
        return issues

    for app_file in _find_files(connected_app_dir, "*.connectedApp-meta.xml"):
        root = _parse_xml(app_file)
        if root is None:
            issues.append(f"Could not parse Connected App metadata: {app_file.name}")
            continue

        # Collect all OAuth scope values in this connected app.
        oauth_config = root.find(_tag("oauthConfig"))
        if oauth_config is None:
            continue

        scopes: set[str] = set()
        for scope_elem in oauth_config.findall(_tag("scopes")):
            if scope_elem.text:
                scopes.add(scope_elem.text.strip())

        # If the app has any Data Cloud-related scope but is missing cdp_ingest_api,
        # it may be intended as an Ingestion API app but is misconfigured.
        has_dc_scope = bool(scopes & INGESTION_INDICATOR_SCOPES)
        has_ingest_scope = REQUIRED_INGESTION_SCOPE in scopes

        if has_dc_scope and not has_ingest_scope:
            issues.append(
                f"Connected App '{app_file.stem.replace('.connectedApp-meta', '')}': "
                f"has Data Cloud-related OAuth scope(s) but is missing the required "
                f"'cdp_ingest_api' scope. Ingestion API source registration will fail "
                f"without this scope. Add 'cdp_ingest_api' to the app's OAuth scopes."
            )

    return issues


# ---------------------------------------------------------------------------
# Check: Custom (cloned) Data Cloud permission sets
# ---------------------------------------------------------------------------

def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Detect permission sets that appear to be clones of standard Data Cloud sets."""
    issues: list[str] = []
    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return issues

    for ps_file in _find_files(ps_dir, "*.permissionset-meta.xml"):
        ps_api_name = ps_file.stem.replace(".permissionset-meta", "")

        # Skip the known standard sets themselves.
        if ps_api_name in STANDARD_DC_PERMISSION_SETS:
            continue

        # Check if the name looks like a clone of a standard Data Cloud permission set.
        for pattern in DC_PERM_SET_CLONE_PATTERNS:
            if pattern.search(ps_api_name):
                issues.append(
                    f"Permission Set '{ps_api_name}' appears to be a custom clone of a "
                    f"standard Data Cloud permission set. Cloning Data Cloud permission "
                    f"sets transfers maintenance to the org admin and may miss capability "
                    f"updates in future releases. Use the six standard Salesforce-managed "
                    f"Data Cloud permission sets instead, assigning multiple if needed."
                )
                break

    return issues


# ---------------------------------------------------------------------------
# Check: Data space membership notes in deployment metadata
# ---------------------------------------------------------------------------

def check_for_data_space_notes(manifest_dir: Path) -> list[str]:
    """Warn if Connected Apps for Ingestion API exist but no data space notes are present.

    This is a soft check — it cannot inspect live org configuration, but it can
    remind the deployer to verify data space membership was completed manually in Setup.
    """
    issues: list[str] = []
    connected_app_dir = manifest_dir / "connectedApps"
    if not connected_app_dir.exists():
        return issues

    ingest_apps_found = False
    for app_file in _find_files(connected_app_dir, "*.connectedApp-meta.xml"):
        root = _parse_xml(app_file)
        if root is None:
            continue
        oauth_config = root.find(_tag("oauthConfig"))
        if oauth_config is None:
            continue
        for scope_elem in oauth_config.findall(_tag("scopes")):
            if scope_elem.text and scope_elem.text.strip() == REQUIRED_INGESTION_SCOPE:
                ingest_apps_found = True
                break

    if ingest_apps_found:
        # Check for a provisioning notes or README that mentions data spaces.
        notes_files = (
            list(manifest_dir.parent.glob("*provisioning*"))
            + list(manifest_dir.parent.glob("*data-space*"))
            + list(manifest_dir.parent.glob("*DATACLOUD*"))
        )
        if not notes_files:
            issues.append(
                "Ingestion API Connected App(s) detected in metadata, but no provisioning "
                "notes file found. Reminder: data space membership for each user must be "
                "completed manually in Data Cloud Setup (Data Spaces > Manage Assignments). "
                "Permission set assignment alone does NOT grant data space access."
            )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Data Cloud provisioning issues: "
            "missing cdp_ingest_api OAuth scope on Connected Apps, custom clones of "
            "standard Data Cloud permission sets, and missing data space assignment reminders."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory containing Salesforce metadata subfolders "
            "(connectedApps/, permissionsets/, etc.). Default: current directory."
        ),
    )
    return parser.parse_args()


def check_data_cloud_provisioning(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_connected_apps(manifest_dir))
    issues.extend(check_permission_sets(manifest_dir))
    issues.extend(check_for_data_space_notes(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_cloud_provisioning(manifest_dir)

    if not issues:
        print("No Data Cloud provisioning issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
