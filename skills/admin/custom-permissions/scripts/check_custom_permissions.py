#!/usr/bin/env python3
"""Checker script for Custom Permissions skill.

Scans Salesforce metadata XML files to report:
  1. Which custom permissions are defined in the org metadata.
  2. Which permission sets grant each custom permission.
  3. Custom permissions that are defined but granted by no permission set (orphans).
  4. Permission sets that reference a custom permission name not found in the
     customPermissions metadata directory (dangling references).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_custom_permissions.py [--manifest-dir path/to/metadata]

The script walks the manifest directory looking for:
  - *.customPermission-meta.xml  (custom permission definitions)
  - *.permissionset-meta.xml     (permission set definitions)

Exit codes:
  0 — no issues found
  1 — one or more issues found (orphaned permissions or dangling references)
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Namespace helpers
# ---------------------------------------------------------------------------

# Salesforce metadata XML uses a default namespace. ElementTree requires
# explicit namespace handling.
_SF_NS = "http://soap.sforce.com/2006/04/metadata"
_NS = {"sf": _SF_NS}


def _tag(local: str) -> str:
    """Return a Clark-notation tag for the Salesforce metadata namespace."""
    return f"{{{_SF_NS}}}{local}"


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def parse_custom_permission_names(manifest_dir: Path) -> set[str]:
    """Return the API names of all custom permissions found in the metadata tree.

    Looks for files matching ``*.customPermission-meta.xml`` anywhere under
    *manifest_dir*.  The API name is derived from the filename stem (the part
    before ``.customPermission-meta.xml``).
    """
    names: set[str] = set()
    for cp_file in manifest_dir.rglob("*.customPermission-meta.xml"):
        # filename: MyPermission.customPermission-meta.xml  -> api name: MyPermission
        stem = cp_file.name.replace(".customPermission-meta.xml", "")
        names.add(stem)
    return names


def parse_permission_set_grants(
    manifest_dir: Path,
) -> dict[str, list[str]]:
    """Return a mapping of permission-set-name -> [custom permission API names granted].

    Looks for files matching ``*.permissionset-meta.xml`` anywhere under
    *manifest_dir* and parses the ``<customPermissions>`` nodes.
    """
    grants: dict[str, list[str]] = {}
    for ps_file in manifest_dir.rglob("*.permissionset-meta.xml"):
        ps_name = ps_file.name.replace(".permissionset-meta.xml", "")
        try:
            tree = ET.parse(ps_file)
        except ET.ParseError as exc:
            # Malformed XML — report but continue
            grants.setdefault(ps_name, [])
            grants[ps_name].append(f"[PARSE ERROR: {exc}]")
            continue

        root = tree.getroot()
        perm_names: list[str] = []
        for cp_node in root.findall(_tag("customPermissions")):
            enabled_node = cp_node.find(_tag("enabled"))
            name_node = cp_node.find(_tag("name"))
            if (
                name_node is not None
                and name_node.text
                and enabled_node is not None
                and enabled_node.text == "true"
            ):
                perm_names.append(name_node.text.strip())

        grants[ps_name] = perm_names

    return grants


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def analyse(
    defined_permissions: set[str],
    grants: dict[str, list[str]],
) -> tuple[list[str], list[str], dict[str, list[str]]]:
    """Analyse coverage and return (orphans, dangling_refs, coverage_map).

    orphans:        custom permissions defined but granted by no permission set.
    dangling_refs:  custom permission names referenced in permission sets but
                    not found in customPermission metadata.
    coverage_map:   {custom-permission-api-name: [permission-set-name, ...]}
    """
    coverage_map: dict[str, list[str]] = {p: [] for p in defined_permissions}

    dangling_refs: list[str] = []

    for ps_name, perm_names in grants.items():
        for perm_name in perm_names:
            if perm_name.startswith("[PARSE ERROR"):
                continue
            if perm_name in coverage_map:
                coverage_map[perm_name].append(ps_name)
            else:
                dangling_refs.append(
                    f"Permission set '{ps_name}' references '{perm_name}' "
                    f"which is not defined in the customPermissions metadata directory."
                )

    orphans: list[str] = [
        p for p, ps_list in coverage_map.items() if not ps_list
    ]

    return orphans, dangling_refs, coverage_map


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_coverage_report(coverage_map: dict[str, list[str]]) -> None:
    """Print a human-readable coverage table."""
    if not coverage_map:
        print("  (no custom permissions found)")
        return

    max_perm_len = max(len(p) for p in coverage_map)
    header = f"  {'Custom Permission':<{max_perm_len}}  Permission Sets"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for perm_name in sorted(coverage_map):
        ps_list = coverage_map[perm_name]
        ps_display = ", ".join(sorted(ps_list)) if ps_list else "(none)"
        print(f"  {perm_name:<{max_perm_len}}  {ps_display}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata to report which permission sets grant "
            "which custom permissions, and flag orphaned or dangling references."
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

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}")
        return 1

    print(f"Scanning: {manifest_dir.resolve()}")
    print()

    # 1. Discover defined custom permissions
    defined_permissions = parse_custom_permission_names(manifest_dir)
    print(f"Custom permissions defined in metadata: {len(defined_permissions)}")
    if not defined_permissions:
        print("  (no *.customPermission-meta.xml files found)")

    # 2. Discover permission set grants
    grants = parse_permission_set_grants(manifest_dir)
    print(f"Permission sets scanned:                {len(grants)}")
    print()

    # 3. Analyse
    orphans, dangling_refs, coverage_map = analyse(defined_permissions, grants)

    # 4. Print coverage table
    print("Coverage (custom permission -> granting permission sets):")
    print_coverage_report(coverage_map)
    print()

    # 5. Print issues
    issues: list[str] = []

    if orphans:
        print("ORPHANED PERMISSIONS (defined but granted by no permission set):")
        for perm in sorted(orphans):
            msg = f"  '{perm}' is defined but not included in any permission set."
            print(msg)
            issues.append(msg)
        print()

    if dangling_refs:
        print("DANGLING REFERENCES (permission sets reference undefined custom permissions):")
        for ref in sorted(dangling_refs):
            print(f"  {ref}")
            issues.append(ref)
        print()

    if not issues:
        print("No issues found.")
        return 0

    print(f"{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
