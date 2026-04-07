#!/usr/bin/env python3
"""Checker script for Subscriber Data Management skill.

Checks Marketing Cloud subscriber configuration artifacts and metadata exports
for common subscriber identity and compliance issues.
Uses stdlib only — no pip dependencies.

Usage:
    python3 check_subscriber_data_management.py [--help]
    python3 check_subscriber_data_management.py --manifest-dir path/to/metadata
    python3 check_subscriber_data_management.py --subscribers-csv path/to/all_subscribers.csv
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

# Regex: valid 18-character Salesforce ID (alphanumeric, case-sensitive)
SF_ID_PATTERN = re.compile(r'^[a-zA-Z0-9]{18}$')

# Email pattern for detecting email-as-key usage (permissive — catches @domain)
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# Status values that indicate a subscriber cannot receive sends
BLOCKED_STATUSES = {'unsubscribed', 'held', 'bounced'}

# Minimum fraction of non-blocked subscribers expected in a healthy list
HEALTHY_ACTIVE_THRESHOLD = 0.70

# Maximum fraction of Held subscribers before a review is flagged
HELD_FRACTION_WARNING = 0.05


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Marketing Cloud subscriber data management configuration "
            "for common identity, compliance, and deliverability issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata (optional).",
    )
    parser.add_argument(
        "--subscribers-csv",
        default=None,
        help=(
            "Path to an exported All Subscribers CSV file with columns: "
            "SubscriberKey, EmailAddress, Status (optional)."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Check: metadata directory
# ---------------------------------------------------------------------------

def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Check metadata directory for subscriber-relevant artifacts."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for any sendable DE definitions (XML metadata)
    de_files = list(manifest_dir.rglob("*.object"))
    if de_files:
        for de_file in de_files:
            content = de_file.read_text(encoding="utf-8", errors="replace")
            # Warn if any DE definition references "EmailAddress" as a key field
            # (heuristic: looks for EmailAddress in a primaryKey or externalId context)
            if "EmailAddress" in content and (
                "primaryKey" in content or "externalId" in content
            ):
                issues.append(
                    f"Possible email-as-key pattern in DE definition: {de_file.name}. "
                    "Verify SubscriberKey is mapped to CRM Contact/Lead ID, not EmailAddress."
                )

    return issues


# ---------------------------------------------------------------------------
# Check: subscribers CSV export
# ---------------------------------------------------------------------------

def check_subscribers_csv(csv_path: Path) -> list[str]:
    """Parse an All Subscribers CSV export and check for common issues."""
    issues: list[str] = []

    if not csv_path.exists():
        issues.append(f"Subscribers CSV not found: {csv_path}")
        return issues

    rows: list[dict] = []
    try:
        with csv_path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]
            required = {"subscriberkey", "emailaddress", "status"}
            missing = required - set(fieldnames)
            if missing:
                issues.append(
                    f"Subscribers CSV is missing required columns: {', '.join(sorted(missing))}. "
                    "Expected: SubscriberKey, EmailAddress, Status."
                )
                return issues
            for row in reader:
                # Normalize keys to lowercase for consistent access
                rows.append({k.strip().lower(): v.strip() for k, v in row.items()})
    except Exception as exc:  # noqa: BLE001
        issues.append(f"Could not parse subscribers CSV: {exc}")
        return issues

    if not rows:
        issues.append("Subscribers CSV is empty — no subscriber records found.")
        return issues

    total = len(rows)
    email_as_key_count = 0
    held_count = 0
    unsubscribed_count = 0
    bounced_count = 0
    active_count = 0
    invalid_key_count = 0

    for row in rows:
        key = row.get("subscriberkey", "")
        email = row.get("emailaddress", "")
        status = row.get("status", "").lower()

        # Check: email-as-key pattern
        if EMAIL_PATTERN.match(key):
            email_as_key_count += 1

        # Check: key is not a valid 18-char SF ID (but also not an email — flag separately)
        elif key and not SF_ID_PATTERN.match(key):
            invalid_key_count += 1

        # Tally statuses
        if status == "held":
            held_count += 1
        elif status == "unsubscribed":
            unsubscribed_count += 1
        elif status == "bounced":
            bounced_count += 1
        elif status == "active":
            active_count += 1

    # --- Report email-as-key issues ---
    if email_as_key_count > 0:
        pct = email_as_key_count / total * 100
        issues.append(
            f"Email-as-Subscriber-Key detected: {email_as_key_count} of {total} records "
            f"({pct:.1f}%) use an email address as SubscriberKey. "
            "Best practice is to use the 18-character CRM Contact/Lead ID. "
            "Engage Salesforce Support for a Subscriber Key migration."
        )

    if invalid_key_count > 0:
        issues.append(
            f"Non-standard SubscriberKey format: {invalid_key_count} of {total} records "
            "have keys that are neither email addresses nor 18-character Salesforce IDs. "
            "Verify the Subscriber Key strategy is intentional and documented."
        )

    # --- Report Held subscriber fraction ---
    if total > 0:
        held_fraction = held_count / total
        if held_fraction > HELD_FRACTION_WARNING:
            issues.append(
                f"High Held subscriber rate: {held_count} of {total} records "
                f"({held_fraction * 100:.1f}%) have Held status. "
                "Held subscribers are permanently suppressed from all sends. "
                "Review _Bounce Data View to investigate bounce reasons and reactivate "
                "false positives with documented evidence."
            )

    # --- Report overall active rate ---
    if total > 0:
        active_fraction = active_count / total
        if active_fraction < HEALTHY_ACTIVE_THRESHOLD:
            blocked = held_count + unsubscribed_count + bounced_count
            issues.append(
                f"Low active subscriber rate: {active_count} of {total} records "
                f"({active_fraction * 100:.1f}%) are Active. "
                f"{blocked} records are blocked (Held: {held_count}, "
                f"Unsubscribed: {unsubscribed_count}, Bounced: {bounced_count}). "
                "Investigate list health and confirm suppression records are legitimate."
            )

    if not issues:
        # Summary line when all checks pass
        print(
            f"Subscriber data check passed: {total} records reviewed. "
            f"Active: {active_count}, Held: {held_count}, "
            f"Unsubscribed: {unsubscribed_count}, Bounced: {bounced_count}."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_manifest_dir(manifest_dir))

    if args.subscribers_csv:
        csv_path = Path(args.subscribers_csv)
        all_issues.extend(check_subscribers_csv(csv_path))

    if not args.manifest_dir and not args.subscribers_csv:
        print(
            "No inputs provided. Run with --help to see available options.\n"
            "  --manifest-dir   Check Salesforce metadata directory\n"
            "  --subscribers-csv  Check exported All Subscribers CSV",
            file=sys.stderr,
        )
        return 2

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
