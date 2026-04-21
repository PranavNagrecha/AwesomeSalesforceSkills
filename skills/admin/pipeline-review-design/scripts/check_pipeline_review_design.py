#!/usr/bin/env python3
"""Check Opportunity metadata for Pipeline Inspection readiness.

Pipeline Inspection surfaces deals in the forecast hierarchy via Stage →
ForecastCategoryName mapping. Common misconfigurations:

  - A Stage that maps to `Omitted` (deals disappear from inspection view).
  - Stage labels that imply a pipeline stage but aren't marked `IsActive`.
  - No `ForecastCategoryName` child on a Stage picklist value (defaults to
    Pipeline, which is sometimes intended — this is flagged as REVIEW, not
    ERROR).
  - Opportunity object missing the `StageName` picklist entirely (corrupt
    metadata export or scratch-org misconfiguration).

The checker reads standard Opportunity picklist metadata (either the
`StandardValueSet.OpportunityStage.standardValueSet-meta.xml` file or an
object-level `Opportunity.object-meta.xml` with inline picklist values) and
prints JSON findings plus a WARN to stderr when anything is off.

Usage:
    python3 check_pipeline_review_design.py path/to/force-app
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


STAGE_FILE_CANDIDATES = (
    "OpportunityStage.standardValueSet-meta.xml",
    "Opportunity.object-meta.xml",
)
NAMESPACE = "{http://soap.sforce.com/2006/04/metadata}"


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def child_text(element: ET.Element, name: str) -> str:
    for child in element:
        if local_name(child.tag) == name:
            return (child.text or "").strip()
    return ""


def discover_stage_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for candidate in STAGE_FILE_CANDIDATES:
        for match in root.rglob(candidate):
            if match.is_file():
                found.append(match)
    return sorted(set(found))


def audit_stage_values(path: Path) -> list[str]:
    findings: list[str] = []
    tree = ET.parse(path)
    root = tree.getroot()

    value_elements: list[ET.Element] = []
    for element in root.iter():
        if local_name(element.tag) in ("standardValue", "values"):
            value_elements.append(element)

    if not value_elements:
        findings.append(f"ERROR {path}: no Opportunity stage picklist values found")
        return findings

    for value in value_elements:
        label = child_text(value, "label") or child_text(value, "fullName") or "<unlabeled>"
        is_active = child_text(value, "isActive")
        forecast_cat = child_text(value, "forecastCategoryName")

        if is_active and is_active.lower() == "false":
            findings.append(f"WARN {path}: stage `{label}` is inactive — will not appear in Pipeline Inspection")
            continue

        if not forecast_cat:
            findings.append(f"REVIEW {path}: stage `{label}` has no ForecastCategoryName — will default to Pipeline")
        elif forecast_cat == "Omitted":
            findings.append(
                f"ISSUE {path}: stage `{label}` maps to forecastCategory=Omitted — deals in this stage WILL NOT appear in Pipeline Inspection"
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest_dir", nargs="?", default=".", help="Salesforce source root to scan")
    args = parser.parse_args()

    root = Path(args.manifest_dir).resolve()
    if not root.exists():
        print(f"ERROR: manifest-dir does not exist: {root}", file=sys.stderr)
        return 2

    files = discover_stage_files(root)
    if not files:
        print(
            json.dumps(
                {
                    "findings": [],
                    "summary": "No Opportunity stage metadata found under scanned root.",
                    "scanned_root": str(root),
                },
                indent=2,
            )
        )
        print("WARN: no Opportunity stage metadata under scanned root", file=sys.stderr)
        return 0

    findings: list[str] = []
    for path in files:
        findings.extend(audit_stage_values(path))

    print(
        json.dumps(
            {
                "findings": findings,
                "summary": f"Scanned {len(files)} stage-metadata file(s); {len(findings)} finding(s).",
                "scanned_root": str(root),
            },
            indent=2,
        )
    )

    has_issue = any(f.startswith(("ERROR", "ISSUE")) for f in findings)
    if has_issue:
        print(f"ERROR: {sum(1 for f in findings if f.startswith(('ERROR', 'ISSUE')))} hard finding(s) require action", file=sys.stderr)
        return 1
    if findings:
        print(f"WARN: {len(findings)} advisory finding(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
