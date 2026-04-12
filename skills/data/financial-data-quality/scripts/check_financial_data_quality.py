#!/usr/bin/env python3
"""Checker script for Financial Data Quality (FSC) skill.

Analyzes Salesforce org metadata to detect common FSC financial data quality issues:
- Validation rules on FinancialAccount missing Custom Permission bypass
- Validation rules on FinancialAccount missing RecordType guards
- Duplicate Rules incorrectly targeting FinancialAccount (unsupported)
- Apex triggers on FinancialAccount missing bulk-safe SOQL patterns (SOQL inside for-loop)
- Missing Apex triggers on FinancialAccount for duplicate detection

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_financial_data_quality.py [--help]
    python3 check_financial_data_quality.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Validation rule file detection
VALIDATION_RULE_PATTERN = re.compile(r"\.validationRule-meta\.xml$", re.IGNORECASE)

# Object names that indicate FSC financial objects
FSC_FINANCIAL_OBJECTS = {"FinancialAccount", "FinServ__FinancialAccount__c", "FinancialHolding", "FinServ__FinancialHolding__c"}

# Custom Permission bypass pattern in validation rules
CUSTOM_PERMISSION_BYPASS = re.compile(r"\$Permission\.", re.IGNORECASE)

# RecordType guard pattern in validation rule formulas
RECORDTYPE_GUARD = re.compile(r"RecordType\.DeveloperName|ISPICKVAL\s*\(\s*RecordType", re.IGNORECASE)

# Profile-based bypass anti-pattern
PROFILE_BYPASS = re.compile(r"\$Profile\.Name", re.IGNORECASE)

# Duplicate Rule file detection
DUPLICATE_RULE_PATTERN = re.compile(r"\.duplicateRule-meta\.xml$", re.IGNORECASE)

# Duplicate rule object reference matching FSC objects
DUPLICATE_RULE_OBJECT = re.compile(
    r"<sobjectType>(FinancialAccount|FinServ__FinancialAccount__c|FinancialHolding|FinServ__FinancialHolding__c)</sobjectType>",
    re.IGNORECASE,
)

# Apex trigger file detection
APEX_TRIGGER_PATTERN = re.compile(r"\.trigger$", re.IGNORECASE)

# Trigger on FSC financial objects
TRIGGER_ON_FINANCIAL_ACCOUNT = re.compile(
    r"trigger\s+\w+\s+on\s+(FinancialAccount|FinServ__FinancialAccount__c)",
    re.IGNORECASE,
)

# Bulk-unsafe: SOQL inside a for-loop over Trigger.new or Trigger.old
# Heuristic: a SELECT statement that appears after a 'for (' on the same logical level
SOQL_IN_FOR_LOOP = re.compile(
    r"for\s*\([^)]*Trigger\.(new|old)[^)]*\)[^{]*\{[^}]*\[SELECT",
    re.IGNORECASE | re.DOTALL,
)

# Alternative heuristic: lines containing [SELECT within a block that also has Trigger.new iteration
SOQL_QUERY_LINE = re.compile(r"\[SELECT", re.IGNORECASE)
FOR_TRIGGER_LINE = re.compile(r"for\s*\(.*Trigger\.(new|old)", re.IGNORECASE)

# before insert trigger event (required for duplicate detection)
BEFORE_INSERT_EVENT = re.compile(r"before\s+insert", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _is_fsc_object_folder(path: Path) -> bool:
    """Check if the path is under an FSC financial object folder."""
    parts = {p.lower() for p in path.parts}
    fsc_names = {o.lower() for o in FSC_FINANCIAL_OBJECTS}
    return bool(parts & fsc_names)


def _object_name_from_path(path: Path) -> str | None:
    """Extract the Salesforce object name from a metadata file path.

    Metadata paths follow: .../objects/<ObjectName>/validationRules/<rule>.validationRule-meta.xml
    or: .../objects/<ObjectName>/<rule>.validationRule-meta.xml (compact layout)
    """
    parts = path.parts
    for i, part in enumerate(parts):
        if part.lower() == "objects" and i + 1 < len(parts):
            return parts[i + 1]
    return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_validation_rules(manifest_dir: Path) -> list[str]:
    """Check validation rules on FSC financial objects."""
    issues: list[str] = []
    found_any = False

    for vr_file in manifest_dir.rglob("*.validationRule-meta.xml"):
        object_name = _object_name_from_path(vr_file)
        if object_name not in FSC_FINANCIAL_OBJECTS:
            continue

        found_any = True
        content = _read_text(vr_file)
        rule_name = vr_file.stem.replace(".validationRule-meta", "")

        # Check for missing Custom Permission bypass
        if not CUSTOM_PERMISSION_BYPASS.search(content):
            issues.append(
                f"VALIDATION_RULE_NO_BYPASS: {vr_file.relative_to(manifest_dir)} — "
                f"Validation rule '{rule_name}' on {object_name} has no $Permission bypass. "
                f"Add NOT($Permission.Bypass_FSC_Validation) to allow integration users to bypass during bulk loads."
            )

        # Check for profile-based bypass (anti-pattern)
        if PROFILE_BYPASS.search(content):
            issues.append(
                f"VALIDATION_RULE_PROFILE_BYPASS: {vr_file.relative_to(manifest_dir)} — "
                f"Validation rule '{rule_name}' on {object_name} uses $Profile.Name for bypass. "
                f"Replace with $Permission.Bypass_FSC_Validation (Custom Permission) for least-privilege, auditable bypass."
            )

        # Check for missing RecordType guard on non-universal rules
        # Heuristic: if the rule has ISBLANK or required-field checks but no RecordType guard,
        # it may apply to all RecordTypes unintentionally
        has_blank_check = "ISBLANK" in content.upper() or "ISNULL" in content.upper()
        if has_blank_check and not RECORDTYPE_GUARD.search(content):
            issues.append(
                f"VALIDATION_RULE_NO_RECORDTYPE_GUARD: {vr_file.relative_to(manifest_dir)} — "
                f"Validation rule '{rule_name}' on {object_name} checks for blank fields but has no RecordType guard. "
                f"If this rule applies only to specific account types (e.g. Insurance, Investment), "
                f"add ISPICKVAL(RecordType.DeveloperName, 'TargetType') to prevent blocking unrelated types."
            )

    return issues


def check_duplicate_rules(manifest_dir: Path) -> list[str]:
    """Detect Duplicate Rules incorrectly targeting FSC financial objects."""
    issues: list[str] = []

    for dr_file in manifest_dir.rglob("*.duplicateRule-meta.xml"):
        content = _read_text(dr_file)
        match = DUPLICATE_RULE_OBJECT.search(content)
        if match:
            object_name = match.group(1)
            rule_name = dr_file.stem.replace(".duplicateRule-meta", "")
            issues.append(
                f"DUPLICATE_RULE_UNSUPPORTED_OBJECT: {dr_file.relative_to(manifest_dir)} — "
                f"Duplicate Rule '{rule_name}' references {object_name} which is NOT supported by standard Salesforce Duplicate Management. "
                f"Standard Duplicate Rules only cover Account, Contact, and Lead. "
                f"Remove this rule and implement duplicate detection via an Apex before-insert trigger on {object_name}."
            )

    return issues


def check_apex_triggers(manifest_dir: Path) -> list[str]:
    """Check Apex triggers on FSC financial objects for bulk-safety and duplicate detection."""
    issues: list[str] = []
    financial_account_triggers: list[Path] = []

    for trigger_file in manifest_dir.rglob("*.trigger"):
        content = _read_text(trigger_file)
        if not TRIGGER_ON_FINANCIAL_ACCOUNT.search(content):
            continue

        financial_account_triggers.append(trigger_file)

        # Heuristic bulk-safety check: detect SOQL queries appearing after for-loop lines
        # Simplified check: look for [SELECT within a reasonable distance after a for(Trigger.new line
        lines = content.splitlines()
        in_for_trigger = False
        for_depth = 0
        for i, line in enumerate(lines):
            if FOR_TRIGGER_LINE.search(line):
                in_for_trigger = True
                for_depth = 0

            if in_for_trigger:
                for_depth += line.count("{") - line.count("}")
                if SOQL_QUERY_LINE.search(line):
                    issues.append(
                        f"TRIGGER_SOQL_IN_FOR_LOOP: {trigger_file.name} (around line {i + 1}) — "
                        f"SOQL query detected inside or near a for-loop over Trigger.new/old in a FinancialAccount trigger. "
                        f"This is not bulk-safe and will hit governor limits during integration loads. "
                        f"Collect all keys into a Set before the loop, execute one SOQL, and check a Map in memory."
                    )
                    in_for_trigger = False  # Report once per trigger
                if for_depth <= 0 and i > 0:
                    in_for_trigger = False

    # Check that at least one before-insert trigger exists on FinancialAccount for duplicate detection
    has_before_insert_dup_trigger = False
    for trig in financial_account_triggers:
        content = _read_text(trig)
        if BEFORE_INSERT_EVENT.search(content):
            has_before_insert_dup_trigger = True
            break

    if not financial_account_triggers:
        issues.append(
            "MISSING_DUPLICATE_DETECTION_TRIGGER: No Apex trigger found on FinancialAccount or FinServ__FinancialAccount__c. "
            "Standard Duplicate Rules do not cover FSC financial objects. "
            "Implement a before-insert Apex trigger with a business-key deduplication check (e.g. ExternalAccountNumber__c)."
        )
    elif not has_before_insert_dup_trigger:
        issues.append(
            "MISSING_BEFORE_INSERT_TRIGGER: FinancialAccount trigger(s) found but none fires on 'before insert'. "
            "Duplicate detection requires a before-insert trigger so addError() can block the insert before commit."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_financial_data_quality(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    # Run all checks
    issues.extend(check_validation_rules(manifest_dir))
    issues.extend(check_duplicate_rules(manifest_dir))
    issues.extend(check_apex_triggers(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check FSC Financial Data Quality configuration and metadata for common issues.\n\n"
            "Detects: missing validation rule bypasses, missing RecordType guards, "
            "Duplicate Rules incorrectly targeting FinancialAccount, "
            "non-bulk-safe Apex triggers, and missing duplicate detection triggers."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_financial_data_quality(manifest_dir)

    if not issues:
        print("No FSC financial data quality issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(f"\n{len(issues)} issue(s) found.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
