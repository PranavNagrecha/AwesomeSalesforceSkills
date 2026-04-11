#!/usr/bin/env python3
"""Checker script for AML/KYC Process Architecture skill.

Validates a Salesforce metadata directory for common AML/KYC architecture issues:
- Named Credentials using Per-User auth (unsafe for batch screening)
- Hardcoded credential patterns in Apex files
- Record-triggered Flows with callout actions (sync callout in bulk-unsafe context)
- Missing PartyProfileRisk field references in screening-related Apex

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_aml_kyc_process_architecture.py [--help]
    python3 check_aml_kyc_process_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check AML/KYC process architecture metadata for common issues.",
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

def find_files(base: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under base."""
    return list(base.rglob(pattern))


def file_contains(path: Path, pattern: str) -> bool:
    """Return True if the file content matches the regex pattern."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return bool(re.search(pattern, text))
    except (OSError, PermissionError):
        return False


def find_pattern_in_files(paths: list[Path], pattern: str) -> list[tuple[Path, int, str]]:
    """Return (file, line_number, line) tuples for each line matching the pattern."""
    results = []
    compiled = re.compile(pattern, re.IGNORECASE)
    for path in paths:
        try:
            for lineno, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1
            ):
                if compiled.search(line):
                    results.append((path, lineno, line.strip()))
        except (OSError, PermissionError):
            continue
    return results


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_named_credentials_per_user_auth(manifest_dir: Path) -> list[str]:
    """Flag Named Credentials using Per-User auth — unsafe for batch/scheduled screening."""
    issues: list[str] = []
    nc_files = find_files(manifest_dir, "*.namedCredential")
    for nc_file in nc_files:
        try:
            content = nc_file.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            continue
        # Per-User principal type in Named Credential XML
        if re.search(r"<principalType>NamedUser</principalType>", content, re.IGNORECASE):
            issues.append(
                f"NAMED_CREDENTIAL_PER_USER: {nc_file.name} uses NamedUser (Per-User) auth. "
                "Batch and scheduled Apex screening jobs require Named Principal auth — "
                "Per-User credentials fail in async/batch context."
            )
    return issues


def check_hardcoded_credentials_in_apex(manifest_dir: Path) -> list[str]:
    """Flag Apex files with patterns suggesting hardcoded API keys or passwords."""
    issues: list[str] = []
    apex_files = find_files(manifest_dir, "*.cls")
    # Patterns that suggest hardcoded secrets
    secret_patterns = [
        (r"(?i)(apiKey|api_key|apikey)\s*=\s*['\"][A-Za-z0-9+/=_\-]{16,}['\"]", "API key"),
        (r"(?i)(password|passwd|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]", "credential/secret"),
        (r"(?i)Authorization\s*:\s*['\"]Bearer\s+[A-Za-z0-9\._\-]{20,}['\"]", "hardcoded Bearer token"),
    ]
    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            continue
        for pattern, label in secret_patterns:
            matches = list(re.finditer(pattern, content))
            if matches:
                issues.append(
                    f"HARDCODED_SECRET ({label}): {apex_file.name} — potential hardcoded "
                    f"credential found. Use Named Credentials with External Credential policies. "
                    f"({len(matches)} match(es) found)"
                )
                break  # one warning per file is enough
    return issues


def check_flow_callout_on_record_trigger(manifest_dir: Path) -> list[str]:
    """Flag Flow metadata files that appear to be record-triggered and contain callout actions."""
    issues: list[str] = []
    flow_files = find_files(manifest_dir, "*.flow")
    for flow_file in flow_files:
        try:
            content = flow_file.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            continue
        is_record_triggered = bool(
            re.search(r"<processType>AutoLaunchedFlow</processType>", content)
            and re.search(r"<triggerType>(RecordAfterSave|RecordBeforeSave)</triggerType>", content)
        )
        has_callout = bool(
            re.search(
                r"<actionType>(externalService|integrationProcedure|apex)</actionType>",
                content,
            )
        )
        if is_record_triggered and has_callout:
            issues.append(
                f"FLOW_SYNC_CALLOUT_RISK: {flow_file.name} is a record-triggered Flow "
                "that invokes an external action. Synchronous callouts in record-triggered "
                "Flows fail in bulk DML context. Refactor to publish a Platform Event and "
                "process the callout asynchronously."
            )
    return issues


def check_batch_apex_allows_callouts(manifest_dir: Path) -> list[str]:
    """Warn if batch Apex classes make callouts but do not implement Database.AllowsCallouts."""
    issues: list[str] = []
    apex_files = find_files(manifest_dir, "*.cls")
    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            continue
        is_batchable = bool(re.search(r"implements\s+Database\.Batchable", content, re.IGNORECASE))
        has_callout = bool(re.search(r"Http\s*\(|HttpRequest\s*\(|callout\s*=\s*true", content, re.IGNORECASE))
        implements_allows_callouts = bool(
            re.search(r"Database\.AllowsCallouts", content, re.IGNORECASE)
        )
        if is_batchable and has_callout and not implements_allows_callouts:
            issues.append(
                f"BATCH_MISSING_ALLOWS_CALLOUTS: {apex_file.name} implements Database.Batchable "
                "and appears to make HTTP callouts but does not implement Database.AllowsCallouts. "
                "Batch classes making callouts must implement Database.AllowsCallouts."
            )
    return issues


def check_party_profile_risk_references(manifest_dir: Path) -> list[str]:
    """Warn if no Apex file references PartyProfileRisk — suggests screening results may not be stored."""
    apex_files = find_files(manifest_dir, "*.cls")
    if not apex_files:
        return []  # No Apex to check
    has_party_profile_risk = any(
        file_contains(f, r"PartyProfileRisk") for f in apex_files
    )
    if not has_party_profile_risk:
        return [
            "MISSING_PARTY_PROFILE_RISK: No Apex class references PartyProfileRisk. "
            "AML/KYC screening results should be stored on PartyProfileRisk "
            "(RiskCategory, RiskScore, RiskReason, RiskReviewDate). "
            "If results are stored elsewhere, verify this is intentional."
        ]
    return []


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_aml_kyc_process_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_named_credentials_per_user_auth(manifest_dir))
    issues.extend(check_hardcoded_credentials_in_apex(manifest_dir))
    issues.extend(check_flow_callout_on_record_trigger(manifest_dir))
    issues.extend(check_batch_apex_allows_callouts(manifest_dir))
    issues.extend(check_party_profile_risk_references(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_aml_kyc_process_architecture(manifest_dir)

    if not issues:
        print("No AML/KYC architecture issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
