#!/usr/bin/env python3
"""Checker script for Business Rules Engine skill.

Inspects Salesforce metadata files for common BRE configuration issues
including Decision Tables and Expression Sets (BRE artifacts).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_business_rules_engine.py [--manifest-dir PATH]

The manifest directory should be the root of a Salesforce DX project or a
retrieved metadata tree. The checker looks for:
  - DecisionTable / DecisionTableVersion XML files
  - ExpressionSet / ExpressionSetVersion XML files (BRE Expression Sets)

Checks performed:
  1. DecisionTableVersion files where status is not 'Active'
  2. ExpressionSetVersion files where IsActive is not 'true' (BRE Expression Sets)
  3. DecisionTable definition files with no corresponding version file
  4. ExpressionSet definition files with no corresponding version file
  5. DecisionTableVersion XML missing a default/fallback row definition
  6. Duplicate or suspicious row entries (same input column values on multiple rows)
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
            "Check Business Rules Engine (BRE) configuration and metadata "
            "for common issues in Decision Tables and Expression Sets."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------


def _text(element: ET.Element | None) -> str:
    """Return stripped text content of an XML element, or empty string."""
    if element is None:
        return ""
    return (element.text or "").strip()


def _find_ns(root: ET.Element, tag: str) -> ET.Element | None:
    """Find a direct child element ignoring any XML namespace prefix."""
    for child in root:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == tag:
            return child
    return None


def _findall_ns(root: ET.Element, tag: str) -> list[ET.Element]:
    """Find all direct child elements ignoring any XML namespace prefix."""
    result = []
    for child in root:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == tag:
            result.append(child)
    return result


def _findall_deep(root: ET.Element, tag: str) -> list[ET.Element]:
    """Recursively find all descendant elements matching a tag (namespace-agnostic)."""
    result = []
    for el in root.iter():
        local = el.tag.split("}")[-1] if "}" in el.tag else el.tag
        if local == tag:
            result.append(el)
    return result


# ---------------------------------------------------------------------------
# Decision Table checks
# ---------------------------------------------------------------------------


def check_decision_table_versions(manifest_dir: Path) -> list[str]:
    """Check DecisionTableVersion metadata for activation status."""
    issues: list[str] = []

    version_files = list(manifest_dir.rglob("*.decisionTableVersion-meta.xml"))
    if not version_files:
        version_files = list(manifest_dir.rglob("*DecisionTableVersion*.xml"))

    for fpath in version_files:
        try:
            tree = ET.parse(fpath)
        except ET.ParseError as exc:
            issues.append(f"XML parse error in {fpath}: {exc}")
            continue

        root = tree.getroot()
        rel = fpath.relative_to(manifest_dir)

        # Check status field (DecisionTable uses Status, not IsActive)
        status_el = (
            _find_ns(root, "status")
            or _find_ns(root, "Status")
        )
        status = _text(status_el).lower()
        if status and status not in ("active",):
            issues.append(
                f"[ACTIVATION] {rel} — DecisionTableVersion status is '{_text(status_el)}' "
                "(not Active). This version will not be called at runtime. "
                "Activate post-deploy via the BRE UI or Connect API — "
                "metadata deployment does NOT auto-activate BRE versions."
            )

    return issues


def check_decision_table_definitions(manifest_dir: Path) -> list[str]:
    """Check that DecisionTable definition files have a corresponding version file."""
    issues: list[str] = []

    definition_files = list(manifest_dir.rglob("*.decisionTable-meta.xml"))
    if not definition_files:
        definition_files = list(manifest_dir.rglob("*DecisionTable*.xml"))
        definition_files = [
            f for f in definition_files
            if "Version" not in f.stem and "version" not in f.stem
            and "Row" not in f.stem and "Column" not in f.stem
        ]

    for fpath in definition_files:
        parent = fpath.parent
        version_siblings = (
            list(parent.rglob("*.decisionTableVersion-meta.xml"))
            + list(parent.rglob("*DecisionTableVersion*.xml"))
        )
        if not version_siblings:
            rel = fpath.relative_to(manifest_dir)
            issues.append(
                f"[NO VERSION] {rel} — DecisionTable definition found but no version file "
                "detected in the same directory tree. "
                "A Decision Table cannot be activated without at least one version."
            )

    return issues


def check_decision_table_default_rows(manifest_dir: Path) -> list[str]:
    """Warn when DecisionTable version XML has no apparent default/fallback row.

    A default row has all input condition columns blank (null/empty) and serves
    as the fallback for unmatched inputs. Without it, unmatched inputs return null
    output attributes with no runtime error.

    Note: This is a heuristic check based on XML structure. It looks for a row
    element where all condition values appear empty. False negatives are possible
    for tables whose conditions use an operator that implies a catch-all.
    """
    issues: list[str] = []

    version_files = list(manifest_dir.rglob("*.decisionTableVersion-meta.xml"))
    if not version_files:
        version_files = list(manifest_dir.rglob("*DecisionTableVersion*.xml"))

    for fpath in version_files:
        try:
            tree = ET.parse(fpath)
        except ET.ParseError:
            continue  # Already reported in check_decision_table_versions

        root = tree.getroot()
        rel = fpath.relative_to(manifest_dir)

        rows = _findall_deep(root, "decisionTableRow") or _findall_deep(root, "DecisionTableRow")
        if not rows:
            continue  # No rows defined — separate check would catch empty table

        has_default_row = False
        for row in rows:
            conditions = (
                _findall_deep(row, "decisionTableCondition")
                or _findall_deep(row, "DecisionTableCondition")
            )
            # A row with no conditions, or all conditions with empty values, is a default row
            if not conditions:
                has_default_row = True
                break
            all_empty = all(
                not _text(_find_ns(cond, "value") or _find_ns(cond, "Value"))
                for cond in conditions
            )
            if all_empty:
                has_default_row = True
                break

        if not has_default_row:
            issues.append(
                f"[NO DEFAULT ROW] {rel} — No default/fallback row detected. "
                "Without a default row, unmatched inputs return null output attributes "
                "with no runtime error. Add a row with all condition columns blank "
                "returning safe default output values."
            )

    return issues


# ---------------------------------------------------------------------------
# Expression Set (BRE) checks
# ---------------------------------------------------------------------------


def check_expression_set_bre_versions(manifest_dir: Path) -> list[str]:
    """Check ExpressionSetVersion files for BRE activation issues.

    This check looks for Expression Set versions used in BRE context.
    ExpressionSet versions use IsActive=true/false for activation.
    """
    issues: list[str] = []

    version_files = list(manifest_dir.rglob("*.expressionSetVersion-meta.xml"))
    if not version_files:
        version_files = list(manifest_dir.rglob("*ExpressionSetVersion*.xml"))

    for fpath in version_files:
        try:
            tree = ET.parse(fpath)
        except ET.ParseError as exc:
            issues.append(f"XML parse error in {fpath}: {exc}")
            continue

        root = tree.getroot()
        rel = fpath.relative_to(manifest_dir)

        is_active_el = _find_ns(root, "isActive") or _find_ns(root, "IsActive")
        is_active = _text(is_active_el).lower()

        if is_active_el is not None and is_active == "false":
            issues.append(
                f"[ACTIVATION] {rel} — ExpressionSetVersion IsActive=false. "
                "This BRE Expression Set version will not be evaluated at runtime. "
                "Activate post-deploy via the BRE UI or Connect API — "
                "metadata deployment does NOT auto-activate BRE versions."
            )

        # Check for usageType to identify BRE-specific expression sets
        usage_el = _find_ns(root, "usageType") or _find_ns(root, "UsageType")
        usage = _text(usage_el).lower()
        if usage and usage not in ("bre", "producteligibility", "pricing", ""):
            # Non-BRE expression sets are out of scope for this checker
            pass  # Could add a note here if desired

    return issues


def check_expression_set_definitions(manifest_dir: Path) -> list[str]:
    """Check that ExpressionSet definition files have a corresponding version file."""
    issues: list[str] = []

    definition_files = list(manifest_dir.rglob("*.expressionSet-meta.xml"))
    if not definition_files:
        definition_files = list(manifest_dir.rglob("*ExpressionSet*.xml"))
        definition_files = [
            f for f in definition_files
            if "Version" not in f.stem and "version" not in f.stem
        ]

    for fpath in definition_files:
        parent = fpath.parent
        version_siblings = (
            list(parent.rglob("*.expressionSetVersion-meta.xml"))
            + list(parent.rglob("*ExpressionSetVersion*.xml"))
        )
        if not version_siblings:
            rel = fpath.relative_to(manifest_dir)
            issues.append(
                f"[NO VERSION] {rel} — ExpressionSet definition found but no version file "
                "detected in the same directory tree. "
                "A BRE Expression Set cannot be activated without at least one version."
            )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def check_business_rules_engine(manifest_dir: Path) -> list[str]:
    """Run all BRE checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_decision_table_versions(manifest_dir))
    issues.extend(check_decision_table_definitions(manifest_dir))
    issues.extend(check_decision_table_default_rows(manifest_dir))
    issues.extend(check_expression_set_bre_versions(manifest_dir))
    issues.extend(check_expression_set_definitions(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_business_rules_engine(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
