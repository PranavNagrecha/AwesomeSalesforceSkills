#!/usr/bin/env python3
"""Checker script for Real-Time vs Batch Integration skill.

Analyzes Salesforce metadata in a local sfdx/metadata directory and flags
patterns that conflict with the guidance in the real-time-vs-batch-integration skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_real_time_vs_batch_integration.py [--help]
    python3 check_real_time_vs_batch_integration.py --manifest-dir path/to/metadata
    python3 check_real_time_vs_batch_integration.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for real-time vs batch integration anti-patterns. "
            "Detects callout-per-record triggers, missing Named Credentials, and bulk "
            "API configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, *patterns: str) -> list[Path]:
    """Return all files under root matching any of the given glob patterns."""
    found: list[Path] = []
    for pattern in patterns:
        found.extend(root.rglob(pattern))
    return found


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_callout_in_trigger_loop(manifest_dir: Path) -> list[str]:
    """Detect Apex triggers that call @future or callout methods inside a for-loop.

    A trigger iterating Trigger.new and calling an external-facing method per record
    will hit the 100 callouts/transaction limit at bulk volume.
    """
    issues: list[str] = []
    trigger_files = _find_files(manifest_dir, "*.trigger")

    for tf in trigger_files:
        content = _read_text(tf)
        lines = content.splitlines()

        inside_for = False
        for i, line in enumerate(lines, start=1):
            stripped = line.strip().lower()

            # Rough heuristic: entering a for-loop over Trigger.new/Trigger.old
            if "for (" in stripped and ("trigger.new" in stripped or "trigger.old" in stripped):
                inside_for = True
            if inside_for and "{" in stripped:
                inside_for = True
            if inside_for and stripped == "}":
                inside_for = False

            if inside_for:
                # Look for @future-style method calls, Http.send, or common callout patterns
                if any(kw in stripped for kw in ("httprequest", "http.send", "callout", "@future")):
                    issues.append(
                        f"{tf.name}:{i} — possible callout inside Trigger.new loop. "
                        "At bulk volume this will hit the 100 callouts/transaction limit. "
                        "Publish a Platform Event instead and process asynchronously."
                    )
                    break  # one issue per file is enough

    return issues


def check_hardcoded_endpoints(manifest_dir: Path) -> list[str]:
    """Detect Apex files with hardcoded HTTP endpoint strings instead of Named Credentials.

    Named Credentials are required for all outbound callouts per security guidance.
    """
    issues: list[str] = []
    apex_files = _find_files(manifest_dir, "*.cls", "*.trigger")

    for af in apex_files:
        content = _read_text(af)
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Look for string literals that look like HTTP endpoints not using callout://
            if (
                "http://" in stripped.lower() or
                ("https://" in stripped.lower() and "callout://" not in stripped.lower())
            ):
                # Exclude comments and common false positives (test assertions, doc strings)
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    issues.append(
                        f"{af.name}:{i} — hardcoded HTTP endpoint detected. "
                        "Use a Named Credential (callout://MyCredential) instead of "
                        "embedding URLs in Apex. This applies to both real-time callouts "
                        "and any HTTP-based batch integration."
                    )
                    break  # one issue per file

    return issues


def check_platform_event_publish_behavior(manifest_dir: Path) -> list[str]:
    """Check Platform Event metadata for PUBLISH_IMMEDIATELY publish behavior.

    PUBLISH_IMMEDIATELY (the default) means events fire even when the publishing
    transaction rolls back. Flag any event definitions that do not explicitly
    set PHASE_AFTER_COMMIT when they are used in transactional flows.
    """
    issues: list[str] = []
    event_files = _find_files(manifest_dir, "*.event")

    for ef in event_files:
        content = _read_text(ef)
        # If publishBehavior is not set to PHASE_AFTER_COMMIT, flag for review
        if "PHASE_AFTER_COMMIT" not in content:
            # Only flag if the file looks like a real Platform Event metadata file
            if "<PlatformEventChannel>" in content or "<fullName>" in content:
                issues.append(
                    f"{ef.name} — Platform Event definition does not specify "
                    "publishBehavior=PHASE_AFTER_COMMIT. The default PUBLISH_IMMEDIATELY "
                    "means events are NOT rolled back when the publishing transaction fails. "
                    "Review whether this is intentional for this event type."
                )

    return issues


def check_bulk_api_external_id(manifest_dir: Path) -> list[str]:
    """Check custom object metadata for presence of an External ID field.

    Objects used in Bulk API 2.0 upsert jobs require an External ID field to ensure
    idempotent operations and safe retries.
    """
    issues: list[str] = []
    field_files = _find_files(manifest_dir, "*.field-meta.xml")

    objects_with_external_id: set[str] = set()
    for ff in field_files:
        content = _read_text(ff)
        if "<externalId>true</externalId>" in content:
            # Extract parent object name from path (e.g., objects/Account/fields/Ext_Id__c.field-meta.xml)
            parent = ff.parent.parent.name
            objects_with_external_id.add(parent)

    # Check if any triggers reference Bulk API patterns without a known external ID on the object
    # This is a soft hint — a trigger referencing an object that has no external ID field is a risk
    trigger_files = _find_files(manifest_dir, "*.trigger")
    for tf in trigger_files:
        content = _read_text(tf)
        # Look for upsert statements without an external ID reference
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            stripped = line.strip().lower()
            if "database.upsert" in stripped or stripped.startswith("upsert "):
                # Check if the object type used in the upsert has any external ID field
                # Simple heuristic: if the trigger file name matches a known object
                obj_name = tf.stem  # e.g., "AccountTrigger" → check Account
                obj_candidate = obj_name.replace("Trigger", "").replace("trigger", "")
                if obj_candidate and obj_candidate not in objects_with_external_id:
                    issues.append(
                        f"{tf.name}:{i} — upsert statement found but no External ID field "
                        f"detected on '{obj_candidate}'. Bulk API 2.0 upsert jobs require "
                        "an External ID field for idempotent retries. Add one if this object "
                        "is used in bulk ingest jobs."
                    )
                    break

    return issues


def check_named_credential_usage(manifest_dir: Path) -> list[str]:
    """Verify that Named Credential metadata exists if callout Apex is present.

    If Apex callout code exists but no Named Credential metadata is found,
    endpoints may be hardcoded or managed outside source control.
    """
    issues: list[str] = []

    apex_files = _find_files(manifest_dir, "*.cls", "*.trigger")
    has_callouts = any(
        "callout://" in _read_text(f).lower() or
        "httprequest" in _read_text(f).lower()
        for f in apex_files
    )

    if not has_callouts:
        return issues  # no callout code found, nothing to check

    named_credential_files = _find_files(manifest_dir, "*.namedCredential", "*.namedCredential-meta.xml")
    if not named_credential_files:
        issues.append(
            "Apex callout code detected but no Named Credential metadata found in this directory. "
            "Ensure all outbound callout endpoints are defined as Named Credentials in source control. "
            "Hardcoded endpoints violate the security requirements for real-time integrations."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_real_time_vs_batch_integration(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_callout_in_trigger_loop(manifest_dir))
    issues.extend(check_hardcoded_endpoints(manifest_dir))
    issues.extend(check_platform_event_publish_behavior(manifest_dir))
    issues.extend(check_bulk_api_external_id(manifest_dir))
    issues.extend(check_named_credential_usage(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_real_time_vs_batch_integration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
