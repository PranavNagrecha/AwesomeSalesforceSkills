#!/usr/bin/env python3
"""Checker script for API Version Management skill.

Scans a Salesforce metadata source directory for API version drift, retired
versions, and missing explicit LWC version declarations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_api_version_management.py --manifest-dir force-app/
    python3 check_api_version_management.py --manifest-dir force-app/ --min-version 45
    python3 check_api_version_management.py --manifest-dir . --project-file sfdx-project.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Versions 7.0-30.0 retired in Summer '22. 31.0 is the absolute floor.
ABSOLUTE_MIN_VERSION = 31

# Default "current" version — Spring '25
DEFAULT_CURRENT_VERSION = 63

# Maximum acceptable drift from sourceApiVersion
MAX_DRIFT = 2

# Regex to extract <apiVersion>NN.0</apiVersion> from XML metadata
_RE_API_VERSION = re.compile(
    r"<apiVersion>\s*(\d+)(?:\.\d+)?\s*</apiVersion>", re.IGNORECASE
)

# Aura component/application version attribute
_RE_AURA_VERSION = re.compile(
    r'<aura:(?:component|application|event|interface)[^>]*\bversion\s*=\s*"(\d+(?:\.\d+)?)"',
    re.IGNORECASE,
)

# Metadata file extensions that carry apiVersion
META_XML_GLOBS = [
    "**/*.cls-meta.xml",
    "**/*.trigger-meta.xml",
    "**/*.page-meta.xml",
    "**/*.component-meta.xml",
    "**/*.js-meta.xml",
    "**/*.email-meta.xml",
    "**/*.resource-meta.xml",
    "**/*.app-meta.xml",
]

# Aura markup files that may carry version attributes
AURA_GLOBS = [
    "**/*.cmp",
    "**/*.app",
    "**/*.evt",
    "**/*.intf",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Salesforce metadata for API version drift, retired versions, "
            "and missing LWC version declarations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata source (default: current directory).",
    )
    parser.add_argument(
        "--project-file",
        default=None,
        help="Path to sfdx-project.json. If provided, sourceApiVersion is read from it.",
    )
    parser.add_argument(
        "--min-version",
        type=int,
        default=ABSOLUTE_MIN_VERSION,
        help=f"Minimum acceptable API version (default: {ABSOLUTE_MIN_VERSION}).",
    )
    parser.add_argument(
        "--max-drift",
        type=int,
        default=MAX_DRIFT,
        help=f"Maximum acceptable version drift from sourceApiVersion (default: {MAX_DRIFT}).",
    )
    return parser.parse_args()


def read_source_api_version(project_file: Path) -> int | None:
    """Read sourceApiVersion from sfdx-project.json."""
    if not project_file.exists():
        return None
    try:
        data = json.loads(project_file.read_text(encoding="utf-8"))
        raw = data.get("sourceApiVersion", "")
        # sourceApiVersion is a string like "63.0"
        match = re.match(r"(\d+)", str(raw))
        return int(match.group(1)) if match else None
    except (json.JSONDecodeError, ValueError):
        return None


def extract_version_from_xml(filepath: Path) -> int | None:
    """Extract the apiVersion integer from an XML metadata file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = _RE_API_VERSION.search(content)
    if match:
        return int(match.group(1))
    return None


def extract_version_from_aura(filepath: Path) -> int | None:
    """Extract the version attribute from an Aura markup file."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    match = _RE_AURA_VERSION.search(content)
    if match:
        return int(float(match.group(1)))
    return None


def check_api_version_management(
    manifest_dir: Path,
    source_api_version: int | None,
    min_version: int,
    max_drift: int,
) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    baseline = source_api_version or DEFAULT_CURRENT_VERSION
    component_versions: list[tuple[Path, int]] = []

    # --- Scan meta.xml files ---
    for glob_pattern in META_XML_GLOBS:
        for filepath in manifest_dir.rglob(glob_pattern.replace("**/", "")):
            version = extract_version_from_xml(filepath)
            if version is not None:
                component_versions.append((filepath, version))

    # --- Scan Aura markup files ---
    for glob_pattern in AURA_GLOBS:
        for filepath in manifest_dir.rglob(glob_pattern.replace("**/", "")):
            version = extract_version_from_aura(filepath)
            if version is not None:
                component_versions.append((filepath, version))

    if not component_versions:
        issues.append(
            f"No versioned metadata files found in {manifest_dir}. "
            "Verify the directory contains Salesforce source metadata."
        )
        return issues

    # --- Check for retired versions ---
    retired = [
        (p, v) for p, v in component_versions if v < min_version
    ]
    for filepath, version in retired:
        issues.append(
            f"RETIRED VERSION: {filepath.name} is at API version {version}.0 "
            f"(minimum safe: {min_version}.0). This version is retired or approaching retirement."
        )

    # --- Check for version drift ---
    drifted = [
        (p, v) for p, v in component_versions
        if v < (baseline - max_drift) and v >= min_version
    ]
    for filepath, version in drifted:
        issues.append(
            f"VERSION DRIFT: {filepath.name} is at API version {version}.0, "
            f"which is {baseline - version} versions behind sourceApiVersion {baseline}.0 "
            f"(max drift tolerance: {max_drift})."
        )

    # --- Check for LWC bundles missing explicit apiVersion ---
    for filepath in manifest_dir.rglob("*.js-meta.xml"):
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not _RE_API_VERSION.search(content):
            issues.append(
                f"MISSING LWC VERSION: {filepath.name} has no explicit <apiVersion> element. "
                "As of Spring '25, LWC components require explicit version declaration."
            )

    # --- Summary statistics ---
    versions = [v for _, v in component_versions]
    version_counts: dict[int, int] = {}
    for v in versions:
        version_counts[v] = version_counts.get(v, 0) + 1

    if len(version_counts) > 1:
        summary_parts = [f"v{v}.0: {c}" for v, c in sorted(version_counts.items())]
        issues.append(
            f"VERSION SPREAD: {len(component_versions)} components across "
            f"{len(version_counts)} distinct versions ({', '.join(summary_parts)}). "
            f"Target: consolidate to {baseline}.0."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    # Read sourceApiVersion if project file specified or auto-detect
    source_api_version = None
    if args.project_file:
        project_path = Path(args.project_file)
        source_api_version = read_source_api_version(project_path)
        if source_api_version is None:
            print(f"WARNING: Could not read sourceApiVersion from {args.project_file}")
    else:
        # Auto-detect sfdx-project.json in manifest dir or parent
        for candidate in [
            manifest_dir / "sfdx-project.json",
            manifest_dir.parent / "sfdx-project.json",
        ]:
            source_api_version = read_source_api_version(candidate)
            if source_api_version is not None:
                print(f"INFO: Using sourceApiVersion {source_api_version}.0 from {candidate}")
                break

    issues = check_api_version_management(
        manifest_dir, source_api_version, args.min_version, args.max_drift
    )

    if not issues:
        print("No API version issues found. All components are consistent and current.")
        return 0

    print(f"\n{'='*70}")
    print(f"API VERSION MANAGEMENT — {len(issues)} issue(s) found")
    print(f"{'='*70}\n")

    for issue in issues:
        print(f"  ISSUE: {issue}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
