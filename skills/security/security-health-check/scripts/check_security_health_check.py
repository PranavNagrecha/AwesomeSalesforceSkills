#!/usr/bin/env python3
"""Checker script for Security Health Check skill.

Validates a Salesforce project metadata directory for the most common mistake
this skill prevents: having a custom baseline XML file that demotes settings
to Informational or lowers thresholds below the Salesforce recommended minimums,
which produces a misleadingly high Health Check score without improving security.

Also checks whether any Health Check baseline XML files have been committed to
the metadata directory with documented deviations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_security_health_check.py [--help]
    python3 check_security_health_check.py --manifest-dir path/to/metadata
    python3 check_security_health_check.py --baseline path/to/baseline.xml
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# Salesforce standard minimum thresholds (conservative floor values).
# A custom baseline must not set standardValue BELOW these for the given setting.
# Source: Salesforce Security Health Check documentation.
SALESFORCE_MINIMUM_THRESHOLDS: dict[str, tuple[str, str]] = {
    # setting name -> (minimum acceptable value, unit/description)
    "MinPasswordLength": ("8", "characters"),
    "MaxLoginAttempts": ("10", "attempts before lockout"),
    "PasswordComplexity": ("1", "complexity level (1=alpha+numeric required)"),
    "MaxPasswordAgeDays": ("365", "days — 0 means never expires (non-compliant)"),
    "SessionTimeout": ("120", "minutes — do not exceed 720 min (12 hrs) for High Risk"),
}

# Settings where the risk type must NOT be lowered below this level.
# Demoting these to Informational is a common score-gaming anti-pattern.
REQUIRED_MIN_RISK: dict[str, str] = {
    "MinPasswordLength": "HIGH_RISK",
    "PasswordComplexity": "HIGH_RISK",
    "MaxLoginAttempts": "MEDIUM_RISK",
}

# Informational risk type string in baseline XML
INFORMATIONAL = "INFORMATIONAL"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a Security Health Check custom baseline XML or project metadata "
            "directory for common anti-patterns: risk demotion, threshold relaxation, "
            "and missing deviation documentation."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help="Root directory of the Salesforce metadata to scan for baseline XML files.",
    )
    parser.add_argument(
        "--baseline",
        default=None,
        help="Path to a specific Health Check custom baseline XML file to validate.",
    )
    return parser.parse_args()


def find_baseline_files(manifest_dir: Path) -> list[Path]:
    """Return all XML files in the directory tree that look like Health Check baselines."""
    candidates: list[Path] = []
    for xml_file in manifest_dir.rglob("*.xml"):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            # Health Check baseline XML typically has a root element containing
            # <setting> children with <settingName>, <standardValue>, <riskType>.
            children = list(root)
            if any(
                child.find("settingName") is not None
                or child.find("riskType") is not None
                for child in children
            ):
                candidates.append(xml_file)
        except ET.ParseError:
            continue
    return candidates


def validate_baseline_xml(baseline_path: Path) -> list[str]:
    """Validate a single Health Check baseline XML file.

    Returns a list of issue strings. Empty list means no issues found.
    """
    issues: list[str] = []

    try:
        tree = ET.parse(baseline_path)
    except ET.ParseError as exc:
        return [f"[{baseline_path.name}] XML parse error: {exc}"]

    root = tree.getroot()

    # Each <setting> block contains <settingName>, <standardValue>, <riskType>
    for setting in root.iter("setting"):
        name_el = setting.find("settingName")
        value_el = setting.find("standardValue")
        risk_el = setting.find("riskType")

        if name_el is None:
            continue

        name = (name_el.text or "").strip()
        value = (value_el.text or "").strip() if value_el is not None else None
        risk = (risk_el.text or "").strip().upper() if risk_el is not None else None

        # Check 1: required-minimum risk settings demoted to Informational
        if name in REQUIRED_MIN_RISK and risk == INFORMATIONAL:
            required_min = REQUIRED_MIN_RISK[name]
            issues.append(
                f"[{baseline_path.name}] ANTI-PATTERN: '{name}' is set to INFORMATIONAL. "
                f"This setting must be at least {required_min}. Demoting it to Informational "
                f"removes its contribution to the score without fixing the underlying risk."
            )

        # Check 2: risk level below required minimum (e.g., HIGH_RISK downgraded to LOW_RISK)
        if name in REQUIRED_MIN_RISK and risk is not None and risk != INFORMATIONAL:
            risk_order = {"HIGH_RISK": 3, "MEDIUM_RISK": 2, "LOW_RISK": 1, "INFORMATIONAL": 0}
            min_risk = REQUIRED_MIN_RISK[name]
            if risk_order.get(risk, 0) < risk_order.get(min_risk, 0):
                issues.append(
                    f"[{baseline_path.name}] RISK DEMOTION: '{name}' has riskType='{risk}' "
                    f"but the minimum recommended level is '{min_risk}'. "
                    f"Downgrading this setting reduces score sensitivity without improving security."
                )

        # Check 3: numeric threshold below Salesforce minimum floor
        if name in SALESFORCE_MINIMUM_THRESHOLDS and value is not None:
            min_val_str, unit = SALESFORCE_MINIMUM_THRESHOLDS[name]
            try:
                val_int = int(value)
                min_int = int(min_val_str)

                # Special case: MaxPasswordAgeDays=0 means "never expires" — non-compliant
                if name == "MaxPasswordAgeDays" and val_int == 0:
                    issues.append(
                        f"[{baseline_path.name}] THRESHOLD ISSUE: '{name}' is 0 (never expires). "
                        f"Password expiration should be enabled. "
                        f"A value of 0 is non-compliant with the Salesforce standard."
                    )
                elif val_int < min_int and name != "MaxPasswordAgeDays":
                    issues.append(
                        f"[{baseline_path.name}] THRESHOLD RELAXED: '{name}' standardValue='{value}' "
                        f"is below the Salesforce minimum of '{min_val_str}' {unit}. "
                        f"This custom baseline is weaker than the Salesforce standard."
                    )
            except ValueError:
                pass  # Non-numeric values are not checked here

    return issues


def check_manifest_dir(manifest_dir: Path) -> list[str]:
    """Scan a metadata directory for baseline XML files and validate each one."""
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    baseline_files = find_baseline_files(manifest_dir)

    if not baseline_files:
        # Not an error — many projects don't commit a custom baseline.
        # Report it as informational.
        issues.append(
            "INFO: No Health Check baseline XML files found in the metadata directory. "
            "If a custom baseline is in use, ensure it is version-controlled alongside "
            "this project and periodically reviewed against the Salesforce standard."
        )
        return issues

    for bf in baseline_files:
        file_issues = validate_baseline_xml(bf)
        issues.extend(file_issues)

    return issues


def main() -> int:
    args = parse_args()

    all_issues: list[str] = []

    if args.baseline:
        baseline_path = Path(args.baseline)
        if not baseline_path.exists():
            print(f"ERROR: Baseline file not found: {baseline_path}", file=sys.stderr)
            return 2
        all_issues.extend(validate_baseline_xml(baseline_path))

    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        all_issues.extend(check_manifest_dir(manifest_dir))

    if args.baseline is None and args.manifest_dir is None:
        # Default: scan current directory
        all_issues.extend(check_manifest_dir(Path(".")))

    if not all_issues:
        print("No issues found.")
        return 0

    error_count = 0
    for issue in all_issues:
        prefix = "INFO" if issue.startswith("INFO:") else "ISSUE"
        print(f"{prefix}: {issue}")
        if prefix == "ISSUE":
            error_count += 1

    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
