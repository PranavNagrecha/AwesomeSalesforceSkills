#!/usr/bin/env python3
"""Checker script for Integration User Management skill.

Checks org metadata or configuration relevant to Integration User Management.
Uses stdlib only — no pip dependencies.

Checks performed:
  1. Scans profile XML files for integration-named profiles using non-API-only settings.
  2. Scans permission set XML files assigned to integration-named users for over-broad object access.
  3. Warns if no 'Minimum Access - API Only' profile XML is found in the manifest.
  4. Detects permission sets that include 'System Administrator' or admin-cloned patterns.
  5. Checks for LoginHistory-related query files or SOQL references in the manifest directory.

Usage:
    python3 check_integration_user_management.py [--help]
    python3 check_integration_user_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Profile names that indicate the integration user is misconfigured
PROHIBITED_PROFILES_FOR_INTEGRATION = {
    "system administrator",
    "standard user",
    "salesforce api only system integrations",  # legacy name sometimes seen
}

# The correct profile name for integration users
CORRECT_INTEGRATION_PROFILE = "minimum access - api only integrations"

# Keywords that suggest a file or username is integration-related
INTEGRATION_KEYWORDS = [
    "integration",
    "api-user",
    "apiuser",
    "service-account",
    "serviceaccount",
    "mulesoft",
    "middleware",
    "etl",
    "dataloader",
]

# Object permission fields in Salesforce metadata XML
OBJECT_PERM_FIELDS = {
    "allowCreate",
    "allowDelete",
    "allowEdit",
    "allowRead",
    "modifyAllRecords",
    "viewAllRecords",
}

# Threshold: warn if a permission set grants access to more than this many top-level objects
OBJECT_PERMISSION_COUNT_THRESHOLD = 10


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_integration_related(name: str) -> bool:
    """Return True if the name suggests an integration user or permission set."""
    lower = name.lower()
    return any(kw in lower for kw in INTEGRATION_KEYWORDS)


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from a tag string."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def get_text(element: ET.Element, child_tag: str) -> str:
    """Return stripped text of first matching child tag, or empty string."""
    child = element.find(f".//{child_tag}")
    if child is not None and child.text:
        return child.text.strip()
    # Also try namespace-stripped search
    for el in element.iter():
        if strip_ns(el.tag) == child_tag:
            return (el.text or "").strip()
    return ""


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_profiles(manifest_dir: Path) -> list[str]:
    """Check profile metadata files for integration users on prohibited profiles."""
    issues: list[str] = []
    profiles_dir = manifest_dir / "profiles"

    if not profiles_dir.exists():
        # Not every repo layout has a profiles/ directory; not an error
        return issues

    profile_files = list(profiles_dir.glob("*.profile-meta.xml")) + list(
        profiles_dir.glob("*.profile")
    )

    found_api_only_profile = False

    for pf in profile_files:
        stem = pf.stem.replace(".profile-meta", "").replace(".profile", "")
        lower_stem = stem.lower()

        if CORRECT_INTEGRATION_PROFILE in lower_stem or "api only" in lower_stem:
            found_api_only_profile = True

        if is_integration_related(stem):
            root = parse_xml_safe(pf)
            if root is None:
                issues.append(f"Could not parse profile XML: {pf}")
                continue

            # Check userLicense node
            user_license = get_text(root, "userLicense")
            # Check if the profile has loginIpRanges or apiOnly indicators
            # In profile XML, API-only is indicated by not having a loginHours or
            # by the profile being the Minimum Access - API Only type.
            # We check for the presence of a <userLicense> that is NOT
            # 'Salesforce Integration'.
            if user_license and user_license.lower() not in (
                "salesforce integration",
                "salesforce api integration",
                "",
            ):
                issues.append(
                    f"Profile '{stem}' appears integration-related but has "
                    f"userLicense='{user_license}'. Expected 'Salesforce Integration'."
                )

            # Warn if profile name suggests admin
            if any(p in lower_stem for p in ["administrator", "admin", "sysadmin"]):
                issues.append(
                    f"Profile '{stem}' has 'admin' in its name and appears integration-related. "
                    "Integration users should use 'Minimum Access - API Only Integrations', "
                    "not an admin profile."
                )

    if profile_files and not found_api_only_profile:
        issues.append(
            "No 'Minimum Access - API Only Integrations' profile XML found in profiles/. "
            "Ensure integration users are on this profile, not a standard or admin profile."
        )

    return issues


def check_permission_sets(manifest_dir: Path) -> list[str]:
    """Check permission set metadata files for over-broad object access."""
    issues: list[str] = []
    ps_dir = manifest_dir / "permissionsets"

    if not ps_dir.exists():
        return issues

    ps_files = list(ps_dir.glob("*.permissionset-meta.xml")) + list(
        ps_dir.glob("*.permissionset")
    )

    for psf in ps_files:
        stem = psf.stem.replace(".permissionset-meta", "").replace(".permissionset", "")

        if not is_integration_related(stem):
            continue

        root = parse_xml_safe(psf)
        if root is None:
            issues.append(f"Could not parse permission set XML: {psf}")
            continue

        # Count objectPermissions entries
        obj_perms = [
            el for el in root.iter()
            if strip_ns(el.tag) == "objectPermissions"
        ]

        if len(obj_perms) > OBJECT_PERMISSION_COUNT_THRESHOLD:
            issues.append(
                f"Permission set '{stem}' grants access to {len(obj_perms)} objects. "
                f"Integration permission sets should be scoped tightly (threshold: "
                f"{OBJECT_PERMISSION_COUNT_THRESHOLD}). Review for over-permissioning."
            )

        # Check for modifyAllRecords or viewAllRecords on any object
        for op in obj_perms:
            obj_name = ""
            modify_all = False
            view_all = False

            for child in op:
                tag = strip_ns(child.tag)
                text = (child.text or "").strip().lower()
                if tag == "object":
                    obj_name = child.text or ""
                elif tag == "modifyAllRecords" and text == "true":
                    modify_all = True
                elif tag == "viewAllRecords" and text == "true":
                    view_all = True

            if modify_all:
                issues.append(
                    f"Permission set '{stem}' grants ModifyAllRecords on '{obj_name}'. "
                    "Integration users should not have ModifyAllRecords unless explicitly required."
                )
            if view_all:
                issues.append(
                    f"Permission set '{stem}' grants ViewAllRecords on '{obj_name}'. "
                    "Verify this is required — ViewAllRecords bypasses sharing rules."
                )

        # Check for system permissions that indicate admin-level access
        sys_perms = [
            el for el in root.iter()
            if strip_ns(el.tag) == "systemPermissions"
        ]
        admin_like_permissions = {
            "ManageUsers",
            "ModifyAllData",
            "ViewAllData",
            "AuthorApex",
            "CustomizeApplication",
        }
        for sp in sys_perms:
            perm_name = ""
            perm_enabled = False
            for child in sp:
                tag = strip_ns(child.tag)
                text = (child.text or "").strip()
                if tag == "name":
                    perm_name = text
                elif tag == "enabled" and text.lower() == "true":
                    perm_enabled = True
            if perm_enabled and perm_name in admin_like_permissions:
                issues.append(
                    f"Permission set '{stem}' enables system permission '{perm_name}'. "
                    "This is an admin-level permission and should not be granted to integration users."
                )

    return issues


def check_connected_app_run_as(manifest_dir: Path) -> list[str]:
    """Warn if Connected App XML files reference a 'run as' user that looks admin-like."""
    issues: list[str] = []
    ca_dir = manifest_dir / "connectedApps"

    if not ca_dir.exists():
        return issues

    ca_files = list(ca_dir.glob("*.connectedApp-meta.xml")) + list(
        ca_dir.glob("*.connectedApp")
    )

    for caf in ca_files:
        root = parse_xml_safe(caf)
        if root is None:
            issues.append(f"Could not parse Connected App XML: {caf}")
            continue

        # Look for oauthConfig/runAs or oauthClientCredentialUser elements
        run_as = get_text(root, "runAs") or get_text(root, "oauthClientCredentialUser")
        if run_as:
            if any(kw in run_as.lower() for kw in ["admin", "sysadmin", "administrator"]):
                issues.append(
                    f"Connected App '{caf.stem}' has runAs/oauthClientCredentialUser='{run_as}'. "
                    "The run-as user appears to be an admin account. "
                    "Set this to the dedicated integration user, not an admin."
                )
            elif not is_integration_related(run_as):
                issues.append(
                    f"Connected App '{caf.stem}' has runAs/oauthClientCredentialUser='{run_as}'. "
                    "Verify this is the correct dedicated integration user and not a personal account."
                )

    return issues


def check_login_history_monitoring(manifest_dir: Path) -> list[str]:
    """Warn if no SOQL or report referencing LoginHistory is found anywhere in the manifest."""
    issues: list[str] = []

    # Search for any .soql, .sql, or report files referencing LoginHistory
    soql_files = list(manifest_dir.rglob("*.soql")) + list(manifest_dir.rglob("*.sql"))
    login_history_referenced = False

    for sf in soql_files:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
            if "LoginHistory" in content:
                login_history_referenced = True
                break
        except OSError:
            continue

    # Also check reports directory for LoginHistory-related reports
    reports_dir = manifest_dir / "reports"
    if reports_dir.exists():
        report_files = list(reports_dir.rglob("*.report-meta.xml"))
        for rf in report_files:
            try:
                content = rf.read_text(encoding="utf-8", errors="ignore")
                if "LoginHistory" in content:
                    login_history_referenced = True
                    break
            except OSError:
                continue

    if not login_history_referenced and (soql_files or (reports_dir.exists() and report_files)):
        issues.append(
            "No LoginHistory reference found in SOQL files or reports. "
            "Integration user login monitoring requires querying LoginHistory via SOQL or a scheduled report. "
            "Add a LoginHistory query or report scoped to the integration user's Id."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Integration User Management configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_integration_user_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_profiles(manifest_dir))
    issues.extend(check_permission_sets(manifest_dir))
    issues.extend(check_connected_app_run_as(manifest_dir))
    issues.extend(check_login_history_monitoring(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_integration_user_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
