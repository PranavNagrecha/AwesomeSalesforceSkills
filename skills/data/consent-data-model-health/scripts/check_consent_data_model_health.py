#!/usr/bin/env python3
"""Checker script for Consent Data Model Health skill.

Validates Health Cloud consent hierarchy completeness and AuthorizationFormConsent
field quality by inspecting a Salesforce metadata export or a JSON data export.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_consent_data_model_health.py [--help]
    python3 check_consent_data_model_health.py --manifest-dir path/to/metadata
    python3 check_consent_data_model_health.py --consent-json path/to/consent_records.json

The --consent-json option accepts a JSON array of AuthorizationFormConsent records
exported from SOQL, e.g.:
  sfdx force:data:soql:query -q "SELECT Id, ConsentGiverId, Status,
    ConsentCapturedSource, ConsentCapturedDateTime, AuthorizationFormTextId
    FROM AuthorizationFormConsent" --json > consent_records.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


VALID_STATUS_VALUES = {"Seen", "Signed"}
REQUIRED_FIELDS = {"ConsentGiverId", "AuthorizationFormTextId", "Status",
                   "ConsentCapturedSource", "ConsentCapturedDateTime"}

# Individual IDs start with '005' in Salesforce (User/Contact share prefix,
# but Individual is a distinct object with prefix '005' in standard orgs).
# More precisely, Individual records use the '005' key prefix just like User.
# The practical check here is to flag any ConsentGiverId that looks like a
# Contact ('003') or Account ('001') ID, which are common mis-population errors.
DISALLOWED_CONSENT_GIVER_PREFIXES = {
    "001",  # Account
    "003",  # Contact
    "0015", # Account (15-char)
    "0035", # Contact (15-char)
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Health Cloud consent hierarchy completeness and "
            "AuthorizationFormConsent field quality."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata export (default: current directory).",
    )
    parser.add_argument(
        "--consent-json",
        default=None,
        help=(
            "Path to a JSON file containing an array of AuthorizationFormConsent records "
            "exported from SOQL (sfdx force:data:soql:query --json output)."
        ),
    )
    return parser.parse_args()


def check_manifest_hierarchy(manifest_dir: Path) -> list[str]:
    """Check metadata directory for consent hierarchy completeness.

    Looks for CustomObject XML files confirming that all five hierarchy objects
    exist in the org metadata. This is a structural completeness check.
    """
    issues: list[str] = []

    required_objects = [
        "DataUsePurpose",
        "AuthorizationForm",
        "AuthorizationFormText",
        "AuthorizationFormDataUse",
        "AuthorizationFormConsent",
    ]

    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Try common sfdx project layout
        objects_dir = manifest_dir / "force-app" / "main" / "default" / "objects"

    if not objects_dir.exists():
        issues.append(
            f"No 'objects' directory found under {manifest_dir}. "
            "Cannot verify consent hierarchy object metadata. "
            "Pass a valid Salesforce metadata or sfdx project root."
        )
        return issues

    found_objects = {p.name for p in objects_dir.iterdir() if p.is_dir()}

    for obj in required_objects:
        if obj not in found_objects:
            issues.append(
                f"Missing object metadata: '{obj}' not found in {objects_dir}. "
                "The full five-object consent hierarchy must be present. "
                "Confirm Health Cloud is provisioned and the metadata has been retrieved."
            )

    return issues


def check_consent_records(records: list[dict]) -> list[str]:
    """Validate a list of AuthorizationFormConsent record dicts.

    Checks:
    - Required fields are populated (not null/empty)
    - Status is a valid value (Seen or Signed)
    - ConsentGiverId does not appear to reference a Contact or Account
    - ConsentCapturedSource is populated on Signed records
    - ConsentCapturedDateTime is populated on Signed records
    """
    issues: list[str] = []

    if not records:
        issues.append(
            "No AuthorizationFormConsent records found in input. "
            "Verify the SOQL export and that the org has consent records."
        )
        return issues

    missing_source_count = 0
    missing_datetime_count = 0
    bad_status_count = 0
    bad_giver_count = 0
    missing_text_count = 0

    bad_status_examples: list[str] = []
    bad_giver_examples: list[str] = []

    for record in records:
        record_id = record.get("Id", "<no Id>")

        # Check Status value
        status = record.get("Status")
        if status not in VALID_STATUS_VALUES:
            bad_status_count += 1
            if len(bad_status_examples) < 5:
                bad_status_examples.append(
                    f"  Id={record_id}, Status='{status}'"
                )

        # Check ConsentCapturedSource on Signed records
        if status == "Signed":
            source = record.get("ConsentCapturedSource")
            if not source or str(source).strip() == "" or source == "null":
                missing_source_count += 1

            # Check ConsentCapturedDateTime on Signed records
            captured_dt = record.get("ConsentCapturedDateTime")
            if not captured_dt or str(captured_dt).strip() == "" or captured_dt == "null":
                missing_datetime_count += 1

        # Check ConsentGiverId does not look like a Contact or Account
        giver_id = record.get("ConsentGiverId", "")
        if giver_id:
            # Salesforce IDs are 15 or 18 chars; prefix is the first 3 chars
            prefix_3 = str(giver_id)[:3].lower()
            if prefix_3 in {"001", "003"}:
                bad_giver_count += 1
                if len(bad_giver_examples) < 5:
                    bad_giver_examples.append(
                        f"  Id={record_id}, ConsentGiverId={giver_id} "
                        f"(prefix '{prefix_3}' suggests Contact/Account, not Individual)"
                    )

        # Check AuthorizationFormTextId is populated
        text_id = record.get("AuthorizationFormTextId")
        if not text_id or str(text_id).strip() == "" or text_id == "null":
            missing_text_count += 1

    total = len(records)

    if bad_status_count > 0:
        examples_str = "\n".join(bad_status_examples)
        issues.append(
            f"{bad_status_count}/{total} AuthorizationFormConsent record(s) have an invalid "
            f"Status value. Valid values are exactly 'Seen' or 'Signed' (sentence case). "
            f"Examples:\n{examples_str}"
        )

    if bad_giver_count > 0:
        examples_str = "\n".join(bad_giver_examples)
        issues.append(
            f"{bad_giver_count}/{total} AuthorizationFormConsent record(s) have a "
            "ConsentGiverId that appears to reference a Contact (003) or Account (001) "
            "instead of an Individual. ConsentGiverId must reference the Individual record. "
            f"Examples:\n{examples_str}"
        )

    if missing_source_count > 0:
        issues.append(
            f"{missing_source_count}/{total} AuthorizationFormConsent record(s) with "
            "Status='Signed' are missing ConsentCapturedSource. "
            "This field is required for HIPAA audit trail completeness. "
            "Valid values include: Web, Email, Verbal, Paper."
        )

    if missing_datetime_count > 0:
        issues.append(
            f"{missing_datetime_count}/{total} AuthorizationFormConsent record(s) with "
            "Status='Signed' are missing ConsentCapturedDateTime. "
            "This timestamp is required for HIPAA audit trails."
        )

    if missing_text_count > 0:
        issues.append(
            f"{missing_text_count}/{total} AuthorizationFormConsent record(s) are missing "
            "AuthorizationFormTextId. Each consent record must link to a specific "
            "form version to maintain a complete authorization trail."
        )

    return issues


def load_consent_json(consent_json_path: Path) -> list[dict]:
    """Load consent records from a JSON file.

    Accepts both a bare JSON array and the sfdx --json output format:
    {"status": 0, "result": {"records": [...]}}
    """
    with open(consent_json_path, encoding="utf-8") as f:
        data = json.load(f)

    # sfdx --json output wraps records under result.records
    if isinstance(data, dict):
        if "result" in data and "records" in data["result"]:
            return data["result"]["records"]
        if "records" in data:
            return data["records"]
        # Single record wrapped in dict
        return [data]

    if isinstance(data, list):
        return data

    return []


def main() -> int:
    args = parse_args()
    issues: list[str] = []

    ran_any_check = False

    # Check metadata hierarchy if manifest dir provided (or default)
    if args.manifest_dir is not None:
        manifest_dir = Path(args.manifest_dir)
        ran_any_check = True
        if not manifest_dir.exists():
            issues.append(f"Manifest directory not found: {manifest_dir}")
        else:
            issues.extend(check_manifest_hierarchy(manifest_dir))

    # Check consent records if JSON file provided
    if args.consent_json is not None:
        consent_json_path = Path(args.consent_json)
        ran_any_check = True
        if not consent_json_path.exists():
            issues.append(f"Consent JSON file not found: {consent_json_path}")
        else:
            try:
                records = load_consent_json(consent_json_path)
                issues.extend(check_consent_records(records))
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                issues.append(f"Failed to parse consent JSON: {exc}")

    if not ran_any_check:
        # Default: run hierarchy check against current directory
        manifest_dir = Path(".")
        issues.extend(check_manifest_hierarchy(manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
