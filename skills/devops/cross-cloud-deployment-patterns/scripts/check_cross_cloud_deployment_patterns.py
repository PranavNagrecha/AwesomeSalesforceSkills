#!/usr/bin/env python3
"""Checker script for Cross-Cloud Deployment Patterns skill.

Validates a Salesforce metadata directory or package.xml for common cross-cloud
deployment anti-patterns: SiteDotCom in manifests, mixed-layer packages, and
Experience types deployed alongside foundation types in the same manifest.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_cross_cloud_deployment_patterns.py --help
    python3 check_cross_cloud_deployment_patterns.py --manifest-dir path/to/metadata
    python3 check_cross_cloud_deployment_patterns.py --package-xml path/to/package.xml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Layer classification — maps metadata type names to deployment layers.
# Layer 1 = foundation (custom objects, Apex, etc.)
# Layer 2 = network (Network, CustomSite)
# Layer 3 = experience (ExperienceBundle, DigitalExperienceBundle)
# ---------------------------------------------------------------------------

FOUNDATION_TYPES: set[str] = {
    "CustomObject",
    "CustomField",
    "CustomMetadata",
    "ApexClass",
    "ApexTrigger",
    "ApexPage",
    "ApexComponent",
    "LightningComponentBundle",
    "AuraDefinitionBundle",
    "PermissionSet",
    "PermissionSetGroup",
    "Profile",
    "CustomLabel",
    "CustomSetting",
    "StaticResource",
    "FlexiPage",
    "Layout",
    "RecordType",
    "ValidationRule",
    "WorkflowRule",
    "Flow",
    "Queue",
    "Group",
    "Role",
    "AssignmentRule",
    "AutoResponseRule",
    "EscalationRule",
}

NETWORK_TYPES: set[str] = {
    "Network",
    "CustomSite",
    "SiteDotCom",  # not deployable — flag if found in any manifest
}

EXPERIENCE_TYPES: set[str] = {
    "ExperienceBundle",
    "DigitalExperienceBundle",
}

NON_DEPLOYABLE_TYPES: set[str] = {
    "SiteDotCom",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata directory or package.xml for cross-cloud "
            "deployment anti-patterns."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce DX project or metadata directory.",
    )
    parser.add_argument(
        "--package-xml",
        default=None,
        help="Path to a specific package.xml file to inspect.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_package_xmls(root: Path) -> list[Path]:
    """Return all package.xml files found under root."""
    return list(root.rglob("package.xml"))


def parse_package_xml(path: Path) -> dict[str, list[str]]:
    """Parse a package.xml and return {typeName: [members]} mapping."""
    try:
        tree = ElementTree.parse(path)
    except ElementTree.ParseError as exc:
        return {"__parse_error__": [str(exc)]}

    ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
    types: dict[str, list[str]] = {}
    root_elem = tree.getroot()

    for types_elem in root_elem.findall("sf:types", ns):
        name_elem = types_elem.find("sf:name", ns)
        if name_elem is None or not name_elem.text:
            continue
        type_name = name_elem.text.strip()
        members = [
            m.text.strip()
            for m in types_elem.findall("sf:members", ns)
            if m.text
        ]
        types[type_name] = members

    return types


def classify_type(type_name: str) -> str:
    """Return 'foundation', 'network', 'experience', or 'other'."""
    if type_name in FOUNDATION_TYPES:
        return "foundation"
    if type_name in NETWORK_TYPES:
        return "network"
    if type_name in EXPERIENCE_TYPES:
        return "experience"
    return "other"


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_package_for_mixed_layers(
    package_path: Path,
    types: dict[str, list[str]],
) -> list[str]:
    """Flag packages that mix experience types with foundation or network types."""
    issues: list[str] = []

    if "__parse_error__" in types:
        issues.append(
            f"{package_path}: XML parse error — {types['__parse_error__'][0]}"
        )
        return issues

    layers_present: set[str] = set()
    for type_name in types:
        layer = classify_type(type_name)
        if layer != "other":
            layers_present.add(layer)

    # Check for non-deployable types
    for type_name in types:
        if type_name in NON_DEPLOYABLE_TYPES:
            issues.append(
                f"{package_path}: contains non-deployable type '{type_name}'. "
                f"Remove '{type_name}' from this package.xml — it must never be deployed."
            )

    # Check for mixed foundation + experience in same package
    if "foundation" in layers_present and "experience" in layers_present:
        experience_types = [t for t in types if t in EXPERIENCE_TYPES]
        foundation_types = [t for t in types if t in FOUNDATION_TYPES]
        issues.append(
            f"{package_path}: mixes foundation types {foundation_types} and "
            f"experience types {experience_types} in the same package. "
            "Deploy foundation types first in a separate transaction to avoid "
            "'no Network named X found' errors."
        )

    # Check for experience types without network types being flagged
    # (network might already exist in target — this is advisory only)
    if "experience" in layers_present and "network" in layers_present:
        experience_types = [t for t in types if t in EXPERIENCE_TYPES]
        network_types = [t for t in types if t in NETWORK_TYPES and t not in NON_DEPLOYABLE_TYPES]
        issues.append(
            f"{package_path}: contains both network types {network_types} and "
            f"experience types {experience_types} in the same package. "
            "Network metadata (Network, CustomSite) must be deployed in a prior "
            "transaction so they are fully committed before ExperienceBundle is evaluated."
        )

    return issues


def check_for_sitedotcom_files(root: Path) -> list[str]:
    """Scan for SiteDotCom blob files in the project directory."""
    issues: list[str] = []
    patterns = ["*.site", "siteDotCom"]

    for pattern in patterns:
        matches = list(root.rglob(pattern))
        for match in matches:
            issues.append(
                f"SiteDotCom artifact found: {match}. "
                "Add '**/siteDotCom/**' and '*.site' to .forceignore to prevent "
                "accidental staging and deployment."
            )

    # Also check for directories named siteDotCom
    for d in root.rglob("*"):
        if d.is_dir() and d.name.lower() in {"sitedotcom", "site-dot-com"}:
            issues.append(
                f"SiteDotCom directory found: {d}. "
                "This directory contains non-deployable content. Add to .forceignore."
            )

    return issues


def check_forceignore_for_sitedotcom(root: Path) -> list[str]:
    """Warn if .forceignore does not exclude SiteDotCom."""
    issues: list[str] = []
    forceignore = root / ".forceignore"

    if not forceignore.exists():
        issues.append(
            f"{root}/.forceignore does not exist. "
            "Create it and add '**/siteDotCom/**' and '*.site' to prevent "
            "SiteDotCom blobs from being staged."
        )
        return issues

    content = forceignore.read_text(encoding="utf-8", errors="replace")
    has_sitedotcom_rule = bool(
        re.search(r"sitedotcom|SiteDotCom|\.site\b", content, re.IGNORECASE)
    )

    if not has_sitedotcom_rule:
        issues.append(
            f"{forceignore}: does not contain a SiteDotCom exclusion rule. "
            "Add '**/siteDotCom/**' and '*.site' to prevent accidental deployment."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_checks(manifest_dir: Path | None, package_xml_path: Path | None) -> list[str]:
    all_issues: list[str] = []

    # Determine which package.xml files to inspect
    if package_xml_path is not None:
        if not package_xml_path.exists():
            return [f"Package XML not found: {package_xml_path}"]
        packages_to_check = [package_xml_path]
        root_dir = package_xml_path.parent
    elif manifest_dir is not None:
        root_dir = manifest_dir
        if not root_dir.exists():
            return [f"Manifest directory not found: {root_dir}"]
        packages_to_check = find_package_xmls(root_dir)
        if not packages_to_check:
            all_issues.append(
                f"No package.xml files found under {root_dir}. "
                "Nothing to check — pass --package-xml for a specific file."
            )
    else:
        return ["No --manifest-dir or --package-xml provided. Nothing to check."]

    # Check each package.xml for mixed-layer anti-patterns
    for pkg_path in packages_to_check:
        types = parse_package_xml(pkg_path)
        all_issues.extend(check_package_for_mixed_layers(pkg_path, types))

    # Scan project root for SiteDotCom artifacts and .forceignore rules
    if manifest_dir is not None:
        all_issues.extend(check_for_sitedotcom_files(root_dir))
        all_issues.extend(check_forceignore_for_sitedotcom(root_dir))

    return all_issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir) if args.manifest_dir else None
    package_xml_path = Path(args.package_xml) if args.package_xml else None

    issues = run_checks(manifest_dir, package_xml_path)

    if not issues:
        print("No cross-cloud deployment anti-patterns detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
