#!/usr/bin/env python3
"""Checker script for Health Cloud APIs skill.

Checks org metadata for common Health Cloud API usage issues:
- Connected App OAuth scope configuration
- FHIR bundle size in Apex/integration code
- HTTP 424 error handling patterns

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_apis.py [--help]
    python3 check_health_cloud_apis.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Health Cloud API configuration and code for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_connected_app_healthcare_scope(manifest_dir: Path) -> list[str]:
    """Check Connected Apps for `healthcare` OAuth scope."""
    issues: list[str] = []
    connected_apps_dir = manifest_dir / "connectedApps"
    if not connected_apps_dir.exists():
        return issues

    for app_file in connected_apps_dir.glob("*.connectedApp-meta.xml"):
        content = app_file.read_text(encoding="utf-8")
        if "healthcare" in content.lower() or "fhir" in content.lower():
            if "<oauthScope>healthcare</oauthScope>" not in content:
                issues.append(
                    f"{app_file.name}: Connected App appears to be used for Health Cloud/FHIR "
                    "but does not include the 'healthcare' OAuth scope. "
                    "FHIR Healthcare API calls require the 'healthcare' scope."
                )
    return issues


def check_apex_fhir_bundle_sizes(manifest_dir: Path) -> list[str]:
    """Check Apex classes for FHIR bundle size patterns."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8")
        if "healthcare/fhir" not in content.lower() and "fhir" not in content.lower():
            continue
        # Look for common large batch size numbers
        for large_size in ["200", "500", "1000", "2000"]:
            if large_size in content and "batch" in content.lower():
                issues.append(
                    f"{cls_file.name}: Class references FHIR operations and batch size {large_size}. "
                    "FHIR Healthcare API bundles are limited to 30 entries maximum. "
                    "Verify bundle chunking is implemented correctly."
                )
                break
    return issues


def check_apex_404_error_handling(manifest_dir: Path) -> list[str]:
    """Check Apex classes for HTTP 424 error handling in FHIR contexts."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8")
        if ("healthcare/fhir" in content.lower() or "fhir" in content.lower()) and "statusCode" in content:
            if "424" not in content:
                issues.append(
                    f"{cls_file.name}: Class uses FHIR API and handles status codes "
                    "but does not appear to handle HTTP 424 (Failed Dependency). "
                    "FHIR bundle failures cascade via 424 for dependent entries. "
                    "Implement 424 detection and root cause tracing."
                )
    return issues


def check_health_cloud_apis(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_connected_app_healthcare_scope(manifest_dir))
    issues.extend(check_apex_fhir_bundle_sizes(manifest_dir))
    issues.extend(check_apex_404_error_handling(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_health_cloud_apis(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
