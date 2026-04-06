#!/usr/bin/env python3
"""Checker script for the destructive-changes-deployment skill.

Scans a Salesforce metadata project directory for common destructive-manifest
authoring mistakes. Stdlib only — no pip dependencies required.

Checks performed:
  1. Destructive manifest contains <version> element (invalid — version belongs only in package.xml)
  2. Destructive manifest uses wildcard members (<members>*</members>)
  3. Destructive manifest lists undeletable metadata types (RecordType, active Flows implied)
  4. Companion package.xml is missing when a destructive manifest is present
  5. Deployment command in shell scripts uses destructive flag without --manifest

Usage:
    python3 check_destructive.py --manifest-dir path/to/metadata
    python3 check_destructive.py --manifest-dir .  # current directory
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DESTRUCTIVE_FILENAMES = {
    "destructiveChanges.xml",
    "destructiveChangesPre.xml",
    "destructiveChangesPost.xml",
}

# Types that cannot be deleted via the Metadata API.
# Source: Salesforce Metadata API Developer Guide — Deleting Components
UNDELETABLE_TYPES = {
    "RecordType",
    "PicklistValue",
    "GlobalValueSet",  # individual values cannot be removed via deployment
}

NAMESPACE = "http://soap.sforce.com/2006/04/metadata"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce destructive-changes manifests for common authoring mistakes.\n"
            "Scans the given directory recursively for destructiveChanges*.xml files."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_destructive_manifests(root: Path) -> list[Path]:
    """Return all destructive manifest files under root."""
    found = []
    for name in DESTRUCTIVE_FILENAMES:
        found.extend(root.rglob(name))
    return sorted(found)


def find_package_xml(root: Path) -> list[Path]:
    """Return all package.xml files under root."""
    return sorted(root.rglob("package.xml"))


def check_manifest(manifest_path: Path) -> list[str]:
    """Run per-manifest checks. Return list of issue strings."""
    issues: list[str] = []
    rel = manifest_path

    # Parse XML safely
    try:
        tree = ET.parse(manifest_path)
    except ET.ParseError as exc:
        issues.append(f"[{rel}] XML parse error: {exc}")
        return issues

    root_el = tree.getroot()

    # Strip namespace for element matching
    def tag(local: str) -> str:
        return f"{{{NAMESPACE}}}{local}"

    # Check 1: <version> element present in destructive manifest (invalid)
    version_els = root_el.findall(tag("version"))
    if version_els:
        issues.append(
            f"[{rel}] INVALID: <version> element found. "
            "Destructive manifests must NOT include <version>; "
            "version belongs only in the companion package.xml."
        )

    # Check 2: Wildcard member (<members>*</members>)
    for types_el in root_el.findall(tag("types")):
        for members_el in types_el.findall(tag("members")):
            if members_el.text and members_el.text.strip() == "*":
                type_name_el = types_el.find(tag("name"))
                type_name = type_name_el.text.strip() if type_name_el is not None and type_name_el.text else "unknown"
                issues.append(
                    f"[{rel}] INVALID: Wildcard member (*) found for type '{type_name}'. "
                    "Wildcards are not supported in destructive manifests — "
                    "list every member explicitly."
                )

    # Check 3: Undeletable metadata types
    for types_el in root_el.findall(tag("types")):
        type_name_el = types_el.find(tag("name"))
        if type_name_el is None or not type_name_el.text:
            continue
        type_name = type_name_el.text.strip()
        if type_name in UNDELETABLE_TYPES:
            issues.append(
                f"[{rel}] WARNING: Metadata type '{type_name}' cannot be deleted via the "
                "Metadata API. Record Types and Picklist values must be removed manually "
                "through Setup. This deployment will fail."
            )

    return issues


def check_companion_package(destructive_files: list[Path], package_files: list[Path]) -> list[str]:
    """Warn if a destructive manifest has no companion package.xml in the same directory."""
    issues: list[str] = []
    package_dirs = {p.parent for p in package_files}
    for destructive in destructive_files:
        if destructive.parent not in package_dirs:
            issues.append(
                f"[{destructive}] WARNING: No companion package.xml found in the same directory. "
                "The Metadata API requires a package.xml in the deployment container even when "
                "no components are being added. Create an API-version-only package.xml."
            )
    return issues


def check_shell_scripts(root: Path) -> list[str]:
    """Scan shell scripts for sf deploy commands using destructive flags without --manifest."""
    issues: list[str] = []
    shell_files = list(root.rglob("*.sh")) + list(root.rglob("*.bash"))
    destructive_flag_pattern = re.compile(
        r"(--pre-destructive-changes|--post-destructive-changes)"
    )
    manifest_flag_pattern = re.compile(r"(--manifest|--source-dir)")

    for sh_file in shell_files:
        try:
            content = sh_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            if "sf project deploy start" in line or "sfdx force:source:deploy" in line:
                # Collect the full command (may span multiple lines with backslash continuation)
                command_block = line
                j = i
                while command_block.rstrip().endswith("\\") and j < len(lines):
                    command_block += "\n" + lines[j]
                    j += 1
                has_destructive = bool(destructive_flag_pattern.search(command_block))
                has_manifest = bool(manifest_flag_pattern.search(command_block))
                if has_destructive and not has_manifest:
                    issues.append(
                        f"[{sh_file}:{i}] WARNING: Deploy command uses a destructive flag but "
                        "has no --manifest or --source-dir argument. A companion package.xml "
                        "is required even when deploying only deletions."
                    )
    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()

    if not manifest_dir.exists():
        print(f"ERROR: Directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    destructive_files = find_destructive_manifests(manifest_dir)
    package_files = find_package_xml(manifest_dir)

    if not destructive_files:
        print(f"No destructive manifests found under: {manifest_dir}")
        print("Nothing to check.")
        return 0

    print(f"Found {len(destructive_files)} destructive manifest(s) under: {manifest_dir}\n")

    all_issues: list[str] = []

    for manifest_path in destructive_files:
        all_issues.extend(check_manifest(manifest_path))

    all_issues.extend(check_companion_package(destructive_files, package_files))
    all_issues.extend(check_shell_scripts(manifest_dir))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(all_issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
