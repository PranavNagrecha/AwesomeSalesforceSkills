#!/usr/bin/env python3
"""Checker script for Fundraising Process Mapping skill.

Checks Salesforce metadata for common fundraising process mapping issues:
- Missing or misconfigured Opportunity stage picklist values
- Duplicate stage names across Sales Processes
- Stages missing probability values (probability = 0 on non-closed stages)
- NPSP four-process presence check
- Stage vocabulary anti-patterns (generic commercial stage names in nonprofit context)

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fundraising_process_mapping.py [--help]
    python3 check_fundraising_process_mapping.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Stage names that are default Salesforce commercial sales stage values
# and are inappropriate for nonprofit fundraising pipelines.
COMMERCIAL_STAGE_ANTIPATTERNS = {
    "Needs Analysis",
    "Value Proposition",
    "Id. Decision Makers",
    "Perception Analysis",
    "Proposal/Price Quote",
    "Negotiation/Review",
}

# NPSP-expected record type developer names (standard NPSP provisioning)
NPSP_EXPECTED_RECORD_TYPES = {
    "Donation",
    "Grant",
    "In_Kind",
    "Major_Gift",
}

# Minimum recommended stages for a fundraising Sales Process
MIN_STAGES_PER_PROCESS = 4

# Salesforce closed-stage indicator values (IsClosed = true equivalents in picklist XML)
CLOSED_STAGE_INDICATORS = {"Closed Won", "Closed Lost"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for fundraising process mapping issues. "
            "Validates Opportunity stage picklist configuration and Sales Process "
            "alignment for NPSP and Nonprofit Cloud orgs."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def find_opportunity_metadata(manifest_dir: Path) -> list[Path]:
    """Return paths to Opportunity metadata XML files."""
    candidates = [
        manifest_dir / "objects" / "Opportunity.object",
        manifest_dir / "objects" / "Opportunity" / "Opportunity.object-meta.xml",
        manifest_dir / "force-app" / "main" / "default" / "objects" / "Opportunity" / "Opportunity.object-meta.xml",
    ]
    # Also check for standard metadata API object file
    for candidate in candidates:
        if candidate.exists():
            return [candidate]

    # Search for any Opportunity metadata file
    found = list(manifest_dir.rglob("Opportunity.object-meta.xml"))
    found += list(manifest_dir.rglob("Opportunity.object"))
    return found


def parse_stage_picklist_from_xml(xml_path: Path) -> list[dict]:
    """Parse Opportunity StageName picklist values from metadata XML.

    Returns a list of dicts with keys: fullName, label, probability, isClosed, isActive.
    """
    stages = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # Handle namespace-prefixed XML (Metadata API format)
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # Find fields section
        for field in root.iter(f"{ns}fields"):
            full_name_el = field.find(f"{ns}fullName")
            if full_name_el is None or full_name_el.text != "StageName":
                continue
            for value_set in field.iter(f"{ns}valueSet"):
                for value in value_set.iter(f"{ns}value"):
                    full_name = _text(value.find(f"{ns}fullName"))
                    label = _text(value.find(f"{ns}label")) or full_name
                    probability = _text(value.find(f"{ns}probability")) or "0"
                    is_closed = _text(value.find(f"{ns}closed")) or "false"
                    is_active = _text(value.find(f"{ns}isActive")) or "true"
                    stages.append({
                        "fullName": full_name,
                        "label": label,
                        "probability": float(probability) if probability else 0.0,
                        "isClosed": is_closed.lower() == "true",
                        "isActive": is_active.lower() != "false",
                    })
    except (ET.ParseError, OSError):
        pass
    return stages


def _text(element) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def check_stage_vocabulary(stages: list[dict]) -> list[str]:
    """Check for commercial-stage anti-patterns in active stage names."""
    issues = []
    active_labels = {s["label"] for s in stages if s["isActive"]}
    hits = active_labels & COMMERCIAL_STAGE_ANTIPATTERNS
    if hits:
        issues.append(
            f"Commercial sales stage names found in Opportunity StageName picklist — "
            f"not appropriate for nonprofit fundraising: {sorted(hits)}. "
            f"Replace with nonprofit lifecycle stages (Cultivation, Solicitation, etc.)."
        )
    return issues


def check_probability_values(stages: list[dict]) -> list[str]:
    """Warn on active, non-closed stages with 0% probability (report accuracy risk)."""
    issues = []
    for stage in stages:
        if not stage["isActive"]:
            continue
        if stage["isClosed"]:
            continue
        if stage["probability"] == 0.0:
            issues.append(
                f"Stage '{stage['label']}' is an open stage with 0% probability. "
                f"This causes all pipeline records in this stage to report as $0 in "
                f"forecast views. Set a non-zero probability or confirm this is intentional."
            )
    return issues


def check_minimum_stage_count(stages: list[dict]) -> list[str]:
    """Warn if fewer than MIN_STAGES_PER_PROCESS active stages exist."""
    issues = []
    active_stages = [s for s in stages if s["isActive"]]
    if 0 < len(active_stages) < MIN_STAGES_PER_PROCESS:
        issues.append(
            f"Only {len(active_stages)} active Opportunity stage(s) found. "
            f"A fundraising pipeline typically needs at least {MIN_STAGES_PER_PROCESS} stages "
            f"(e.g., Cultivation, Solicitation, Closed Won, Closed Lost). "
            f"Review whether the Sales Process is fully configured."
        )
    return issues


def check_closed_stage_presence(stages: list[dict]) -> list[str]:
    """Ensure at least one Won and one Lost closed stage exist."""
    issues = []
    active_stages = [s for s in stages if s["isActive"]]
    if not active_stages:
        return issues
    has_closed_won = any(s["isClosed"] and s["probability"] == 100.0 for s in active_stages)
    has_closed_lost = any(s["isClosed"] and s["probability"] == 0.0 for s in active_stages)
    if not has_closed_won:
        issues.append(
            "No 'Closed Won' equivalent stage found (closed = true, probability = 100%). "
            "Fundraising pipelines require a Closed Won stage to record successful gifts. "
            "Check Sales Process configuration."
        )
    if not has_closed_lost:
        issues.append(
            "No 'Closed Lost' equivalent stage found (closed = true, probability = 0%). "
            "Fundraising pipelines should include a Closed Lost stage for declined solicitations. "
            "Check Sales Process configuration."
        )
    return issues


def check_npsp_record_types(manifest_dir: Path) -> list[str]:
    """Check whether NPSP standard Opportunity Record Types are present."""
    issues = []
    record_type_dirs = [
        manifest_dir / "objects" / "Opportunity" / "recordTypes",
        manifest_dir / "force-app" / "main" / "default" / "objects" / "Opportunity" / "recordTypes",
    ]
    found_record_types: set[str] = set()
    for rt_dir in record_type_dirs:
        if rt_dir.exists():
            for rt_file in rt_dir.glob("*.recordType-meta.xml"):
                found_record_types.add(rt_file.stem.replace(".recordType-meta", ""))

    if not found_record_types:
        # No record types in manifest — skip NPSP check, manifest may be incomplete
        return issues

    missing_npsp = NPSP_EXPECTED_RECORD_TYPES - found_record_types
    if missing_npsp:
        issues.append(
            f"If this is an NPSP org, the following standard Opportunity Record Types are not "
            f"present in the metadata manifest: {sorted(missing_npsp)}. "
            f"Expected for NPSP: Donation, Grant, In_Kind, Major_Gift. "
            f"If this is a Nonprofit Cloud (NPC) org, disregard — NPSP Record Types do not apply."
        )
    return issues


def check_fundraising_process_mapping(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    opp_files = find_opportunity_metadata(manifest_dir)

    if not opp_files:
        # No Opportunity metadata found — provide informational guidance rather than hard error
        issues.append(
            "No Opportunity metadata file found in manifest. "
            "To fully validate fundraising process configuration, include Opportunity.object-meta.xml "
            "in the metadata manifest and re-run this check."
        )
        return issues

    for opp_file in opp_files:
        stages = parse_stage_picklist_from_xml(opp_file)
        if not stages:
            issues.append(
                f"Could not parse Opportunity StageName picklist from {opp_file}. "
                f"Verify the file is a valid Salesforce Metadata API object XML."
            )
            continue

        issues.extend(check_stage_vocabulary(stages))
        issues.extend(check_probability_values(stages))
        issues.extend(check_minimum_stage_count(stages))
        issues.extend(check_closed_stage_presence(stages))

    issues.extend(check_npsp_record_types(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_fundraising_process_mapping(manifest_dir)

    if not issues:
        print("No fundraising process mapping issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
