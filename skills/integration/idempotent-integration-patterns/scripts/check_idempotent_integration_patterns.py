#!/usr/bin/env python3
"""Checker script for Idempotent Integration Patterns skill.

Checks Apex code for common idempotency anti-patterns (e.g., Publish Immediately in triggers).
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_idempotent_integration_patterns.py [--help]
    python3 check_idempotent_integration_patterns.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex code for idempotency anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_apex_for_idempotency_issues(manifest_dir: Path) -> list[str]:
    """Check Apex trigger files for Platform Event Publish Immediately anti-patterns."""
    issues: list[str] = []

    apex_dir = manifest_dir / "classes"
    trigger_dir = manifest_dir / "triggers"

    apex_files = list(apex_dir.glob("*.cls")) if apex_dir.exists() else []
    trigger_files = list(trigger_dir.glob("*.trigger")) if trigger_dir.exists() else []
    all_files = apex_files + trigger_files

    # Pattern to find EventBus.publish() calls without PublishAfterCommit
    publish_pattern = re.compile(r"EventBus\.publish\(", re.IGNORECASE)
    # Pattern to check if Publish After Commit is configured
    after_commit_pattern = re.compile(
        r"PublishAfterCommit|PublishBehavior|AFTER_COMMIT", re.IGNORECASE
    )

    # Pattern for REST API POST calls that should be PATCH
    post_pattern = re.compile(r"HttpRequest\s*req\s*=.*?req\.setMethod\(['\"]POST['\"]\)", re.DOTALL)

    for apex_file in all_files:
        try:
            content = apex_file.read_text(encoding="utf-8")
            file_name = apex_file.stem

            # Check for EventBus.publish() without Publish After Commit nearby
            if publish_pattern.search(content) and not after_commit_pattern.search(content):
                # Only flag if this appears to be in a trigger context
                if apex_file.suffix == ".trigger" or "trigger" in file_name.lower():
                    issues.append(
                        f"Trigger/class '{file_name}': "
                        "Found EventBus.publish() without PublishAfterCommit setting. "
                        "Platform Events published from DML triggers should use "
                        "Publish After Commit to avoid delivering events for rolled-back transactions."
                    )

        except OSError:
            pass

    return issues


def check_idempotent_integration_patterns(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_for_idempotency_issues(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_idempotent_integration_patterns(manifest_dir)

    if not issues:
        print("No idempotency pattern issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
