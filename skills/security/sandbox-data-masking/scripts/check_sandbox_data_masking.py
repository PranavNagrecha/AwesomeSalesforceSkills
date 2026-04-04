#!/usr/bin/env python3
"""Checker script for Sandbox Data Masking skill.

Inspects a Salesforce metadata directory for configuration signals that indicate
sandbox data masking is or is not properly set up. Checks for:
  - Presence of SandboxPostCopy Apex classes that reference Data Mask
  - Apex classes with obvious PII field references lacking masking commentary
  - Presence of Data Mask configuration metadata files
  - Validation rules that might conflict with Null/Delete masking on required fields

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_sandbox_data_masking.py [--manifest-dir path/to/metadata]
    python3 check_sandbox_data_masking.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Keywords that suggest Data Mask integration in an Apex class
_DATA_MASK_PATTERNS = [
    re.compile(r"SandboxPostCopy", re.IGNORECASE),
    re.compile(r"DataMask", re.IGNORECASE),
    re.compile(r"data_mask", re.IGNORECASE),
    re.compile(r"runApexClass", re.IGNORECASE),
]

# Common PII field name patterns — signals fields that should be in a masking policy
_PII_FIELD_PATTERNS = [
    re.compile(r"\b(ssn|social.?security|national.?id)\b", re.IGNORECASE),
    re.compile(r"\b(dob|date.?of.?birth|birthdate)\b", re.IGNORECASE),
    re.compile(r"\b(passport|driver.?licen[sc]e)\b", re.IGNORECASE),
    re.compile(r"\bphi\b", re.IGNORECASE),
    re.compile(r"\bpii\b", re.IGNORECASE),
    re.compile(r"\b(credit.?card|card.?number|cvv|ccn)\b", re.IGNORECASE),
    re.compile(r"\b(bank.?account|routing.?number)\b", re.IGNORECASE),
    re.compile(r"\bmedical.?record\b", re.IGNORECASE),
]

# Masking type tokens in Data Mask configuration files
_MASKING_TYPE_TOKENS = {"RANDOM", "FAMILIAR_NAME", "UNIQUE", "NULL", "DELETE"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for sandbox data masking configuration signals. "
            "Reports missing SandboxPostCopy integration, potential unmasked PII fields, "
            "and other common Data Mask configuration issues."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_files(root: Path, pattern: str) -> list[Path]:
    """Recursively find files matching a glob pattern."""
    return sorted(root.rglob(pattern))


def check_sandbox_post_copy_present(manifest_dir: Path) -> list[str]:
    """Check whether any Apex class implements SandboxPostCopy."""
    issues: list[str] = []
    apex_files = find_files(manifest_dir, "*.cls")
    if not apex_files:
        return issues  # No Apex files to check

    found_post_copy = False
    found_data_mask_ref = False

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        if re.search(r"implements\s+SandboxPostCopy", content, re.IGNORECASE):
            found_post_copy = True
            # Check whether it references DataMask
            for pattern in _DATA_MASK_PATTERNS[1:]:  # skip SandboxPostCopy itself
                if pattern.search(content):
                    found_data_mask_ref = True
                    break

    if not found_post_copy:
        issues.append(
            "No Apex class implementing SandboxPostCopy found. "
            "Data Mask should be triggered automatically via SandboxPostCopy to prevent "
            "the window of PII exposure between sandbox refresh completion and manual masking."
        )
    elif found_post_copy and not found_data_mask_ref:
        issues.append(
            "SandboxPostCopy class found but it does not appear to reference DataMask. "
            "Verify the post-copy class invokes the Data Mask configuration, not just "
            "other post-refresh setup tasks."
        )

    return issues


def check_pii_field_names_in_apex(manifest_dir: Path) -> list[str]:
    """Warn when Apex files reference likely PII field names without masking commentary."""
    issues: list[str] = []
    apex_files = find_files(manifest_dir, "*.cls")

    for apex_file in apex_files:
        try:
            content = apex_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        for pattern in _PII_FIELD_PATTERNS:
            if pattern.search(content):
                # Check whether there is any masking-related comment nearby
                has_masking_comment = bool(
                    re.search(r"(mask|anonymi[sz]|redact|obfuscat)", content, re.IGNORECASE)
                )
                if not has_masking_comment:
                    issues.append(
                        f"{apex_file.name}: references likely PII field(s) "
                        f"(matched pattern: '{pattern.pattern}') with no masking commentary. "
                        "Confirm these fields are included in the Data Mask configuration."
                    )
                break  # one warning per file is enough

    return issues


def check_validation_rules_for_required_fields(manifest_dir: Path) -> list[str]:
    """Detect validation rules that enforce required constraints — these conflict with Null masking."""
    issues: list[str] = []
    # Validation rule metadata lives in object directories as .validationRule-meta.xml or inside
    # the object XML. Look for both patterns.
    vr_files = find_files(manifest_dir, "*.validationRule-meta.xml")
    object_files = find_files(manifest_dir, "*.object-meta.xml")

    required_check_pattern = re.compile(
        r"ISBLANK|ISNULL|NOT\s*\(.*ISBLANK|NOT\s*\(.*ISNULL", re.IGNORECASE
    )

    def _scan_file(path: Path) -> bool:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            return bool(required_check_pattern.search(content))
        except OSError:
            return False

    vr_with_required = [f for f in vr_files if _scan_file(f)]
    obj_with_required = [f for f in object_files if _scan_file(f)]

    if vr_with_required or obj_with_required:
        affected = [f.name for f in vr_with_required + obj_with_required]
        issues.append(
            f"Found {len(affected)} validation rule file(s) that enforce non-blank/non-null "
            f"constraints ({', '.join(affected[:5])}{'...' if len(affected) > 5 else ''}). "
            "If any of these fields are configured for Null/Delete masking in Data Mask, "
            "the masking job will abort mid-run. Review each validation rule and switch "
            "affected fields to Pseudonymous or Deterministic masking, or disable the rule "
            "before running Data Mask."
        )

    return issues


def check_data_mask_config_present(manifest_dir: Path) -> list[str]:
    """Check for any Data Mask managed-package configuration files."""
    issues: list[str] = []
    # Data Mask saves configurations as CustomMetadata records or in a managed package
    # namespace. Look for any file containing the DataMask namespace token.
    all_xml = find_files(manifest_dir, "*.xml")
    found_config = any(
        "datamask" in f.name.lower() or "DataMask" in f.name
        for f in all_xml
    )

    if not found_config:
        # Also scan content of CustomMetadata files
        cmd_files = find_files(manifest_dir, "*.md-meta.xml")
        for f in cmd_files:
            try:
                if "DataMask" in f.read_text(encoding="utf-8", errors="replace"):
                    found_config = True
                    break
            except OSError:
                continue

    if not found_config and (find_files(manifest_dir, "*.cls") or find_files(manifest_dir, "*.object-meta.xml")):
        issues.append(
            "No Data Mask configuration metadata detected in the manifest directory. "
            "If this org uses a Full Copy or Partial Copy sandbox with production data, "
            "a Data Mask policy should be configured and version-controlled. "
            "Note: Data Mask configurations may be stored inside the package namespace "
            "and not exported by default — verify in the sandbox org directly."
        )

    return issues


def check_sandbox_data_masking(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_sandbox_post_copy_present(manifest_dir))
    issues.extend(check_pii_field_names_in_apex(manifest_dir))
    issues.extend(check_validation_rules_for_required_fields(manifest_dir))
    issues.extend(check_data_mask_config_present(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_sandbox_data_masking(manifest_dir)

    if not issues:
        print("No sandbox data masking issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
