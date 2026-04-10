#!/usr/bin/env python3
"""Checker script for FSL Custom Actions Mobile skill.

Scans LWC source and metadata for common FSL Mobile custom action anti-patterns:
- Nimbus plugin calls without isAvailable() guard
- navigator.geolocation usage in LWC JS files
- lightning__GlobalAction targets without FSL Mobile notes
- Missing endCapture() in catch blocks

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_custom_actions_mobile.py [--help]
    python3 check_fsl_custom_actions_mobile.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_NIMBUS_IMPORT_RE = re.compile(
    r'import\s*\{[^}]*get(BarcodeScanner|LocationService|CameraCapture)[^}]*\}\s*from\s*[\'"]lightning/mobileCapabilities[\'"]',
    re.IGNORECASE,
)
_IS_AVAILABLE_RE = re.compile(r'\.isAvailable\(\)', re.IGNORECASE)
_BEGIN_CAPTURE_RE = re.compile(r'\.beginCapture\(', re.IGNORECASE)
_END_CAPTURE_RE = re.compile(r'\.endCapture\(', re.IGNORECASE)
_NAVIGATOR_GEO_RE = re.compile(r'navigator\.geolocation', re.IGNORECASE)
_GLOBAL_ACTION_RE = re.compile(r'lightning__GlobalAction', re.IGNORECASE)


def check_fsl_custom_actions_mobile(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    js_files = list(manifest_dir.rglob("*.js"))
    xml_files = list(manifest_dir.rglob("*.js-meta.xml"))

    for js_file in js_files:
        if "__tests__" in str(js_file):
            continue
        try:
            source = js_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        rel = js_file.relative_to(manifest_dir)

        # Check 1: Nimbus plugin imported but no isAvailable() guard
        if _NIMBUS_IMPORT_RE.search(source):
            if not _IS_AVAILABLE_RE.search(source):
                issues.append(
                    f"{rel}: Nimbus plugin imported from lightning/mobileCapabilities but "
                    "no isAvailable() check found. Nimbus plugins return null outside FSL Mobile. "
                    "Add: if (plugin == null || !plugin.isAvailable()) {{ return; }}"
                )

        # Check 2: beginCapture without endCapture in catch path (heuristic)
        if _BEGIN_CAPTURE_RE.search(source):
            if not _END_CAPTURE_RE.search(source):
                issues.append(
                    f"{rel}: beginCapture() found but endCapture() not found. "
                    "endCapture() must be called in both .then() and .catch() handlers "
                    "to release the scanner session."
                )

        # Check 3: navigator.geolocation usage
        if _NAVIGATOR_GEO_RE.search(source):
            issues.append(
                f"{rel}: navigator.geolocation detected. "
                "Use getLocationService() from lightning/mobileCapabilities instead. "
                "navigator.geolocation is not available in the FSL Mobile LWC runtime."
            )

    for xml_file in xml_files:
        try:
            source = xml_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = xml_file.relative_to(manifest_dir)
        # Check 4: GlobalAction without note (informational)
        if _GLOBAL_ACTION_RE.search(source):
            issues.append(
                f"{rel}: lightning__GlobalAction target detected. "
                "Verify this component is configured in FSL Mobile App Manager, not a standard Lightning app. "
                "lightning__GlobalAction renders only in FSL Mobile, not in Lightning Experience or standard Salesforce Mobile."
            )

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC source for FSL Custom Actions Mobile anti-patterns.",
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
    issues = check_fsl_custom_actions_mobile(manifest_dir)

    if not issues:
        print("No FSL Custom Actions Mobile issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
