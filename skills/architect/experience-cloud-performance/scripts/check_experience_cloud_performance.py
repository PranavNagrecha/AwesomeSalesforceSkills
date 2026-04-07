#!/usr/bin/env python3
"""Checker script for Experience Cloud Performance skill.

Checks Salesforce metadata in a retrieved project directory for common
Experience Cloud performance anti-patterns.

Checks performed:
  1. Detects Apex controller methods used as @wire targets that lack
     cacheable=true, which prevents LWR wire service caching.
  2. Warns when a single LWC component's JS file contains more than 3
     distinct @wire decorator imports — a signal of non-consolidated data access.
  3. Detects static resource references that do not include version tokens in
     their HTML/component markup — a signal of un-versioned cache-busting.
  4. Verifies that Experience Site metadata files are present (basic structural check).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_performance.py [--manifest-dir PATH]
    python3 check_experience_cloud_performance.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Experience Cloud performance anti-patterns in Salesforce metadata. "
            "Looks for non-cacheable Apex wire targets, high wire-call density per component, "
            "and un-versioned static resource references."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_apex_wire_cacheable(manifest_dir: Path) -> list[str]:
    """Warn on @AuraEnabled Apex methods without cacheable=true that are
    commonly used as @wire targets (read-only methods: get*, find*, fetch*, query*).

    A non-cacheable wire target bypasses the LWR wire service cache and forces
    a server round-trip on every component mount.
    """
    issues: list[str] = []
    # Pattern: @AuraEnabled without (cacheable=true) on the same or next line
    # followed by a method name that looks like a read method
    aura_enabled_pattern = re.compile(
        r"@AuraEnabled(?!\s*\(\s*cacheable\s*=\s*true\s*\))\s*\n?\s*"
        r"public\s+(?:static\s+)?(?:\w+\s+)*(get\w+|find\w+|fetch\w+|query\w+|load\w+)\s*\(",
        re.MULTILINE,
    )

    apex_classes = list(manifest_dir.rglob("*.cls"))
    for cls_file in apex_classes:
        try:
            content = cls_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = aura_enabled_pattern.findall(content)
        if matches:
            issues.append(
                f"Apex class '{cls_file.name}' contains @AuraEnabled read method(s) without "
                f"cacheable=true — these cannot benefit from LWR wire service caching: "
                f"{matches[:3]}"
            )

    return issues


def check_wire_call_density(manifest_dir: Path, threshold: int = 3) -> list[str]:
    """Warn when a single LWC JS file has more than `threshold` distinct @wire
    decorator usages. High wire density on one page component is a signal that
    Apex calls have not been consolidated.
    """
    issues: list[str] = []
    wire_pattern = re.compile(r"@wire\s*\(", re.MULTILINE)

    lwc_js_files = list(manifest_dir.rglob("*.js"))
    for js_file in lwc_js_files:
        # Skip test files
        if "__tests__" in str(js_file) or ".test." in js_file.name:
            continue
        try:
            content = js_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        wire_count = len(wire_pattern.findall(content))
        if wire_count > threshold:
            issues.append(
                f"LWC component '{js_file.parent.name}/{js_file.name}' has {wire_count} @wire "
                f"calls (threshold: {threshold}). Consider consolidating Apex calls into a single "
                f"data provider to reduce server round-trips on page load."
            )

    return issues


def check_static_resource_versioning(manifest_dir: Path) -> list[str]:
    """Warn when static resources are referenced without version tokens in
    HTML templates or component markup. Un-versioned static resource URLs
    cannot be cache-busted and may serve stale content for up to 1 day.
    """
    issues: list[str] = []
    # Look for staticresource references without a ? query string (version token)
    # Common pattern: /resource/MyResource/path without ?vX or version key
    static_ref_pattern = re.compile(
        r'["\'](?:/resource/\d+/\w+/[^"\'?]+)["\']',
        re.MULTILINE,
    )
    # Also flag bare import-based staticResource references in JS that
    # reference a top-level resource without a path or version marker
    import_pattern = re.compile(
        r"import\s+\w+\s+from\s+['\"]@salesforce/staticResource/(\w+)['\"]",
        re.MULTILINE,
    )

    html_files = list(manifest_dir.rglob("*.html"))
    js_files = list(manifest_dir.rglob("*.js"))

    for html_file in html_files:
        try:
            content = html_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = static_ref_pattern.findall(content)
        if matches:
            issues.append(
                f"Template '{html_file.name}' references static resource URL(s) without version "
                f"token: {matches[:3]}. These URLs will be cached for up to 1 day after updates."
            )

    for js_file in js_files:
        if "__tests__" in str(js_file):
            continue
        try:
            content = js_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = import_pattern.findall(content)
        if matches:
            # This is informational, not necessarily wrong — just noting that
            # the developer should verify update strategy for these resources.
            issues.append(
                f"Component '{js_file.parent.name}/{js_file.name}' imports static resource(s) "
                f"'{', '.join(matches[:3])}'. Confirm these resources use version-keyed URLs or "
                f"have a cache-invalidation strategy for updates (1-day CDN TTL applies)."
            )

    return issues


def check_experience_site_metadata_present(manifest_dir: Path) -> list[str]:
    """Basic structural check: warn if no ExperienceBundle or Network metadata
    is found in the project — this may indicate the checker is running against
    a non-Experience-Cloud project.
    """
    issues: list[str] = []

    has_experience_bundle = any(manifest_dir.rglob("*.site"))
    has_network_meta = any(manifest_dir.rglob("*.network"))
    has_experience_folder = any(
        d for d in manifest_dir.rglob("*")
        if d.is_dir() and d.name == "experiences"
    )

    if not (has_experience_bundle or has_network_meta or has_experience_folder):
        issues.append(
            "No Experience Cloud metadata found (no .site, .network, or experiences/ directory). "
            "Confirm --manifest-dir points to a Salesforce project containing Experience Cloud metadata."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_experience_cloud_performance(manifest_dir: Path) -> list[str]:
    """Run all checks and return a combined list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_experience_site_metadata_present(manifest_dir))
    issues.extend(check_apex_wire_cacheable(manifest_dir))
    issues.extend(check_wire_call_density(manifest_dir))
    issues.extend(check_static_resource_versioning(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_performance(manifest_dir)

    if not issues:
        print("No Experience Cloud performance issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
