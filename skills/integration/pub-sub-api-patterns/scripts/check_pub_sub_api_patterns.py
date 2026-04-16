#!/usr/bin/env python3
"""Checker script for Pub Sub Api Patterns skill.

Checks org metadata or configuration relevant to Pub Sub Api Patterns.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_pub_sub_api_patterns.py [--help]
    python3 check_pub_sub_api_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Pub Sub Api Patterns configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_pub_sub_api_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    TODO: Implement real checks relevant to this skill.
    Each returned string should describe a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Python code for CometD/EMP Connector usage (legacy pattern)
    code_files = list(manifest_dir.rglob("*.py")) + list(manifest_dir.rglob("*.java"))
    for code_file in code_files:
        try:
            text = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "cometd" in text.lower() or "emp_connector" in text.lower() or "EmpConnector" in text:
            issues.append(
                f"{code_file}: Uses CometD/EMP Connector — "
                "For new integrations, use Pub/Sub API gRPC (pub-sub-api-patterns skill). "
                "CometD is legacy."
            )
        # Check for missing replay ID persistence
        if "FetchRequest" in text or "Subscribe" in text:
            if "replay_id" not in text.lower() and "replayId" not in text and "replayid" not in text.lower():
                issues.append(
                    f"{code_file}: Pub/Sub API subscriber detected but no replay ID persistence found — "
                    "Persist replayId after each batch to enable resume on reconnect."
                )
        # Check for 15-character org ID usage (should be 18)
        if "tenantid" in text.lower() or "tenant_id" in text.lower():
            import re
            # Look for short string assignments near tenantid
            short_id_pattern = re.findall(r'tenantid["\s]*[:=]["\s]*([A-Za-z0-9]{15})["\s]', text)
            if short_id_pattern:
                issues.append(
                    f"{code_file}: tenantid may use 15-character Org ID — "
                    "Pub/Sub API requires 18-character Org ID. "
                    "Use SOQL 'SELECT Id FROM Organization' to get 18-char format."
                )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_pub_sub_api_patterns(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
