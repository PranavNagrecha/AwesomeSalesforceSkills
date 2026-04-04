#!/usr/bin/env python3
"""Checker script for SOAP API Patterns skill.

Scans Salesforce project source files for common SOAP API integration
anti-patterns:
  - Old or retired API versions in SOAP endpoint URLs
  - Hardcoded instance hostnames (e.g., na1.salesforce.com)
  - Login endpoint used as the permanent service URL (not replaced by serverUrl)
  - Credentials or security tokens embedded in source
  - Missing per-record result inspection after DML calls

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_soap_api_patterns.py [--help]
    python3 check_soap_api_patterns.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum acceptable SOAP API version (roughly last 4+ major releases from Spring '25)
MIN_SOAP_API_VERSION = 56

# File extensions to scan
_SCAN_EXTENSIONS = {".cls", ".java", ".cs", ".py", ".js", ".ts", ".xml", ".json"}

# Directories to skip
_SKIP_DIRS = {"node_modules", ".sfdx", "__pycache__", ".git", "target", "bin", "obj"}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# SOAP endpoint URLs with an explicit version number
_RE_SOAP_VERSION = re.compile(
    r"/services/Soap/[ucm]/(\d+)(?:\.\d+)?",
    re.IGNORECASE,
)

# Hardcoded Salesforce instance hostnames (na1, cs1, ap1, eu0 etc.)
_RE_HARDCODED_INSTANCE = re.compile(
    r"https?://(?:na\d+|cs\d+|ap\d+|eu\d+|db\d+|gs\d+)\."
    r"salesforce\.com",
    re.IGNORECASE,
)

# Login endpoint used as service URL in connection/binding setup
# Flags patterns like setUrl("https://login.salesforce.com/services/Soap/...")
# or serviceEndpoint = "https://login.salesforce.com/..."
_RE_LOGIN_AS_SERVICE = re.compile(
    r"(?:setUrl|setServiceEndpoint|ServiceEndpoint|\.Url\s*=|authEndpoint)\s*[=(\"']+\s*"
    r"https://(?:login|test)\.salesforce\.com/services/Soap/[ucm]/",
    re.IGNORECASE,
)

# Patterns suggesting plain-text passwords in source
_RE_EMBEDDED_PASSWORD = re.compile(
    r'(?:password|passwd|pwd)\s*[=:]\s*["\'][^"\']{6,}["\']',
    re.IGNORECASE,
)

# Security token concatenation in source (e.g., password + token literals)
_RE_EMBEDDED_TOKEN = re.compile(
    r'(?:securityToken|security_token|token)\s*[=:]\s*["\'][A-Za-z0-9]{6,}["\']',
    re.IGNORECASE,
)

# Patterns indicating a SOAP create/update/upsert/delete call is made
_RE_DML_CALL = re.compile(
    r"\b(?:\.create|\.update|\.upsert|\.delete)\s*\(",
    re.IGNORECASE,
)

# Patterns indicating per-record result inspection (isSuccess, getErrors, SaveResult)
_RE_RESULT_INSPECTION = re.compile(
    r"(?:isSuccess|getErrors|SaveResult|UpsertResult|\.success|\.errors)",
    re.IGNORECASE,
)

# query() call present but no queryMore() or done-flag check
_RE_QUERY_CALL = re.compile(r"\b\.query\s*\(", re.IGNORECASE)
_RE_QUERY_MORE = re.compile(r"\b\.queryMore\s*\(|queryMore", re.IGNORECASE)
_RE_DONE_FLAG = re.compile(r"\.isDone\(\)|\"done\"\s*:|\.done\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Per-file check functions
# ---------------------------------------------------------------------------


def _read_file(path: Path) -> str | None:
    """Return file text or None if unreadable."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None


def _check_api_version(path: Path, text: str) -> list[str]:
    """Flag SOAP endpoint URLs with versions below the minimum."""
    issues: list[str] = []
    for match in _RE_SOAP_VERSION.finditer(text):
        try:
            version = int(match.group(1))
        except ValueError:
            continue
        if version < MIN_SOAP_API_VERSION:
            line_num = text[: match.start()].count("\n") + 1
            issues.append(
                f"{path}:{line_num} — SOAP API version v{version}.0 is below the "
                f"recommended minimum (v{MIN_SOAP_API_VERSION}.0). Update the endpoint "
                f"URL to v{MIN_SOAP_API_VERSION}.0 or later (Spring '25 = v63.0)."
            )
    return issues


def _check_hardcoded_instance(path: Path, text: str) -> list[str]:
    """Flag hardcoded Salesforce instance hostnames."""
    issues: list[str] = []
    for match in _RE_HARDCODED_INSTANCE.finditer(text):
        line_num = text[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_num} — Hardcoded Salesforce instance hostname detected: "
            f"'{match.group()}'. Use the serverUrl from LoginResult instead of a "
            f"static instance URL — other instances (sandbox, EU, Hyperforce) will fail."
        )
    return issues


def _check_login_as_service_url(path: Path, text: str) -> list[str]:
    """Flag use of the login endpoint as the permanent SOAP service URL."""
    issues: list[str] = []
    for match in _RE_LOGIN_AS_SERVICE.finditer(text):
        line_num = text[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_num} — login.salesforce.com or test.salesforce.com appears "
            f"to be set as the permanent SOAP service endpoint. After login(), switch "
            f"all subsequent calls to the serverUrl from LoginResult."
        )
    return issues


def _check_embedded_credentials(path: Path, text: str) -> list[str]:
    """Flag embedded plaintext passwords or security tokens."""
    issues: list[str] = []
    for match in _RE_EMBEDDED_PASSWORD.finditer(text):
        line_num = text[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_num} — Possible hardcoded password detected. Credentials "
            f"must not be embedded in source code. Use environment variables or a "
            f"secrets manager instead."
        )
    for match in _RE_EMBEDDED_TOKEN.finditer(text):
        line_num = text[: match.start()].count("\n") + 1
        issues.append(
            f"{path}:{line_num} — Possible hardcoded security token detected. "
            f"Security tokens are static credentials; store them in environment "
            f"variables or a secrets manager, never in source."
        )
    return issues


def _check_dml_result_inspection(path: Path, text: str) -> list[str]:
    """Check that DML calls (create/update/upsert/delete) also inspect per-record results."""
    issues: list[str] = []
    if not _RE_DML_CALL.search(text):
        return issues
    if not _RE_RESULT_INSPECTION.search(text):
        issues.append(
            f"{path} — SOAP DML call (create/update/upsert/delete) detected but no "
            f"per-record result inspection found (isSuccess/getErrors/SaveResult/"
            f"UpsertResult). SOAP DML calls partially succeed without throwing a fault "
            f"— always inspect each result in the returned array."
        )
    return issues


def _check_query_pagination(path: Path, text: str) -> list[str]:
    """Check that query() calls are accompanied by queryMore() pagination."""
    issues: list[str] = []
    if not _RE_QUERY_CALL.search(text):
        return issues
    has_query_more = bool(_RE_QUERY_MORE.search(text))
    has_done_flag = bool(_RE_DONE_FLAG.search(text))
    if not has_query_more or not has_done_flag:
        missing: list[str] = []
        if not has_query_more:
            missing.append("queryMore()")
        if not has_done_flag:
            missing.append("done flag check (isDone()/done)")
        issues.append(
            f"{path} — SOAP query() call detected but pagination handling is incomplete "
            f"(missing: {', '.join(missing)}). query() returns a partial result set when "
            f"done=false; call queryMore() until isDone() returns true to avoid silently "
            f"truncating results."
        )
    return issues


# ---------------------------------------------------------------------------
# Main scanner
# ---------------------------------------------------------------------------


def check_soap_api_patterns(manifest_dir: Path) -> list[str]:
    """Scan manifest_dir for SOAP API integration issues.

    Returns a list of actionable issue strings.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    source_files = [
        f
        for f in manifest_dir.rglob("*")
        if f.is_file()
        and f.suffix in _SCAN_EXTENSIONS
        and not any(part in _SKIP_DIRS for part in f.parts)
    ]

    for source_file in source_files:
        text = _read_file(source_file)
        if text is None:
            continue

        # Only inspect files that appear to involve SOAP / Salesforce API calls
        if not (
            "salesforce.com" in text.lower()
            or "sforce.com" in text.lower()
            or "/services/Soap" in text
            or "EnterpriseConnection" in text
            or "PartnerConnection" in text
            or "MetadataConnection" in text
            or "SforceService" in text
        ):
            continue

        issues.extend(_check_api_version(source_file, text))
        issues.extend(_check_hardcoded_instance(source_file, text))
        issues.extend(_check_login_as_service_url(source_file, text))
        issues.extend(_check_embedded_credentials(source_file, text))
        issues.extend(_check_dml_result_inspection(source_file, text))
        issues.extend(_check_query_pagination(source_file, text))

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce project source files for SOAP API integration "
            "anti-patterns: old API versions, hardcoded instance URLs, login "
            "endpoint misuse, embedded credentials, missing DML result inspection, "
            "and incomplete query pagination."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce project source (default: current directory).",
    )
    args = parser.parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues = check_soap_api_patterns(manifest_dir)

    if not issues:
        print("No SOAP API pattern issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
