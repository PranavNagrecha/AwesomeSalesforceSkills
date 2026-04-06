#!/usr/bin/env python3
"""Checker script for Case History Migration skill.

Validates migration CSV files and metadata for common case history migration
issues: EmailMessage Status='3' usage, ContentDocumentLink Bulk API misuse
signals, CaseHistory direct-insert attempts, missing EmailMessageRelation,
and incorrect object load order.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_case_history_migration.py [--help]
    python3 check_case_history_migration.py --manifest-dir path/to/csvs
    python3 check_case_history_migration.py --csv-file EmailMessage.csv --object EmailMessage
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# EmailMessage Status values that are safe for migration loads
SAFE_EMAIL_STATUS_VALUES = {"0", "1", "2", "4"}
# Status='3' (Sent) permanently locks the record — never use in migrations
LOCKED_EMAIL_STATUS = "3"

# Objects that indicate a direct CaseHistory insert attempt (always wrong)
CASE_HISTORY_DIRECT_INSERT_SIGNALS = {
    "casehistory",
    "case_history",
    "case-history",
}

# ContentDocumentLink is not supported by Bulk API 2.0
# Flag any CSV named ContentDocumentLink as a warning if it appears
# in a folder alongside a Bulk API job manifest
CONTENT_DOCUMENT_LINK_OBJECT = "contentdocumentlink"

# Required load order: each object must appear after all items above it
REQUIRED_LOAD_ORDER = [
    "case",
    "casecomment",
    "emailmessage",
    "emailmessagerelation",
    "contentversion",
    "contentdocumentlink",
]


# ---------------------------------------------------------------------------
# CSV Checkers
# ---------------------------------------------------------------------------


def check_email_message_csv(csv_path: Path) -> list[str]:
    """Check an EmailMessage CSV for Status='3' (permanent lock) usage."""
    issues: list[str] = []
    try:
        with csv_path.open(newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            headers_lower = [h.lower() for h in (reader.fieldnames or [])]
            if "status" not in headers_lower:
                issues.append(
                    f"{csv_path.name}: 'Status' column not found — "
                    "EmailMessage must include a Status value."
                )
                return issues

            locked_rows: list[int] = []
            for i, row in enumerate(reader, start=2):  # row 1 = header
                status_val = None
                for key in row:
                    if key.lower() == "status":
                        status_val = (row[key] or "").strip()
                        break
                if status_val == LOCKED_EMAIL_STATUS:
                    locked_rows.append(i)

            if locked_rows:
                sample = locked_rows[:5]
                issues.append(
                    f"{csv_path.name}: {len(locked_rows)} row(s) have Status='3' (Sent). "
                    f"This permanently locks EmailMessage records — they cannot be updated "
                    f"or deleted after insert. Use Status='1' (Read) for inbound or "
                    f"Status='2' (Replied) for outbound historical emails. "
                    f"Sample rows: {sample}"
                )
    except Exception as exc:
        issues.append(f"{csv_path.name}: could not parse CSV — {exc}")
    return issues


def check_for_case_history_csv(manifest_dir: Path) -> list[str]:
    """Warn if any CSV file name suggests a direct CaseHistory insert attempt."""
    issues: list[str] = []
    for csv_path in manifest_dir.glob("*.csv"):
        stem_lower = csv_path.stem.lower().replace(" ", "").replace("_", "").replace("-", "")
        if stem_lower in {s.replace("_", "").replace("-", "") for s in CASE_HISTORY_DIRECT_INSERT_SIGNALS}:
            issues.append(
                f"{csv_path.name}: file name suggests a direct CaseHistory insert attempt. "
                "CaseHistory is not insertable (INVALID_TYPE_FOR_OPERATION). "
                "Use Task records or FeedItem records to approximate historical case audit data."
            )
    return issues


def check_email_message_relation_present(manifest_dir: Path) -> list[str]:
    """Warn if EmailMessage CSV exists but EmailMessageRelation CSV is absent."""
    issues: list[str] = []
    csv_stems_lower = {p.stem.lower() for p in manifest_dir.glob("*.csv")}
    has_email_message = any(
        "emailmessage" in s and "relation" not in s for s in csv_stems_lower
    )
    has_email_message_relation = any(
        "emailmessagerelation" in s for s in csv_stems_lower
    )
    if has_email_message and not has_email_message_relation:
        issues.append(
            "EmailMessage CSV found but no EmailMessageRelation CSV detected. "
            "Without EmailMessageRelation rows, email recipients are not linked to "
            "Contact/Lead/User records. Add an EmailMessageRelation load step."
        )
    return issues


def check_content_document_link_load_method(manifest_dir: Path) -> list[str]:
    """
    Warn if a ContentDocumentLink CSV exists alongside a Bulk API job manifest
    or job config file, which suggests it will be loaded via Bulk API 2.0.
    """
    issues: list[str] = []
    cdl_csv = None
    for csv_path in manifest_dir.glob("*.csv"):
        if csv_path.stem.lower().replace("_", "").replace("-", "") == CONTENT_DOCUMENT_LINK_OBJECT:
            cdl_csv = csv_path
            break

    if cdl_csv is None:
        return issues

    # Look for signals that a Bulk API loader config exists
    bulk_signals = list(manifest_dir.glob("*bulk*")) + list(manifest_dir.glob("*job*.json"))
    if bulk_signals:
        issues.append(
            f"{cdl_csv.name}: ContentDocumentLink CSV found alongside Bulk API job files "
            f"({[p.name for p in bulk_signals[:3]]}). ContentDocumentLink does NOT support "
            "Bulk API 2.0. Load ContentDocumentLink via the REST API or SOAP API only."
        )
    else:
        # Always warn about ContentDocumentLink regardless of method signals
        issues.append(
            f"{cdl_csv.name}: ContentDocumentLink detected. Reminder — this object does NOT "
            "support Bulk API 2.0. Ensure you are loading via REST API or SOAP API."
        )
    return issues


def check_load_order(manifest_dir: Path) -> list[str]:
    """
    Check that CSVs exist in the correct dependency order.
    Reports if a child object CSV exists but its parent CSV is missing.
    """
    issues: list[str] = []
    present: set[str] = set()
    for csv_path in manifest_dir.glob("*.csv"):
        stem_norm = csv_path.stem.lower().replace("_", "").replace("-", "").replace(" ", "")
        present.add(stem_norm)

    # Map normalized names to REQUIRED_LOAD_ORDER entries
    def normalize(s: str) -> str:
        return s.lower().replace("_", "").replace("-", "").replace(" ", "")

    order_norm = [normalize(o) for o in REQUIRED_LOAD_ORDER]

    # Parent dependency map: object → required parent
    deps = {
        "casecomment": "case",
        "emailmessage": "case",
        "emailmessagerelation": "emailmessage",
        "contentdocumentlink": "contentversion",
    }

    for child_norm, parent_norm in deps.items():
        child_present = any(child_norm in s for s in present)
        parent_present = any(parent_norm in s for s in present)
        if child_present and not parent_present:
            child_display = next((o for o in REQUIRED_LOAD_ORDER if normalize(o) == child_norm), child_norm)
            parent_display = next((o for o in REQUIRED_LOAD_ORDER if normalize(o) == parent_norm), parent_norm)
            issues.append(
                f"Load order violation: '{child_display}' CSV found but no '{parent_display}' CSV detected. "
                f"'{child_display}' requires '{parent_display}' to exist first. "
                "Check that the parent object is loaded before the child."
            )
    return issues


def check_content_version_csv(manifest_dir: Path) -> list[str]:
    """Check ContentVersion CSV for required columns."""
    issues: list[str] = []
    required_columns = {"title", "pathonclient", "versiondata"}
    for csv_path in manifest_dir.glob("*.csv"):
        if "contentversion" in csv_path.stem.lower() and "link" not in csv_path.stem.lower():
            try:
                with csv_path.open(newline="", encoding="utf-8-sig") as fh:
                    reader = csv.DictReader(fh)
                    headers_lower = {h.lower() for h in (reader.fieldnames or [])}
                    missing = required_columns - headers_lower
                    if missing:
                        issues.append(
                            f"{csv_path.name}: ContentVersion CSV is missing required columns: "
                            f"{sorted(missing)}. Required: Title, PathOnClient, VersionData."
                        )
            except Exception as exc:
                issues.append(f"{csv_path.name}: could not parse CSV — {exc}")
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_case_history_migration(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Check each EmailMessage CSV for Status='3'
    for csv_path in manifest_dir.glob("*.csv"):
        stem_norm = csv_path.stem.lower().replace("_", "").replace("-", "").replace(" ", "")
        if "emailmessage" in stem_norm and "relation" not in stem_norm:
            issues.extend(check_email_message_csv(csv_path))

    # Check for CaseHistory direct-insert attempt
    issues.extend(check_for_case_history_csv(manifest_dir))

    # Check for missing EmailMessageRelation
    issues.extend(check_email_message_relation_present(manifest_dir))

    # Check ContentDocumentLink load method
    issues.extend(check_content_document_link_load_method(manifest_dir))

    # Check load order dependencies
    issues.extend(check_load_order(manifest_dir))

    # Check ContentVersion required columns
    issues.extend(check_content_version_csv(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Case History Migration CSV files for common issues: "
            "EmailMessage Status='3' locking, ContentDocumentLink Bulk API misuse, "
            "CaseHistory insert attempts, missing EmailMessageRelation, and load order violations."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Directory containing migration CSV files (default: current directory).",
    )
    parser.add_argument(
        "--csv-file",
        default=None,
        help="Path to a single CSV file to check (used with --object).",
    )
    parser.add_argument(
        "--object",
        default=None,
        help="Salesforce object type of the CSV file (e.g. EmailMessage).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Single-file mode
    if args.csv_file and args.object:
        csv_path = Path(args.csv_file)
        obj_norm = args.object.lower().replace("_", "").replace("-", "")
        issues: list[str] = []
        if obj_norm == "emailmessage":
            issues = check_email_message_csv(csv_path)
        elif obj_norm == "contentversion":
            issues = check_content_version_csv(csv_path.parent)
        else:
            print(f"No specific checks implemented for object type: {args.object}")
            return 0
    else:
        manifest_dir = Path(args.manifest_dir)
        issues = check_case_history_migration(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
