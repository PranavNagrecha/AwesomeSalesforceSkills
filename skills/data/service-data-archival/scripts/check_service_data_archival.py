#!/usr/bin/env python3
"""Checker script for Service Data Archival skill.

Validates archival plan documents and deletion scripts for common issues:
- Orphaned ContentDocumentLink references (no ContentDocument check step)
- Missing legal-hold filter in deletion SOQL
- Wrong deletion order (Case before EmailMessage/ContentDocument)
- Missing post-deletion validation steps
- Use of synchronous DML instead of Bulk API for large-volume deletes
- ContentDocument deleted before ContentDocumentLink

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_service_data_archival.py [--help]
    python3 check_service_data_archival.py --scan-file path/to/script_or_plan.sql
    python3 check_service_data_archival.py --scan-dir path/to/scripts/
    python3 check_service_data_archival.py --checklist
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Patterns that indicate a DELETE on Case without EmailMessage handling nearby
CASE_DELETE_PATTERN = re.compile(
    r"\bdelete\b.{0,120}?\bCase\b",
    re.IGNORECASE | re.DOTALL,
)

EMAIL_MESSAGE_PATTERN = re.compile(
    r"\bEmailMessage\b",
    re.IGNORECASE,
)

CONTENT_DOC_LINK_PATTERN = re.compile(
    r"\bContentDocumentLink\b",
    re.IGNORECASE,
)

CONTENT_DOC_PATTERN = re.compile(
    r"\bContentDocument\b(?!Link)",
    re.IGNORECASE,
)

LEGAL_HOLD_PATTERN = re.compile(
    r"Legal_Hold__c\s*=\s*false",
    re.IGNORECASE,
)

SOQL_DELETE_PATTERN = re.compile(
    r"\bDELETE\b\s+FROM\s+\w+",
    re.IGNORECASE,
)

# Bulk API indicators
BULK_API_PATTERN = re.compile(
    r"(?:BulkApi|bulk_api|api_asynch|hardDelete|jobs/ingest|Bulk\s+API)",
    re.IGNORECASE,
)

# Apex synchronous delete on large objects — flagged when no Bulk API reference present
APEX_DELETE_PATTERN = re.compile(
    r"\bdelete\s+\w+(?:emails?|messages?|contentDocs?|cases?)\b",
    re.IGNORECASE,
)

# Attachment (legacy) instead of ContentDocument
LEGACY_ATTACHMENT_PATTERN = re.compile(
    r"\bAttachment\b(?!\s*History)",
    re.IGNORECASE,
)

# Post-deletion validation — looking for COUNT queries after delete
POST_VALIDATION_PATTERN = re.compile(
    r"(?:COUNT\(Id\)|Storage\s+Usage|check_service_data_archival|orphan)",
    re.IGNORECASE,
)

# Recycle Bin / hard delete handling
RECYCLE_BIN_PATTERN = re.compile(
    r"(?:emptyRecycleBin|hardDelete|Recycle\s+Bin|recycle_bin)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_deletion_order(content: str, filename: str) -> list[str]:
    """Warn if Case deletion appears before EmailMessage or ContentDocument handling."""
    issues: list[str] = []

    case_delete_matches = [m.start() for m in CASE_DELETE_PATTERN.finditer(content)]
    email_matches = [m.start() for m in EMAIL_MESSAGE_PATTERN.finditer(content)]
    cdl_matches = [m.start() for m in CONTENT_DOC_LINK_PATTERN.finditer(content)]

    if not case_delete_matches:
        return issues

    first_case_delete = min(case_delete_matches)

    if email_matches and min(email_matches) > first_case_delete:
        issues.append(
            f"{filename}: EmailMessage handling appears AFTER Case deletion. "
            "Correct order: handle EmailMessage before or alongside Case deletion "
            "to avoid orphaned email records."
        )

    if cdl_matches and min(cdl_matches) > first_case_delete:
        issues.append(
            f"{filename}: ContentDocumentLink handling appears AFTER Case deletion. "
            "ContentDocumentLink records must be processed before Case deletion "
            "to ensure file storage cleanup."
        )

    return issues


def check_legal_hold_filter(content: str, filename: str) -> list[str]:
    """Warn if deletion SOQL is present but no legal-hold filter is found."""
    issues: list[str] = []

    has_deletion = bool(
        CASE_DELETE_PATTERN.search(content)
        or SOQL_DELETE_PATTERN.search(content)
        or re.search(r"\bdelete\b\s+\w+", content, re.IGNORECASE)
    )

    if has_deletion and not LEGAL_HOLD_PATTERN.search(content):
        issues.append(
            f"{filename}: Deletion logic found but no Legal_Hold__c = false filter detected. "
            "All deletion SOQL must exclude legal-hold records at the WHERE clause level. "
            "Missing legal-hold filters cause Bulk API batch failures when held records "
            "are included."
        )

    return issues


def check_content_doc_orphan_handling(content: str, filename: str) -> list[str]:
    """Warn if ContentDocument deletion is present but no ContentDocumentLink check precedes it."""
    issues: list[str] = []

    cd_matches = [m.start() for m in re.finditer(r"\bContentDocument\b(?!Link)", content, re.IGNORECASE)]
    cdl_matches = [m.start() for m in CONTENT_DOC_LINK_PATTERN.finditer(content)]

    if not cd_matches:
        return issues

    first_cd = min(cd_matches)

    # ContentDocumentLink should appear before ContentDocument deletion
    if not cdl_matches or min(cdl_matches) > first_cd:
        issues.append(
            f"{filename}: ContentDocument appears before ContentDocumentLink handling. "
            "ContentDocumentLink records must be deleted before ContentDocument records. "
            "Also verify ContentDocument records have no other active links before deletion "
            "(HAVING COUNT(Id) = 1 check)."
        )

    # Check for the 'other links' guard (HAVING COUNT or similar)
    having_check = re.search(r"HAVING\s+COUNT\s*\(", content, re.IGNORECASE)
    link_count_check = re.search(r"linkCount|link_count|COUNT.*ContentDocumentLink", content, re.IGNORECASE)
    if not having_check and not link_count_check:
        issues.append(
            f"{filename}: No multi-link guard found for ContentDocument deletion. "
            "A ContentDocument may be linked to multiple entities. "
            "Use HAVING COUNT(Id) = 1 on ContentDocumentLink to identify exclusively-linked "
            "documents before deleting, to avoid destroying shared files."
        )

    return issues


def check_legacy_attachment_usage(content: str, filename: str) -> list[str]:
    """Warn if legacy Attachment object is referenced instead of ContentDocument."""
    issues: list[str] = []

    if LEGACY_ATTACHMENT_PATTERN.search(content):
        issues.append(
            f"{filename}: Reference to legacy 'Attachment' object found. "
            "Modern Service Cloud orgs (post-Spring '16 with Salesforce Files) store "
            "files as ContentDocument/ContentVersion linked via ContentDocumentLink. "
            "Verify which storage mechanism is in use before targeting Attachment records."
        )

    return issues


def check_post_deletion_validation(content: str, filename: str) -> list[str]:
    """Warn if no post-deletion validation step is found in deletion scripts."""
    issues: list[str] = []

    has_deletion = bool(
        CASE_DELETE_PATTERN.search(content)
        or re.search(r"\bdelete\b\s+\w+", content, re.IGNORECASE)
    )

    if has_deletion and not POST_VALIDATION_PATTERN.search(content):
        issues.append(
            f"{filename}: Deletion logic found but no post-deletion validation step detected. "
            "After deletion, run COUNT(Id) queries on deleted objects and compare "
            "Setup > Storage Usage to the pre-deletion baseline. "
            "Also check for orphaned ContentDocumentLink and ContentDocument records."
        )

    return issues


def check_recycle_bin_handling(content: str, filename: str) -> list[str]:
    """Warn if deletion is present but no Recycle Bin empty / hard-delete step is found."""
    issues: list[str] = []

    has_deletion = bool(
        CASE_DELETE_PATTERN.search(content)
        or re.search(r"\bdelete\b\s+\w+", content, re.IGNORECASE)
    )

    if has_deletion and not RECYCLE_BIN_PATTERN.search(content):
        issues.append(
            f"{filename}: Deletion logic found but no Recycle Bin empty or hard-delete step detected. "
            "Deleted records remain in the Recycle Bin for 15 days and continue to count "
            "against storage during that period. "
            "Use hard-delete (Bulk API hardDelete operation) or emptyRecycleBin() "
            "to reclaim storage immediately after deletion."
        )

    return issues


def check_bulk_api_for_scale(content: str, filename: str) -> list[str]:
    """Warn if Apex synchronous delete is used without Bulk API for large-volume objects."""
    issues: list[str] = []

    apex_del = APEX_DELETE_PATTERN.search(content)
    if apex_del and not BULK_API_PATTERN.search(content):
        issues.append(
            f"{filename}: Apex synchronous delete found with no Bulk API reference. "
            "For EmailMessage, ContentDocument, or Case deletion at scale (> 10,000 records), "
            "use Bulk API 2.0 instead of synchronous Apex DML. "
            "Synchronous DML is capped at 10,000 rows per transaction and consumes Apex governor limits."
        )

    return issues


# ---------------------------------------------------------------------------
# File scanner
# ---------------------------------------------------------------------------

SCANNABLE_EXTENSIONS = {".sql", ".soql", ".apex", ".cls", ".py", ".md", ".txt", ".sh"}


def scan_file(path: Path) -> list[str]:
    """Run all checks against a single file. Return list of issue strings."""
    if path.suffix.lower() not in SCANNABLE_EXTENSIONS:
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"{path}: Could not read file — {exc}"]

    filename = str(path)
    issues: list[str] = []
    issues.extend(check_deletion_order(content, filename))
    issues.extend(check_legal_hold_filter(content, filename))
    issues.extend(check_content_doc_orphan_handling(content, filename))
    issues.extend(check_legacy_attachment_usage(content, filename))
    issues.extend(check_post_deletion_validation(content, filename))
    issues.extend(check_recycle_bin_handling(content, filename))
    issues.extend(check_bulk_api_for_scale(content, filename))
    return issues


def scan_directory(directory: Path) -> list[str]:
    """Recursively scan all scannable files in a directory."""
    issues: list[str] = []
    for path in sorted(directory.rglob("*")):
        if path.is_file():
            issues.extend(scan_file(path))
    return issues


# ---------------------------------------------------------------------------
# Guided checklist (standalone mode)
# ---------------------------------------------------------------------------

CHECKLIST = """
================================================================================
SERVICE DATA ARCHIVAL — PRE-EXECUTION CHECKLIST
================================================================================

Before running any deletion script, confirm each item below.

STORAGE BASELINE
  [ ] Data Storage GB and File Storage GB recorded from Setup > Storage Usage
  [ ] Primary storage driver identified (EmailMessage vs ContentDocument)
  [ ] Record counts by object confirmed via SOQL (Case, EmailMessage, ContentDocument)

RETENTION POLICY
  [ ] Retention matrix confirmed with legal/compliance team
  [ ] Minimum retention period documented per object type
  [ ] Export-before-delete requirement confirmed for each object

LEGAL HOLD
  [ ] Legal-hold list refreshed from source of truth TODAY (not a cached copy)
  [ ] Legal-hold exclusion applied in SOQL WHERE clause (not post-query filtering)
  [ ] Legal-hold record count confirmed (Cases, EmailMessage, ContentDocument)

EXPORT / ARCHIVE
  [ ] EmailMessage records exported to external store (if required)
  [ ] ContentDocument blobs exported to external store (if required)
  [ ] Case records exported to external store (if required)
  [ ] Export checksums confirmed

DELETION SEQUENCE
  [ ] Step 1: ContentDocumentLink records deleted for exclusively-linked Cases
  [ ] Step 2: Orphaned ContentDocument records deleted
  [ ] Step 3: EmailMessage records deleted by CaseId
  [ ] Step 4: Case records deleted (if in scope)
  [ ] Each step validated with post-step COUNT query before proceeding

POST-DELETION
  [ ] Recycle Bin emptied (hard-delete or emptyRecycleBin)
  [ ] Setup > Storage Usage re-checked and delta confirmed
  [ ] Orphan scan run with this script
  [ ] Legal/compliance sign-off recorded

================================================================================
"""


# ---------------------------------------------------------------------------
# Argument parsing and main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check service data archival scripts and plans for common issues.\n"
            "Validates deletion order, legal-hold filters, ContentDocument orphan handling,\n"
            "Recycle Bin cleanup, and post-deletion validation steps."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--scan-file",
        metavar="FILE",
        help="Scan a single file for archival issues.",
    )
    group.add_argument(
        "--scan-dir",
        metavar="DIR",
        help="Recursively scan a directory for archival issues.",
    )
    group.add_argument(
        "--checklist",
        action="store_true",
        help="Print the pre-execution checklist and exit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.checklist:
        print(CHECKLIST)
        return 0

    issues: list[str] = []

    if args.scan_file:
        path = Path(args.scan_file)
        if not path.exists():
            print(f"ERROR: File not found: {path}", file=sys.stderr)
            return 2
        issues = scan_file(path)

    elif args.scan_dir:
        directory = Path(args.scan_dir)
        if not directory.is_dir():
            print(f"ERROR: Directory not found: {directory}", file=sys.stderr)
            return 2
        issues = scan_directory(directory)

    else:
        # Default: print checklist and usage hint
        print(CHECKLIST)
        print("To scan a file:      python3 check_service_data_archival.py --scan-file <path>")
        print("To scan a directory: python3 check_service_data_archival.py --scan-dir <path>")
        return 0

    if not issues:
        print("No issues found.")
        return 0

    print(f"\nFound {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"  [{i}] WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found. Review and resolve before executing archival.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
