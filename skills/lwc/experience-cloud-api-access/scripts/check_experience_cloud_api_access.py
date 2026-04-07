#!/usr/bin/env python3
"""Checker script for Experience Cloud API Access skill.

Scans Salesforce metadata for common API access anti-patterns involving
Experience Cloud guest users and external users.

Checks performed:
  - Apex classes without an explicit sharing declaration that are callable by guest/external users
  - Connected Apps with overly broad OAuth scopes (full, admin) in the metadata
  - Profile XML for guest/community profiles missing "API Enabled" when it may be required

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_experience_cloud_api_access.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SHARING_DECL_RE = re.compile(
    r"\b(with sharing|without sharing|inherited sharing)\b",
    re.IGNORECASE,
)
_AURA_ENABLED_RE = re.compile(r"@AuraEnabled", re.IGNORECASE)
_REMOTE_ACTION_RE = re.compile(r"@RemoteAction", re.IGNORECASE)

_BROAD_SCOPES = {"full", "admin", "web", "visualforce"}
_SCOPE_TAG_RE = re.compile(r"<oauthScopes>(.*?)</oauthScopes>", re.DOTALL)
_SCOPE_VALUE_RE = re.compile(r"<oauthScope>(.*?)</oauthScope>")

_PROFILE_NAME_PATTERNS = [
    re.compile(r"Guest User", re.IGNORECASE),
    re.compile(r"Customer Community", re.IGNORECASE),
    re.compile(r"Partner Community", re.IGNORECASE),
]
_API_ENABLED_TAG_RE = re.compile(
    r"<userPermissions>.*?<enabled>(true|false)</enabled>.*?<name>ApiEnabled</name>.*?</userPermissions>",
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_apex_sharing(manifest_dir: Path) -> list[str]:
    """Flag Apex classes with @AuraEnabled or @RemoteAction that lack an explicit sharing declaration."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.is_dir():
        return issues

    for cls_file in sorted(classes_dir.glob("*.cls")):
        content = cls_file.read_text(encoding="utf-8", errors="replace")
        has_aura = _AURA_ENABLED_RE.search(content) is not None
        has_remote = _REMOTE_ACTION_RE.search(content) is not None
        if not (has_aura or has_remote):
            continue
        has_sharing = _SHARING_DECL_RE.search(content) is not None
        without_sharing = re.search(r"\bwithout sharing\b", content, re.IGNORECASE) is not None
        if not has_sharing:
            issues.append(
                f"Apex class '{cls_file.name}' has @AuraEnabled/@RemoteAction but no sharing "
                f"declaration — defaults to system context, which is unsafe for guest-accessible endpoints. "
                f"Add 'with sharing'."
            )
        elif without_sharing:
            issues.append(
                f"Apex class '{cls_file.name}' has @AuraEnabled/@RemoteAction and is declared "
                f"'without sharing' — this bypasses guest profile FLS and external OWD enforcement. "
                f"Change to 'with sharing' for any class reachable by Experience Cloud guest or external users."
            )
    return issues


def check_connected_app_scopes(manifest_dir: Path) -> list[str]:
    """Flag Connected Apps that grant overly broad OAuth scopes."""
    issues: list[str] = []
    apps_dir = manifest_dir / "connectedApps"
    if not apps_dir.is_dir():
        return issues

    for app_file in sorted(apps_dir.glob("*.connectedApp")):
        content = app_file.read_text(encoding="utf-8", errors="replace")
        scopes_match = _SCOPE_TAG_RE.search(content)
        if not scopes_match:
            continue
        scopes_block = scopes_match.group(1)
        granted_scopes = {
            m.group(1).strip().lower()
            for m in _SCOPE_VALUE_RE.finditer(scopes_block)
        }
        bad_scopes = granted_scopes & _BROAD_SCOPES
        if bad_scopes:
            issues.append(
                f"Connected App '{app_file.stem}' grants overly broad OAuth scope(s): "
                f"{', '.join(sorted(bad_scopes))}. "
                f"External user integrations should use 'api' scope only. "
                f"Remove: {', '.join(sorted(bad_scopes))}."
            )
    return issues


def check_external_profile_api_enabled(manifest_dir: Path) -> list[str]:
    """Flag external/community profiles where ApiEnabled is explicitly set to false."""
    issues: list[str] = []
    profiles_dir = manifest_dir / "profiles"
    if not profiles_dir.is_dir():
        return issues

    for profile_file in sorted(profiles_dir.glob("*.profile")):
        name = profile_file.stem
        is_external = any(p.search(name) for p in _PROFILE_NAME_PATTERNS)
        if not is_external:
            continue
        content = profile_file.read_text(encoding="utf-8", errors="replace")
        for match in _API_ENABLED_TAG_RE.finditer(content):
            enabled_val = match.group(1).strip().lower()
            if enabled_val == "false":
                issues.append(
                    f"Profile '{name}' has ApiEnabled=false. "
                    f"Customer Community Plus and Partner Community users require ApiEnabled=true "
                    f"on their profile to call the Salesforce REST/SOAP API. "
                    f"(Ignore this if the profile is for Customer Community — that license has no API entitlement.)"
                )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Experience Cloud API access anti-patterns: "
            "Apex sharing declarations, Connected App OAuth scopes, and external profile API access."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_experience_cloud_api_access(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_sharing(manifest_dir))
    issues.extend(check_connected_app_scopes(manifest_dir))
    issues.extend(check_external_profile_api_enabled(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_experience_cloud_api_access(manifest_dir)

    if not issues:
        print("No Experience Cloud API access issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
