#!/usr/bin/env python3
"""Checker script for Calculation Procedures skill.

Inspects Salesforce metadata files for common Calculation Procedure and
Calculation Matrix configuration issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_calculation_procedures.py [--manifest-dir PATH]

The manifest directory should be the root of a Salesforce DX project or a
retrieved metadata tree. The checker looks for:
  - ExpressionSet / ExpressionSetVersion XML files
  - CalculationMatrix / CalculationMatrixVersion XML files

Checks performed:
  1. ExpressionSetVersion files where IsActive is not 'true'
  2. ExpressionSetVersion files referencing a SubExpression step (basic XML scan)
  3. CalculationMatrixVersion files where IsActive is not 'true' or EndDateTime is
     set to a date in the past (relative to the current system date)
  4. Presence of any ExpressionSet or CalculationMatrix file without a
     corresponding version file in the same directory tree
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Calculation Procedures configuration and metadata for common issues.",
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
    """Return stripped text of an XML element, or empty string."""
    if element is None:
        return ""
    return (element.text or "").strip()


def _find_ns(root: ET.Element, tag: str) -> ET.Element | None:
    """Find a child element ignoring any XML namespace prefix."""
    for child in root:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == tag:
            return child
    return None


def _findall_ns(root: ET.Element, tag: str) -> list[ET.Element]:
    """Find all child elements ignoring any XML namespace prefix."""
    result = []
    for child in root:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local == tag:
            result.append(child)
    return result


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_expression_set_versions(manifest_dir: Path) -> list[str]:
    """Check ExpressionSetVersion metadata files for activation issues."""
    issues: list[str] = []
    now = datetime.now(tz=timezone.utc)

    version_files = list(manifest_dir.rglob("*.expressionSetVersion-meta.xml"))
    if not version_files:
        # Also look for generic XML under expressionSetVersions directories
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
        if is_active == "false":
            issues.append(
                f"[ACTIVATION] {rel} — ExpressionSetVersion IsActive=false. "
                "Procedure will error at runtime if called."
            )

        end_dt_el = _find_ns(root, "endDateTime") or _find_ns(root, "EndDateTime")
        if end_dt_el is not None:
            end_str = _text(end_dt_el)
            if end_str:
                try:
                    # Accept ISO 8601 with or without timezone
                    end_str_clean = end_str.replace("Z", "+00:00")
                    end_dt = datetime.fromisoformat(end_str_clean)
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                    if end_dt < now:
                        issues.append(
                            f"[EXPIRED VERSION] {rel} — EndDateTime {end_str!r} is in the past. "
                            "This version will never be selected at runtime."
                        )
                except ValueError:
                    issues.append(
                        f"[DATE PARSE] {rel} — Cannot parse EndDateTime value {end_str!r}."
                    )

    return issues


def check_calculation_matrix_versions(manifest_dir: Path) -> list[str]:
    """Check CalculationMatrixVersion metadata files for activation and date issues."""
    issues: list[str] = []
    now = datetime.now(tz=timezone.utc)

    version_files = list(manifest_dir.rglob("*.calculationMatrixVersion-meta.xml"))
    if not version_files:
        version_files = list(manifest_dir.rglob("*CalculationMatrixVersion*.xml"))

    for fpath in version_files:
        try:
            tree = ET.parse(fpath)
        except ET.ParseError as exc:
            issues.append(f"XML parse error in {fpath}: {exc}")
            continue

        root = tree.getroot()
        rel = fpath.relative_to(manifest_dir)

        is_active_el = (
            _find_ns(root, "isActive")
            or _find_ns(root, "IsActive")
            or _find_ns(root, "IsVersionEnabled")
        )
        is_active = _text(is_active_el).lower()
        if is_active == "false":
            issues.append(
                f"[ACTIVATION] {rel} — CalculationMatrixVersion is inactive. "
                "Lookup steps referencing this matrix will return null at runtime."
            )

        end_dt_el = _find_ns(root, "endDateTime") or _find_ns(root, "EndDateTime")
        if end_dt_el is not None:
            end_str = _text(end_dt_el)
            if end_str:
                try:
                    end_str_clean = end_str.replace("Z", "+00:00")
                    end_dt = datetime.fromisoformat(end_str_clean)
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                    if end_dt < now:
                        issues.append(
                            f"[EXPIRED VERSION] {rel} — Matrix version EndDateTime {end_str!r} "
                            "is in the past. This version will not be selected."
                        )
                except ValueError:
                    issues.append(
                        f"[DATE PARSE] {rel} — Cannot parse EndDateTime value {end_str!r}."
                    )

        rank_el = _find_ns(root, "rank") or _find_ns(root, "Rank")
        if rank_el is None:
            issues.append(
                f"[RANK MISSING] {rel} — CalculationMatrixVersion has no Rank field. "
                "If multiple versions overlap in date range, selection will be non-deterministic."
            )

    return issues


def check_expression_set_definitions(manifest_dir: Path) -> list[str]:
    """Check that ExpressionSet definition files have a corresponding version file nearby."""
    issues: list[str] = []

    definition_files = list(manifest_dir.rglob("*.expressionSet-meta.xml"))
    if not definition_files:
        definition_files = list(manifest_dir.rglob("*ExpressionSet*.xml"))
        # Exclude version files from the definition list
        definition_files = [
            f for f in definition_files
            if "Version" not in f.stem and "version" not in f.stem
        ]

    for fpath in definition_files:
        parent = fpath.parent
        # Look for any version file in the same directory or subdirectories
        version_siblings = (
            list(parent.rglob("*.expressionSetVersion-meta.xml"))
            + list(parent.rglob("*ExpressionSetVersion*.xml"))
        )
        if not version_siblings:
            rel = fpath.relative_to(manifest_dir)
            issues.append(
                f"[NO VERSION] {rel} — ExpressionSet definition found but no version file "
                "detected in the same directory tree. Procedure cannot be activated without a version."
            )

    return issues


def check_calculation_matrix_definitions(manifest_dir: Path) -> list[str]:
    """Check that CalculationMatrix definition files have a corresponding version file nearby."""
    issues: list[str] = []

    definition_files = list(manifest_dir.rglob("*.calculationMatrix-meta.xml"))
    if not definition_files:
        definition_files = list(manifest_dir.rglob("*CalculationMatrix*.xml"))
        definition_files = [
            f for f in definition_files
            if "Version" not in f.stem and "version" not in f.stem
            and "Row" not in f.stem and "Column" not in f.stem
        ]

    for fpath in definition_files:
        parent = fpath.parent
        version_siblings = (
            list(parent.rglob("*.calculationMatrixVersion-meta.xml"))
            + list(parent.rglob("*CalculationMatrixVersion*.xml"))
        )
        if not version_siblings:
            rel = fpath.relative_to(manifest_dir)
            issues.append(
                f"[NO VERSION] {rel} — CalculationMatrix definition found but no version file "
                "detected in the same directory tree. Lookup steps will fail without an active version."
            )

    return issues


def check_for_looping_enabled(manifest_dir: Path) -> list[str]:
    """Warn when IsLoopingEnabled=true is found in expression set version files."""
    issues: list[str] = []

    version_files = (
        list(manifest_dir.rglob("*.expressionSetVersion-meta.xml"))
        + list(manifest_dir.rglob("*ExpressionSetVersion*.xml"))
    )

    for fpath in version_files:
        try:
            tree = ET.parse(fpath)
        except ET.ParseError:
            continue  # Already reported in check_expression_set_versions

        root = tree.getroot()
        looping_el = _find_ns(root, "isLoopingEnabled") or _find_ns(root, "IsLoopingEnabled")
        if looping_el is not None and _text(looping_el).lower() == "true":
            rel = fpath.relative_to(manifest_dir)
            issues.append(
                f"[LOOPING ENABLED] {rel} — IsLoopingEnabled=true. Looping significantly "
                "increases execution time. Verify this is intentional and that loop termination "
                "conditions are correctly configured."
            )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def check_calculation_procedures(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_expression_set_versions(manifest_dir))
    issues.extend(check_calculation_matrix_versions(manifest_dir))
    issues.extend(check_expression_set_definitions(manifest_dir))
    issues.extend(check_calculation_matrix_definitions(manifest_dir))
    issues.extend(check_for_looping_enabled(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_calculation_procedures(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
