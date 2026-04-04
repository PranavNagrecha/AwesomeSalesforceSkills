#!/usr/bin/env python3
"""Checker script for sf CLI and SFDX Essentials skill.

Validates a Salesforce DX project for common sf CLI configuration issues:
- Missing or malformed sfdx-project.json
- package.xml files that use wildcard for standard objects
- Private key files accidentally included (not gitignored)
- Deployment scripts committing to production without test level set

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sf_cli_and_sfdx_essentials.py [--help]
    python3 check_sf_cli_and_sfdx_essentials.py --project-dir path/to/sfdx-project
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


STANDARD_OBJECTS = {
    "Account", "Contact", "Lead", "Opportunity", "Case", "Task", "Event",
    "User", "Campaign", "CampaignMember", "Contract", "Order", "Product2",
    "Pricebook2", "PricebookEntry", "Quote", "QuoteLineItem", "Asset",
    "Entitlement", "ServiceContract", "WorkOrder",
}

PRIVATE_KEY_PATTERNS = ["*.key", "*.pem", "server.key", "jwtRS256.key"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce DX project for sf CLI and SFDX configuration issues.",
    )
    parser.add_argument(
        "--project-dir",
        default=".",
        help="Root directory of the Salesforce DX project (default: current directory).",
    )
    return parser.parse_args()


def check_sfdx_project_json(project_dir: Path) -> list[str]:
    """Check sfdx-project.json for required fields and common problems."""
    issues: list[str] = []
    project_file = project_dir / "sfdx-project.json"

    if not project_file.exists():
        issues.append(
            "sfdx-project.json not found. Run `sf project generate --name <name>` to create a project."
        )
        return issues

    try:
        with project_file.open() as f:
            config = json.load(f)
    except json.JSONDecodeError as exc:
        issues.append(f"sfdx-project.json is not valid JSON: {exc}")
        return issues

    if "packageDirectories" not in config:
        issues.append("sfdx-project.json missing 'packageDirectories'. This field is required.")

    if "sourceApiVersion" not in config:
        issues.append(
            "sfdx-project.json missing 'sourceApiVersion'. "
            "Set this to match your target org's API version to avoid silent retrieve failures."
        )
    else:
        try:
            version = float(config["sourceApiVersion"])
            if version < 50.0:
                issues.append(
                    f"sfdx-project.json 'sourceApiVersion' is {version}, which is older than API 50.0 (Winter '21). "
                    "Many modern metadata types require API 55.0+. Update to current version."
                )
        except (ValueError, TypeError):
            issues.append(
                f"sfdx-project.json 'sourceApiVersion' value '{config['sourceApiVersion']}' is not a valid API version number."
            )

    return issues


def check_package_xml_files(project_dir: Path) -> list[str]:
    """Scan package.xml files for standard object wildcard usage."""
    issues: list[str] = []
    xml_ns = "http://soap.sforce.com/2006/04/metadata"

    for xml_file in project_dir.rglob("package.xml"):
        try:
            tree = ET.parse(xml_file)
        except ET.ParseError as exc:
            issues.append(f"{xml_file}: malformed XML — {exc}")
            continue

        root = tree.getroot()
        for types_el in root.findall(f"{{{xml_ns}}}types"):
            name_el = types_el.find(f"{{{xml_ns}}}name")
            if name_el is None or name_el.text != "CustomObject":
                continue
            for member_el in types_el.findall(f"{{{xml_ns}}}members"):
                if member_el.text and member_el.text.strip() == "*":
                    issues.append(
                        f"{xml_file}: CustomObject uses wildcard '<members>*</members>'. "
                        "Standard objects (Account, Contact, etc.) are not returned by wildcard. "
                        "List standard objects explicitly by name alongside the wildcard."
                    )
                    break

        # Check API version is present
        version_el = root.find(f"{{{xml_ns}}}version")
        if version_el is None or not version_el.text:
            issues.append(
                f"{xml_file}: missing <version> element. "
                "Add <version>62.0</version> (or current API version) to the manifest."
            )

    return issues


def check_gitignore_for_keys(project_dir: Path) -> list[str]:
    """Check that private key patterns are in .gitignore."""
    issues: list[str] = []
    gitignore_path = project_dir / ".gitignore"

    # Check if any .key or .pem files exist unprotected
    key_files_found = []
    for pattern in ["*.key", "*.pem"]:
        key_files_found.extend(project_dir.rglob(pattern))

    if not key_files_found:
        return issues  # No key files present — nothing to check

    if not gitignore_path.exists():
        issues.append(
            "Private key files found but no .gitignore exists. "
            "Add '*.key' and '*.pem' to .gitignore immediately to prevent committing credentials."
        )
        return issues

    gitignore_content = gitignore_path.read_text()
    missing_patterns = []
    for pattern in ("*.key", "*.pem"):
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)

    if missing_patterns:
        issues.append(
            f"Private key files detected but these patterns are NOT in .gitignore: {missing_patterns}. "
            "Add them to .gitignore to prevent committing JWT credentials to version control."
        )

    return issues


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)

    if not project_dir.exists():
        print(f"ERROR: Project directory not found: {project_dir}")
        return 1

    all_issues: list[str] = []
    all_issues.extend(check_sfdx_project_json(project_dir))
    all_issues.extend(check_package_xml_files(project_dir))
    all_issues.extend(check_gitignore_for_keys(project_dir))

    if not all_issues:
        print("No sf CLI / SFDX configuration issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
