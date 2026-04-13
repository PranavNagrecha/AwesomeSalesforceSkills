#!/usr/bin/env python3
"""Checker script for Program Outcome Tracking Design skill.

Checks org metadata or configuration relevant to Program Outcome Tracking Design.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_program_outcome_tracking_design.py [--help]
    python3 check_program_outcome_tracking_design.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Program Outcome Tracking Design configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files_recursive(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return list(root.rglob(pattern))


def check_pmm_namespace_objects(manifest_dir: Path, issues: list[str]) -> None:
    """Check for pmdm namespace objects (Program__c, ProgramEngagement__c, ServiceDelivery__c)."""
    # Look for pmdm__* or PMDM__* object metadata files
    all_object_files = find_files_recursive(manifest_dir, "*.object-meta.xml")
    object_names = [f.stem.replace(".object-meta", "") for f in all_object_files]

    pmm_core_objects = {
        "pmdm__Program__c": "Program__c (PMM core object — represents a program)",
        "pmdm__ProgramEngagement__c": "ProgramEngagement__c (PMM core object — participant enrollment)",
        "pmdm__ServiceDelivery__c": "ServiceDelivery__c (PMM core object — service delivery records)",
    }

    # Also search Apex files and metadata for pmdm__ namespace references
    apex_files = find_files_recursive(manifest_dir, "*.cls")
    all_apex_content = ""
    for af in apex_files:
        all_apex_content += af.read_text(encoding="utf-8", errors="replace")

    # Check field metadata for pmdm namespace references
    field_files = find_files_recursive(manifest_dir, "*.field-meta.xml")
    all_field_content = ""
    for ff in field_files:
        all_field_content += ff.read_text(encoding="utf-8", errors="replace")

    combined_content = all_apex_content + all_field_content

    for obj_api, obj_label in pmm_core_objects.items():
        # Match either prefixed object file name or namespace reference in code
        short_name = obj_api.replace("pmdm__", "")
        found_in_files = any(obj_api in n or short_name in n for n in object_names)
        found_in_content = obj_api in combined_content or obj_api.replace("pmdm__", "pmdm__") in combined_content

        if not found_in_files and not found_in_content:
            issues.append(
                f"{obj_api} ({obj_label}) not found in manifest. "
                "NPSP Program Management Module (PMM) uses the pmdm namespace. "
                "If this org uses PMM, confirm the package is installed and these objects are present. "
                "If the org uses Nonprofit Cloud (NPC), the object model is different — "
                "NPC uses Program, ProgramEngagement, and ServiceDelivery without the pmdm__ prefix."
            )
        else:
            print(f"  OK: Found reference to {obj_api}.")


def check_custom_outcome_objects(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if no custom Outcome or Indicator objects exist — PMM ships none, practitioner must build them."""
    all_object_files = find_files_recursive(manifest_dir, "*.object-meta.xml")
    object_names = [f.stem.replace(".object-meta", "").lower() for f in all_object_files]

    outcome_patterns = ["outcome", "indicator", "logicmodel", "impact_measure", "program_result"]
    found_outcome = any(
        any(pat in name for pat in outcome_patterns)
        for name in object_names
    )

    if not found_outcome:
        issues.append(
            "No custom Outcome or Indicator object found in manifest. "
            "NPSP PMM does NOT ship Outcome__c, Indicator__c, or LogicModel__c objects. "
            "Structured outcome tracking (indicators, targets, actuals) requires custom objects "
            "designed by the implementor. Without custom outcome objects, grant reporting can only "
            "surface service delivery counts (Quantity__c on ServiceDelivery__c), not measured outcomes. "
            "If the org uses Nonprofit Cloud (NPC), use the native Outcome Management feature instead "
            "of building custom objects."
        )
    else:
        matched = [n for n in object_names if any(pat in n for pat in outcome_patterns)]
        print(f"  OK: Found potential outcome/indicator object(s): {matched}")


def check_service_delivery_custom_fields(manifest_dir: Path, issues: list[str]) -> None:
    """Check for custom fields on ServiceDelivery__c — Quantity__c and UnitOfMeasurement__c are stock."""
    # Look for field metadata files scoped to ServiceDelivery
    sd_field_files = find_files_recursive(manifest_dir, "ServiceDelivery__c.*.field-meta.xml")
    # Also match pmdm__ServiceDelivery__c
    pmdm_sd_field_files = find_files_recursive(manifest_dir, "pmdm__ServiceDelivery__c.*.field-meta.xml")
    # Fields directory pattern: objects/ServiceDelivery__c/fields/*.field-meta.xml
    sd_dir_field_files = find_files_recursive(manifest_dir, "fields/*.field-meta.xml")

    # Filter to ServiceDelivery context
    def is_sd_field(p: Path) -> bool:
        parts = [part.lower() for part in p.parts]
        return "servicedelivery__c" in parts or "pmdm__servicedelivery__c" in parts

    sd_fields = sd_field_files + pmdm_sd_field_files + [f for f in sd_dir_field_files if is_sd_field(f)]

    stock_fields = {"quantity__c", "unitofmeasurement__c", "pmdm__quantity__c", "pmdm__unitofmeasurement__c"}
    custom_fields = [
        f for f in sd_fields
        if f.stem.replace(".field-meta", "").lower() not in stock_fields
        and not f.stem.replace(".field-meta", "").startswith("pmdm__")  # exclude managed fields
    ]

    if sd_fields and not custom_fields:
        issues.append(
            "ServiceDelivery__c fields found in manifest include only standard PMM fields "
            "(Quantity__c, UnitOfMeasurement__c). No custom fields detected on ServiceDelivery__c. "
            "If the org tracks additional outcome-related data at the delivery level "
            "(e.g., pre/post assessment scores, attendance type, completion indicator), "
            "custom fields on ServiceDelivery__c should be added. "
            "Remember: Quantity__c tracks units of service delivered, not outcome achievement."
        )
    elif not sd_fields:
        # No ServiceDelivery field metadata found — not necessarily an error, depends on structure
        print("  INFO: No ServiceDelivery__c field metadata found to inspect (may be a full-package install).")
    else:
        print(f"  OK: Found {len(custom_fields)} custom field(s) on ServiceDelivery__c.")


def check_npc_objects_in_npsp_context(manifest_dir: Path, issues: list[str]) -> None:
    """Warn if the org appears to be NPC (Nonprofit Cloud) vs NPSP — different object model."""
    all_object_files = find_files_recursive(manifest_dir, "*.object-meta.xml")
    all_field_files = find_files_recursive(manifest_dir, "*.field-meta.xml")
    all_apex_files = find_files_recursive(manifest_dir, "*.cls")

    object_names = " ".join(f.name for f in all_object_files + all_field_files)
    apex_content = " ".join(
        f.read_text(encoding="utf-8", errors="replace") for f in all_apex_files
    )

    # NPC-specific signals
    npc_signals = [
        ("npc__", "NPC namespace prefix (npc__) detected"),
        ("OutcomeMgmt", "Outcome Management (NPC native feature) references detected"),
        ("IndividualApplication", "IndividualApplication object (NPC pattern) detected"),
    ]
    # NPSP signals
    npsp_signals = [
        "npsp__",
        "npe01__",
        "npo02__",
        "pmdm__",
    ]

    has_npc = any(signal in object_names or signal in apex_content for signal, _ in npc_signals)
    has_npsp = any(signal in object_names or signal in apex_content for signal in npsp_signals)

    if has_npc and has_npsp:
        issues.append(
            "Metadata contains both NPC (npc__ namespace / OutcomeMgmt) and NPSP (npsp__, npe01__, pmdm__) "
            "namespace references. These are distinct platforms with different object models. "
            "NPC Outcome Management objects (Outcome, Indicator, Indicator Result) are NOT available in "
            "NPSP/PMM orgs. Confirm which platform this org is on before proceeding with outcome design. "
            "Mixed signals may indicate an in-progress migration or a mismatched architecture document."
        )
    elif has_npc and not has_npsp:
        print(
            "  INFO: Org appears to be Nonprofit Cloud (NPC) based on namespace signals. "
            "Use NPC Outcome Management (Outcome, Indicator, Indicator Result) — not custom objects."
        )
    elif has_npsp and not has_npc:
        print("  OK: Org appears to be NPSP/PMM based on namespace signals.")
    else:
        issues.append(
            "Neither NPSP (npsp__, npe01__, pmdm__) nor NPC namespace signals detected in manifest. "
            "Confirm whether this is an NPSP/PMM org or Nonprofit Cloud (NPC) org before designing "
            "outcome tracking objects. The data models are fundamentally different between platforms."
        )


def check_program_outcome_tracking_design(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    print(f"Checking Program Outcome Tracking Design in: {manifest_dir.resolve()}")

    check_pmm_namespace_objects(manifest_dir, issues)
    check_custom_outcome_objects(manifest_dir, issues)
    check_service_delivery_custom_fields(manifest_dir, issues)
    check_npc_objects_in_npsp_context(manifest_dir, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_program_outcome_tracking_design(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:", file=sys.stderr)
    for issue in issues:
        print(f"\nWARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
