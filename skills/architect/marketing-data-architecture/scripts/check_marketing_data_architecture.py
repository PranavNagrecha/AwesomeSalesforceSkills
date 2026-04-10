#!/usr/bin/env python3
"""Checker script for Marketing Data Architecture skill.

Validates Marketing Cloud data architecture design artifacts — specifically
JSON or YAML data model definition files — against common anti-patterns.

Checks performed:
  1. Wide DE warning: flags any DE with more than 200 columns defined
  2. Missing sendable DE: warns if no DE is marked as sendable
  3. Missing Send Relationship on sendable DEs
  4. Email-as-SubscriberKey anti-pattern: warns if email field is set as PK on a sendable DE
  5. Missing Contact Key field on sendable DEs
  6. Missing Data Relationships section in the model

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_marketing_data_architecture.py [--help]
    python3 check_marketing_data_architecture.py --model path/to/data_model.json
    python3 check_marketing_data_architecture.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WIDE_DE_COLUMN_THRESHOLD = 200
CONTACT_KEY_ALIASES = {"contactkey", "subscriberkey", "contact_key", "subscriber_key"}
EMAIL_FIELD_ALIASES = {"email", "emailaddress", "email_address"}


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Marketing Cloud data architecture design artifacts for common issues."
        ),
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Path to a JSON data model file describing DEs (optional).",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of Salesforce/MC metadata to scan (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# JSON model checks
# ---------------------------------------------------------------------------


def check_model_file(model_path: Path) -> list[str]:
    """Parse a JSON data model file and return a list of issue strings.

    Expected model shape (example):
    {
      "data_extensions": [
        {
          "name": "Contacts_DE",
          "sendable": true,
          "send_relationship": {"field": "ContactKey", "maps_to": "Subscriber Key"},
          "columns": [
            {"name": "ContactKey", "type": "Text", "primary_key": true},
            {"name": "EmailAddress", "type": "Email"},
            ...
          ]
        }
      ],
      "data_relationships": [
        {"source_de": "Contacts_DE", "source_field": "ContactKey",
         "target_de": "Orders_DE", "target_field": "ContactKey"}
      ]
    }
    """
    issues: list[str] = []

    if not model_path.exists():
        issues.append(f"Model file not found: {model_path}")
        return issues

    try:
        with model_path.open("r", encoding="utf-8") as fh:
            model: dict[str, Any] = json.load(fh)
    except json.JSONDecodeError as exc:
        issues.append(f"Cannot parse model file as JSON: {exc}")
        return issues

    data_extensions: list[dict[str, Any]] = model.get("data_extensions", [])
    if not data_extensions:
        issues.append(
            "Model file has no 'data_extensions' key or it is empty — "
            "cannot validate DE design."
        )
        return issues

    has_sendable = False
    has_relationships = bool(model.get("data_relationships"))

    for de in data_extensions:
        de_name = de.get("name", "<unnamed>")
        columns: list[dict[str, Any]] = de.get("columns", [])
        sendable: bool = de.get("sendable", False)

        # Check 1: Wide DE
        if len(columns) > WIDE_DE_COLUMN_THRESHOLD:
            issues.append(
                f"DE '{de_name}' has {len(columns)} columns — exceeds the "
                f"~{WIDE_DE_COLUMN_THRESHOLD}-column threshold. Query performance "
                "will degrade; consider normalizing into multiple DEs."
            )

        if sendable:
            has_sendable = True

            # Check 2: Sendable DE missing Send Relationship
            send_rel = de.get("send_relationship")
            if not send_rel:
                issues.append(
                    f"Sendable DE '{de_name}' has no 'send_relationship' defined. "
                    "A Send Relationship mapping a DE field to All Subscribers "
                    "Subscriber Key is required for the DE to be used as a send audience."
                )
            else:
                rel_field = send_rel.get("field", "")
                maps_to = send_rel.get("maps_to", "")
                if not rel_field:
                    issues.append(
                        f"Sendable DE '{de_name}': send_relationship.field is empty."
                    )
                if "subscriber" not in maps_to.lower() and "email" not in maps_to.lower():
                    issues.append(
                        f"Sendable DE '{de_name}': send_relationship.maps_to is "
                        f"'{maps_to}' — expected 'Subscriber Key' or 'Email Address'."
                    )

            # Check 3: Email address as PK on sendable DE (anti-pattern)
            pk_columns = [
                c for c in columns if c.get("primary_key", False)
            ]
            pk_names_lower = {c.get("name", "").lower().replace(" ", "") for c in pk_columns}
            if pk_names_lower & EMAIL_FIELD_ALIASES:
                issues.append(
                    f"Sendable DE '{de_name}': an email field is marked as the primary key. "
                    "Email addresses are not unique in All Subscribers. Use Contact Key "
                    "(SubscriberKey) as the primary key and join key instead."
                )

            # Check 4: No Contact Key field on sendable DE
            col_names_lower = {c.get("name", "").lower().replace(" ", "") for c in columns}
            if not (col_names_lower & CONTACT_KEY_ALIASES):
                issues.append(
                    f"Sendable DE '{de_name}' does not appear to have a Contact Key "
                    "/ SubscriberKey field (checked for common aliases: "
                    f"{sorted(CONTACT_KEY_ALIASES)}). A Contact Key field is required "
                    "for the Send Relationship and for cross-DE joins."
                )

    # Check 5: No sendable DE at all
    if not has_sendable:
        issues.append(
            "No sendable DE found in the model. At least one DE must be marked "
            "'sendable: true' with a Send Relationship to All Subscribers for "
            "email sends to be possible."
        )

    # Check 6: Multi-DE model missing Data Relationships
    if len(data_extensions) > 1 and not has_relationships:
        issues.append(
            f"Model has {len(data_extensions)} DEs but no 'data_relationships' are defined. "
            "Data Relationships in Contact Builder are required for audience builder "
            "traversals and Journey Builder decision splits that reference related DE data. "
            "Define relationships for every DE-to-DE join in the model."
        )

    return issues


# ---------------------------------------------------------------------------
# Manifest directory checks (heuristic scan for common issues in file names /
# directory structure — stdlib only, no metadata parsing)
# ---------------------------------------------------------------------------


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Heuristic checks against a metadata directory.

    Without a data model file this function looks for signals that suggest
    known anti-patterns (e.g., a very large number of JSON/CSV files that
    might indicate unarchived staging DEs, or absence of a data model doc).
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for a data model JSON/YAML file — its absence is a documentation gap
    model_files = list(manifest_dir.rglob("data_model*.json")) + list(
        manifest_dir.rglob("data_model*.yaml")
    )
    if not model_files:
        issues.append(
            "No 'data_model*.json' or 'data_model*.yaml' file found under "
            f"{manifest_dir}. A documented data model is required for this skill. "
            "Use --model to point to a specific file for detailed DE validation."
        )

    # Check for suspiciously large numbers of CSV staging files (signals unbounded DE growth)
    csv_files = list(manifest_dir.rglob("*.csv"))
    if len(csv_files) > 50:
        issues.append(
            f"Found {len(csv_files)} CSV files under {manifest_dir}. "
            "Large numbers of staging CSV files may indicate that old import files "
            "are not being archived, which can complicate data lineage and auditing."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.model:
        model_path = Path(args.model)
        all_issues.extend(check_model_file(model_path))
    else:
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_manifest_dir(manifest_dir))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
