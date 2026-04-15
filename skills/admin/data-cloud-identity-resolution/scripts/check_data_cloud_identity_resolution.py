#!/usr/bin/env python3
"""Checker script for Data Cloud Identity Resolution skill.

Validates identity resolution ruleset configuration files for common issues
documented in the skill's gotchas and well-architected references.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_data_cloud_identity_resolution.py [--help]
    python3 check_data_cloud_identity_resolution.py --manifest-dir path/to/metadata

The script scans for JSON/YAML/XML files that describe identity resolution
ruleset configuration (exported from Data Cloud or written as IaC) and
checks them against known platform constraints.

Supported manifest formats:
  - JSON files matching the pattern *identity*resolution*.json
  - XML files matching the pattern *IdentityResolution*.xml
  - Plain-text SKILL design docs matching the template format

Even without a manifest, the script emits guidance-only warnings that
remind practitioners of the key constraints before they configure rulesets.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants derived from official Salesforce platform limits
# ---------------------------------------------------------------------------

MAX_RULESETS_PER_ORG = 2
"""Hard org-level limit. Cannot be raised via support.
Source: Data Cloud Limits (help.salesforce.com, id=sf.c360_a_data_cloud_limits.htm)
"""

MAX_MANUAL_RUNS_PER_DAY = 4
"""Maximum manual identity resolution runs per ruleset per 24-hour window.
Source: Data Cloud Limits (help.salesforce.com, id=sf.c360_a_data_cloud_limits.htm)
"""

RULESET_ID_LENGTH = 4
"""Identity resolution ruleset IDs are exactly 4 alphanumeric characters.
This ID is immutable after creation.
"""

# Match types that are supported in real-time resolution contexts.
REALTIME_SAFE_MATCH_TYPES = {"exact", "exact_normalized", "normalized_exact"}

# Match types that are batch-only.
BATCH_ONLY_MATCH_TYPES = {"fuzzy", "normalized_address", "normalized"}

# Prohibited test/placeholder ruleset IDs that should never go to production.
PLACEHOLDER_RULESET_IDS = {"test", "tmp1", "tmp2", "demo", "temp"}

# DMO fields where Normalized match type is valid.
NORMALIZED_MATCH_SUPPORTED_DMOS = {
    "contactpointemail",
    "contact_point_email",
    "contactpointphone",
    "contact_point_phone",
    "contactpointaddress",
    "contact_point_address",
}

# DMO fields where Normalized match type is NOT valid (Individual DMO).
NORMALIZED_MATCH_NOT_SUPPORTED_FIELDS = {
    "firstname",
    "first_name",
    "lastname",
    "last_name",
    "middlename",
    "middle_name",
    "name",
}


# ---------------------------------------------------------------------------
# Checker functions
# ---------------------------------------------------------------------------

def check_ruleset_count(manifest_dir: Path) -> list[str]:
    """Warn if more than 2 identity resolution ruleset files are found.

    Data Cloud enforces a hard 2-ruleset limit per org. The Starter Data
    Bundle auto-creates one ruleset, leaving only 1 slot for custom rulesets.
    """
    issues: list[str] = []

    ruleset_files = (
        list(manifest_dir.rglob("*identity*resolution*.json"))
        + list(manifest_dir.rglob("*IdentityResolution*.xml"))
        + list(manifest_dir.rglob("*identity_resolution*.json"))
    )

    if len(ruleset_files) > MAX_RULESETS_PER_ORG:
        issues.append(
            f"Found {len(ruleset_files)} identity resolution ruleset file(s) — "
            f"the hard org limit is {MAX_RULESETS_PER_ORG}. "
            f"This includes any ruleset auto-created by the Starter Data Bundle. "
            f"Files found: {[str(f.name) for f in ruleset_files]}"
        )

    return issues


def check_ruleset_ids(manifest_dir: Path) -> list[str]:
    """Warn if ruleset IDs appear to be placeholder/test values or wrong length.

    Ruleset IDs are 4-character alphanumeric strings that are IMMUTABLE after
    creation. A placeholder ID (TEST, TMP1, etc.) becomes permanent.
    """
    issues: list[str] = []

    ruleset_files = (
        list(manifest_dir.rglob("*identity*resolution*.json"))
        + list(manifest_dir.rglob("*identity_resolution*.json"))
    )

    for fpath in ruleset_files:
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        ruleset_id = data.get("rulesetId") or data.get("id") or data.get("ruleset_id")
        if not ruleset_id:
            continue

        ruleset_id_str = str(ruleset_id).strip()

        if len(ruleset_id_str) != RULESET_ID_LENGTH:
            issues.append(
                f"{fpath.name}: rulesetId '{ruleset_id_str}' is {len(ruleset_id_str)} "
                f"characters — ruleset IDs must be exactly {RULESET_ID_LENGTH} "
                f"alphanumeric characters. This ID is IMMUTABLE after creation."
            )

        if ruleset_id_str.lower() in PLACEHOLDER_RULESET_IDS:
            issues.append(
                f"{fpath.name}: rulesetId '{ruleset_id_str}' appears to be a "
                f"placeholder or test ID. Ruleset IDs are immutable after creation "
                f"and will be permanent identifiers in activation targets and API calls. "
                f"Choose a meaningful ID before creating this ruleset."
            )

    return issues


def check_match_rules_for_realtime_safety(manifest_dir: Path) -> list[str]:
    """Warn if batch-only match rule types are found in rulesets.

    Fuzzy and full Address Normalized match types are batch-only.
    In real-time resolution contexts, these rules are silently skipped.
    """
    issues: list[str] = []

    ruleset_files = (
        list(manifest_dir.rglob("*identity*resolution*.json"))
        + list(manifest_dir.rglob("*identity_resolution*.json"))
    )

    for fpath in ruleset_files:
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        match_rules = data.get("matchRules") or data.get("match_rules") or []
        if not isinstance(match_rules, list):
            continue

        for rule in match_rules:
            rule_type = (
                rule.get("matchType") or rule.get("match_type") or ""
            ).lower().replace("-", "_")

            if rule_type in BATCH_ONLY_MATCH_TYPES:
                rule_label = rule.get("name") or rule.get("label") or str(rule)
                issues.append(
                    f"{fpath.name}: match rule '{rule_label}' uses type '{rule_type}' "
                    f"which is BATCH-ONLY. In real-time resolution contexts, this rule "
                    f"is silently skipped. Fuzzy (first name) and full Normalized Address "
                    f"are not evaluated during real-time identity resolution. "
                    f"If real-time fidelity is required, use Exact or Exact Normalized only."
                )

    return issues


def check_normalized_match_on_individual_dmo(manifest_dir: Path) -> list[str]:
    """Warn if Normalized match type is applied to Individual DMO name fields.

    Normalized match is only valid on Contact Point DMO fields (Email, Phone,
    Address). Applying it to Individual > First Name or Last Name is not
    supported and will not behave as expected.
    """
    issues: list[str] = []

    ruleset_files = (
        list(manifest_dir.rglob("*identity*resolution*.json"))
        + list(manifest_dir.rglob("*identity_resolution*.json"))
    )

    for fpath in ruleset_files:
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        match_rules = data.get("matchRules") or data.get("match_rules") or []
        if not isinstance(match_rules, list):
            continue

        for rule in match_rules:
            rule_type = (
                rule.get("matchType") or rule.get("match_type") or ""
            ).lower()
            field = (
                rule.get("field") or rule.get("fieldName") or rule.get("field_name") or ""
            ).lower().replace(" ", "_")
            dmo = (
                rule.get("dmo") or rule.get("dmoName") or rule.get("dmo_name") or ""
            ).lower().replace(" ", "").replace("_", "")

            if "normalized" in rule_type:
                if field in NORMALIZED_MATCH_NOT_SUPPORTED_FIELDS:
                    issues.append(
                        f"{fpath.name}: Normalized match type applied to field '{field}' "
                        f"(DMO: '{dmo}'). Normalized match is only supported on Contact "
                        f"Point DMO fields (Email Address, Phone Number, Address fields). "
                        f"For Individual DMO name fields, use Exact or Fuzzy (first name only)."
                    )
                if dmo in ("individual",) and field not in NORMALIZED_MATCH_NOT_SUPPORTED_FIELDS:
                    issues.append(
                        f"{fpath.name}: Normalized match type on Individual DMO field '{field}' "
                        f"is not a documented platform-supported configuration. Verify this "
                        f"field is supported before proceeding."
                    )

    return issues


def check_reconciliation_rules_presence(manifest_dir: Path) -> list[str]:
    """Warn if reconciliation rules are absent from a ruleset file.

    A ruleset without explicit reconciliation rules uses platform defaults,
    which may not reflect business requirements for source trust ranking.
    """
    issues: list[str] = []

    ruleset_files = (
        list(manifest_dir.rglob("*identity*resolution*.json"))
        + list(manifest_dir.rglob("*identity_resolution*.json"))
    )

    for fpath in ruleset_files:
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        recon_rules = (
            data.get("reconciliationRules")
            or data.get("reconciliation_rules")
            or []
        )

        if not recon_rules:
            ruleset_id = data.get("rulesetId") or data.get("id") or fpath.stem
            issues.append(
                f"{fpath.name}: No reconciliation rules found for ruleset '{ruleset_id}'. "
                f"Reconciliation rules determine which source value populates each Unified "
                f"Individual attribute when matched records disagree. Leaving them as defaults "
                f"may produce unexpected behavior. Define explicit reconciliation rules with "
                f"Source Priority or Most Recent strategies."
            )

    return issues


def emit_standing_guidance() -> list[str]:
    """Return guidance-only reminders about identity resolution constraints.

    These are emitted on every run as proactive reminders, regardless of
    whether any ruleset files are found in the manifest directory.
    """
    guidance = [
        "GUIDANCE: Hard org limit is 2 identity resolution rulesets total — includes any "
        "auto-created Starter Data Bundle ruleset. Confirm slot count before creating rulesets.",

        "GUIDANCE: Ruleset 4-character ID is IMMUTABLE after creation. "
        "Choose a meaningful ID (e.g., EMLP, PHNC) before saving. Document it in the "
        "architecture decision record immediately.",

        "GUIDANCE: Fuzzy match (first name) is batch-only — silently skipped in real-time "
        "resolution. If real-time fidelity is required, use Exact or Exact Normalized only.",

        "GUIDANCE: Changing any reconciliation rule on an existing ruleset triggers a FULL "
        "re-run of all clusters, not an incremental update. Plan as a maintenance operation.",

        "GUIDANCE: Manual run limit is 4 per ruleset per 24-hour window. "
        "Do not plan iterative testing that exceeds this limit in a single day.",
    ]
    return guidance


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Data Cloud Identity Resolution configuration for common issues.\n"
            "Validates against platform limits and known gotchas documented in the skill."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing identity resolution configuration files (default: current directory).",
    )
    parser.add_argument(
        "--guidance-only",
        action="store_true",
        help="Emit standing guidance reminders only, skip file-based checks.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    issues: list[str] = []
    guidance: list[str] = []

    if not manifest_dir.exists():
        print(f"ERROR: Manifest directory not found: {manifest_dir}", file=sys.stderr)
        return 2

    # Always emit standing guidance.
    guidance = emit_standing_guidance()

    if not args.guidance_only:
        issues += check_ruleset_count(manifest_dir)
        issues += check_ruleset_ids(manifest_dir)
        issues += check_match_rules_for_realtime_safety(manifest_dir)
        issues += check_normalized_match_on_individual_dmo(manifest_dir)
        issues += check_reconciliation_rules_presence(manifest_dir)

    for msg in guidance:
        print(f"INFO: {msg}")

    if not issues:
        print("\nNo issues found in identity resolution configuration files.")
        return 0

    print(f"\nFound {len(issues)} issue(s):\n", file=sys.stderr)
    for issue in issues:
        print(f"WARN: {issue}\n", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
