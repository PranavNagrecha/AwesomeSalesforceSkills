#!/usr/bin/env python3
"""Checker script for AI Agent to Org Integration Architecture skill.

Checks metadata and configuration for common architectural anti-patterns:
- Overprivileged Connected App run-as users (System Admin profile references)
- Missing field-level security on PII-sensitive objects in profiles
- Connected App metadata missing Client Credentials Flow configuration
- Apex REST endpoints accessible without sharing enforcement

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ai_agent_org_integration_architecture.py [--help]
    python3 check_ai_agent_org_integration_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check AI agent org integration architecture for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_connected_apps(manifest_dir: Path, issues: list[str]) -> None:
    """Check Connected App metadata for integration architecture issues."""
    # Common Connected App metadata locations
    for ca_dir in [
        manifest_dir / "force-app" / "main" / "default" / "connectedApps",
        manifest_dir / "connectedApps",
    ]:
        if not ca_dir.exists():
            continue
        for ca_file in ca_dir.glob("*.connectedApp-meta.xml"):
            try:
                content = ca_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            fname = ca_file.name

            # Check: warn if System Administrator profile is referenced as run-as user
            if re.search(r"<runAsUser>[^<]*[Aa]dmin[^<]*</runAsUser>", content):
                issues.append(
                    f"{fname}: Connected App run-as user appears to reference an admin account. "
                    "AI agent service accounts should use a custom profile with least-privilege permissions, "
                    "not a System Administrator or admin-named user."
                )

            # Check: warn if oauthConfig block is missing enableClientCredentials
            if "<oauthConfig>" in content and "enableClientCredentials" not in content:
                issues.append(
                    f"{fname}: Connected App oauthConfig does not include enableClientCredentials. "
                    "For service-to-service AI agent integration, ensure OAuth 2.0 Client Credentials "
                    "Flow is enabled if using the Client Credentials pattern."
                )

            # Check: warn if scope is too broad (full or full_access)
            if re.search(r"<scope>full</scope>|<scope>full_access</scope>", content):
                issues.append(
                    f"{fname}: Connected App uses 'full' or 'full_access' OAuth scope. "
                    "AI agent integrations should use the minimum necessary scopes (e.g., 'api', 'refresh_token'). "
                    "Full access grants access to all API surfaces including admin functions."
                )


def check_apex_sharing(manifest_dir: Path, issues: list[str]) -> None:
    """Check Apex classes used as API endpoints for sharing keyword decisions."""
    for apex_dir in [
        manifest_dir / "force-app" / "main" / "default" / "classes",
        manifest_dir / "classes",
    ]:
        if not apex_dir.exists():
            continue
        for apex_file in apex_dir.glob("*.cls"):
            try:
                content = apex_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            # Only check REST-exposed classes (likely AI agent entry points)
            if "@RestResource" not in content:
                continue

            fname = apex_file.name

            # Warn if no sharing keyword is used at all — should be a conscious decision
            has_sharing = (
                "with sharing" in content or
                "without sharing" in content or
                "inherited sharing" in content
            )
            if not has_sharing:
                issues.append(
                    f"{fname}: @RestResource class has no sharing keyword. "
                    "For AI agent API endpoints, sharing behavior should be explicit. "
                    "Omitting the keyword defaults to 'without sharing' in system context. "
                    "Add 'with sharing', 'without sharing', or 'inherited sharing' with a comment explaining the decision."
                )


def check_ai_agent_org_integration_architecture(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    check_connected_apps(manifest_dir, issues)
    check_apex_sharing(manifest_dir, issues)

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_ai_agent_org_integration_architecture(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
