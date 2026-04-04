#!/usr/bin/env python3
"""Checker script for Apex Email Services skill.

Scans a Salesforce metadata directory for common Email Services issues:
- InboundEmailHandler classes missing null guards for attachment lists
- EmailServicesFunction metadata with isActive set to false
- Handler classes not returning InboundEmailResult in all code paths (heuristic)
- Missing try/catch block in handleInboundEmail

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_apex_email_services.py [--help]
    python3 check_apex_email_services.py --manifest-dir path/to/force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Apex Email Services configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_email_service_active(manifest_dir: Path) -> list[str]:
    """Warn when an EmailServicesFunction metadata file has isActive = false."""
    issues: list[str] = []
    email_svc_dir = manifest_dir / "emailservices"
    if not email_svc_dir.exists():
        # Not present — nothing to check
        return issues

    for xml_file in email_svc_dir.glob("*.emailservices-meta.xml"):
        content = xml_file.read_text(encoding="utf-8")
        # Look for <isActive>false</isActive>
        if re.search(r"<isActive>\s*false\s*</isActive>", content, re.IGNORECASE):
            issues.append(
                f"{xml_file.name}: Email Service address is inactive (isActive=false). "
                "Inbound mail will be silently discarded until this is set to true."
            )

    return issues


def check_handler_null_guards(manifest_dir: Path) -> list[str]:
    """Heuristic: warn when a handler iterates attachments without a null check."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    # Pattern: file implements InboundEmailHandler
    handler_pattern = re.compile(
        r"implements\s+Messaging\.InboundEmailHandler", re.IGNORECASE
    )
    # Pattern: iterates textAttachments or binaryAttachments directly
    unsafe_iter_pattern = re.compile(
        r"for\s*\([^)]*email\.(textAttachments|binaryAttachments)\)", re.IGNORECASE
    )
    # Pattern: null guard present
    null_guard_pattern = re.compile(
        r"(textAttachments|binaryAttachments)\s*!=\s*null", re.IGNORECASE
    )

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8")
        if not handler_pattern.search(content):
            continue  # Not a handler — skip

        if unsafe_iter_pattern.search(content) and not null_guard_pattern.search(content):
            issues.append(
                f"{cls_file.name}: InboundEmailHandler iterates email.textAttachments or "
                "email.binaryAttachments without a null guard. These lists are null (not empty) "
                "when no attachments exist, causing NullPointerException."
            )

    return issues


def check_handler_try_catch(manifest_dir: Path) -> list[str]:
    """Heuristic: warn when a handler has no try/catch block in handleInboundEmail."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    handler_pattern = re.compile(
        r"implements\s+Messaging\.InboundEmailHandler", re.IGNORECASE
    )
    method_pattern = re.compile(
        r"handleInboundEmail\s*\(", re.IGNORECASE
    )
    try_catch_pattern = re.compile(r"\btry\s*\{", re.IGNORECASE)

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8")
        if not handler_pattern.search(content):
            continue
        if method_pattern.search(content) and not try_catch_pattern.search(content):
            issues.append(
                f"{cls_file.name}: handleInboundEmail does not appear to have a try/catch block. "
                "Unhandled exceptions cause the handler to fail and may trigger a bounce storm "
                "depending on the Email Service Error Action configuration."
            )

    return issues


def check_handler_returns_result(manifest_dir: Path) -> list[str]:
    """Heuristic: warn when a handler does not reference InboundEmailResult."""
    issues: list[str] = []
    classes_dir = manifest_dir / "classes"
    if not classes_dir.exists():
        return issues

    handler_pattern = re.compile(
        r"implements\s+Messaging\.InboundEmailHandler", re.IGNORECASE
    )
    result_pattern = re.compile(
        r"InboundEmailResult", re.IGNORECASE
    )

    for cls_file in classes_dir.glob("*.cls"):
        content = cls_file.read_text(encoding="utf-8")
        if not handler_pattern.search(content):
            continue
        if not result_pattern.search(content):
            issues.append(
                f"{cls_file.name}: InboundEmailHandler does not reference InboundEmailResult. "
                "handleInboundEmail must return a Messaging.InboundEmailResult; "
                "a null return is treated as failure by the Email Services framework."
            )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_apex_email_services(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_email_service_active(manifest_dir))
    issues.extend(check_handler_null_guards(manifest_dir))
    issues.extend(check_handler_try_catch(manifest_dir))
    issues.extend(check_handler_returns_result(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_apex_email_services(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
