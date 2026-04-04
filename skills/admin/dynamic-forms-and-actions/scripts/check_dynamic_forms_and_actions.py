#!/usr/bin/env python3
"""Checker script for Dynamic Forms and Dynamic Actions skill.

Inspects Salesforce metadata in a local source-format project to detect common
Dynamic Forms and Dynamic Actions configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_dynamic_forms_and_actions.py [--help]
    python3 check_dynamic_forms_and_actions.py --manifest-dir path/to/metadata
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
            "Check Salesforce metadata for common Dynamic Forms and Dynamic Actions "
            "configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_flexipages(manifest_dir: Path) -> list[Path]:
    """Return all .flexipage-meta.xml files under manifest_dir."""
    return list(manifest_dir.rglob("*.flexipage-meta.xml"))


def _namespace(tag: str) -> str:
    """Extract namespace from an ElementTree tag like {ns}LocalName."""
    if tag.startswith("{"):
        return tag[1 : tag.index("}")]
    return ""


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse XML and return the root element, or None on parse failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError:
        return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_flexipage_files(manifest_dir: Path) -> list[str]:
    """Run all checks across .flexipage-meta.xml files found under manifest_dir."""
    issues: list[str] = []
    flexipages = _find_flexipages(manifest_dir)

    if not flexipages:
        # Not necessarily an error — the project may not have record pages.
        return issues

    for fp_path in flexipages:
        root = _parse_xml_safe(fp_path)
        if root is None:
            issues.append(f"[{fp_path.name}] Could not parse XML — file may be malformed.")
            continue

        ns = _namespace(root.tag)
        prefix = f"{{{ns}}}" if ns else ""

        page_name = fp_path.stem.replace(".flexipage-meta", "")
        issues.extend(_check_dynamic_forms_migration(root, prefix, page_name, fp_path))
        issues.extend(_check_dynamic_actions_conflicts(root, prefix, page_name, fp_path))
        issues.extend(_check_visibility_filter_completeness(root, prefix, page_name, fp_path))

    return issues


def _check_dynamic_forms_migration(
    root: ET.Element, prefix: str, page_name: str, fp_path: Path
) -> list[str]:
    """
    Warn if a flexipage appears to have Dynamic Forms enabled (individual field
    components present) but also retains a legacy 'fields' region or component
    that suggests the upgrade wizard was not run.

    This is a heuristic check: it looks for both a fieldComponent-type region and
    a legacy 'forceApps:recordLayout' or equivalent component in the same page.
    """
    issues: list[str] = []

    components = root.findall(f".//{prefix}componentInstance")
    component_names = [
        c.findtext(f"{prefix}componentName") or "" for c in components
    ]

    has_field_component = any("fieldInstance" in n or "Field" in n for n in component_names)
    has_legacy_layout = any(
        "recordLayout" in n.lower() or "pagelayout" in n.lower() for n in component_names
    )

    if has_field_component and has_legacy_layout:
        issues.append(
            f"[{page_name}] Page appears to have both Dynamic Forms field components and a "
            f"legacy page layout component. Verify the 'Upgrade Now' migration was completed "
            f"and the old layout component was removed. File: {fp_path}"
        )

    return issues


def _check_dynamic_actions_conflicts(
    root: ET.Element, prefix: str, page_name: str, fp_path: Path
) -> list[str]:
    """
    Warn if Dynamic Actions appears to be enabled (action components with
    visibility filters are present) but standard action components without filters
    also exist, suggesting a partial migration from page layout actions.
    """
    issues: list[str] = []

    components = root.findall(f".//{prefix}componentInstance")

    action_components = [
        c for c in components
        if "action" in (c.findtext(f"{prefix}componentName") or "").lower()
    ]

    if not action_components:
        return issues

    actions_with_filters = sum(
        1 for c in action_components
        if c.find(f".//{prefix}visibilityRule") is not None
    )
    actions_without_filters = len(action_components) - actions_with_filters

    if actions_with_filters > 0 and actions_without_filters > 0:
        issues.append(
            f"[{page_name}] Mixing Dynamic Actions components with visibility rules and action "
            f"components without visibility rules on the same page. This can cause duplicate "
            f"action entries or unpredictable visibility. Ensure all actions are managed "
            f"exclusively via Dynamic Actions or exclusively via page layout. File: {fp_path}"
        )

    return issues


def _check_visibility_filter_completeness(
    root: ET.Element, prefix: str, page_name: str, fp_path: Path
) -> list[str]:
    """
    Warn if any visibility rule's filter criteria reference fields but have no
    value specified — an empty filter value causes the condition to never match.
    """
    issues: list[str] = []

    criteria = root.findall(f".//{prefix}criteria")
    for criterion in criteria:
        field = criterion.findtext(f"{prefix}leftValue") or ""
        value = criterion.findtext(f"{prefix}rightValue") or ""
        operator = criterion.findtext(f"{prefix}operator") or ""

        # Operators like 'isNull' / 'isNotNull' legitimately have no right value.
        value_required_operators = {
            "equals", "notEqual", "greaterThan", "lessThan",
            "greaterOrEqual", "lessOrEqual", "contains", "startsWith",
        }

        if operator.lower() in value_required_operators and not value.strip() and field.strip():
            issues.append(
                f"[{page_name}] Visibility filter criterion on field '{field}' uses operator "
                f"'{operator}' but has no right-hand value. The condition will never match. "
                f"File: {fp_path}"
            )

    return issues


# ---------------------------------------------------------------------------
# Object support check (heuristic from package manifest)
# ---------------------------------------------------------------------------

def check_package_manifest(manifest_dir: Path) -> list[str]:
    """
    Check package.xml for Dynamic Forms usage on objects that historically have
    had limited support. This is informational — the supported list changes each
    release, so only flag objects known to be restricted.
    """
    issues: list[str] = []

    # Objects that, as of Spring '25, do not support Dynamic Forms.
    # This list is not exhaustive; practitioners should always verify current docs.
    known_unsupported = {
        "Task", "Event", "User", "Contract", "Product2",
        "Pricebook2", "PricebookEntry",
    }

    package_xml = manifest_dir / "package.xml"
    if not package_xml.exists():
        # Try common alternative locations.
        for candidate in manifest_dir.rglob("package.xml"):
            package_xml = candidate
            break

    if not package_xml.exists():
        return issues

    root = _parse_xml_safe(package_xml)
    if root is None:
        return issues

    ns = _namespace(root.tag)
    prefix = f"{{{ns}}}" if ns else ""

    for type_elem in root.findall(f".//{prefix}types"):
        type_name = type_elem.findtext(f"{prefix}name") or ""
        if type_name == "FlexiPage":
            for member in type_elem.findall(f"{prefix}members"):
                page_api_name = member.text or ""
                # FlexiPage names often start with the object name.
                for obj in known_unsupported:
                    if page_api_name.lower().startswith(obj.lower()):
                        issues.append(
                            f"FlexiPage '{page_api_name}' appears to be for '{obj}', "
                            f"which has historically had limited or no Dynamic Forms support. "
                            f"Verify this object is supported in your current Salesforce release."
                        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_dynamic_forms_and_actions(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_flexipage_files(manifest_dir))
    issues.extend(check_package_manifest(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_dynamic_forms_and_actions(manifest_dir)

    if not issues:
        print("No Dynamic Forms / Dynamic Actions issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
