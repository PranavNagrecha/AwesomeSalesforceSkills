#!/usr/bin/env python3
"""Checker script for FSL Scheduling Optimization Design skill.

Validates Salesforce metadata and exported JSON/CSV artifacts for common
FSL optimizer misconfiguration patterns.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_scheduling_optimization_design.py [--help]
    python3 check_fsl_scheduling_optimization_design.py --manifest-dir path/to/metadata

Expected manifest directory layout (all files optional; missing files are skipped):
    <manifest-dir>/
        service_appointments.json     — list of {Id, DueDate, Priority, Status} dicts
        optimization_configs.json     — list of {Name, Type, Horizon, PolicyName} dicts
        scheduling_policies.json      — list of {Id, Name} dicts
        work_rules.json               — list of {PolicyId, PolicyName, Type} dicts

JSON format:
    service_appointments.json:
        [{"Id": "...", "DueDate": "2026-04-10", "Priority": "2", "Status": "Scheduled"}, ...]
        DueDate: ISO date string or null/empty string
        Priority: numeric string "1"–"10" or null/empty string
        Status: string

    optimization_configs.json:
        [{"Name": "Morning Run", "Type": "Global", "Horizon": 5, "PolicyName": "High Intensity"}, ...]
        Type: "Global" | "InDay" | "ResourceSchedule"
        Horizon: integer (days); relevant for Global

    work_rules.json:
        [{"PolicyId": "...", "PolicyName": "High Intensity", "Type": "ServiceResourceAvailability"}, ...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Appointment statuses that are terminal — excluded from data quality checks
TERMINAL_STATUSES = {"Completed", "Cancelled", "Cannot Complete"}

# Maximum acceptable percentage of active appointments with null DueDate
NULL_DUE_DATE_WARN_PCT = 5.0

# Maximum acceptable percentage of active appointments with null Priority
NULL_PRIORITY_WARN_PCT = 5.0

# Priority 1 saturation: if more than this % of appointments are priority 1,
# the tier model is over-assigned (eliminates optimizer differentiation)
PRIORITY_1_SATURATION_WARN_PCT = 20.0

# Maximum recommended Global Optimization horizon (days)
MAX_GLOBAL_HORIZON_DAYS = 7

# Work rule type that is mandatory in every scheduling policy used by the optimizer
REQUIRED_WORK_RULE_TYPE = "ServiceResourceAvailability"


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> list[dict] | None:
    """Load a JSON file and return its contents, or None if the file does not exist."""
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_appointment_data_quality(manifest_dir: Path) -> list[str]:
    """Check service appointments for null DueDate and null Priority."""
    issues: list[str] = []
    records = _load_json(manifest_dir / "service_appointments.json")
    if records is None:
        return issues  # file absent — skip silently

    active = [
        r for r in records
        if isinstance(r, dict) and r.get("Status", "") not in TERMINAL_STATUSES
    ]
    total = len(active)
    if total == 0:
        return issues

    null_due_date = [
        r for r in active
        if not r.get("DueDate")
    ]
    null_priority = [
        r for r in active
        if not r.get("Priority")
    ]
    priority_1 = [
        r for r in active
        if str(r.get("Priority", "")).strip() == "1"
    ]

    null_dd_pct = (len(null_due_date) / total) * 100
    null_prio_pct = (len(null_priority) / total) * 100
    prio_1_pct = (len(priority_1) / total) * 100

    if null_dd_pct > NULL_DUE_DATE_WARN_PCT:
        issues.append(
            f"{len(null_due_date)} of {total} active service appointments "
            f"({null_dd_pct:.1f}%) have null DueDate. "
            f"Null DueDate appointments are treated as lowest priority by the FSL Optimizer "
            f"and may never be scheduled in constrained runs. "
            f"Threshold: {NULL_DUE_DATE_WARN_PCT}%."
        )

    if null_prio_pct > NULL_PRIORITY_WARN_PCT:
        issues.append(
            f"{len(null_priority)} of {total} active service appointments "
            f"({null_prio_pct:.1f}%) have null Priority. "
            f"Null Priority prevents the optimizer from differentiating urgency between appointments. "
            f"Threshold: {NULL_PRIORITY_WARN_PCT}%."
        )

    if prio_1_pct > PRIORITY_1_SATURATION_WARN_PCT:
        issues.append(
            f"{len(priority_1)} of {total} active service appointments "
            f"({prio_1_pct:.1f}%) are Priority 1. "
            f"Priority 1 generates ~25,500 optimizer points. "
            f"Over-assigning Priority 1 eliminates optimizer differentiation — "
            f"all priority-1 appointments appear equal and ordering falls back to DueDate only. "
            f"Reserve Priority 1 for genuine emergencies (<{PRIORITY_1_SATURATION_WARN_PCT:.0f}% of volume)."
        )

    return issues


def check_optimization_configs(manifest_dir: Path) -> list[str]:
    """Check optimization job configurations for common misconfiguration patterns."""
    issues: list[str] = []
    configs = _load_json(manifest_dir / "optimization_configs.json")
    if configs is None:
        return issues

    valid_types = {"Global", "InDay", "ResourceSchedule"}

    for cfg in configs:
        if not isinstance(cfg, dict):
            continue
        name = cfg.get("Name", "<unnamed>")
        opt_type = cfg.get("Type", "")
        horizon = cfg.get("Horizon")
        policy_name = cfg.get("PolicyName", "")

        # Unknown optimization type
        if opt_type and opt_type not in valid_types:
            issues.append(
                f"Optimization config '{name}': unrecognized Type '{opt_type}'. "
                f"Valid types: {', '.join(sorted(valid_types))}."
            )

        # Global horizon sanity check
        if opt_type == "Global" and horizon is not None:
            try:
                horizon_int = int(horizon)
            except (TypeError, ValueError):
                horizon_int = None

            if horizon_int is not None and horizon_int > MAX_GLOBAL_HORIZON_DAYS:
                issues.append(
                    f"Optimization config '{name}' (Global): Horizon is {horizon_int} days, "
                    f"which exceeds the maximum recommended value of {MAX_GLOBAL_HORIZON_DAYS} days. "
                    f"Long horizons increase run time and may cause timeouts."
                )
            if horizon_int is not None and horizon_int < 1:
                issues.append(
                    f"Optimization config '{name}' (Global): Horizon is {horizon_int} days — "
                    f"must be at least 1."
                )

        # In-Day configs should not have a horizon >1
        if opt_type == "InDay" and horizon is not None:
            try:
                horizon_int = int(horizon)
            except (TypeError, ValueError):
                horizon_int = None
            if horizon_int is not None and horizon_int > 1:
                issues.append(
                    f"Optimization config '{name}' (InDay): Horizon is {horizon_int} days. "
                    f"In-Day optimization is scoped to the current day only (horizon = 1). "
                    f"Using a longer horizon converts this to a Global-style run with same-day scope."
                )

        # No scheduling policy assigned
        if not policy_name:
            issues.append(
                f"Optimization config '{name}': No scheduling policy assigned. "
                f"The optimizer requires a scheduling policy to filter and rank candidates."
            )

    return issues


def check_policy_work_rules(manifest_dir: Path) -> list[str]:
    """Check that scheduling policies referenced by optimization configs have the required work rule."""
    issues: list[str] = []

    configs = _load_json(manifest_dir / "optimization_configs.json")
    work_rules = _load_json(manifest_dir / "work_rules.json")

    if configs is None or work_rules is None:
        return issues

    # Build a set of (policy_name, rule_type) pairs
    policy_rule_pairs: set[tuple[str, str]] = set()
    for rule in work_rules:
        if not isinstance(rule, dict):
            continue
        policy_name = rule.get("PolicyName", "")
        rule_type = rule.get("Type", "")
        if policy_name and rule_type:
            policy_rule_pairs.add((policy_name, rule_type))

    # For each optimization config, verify the assigned policy has the required work rule
    for cfg in configs:
        if not isinstance(cfg, dict):
            continue
        config_name = cfg.get("Name", "<unnamed>")
        policy_name = cfg.get("PolicyName", "")
        if not policy_name:
            continue  # already flagged in check_optimization_configs

        if (policy_name, REQUIRED_WORK_RULE_TYPE) not in policy_rule_pairs:
            issues.append(
                f"Optimization config '{config_name}' uses scheduling policy '{policy_name}', "
                f"which is missing the '{REQUIRED_WORK_RULE_TYPE}' work rule. "
                f"Without this rule, the optimizer ignores resource working hours and absences, "
                f"producing schedules that violate technician availability."
            )

    return issues


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


def check_fsl_scheduling_optimization_design(manifest_dir: Path) -> list[str]:
    """Run all checks and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_appointment_data_quality(manifest_dir))
    issues.extend(check_optimization_configs(manifest_dir))
    issues.extend(check_policy_work_rules(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSL Scheduling Optimization Design configuration and metadata for common issues. "
            "Reads JSON export files from a manifest directory. All files are optional; "
            "missing files are silently skipped."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory containing JSON export files (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fsl_scheduling_optimization_design(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
