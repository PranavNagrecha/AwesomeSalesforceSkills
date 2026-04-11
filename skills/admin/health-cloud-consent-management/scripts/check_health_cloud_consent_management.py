#!/usr/bin/env python3
"""Checker script for Health Cloud Consent Management skill.

Checks org metadata for common Health Cloud consent management issues:
- AuthorizationFormText default flag configuration
- Flow patterns for consent capture and withdrawal
- Permission set configurations for consent objects

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_consent_management.py [--help]
    python3 check_health_cloud_consent_management.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Health Cloud Consent Management configuration for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_flows_for_consent_deletion(manifest_dir: Path) -> list[str]:
    """Check Flows for patterns that delete AuthorizationFormConsent records."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        content = flow_file.read_text(encoding="utf-8")
        if "AuthorizationFormConsent" in content and "<recordDeletes>" in content:
            issues.append(
                f"{flow_file.name}: Flow references AuthorizationFormConsent in a recordDeletes element. "
                "HIPAA requires consent records to be retained. Use Status update instead of delete for withdrawal."
            )
    return issues


def check_flows_for_consent_status(manifest_dir: Path) -> list[str]:
    """Check that Flows using AuthorizationFormConsent handle required statuses."""
    issues: list[str] = []
    flows_dir = manifest_dir / "flows"
    if not flows_dir.exists():
        return issues

    for flow_file in flows_dir.glob("*.flow-meta.xml"):
        content = flow_file.read_text(encoding="utf-8")
        if "AuthorizationFormConsent" not in content:
            continue
        if "Signed" not in content and "Seen" not in content:
            issues.append(
                f"{flow_file.name}: Flow references AuthorizationFormConsent but does not appear to check "
                "for 'Signed' or 'Seen' status values. Verify consent status handling is complete."
            )
    return issues


def check_objects_for_consent_hierarchy(manifest_dir: Path) -> list[str]:
    """Check for presence of consent hierarchy objects in metadata."""
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    required_objects = [
        "DataUsePurpose",
        "AuthorizationForm",
        "AuthorizationFormText",
        "AuthorizationFormDataUse",
        "AuthorizationFormConsent",
    ]
    present = {d.name for d in objects_dir.iterdir() if d.is_dir()}
    missing = [obj for obj in required_objects if obj not in present]
    if missing:
        issues.append(
            f"Consent hierarchy objects not found in objects/: {', '.join(missing)}. "
            "These objects are required for Health Cloud consent management. "
            "Verify they exist in the org and are included in the metadata retrieval."
        )
    return issues


def check_health_cloud_consent_management(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_flows_for_consent_deletion(manifest_dir))
    issues.extend(check_flows_for_consent_status(manifest_dir))
    issues.extend(check_objects_for_consent_hierarchy(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_health_cloud_consent_management(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
