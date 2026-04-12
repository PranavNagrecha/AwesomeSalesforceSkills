#!/usr/bin/env python3
"""Checker script for Data Cloud Architecture skill.

Validates Data Cloud architecture design artifacts and metadata for common
architecture issues: DMO mapping completeness, identity resolution ruleset
configuration, and activation target pre-flight requirements.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_architecture.py [--help]
    python3 check_data_cloud_architecture.py --manifest-dir path/to/metadata
    python3 check_data_cloud_architecture.py --mapping-csv path/to/dmo_mapping.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# DMO types that qualify a source record for identity resolution participation.
# A data source must map at least one field to one of these DMOs to contribute
# to Unified Individual clusters.
IDENTITY_ELIGIBLE_DMOS = {
    "ContactPointEmail",
    "ContactPointPhone",
    "PartyIdentification",
}

# Fields required on each identity-eligible DMO for the match to be valid.
REQUIRED_DMO_FIELDS = {
    "ContactPointEmail": {"emailAddress"},
    "ContactPointPhone": {"telephoneNumber"},
    "PartyIdentification": {"partyIdentificationNumber", "partyIdentificationType"},
}

# Reconciliation rule values that are valid in Data Cloud.
VALID_RECONCILIATION_RULES = {"Most Frequent", "Most Recent", "Source Priority"}

# Minimum number of match rules recommended for a production ruleset.
MIN_MATCH_RULES = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> dict | list | None:
    """Load a JSON file and return its contents, or None on failure."""
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    """Load a CSV file and return rows as list of dicts."""
    try:
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            return list(reader)
    except OSError:
        return []


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_dmo_mapping_csv(csv_path: Path) -> list[str]:
    """Validate a DMO mapping CSV for identity resolution eligibility.

    Expected CSV columns:
      source_name, source_field, dmo_name, dmo_field

    Checks:
    - At least one row maps to an identity-eligible DMO per source.
    - Required fields are present on each identity-eligible DMO mapping.
    """
    issues: list[str] = []
    rows = _load_csv_rows(csv_path)

    if not rows:
        issues.append(
            f"DMO mapping CSV is empty or unreadable: {csv_path}. "
            "Provide a CSV with columns: source_name, source_field, dmo_name, dmo_field."
        )
        return issues

    required_columns = {"source_name", "source_field", "dmo_name", "dmo_field"}
    actual_columns = set(rows[0].keys()) if rows else set()
    missing_cols = required_columns - actual_columns
    if missing_cols:
        issues.append(
            f"DMO mapping CSV is missing required columns: {sorted(missing_cols)}. "
            f"Found columns: {sorted(actual_columns)}."
        )
        return issues

    # Group rows by source
    sources: dict[str, list[dict]] = {}
    for row in rows:
        src = row.get("source_name", "").strip()
        if src:
            sources.setdefault(src, []).append(row)

    for source_name, source_rows in sources.items():
        mapped_dmos: dict[str, set[str]] = {}
        for row in source_rows:
            dmo = row.get("dmo_name", "").strip()
            field = row.get("dmo_field", "").strip()
            if dmo:
                mapped_dmos.setdefault(dmo, set()).add(field)

        # Check identity resolution eligibility
        eligible = IDENTITY_ELIGIBLE_DMOS & set(mapped_dmos.keys())
        if not eligible:
            issues.append(
                f"Source '{source_name}' has no mapping to an identity-resolution-eligible DMO. "
                f"Map at least one field to ContactPointEmail, ContactPointPhone, or "
                f"PartyIdentification. This source will not contribute to Unified Individual clusters."
            )
        else:
            # Check required fields on each eligible DMO
            for dmo in eligible:
                required_fields = REQUIRED_DMO_FIELDS.get(dmo, set())
                mapped_fields = mapped_dmos.get(dmo, set())
                missing_fields = required_fields - mapped_fields
                if missing_fields:
                    issues.append(
                        f"Source '{source_name}' maps to '{dmo}' but is missing required "
                        f"field(s): {sorted(missing_fields)}. "
                        f"Without these fields, identity resolution matching will not function "
                        f"correctly for this source."
                    )

            # Special check: PartyIdentification requires both number and type
            if "PartyIdentification" in mapped_dmos:
                pi_fields = mapped_dmos["PartyIdentification"]
                if "partyIdentificationNumber" in pi_fields and "partyIdentificationType" not in pi_fields:
                    issues.append(
                        f"Source '{source_name}' maps PartyIdentification.partyIdentificationNumber "
                        f"but not partyIdentificationType. Both fields are required. Without "
                        f"partyIdentificationType, the ID cannot be scoped to a specific system "
                        f"and match rules cannot filter by ID type."
                    )

    return issues


def check_identity_resolution_json(ir_config_path: Path) -> list[str]:
    """Validate an identity resolution configuration JSON file.

    Expected JSON structure:
    {
      "rulesetName": "string",
      "matchRules": [
        {"ruleName": "string", "matchType": "Exact|Fuzzy|Normalized|Compound",
         "dmoName": "string", "fieldName": "string"}
      ],
      "reconciliationRules": [
        {"fieldName": "string", "rule": "Most Frequent|Most Recent|Source Priority"}
      ]
    }
    """
    issues: list[str] = []
    config = _load_json(ir_config_path)

    if config is None:
        issues.append(
            f"Identity resolution config file is missing or invalid JSON: {ir_config_path}"
        )
        return issues

    if not isinstance(config, dict):
        issues.append(f"Identity resolution config must be a JSON object: {ir_config_path}")
        return issues

    # Check match rules
    match_rules = config.get("matchRules", [])
    if len(match_rules) < MIN_MATCH_RULES:
        issues.append(
            f"Identity resolution ruleset has {len(match_rules)} match rule(s). "
            f"At least {MIN_MATCH_RULES} match rule is required. A ruleset with no match rules "
            f"will produce no Unified Individual clusters."
        )

    for i, rule in enumerate(match_rules):
        if not isinstance(rule, dict):
            continue
        dmo = rule.get("dmoName", "")
        if dmo and dmo not in IDENTITY_ELIGIBLE_DMOS:
            issues.append(
                f"Match rule {i + 1} ('{rule.get('ruleName', 'unnamed')}') targets DMO "
                f"'{dmo}' which is not identity-resolution-eligible. Match rules must target "
                f"ContactPointEmail, ContactPointPhone, or PartyIdentification."
            )
        match_type = rule.get("matchType", "")
        if match_type == "Fuzzy" and i == 0:
            issues.append(
                f"Match rule 1 ('{rule.get('ruleName', 'unnamed')}') uses Fuzzy matching as "
                f"the primary rule. Fuzzy matching as the primary rule risks false identity "
                f"merges through transitive matching. Prefer Exact or Normalized matching on "
                f"a unique identifier (email, phone, loyalty ID) as the primary rule."
            )

    # Check reconciliation rules
    recon_rules = config.get("reconciliationRules", [])
    for rule in recon_rules:
        if not isinstance(rule, dict):
            continue
        rule_type = rule.get("rule", "")
        if rule_type and rule_type not in VALID_RECONCILIATION_RULES:
            issues.append(
                f"Reconciliation rule for field '{rule.get('fieldName', 'unknown')}' has "
                f"invalid rule type '{rule_type}'. "
                f"Valid values: {sorted(VALID_RECONCILIATION_RULES)}."
            )

    return issues


def check_activation_targets_json(targets_path: Path) -> list[str]:
    """Validate an activation targets configuration JSON.

    Expected JSON structure:
    {
      "activationTargets": [
        {"targetName": "string", "targetType": "string",
         "connectionStatus": "Connected|Pending|Error",
         "lastVerified": "YYYY-MM-DD"}
      ]
    }
    """
    issues: list[str] = []
    config = _load_json(targets_path)

    if config is None:
        issues.append(
            f"Activation targets config file is missing or invalid JSON: {targets_path}"
        )
        return issues

    if not isinstance(config, dict):
        issues.append(
            f"Activation targets config must be a JSON object: {targets_path}"
        )
        return issues

    targets = config.get("activationTargets", [])
    if not targets:
        issues.append(
            "No activation targets defined. At least one activation target is required "
            "before publishing segments."
        )
        return issues

    for target in targets:
        if not isinstance(target, dict):
            continue
        name = target.get("targetName", "unnamed")
        status = target.get("connectionStatus", "")
        if status != "Connected":
            issues.append(
                f"Activation target '{name}' has connection status '{status}'. "
                f"Status must be 'Connected' before any segment can be published to this target. "
                f"Re-authenticate the target and verify the connection."
            )
        if not target.get("lastVerified"):
            issues.append(
                f"Activation target '{name}' has no lastVerified date. "
                f"Authentication should be tested and the verification date recorded "
                f"before go-live. Ad platform tokens expire — track token age."
            )

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Run general manifest directory checks for Data Cloud architecture artifacts."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Look for common Data Cloud architecture config files
    dmo_mapping_candidates = list(manifest_dir.glob("*dmo*mapping*.csv")) + list(
        manifest_dir.glob("*mapping*.csv")
    )
    ir_config_candidates = list(manifest_dir.glob("*identity*resolution*.json")) + list(
        manifest_dir.glob("*ir*config*.json")
    )
    activation_candidates = list(manifest_dir.glob("*activation*target*.json")) + list(
        manifest_dir.glob("*activation*.json")
    )

    if dmo_mapping_candidates:
        for path in dmo_mapping_candidates:
            issues.extend(check_dmo_mapping_csv(path))
    else:
        issues.append(
            "No DMO mapping CSV found in manifest directory. "
            "Expected a file matching '*dmo*mapping*.csv' or '*mapping*.csv'. "
            "DMO mapping documentation is required to verify identity resolution eligibility."
        )

    if ir_config_candidates:
        for path in ir_config_candidates:
            issues.extend(check_identity_resolution_json(path))

    if activation_candidates:
        for path in activation_candidates:
            issues.extend(check_activation_targets_json(path))

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Data Cloud Architecture design artifacts for common issues: "
            "DMO mapping completeness, identity resolution ruleset configuration, "
            "and activation target pre-flight readiness."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory containing Data Cloud architecture artifacts (CSV and JSON config files).",
    )
    parser.add_argument(
        "--mapping-csv",
        default=None,
        help="Path to a DMO mapping CSV file (columns: source_name, source_field, dmo_name, dmo_field).",
    )
    parser.add_argument(
        "--ir-config",
        default=None,
        help="Path to an identity resolution configuration JSON file.",
    )
    parser.add_argument(
        "--activation-targets",
        default=None,
        help="Path to an activation targets configuration JSON file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    all_issues: list[str] = []

    if args.mapping_csv:
        all_issues.extend(check_dmo_mapping_csv(Path(args.mapping_csv)))

    if args.ir_config:
        all_issues.extend(check_identity_resolution_json(Path(args.ir_config)))

    if args.activation_targets:
        all_issues.extend(check_activation_targets_json(Path(args.activation_targets)))

    if args.manifest_dir:
        all_issues.extend(check_manifest_dir(Path(args.manifest_dir)))

    if not (args.manifest_dir or args.mapping_csv or args.ir_config or args.activation_targets):
        # Default: check current directory
        all_issues.extend(check_manifest_dir(Path(".")))

    if not all_issues:
        print("No issues found.")
        return 0

    for issue in all_issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
