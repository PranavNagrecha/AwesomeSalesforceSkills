#!/usr/bin/env python3
"""Checker script for API-Led Connectivity Architecture skill.

Scans Apex source files and Named Credential metadata for common API-led
connectivity anti-patterns documented in this skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_api_led_connectivity_architecture.py --apex-dir path/to/force-app/main/default
    python3 check_api_led_connectivity_architecture.py --apex-dir . --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Detects Apex HTTP callout that references a Process or System API URL pattern
# (URLs containing "process-" or "system-" in the endpoint path or named credential name)
PROCESS_OR_SYSTEM_API_CALLOUT = re.compile(
    r"setEndpoint\s*\(\s*['\"]([^'\"]*(?:process-|system-)[^'\"]*)['\"]",
    re.IGNORECASE,
)

# Detects Named Credential references for process/system APIs in Apex callout code
NAMED_CRED_PROCESS_SYSTEM = re.compile(
    r"callout:([A-Za-z0-9_]*(?:process|system)[A-Za-z0-9_]*)/",
    re.IGNORECASE,
)

# Detects Apex HTTP callout without any Named Credential (hardcoded URL starting with http)
HARDCODED_URL_CALLOUT = re.compile(
    r"setEndpoint\s*\(\s*['\"]https?://",
    re.IGNORECASE,
)

# Detects valid Named Credential pattern (callout:xxx)
NAMED_CRED_REF = re.compile(
    r"setEndpoint\s*\(\s*['\"]callout:",
    re.IGNORECASE,
)

# Detects Agentforce-related class patterns calling process/system URLs
AGENTFORCE_CLASS = re.compile(
    r"@InvocableMethod|implements\s+Invocable|AgentAction",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# File-level checkers
# ---------------------------------------------------------------------------

def check_apex_file(path: Path, verbose: bool) -> list[str]:
    """Run all checks against a single Apex file. Returns list of issue strings."""
    issues: list[str] = []
    content = path.read_text(encoding="utf-8", errors="replace")
    name = path.name

    is_agentforce_related = bool(AGENTFORCE_CLASS.search(content))

    # Anti-pattern: Hardcoded URL in callout (no Named Credential)
    if HARDCODED_URL_CALLOUT.search(content) and not NAMED_CRED_REF.search(content):
        issues.append(
            f"{name}: HTTP callout with hardcoded URL (https://) found — "
            "callouts should use Named Credentials (callout:NamedCredentialName/path). "
            "Hardcoded URLs bypass centralized credential management and make "
            "environment migration (sandbox → production) error-prone. "
            "[anti-pattern: hardcoded callout URL]"
        )

    # Anti-pattern: Agentforce invocable method calling Process or System API directly
    if is_agentforce_related:
        process_system_match = PROCESS_OR_SYSTEM_API_CALLOUT.search(content)
        named_cred_ps_match = NAMED_CRED_PROCESS_SYSTEM.search(content)
        if process_system_match or named_cred_ps_match:
            matched = (process_system_match or named_cred_ps_match).group(0)
            issues.append(
                f"{name}: Agentforce-related class (@InvocableMethod or AgentAction) appears to call "
                f"a Process or System API directly ({matched[:80]}) — "
                "Agentforce agents must route through Experience APIs via Agent Fabric, "
                "not call Process or System APIs directly. "
                "Direct calls bypass rate limiting, audit logging, and security isolation. "
                "[anti-pattern: agent bypassing Experience API layer]"
            )

    if verbose and not issues:
        print(f"  OK  {name}")

    return issues


def check_named_credential_metadata(path: Path, verbose: bool) -> list[str]:
    """Check a Named Credential XML metadata file for shared credential anti-patterns."""
    issues: list[str] = []
    name = path.name

    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # Strip namespace if present
        label_el = root.find(".//{*}label") or root.find("label")
        label = label_el.text if label_el is not None else name
    except ET.ParseError:
        # Not valid XML — skip
        return issues

    # Warn on Named Credentials with "shared" in label — common signal of shared credentials
    if re.search(r"shared", label or "", re.IGNORECASE):
        issues.append(
            f"{name}: Named Credential label contains 'shared' ({label}) — "
            "shared credentials across multiple consumers (CRM, mobile, Agentforce agents) "
            "prevent per-consumer rate limiting, make audit logs ambiguous, "
            "and make independent revocation impossible. "
            "Use dedicated Named Credentials per consumer type. "
            "[anti-pattern: shared OAuth credentials]"
        )

    if verbose and not issues:
        print(f"  OK  {name}")

    return issues


# ---------------------------------------------------------------------------
# Directory walker
# ---------------------------------------------------------------------------

def scan_directory(apex_dir: Path, verbose: bool) -> list[str]:
    """Walk apex_dir and check .cls, .trigger, and .namedCredential files."""
    all_issues: list[str] = []

    apex_files = list(apex_dir.rglob("*.cls")) + list(apex_dir.rglob("*.trigger"))
    named_cred_files = list(apex_dir.rglob("*.namedCredential"))

    total = len(apex_files) + len(named_cred_files)
    if total == 0:
        print(f"No Apex or Named Credential files found under: {apex_dir}", file=sys.stderr)
        return all_issues

    if verbose:
        print(
            f"Scanning {len(apex_files)} Apex file(s) and "
            f"{len(named_cred_files)} Named Credential file(s) under {apex_dir} ..."
        )

    for apex_file in sorted(apex_files):
        all_issues.extend(check_apex_file(apex_file, verbose))

    for nc_file in sorted(named_cred_files):
        all_issues.extend(check_named_credential_metadata(nc_file, verbose))

    return all_issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex metadata and Named Credentials for API-led connectivity "
            "anti-patterns: hardcoded callout URLs, Agentforce agents bypassing "
            "Experience API layer, and shared Named Credentials across consumers."
        ),
    )
    parser.add_argument(
        "--apex-dir",
        default=".",
        help="Root directory containing Apex and metadata files (default: current directory).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print OK lines for files that pass all checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    apex_dir = Path(args.apex_dir)

    if not apex_dir.exists():
        print(f"ERROR: Directory not found: {apex_dir}", file=sys.stderr)
        return 2

    issues = scan_directory(apex_dir, verbose=args.verbose)

    if not issues:
        print("No API-led connectivity architecture issues found.")
        return 0

    print(f"\n{len(issues)} issue(s) found:\n", file=sys.stderr)
    for issue in issues:
        print(f"WARN: {issue}\n", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
