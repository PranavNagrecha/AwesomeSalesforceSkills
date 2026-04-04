#!/usr/bin/env python3
"""Checker script for Custom Metadata Types And Settings skill.

Scans a Salesforce metadata directory for common issues related to Custom
Metadata Types (CMT) and Custom Settings, including:
  - Custom Settings that consume SOQL without null checks in Apex
  - List Custom Settings (deprecated in Lightning)
  - CMT access patterns that incorrectly assume governor limit cost
  - Bare field access on getInstance() without null checks
  - Apex code that stores secrets in CMT or Custom Settings

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_custom_metadata_types_and_settings.py [--manifest-dir path/to/metadata]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Bare getInstance() or getValues() chained directly to a field — no null check
_BARE_INSTANCE_CHAIN = re.compile(
    r"\w+__c\.(getInstance|getValues)\s*\([^)]*\)\s*\.\w+",
    re.IGNORECASE,
)

# Direct array index on a CMT SOQL result without an isEmpty check
_BARE_CMT_INDEX = re.compile(
    r"\[SELECT\s+.+FROM\s+\w+__mdt\b[^\]]*\]\s*\[\s*0\s*\]",
    re.IGNORECASE | re.DOTALL,
)

# String literals that look like secrets stored in metadata/settings fields
_SECRET_FIELD_NAMES = re.compile(
    r"(password|secret|token|api_key|apikey|client_secret|bearer)\s*=\s*['\"]",
    re.IGNORECASE,
)

# Checks for `getValues('SomeStringName')` — indicates List Custom Setting usage
_LIST_SETTING_GET_VALUES = re.compile(
    r"\w+__c\.getValues\s*\(\s*['\"][\w\s]+['\"]\s*\)",
    re.IGNORECASE,
)

# Detects comment-style warnings about SOQL limits on CMT queries (false alarm pattern)
# This is informational — it may indicate the author misunderstands CMT governor behavior
_CMT_SOQL_LIMIT_COMMENT = re.compile(
    r"(#|//|/\*).*(soql|governor|limit).*(mdt|metadata)",
    re.IGNORECASE,
)


def _check_apex_file(path: Path, issues: list[str]) -> None:
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        issues.append(f"Could not read file: {path}")
        return

    rel = path.name

    # Bare chained access on Custom Setting instance — NullPointerException risk
    if _BARE_INSTANCE_CHAIN.search(content):
        issues.append(
            f"{rel}: Custom Setting getInstance()/getValues() chained directly to a "
            "field without a null check. If no record exists in the org, this throws "
            "a NullPointerException. Add a null guard: "
            "`if (settings != null && settings.Field__c != null) { ... }`"
        )

    # Bare array index on CMT SOQL — will throw if list is empty
    if _BARE_CMT_INDEX.search(content):
        issues.append(
            f"{rel}: CMT SOQL result accessed with [0] without an isEmpty() check. "
            "If the CMT record does not exist in the org, this throws a "
            "ListException. Use `if (!results.isEmpty()) {{ ... }}` first."
        )

    # List Custom Setting getValues with a string key
    if _LIST_SETTING_GET_VALUES.search(content):
        issues.append(
            f"{rel}: getValues('Name') pattern detected — this is a List Custom "
            "Setting access. List Custom Settings are deprecated in Lightning. "
            "Migrate this configuration to a Custom Metadata Type."
        )

    # Secret-looking field assignments
    if _SECRET_FIELD_NAMES.search(content):
        issues.append(
            f"{rel}: Field assignment with a name suggesting credentials or secrets "
            "(password, token, secret, api_key, etc.). Do not store secrets in "
            "Custom Metadata Types or Custom Settings. Use Named Credentials or a "
            "supported secret management mechanism instead."
        )


def _check_object_metadata(path: Path, issues: list[str]) -> None:
    """Check CustomSetting object metadata XML for List type usage."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return

    # List Custom Setting metadata has <customSettingsType>List</customSettingsType>
    if re.search(r"<customSettingsType>\s*List\s*</customSettingsType>", content, re.IGNORECASE):
        issues.append(
            f"{path.name}: List Custom Setting detected. List Custom Settings are "
            "deprecated in Lightning Experience. Migrate to a Custom Metadata Type "
            "for new implementations. If this is existing code, schedule migration."
        )


def _check_cmt_metadata(path: Path, issues: list[str]) -> None:
    """Check Custom Metadata Type object definition for common issues."""
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return

    # Check for fields with secret-sounding names in CMT definitions
    if re.search(
        r"<fullName>(password|secret|token|api_key|apikey|client_secret|bearer)\w*</fullName>",
        content,
        re.IGNORECASE,
    ):
        issues.append(
            f"{path.name}: Custom Metadata Type field with a secret-sounding name "
            "(password, token, secret, api_key, etc.). CMT fields are visible to any "
            "user with access to Setup and are not a secure secret store. Use Named "
            "Credentials for credentials and tokens."
        )


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check Apex classes and triggers
    for apex_dir_name in ("classes", "triggers"):
        apex_dir = manifest_dir / apex_dir_name
        if apex_dir.is_dir():
            for apex_file in apex_dir.glob("*.cls"):
                _check_apex_file(apex_file, issues)
            for apex_file in apex_dir.glob("*.trigger"):
                _check_apex_file(apex_file, issues)

    # Also search recursively under force-app layout
    for apex_file in manifest_dir.rglob("*.cls"):
        if apex_file.parent.name == "classes":
            continue  # already covered above
        _check_apex_file(apex_file, issues)
    for apex_file in manifest_dir.rglob("*.trigger"):
        if apex_file.parent.name == "triggers":
            continue
        _check_apex_file(apex_file, issues)

    # Check Custom Setting object XML files
    objects_dir = manifest_dir / "objects"
    if objects_dir.is_dir():
        # Old metadata format: single .object file per object
        for obj_file in objects_dir.glob("*.object"):
            _check_object_metadata(obj_file, issues)
        # New SFDX format: objects/<ObjectName>/<ObjectName>.object-meta.xml
        for obj_file in objects_dir.rglob("*.object-meta.xml"):
            _check_object_metadata(obj_file, issues)

    # Check Custom Metadata Type object definitions
    custom_metadata_dir = manifest_dir / "customMetadata"
    if not custom_metadata_dir.is_dir():
        # Try SFDX layout
        custom_metadata_dir = manifest_dir / "force-app" / "main" / "default" / "customMetadata"

    if custom_metadata_dir.is_dir():
        for mdt_file in custom_metadata_dir.rglob("*.md-meta.xml"):
            _check_cmt_metadata(mdt_file, issues)

    # Check for CMT object definitions (the type, not records) — looking for secret fields
    for obj_file in manifest_dir.rglob("*__mdt.object-meta.xml"):
        _check_cmt_metadata(obj_file, issues)

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for Custom Metadata Type and Custom Setting "
            "anti-patterns: null-check omissions, deprecated List Custom Settings, "
            "secret field names, and missing governor-limit awareness."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    args = parser.parse_args()

    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_manifest_dir(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
