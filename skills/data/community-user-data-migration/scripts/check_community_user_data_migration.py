#!/usr/bin/env python3
"""Checker script for Community User Data Migration skill.

Inspects a CSV file intended for community user migration and checks for
common issues that cause bulk User insert/update failures in Salesforce.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_community_user_data_migration.py [--help]
    python3 check_community_user_data_migration.py --csv path/to/users.csv
    python3 check_community_user_data_migration.py --csv users.csv --operation insert
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

VALID_USER_TYPES = {
    "PowerCustomerSuccess",
    "PowerCustomerSuccessPortal",
    "PowerPartner",
    "CspLitePortal",
}

REQUIRED_INSERT_FIELDS = {
    "ContactId",
    "ProfileId",
    "UserType",
    "Username",
    "Email",
    "FirstName",
    "LastName",
    "Alias",
    "TimeZoneSidKey",
    "LocaleSidKey",
    "EmailEncodingKey",
    "LanguageLocaleKey",
    "IsActive",
}

REQUIRED_UPDATE_FIELDS = {
    "Id",
    "ProfileId",
}

IMMUTABLE_FIELDS = {"UserType"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check a community user migration CSV for common issues.",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Path to the User migration CSV file to inspect.",
    )
    parser.add_argument(
        "--operation",
        choices=["insert", "update"],
        default="insert",
        help="Data Loader operation type: insert (default) or update.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce metadata (unused; kept for interface compatibility).",
    )
    return parser.parse_args()


def check_csv(csv_path: Path, operation: str) -> list[str]:
    """Inspect a migration CSV and return a list of issue strings."""
    issues: list[str] = []

    if not csv_path.exists():
        issues.append(f"CSV file not found: {csv_path}")
        return issues

    try:
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                issues.append("CSV appears to be empty or has no header row.")
                return issues

            headers = set(reader.fieldnames)

            # --- Field presence checks ---
            if operation == "insert":
                missing = REQUIRED_INSERT_FIELDS - headers
                if missing:
                    issues.append(
                        f"INSERT: Missing required columns: {', '.join(sorted(missing))}"
                    )
            elif operation == "update":
                missing = REQUIRED_UPDATE_FIELDS - headers
                if missing:
                    issues.append(
                        f"UPDATE: Missing required columns: {', '.join(sorted(missing))}"
                    )
                if "UserType" in headers:
                    issues.append(
                        "UPDATE: 'UserType' column detected. UserType is immutable after User "
                        "creation — remove this column. License migration must be done via "
                        "ProfileId update only."
                    )

            # --- Row-level checks ---
            usernames: list[str] = []
            rows_checked = 0

            for row_num, row in enumerate(reader, start=2):
                rows_checked += 1

                # ContactId blank check (insert only)
                if operation == "insert" and "ContactId" in headers:
                    contact_id = (row.get("ContactId") or "").strip()
                    if not contact_id:
                        issues.append(
                            f"Row {row_num}: ContactId is blank. Every external User insert "
                            "requires a valid ContactId referencing an existing Contact."
                        )

                # UserType value check (insert only)
                if operation == "insert" and "UserType" in headers:
                    user_type = (row.get("UserType") or "").strip()
                    if user_type and user_type not in VALID_USER_TYPES:
                        issues.append(
                            f"Row {row_num}: Unrecognised UserType '{user_type}'. "
                            f"Valid values: {', '.join(sorted(VALID_USER_TYPES))}."
                        )

                # Username uniqueness within the file
                if "Username" in headers:
                    username = (row.get("Username") or "").strip().lower()
                    if username:
                        usernames.append(username)

                # Sandbox username suffix warning
                if "Username" in headers:
                    raw_username = (row.get("Username") or "").strip()
                    for suffix in (".sandbox", ".dev", ".uat", ".qa", ".staging", ".invalid"):
                        if raw_username.lower().endswith(suffix):
                            issues.append(
                                f"Row {row_num}: Username '{raw_username}' ends with sandbox "
                                f"suffix '{suffix}'. Sandbox usernames must be scrubbed before "
                                "use in a production migration."
                            )
                            break

                # IsActive value check
                if "IsActive" in headers:
                    is_active = (row.get("IsActive") or "").strip().lower()
                    if is_active and is_active not in ("true", "false", "1", "0"):
                        issues.append(
                            f"Row {row_num}: IsActive value '{is_active}' is not a recognised "
                            "boolean. Use 'true' or 'false'."
                        )

            # Duplicate Username check within the file
            seen: set[str] = set()
            duplicates: set[str] = set()
            for uname in usernames:
                if uname in seen:
                    duplicates.add(uname)
                seen.add(uname)
            if duplicates:
                issues.append(
                    f"Duplicate Usernames detected within the CSV "
                    f"({len(duplicates)} value(s)): {', '.join(sorted(duplicates)[:5])}..."
                )

            if rows_checked == 0:
                issues.append("CSV header is present but the file contains no data rows.")

    except csv.Error as exc:
        issues.append(f"CSV parse error: {exc}")

    return issues


def main() -> int:
    args = parse_args()

    if args.csv is None:
        print(
            "No --csv file specified. Pass --csv path/to/users.csv to inspect a migration file.",
            file=sys.stderr,
        )
        print(
            "Run with --help for usage information.",
            file=sys.stderr,
        )
        return 1

    csv_path = Path(args.csv)
    issues = check_csv(csv_path, args.operation)

    if not issues:
        print(f"No issues found in {csv_path} ({args.operation} operation).")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
