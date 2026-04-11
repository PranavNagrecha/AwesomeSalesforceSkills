#!/usr/bin/env python3
"""Checker script for Health Cloud Apex Extensions skill.

Scans Apex source files (.cls) under a manifest directory for known
Health Cloud anti-patterns: direct DML on clinical objects, missing
HealthCloudGA namespace prefix, and unconditional System.debug() calls
in clinical-data contexts.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_apex_extensions.py [--help]
    python3 check_health_cloud_apex_extensions.py --manifest-dir path/to/src
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns: direct DML on Health Cloud clinical objects
# ---------------------------------------------------------------------------
_CLINICAL_OBJECTS = [
    "CarePlan",
    "CarePlanGoal",
    "CarePlanProblem",
    "CarePlanTemplate__c",
    "ReferralRequest__c",
    "EhrPatientMedication",
    "PatientHealthCondition",
    "ClinicalEncounterCode",
]

# Matches: insert new CarePlan(...) or insert carePlanVar or update cp
# where cp is ambiguous — flag any direct DML near clinical object names.
_DIRECT_DML_PATTERN = re.compile(
    r"\b(insert|update|delete|upsert)\s+(new\s+)?("
    + "|".join(re.escape(obj) for obj in _CLINICAL_OBJECTS)
    + r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Patterns: missing HealthCloudGA namespace on CarePlanProcessorCallback
# ---------------------------------------------------------------------------
_MISSING_NAMESPACE_PATTERN = re.compile(
    r"\bimplements\s+CarePlanProcessorCallback\b",
    re.IGNORECASE,
)

# Correct form should include the namespace
_CORRECT_NAMESPACE_PATTERN = re.compile(
    r"\bimplements\s+HealthCloudGA\.CarePlanProcessorCallback\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Patterns: unconditional System.debug() referencing clinical variables
# ---------------------------------------------------------------------------
# Flag System.debug( calls that are NOT inside an if block checking a debug flag
# and that appear in files containing clinical object queries.
_SYSTEM_DEBUG_PATTERN = re.compile(r"\bSystem\.debug\s*\(", re.IGNORECASE)

_CLINICAL_FIELD_HINT = re.compile(
    r"(EhrPatientMedication|PatientHealthCondition|ClinicalEncounterCode"
    r"|AuthorizationFormConsent|MedicationName__c|Dosage__c|ConditionCode__c)",
    re.IGNORECASE,
)

# A debug gate check — if this appears in the same file, System.debug is gated
_DEBUG_GATE_PATTERN = re.compile(
    r"DebugSettings__mdt|IsDebugEnabled|debugEnabled|isDebugOn",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Patterns: callback class declared as public instead of global
# ---------------------------------------------------------------------------
_PUBLIC_CALLBACK_PATTERN = re.compile(
    r"\bpublic\s+(class|interface)\s+\w+\s+implements\s+HealthCloudGA\.",
    re.IGNORECASE,
)


def _scan_file(path: Path) -> list[str]:
    """Return issue strings for a single Apex file."""
    issues: list[str] = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        issues.append(f"{path}: cannot read file — {exc}")
        return issues

    lines = content.splitlines()

    # Check for direct DML on clinical objects
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Skip comment lines
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if _DIRECT_DML_PATTERN.search(line):
            issues.append(
                f"{path}:{lineno}: DIRECT_DML — Direct DML on a Health Cloud clinical "
                f"object detected. Use Health Cloud invocable actions (CreateCarePlan, "
                f"AddCarePlanGoal) or the ICC framework instead. Line: {stripped!r}"
            )

    # Check for CarePlanProcessorCallback without HealthCloudGA namespace
    if _MISSING_NAMESPACE_PATTERN.search(content) and not _CORRECT_NAMESPACE_PATTERN.search(content):
        issues.append(
            f"{path}: MISSING_NAMESPACE — 'implements CarePlanProcessorCallback' found "
            f"without 'HealthCloudGA.' namespace prefix. The interface will not resolve. "
            f"Use: implements HealthCloudGA.CarePlanProcessorCallback"
        )

    # Check for public (not global) class implementing HealthCloudGA interfaces
    for lineno, line in enumerate(lines, start=1):
        if _PUBLIC_CALLBACK_PATTERN.search(line):
            issues.append(
                f"{path}:{lineno}: NON_GLOBAL_CALLBACK — Class implementing a HealthCloudGA "
                f"interface must be declared 'global', not 'public'. Line: {line.strip()!r}"
            )

    # Check for unconditional System.debug() in files touching clinical data
    file_has_clinical_refs = bool(_CLINICAL_FIELD_HINT.search(content))
    file_has_debug_gate = bool(_DEBUG_GATE_PATTERN.search(content))

    if file_has_clinical_refs and not file_has_debug_gate:
        for lineno, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            if _SYSTEM_DEBUG_PATTERN.search(line):
                issues.append(
                    f"{path}:{lineno}: UNGATED_DEBUG — System.debug() in a class that "
                    f"references clinical object fields without a debug gate. "
                    f"PHI may be written to debug logs. Add a DebugSettings__mdt gate. "
                    f"Line: {stripped!r}"
                )

    return issues


def check_health_cloud_apex_extensions(manifest_dir: Path) -> list[str]:
    """Scan all .cls files under manifest_dir and return a list of issue strings."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    cls_files = list(manifest_dir.rglob("*.cls"))
    if not cls_files:
        # Not necessarily an error — might be a non-Apex project
        return issues

    for cls_file in sorted(cls_files):
        issues.extend(_scan_file(cls_file))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex source files for Health Cloud anti-patterns: "
            "direct DML on clinical objects, missing HealthCloudGA namespace, "
            "and ungated System.debug() calls near clinical field references."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata/source (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_health_cloud_apex_extensions(manifest_dir)

    if not issues:
        print("No Health Cloud Apex anti-patterns detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
