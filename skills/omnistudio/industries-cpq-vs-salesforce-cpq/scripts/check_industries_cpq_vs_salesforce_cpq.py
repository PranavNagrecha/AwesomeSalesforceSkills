#!/usr/bin/env python3
"""Checker script for Industries CPQ vs Salesforce CPQ skill.

Inspects Salesforce metadata in a local SFDX project directory for signals
that indicate which CPQ product is present and flags common misconfiguration
or coexistence risks.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_cpq_vs_salesforce_cpq.py [--help]
    python3 check_industries_cpq_vs_salesforce_cpq.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata directory for CPQ product signals and "
            "common Industries CPQ / Salesforce CPQ coexistence risks."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files_with_extension(root: Path, extension: str) -> list[Path]:
    """Recursively find all files with the given extension under root."""
    results: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fname in filenames:
            if fname.endswith(extension):
                results.append(Path(dirpath) / fname)
    return results


def check_for_sbqq_namespace(manifest_dir: Path) -> list[str]:
    """Check for Salesforce CPQ managed-package namespace references."""
    issues: list[str] = []
    apex_files = find_files_with_extension(manifest_dir, ".cls")
    trigger_files = find_files_with_extension(manifest_dir, ".trigger")
    all_apex = apex_files + trigger_files

    sbqq_files = []
    for f in all_apex:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if "SBQQ__" in content:
                sbqq_files.append(str(f))
        except OSError:
            pass

    if sbqq_files:
        issues.append(
            f"Salesforce CPQ managed-package namespace (SBQQ__) found in {len(sbqq_files)} "
            f"Apex file(s). These will require remapping if migrating to Revenue Cloud: "
            f"{', '.join(sbqq_files[:5])}"
            + (" [and more]" if len(sbqq_files) > 5 else "")
        )
    return issues


def check_for_vlocity_namespace_in_datapacks(manifest_dir: Path) -> list[str]:
    """Check for legacy Vlocity namespace tokens in DataPack JSON files."""
    issues: list[str] = []
    json_files = find_files_with_extension(manifest_dir, ".json")

    vlocity_files = []
    for f in json_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if "%vlocity_namespace%" in content:
                vlocity_files.append(str(f))
        except OSError:
            pass

    if vlocity_files:
        issues.append(
            f"Legacy Vlocity namespace token (%vlocity_namespace%) found in "
            f"{len(vlocity_files)} JSON file(s). These DataPacks require namespace "
            f"migration before deploying to a native OmniStudio org: "
            f"{', '.join(vlocity_files[:5])}"
            + (" [and more]" if len(vlocity_files) > 5 else "")
        )
    return issues


def check_for_coexistence_signals(manifest_dir: Path) -> list[str]:
    """Check for signals that both CPQ products may be in use simultaneously."""
    issues: list[str] = []

    # Look for OmniScript XML files (Industries CPQ signal)
    xml_files = find_files_with_extension(manifest_dir, ".xml")
    omni_scripts = [
        f for f in xml_files
        if "OmniScript" in f.name or "omniScript" in f.name
    ]

    # Look for Salesforce CPQ managed-package object XML files
    sbqq_xml = [
        f for f in xml_files
        if "SBQQ__" in f.name
    ]

    if omni_scripts and sbqq_xml:
        issues.append(
            "Both OmniScript components and SBQQ__ object definitions detected in the "
            "same metadata directory. This may indicate Industries CPQ and Salesforce CPQ "
            "coexistence. Review the CPQ coexistence governance design in "
            "references/examples.md before proceeding."
        )
    return issues


def check_for_calculation_procedures(manifest_dir: Path) -> list[str]:
    """Check for Industries CPQ Calculation Procedure components."""
    issues: list[str] = []
    json_files = find_files_with_extension(manifest_dir, ".json")

    calc_proc_files = [
        f for f in json_files
        if "CalculationProcedure" in f.name or "calculationProcedure" in f.name
    ]

    if calc_proc_files:
        # Not an issue — just informational to confirm Industries CPQ presence
        issues.append(
            f"INFO: {len(calc_proc_files)} Calculation Procedure file(s) detected — "
            "confirms Industries CPQ is in use. Ensure OmniStudio / Industries Cloud "
            "license is confirmed for target org before deploying."
        )
    return issues


def check_for_cpq_plugin_apex(manifest_dir: Path) -> list[str]:
    """Check for Salesforce CPQ Apex plugin interface implementations."""
    issues: list[str] = []
    apex_files = find_files_with_extension(manifest_dir, ".cls")

    plugin_interfaces = [
        "SBQQ.QuoteCalculatorPlugin",
        "SBQQ.PricingPlugin",
        "SBQQ.ProductPlugin",
        "SBQQ.QuoteDocumentPlugin",
    ]

    plugin_files = []
    for f in apex_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            if any(iface in content for iface in plugin_interfaces):
                plugin_files.append(str(f))
        except OSError:
            pass

    if plugin_files:
        issues.append(
            f"Salesforce CPQ Apex plugin interface implementation(s) found in "
            f"{len(plugin_files)} file(s). Revenue Cloud does not support the same "
            f"Apex plugin hook points. These will require redesign during migration: "
            f"{', '.join(plugin_files[:3])}"
            + (" [and more]" if len(plugin_files) > 3 else "")
        )
    return issues


def check_industries_cpq_vs_salesforce_cpq(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue/info strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_for_sbqq_namespace(manifest_dir))
    issues.extend(check_for_vlocity_namespace_in_datapacks(manifest_dir))
    issues.extend(check_for_coexistence_signals(manifest_dir))
    issues.extend(check_for_calculation_procedures(manifest_dir))
    issues.extend(check_for_cpq_plugin_apex(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_industries_cpq_vs_salesforce_cpq(manifest_dir)

    if not issues:
        print("No CPQ issues detected in the manifest directory.")
        return 0

    error_count = 0
    for issue in issues:
        if issue.startswith("INFO:"):
            print(f"  {issue}")
        else:
            print(f"ISSUE: {issue}")
            error_count += 1

    if error_count:
        print(f"\n{error_count} issue(s) found. Review the skill guidance before proceeding.")

    return 1 if error_count else 0


if __name__ == "__main__":
    sys.exit(main())
