#!/usr/bin/env python3
"""Checker script for Vlocity to Native OmniStudio Migration skill.

Scans a Salesforce SFDX project directory for Vlocity managed package
namespace references that must be updated before or after running the
OmniStudio Migration Tool.

Checks performed:
  1. LWC HTML files using managed package OmniStudio component tags
     (c-omni-script, c-flex-card, c-omni-card) instead of native omnistudio-* tags.
  2. Apex classes calling Vlocity service classes
     (vlocity_ins., vlocity_cmt., vlocity_ps.).
  3. Apex classes or SOQL referencing Vlocity custom objects
     (vlocity_ins__OmniScript__c, etc.).
  4. package.xml manifests missing native OmniStudio metadata types.
  5. JavaScript files using direct fetch/XMLHttpRequest calls to Integration
     Procedure REST endpoints (bypasses sharing enforcement).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_vlocity_to_native_omnistudio_migration.py [--manifest-dir PATH]
    python3 check_vlocity_to_native_omnistudio_migration.py --manifest-dir force-app/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# LWC HTML: managed package OmniStudio component tags
MANAGED_TAG_PATTERNS = [
    re.compile(r"<c-omni-script\b", re.IGNORECASE),
    re.compile(r"<c-flex-card\b", re.IGNORECASE),
    re.compile(r"<c-omni-card\b", re.IGNORECASE),
    re.compile(r"<c-omni-out\b", re.IGNORECASE),
]

# Apex: Vlocity namespace service class calls
VLOCITY_NAMESPACE_PATTERN = re.compile(
    r"\bvlocity_(ins|cmt|ps)\s*\.", re.IGNORECASE
)

# Apex/SOQL: Vlocity custom object queries
VLOCITY_OBJECT_QUERY_PATTERN = re.compile(
    r"\bFROM\s+vlocity_(ins|cmt|ps)__\w+__c\b", re.IGNORECASE
)

# Apex: Vlocity custom object field references in DML or assignments
VLOCITY_FIELD_PATTERN = re.compile(
    r"\bvlocity_(ins|cmt|ps)__\w+__[cr]\b", re.IGNORECASE
)

# JavaScript: direct REST calls to Integration Procedure endpoints
IP_REST_PATTERN = re.compile(
    r"(fetch|XMLHttpRequest|axios)\s*[\(\.].*integrationprocedure", re.IGNORECASE
)

# package.xml: native OmniStudio metadata types that must be declared
NATIVE_OMNISTUDIO_TYPES = [
    "OmniScriptDefinition",
    "OmniIntegrationProcedure",
    "OmniDataTransform",
    "OmniUiCard",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_files(root: Path, suffix: str) -> list[Path]:
    """Recursively find all files with the given suffix under root."""
    return sorted(root.rglob(f"*{suffix}"))


def check_lwc_html(manifest_dir: Path) -> list[str]:
    """Check LWC HTML files for managed package OmniStudio component tags."""
    issues: list[str] = []
    html_files = find_files(manifest_dir, ".html")
    for path in html_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pattern in MANAGED_TAG_PATTERNS:
            matches = pattern.findall(content)
            if matches:
                tag = pattern.pattern.lstrip("<").rstrip(r"\b")
                # Find line numbers for context
                lines_with_issue = [
                    i + 1
                    for i, line in enumerate(content.splitlines())
                    if pattern.search(line)
                ]
                line_list = ", ".join(str(n) for n in lines_with_issue[:5])
                issues.append(
                    f"[LWC-MANAGED-TAG] {path}: uses managed package tag "
                    f"'{tag}' (found on line(s) {line_list}). "
                    f"Replace with the native omnistudio-* equivalent."
                )
    return issues


def check_apex_vlocity_refs(manifest_dir: Path) -> list[str]:
    """Check Apex classes for Vlocity namespace service class and object references."""
    issues: list[str] = []
    apex_files = find_files(manifest_dir, ".cls")
    for path in apex_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Check for namespace.ServiceClass calls
        ns_matches = [
            i + 1
            for i, line in enumerate(content.splitlines())
            if VLOCITY_NAMESPACE_PATTERN.search(line)
        ]
        if ns_matches:
            line_list = ", ".join(str(n) for n in ns_matches[:5])
            issues.append(
                f"[APEX-VLOCITY-NS] {path}: references Vlocity namespace "
                f"(vlocity_ins/cmt/ps) on line(s) {line_list}. "
                f"Update to omnistudio.* equivalent after migration."
            )

        # Check for SOQL querying Vlocity custom objects
        soql_matches = [
            i + 1
            for i, line in enumerate(content.splitlines())
            if VLOCITY_OBJECT_QUERY_PATTERN.search(line)
        ]
        if soql_matches:
            line_list = ", ".join(str(n) for n in soql_matches[:5])
            issues.append(
                f"[APEX-VLOCITY-SOQL] {path}: queries Vlocity custom objects "
                f"(vlocity_*__OmniScript__c etc.) on line(s) {line_list}. "
                f"Native OmniStudio components are metadata, not sObject records. "
                f"Remove or replace these queries."
            )

    return issues


def check_js_direct_ip_calls(manifest_dir: Path) -> list[str]:
    """Check JS files for direct REST calls to Integration Procedure endpoints."""
    issues: list[str] = []
    js_files = find_files(manifest_dir, ".js")
    for path in js_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = [
            i + 1
            for i, line in enumerate(content.splitlines())
            if IP_REST_PATTERN.search(line)
        ]
        if matches:
            line_list = ", ".join(str(n) for n in matches[:5])
            issues.append(
                f"[JS-DIRECT-IP-CALL] {path}: possible direct REST call to "
                f"Integration Procedure endpoint on line(s) {line_list}. "
                f"Use an @AuraEnabled Apex intermediary to preserve sharing enforcement."
            )
    return issues


def check_package_xml(manifest_dir: Path) -> list[str]:
    """Check package.xml files for native OmniStudio metadata type declarations."""
    issues: list[str] = []
    package_files = list(manifest_dir.rglob("package.xml"))
    if not package_files:
        return issues  # No package.xml found; not a blocking issue

    for path in package_files:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        missing_types = [
            t for t in NATIVE_OMNISTUDIO_TYPES if t not in content
        ]
        if missing_types:
            issues.append(
                f"[PACKAGE-XML-MISSING-TYPES] {path}: missing native OmniStudio "
                f"metadata type(s): {', '.join(missing_types)}. "
                f"Add these types to ensure native OmniStudio components are "
                f"retrieved and deployed correctly."
            )
    return issues


def check_vlocity_to_native_omnistudio_migration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_lwc_html(manifest_dir))
    issues.extend(check_apex_vlocity_refs(manifest_dir))
    issues.extend(check_js_direct_ip_calls(manifest_dir))
    issues.extend(check_package_xml(manifest_dir))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce SFDX project metadata for Vlocity managed package "
            "namespace references that must be updated when migrating to native OmniStudio."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce SFDX project or metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_vlocity_to_native_omnistudio_migration(manifest_dir)

    if not issues:
        print("No Vlocity namespace issues found. Metadata appears ready for native OmniStudio.")
        return 0

    print(f"Found {len(issues)} issue(s):\n")
    for issue in issues:
        print(f"ISSUE: {issue}\n")

    return 1


if __name__ == "__main__":
    sys.exit(main())
