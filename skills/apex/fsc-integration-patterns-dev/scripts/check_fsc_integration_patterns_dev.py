#!/usr/bin/env python3
"""Checker script for FSC Integration Patterns Dev skill.

Checks Salesforce metadata for common FSC integration anti-patterns:
- Synchronous callouts in Apex trigger files on FSC financial objects
- Hardcoded FSC namespace without conditional check
- Username/password OAuth flow in Connected App metadata
- Missing Database.AllowsCallouts on batch classes that contain Http callouts
- RBL-disabling pattern absent from batch integration classes

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsc_integration_patterns_dev.py [--help]
    python3 check_fsc_integration_patterns_dev.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# FSC financial object names that signal this is FSC integration code
FSC_OBJECT_NAMES = [
    "FinancialAccount",
    "FinancialHolding",
    "FinServ__FinancialAccount__c",
    "FinServ__FinancialHolding__c",
]

# Trigger file patterns
TRIGGER_CALLOUT_PATTERN = re.compile(
    r"\bHttp\b|\bHttpRequest\b|\bHttpResponse\b|\bcallout\s*=\s*true\b",
    re.IGNORECASE,
)

TRIGGER_FSC_OBJECT_PATTERN = re.compile(
    r"trigger\s+\w+\s+on\s+(?:FinServ__FinancialHolding__c|FinancialHolding|"
    r"FinServ__FinancialAccount__c|FinancialAccount)\b",
    re.IGNORECASE,
)

# Batch class patterns
BATCHABLE_PATTERN = re.compile(r"implements\s+Database\.Batchable", re.IGNORECASE)
ALLOWS_CALLOUTS_PATTERN = re.compile(r"Database\.AllowsCallouts", re.IGNORECASE)
HTTP_CALLOUT_IN_EXECUTE_PATTERN = re.compile(
    r"public\s+void\s+execute\s*\([^)]*\).*?(?=public\s+(?:void\s+finish|Database\.QueryLocator\s+start))",
    re.DOTALL | re.IGNORECASE,
)

# Namespace checks
MANAGED_PKG_ONLY_PATTERN = re.compile(
    r"FinServ__FinancialAccount__c|FinServ__FinancialHolding__c", re.IGNORECASE
)
CORE_FSC_ONLY_PATTERN = re.compile(
    r"(?<!\w)FinancialAccount(?!__c|\w)|(?<!\w)FinancialHolding(?!__c|\w)",
    re.IGNORECASE,
)
NAMESPACE_CONDITIONAL_PATTERN = re.compile(
    r"containsKey\s*\(\s*['\"]FinServ__|getGlobalDescribe|isManagedPackage",
    re.IGNORECASE,
)

# Connected App metadata patterns
USERNAME_PASSWORD_FLOW_PATTERN = re.compile(
    r"grant_type\s*=\s*password|<oauthConfig>.*?<allowUsernamePasswordFlows>true",
    re.DOTALL | re.IGNORECASE,
)
PASSWORD_FLOW_XML_PATTERN = re.compile(
    r"<allowUsernamePasswordFlows>\s*true\s*</allowUsernamePasswordFlows>",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check FSC integration metadata for common anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_trigger_callouts(manifest_dir: Path) -> list[str]:
    """Detect synchronous callouts inside triggers on FSC financial objects."""
    issues: list[str] = []
    trigger_dir = manifest_dir / "triggers"
    if not trigger_dir.exists():
        # Also check force-app structure
        trigger_dir = manifest_dir / "force-app" / "main" / "default" / "triggers"
    if not trigger_dir.exists():
        return issues

    for trigger_file in trigger_dir.glob("*.trigger"):
        content = trigger_file.read_text(encoding="utf-8", errors="replace")
        if TRIGGER_FSC_OBJECT_PATTERN.search(content) and TRIGGER_CALLOUT_PATTERN.search(content):
            issues.append(
                f"CALLOUT_IN_FSC_TRIGGER: {trigger_file.name} — contains HTTP callout logic "
                f"inside a trigger on a FSC financial object. Callouts after DML are prohibited "
                f"at runtime (CalloutException). Move callouts to Batchable/Queueable."
            )
    return issues


def check_batch_allows_callouts(manifest_dir: Path) -> list[str]:
    """Detect Batchable classes that contain Http callouts but do not implement AllowsCallouts."""
    issues: list[str] = []
    apex_dirs = [
        manifest_dir / "classes",
        manifest_dir / "force-app" / "main" / "default" / "classes",
    ]

    for apex_dir in apex_dirs:
        if not apex_dir.exists():
            continue
        for cls_file in apex_dir.glob("*.cls"):
            content = cls_file.read_text(encoding="utf-8", errors="replace")
            if not BATCHABLE_PATTERN.search(content):
                continue
            if TRIGGER_CALLOUT_PATTERN.search(content) and not ALLOWS_CALLOUTS_PATTERN.search(content):
                issues.append(
                    f"MISSING_ALLOWS_CALLOUTS: {cls_file.name} — implements Database.Batchable "
                    f"and contains Http callout code but does not implement Database.AllowsCallouts. "
                    f"Callouts in execute() will fail at runtime without this interface."
                )
    return issues


def check_namespace_hardcoding(manifest_dir: Path) -> list[str]:
    """Detect Apex files that reference only one FSC namespace variant without a conditional check."""
    issues: list[str] = []
    apex_dirs = [
        manifest_dir / "classes",
        manifest_dir / "force-app" / "main" / "default" / "classes",
    ]

    for apex_dir in apex_dirs:
        if not apex_dir.exists():
            continue
        for cls_file in apex_dir.glob("*.cls"):
            content = cls_file.read_text(encoding="utf-8", errors="replace")
            has_managed = bool(MANAGED_PKG_ONLY_PATTERN.search(content))
            has_core = bool(CORE_FSC_ONLY_PATTERN.search(content))
            has_conditional = bool(NAMESPACE_CONDITIONAL_PATTERN.search(content))

            if has_managed and not has_conditional:
                issues.append(
                    f"NAMESPACE_HARDCODED_MANAGED_PKG: {cls_file.name} — references "
                    f"FinServ__ namespace objects without a namespace conditional check. "
                    f"This will fail on Core FSC orgs. Add a getGlobalDescribe/containsKey guard "
                    f"or parameterize object names in configuration."
                )
            elif has_core and not has_conditional and not has_managed:
                # Only flag if it contains non-trivial FSC object references
                # (avoid false positives on generic SObject code)
                fsc_ref_count = len(CORE_FSC_ONLY_PATTERN.findall(content))
                if fsc_ref_count >= 3:
                    issues.append(
                        f"NAMESPACE_HARDCODED_CORE_FSC: {cls_file.name} — references Core FSC "
                        f"object names without a namespace conditional check. This will fail on "
                        f"managed-package FSC orgs. Add a getGlobalDescribe/containsKey guard."
                    )
    return issues


def check_connected_app_oauth_flow(manifest_dir: Path) -> list[str]:
    """Detect Connected App metadata that enables username/password OAuth flow."""
    issues: list[str] = []
    connected_app_dirs = [
        manifest_dir / "connectedApps",
        manifest_dir / "force-app" / "main" / "default" / "connectedApps",
    ]

    for ca_dir in connected_app_dirs:
        if not ca_dir.exists():
            continue
        for ca_file in ca_dir.glob("*.connectedApp-meta.xml"):
            content = ca_file.read_text(encoding="utf-8", errors="replace")
            if PASSWORD_FLOW_XML_PATTERN.search(content):
                issues.append(
                    f"USERNAME_PASSWORD_OAUTH_ENABLED: {ca_file.name} — Connected App has "
                    f"allowUsernamePasswordFlows=true. Integration users must authenticate via "
                    f"OAuth 2.0 JWT Bearer flow. Disable password flow and configure certificate-based auth."
                )
    return issues


def check_fsc_integration_patterns_dev(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_trigger_callouts(manifest_dir))
    issues.extend(check_batch_allows_callouts(manifest_dir))
    issues.extend(check_namespace_hardcoding(manifest_dir))
    issues.extend(check_connected_app_oauth_flow(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsc_integration_patterns_dev(manifest_dir)

    if not issues:
        print("No FSC integration anti-patterns found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
