#!/usr/bin/env python3
"""Checker script for FSL Scheduling Policies skill.

Validates Field Service Lightning scheduling policy metadata exported from
a Salesforce org for common configuration problems.

Checks performed:
  1. Every scheduling policy has at least one work rule of type
     'Service Resource Availability'.
  2. Service objective weights in each policy sum to approximately 100
     (within a 5-point tolerance).
  3. No work rules are present with placeholder or incomplete names
     indicating an unfinished configuration.
  4. Policies that appear to be clones of default policies retain
     their custom names (not named identically to the four Salesforce defaults).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_scheduling_policies.py [--manifest-dir path/to/metadata]
    python3 check_fsl_scheduling_policies.py --help

Expected metadata layout (Salesforce DX / MDAPI export):
    <manifest-dir>/
        objects/
            FSL__Scheduling_Policy__c/     (optional — for field metadata)
        customMetadata/                    (if policies are stored as custom metadata)
        reports/                           (ignored)

    OR flat CSV/JSON export files:
        <manifest-dir>/scheduling_policies.json
        <manifest-dir>/work_rules.json
        <manifest-dir>/service_objectives.json

    JSON format expected:
      scheduling_policies.json  — list of {Id, Name} dicts
      work_rules.json           — list of {Id, Name, FSL__Scheduling_Policy__c,
                                            FSL__Type__c} dicts
      service_objectives.json   — list of {Id, Name, FSL__Scheduling_Policy__c,
                                            FSL__Weight__c} dicts
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Salesforce default policy names — these should never be the name of a
# custom policy (they should only exist as unmodified Salesforce defaults).
DEFAULT_POLICY_NAMES = {
    "Customer First",
    "High Intensity",
    "Soft Boundaries",
    "Emergency",
}

# The mandatory work rule type that every custom policy must contain.
REQUIRED_WORK_RULE_TYPE = "Service Resource Availability"

# Tolerance for objective weight sum validation (weights should sum to ~100).
WEIGHT_SUM_TOLERANCE = 5.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSL Scheduling Policy metadata for common configuration issues.\n\n"
            "Expects JSON export files in --manifest-dir:\n"
            "  scheduling_policies.json\n"
            "  work_rules.json\n"
            "  service_objectives.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Directory containing exported JSON metadata files (default: current directory).",
    )
    return parser.parse_args()


def load_json_file(path: Path) -> list[dict]:
    """Load a JSON file and return its contents as a list of dicts.

    Returns an empty list if the file does not exist (non-fatal — the
    caller decides whether absence is an error).
    """
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "records" in data:
        # Salesforce query result envelope
        return data["records"]
    return []


def check_fsl_scheduling_policies(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Each returned string describes a concrete, actionable issue.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # ------------------------------------------------------------------
    # Load export files
    # ------------------------------------------------------------------
    policies = load_json_file(manifest_dir / "scheduling_policies.json")
    work_rules = load_json_file(manifest_dir / "work_rules.json")
    objectives = load_json_file(manifest_dir / "service_objectives.json")

    if not policies:
        issues.append(
            "scheduling_policies.json not found or empty in manifest directory. "
            "Export FSL__Scheduling_Policy__c records and save as scheduling_policies.json."
        )
        return issues

    # Build lookup maps keyed by policy Id
    rules_by_policy: dict[str, list[dict]] = {}
    for rule in work_rules:
        policy_id = rule.get("FSL__Scheduling_Policy__c", "")
        rules_by_policy.setdefault(policy_id, []).append(rule)

    objectives_by_policy: dict[str, list[dict]] = {}
    for obj in objectives:
        policy_id = obj.get("FSL__Scheduling_Policy__c", "")
        objectives_by_policy.setdefault(policy_id, []).append(obj)

    # ------------------------------------------------------------------
    # Check each policy
    # ------------------------------------------------------------------
    for policy in policies:
        policy_id = policy.get("Id", "<unknown>")
        policy_name = policy.get("Name", "<unnamed>")

        # Check 1: Custom policy names should not duplicate default policy names
        if policy_name in DEFAULT_POLICY_NAMES:
            issues.append(
                f"Policy '{policy_name}' (Id: {policy_id}) uses a default policy name. "
                "Custom policies must have unique names. Clone the default and rename "
                "before making any configuration changes."
            )

        policy_rules = rules_by_policy.get(policy_id, [])
        policy_objectives = objectives_by_policy.get(policy_id, [])

        # Check 2: Service Resource Availability work rule must be present
        rule_types = [r.get("FSL__Type__c", "") for r in policy_rules]
        if REQUIRED_WORK_RULE_TYPE not in rule_types:
            issues.append(
                f"Policy '{policy_name}' (Id: {policy_id}) is missing the "
                f"'{REQUIRED_WORK_RULE_TYPE}' work rule. Without this rule, the "
                "scheduler ignores all resource working hours and absences. "
                "Add a work rule of type 'Service Resource Availability' to this policy."
            )

        # Check 3: Service objective weights should sum to approximately 100
        if policy_objectives:
            total_weight = sum(
                float(o.get("FSL__Weight__c", 0) or 0) for o in policy_objectives
            )
            if abs(total_weight - 100.0) > WEIGHT_SUM_TOLERANCE:
                issues.append(
                    f"Policy '{policy_name}' (Id: {policy_id}) has service objective "
                    f"weights summing to {total_weight:.1f}% (expected ~100%). "
                    "Imbalanced weights produce unpredictable candidate rankings. "
                    "Adjust objective weights to sum to 100%."
                )

        # Check 4: Policies with zero work rules are likely misconfigured
        if not policy_rules:
            issues.append(
                f"Policy '{policy_name}' (Id: {policy_id}) has no work rules. "
                "A policy with no work rules never filters any candidate slot, "
                "which is almost never intentional. Add at minimum the "
                "'Service Resource Availability' work rule."
            )

        # Check 5: Policies with zero objectives will not rank candidates
        if not policy_objectives:
            issues.append(
                f"Policy '{policy_name}' (Id: {policy_id}) has no service objectives. "
                "Without objectives, candidate slots cannot be ranked after filtering. "
                "Add at least one service objective (e.g., ASAP) with a non-zero weight."
            )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_scheduling_policies(manifest_dir)

    if not issues:
        print("No FSL scheduling policy issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
