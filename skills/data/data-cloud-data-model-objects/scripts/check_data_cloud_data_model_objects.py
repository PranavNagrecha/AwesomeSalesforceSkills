#!/usr/bin/env python3
"""Checker script for Data Cloud Data Model Objects skill.

Validates DMO design documents and code for common Data Cloud DMO issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_data_model_objects.py --manifest-dir <path>

Exit codes:
    0 — no issues found
    1 — one or more issues found
"""

import argparse
import re
import sys
from pathlib import Path


MANDATORY_IDENTITY_DMOS = [
    "Individual",
    "Party Identification",
    "Contact Point Email",
    "Contact Point Phone",
    "Contact Point Address",
]

MANDATORY_IDENTITY_PATTERNS = [re.compile(re.escape(dmo), re.IGNORECASE) for dmo in MANDATORY_IDENTITY_DMOS]


def check_soql_against_dmo(path: Path) -> list[str]:
    """Warn if SOQL queries appear to target DMO objects (ssot__ prefix)."""
    issues = []
    soql_pattern = re.compile(r"SELECT\s+.+\s+FROM\s+ssot__\w+__dlm", re.IGNORECASE)
    for apex_file in list(path.glob("**/*.cls")) + list(path.glob("**/*.trigger")):
        try:
            content = apex_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if soql_pattern.search(content):
            issues.append(
                f"ERROR: {apex_file.name} appears to use SOQL against a Data Cloud DMO object "
                f"(ssot__ prefix with __dlm suffix). DMOs do not support SOQL. "
                f"Use the Data Cloud Query API with ANSI SQL: POST /ssot/queryapis/queryjobs."
            )
    return issues


def check_system_xmd_patch(path: Path) -> list[str]:
    """Warn if code attempts to PATCH System XMD."""
    issues = []
    system_xmd_pattern = re.compile(r"xmds/system", re.IGNORECASE)
    patch_pattern = re.compile(r"(PATCH|patch)", re.IGNORECASE)

    for code_file in list(path.glob("**/*.py")) + list(path.glob("**/*.cls")) + list(path.glob("**/*.js")):
        try:
            content = code_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if system_xmd_pattern.search(content) and patch_pattern.search(content):
            issues.append(
                f"WARN: {code_file.name} appears to PATCH System XMD (/xmds/system). "
                f"System XMD is immutable — this will return HTTP 403. "
                f"Target Main XMD instead: PATCH .../wave/datasets/{{id}}/xmds/main."
            )
    return issues


def check_mandatory_dmo_coverage(path: Path) -> list[str]:
    """Check design documents for coverage of mandatory identity DMOs."""
    issues = []
    plan_files = list(path.glob("**/*.md")) + list(path.glob("**/*.txt"))

    for plan_file in plan_files:
        try:
            content = plan_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        # Only check files that seem to describe DMO mapping
        if "DMO" not in content and "Data Model Object" not in content:
            continue
        missing_dmos = [dmo for dmo, pattern in zip(MANDATORY_IDENTITY_DMOS, MANDATORY_IDENTITY_PATTERNS)
                        if not pattern.search(content)]
        if missing_dmos:
            issues.append(
                f"WARN: {plan_file.name} describes DMO design but does not mention these mandatory "
                f"identity resolution DMOs: {missing_dmos}. "
                f"All five mandatory DMOs must be mapped for identity resolution to function."
            )
    return issues


def check_streaming_transform_joins(path: Path) -> list[str]:
    """Warn if a streaming transform plan references multiple source DLOs."""
    issues = []
    for plan_file in list(path.glob("**/*.md")) + list(path.glob("**/*.txt")):
        try:
            content = plan_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "streaming transform" in content.lower() or "streaming_transform" in content.lower():
            if re.search(r"join|JOIN", content):
                issues.append(
                    f"WARN: {plan_file.name} describes a streaming transform with a join operation. "
                    f"Streaming transforms support only a single source DLO and cannot perform joins. "
                    f"Use a batch transform for cross-DLO joins."
                )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Data Cloud DMO design documents and code."
    )
    parser.add_argument("--manifest-dir", type=Path, default=Path("."),
                        help="Directory to scan for Apex, Python, JS, and plan files")
    args = parser.parse_args()

    all_issues: list[str] = []

    if args.manifest_dir.exists():
        all_issues.extend(check_soql_against_dmo(args.manifest_dir))
        all_issues.extend(check_system_xmd_patch(args.manifest_dir))
        all_issues.extend(check_mandatory_dmo_coverage(args.manifest_dir))
        all_issues.extend(check_streaming_transform_joins(args.manifest_dir))
    else:
        all_issues.append(f"ERROR: Directory not found: {args.manifest_dir}")

    if all_issues:
        for issue in all_issues:
            print(issue)
        return 1

    print("OK: No Data Cloud DMO issues detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
