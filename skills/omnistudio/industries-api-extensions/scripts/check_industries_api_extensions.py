#!/usr/bin/env python3
"""Checker script for Industries API Extensions skill.

Scans Salesforce metadata and source files for common anti-patterns related to
Industries-specific API extensions: direct DML on InsurancePolicy/ServicePoint,
hardcoded MuleSoft gateway URLs for Communications Cloud, and missing ID-resolution
before TM Forum API calls.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_industries_api_extensions.py [--help]
    python3 check_industries_api_extensions.py --manifest-dir path/to/metadata
    python3 check_industries_api_extensions.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns that indicate direct DML or REST CRUD on industry-specific objects
# ---------------------------------------------------------------------------

# Apex DML anti-patterns: insert/update/delete on InsurancePolicy or ServicePoint
APEX_DIRECT_DML = re.compile(
    r"\b(insert|update|delete|upsert)\s+\w*\s*(?:new\s+)?"
    r"(InsurancePolicy|InsurancePolicyCoverage|ServicePoint__c)\b",
    re.IGNORECASE,
)

# REST PATCH/POST directly to sobjects endpoint for insurance or E&U objects
REST_SOBJECTS_INSURANCE = re.compile(
    r"/sobjects/(InsurancePolicy|InsurancePolicyCoverage|ServicePoint__c)/",
    re.IGNORECASE,
)

# MuleSoft gateway URL pattern for Communications Cloud TM Forum APIs
MULESOFT_GATEWAY_URL = re.compile(
    r"https?://[a-z0-9\-]+\.cloudhub\.io.*(?:tmf|communications|comms)",
    re.IGNORECASE,
)

# TM Forum payload with name-based product resolution (missing id field alongside name)
TMF_NAME_WITHOUT_ID = re.compile(
    r'"productOffering"\s*:\s*\{[^}]*"name"\s*:[^}]*\}',
    re.DOTALL,
)

# Service Process Connect API response accessed without presence check
SERVICE_PROCESS_HARDCODED_ACCESS = re.compile(
    r'outputParameters\["[a-zA-Z]',
)


def check_apex_files(manifest_dir: Path) -> list[str]:
    """Check Apex (.cls) files for direct DML on industry objects."""
    issues: list[str] = []
    apex_files = list(manifest_dir.rglob("*.cls"))
    for apex_file in apex_files:
        try:
            text = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if APEX_DIRECT_DML.search(line):
                issues.append(
                    f"{apex_file}:{lineno}: Direct DML on InsurancePolicy or ServicePoint detected. "
                    f"Use the Insurance Policy Business Connect API or E&U Update Asset Status API instead. "
                    f"Line: {line.strip()!r}"
                )
    return issues


def check_for_mulesoft_gateway(manifest_dir: Path) -> list[str]:
    """Check all source files for deprecated MuleSoft gateway URLs used for Comms Cloud."""
    issues: list[str] = []
    # Check common source file types
    for ext in ("*.cls", "*.js", "*.json", "*.yaml", "*.yml", "*.xml", "*.md"):
        for src_file in manifest_dir.rglob(ext):
            try:
                text = src_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if MULESOFT_GATEWAY_URL.search(line):
                    issues.append(
                        f"{src_file}:{lineno}: Possible MuleSoft gateway URL for Communications Cloud detected. "
                        f"This path is deprecated as of Winter '27. Migrate to Direct Access "
                        f"(https://<instance>.my.salesforce.com/services/apexrest/tmf-api/...). "
                        f"Line: {line.strip()!r}"
                    )
    return issues


def check_rest_sobjects_patterns(manifest_dir: Path) -> list[str]:
    """Check for direct REST CRUD on InsurancePolicy or ServicePoint objects."""
    issues: list[str] = []
    for ext in ("*.cls", "*.js", "*.py", "*.json", "*.yaml", "*.yml"):
        for src_file in manifest_dir.rglob(ext):
            try:
                text = src_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if REST_SOBJECTS_INSURANCE.search(line):
                    issues.append(
                        f"{src_file}:{lineno}: Direct REST /sobjects/ call to InsurancePolicy or ServicePoint detected. "
                        f"Industry lifecycle operations must use the industry-specific Connect API endpoint. "
                        f"Line: {line.strip()!r}"
                    )
    return issues


def check_tmf_name_resolution(manifest_dir: Path) -> list[str]:
    """Check JSON/JS files for TM Forum payloads that use name instead of id for product resolution."""
    issues: list[str] = []
    for ext in ("*.json", "*.js", "*.cls"):
        for src_file in manifest_dir.rglob(ext):
            try:
                text = src_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            # Look for productOffering blocks with name but no id
            matches = TMF_NAME_WITHOUT_ID.findall(text)
            for match in matches:
                if '"id"' not in match:
                    issues.append(
                        f"{src_file}: TM Forum productOffering block uses 'name' without 'id'. "
                        f"Salesforce Communications Cloud TM Forum APIs are ID-driven. "
                        f"Pass the Salesforce record ID in the 'id' field, not a product name or catalog code."
                    )
                    break  # One warning per file is sufficient
    return issues


def check_service_process_response_access(manifest_dir: Path) -> list[str]:
    """Check for hardcoded Service Process API response field access without presence check."""
    issues: list[str] = []
    for ext in ("*.cls", "*.js", "*.py"):
        for src_file in manifest_dir.rglob(ext):
            try:
                text = src_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if SERVICE_PROCESS_HARDCODED_ACCESS.search(line):
                    issues.append(
                        f"{src_file}:{lineno}: Hardcoded access to Service Process Connect API outputParameters detected. "
                        f"Service Process response schema is dynamic and changes when the process definition is updated. "
                        f"Add a presence check before accessing output parameter fields. "
                        f"Line: {line.strip()!r}"
                    )
    return issues


def check_industries_api_extensions(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_files(manifest_dir))
    issues.extend(check_for_mulesoft_gateway(manifest_dir))
    issues.extend(check_rest_sobjects_patterns(manifest_dir))
    issues.extend(check_tmf_name_resolution(manifest_dir))
    issues.extend(check_service_process_response_access(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata and source files for Industries API extension anti-patterns. "
            "Detects: direct DML on InsurancePolicy/ServicePoint, deprecated MuleSoft gateway URLs "
            "for Communications Cloud, TM Forum name-based product resolution, and unsafe Service "
            "Process response access."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata or source (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_industries_api_extensions(manifest_dir)

    if not issues:
        print("No Industries API extension anti-patterns found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
