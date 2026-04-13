#!/usr/bin/env python3
"""Checker script for OmniStudio vs Standard Architecture skill.

Detects OmniStudio-related metadata patterns in a Salesforce metadata manifest
directory and reports potential architectural issues — particularly mixed-runtime
patterns (Vlocity managed package + Standard Runtime components coexisting) and
missing license gate documentation.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_omnistudio_vs_standard_architecture.py [--help]
    python3 check_omnistudio_vs_standard_architecture.py --manifest-dir path/to/metadata
    python3 check_omnistudio_vs_standard_architecture.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Namespace prefixes that indicate legacy managed-package OmniStudio
# ---------------------------------------------------------------------------
VLOCITY_NAMESPACE_PREFIXES = ("vlocity_ins__", "industries__")

# File extensions that may contain namespace-prefixed OmniStudio references
METADATA_EXTENSIONS = (
    ".xml",
    ".json",
    ".cls",
    ".trigger",
    ".page",
    ".component",
    ".app",
    ".cmp",
    ".js",
    ".html",
)

# Standard Runtime OmniStudio metadata type names (no namespace)
STANDARD_RUNTIME_METADATA_DIRS = (
    "OmniScripts",
    "OmniIntegrationProcedures",
    "FlexCards",
    "OmniDataTransformations",
)

# Managed package OmniStudio metadata type directory patterns
MANAGED_PACKAGE_METADATA_PATTERNS = (
    "vlocity_ins__OmniScript",
    "industries__OmniScript",
    "vlocity_ins__IntegrationProcedure",
    "industries__IntegrationProcedure",
    "vlocity_ins__FlexCard",
    "industries__FlexCard",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for OmniStudio architectural issues: "
            "mixed-runtime patterns, namespace-prefixed references, and "
            "potential license gate violations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _walk_files(root: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Return all files under root matching any of the given extensions."""
    results: list[Path] = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if any(name.endswith(ext) for ext in extensions):
                results.append(Path(dirpath) / name)
    return results


def detect_mixed_runtime(manifest_dir: Path) -> list[str]:
    """Flag orgs where both Standard Runtime and managed-package metadata coexist."""
    issues: list[str] = []

    has_standard_runtime = False
    has_managed_package = False

    standard_rt_found: list[str] = []
    managed_pkg_found: list[str] = []

    for dirpath, dirnames, _filenames in os.walk(manifest_dir):
        for dirname in dirnames:
            if dirname in STANDARD_RUNTIME_METADATA_DIRS:
                has_standard_runtime = True
                standard_rt_found.append(str(Path(dirpath) / dirname))
            if any(dirname.startswith(p) for p in MANAGED_PACKAGE_METADATA_PATTERNS):
                has_managed_package = True
                managed_pkg_found.append(str(Path(dirpath) / dirname))

    if has_standard_runtime and has_managed_package:
        issues.append(
            "MIXED RUNTIME DETECTED: Standard Runtime OmniStudio metadata directories "
            f"({', '.join(standard_rt_found[:3])}) coexist with managed-package metadata directories "
            f"({', '.join(managed_pkg_found[:3])}). "
            "This split-runtime state can cause deployment failures and rendering conflicts. "
            "Run an OmniStudio Conversion Tool assessment before adding new components."
        )

    return issues


def detect_vlocity_namespace_references(manifest_dir: Path) -> list[str]:
    """Flag files that reference Vlocity managed-package namespaces."""
    issues: list[str] = []
    files_with_refs: list[str] = []

    for fpath in _walk_files(manifest_dir, METADATA_EXTENSIONS):
        try:
            content = fpath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(prefix in content for prefix in VLOCITY_NAMESPACE_PREFIXES):
            files_with_refs.append(str(fpath))

    if files_with_refs:
        sample = files_with_refs[:5]
        issues.append(
            f"VLOCITY NAMESPACE REFERENCES FOUND in {len(files_with_refs)} file(s). "
            f"Sample: {', '.join(sample)}. "
            "These indicate Vlocity managed-package OmniStudio is in use. "
            "New OmniStudio components should target Standard Runtime. "
            "If Standard Runtime is also present, assess mixed-runtime risks."
        )

    return issues


def detect_standard_runtime_metadata(manifest_dir: Path) -> list[str]:
    """Report Standard Runtime OmniStudio metadata directories found (informational)."""
    issues: list[str] = []
    found: list[str] = []

    for dirpath, dirnames, _filenames in os.walk(manifest_dir):
        for dirname in dirnames:
            if dirname in STANDARD_RUNTIME_METADATA_DIRS:
                found.append(str(Path(dirpath) / dirname))

    if found:
        issues.append(
            f"INFO: Standard Runtime OmniStudio metadata directories found: {', '.join(found)}. "
            "Confirm Setup > OmniStudio Settings > Enable OmniStudio Standard Runtime is toggled on "
            "in the target org before deploying."
        )

    return issues


def detect_omniscript_without_license_doc(manifest_dir: Path) -> list[str]:
    """Flag OmniStudio metadata presence without an ADR or license confirmation document."""
    issues: list[str] = []

    has_omnistudio = False
    for dirpath, dirnames, _filenames in os.walk(manifest_dir):
        for dirname in dirnames:
            if dirname in STANDARD_RUNTIME_METADATA_DIRS or any(
                dirname.startswith(p) for p in MANAGED_PACKAGE_METADATA_PATTERNS
            ):
                has_omnistudio = True
                break
        if has_omnistudio:
            break

    if not has_omnistudio:
        # Also check for namespace references in files
        for fpath in _walk_files(manifest_dir, METADATA_EXTENSIONS):
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if any(prefix in content for prefix in VLOCITY_NAMESPACE_PREFIXES):
                has_omnistudio = True
                break

    if has_omnistudio:
        # Look for an ADR or decision doc in common locations
        adr_indicators = ("ADR", "adr", "decision", "architecture-decision", "DECISION")
        doc_extensions = (".md", ".txt", ".docx", ".pdf")
        adr_found = False

        for fpath in _walk_files(manifest_dir, doc_extensions):
            if any(indicator in fpath.name for indicator in adr_indicators):
                adr_found = True
                break

        if not adr_found:
            issues.append(
                "MISSING ADR: OmniStudio metadata is present but no Architecture Decision Record "
                "(ADR) document was found in the manifest directory. "
                "Every OmniStudio architecture selection should be documented with license "
                "confirmation, use case continuum mapping, team skills assessment, and stakeholder "
                "sign-off. Use the templates/omnistudio-vs-standard-architecture-template.md template."
            )

    return issues


def check_omnistudio_vs_standard_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(detect_mixed_runtime(manifest_dir))
    issues.extend(detect_vlocity_namespace_references(manifest_dir))
    issues.extend(detect_standard_runtime_metadata(manifest_dir))
    issues.extend(detect_omniscript_without_license_doc(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_omnistudio_vs_standard_architecture(manifest_dir)

    if not issues:
        print("No OmniStudio architectural issues found.")
        return 0

    for issue in issues:
        prefix = "INFO" if issue.startswith("INFO:") else "WARN"
        print(f"{prefix}: {issue}", file=sys.stderr if prefix == "WARN" else sys.stdout)

    warn_count = sum(1 for i in issues if not i.startswith("INFO:"))
    return 1 if warn_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
