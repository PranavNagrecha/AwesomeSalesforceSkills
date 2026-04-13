#!/usr/bin/env python3
"""Checker script for OmniStudio vs Standard Decision skill.

Detects OmniStudio-related metadata patterns in a Salesforce metadata manifest
directory and reports potential architectural issues.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_vs_standard_decision.py [--help]
    python3 check_omnistudio_vs_standard_decision.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


# Metadata file suffixes for OmniStudio component types
OMNISCRIPT_SUFFIXES = (".omniscript", "-omniscript.xml", "OmniScript.xml")
FLEXCARD_SUFFIXES = (".flexcard", "-flexcard.xml", "FlexCard.xml")
INTEGRATION_PROCEDURE_SUFFIXES = (".integrationprocedure", "-integrationprocedure.xml")
DATARAPTOR_SUFFIXES = (".dataraptor", "-dataraptor.xml", "DataRaptor.xml")

# Flow metadata suffix
FLOW_SUFFIX = ".flow-meta.xml"

# Namespace patterns
VLOCITY_NAMESPACE_PATTERN = re.compile(r"\bvlocity_ins__\w+", re.IGNORECASE)
INDUSTRIES_NAMESPACE_PATTERN = re.compile(r"\bindustries__\w+", re.IGNORECASE)

# Screen flow type marker
SCREEN_FLOW_TYPE_PATTERN = re.compile(r"<processType>Flow</processType>", re.IGNORECASE)


def _collect_files_by_suffix(
    manifest_dir: Path,
    suffixes: tuple[str, ...],
) -> list[Path]:
    """Return all files under manifest_dir whose name ends with any of the given suffixes."""
    matches: list[Path] = []
    for root, _dirs, files in os.walk(manifest_dir):
        for fname in files:
            lower = fname.lower()
            if any(lower.endswith(s.lower()) for s in suffixes):
                matches.append(Path(root) / fname)
    return matches


def _find_files_containing_pattern(
    manifest_dir: Path,
    pattern: re.Pattern[str],
    file_glob_suffix: str = ".xml",
) -> list[Path]:
    """Return paths of files that contain the given regex pattern."""
    hits: list[Path] = []
    for root, _dirs, files in os.walk(manifest_dir):
        for fname in files:
            if not fname.lower().endswith(file_glob_suffix.lower()):
                continue
            fpath = Path(root) / fname
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if pattern.search(content):
                hits.append(fpath)
    return hits


def _derive_process_name(path: Path) -> str:
    """Extract a short human-readable process name from a metadata file path."""
    name = path.stem
    # Strip common suffixes like -omniscript, -flow-meta
    for suffix in ("-omniscript", "-flexcard", "-integrationprocedure", ".flow-meta"):
        if name.lower().endswith(suffix.lower()):
            name = name[: -len(suffix)]
            break
    return name


def check_omnistudio_vs_standard_decision(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Checks performed:
    1. Detect OmniScript metadata files.
    2. Detect FlexCard metadata files.
    3. Check for vlocity_ins__ namespace usage in XML files.
    4. Check for industries__ namespace usage in XML files.
    5. Warn if both Screen Flow and OmniScript metadata exist (possible overlap).
    6. Warn if both vlocity_ins__ and industries__ namespaces are present (mixed state).
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # --- Check 1: OmniScript metadata files ---
    omniscript_files = _collect_files_by_suffix(manifest_dir, OMNISCRIPT_SUFFIXES)
    if omniscript_files:
        issues.append(
            f"Found {len(omniscript_files)} OmniScript metadata file(s). "
            "Verify that the target org holds an Industries Cloud license "
            "(FSC, Health Cloud, Manufacturing, Nonprofit, or Education Cloud). "
            "OmniStudio components will fail silently in unlicensed orgs. "
            f"First match: {omniscript_files[0]}"
        )

    # --- Check 2: FlexCard metadata files ---
    flexcard_files = _collect_files_by_suffix(manifest_dir, FLEXCARD_SUFFIXES)
    if flexcard_files:
        issues.append(
            f"Found {len(flexcard_files)} FlexCard metadata file(s). "
            "FlexCards render as blank components in Lightning App Builder without "
            "a valid OmniStudio license. Confirm license is active in the target org. "
            f"First match: {flexcard_files[0]}"
        )

    # --- Check 3: vlocity_ins__ namespace usage ---
    vlocity_files = _find_files_containing_pattern(manifest_dir, VLOCITY_NAMESPACE_PATTERN)
    if vlocity_files:
        issues.append(
            f"Found {len(vlocity_files)} XML file(s) referencing the 'vlocity_ins__' namespace. "
            "This is the legacy Vlocity managed-package namespace. "
            "Ensure the target org uses this namespace (not 'industries__'). "
            "Namespace mismatch causes silent field reference failures. "
            f"First match: {vlocity_files[0]}"
        )

    # --- Check 4: industries__ namespace usage ---
    industries_files = _find_files_containing_pattern(manifest_dir, INDUSTRIES_NAMESPACE_PATTERN)
    if industries_files:
        issues.append(
            f"Found {len(industries_files)} XML file(s) referencing the 'industries__' namespace. "
            "This is the Salesforce-repackaged OmniStudio managed-package namespace. "
            "Ensure the target org uses this namespace (not 'vlocity_ins__'). "
            f"First match: {industries_files[0]}"
        )

    # --- Check 5: Mixed vlocity_ins__ and industries__ (hybrid namespace state) ---
    if vlocity_files and industries_files:
        issues.append(
            "CRITICAL: Both 'vlocity_ins__' and 'industries__' namespace references found. "
            "This indicates a mixed managed-package state. "
            "The org may be mid-migration between Vlocity and Salesforce-repackaged OmniStudio. "
            "Resolve namespace alignment before deploying — mixing namespaces causes "
            "unpredictable runtime failures."
        )

    # --- Check 6: OmniScript + Screen Flow overlap warning ---
    if omniscript_files:
        # Collect .flow-meta.xml files that contain a Screen Flow process type
        flow_files = _collect_files_by_suffix(manifest_dir, (FLOW_SUFFIX,))
        screen_flows = []
        for fpath in flow_files:
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if SCREEN_FLOW_TYPE_PATTERN.search(content):
                screen_flows.append(fpath)

        if screen_flows:
            omniscript_names = {_derive_process_name(f) for f in omniscript_files}
            screen_flow_names = {_derive_process_name(f) for f in screen_flows}
            overlap_candidates = omniscript_names & screen_flow_names
            if overlap_candidates:
                issues.append(
                    f"Possible overlap: OmniScript and Screen Flow metadata share similar names: "
                    f"{sorted(overlap_candidates)}. "
                    "Verify these are not duplicate implementations of the same guided process. "
                    "Running both in parallel increases maintenance burden and risks inconsistent UX."
                )
            else:
                issues.append(
                    f"OmniScript metadata ({len(omniscript_files)} file(s)) and Screen Flow "
                    f"metadata ({len(screen_flows)} file(s)) are both present in this manifest. "
                    "Confirm these serve distinct use cases. "
                    "Duplicate guided-process implementations in both tools create maintenance overhead."
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for OmniStudio vs Standard Decision issues: "
            "license indicators, namespace consistency, and tooling overlap."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_omnistudio_vs_standard_decision(manifest_dir)

    if not issues:
        print("No OmniStudio vs Standard Decision issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
