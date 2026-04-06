#!/usr/bin/env python3
"""Checker script for File And Document Integration skill.

Scans Apex classes, triggers, and metadata for common file integration issues:
- Direct ContentDocument inserts (should use ContentVersion)
- Legacy Attachment object usage in new code
- Missing virus scanning patterns on ContentVersion triggers
- Base64 encoding of VersionData without size guards
- Bulk VersionData queries without heap protection

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_file_and_document_integration.py [--help]
    python3 check_file_and_document_integration.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check File And Document Integration configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_apex_files(manifest_dir: Path) -> list[Path]:
    """Find all .cls and .trigger files recursively."""
    files: list[Path] = []
    for ext in ("*.cls", "*.trigger"):
        files.extend(manifest_dir.rglob(ext))
    return files


def check_direct_content_document_insert(content: str, filepath: Path) -> list[str]:
    """Detect direct ContentDocument inserts."""
    issues: list[str] = []
    pattern = re.compile(r'\bnew\s+ContentDocument\s*\(', re.IGNORECASE)
    for i, line in enumerate(content.splitlines(), 1):
        if pattern.search(line):
            issues.append(
                f"{filepath}:{i} — Direct ContentDocument instantiation detected. "
                "Insert ContentVersion instead; ContentDocument is auto-created."
            )
    return issues


def check_legacy_attachment_usage(content: str, filepath: Path) -> list[str]:
    """Detect usage of the legacy Attachment object."""
    issues: list[str] = []
    pattern = re.compile(r'\bnew\s+Attachment\s*\(', re.IGNORECASE)
    for i, line in enumerate(content.splitlines(), 1):
        if pattern.search(line):
            issues.append(
                f"{filepath}:{i} — Legacy Attachment object used. "
                "Use ContentVersion + ContentDocumentLink for new file storage."
            )
    return issues


def check_bulk_version_data_query(content: str, filepath: Path) -> list[str]:
    """Detect SOQL queries that select VersionData in potentially bulk contexts."""
    issues: list[str] = []
    # Match SELECT ... VersionData ... FROM ContentVersion with a WHERE IN clause
    pattern = re.compile(
        r'SELECT\s+.*\bVersionData\b.*FROM\s+ContentVersion\s+WHERE\s+.*\bIN\b',
        re.IGNORECASE | re.DOTALL,
    )
    if pattern.search(content):
        issues.append(
            f"{filepath} — Bulk query selecting VersionData detected. "
            "VersionData loads full file binaries into heap. "
            "Process files one at a time or use Batch Apex with scope size 1."
        )
    return issues


def check_base64_without_size_guard(content: str, filepath: Path) -> list[str]:
    """Detect base64 encoding of file data without an accompanying size check."""
    issues: list[str] = []
    has_base64 = re.search(r'EncodingUtil\.base64Encode', content, re.IGNORECASE)
    has_version_data = re.search(r'VersionData', content, re.IGNORECASE)
    has_size_check = re.search(r'\.size\(\)|\.length\(\)|ContentSize|FILE_SIZE', content, re.IGNORECASE)

    if has_base64 and has_version_data and not has_size_check:
        issues.append(
            f"{filepath} — Base64 encoding used with VersionData but no file size check found. "
            "Base64 inflates data by 33%; files over ~20 MB should use multipart upload."
        )
    return issues


def check_missing_virus_scan_trigger(manifest_dir: Path) -> list[str]:
    """Check if a ContentVersion trigger exists (advisory, not blocking)."""
    issues: list[str] = []
    trigger_files = list(manifest_dir.rglob("*.trigger"))
    has_cv_trigger = False
    for tf in trigger_files:
        try:
            content = tf.read_text(encoding="utf-8", errors="replace")
            if re.search(r'trigger\s+\w+\s+on\s+ContentVersion', content, re.IGNORECASE):
                has_cv_trigger = True
                break
        except OSError:
            continue

    if trigger_files and not has_cv_trigger:
        issues.append(
            "ADVISORY: No ContentVersion trigger found. "
            "If virus scanning is required, implement an after-insert trigger "
            "that enqueues a scanning Queueable."
        )
    return issues


def check_file_and_document_integration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    apex_files = find_apex_files(manifest_dir)

    if not apex_files:
        issues.append(
            f"No Apex files (.cls, .trigger) found under {manifest_dir}. "
            "Provide a metadata directory containing Apex source files."
        )
        return issues

    for filepath in apex_files:
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            issues.append(f"Could not read {filepath}: {e}")
            continue

        issues.extend(check_direct_content_document_insert(content, filepath))
        issues.extend(check_legacy_attachment_usage(content, filepath))
        issues.extend(check_bulk_version_data_query(content, filepath))
        issues.extend(check_base64_without_size_guard(content, filepath))

    issues.extend(check_missing_virus_scan_trigger(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_file_and_document_integration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
