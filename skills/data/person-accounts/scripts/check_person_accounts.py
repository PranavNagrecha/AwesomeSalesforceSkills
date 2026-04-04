#!/usr/bin/env python3
"""Checker script for Person Accounts skill.

Scans Salesforce metadata XML for common Person Account issues:
- Apex classes/triggers that query Contact without IsPersonAccount filters
- Apex classes/triggers that use IsPersonAccount in before-insert context without RecordTypeId fallback
- Apex classes that attempt to insert Contact records linked to accounts (potential Person Account violation)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_person_accounts.py [--help]
    python3 check_person_accounts.py --manifest-dir path/to/metadata
    python3 check_person_accounts.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# Patterns that indicate potential Person Account issues in Apex
_CONTACT_SOQL_NO_PERSON_FILTER = re.compile(
    r"""FROM\s+Contact\b(?![^'\"]*IsPersonAccount)""",
    re.IGNORECASE,
)

_BEFORE_INSERT_BLOCK = re.compile(
    r"""before\s+insert""",
    re.IGNORECASE,
)

_IS_PERSON_ACCOUNT_CHECK = re.compile(
    r"""\.IsPersonAccount\b""",
    re.IGNORECASE,
)

_RECORD_TYPE_ID_FALLBACK = re.compile(
    r"""RecordTypeId""",
    re.IGNORECASE,
)

_INSERT_CONTACT = re.compile(
    r"""insert\s+\w*[Cc]ontact\b""",
)

_ACCOUNT_ID_ON_CONTACT = re.compile(
    r"""AccountId\s*=\s*\w*[Aa]ccount""",
)


def _read_file_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_apex_files(manifest_dir: Path) -> list[str]:
    """Scan .cls and .trigger files for Person Account issues."""
    issues: list[str] = []

    apex_extensions = ("*.cls", "*.trigger")
    apex_files: list[Path] = []
    for ext in apex_extensions:
        apex_files.extend(manifest_dir.rglob(ext))

    if not apex_files:
        return issues

    for apex_path in sorted(apex_files):
        content = _read_file_text(apex_path)
        rel = apex_path.relative_to(manifest_dir)

        # Check 1: Contact SOQL without IsPersonAccount awareness
        soql_matches = list(_CONTACT_SOQL_NO_PERSON_FILTER.finditer(content))
        if soql_matches:
            for match in soql_matches:
                line_no = content[: match.start()].count("\n") + 1
                issues.append(
                    f"{rel}:{line_no} — Contact SOQL missing IsPersonAccount filter. "
                    f"In a Person Account org, 'FROM Contact' returns PersonContact records. "
                    f"Add 'AND Account.IsPersonAccount = false' or branch explicitly."
                )

        # Check 2: IsPersonAccount used in a file that also contains 'before insert'
        # without a RecordTypeId fallback — potential null-check bug
        if (
            _BEFORE_INSERT_BLOCK.search(content)
            and _IS_PERSON_ACCOUNT_CHECK.search(content)
            and not _RECORD_TYPE_ID_FALLBACK.search(content)
        ):
            issues.append(
                f"{rel} — File contains 'before insert' trigger context and checks "
                f"'IsPersonAccount' but has no 'RecordTypeId' fallback. "
                f"IsPersonAccount is null in before-insert context; use RecordTypeId to detect "
                f"Person Account record types at insert time."
            )

        # Check 3: Potential attempt to insert a Contact linked to an Account
        # (may violate Person Account constraint if Account is a Person Account)
        if _INSERT_CONTACT.search(content) and _ACCOUNT_ID_ON_CONTACT.search(content):
            insert_match = _INSERT_CONTACT.search(content)
            line_no = content[: insert_match.start()].count("\n") + 1
            issues.append(
                f"{rel}:{line_no} — File inserts a Contact and sets AccountId from an Account. "
                f"Verify this code does not run against Person Account records — "
                f"inserting a Contact with a Person Account's AccountId raises FIELD_INTEGRITY_EXCEPTION."
            )

    return issues


def check_record_types(manifest_dir: Path) -> list[str]:
    """Check that at least one Account RecordType is present (prerequisite for Person Accounts)."""
    issues: list[str] = []

    # Look for Account object metadata
    account_object_files = list(manifest_dir.rglob("Account.object-meta.xml")) + list(
        manifest_dir.rglob("Account.object")
    )

    if not account_object_files:
        # No Account object file found — not necessarily an issue (partial metadata)
        return issues

    for obj_file in account_object_files:
        content = _read_file_text(obj_file)
        if "<recordTypes>" not in content and "<recordType>" not in content:
            issues.append(
                f"{obj_file.relative_to(manifest_dir)} — Account object metadata has no "
                f"recordTypes defined. Person Accounts require at least one Account Record Type "
                f"designated as a Person Account type."
            )

    return issues


def check_duplicate_rules(manifest_dir: Path) -> list[str]:
    """Warn if Account DuplicateRule files exist without an IsPersonAccount condition."""
    issues: list[str] = []

    dup_rule_files = list(manifest_dir.rglob("*.duplicateRule-meta.xml")) + list(
        manifest_dir.rglob("*.duplicateRule")
    )

    for rule_file in dup_rule_files:
        content = _read_file_text(rule_file)
        # Only flag Account duplicate rules
        if "<sObjectType>Account</sObjectType>" not in content:
            continue
        if "IsPersonAccount" not in content:
            rel = rule_file.relative_to(manifest_dir)
            issues.append(
                f"{rel} — Account Duplicate Rule does not reference IsPersonAccount. "
                f"In a Person Account org, separate duplicate rules are recommended for "
                f"Person Accounts and Business Accounts to avoid false positive/negative matches."
            )

    return issues


def check_person_accounts(manifest_dir: Path) -> list[str]:
    """Run all Person Account checks against the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_apex_files(manifest_dir))
    issues.extend(check_record_types(manifest_dir))
    issues.extend(check_duplicate_rules(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common Person Account issues: "
            "Contact SOQL without IsPersonAccount filters, before-insert IsPersonAccount checks "
            "without RecordTypeId fallback, Contact inserts that may violate Person Account constraints, "
            "missing Account Record Types, and Duplicate Rules missing IsPersonAccount conditions."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_person_accounts(manifest_dir)

    if not issues:
        print("No Person Account issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
