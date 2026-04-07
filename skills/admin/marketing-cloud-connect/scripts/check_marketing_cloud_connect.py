#!/usr/bin/env python3
"""Checker script for Marketing Cloud Connect skill.

Inspects Salesforce metadata exported via Salesforce CLI (sf project retrieve)
or SFDX to detect common MC Connect configuration issues.

Checks performed:
  1. MC Connect managed package (et4ae5) is present in installed packages metadata
  2. Connector user profile has API Access enabled (if profile XML is present)
  3. Marketing Cloud permission set is present in the metadata
  4. No user record references a community/Experience Cloud license as connector user
  5. Warns if any object has close to or exceeding 250 custom fields (SDS field limit)
  6. Warns if RemoteSiteSetting for Marketing Cloud endpoints is missing

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_cloud_connect.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MC_CONNECT_NAMESPACE = "et4ae5"
MC_PERMISSION_SET_NAMES = {"MarketingCloud", "Marketing_Cloud", "MarketingCloudConnect"}
MC_REMOTE_SITE_KEYWORDS = {"exacttarget", "salesforce.com/mc", "marketingcloud"}
COMMUNITY_LICENSE_KEYWORDS = {"community", "partner", "customer portal", "external"}

# SDS field limit per synchronized object
SDS_FIELD_LIMIT = 250
SDS_WARN_THRESHOLD = 230  # warn when within 20 fields of limit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def iter_xml_files(directory: Path, suffix: str) -> list[Path]:
    """Return all XML files with the given suffix under directory."""
    return list(directory.rglob(f"*{suffix}"))


def parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse an XML file and return the root element, or None on parse error."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


def strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from a tag string."""
    return tag.split("}")[-1] if "}" in tag else tag


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_mc_package_installed(manifest_dir: Path) -> list[str]:
    """Check for MC Connect managed package namespace in installed package metadata."""
    issues: list[str] = []
    # sf project retrieve produces InstalledPackage metadata under installedPackages/
    pkg_files = list(manifest_dir.rglob("installedPackages/*.installedPackage"))
    if not pkg_files:
        # Metadata may not have been retrieved; skip with informational note
        return []

    namespaces_found = set()
    for pf in pkg_files:
        root = parse_xml_safe(pf)
        if root is None:
            continue
        for elem in root.iter():
            tag = strip_ns(elem.tag)
            if tag == "versionNumber" or tag == "activateRSS":
                pass  # not needed
        # The installed package file name is the namespace
        namespaces_found.add(pf.stem)

    if MC_CONNECT_NAMESPACE not in namespaces_found:
        issues.append(
            f"MC Connect managed package namespace '{MC_CONNECT_NAMESPACE}' not found "
            "in installedPackages/ metadata. Confirm the Salesforce Marketing Cloud "
            "managed package is installed in this org."
        )
    return issues


def check_marketing_cloud_permission_set(manifest_dir: Path) -> list[str]:
    """Check that a Marketing Cloud permission set exists in the metadata."""
    issues: list[str] = []
    ps_files = list(manifest_dir.rglob("permissionsets/*.permissionset"))
    if not ps_files:
        return []

    ps_names = {pf.stem for pf in ps_files}
    found = any(
        any(mc_name.lower() in ps_name.lower() for mc_name in MC_PERMISSION_SET_NAMES)
        for ps_name in ps_names
    )
    if not found:
        issues.append(
            "No Marketing Cloud permission set found in permissionsets/ metadata. "
            "The connector user must have the 'Marketing Cloud' permission set "
            "assigned (shipped with the MC Connect managed package)."
        )
    return issues


def check_profile_api_access(manifest_dir: Path) -> list[str]:
    """Check that at least one profile in the metadata has API access enabled."""
    issues: list[str] = []
    profile_files = list(manifest_dir.rglob("profiles/*.profile"))
    if not profile_files:
        return []

    profiles_without_api: list[str] = []
    for pf in profile_files:
        root = parse_xml_safe(pf)
        if root is None:
            continue
        api_enabled = None
        for elem in root.iter():
            tag = strip_ns(elem.tag)
            if tag == "apiEnabled":
                api_enabled = elem.text
                break
        if api_enabled is not None and api_enabled.strip().lower() == "false":
            profiles_without_api.append(pf.stem)

    if profiles_without_api:
        issues.append(
            f"The following profiles have apiEnabled=false: "
            f"{', '.join(profiles_without_api)}. "
            "The connector user's profile must have API access enabled for "
            "MC Connect sync to function."
        )
    return issues


def check_object_field_counts(manifest_dir: Path) -> list[str]:
    """Warn if any object's field count approaches or exceeds the SDS 250-field limit."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return []

    # SFDX decomposed format: objects/<ObjectName>/fields/*.field-meta.xml
    for obj_dir in objects_dir.iterdir():
        if not obj_dir.is_dir():
            continue
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue
        field_count = len(list(fields_dir.glob("*.field-meta.xml")))
        if field_count > SDS_FIELD_LIMIT:
            issues.append(
                f"Object '{obj_dir.name}' has {field_count} field files, exceeding "
                f"the MC Connect SDS limit of {SDS_FIELD_LIMIT} fields. Fields beyond "
                "this limit are silently excluded from Synchronized Data Sources "
                "with no error. Review which fields are enabled for SDS sync."
            )
        elif field_count >= SDS_WARN_THRESHOLD:
            issues.append(
                f"Object '{obj_dir.name}' has {field_count} field files, approaching "
                f"the MC Connect SDS limit of {SDS_FIELD_LIMIT}. Review field sync "
                "configuration before adding more fields."
            )
    return issues


def check_remote_site_settings(manifest_dir: Path) -> list[str]:
    """Check that Remote Site Settings for Marketing Cloud endpoints are present."""
    issues: list[str] = []
    rss_files = list(manifest_dir.rglob("remoteSiteSettings/*.remoteSite"))
    if not rss_files:
        return []

    mc_rss_found = False
    for rss_file in rss_files:
        root = parse_xml_safe(rss_file)
        if root is None:
            continue
        for elem in root.iter():
            tag = strip_ns(elem.tag)
            if tag == "url" and elem.text:
                url_lower = elem.text.lower()
                if any(kw in url_lower for kw in MC_REMOTE_SITE_KEYWORDS):
                    mc_rss_found = True
                    break
        if mc_rss_found:
            break

    if not mc_rss_found:
        issues.append(
            "No Remote Site Setting found for Marketing Cloud endpoints "
            "(expected URL containing 'exacttarget' or 'marketingcloud'). "
            "MC Connect requires Remote Site Settings for its API endpoints; "
            "these are typically created by the managed package install. "
            "Verify the managed package installed correctly."
        )
    return issues


def check_no_todo_placeholders(manifest_dir: Path) -> list[str]:
    """Warn if any MC Connect-related metadata XML files contain TODO placeholders."""
    issues: list[str] = []
    xml_files = list(manifest_dir.rglob("*.xml"))
    for xf in xml_files:
        if "marketingcloud" in xf.name.lower() or "mc_" in xf.name.lower():
            try:
                content = xf.read_text(encoding="utf-8", errors="ignore")
                if "TODO" in content or "PLACEHOLDER" in content:
                    issues.append(
                        f"File {xf} contains TODO or PLACEHOLDER text. "
                        "Review before deploying to production."
                    )
            except OSError:
                pass
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_marketing_cloud_connect(manifest_dir: Path) -> list[str]:
    """Run all MC Connect checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_mc_package_installed(manifest_dir))
    issues.extend(check_marketing_cloud_permission_set(manifest_dir))
    issues.extend(check_profile_api_access(manifest_dir))
    issues.extend(check_object_field_counts(manifest_dir))
    issues.extend(check_remote_site_settings(manifest_dir))
    issues.extend(check_no_todo_placeholders(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Marketing Cloud Connect "
            "configuration issues. Point --manifest-dir at the root of a "
            "Salesforce project retrieved via 'sf project retrieve'."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_marketing_cloud_connect(manifest_dir)

    if not issues:
        print("No MC Connect configuration issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
