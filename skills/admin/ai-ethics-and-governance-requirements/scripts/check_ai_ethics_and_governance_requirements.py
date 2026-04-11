#!/usr/bin/env python3
"""Checker script for AI Ethics and Governance Requirements skill.

Validates that a Salesforce metadata project contains the expected governance
artifacts: custom object definitions for AI audit logging, field history tracking
on AI-written fields, and presence of required disclosure markers in page layouts
or LWC configurations.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_ai_ethics_and_governance_requirements.py [--help]
    python3 check_ai_ethics_and_governance_requirements.py --manifest-dir path/to/metadata
    python3 check_ai_ethics_and_governance_requirements.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import re


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(root: Path, pattern: str) -> list[Path]:
    """Return all files matching a glob pattern under root."""
    return sorted(root.rglob(pattern))


def _file_contains(path: Path, pattern: str) -> bool:
    """Return True if the file content matches the given regex pattern."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return bool(re.search(pattern, text, re.IGNORECASE))
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_ai_decision_log_object(manifest_dir: Path) -> list[str]:
    """Check for a custom object intended to log AI decisions (audit trail).

    Governance requires a structured AI audit log beyond Field History Tracking.
    A custom object with 'AI' or 'Decision' or 'AuditLog' in its name is a
    strong signal this requirement has been addressed.
    """
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        # Not a SFDX metadata project — skip rather than false-alarm
        return issues

    object_dirs = [d for d in objects_dir.iterdir() if d.is_dir()]
    ai_log_pattern = re.compile(r"(AI.*(Decision|Log|Audit)|Audit.*AI|Decision.*Log)", re.IGNORECASE)
    found = [d for d in object_dirs if ai_log_pattern.search(d.name)]

    if not found:
        issues.append(
            "No AI Decision Log custom object found under objects/. "
            "Governance requires a structured audit object (e.g., AI_Decision_Log__c) "
            "to capture model version, confidence score, and contributing features — "
            "Field History Tracking alone is insufficient. "
            "See references/gotchas.md Gotcha 3 for details."
        )
    return issues


def check_field_history_on_ai_fields(manifest_dir: Path) -> list[str]:
    """Check that fields likely written by Einstein have Field History Tracking enabled.

    Looks for field metadata files whose names suggest AI-written values
    (Score, Prediction, Rating, Recommendation) and verifies that the
    containing object has Field History Tracking configured.
    """
    issues: list[str] = []
    objects_dir = manifest_dir / "objects"
    if not objects_dir.exists():
        return issues

    ai_field_pattern = re.compile(
        r"(Score|Prediction|Predicted|Rating|NBAction|NextBestAction|EinsteinScore)",
        re.IGNORECASE,
    )

    for obj_dir in sorted(objects_dir.iterdir()):
        if not obj_dir.is_dir():
            continue
        fields_dir = obj_dir / "fields"
        if not fields_dir.exists():
            continue

        ai_fields = [
            f for f in fields_dir.glob("*.field-meta.xml")
            if ai_field_pattern.search(f.stem)
        ]
        if not ai_fields:
            continue

        # Check if the object XML enables field history tracking
        obj_xml = obj_dir / f"{obj_dir.name}.object-meta.xml"
        if obj_xml.exists():
            content = obj_xml.read_text(encoding="utf-8", errors="replace")
            if "enableHistory" not in content and "trackHistory" not in content.lower():
                issues.append(
                    f"{obj_dir.name}: Contains likely AI-written fields "
                    f"({', '.join(f.stem for f in ai_fields)}) but the object metadata "
                    f"does not show enableHistory. Enable Field History Tracking AND "
                    f"supplement with a custom AI Decision Log for full audit coverage."
                )

    return issues


def check_disclosure_in_lwc(manifest_dir: Path) -> list[str]:
    """Check custom LWC components for AI disclosure language.

    Any LWC that imports getEinsteinPredictions, connectgen, or references
    Einstein/Agentforce APIs should contain disclosure text or a disclosure
    component reference. Absence of any disclosure language is a warning.
    """
    issues: list[str] = []
    lwc_dir = manifest_dir / "lwc"
    if not lwc_dir.exists():
        return issues

    einstein_import_pattern = re.compile(
        r"(getEinsteinPrediction|einstein|agentforce|generateText|llm|copilot)",
        re.IGNORECASE,
    )
    disclosure_pattern = re.compile(
        r"(generated.by.ai|ai.generated|powered.by.einstein|disclaimer|disclosure)",
        re.IGNORECASE,
    )

    for component_dir in sorted(lwc_dir.iterdir()):
        if not component_dir.is_dir():
            continue

        js_files = list(component_dir.glob("*.js"))
        html_files = list(component_dir.glob("*.html"))

        uses_einstein = any(
            _file_contains(f, einstein_import_pattern.pattern) for f in js_files
        )
        if not uses_einstein:
            continue

        has_disclosure = any(
            _file_contains(f, disclosure_pattern.pattern)
            for f in js_files + html_files
        )
        if not has_disclosure:
            issues.append(
                f"LWC component '{component_dir.name}' appears to use Einstein or "
                f"Agentforce APIs (matched AI-related import/call) but no disclosure "
                f"language was found in the component's HTML or JS. "
                f"Add an AI-generated content disclosure per the Salesforce Honesty pillar."
            )

    return issues


def check_governance_policy_document(manifest_dir: Path) -> list[str]:
    """Check for presence of a governance policy document in the project.

    Looks for a markdown or text file whose name or path suggests it is an
    AI governance policy artifact. This is a soft check — absence is a warning,
    not a blocker, since the policy may live outside the metadata project.
    """
    issues: list[str] = []
    policy_pattern = re.compile(
        r"(ai.governance|responsible.ai|ai.policy|ai.ethics)",
        re.IGNORECASE,
    )
    policy_files = [
        f for f in _find_files(manifest_dir, "*.md")
        if policy_pattern.search(f.name)
    ] + [
        f for f in _find_files(manifest_dir, "*.txt")
        if policy_pattern.search(f.name)
    ]

    if not policy_files:
        issues.append(
            "No AI governance policy document found in the project directory "
            "(expected a file with 'ai-governance', 'responsible-ai', or 'ai-policy' "
            "in its name). Governance policy documentation must exist before go-live. "
            "It may live outside this metadata project — confirm with the project team."
        )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_ai_ethics_and_governance_requirements(
    manifest_dir: Path,
    strict: bool = False,
) -> list[str]:
    """Return a list of issue strings found in the manifest directory.

    Each issue is a concrete, actionable governance gap.
    In strict mode, all issues are treated as blocking errors.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_ai_decision_log_object(manifest_dir))
    issues.extend(check_field_history_on_ai_fields(manifest_dir))
    issues.extend(check_disclosure_in_lwc(manifest_dir))
    issues.extend(check_governance_policy_document(manifest_dir))

    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata project for AI ethics and governance "
            "requirements gaps: AI audit log object, field history on AI-written "
            "fields, LWC disclosure markers, and governance policy presence."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata project (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit with code 1 on any issue (default: exit 0 with warnings only).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_ai_ethics_and_governance_requirements(manifest_dir, strict=args.strict)

    if not issues:
        print("AI governance checks passed — no issues found.")
        return 0

    for issue in issues:
        prefix = "ERROR" if args.strict else "WARN"
        print(f"{prefix}: {issue}", file=sys.stderr)

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
