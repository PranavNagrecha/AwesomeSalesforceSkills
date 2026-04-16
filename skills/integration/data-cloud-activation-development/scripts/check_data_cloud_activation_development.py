#!/usr/bin/env python3
"""Checker script for Data Cloud Activation Development skill.

Checks org metadata or configuration relevant to Data Cloud Activation Development.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_activation_development.py [--help]
    python3 check_data_cloud_activation_development.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Data Cloud Activation Development configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_data_cloud_activation_development(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Python/JS files for webhook receivers that skip HMAC verification
    code_files = list(manifest_dir.rglob("*.py")) + list(manifest_dir.rglob("*.js"))
    for code_file in code_files:
        try:
            text = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect webhook handler without HMAC verification
        has_webhook_handler = any(kw in text for kw in ["X-SFDC-Signature", "webhook", "data_action"])
        has_hmac = "hmac" in text.lower() or "HMAC" in text
        if has_webhook_handler and not has_hmac:
            issues.append(
                f"{code_file}: Webhook handler detected but no HMAC verification found — "
                "Data Cloud webhook targets require HMAC-SHA256 verification of X-SFDC-Signature header."
            )
        # Detect assumption of Data Cloud event retry
        if "retry" not in text.lower() and "dead_letter" not in text.lower() and has_webhook_handler:
            issues.append(
                f"{code_file}: Webhook handler with no retry or dead-letter handling — "
                "Data Cloud Data Action Targets do not auto-retry. Implement external dead-letter queue."
            )

    # Check Flow metadata for record-triggered flows trying to watch Data Cloud objects
    flow_files = list(manifest_dir.rglob("*.flow-meta.xml"))
    for flow_file in flow_files:
        try:
            text = flow_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Detect flows with DataCloud or Unified in trigger object name — likely wrong trigger type
        if "RecordTriggerType" in text and "DataCloud" in text:
            issues.append(
                f"{flow_file}: Record-triggered Flow appears to target a Data Cloud object — "
                "Use Data Cloud-Triggered Flows in Data Cloud Setup, not record-triggered Flows."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_data_cloud_activation_development(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
