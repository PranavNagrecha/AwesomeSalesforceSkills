#!/usr/bin/env python3
"""Checker script for sandbox-refresh-and-templates skill.

Scans a Salesforce metadata directory for common issues related to sandbox
refresh, SandboxPostCopy implementation, and hardcoded org IDs.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sandbox_refresh.py [--manifest-dir path/to/metadata]
    python3 check_sandbox_refresh.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# 15- or 18-character Salesforce ID that looks like an org/record ID.
# Org IDs start with '00D'. We look for bare '00D' IDs in source files.
ORG_ID_PATTERN = re.compile(r'\b00D[A-Za-z0-9]{12,15}\b')

# SandboxPostCopy interface reference — should appear in at least one class
SANDBOX_POST_COPY_INTERFACE = re.compile(
    r'implements\s+(?:System\.)?SandboxPostCopy', re.IGNORECASE
)

# runApexClass method — required by the interface
RUN_APEX_CLASS_METHOD = re.compile(
    r'void\s+runApexClass\s*\(', re.IGNORECASE
)

# CronTrigger abort — should appear in any SandboxPostCopy implementation
ABORT_JOB_CALL = re.compile(r'System\.abortJob\s*\(', re.IGNORECASE)

# Hardcoded endpoint URL patterns that should not appear in SandboxPostCopy
PRODUCTION_URL_PATTERN = re.compile(
    r'https://[a-zA-Z0-9\-]+\.my\.salesforce\.com', re.IGNORECASE
)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def find_apex_files(root: Path) -> list[Path]:
    """Return all .cls files under root."""
    return list(root.rglob('*.cls'))


def check_hardcoded_org_ids(apex_files: list[Path]) -> list[str]:
    """Flag Apex files that contain hardcoded org IDs (00Dxxxxxxxxx)."""
    issues: list[str] = []
    for path in apex_files:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        matches = ORG_ID_PATTERN.findall(text)
        if matches:
            issues.append(
                f"Hardcoded org ID(s) {matches} found in {path}. "
                "Org IDs change on every sandbox refresh — store the ID in a "
                "custom setting updated by SandboxPostCopy."
            )
    return issues


def check_sandboxpostcopy_exists(apex_files: list[Path]) -> list[str]:
    """Verify at least one class implements SandboxPostCopy."""
    issues: list[str] = []
    implementing_files: list[Path] = []

    for path in apex_files:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        if SANDBOX_POST_COPY_INTERFACE.search(text):
            implementing_files.append(path)

    if not implementing_files:
        issues.append(
            "No Apex class implementing SandboxPostCopy found in the manifest. "
            "Without a SandboxPostCopy class, all post-refresh configuration "
            "(org settings, scheduled job cleanup, data scrubbing) is manual."
        )
    return issues


def check_sandboxpostcopy_aborts_jobs(apex_files: list[Path]) -> list[str]:
    """Verify SandboxPostCopy implementations call System.abortJob."""
    issues: list[str] = []
    for path in apex_files:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        if not SANDBOX_POST_COPY_INTERFACE.search(text):
            continue
        if not ABORT_JOB_CALL.search(text):
            issues.append(
                f"{path}: SandboxPostCopy class does not call System.abortJob(). "
                "Scheduled jobs are copied from production in WAITING state and "
                "will fire in the sandbox unless explicitly aborted."
            )
    return issues


def check_sandboxpostcopy_has_run_method(apex_files: list[Path]) -> list[str]:
    """Verify SandboxPostCopy class includes runApexClass method."""
    issues: list[str] = []
    for path in apex_files:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        if not SANDBOX_POST_COPY_INTERFACE.search(text):
            continue
        if not RUN_APEX_CLASS_METHOD.search(text):
            issues.append(
                f"{path}: Class declares implements SandboxPostCopy but "
                "runApexClass(SandboxContext) method not found. "
                "The interface requires this method signature."
            )
    return issues


def check_hardcoded_production_urls(apex_files: list[Path]) -> list[str]:
    """Flag SandboxPostCopy classes that hardcode production .my.salesforce.com URLs."""
    issues: list[str] = []
    for path in apex_files:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        if not SANDBOX_POST_COPY_INTERFACE.search(text):
            continue
        url_matches = PRODUCTION_URL_PATTERN.findall(text)
        if url_matches:
            issues.append(
                f"{path}: SandboxPostCopy class contains hardcoded Salesforce URL(s) "
                f"{url_matches}. Endpoint URLs change between production and sandbox — "
                "use a custom setting or SandboxContext.sandboxName() to resolve the URL."
            )
    return issues


def check_sandbox_template_metadata(root: Path) -> list[str]:
    """Look for any sandbox definition XML that references a template."""
    issues: list[str] = []
    sandbox_files = list(root.rglob('*.sandbox'))
    if not sandbox_files:
        # Not necessarily a problem — sandbox definitions may not be in the repo
        return issues

    for path in sandbox_files:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        if '<sandboxType>PARTIAL</sandboxType>' in text or \
                '<type>PARTIAL</type>' in text.lower():
            if '<templateId>' not in text and '<sandboxOptionsId>' not in text:
                issues.append(
                    f"{path}: Partial Copy sandbox definition found without a "
                    "template reference. Without a template, records are copied "
                    "randomly and test data is non-deterministic across refreshes."
                )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_all_checks(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_apex_files(manifest_dir)

    issues.extend(check_hardcoded_org_ids(apex_files))
    issues.extend(check_sandboxpostcopy_exists(apex_files))
    issues.extend(check_sandboxpostcopy_has_run_method(apex_files))
    issues.extend(check_sandboxpostcopy_aborts_jobs(apex_files))
    issues.extend(check_hardcoded_production_urls(apex_files))
    issues.extend(check_sandbox_template_metadata(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common sandbox-refresh issues: "
            "hardcoded org IDs, missing SandboxPostCopy class, unaborted scheduled "
            "jobs, and Partial Copy sandboxes without templates."
        )
    )
    parser.add_argument(
        '--manifest-dir',
        default='.',
        help='Root directory of the Salesforce metadata (default: current directory).',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = run_all_checks(manifest_dir)

    if not issues:
        print('No sandbox refresh issues found.')
        return 0

    for issue in issues:
        print(f'ISSUE: {issue}')

    return 1


if __name__ == '__main__':
    sys.exit(main())
