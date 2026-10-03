#!/usr/bin/env python3
"""Checker script for Change Set Deployment skill.

Validates a local Salesforce metadata directory for common change set
deployment mistakes:

  1. Profile metadata detected: flags the always-deployed sections (user
     permissions, login IP ranges, login hours) for review.
  2. Custom fields referenced in layouts but missing from the metadata tree.
  3. Flows present without a companion post-deploy note about activation.
  4. Apex classes present with no corresponding *Test* class.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_change_set_deployment.py [--manifest-dir path/to/metadata]

The manifest-dir can be the root of a retrieved Salesforce metadata or
source tree. The checker finds `classes/`, `flows/`, `objects/`,
`profiles/`, and `layouts/` directories anywhere below it.
"""

from __future__ import annotations

import argparse
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata directory for common change set "
            "deployment mistakes."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()




def _find_dirs(root: Path, name: str) -> list[Path]:
    """Return every directory called `name` at or below root (root itself included)."""
    found = [d for d in root.rglob(name) if d.is_dir()]
    if (root / name).is_dir() and (root / name) not in found:
        found.append(root / name)
    return sorted(set(found))


def _files(root: Path, dirname: str, pattern: str) -> list[Path]:
    out: list[Path] = []
    for d in _find_dirs(root, dirname):
        out.extend(d.glob(pattern))
    return sorted(set(out))

# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_profiles_present(manifest_dir: Path) -> list[str]:
    """Flag Profile metadata and the sections that always deploy with it.

    The Metadata API scopes profile settings to the other components in the
    same deployment, except user permissions, login IP ranges, and login hours,
    which are always included (Metadata API Developer Guide, Profile > Usage).
    Those three sections are where production-only values get replaced.
    """
    issues: list[str] = []
    profile_files = _files(manifest_dir, "profiles", "*.profile-meta.xml") + \
        _files(manifest_dir, "profiles", "*.profile")
    if not profile_files:
        return issues
    for pf in profile_files:
        name = pf.name.replace(".profile-meta.xml", "").replace(".profile", "")
        try:
            text = pf.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        always = [tag for tag in ("userPermissions", "loginIpRanges", "loginHours") if f"<{tag}>" in text]
        detail = (f" It carries {', '.join(always)}, which deploy regardless of the other components."
                  if always else "")
        issues.append(
            f"PROFILE REVIEW: profile '{name}' is in the deployment.{detail} "
            "Settings for components in the same deployment also change. Compare these "
            "sections with the target org before upload, and prefer permission sets for new access."
        )
    return issues


def check_layouts_missing_fields(manifest_dir: Path) -> list[str]:
    """Detect page layouts that reference custom fields not present in the manifest.

    Parses layout XML for <field> elements ending in __c and cross-checks
    against the object folder in the manifest.
    """
    issues: list[str] = []
    layout_files = _files(manifest_dir, "layouts", "*.layout-meta.xml")
    if not layout_files:
        return issues

    # Build a set of known custom fields from objects/ directory
    # Supports both metadata-api format (objects/<ObjectName>/<fields>/<FieldName>.field-meta.xml)
    # and the flat sfdx format.
    known_fields: set[str] = set()  # "ObjectName.FieldAPIName"
    for objects_dir in _find_dirs(manifest_dir, "objects"):
        # Source format: objects/<ObjName>/fields/<FieldName>.field-meta.xml
        for field_file in objects_dir.rglob("*.field-meta.xml"):
            parts = field_file.parts
            # Find the object name (parent of "fields" dir)
            try:
                fields_idx = list(parts).index("fields")
                obj_name = parts[fields_idx - 1]
                field_name = field_file.stem.replace(".field-meta", "")
                known_fields.add(f"{obj_name}.{field_name}")
            except (ValueError, IndexError):
                pass

    for layout_file in layout_files:
        try:
            tree = ET.parse(layout_file)
        except ET.ParseError:
            issues.append(
                f"PARSE ERROR: Could not parse layout file: {layout_file.name}"
            )
            continue

        ns = {"sf": "http://soap.sforce.com/2006/04/metadata"}
        root = tree.getroot()

        # Layout file name format: ObjectName-LayoutName.layout-meta.xml
        layout_stem = layout_file.stem.replace(".layout-meta", "")
        obj_name = layout_stem.split("-")[0] if "-" in layout_stem else None

        # Collect all <field> elements from layoutItems and quickActionListItems
        missing: list[str] = []
        for item in root.iter():
            tag = item.tag.split("}")[-1]  # strip namespace
            if tag == "field":
                field_val = (item.text or "").strip()
                if field_val.endswith("__c") and obj_name:
                    qualified = f"{obj_name}.{field_val}"
                    if qualified not in known_fields:
                        missing.append(field_val)

        if missing:
            issues.append(
                f"MISSING FIELD DEPENDENCY in layout '{layout_file.name}': "
                f"referenced custom field(s) not found in manifest objects/ directory: "
                f"{', '.join(sorted(set(missing)))}. "
                "Add these fields to the outbound change set before uploading."
            )

    return issues


def check_flows_without_activation_note(manifest_dir: Path) -> list[str]:
    """Flag Flow metadata to remind the practitioner that deployment != activation."""
    issues: list[str] = []
    flow_files = _files(manifest_dir, "flows", "*.flow-meta.xml")
    if not flow_files:
        return issues

    active_flows: list[str] = []
    inactive_flows: list[str] = []

    for flow_file in flow_files:
        try:
            tree = ET.parse(flow_file)
        except ET.ParseError:
            continue

        root = tree.getroot()
        status_el = None
        for el in root.iter():
            if el.tag.split("}")[-1] == "status":
                status_el = el
                break

        name = flow_file.stem.replace(".flow-meta", "")
        status = (status_el.text or "").strip() if status_el is not None else "Unknown"
        if status == "Active":
            active_flows.append(name)
        else:
            inactive_flows.append(name)

    if active_flows:
        issues.append(
            f"FLOW ACTIVATION REMINDER: {len(active_flows)} flow(s) are marked Active "
            f"in the source metadata: {', '.join(sorted(active_flows))}. "
            "In production they deploy INACTIVE unless 'Deploy processes and flows as "
            "active' (FlowSettings enableFlowDeployAsActiveEnabled) is on. When it is on, "
            "deploying an active flow runs Apex tests and checks flow test coverage. "
            "Decide which path this release takes."
        )
    if inactive_flows:
        issues.append(
            f"FLOW POST-DEPLOY ACTION NEEDED: {len(inactive_flows)} flow(s) are "
            f"Inactive in the source metadata: {', '.join(sorted(inactive_flows))}. "
            "If these flows should be active after deployment, add a manual activation "
            "step to the release plan. Change set deployment does not auto-activate flows."
        )

    return issues


def check_apex_classes_missing_tests(manifest_dir: Path) -> list[str]:
    """Detect Apex classes that have no corresponding test class in the manifest."""
    issues: list[str] = []
    all_cls_files = _files(manifest_dir, "classes", "*.cls")
    if not all_cls_files:
        return issues

    # Identify test classes by @isTest annotation in the file body
    test_class_names: set[str] = set()
    non_test_class_names: list[str] = []

    for cls_file in all_cls_files:
        name = cls_file.stem
        try:
            content = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if "@isTest" in content or "@IsTest" in content:
            test_class_names.add(name.lower())
        else:
            non_test_class_names.append(name)

    untested: list[str] = []
    for cls_name in non_test_class_names:
        # Convention: test class is named <ClassName>Test or Test<ClassName>
        base_lower = cls_name.lower()
        has_test = (
            f"{base_lower}test" in test_class_names
            or f"test{base_lower}" in test_class_names
            or base_lower in test_class_names  # exact match edge case
        )
        if not has_test:
            untested.append(cls_name)

    if untested:
        issues.append(
            f"MISSING TEST CLASSES: {len(untested)} Apex class(es) in the manifest "
            f"have no corresponding test class: {', '.join(sorted(untested))}. "
            "Default and Run local tests need 75% overall coverage; Run specified tests "
            "needs 75% on each deployed class and trigger. Include test classes that cover "
            "these classes, or confirm they exist in the target org."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_change_set_deployment(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_profiles_present(manifest_dir))
    issues.extend(check_layouts_missing_fields(manifest_dir))
    issues.extend(check_flows_without_activation_note(manifest_dir))
    issues.extend(check_apex_classes_missing_tests(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_change_set_deployment(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"\nISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found. Review before uploading the change set.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
