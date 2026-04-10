#!/usr/bin/env python3
"""Checker script for FSL Service Report Templates skill.

Scans Salesforce Apex metadata for common anti-patterns in service report
generation code. Checks cover:
  - createServiceReport called synchronously in a trigger (not in Queueable)
  - Missing old-value guard on createServiceReport calls
  - Direct ContentDocument queries without ContentDocumentLink
  - Visualforce renderAs="pdf" patterns used as service report mechanism

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_service_report.py [--manifest-dir path/to/metadata]
    python3 check_service_report.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# createServiceReport call that appears to be in a trigger context (heuristic:
# file name contains "Trigger" and the call is not inside a class that extends
# Queueable or implements Queueable).
_CREATE_REPORT_CALL = re.compile(
    r"ConnectApi\.FieldService\.createServiceReport\s*\(",
    re.IGNORECASE,
)

_QUEUEABLE_IMPL = re.compile(
    r"implements\s+.*Queueable",
    re.IGNORECASE,
)

_OLD_VALUE_GUARD = re.compile(
    r"Trigger\.oldMap|Trigger\.old\b",
    re.IGNORECASE,
)

# Visualforce renderAs="pdf" — wrong mechanism for FSL service reports
_VF_RENDER_AS_PDF = re.compile(
    r'renderAs\s*=\s*["\']pdf["\']',
    re.IGNORECASE,
)

# Direct ContentDocument query without ContentDocumentLink
_DIRECT_CONTENT_DOC_QUERY = re.compile(
    r"FROM\s+ContentDocument\b(?!Link)",
    re.IGNORECASE,
)

_CONTENT_DOC_LINK_QUERY = re.compile(
    r"FROM\s+ContentDocumentLink\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Per-file checks
# ---------------------------------------------------------------------------

def check_apex_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [f"{path}: could not read file"]

    is_trigger_file = "trigger" in path.stem.lower()
    has_queueable = bool(_QUEUEABLE_IMPL.search(source))
    has_create_report = bool(_CREATE_REPORT_CALL.search(source))

    # Check 1: createServiceReport in a trigger file that does NOT implement Queueable
    if has_create_report and is_trigger_file and not has_queueable:
        issues.append(
            f"{path}: createServiceReport called in trigger context without Queueable — "
            "this causes CPU limit failures under bulk load. Move the call to a Queueable.execute() method."
        )

    # Check 2: createServiceReport in trigger file without old-value guard
    if has_create_report and is_trigger_file:
        if not _OLD_VALUE_GUARD.search(source):
            issues.append(
                f"{path}: createServiceReport called in trigger without Trigger.oldMap guard — "
                "this will generate duplicate reports on every save after Completed status is set."
            )

    # Check 3: Direct ContentDocument query (no ContentDocumentLink)
    # Only warn if ContentDocument is queried and ContentDocumentLink is not also present in same file
    direct_doc = _DIRECT_CONTENT_DOC_QUERY.search(source)
    link_doc = _CONTENT_DOC_LINK_QUERY.search(source)
    if direct_doc and not link_doc:
        issues.append(
            f"{path}: direct ContentDocument SOQL query without ContentDocumentLink — "
            "to find service report PDFs linked to a specific record, query ContentDocumentLink "
            "WHERE LinkedEntityId = :recordId instead."
        )

    return issues


def check_visualforce_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return [f"{path}: could not read file"]

    if _VF_RENDER_AS_PDF.search(source):
        issues.append(
            f"{path}: Visualforce page uses renderAs=\"pdf\" — this is NOT the correct mechanism "
            "for FSL service report templates. Use ServiceReportLayout (Setup > Field Service > "
            "Service Report Templates) and ConnectApi.FieldService.createServiceReport() instead."
        )

    return issues


# ---------------------------------------------------------------------------
# Directory walker
# ---------------------------------------------------------------------------

def check_directory(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    # Check Apex classes and triggers
    for ext in ("*.cls", "*.trigger"):
        for apex_file in manifest_dir.rglob(ext):
            issues.extend(check_apex_file(apex_file))

    # Check Visualforce pages
    for vf_file in manifest_dir.rglob("*.page"):
        issues.extend(check_visualforce_file(vf_file))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce Apex and Visualforce metadata for FSL service report "
            "template anti-patterns."
        )
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_directory(manifest_dir)

    if not issues:
        print("No FSL service report anti-patterns detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
