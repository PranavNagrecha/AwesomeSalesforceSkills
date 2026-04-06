#!/usr/bin/env python3
"""Checker script for org-limits-monitoring skill.

Scans a monitoring plan or Apex class file for evidence of org-limit monitoring
best practices:
- Use of OrgLimits.getAll() (preferred) or REST /limits
- Threshold-based alerting (warning and critical)
- Configurable thresholds via Custom Metadata
- Multi-limit coverage (not just one limit)
- Alert channel specification
- Platform Event silent-drop awareness
- Scheduled Apex polling pattern

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_org_limits_monitoring.py --help
    python3 check_org_limits_monitoring.py --file path/to/monitoring-plan.md
    python3 check_org_limits_monitoring.py --file path/to/MonitorJob.cls --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Check:
    name: str
    description: str
    patterns: list[re.Pattern]
    required_in_strict: bool = True
    found: bool = False


def _p(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


CHECKS: list[Check] = [
    Check(
        name="org_limits_apex",
        description="Uses OrgLimits.getAll() for Apex-native limit polling (zero API cost)",
        patterns=[
            _p(r"OrgLimits\.getAll"),
            _p(r"System\.OrgLimits"),
            _p(r"OrgLimits\s+class"),
        ],
    ),
    Check(
        name="rest_limits_resource",
        description="References REST /limits endpoint for comprehensive limit coverage",
        patterns=[
            _p(r"/services/data/v\d+\.\d/limits"),
            _p(r"GET\s+.*/limits"),
            _p(r"REST\s+Limits\s+resource"),
            _p(r"rest.*limits.*endpoint"),
        ],
    ),
    Check(
        name="warning_threshold",
        description="Defines a warning threshold for limit consumption",
        patterns=[
            _p(r"warning.{0,20}threshold"),
            _p(r"warn.{0,15}(70|75|80)\s*%"),
            _p(r"Warning_Threshold"),
            _p(r"alert.{0,20}warning"),
        ],
    ),
    Check(
        name="critical_threshold",
        description="Defines a critical threshold for limit consumption",
        patterns=[
            _p(r"critical.{0,20}threshold"),
            _p(r"critical.{0,15}(85|90|95)\s*%"),
            _p(r"Critical_Threshold"),
            _p(r"alert.{0,20}critical"),
        ],
    ),
    Check(
        name="custom_metadata_config",
        description="Uses Custom Metadata for configurable thresholds (not hard-coded)",
        patterns=[
            _p(r"Custom\s+Metadata"),
            _p(r"__mdt"),
            _p(r"Limit_Monitor_Config"),
            _p(r"configurable\s+threshold"),
        ],
    ),
    Check(
        name="scheduled_apex",
        description="Uses Scheduled Apex for periodic polling",
        patterns=[
            _p(r"Schedulable"),
            _p(r"Scheduled\s+Apex"),
            _p(r"System\.schedule"),
            _p(r"cron\s+expression"),
            _p(r"scheduled\s+job"),
        ],
    ),
    Check(
        name="multi_limit_coverage",
        description="Monitors multiple limit categories (not just one)",
        patterns=[
            _p(r"DailyApiRequests"),
            _p(r"DataStorageMB"),
            _p(r"FileStorageMB"),
            _p(r"HourlyPublishedPlatformEvents"),
            _p(r"DailyAsyncApexExecutions"),
        ],
    ),
    Check(
        name="alert_channel",
        description="Specifies alert notification channel(s)",
        patterns=[
            _p(r"email.{0,20}alert"),
            _p(r"Platform\s+Event.{0,20}alert"),
            _p(r"Custom\s*Notification"),
            _p(r"PagerDuty|Slack|webhook"),
            _p(r"Messaging\.\w+Email"),
            _p(r"notification\s+channel"),
        ],
    ),
    Check(
        name="platform_event_silent_drop",
        description="Addresses Platform Event silent drop behavior when hourly limit is exceeded",
        patterns=[
            _p(r"silent.{0,10}drop"),
            _p(r"silently\s+dropped"),
            _p(r"no\s+exception.{0,20}event"),
            _p(r"reconciliation.{0,20}event"),
            _p(r"subscriber.{0,10}side.{0,10}reconcil"),
        ],
        required_in_strict=True,
    ),
    Check(
        name="percentage_calculation",
        description="Computes consumption as percentage (not absolute values)",
        patterns=[
            _p(r"percent"),
            _p(r"pct.{0,5}used"),
            _p(r"consumption\s+percentage"),
            _p(r"Decimal\.valueOf"),
            _p(r"getLimit\(\)"),
        ],
    ),
]


def scan_file(path: Path) -> list[Check]:
    """Read file and evaluate all checks against its content."""
    text = path.read_text(encoding="utf-8", errors="replace")
    for check in CHECKS:
        for pattern in check.patterns:
            if pattern.search(text):
                check.found = True
                break
    return CHECKS


def print_results(checks: list[Check], strict: bool) -> bool:
    """Print check results and return True if all required checks pass."""
    passed = 0
    failed = 0
    warnings = 0

    for check in checks:
        if check.found:
            print(f"  PASS  {check.name}: {check.description}")
            passed += 1
        elif strict and check.required_in_strict:
            print(f"  FAIL  {check.name}: {check.description}")
            failed += 1
        else:
            print(f"  WARN  {check.name}: {check.description}")
            warnings += 1

    print(f"\nResults: {passed} passed, {failed} failed, {warnings} warnings")

    if strict:
        return failed == 0
    # In non-strict mode, require at least one monitoring surface and one threshold
    has_monitoring = any(
        c.found for c in checks if c.name in ("org_limits_apex", "rest_limits_resource")
    )
    has_threshold = any(
        c.found for c in checks if c.name in ("warning_threshold", "critical_threshold")
    )
    if not has_monitoring:
        print("\nERROR: No monitoring surface detected (OrgLimits.getAll() or REST /limits)")
        return False
    if not has_threshold:
        print("\nERROR: No threshold alerting detected")
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check an org-limits monitoring plan or Apex class for best practices."
    )
    parser.add_argument(
        "--file",
        required=True,
        type=Path,
        help="Path to the monitoring plan (.md) or Apex class (.cls) to check.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Require all checks to pass (default: require minimum coverage).",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"ERROR: File not found: {args.file}")
        sys.exit(2)

    print(f"Checking: {args.file}")
    print(f"Mode: {'strict' if args.strict else 'standard'}\n")

    checks = scan_file(args.file)
    success = print_results(checks, args.strict)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
