#!/usr/bin/env python3
"""Checker script for FSC Deployment Patterns skill.

Scans a Salesforce metadata directory for FSC deployment anti-patterns:
  - FinServ__ namespace presence (flags for namespace model audit)
  - Participant Role custom metadata lacking FinancialAccountRole references
  - package.xml including IndustriesSettings without RecordType (ordering risk)
  - FSC metadata components combined in a single manifest without phase separation

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_deployment_patterns.py --manifest-dir path/to/metadata
    python3 check_fsc_deployment_patterns.py --manifest-dir . --package-xml package.xml
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FINSVC_PATTERN = re.compile(r'FinServ__\w+')

# FSC component types that must be deployed in a specific order
PHASE_ORDER = [
    "RecordType",
    "IndustriesSettings",
    "ParticipantRole",
]

# Metadata types that are safe to deploy in any order relative to FSC sequencing
NEUTRAL_TYPES = {
    "ApexClass", "ApexTrigger", "ApexPage", "ApexComponent",
    "LightningComponentBundle", "AuraDefinitionBundle",
    "CustomLabel", "CustomMetadata", "Workflow", "Flow",
    "Profile", "PermissionSet", "PermissionSetGroup",
}


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_namespace_contamination(manifest_dir: Path) -> list[str]:
    """Detect FinServ__-prefixed API names in metadata XML files."""
    issues: list[str] = []
    xml_files = list(manifest_dir.rglob("*.xml"))

    if not xml_files:
        return issues

    contaminated: dict[str, list[str]] = {}
    for xml_file in xml_files:
        try:
            text = xml_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        matches = FINSVC_PATTERN.findall(text)
        if matches:
            contaminated[str(xml_file.relative_to(manifest_dir))] = list(set(matches))

    if contaminated:
        issues.append(
            "FinServ__ namespace detected in metadata artifacts. "
            "This package is only compatible with managed-package FSC orgs. "
            "If the target org uses platform-native Core FSC (Winter '23+), "
            "all FinServ__-prefixed API names must be rewritten before deployment. "
            f"Affected files ({len(contaminated)}): "
            + "; ".join(
                f"{path}: {names[:3]}{'...' if len(names) > 3 else ''}"
                for path, names in list(contaminated.items())[:5]
            )
        )

    return issues


def check_package_xml_ordering(package_xml_path: Path) -> list[str]:
    """Check package.xml for FSC component ordering risks.

    Flags if IndustriesSettings is present alongside RecordType or ParticipantRole
    in a single manifest (indicating a single-wave deploy that may fail due to
    FSC dependency ordering requirements).
    """
    issues: list[str] = []

    if not package_xml_path.exists():
        return issues

    try:
        tree = ET.parse(package_xml_path)
    except ET.ParseError as exc:
        issues.append(f"package.xml parse error: {exc}")
        return issues

    root = tree.getroot()
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    types_present: set[str] = set()
    for types_elem in root.findall(f"{ns}types"):
        name_elem = types_elem.find(f"{ns}name")
        if name_elem is not None and name_elem.text:
            types_present.add(name_elem.text.strip())

    # Check for single-wave deploy with sequencing risk
    fsc_types_in_package = [t for t in PHASE_ORDER if t in types_present]

    if len(fsc_types_in_package) > 1:
        issues.append(
            f"package.xml contains multiple FSC sequencing-sensitive metadata types "
            f"in a single manifest: {fsc_types_in_package}. "
            f"FSC deployment requires these types to land in strict sequence: "
            f"RecordType → IndustriesSettings → ParticipantRole. "
            f"Split into separate deployment waves to avoid dependency errors. "
            f"See SKILL.md § Recommended Workflow for the phased deployment pattern."
        )

    # Check for IndustriesSettings without RecordType (missing pre-condition)
    if "IndustriesSettings" in types_present and "RecordType" not in types_present:
        issues.append(
            "package.xml includes IndustriesSettings but not RecordType. "
            "Ensure Account record types (Household, Person_Account) were deployed "
            "in a prior wave before this manifest is applied. "
            "Deploying IndustriesSettings before record types exist may leave "
            "Participant Role custom metadata with unresolvable references."
        )

    return issues


def check_participant_role_metadata(manifest_dir: Path) -> list[str]:
    """Check ParticipantRole custom metadata files for common issues."""
    issues: list[str] = []

    # Custom metadata files can live under customMetadata/ directory
    cmdt_dirs = list(manifest_dir.rglob("customMetadata"))
    participant_role_files: list[Path] = []

    for cmdt_dir in cmdt_dirs:
        if cmdt_dir.is_dir():
            participant_role_files.extend(cmdt_dir.glob("ParticipantRole*.md-meta.xml"))
            participant_role_files.extend(cmdt_dir.glob("FinServ__ParticipantRole*.md-meta.xml"))

    if not participant_role_files:
        return issues

    for prf in participant_role_files:
        try:
            text = prf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # Check for empty or placeholder record type references
        if "RecordType" in text and ("TODO" in text or "PLACEHOLDER" in text):
            issues.append(
                f"{prf.name}: ParticipantRole custom metadata contains a TODO or "
                f"PLACEHOLDER in a RecordType reference field. This will deploy "
                f"successfully but the CDS engine will silently ignore this role "
                f"at runtime, resulting in no share-table rows being written."
            )

        # Check for namespace consistency — FinServ__ParticipantRole in a non-namespaced dir
        if "FinServ__ParticipantRole" in prf.name:
            # Check if the enclosing metadata also uses bare (non-namespaced) object refs
            if "FinancialAccount" in text and "FinServ__FinancialAccount" not in text:
                issues.append(
                    f"{prf.name}: ParticipantRole custom metadata file uses FinServ__ "
                    f"namespace in filename but references bare FinancialAccount API names "
                    f"in its XML. This may indicate a namespace mismatch between the file "
                    f"naming convention and the target object model."
                )

    return issues


def check_person_account_sentinel(manifest_dir: Path) -> list[str]:
    """Warn if household-related record types are present without a Person Account sentinel.

    This check cannot verify Person Account enablement (requires org access),
    but it can flag that household record types are present and remind the deployer
    to verify Person Account status before deploying.
    """
    issues: list[str] = []

    # Look for record type metadata files with Household in the name
    household_rt_files = (
        list(manifest_dir.rglob("Account.Household-meta.xml"))
        + list(manifest_dir.rglob("Account.Household.*-meta.xml"))
        + list(manifest_dir.rglob("*Household*.recordType-meta.xml"))
    )

    if household_rt_files:
        issues.append(
            f"Household Account record type metadata detected "
            f"({len(household_rt_files)} file(s)). "
            f"Person Accounts must be enabled in the target org before this metadata "
            f"can be deployed. Verify with: "
            f"`sf data query --query \"SELECT Id FROM RecordType WHERE "
            f"SObjectType='Account' AND DeveloperName='PersonAccount'\" "
            f"--target-org <alias>`. "
            f"If the query returns 0 rows, enable Person Accounts in Setup first."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC metadata artifacts for deployment anti-patterns. "
            "Detects namespace contamination, single-wave ordering risks, "
            "Participant Role reference issues, and household metadata without "
            "a Person Account pre-flight reminder."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--package-xml",
        default=None,
        help="Path to package.xml manifest file to check for ordering risks.",
    )
    return parser.parse_args()


def check_fsc_deployment_patterns(
    manifest_dir: Path,
    package_xml_path: Path | None = None,
) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Run all checks
    issues.extend(check_namespace_contamination(manifest_dir))
    issues.extend(check_participant_role_metadata(manifest_dir))
    issues.extend(check_person_account_sentinel(manifest_dir))

    if package_xml_path is not None:
        issues.extend(check_package_xml_ordering(package_xml_path))
    else:
        # Auto-detect package.xml in the manifest dir
        default_package_xml = manifest_dir / "package.xml"
        if default_package_xml.exists():
            issues.extend(check_package_xml_ordering(default_package_xml))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    package_xml_path = Path(args.package_xml) if args.package_xml else None

    issues = check_fsc_deployment_patterns(manifest_dir, package_xml_path)

    if not issues:
        print("No FSC deployment issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
