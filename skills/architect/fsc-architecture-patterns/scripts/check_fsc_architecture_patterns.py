#!/usr/bin/env python3
"""Checker script for FSC Architecture Patterns skill.

Checks Salesforce metadata for common FSC architecture anti-patterns:
- Managed-package (FinServ__) namespace references in platform-native FSC projects
- Synchronous callout patterns inside FSC object triggers
- Missing Compliant Data Sharing indicators

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_architecture_patterns.py [--help]
    python3 check_fsc_architecture_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Patterns that indicate managed-package FSC namespace usage
FINSERV_NAMESPACE_PATTERN = re.compile(r"\bFinServ__\w+", re.IGNORECASE)

# Patterns that indicate synchronous HTTP callouts inside Apex
SYNC_CALLOUT_PATTERN = re.compile(
    r"(new\s+HttpRequest\(\)|Http\(\)\.send|HttpRequest\s+\w+\s*=)",
    re.IGNORECASE,
)

# Apex file extensions
APEX_EXTENSIONS = {".cls", ".trigger"}

# Metadata XML extensions
XML_EXTENSIONS = {".xml"}


# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------


def _find_files_with_extension(root: Path, extensions: set[str]) -> list[Path]:
    """Return all files under root matching the given extensions."""
    results: list[Path] = []
    for ext in extensions:
        results.extend(root.rglob(f"*{ext}"))
    return sorted(results)


def check_finserv_namespace_in_apex(manifest_dir: Path) -> list[str]:
    """Flag Apex files that reference FinServ__ namespaced objects.

    In platform-native FSC orgs, FinServ__ references indicate either:
    - Legacy code that hasn't been migrated, or
    - A mistaken assumption that the managed package is installed.
    """
    issues: list[str] = []
    apex_files = _find_files_with_extension(manifest_dir, APEX_EXTENSIONS)

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        matches = FINSERV_NAMESPACE_PATTERN.findall(content)
        if matches:
            unique_refs = sorted(set(matches))
            issues.append(
                f"FinServ__ namespace reference(s) found in {apex_file.name} "
                f"— verify this is a managed-package org, not platform-native FSC. "
                f"References: {', '.join(unique_refs[:5])}"
                + (" (and more)" if len(unique_refs) > 5 else "")
            )

    return issues


def check_sync_callouts_in_fsc_triggers(manifest_dir: Path) -> list[str]:
    """Flag trigger files that contain synchronous HTTP callout patterns.

    Synchronous callouts inside triggers on FSC objects (FinancialAccount,
    FinancialHolding, etc.) couple record saves to external system availability.
    This is an FSC architecture anti-pattern; use Platform Events instead.
    """
    issues: list[str] = []
    trigger_files = _find_files_with_extension(manifest_dir, {".trigger"})

    for trigger_file in trigger_files:
        try:
            content = trigger_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if SYNC_CALLOUT_PATTERN.search(content):
            issues.append(
                f"Synchronous HTTP callout pattern detected in trigger {trigger_file.name} "
                f"— FSC architecture requires async integration (Platform Events / Queueable). "
                f"Synchronous callouts from FinancialAccount or FinancialHolding triggers "
                f"couple record saves to external system availability."
            )

    return issues


def check_fsc_sharing_xml(manifest_dir: Path) -> list[str]:
    """Check sharing metadata for indicators of CDS-incompatible OWD settings.

    Looks for SharingModel metadata that would indicate FinancialAccount OWD
    is not set to Private, which would make CDS ineffective.
    """
    issues: list[str] = []
    xml_files = _find_files_with_extension(manifest_dir, XML_EXTENSIONS)

    # Look for object metadata files that might describe FinancialAccount sharing
    for xml_file in xml_files:
        if "FinancialAccount" not in xml_file.name and "financialaccount" not in xml_file.name.lower():
            continue

        try:
            content = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Check for non-private sharing model on FinancialAccount
        # Metadata format: <sharingModel>ReadWrite</sharingModel> or <sharingModel>Read</sharingModel>
        sharing_match = re.search(
            r"<sharingModel>(ReadWrite|Read|ControlledByParent)</sharingModel>",
            content,
            re.IGNORECASE,
        )
        if sharing_match:
            sharing_model = sharing_match.group(1)
            issues.append(
                f"FinancialAccount OWD appears to be '{sharing_model}' in {xml_file.name}. "
                f"Compliant Data Sharing requires OWD = Private to enforce advisor-relationship "
                f"based access control. A non-Private OWD makes CDS share sets ineffective."
            )

    return issues


def check_finserv_namespace_in_flows(manifest_dir: Path) -> list[str]:
    """Flag Flow metadata files that reference FinServ__ namespaced objects.

    Flow XML files may reference FinServ__ objects in API name fields.
    In platform-native FSC orgs, these references indicate stale or incorrect flow design.
    """
    issues: list[str] = []
    # Flows are stored as .flow-meta.xml files
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))

    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        matches = FINSERV_NAMESPACE_PATTERN.findall(content)
        if matches:
            unique_refs = sorted(set(matches))
            issues.append(
                f"FinServ__ namespace reference(s) found in Flow {flow_file.name} "
                f"— verify this is a managed-package org, not platform-native FSC. "
                f"References: {', '.join(unique_refs[:5])}"
                + (" (and more)" if len(unique_refs) > 5 else "")
            )

    return issues


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------


def check_fsc_architecture_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of FSC architecture issues found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_finserv_namespace_in_apex(manifest_dir))
    issues.extend(check_sync_callouts_in_fsc_triggers(manifest_dir))
    issues.extend(check_fsc_sharing_xml(manifest_dir))
    issues.extend(check_finserv_namespace_in_flows(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for FSC architecture anti-patterns. "
            "Detects managed-package namespace in platform-native orgs, "
            "synchronous callouts in triggers, and CDS-incompatible OWD settings."
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
    issues = check_fsc_architecture_patterns(manifest_dir)

    if not issues:
        print("No FSC architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
