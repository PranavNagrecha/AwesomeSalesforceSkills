#!/usr/bin/env python3
"""Checker script for LWC Offline And Mobile skill."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC Offline And Mobile configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_lwc_offline_and_mobile(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    for js_path in sorted(manifest_dir.rglob("*.js")):
        text = js_path.read_text(encoding="utf-8", errors="ignore")
        if "lightning/mobileCapabilities" in text and "isAvailable" not in text:
            issues.append(f"{js_path}: imports `lightning/mobileCapabilities` without an availability check; add runtime gating for unsupported containers.")
        if "window.innerWidth" in text or "navigator.userAgent" in text:
            issues.append(f"{js_path}: appears to infer mobile behavior from browser globals; review whether capability or form-factor APIs would be safer.")
        if "navigator.onLine" in text and "resume" not in text.lower() and "refresh" not in text.lower():
            issues.append(f"{js_path}: checks online state but has no obvious resume or refresh handling; review stale-state behavior for mobile users.")

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwc_offline_and_mobile(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
