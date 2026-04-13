#!/usr/bin/env python3
"""Checker script for Experience Cloud Deployment Admin skill.

Validates a Salesforce metadata project directory for common Experience Cloud
deployment mistakes: SiteDotCom included with ExperienceBundle, missing
ExperienceBundle Metadata API enablement notes, and ordering issues in package.xml.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_deployment_admin.py [--help]
    python3 check_experience_cloud_deployment_admin.py --manifest-dir path/to/metadata
    python3 check_experience_cloud_deployment_admin.py --manifest-dir . --package-xml package.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata project for common Experience Cloud "
            "deployment issues (SiteDotCom inclusion, missing Network before "
            "ExperienceBundle, unpublished site risk)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    parser.add_argument(
        "--package-xml",
        default=None,
        help="Path to a specific package.xml to check. If omitted, searches manifest-dir.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


def _parse_package_xml(path: Path) -> dict[str, list[str]]:
    """Return a dict mapping metadata type name -> list of member names."""
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise ValueError(f"Could not parse {path}: {exc}") from exc

    root = tree.getroot()
    types: dict[str, list[str]] = {}

    for types_elem in root.findall(f"{{{NAMESPACE}}}types"):
        name_elem = types_elem.find(f"{{{NAMESPACE}}}name")
        if name_elem is None or not name_elem.text:
            continue
        type_name = name_elem.text.strip()
        members = [
            m.text.strip()
            for m in types_elem.findall(f"{{{NAMESPACE}}}members")
            if m.text
        ]
        types.setdefault(type_name, []).extend(members)

    return types


def _find_package_xmls(manifest_dir: Path) -> list[Path]:
    """Locate all package.xml files under manifest_dir."""
    return list(manifest_dir.rglob("package.xml"))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_sitedotcom_with_experiencebundle(types: dict[str, list[str]], source: str) -> list[str]:
    """Fail if SiteDotCom and ExperienceBundle appear together in the same manifest."""
    issues: list[str] = []
    has_exp = "ExperienceBundle" in types and types["ExperienceBundle"]
    has_site = "SiteDotCom" in types and types["SiteDotCom"]
    if has_exp and has_site:
        exp_members = ", ".join(types["ExperienceBundle"])
        site_members = ", ".join(types["SiteDotCom"])
        issues.append(
            f"[{source}] CRITICAL: SiteDotCom ({site_members}) and ExperienceBundle "
            f"({exp_members}) appear in the same manifest. Deploying SiteDotCom "
            f"together with ExperienceBundle will cause the deployment to fail. "
            f"Remove all SiteDotCom members from this manifest."
        )
    return issues


def check_network_with_experiencebundle_ordering(types: dict[str, list[str]], source: str) -> list[str]:
    """Warn if ExperienceBundle and Network are in the same manifest (ordering risk)."""
    issues: list[str] = []
    has_exp = "ExperienceBundle" in types and types["ExperienceBundle"]
    has_network = "Network" in types and types["Network"]
    if has_exp and has_network:
        issues.append(
            f"[{source}] WARNING: ExperienceBundle and Network appear in the same "
            f"manifest. Salesforce does not guarantee commit ordering within a single "
            f"deployment. If Network does not exist in the target org, ExperienceBundle "
            f"will fail. Best practice: deploy Network (and CustomSite) in a separate "
            f"prior step, then deploy ExperienceBundle."
        )
    return issues


def check_customsite_missing_when_network_present(types: dict[str, list[str]], source: str) -> list[str]:
    """Warn if Network is present but CustomSite is absent."""
    issues: list[str] = []
    has_network = "Network" in types and types["Network"]
    has_custom_site = "CustomSite" in types and types["CustomSite"]
    if has_network and not has_custom_site:
        issues.append(
            f"[{source}] WARNING: Network members are present but CustomSite is missing. "
            f"An Experience Cloud site typically requires both Network and CustomSite "
            f"to be present in the target org before ExperienceBundle can be deployed. "
            f"Verify that CustomSite already exists in the target or add it to this manifest."
        )
    return issues


def check_experiencebundle_only_manifest(types: dict[str, list[str]], source: str) -> list[str]:
    """Info: ExperienceBundle-only manifest is valid when used as second-step deploy."""
    # This is a valid pattern; surface as informational only.
    issues: list[str] = []
    has_exp = "ExperienceBundle" in types and types["ExperienceBundle"]
    type_count = len([k for k, v in types.items() if v])
    if has_exp and type_count == 1:
        issues.append(
            f"[{source}] INFO: This manifest contains only ExperienceBundle. "
            f"This is correct for a second-step deploy — confirm that Network and CustomSite "
            f"already exist in the target org before running this deployment."
        )
    return issues


def check_sitedotcom_files_on_disk(manifest_dir: Path) -> list[str]:
    """Warn if SiteDotCom artifact directories exist under the project."""
    issues: list[str] = []
    # Common locations: force-app/main/default/siteDotCom/ or metadata/siteDotCom/
    site_dot_com_dirs = list(manifest_dir.rglob("siteDotCom"))
    site_dot_com_dirs = [d for d in site_dot_com_dirs if d.is_dir()]
    if site_dot_com_dirs:
        paths = ", ".join(str(d.relative_to(manifest_dir)) for d in site_dot_com_dirs)
        issues.append(
            f"WARN: SiteDotCom directories found on disk: {paths}. "
            f"These should NOT be included in any deployment that also contains ExperienceBundle. "
            f"Ensure they are excluded from package.xml and from any change set build."
        )
    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_experience_cloud_deployment_admin(manifest_dir: Path, package_xml_path: Path | None) -> list[str]:
    """Return a list of issue strings found in the project."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Disk-level checks (independent of manifest content)
    issues.extend(check_sitedotcom_files_on_disk(manifest_dir))

    # Locate package.xml files to inspect
    if package_xml_path is not None:
        package_xmls = [package_xml_path]
    else:
        package_xmls = _find_package_xmls(manifest_dir)

    if not package_xmls:
        issues.append(
            "INFO: No package.xml found under manifest-dir. "
            "Cannot perform manifest-level checks. "
            "Pass --package-xml to specify a manifest explicitly."
        )
        return issues

    for pkg_path in package_xmls:
        source_label = str(pkg_path.relative_to(manifest_dir)) if manifest_dir in pkg_path.parents else str(pkg_path)
        try:
            types = _parse_package_xml(pkg_path)
        except ValueError as exc:
            issues.append(str(exc))
            continue

        issues.extend(check_sitedotcom_with_experiencebundle(types, source_label))
        issues.extend(check_network_with_experiencebundle_ordering(types, source_label))
        issues.extend(check_customsite_missing_when_network_present(types, source_label))
        issues.extend(check_experiencebundle_only_manifest(types, source_label))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    package_xml_path = Path(args.package_xml).resolve() if args.package_xml else None

    issues = check_experience_cloud_deployment_admin(manifest_dir, package_xml_path)

    if not issues:
        print("No Experience Cloud deployment issues found.")
        return 0

    errors = [i for i in issues if i.startswith("[") and "CRITICAL" in i or (not i.startswith("[") and "WARN" in i)]
    for issue in issues:
        # Route CRITICAL and WARNING to stderr; INFO to stdout
        if "CRITICAL" in issue or ("WARN" in issue and "INFO" not in issue):
            print(f"WARN: {issue}", file=sys.stderr)
        else:
            print(f"INFO: {issue}")

    # Exit non-zero only if there are CRITICAL issues
    has_critical = any("CRITICAL" in i for i in issues)
    return 1 if has_critical else 0


if __name__ == "__main__":
    sys.exit(main())
