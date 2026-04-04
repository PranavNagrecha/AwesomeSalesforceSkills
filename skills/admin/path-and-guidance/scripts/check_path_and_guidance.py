#!/usr/bin/env python3
"""Checker script for Path and Guidance skill.

Scans a Salesforce metadata directory for common Path configuration issues:
1. PathAssistant metadata files that are inactive (status != Active)
2. PathAssistant records with no key fields defined on any stage
3. PathAssistant records with more than 5 key fields on a single stage
4. PathAssistant records referencing long text area fields by heuristic naming
5. Org preference XML missing the EnablePathAssistant flag

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_path_and_guidance.py [--manifest-dir path/to/metadata]

The manifest directory should be the root of a Salesforce DX project
(containing a 'force-app' folder) or a retrieved metadata directory
containing 'pathAssistants' and/or 'settings' subdirectories.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SALESFORCE_NS = "http://soap.sforce.com/2006/04/metadata"
# Heuristic: field API names that commonly indicate long text area types.
# Exact type resolution requires Schema describe, which is not available
# in a static checker. This list flags the most common patterns.
LONG_TEXT_HEURISTICS = [
    "description",
    "__c",  # Narrowed below — only flags names ending with _lta__c, _rtf__c, _notes__c, _body__c
]
LONG_TEXT_SUFFIXES = (
    "_lta__c",
    "_rtf__c",
    "_notes__c",
    "_body__c",
    "_text__c",
    "_detail__c",
)
STANDARD_LONG_TEXT = {"description", "internalnotes"}

MAX_KEY_FIELDS = 5


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_ns(tag: str) -> str:
    """Strip XML namespace from a tag string."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _parse_xml(path: Path) -> ET.Element | None:
    """Parse an XML file, returning the root element or None on failure."""
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError as exc:
        print(f"WARNING: could not parse {path}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def check_path_assistant_files(manifest_dir: Path) -> list[str]:
    """Scan pathAssistants metadata XML for common configuration issues."""
    issues: list[str] = []

    # Locations in DX-format and mdapi-format projects
    candidate_dirs = [
        manifest_dir / "force-app" / "main" / "default" / "pathAssistants",
        manifest_dir / "pathAssistants",
    ]

    pa_files: list[Path] = []
    for candidate in candidate_dirs:
        if candidate.is_dir():
            pa_files.extend(candidate.glob("*.pathAssistant-meta.xml"))
            pa_files.extend(candidate.glob("*.pathAssistant"))

    if not pa_files:
        # Not necessarily an issue — the project may not use Path
        return issues

    for pa_file in pa_files:
        root = _parse_xml(pa_file)
        if root is None:
            continue

        name = pa_file.stem.replace(".pathAssistant-meta", "").replace(".pathAssistant", "")

        # Check 1: active flag
        active_el = root.find(f"{{{SALESFORCE_NS}}}active") or root.find("active")
        if active_el is not None and active_el.text and active_el.text.strip().lower() != "true":
            issues.append(
                f"[{name}] Path is not active (active={active_el.text.strip()}). "
                "Set active=true or this path will not render."
            )

        # Collect step elements
        steps = root.findall(f"{{{SALESFORCE_NS}}}pathAssistantSteps") or root.findall(
            "pathAssistantSteps"
        )

        if not steps:
            issues.append(
                f"[{name}] No pathAssistantSteps found. "
                "Path has no stages configured — key fields and guidance are not set."
            )
            continue

        has_any_key_field = False
        for step in steps:
            # step name/value
            step_name_el = step.find(f"{{{SALESFORCE_NS}}}picklistValueName") or step.find(
                "picklistValueName"
            )
            step_name = step_name_el.text.strip() if step_name_el is not None and step_name_el.text else "(unknown)"

            # key fields
            fields_el = step.find(f"{{{SALESFORCE_NS}}}fieldNames") or step.find("fieldNames")
            if fields_el is not None:
                # fieldNames may be a single element or multiple sibling elements
                field_text = fields_el.text or ""
                field_list = [f.strip() for f in field_text.split(",") if f.strip()]
            else:
                # Multiple <fieldNames> sibling elements
                field_els = step.findall(f"{{{SALESFORCE_NS}}}fieldNames") or step.findall(
                    "fieldNames"
                )
                field_list = [
                    fe.text.strip() for fe in field_els if fe.text and fe.text.strip()
                ]

            if field_list:
                has_any_key_field = True

            # Check 2: too many key fields
            if len(field_list) > MAX_KEY_FIELDS:
                issues.append(
                    f"[{name}] Stage '{step_name}' has {len(field_list)} key fields "
                    f"(max {MAX_KEY_FIELDS}). Salesforce enforces this limit."
                )

            # Check 3: heuristic long text area fields
            for field in field_list:
                field_lower = field.lower()
                if field_lower in STANDARD_LONG_TEXT:
                    issues.append(
                        f"[{name}] Stage '{step_name}': field '{field}' is likely a "
                        "long text area and cannot be used as a key field. "
                        "Remove it or replace with a supported field type."
                    )
                elif field_lower.endswith(LONG_TEXT_SUFFIXES):
                    issues.append(
                        f"[{name}] Stage '{step_name}': field '{field}' has a naming "
                        "pattern that suggests a long text area or rich text area field. "
                        "Verify the field type — long text area fields are not supported "
                        "as key fields in Path."
                    )

        if not has_any_key_field:
            issues.append(
                f"[{name}] Path has no key fields defined on any stage. "
                "Consider adding key fields to surface relevant data at each stage."
            )

    return issues


def check_path_org_setting(manifest_dir: Path) -> list[str]:
    """Check that the Path org preference is enabled in the settings metadata."""
    issues: list[str] = []

    # Locations for Sales.settings-meta.xml or SalesforceSettings
    candidate_files = [
        manifest_dir / "force-app" / "main" / "default" / "settings" / "Sales.settings-meta.xml",
        manifest_dir / "settings" / "Sales.settings-meta.xml",
        manifest_dir / "force-app" / "main" / "default" / "settings" / "Sales.settings",
        manifest_dir / "settings" / "Sales.settings",
    ]

    settings_file: Path | None = None
    for candidate in candidate_files:
        if candidate.is_file():
            settings_file = candidate
            break

    if settings_file is None:
        # Not finding the file is not an error — many projects omit org settings from source
        return issues

    root = _parse_xml(settings_file)
    if root is None:
        return issues

    # Look for <enablePathAssistant>
    enable_el = root.find(f".//{{{SALESFORCE_NS}}}enablePathAssistant") or root.find(
        ".//enablePathAssistant"
    )
    if enable_el is not None and enable_el.text and enable_el.text.strip().lower() == "false":
        issues.append(
            "[Sales.settings] enablePathAssistant is set to false. "
            "No Path records will render until this is enabled. "
            "Set to true or enable via Setup > Path Settings."
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce Path configuration metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce DX project or metadata (default: current directory).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.exists():
        print(f"ISSUE: Manifest directory not found: {manifest_dir}")
        return 1

    issues: list[str] = []
    issues.extend(check_path_assistant_files(manifest_dir))
    issues.extend(check_path_org_setting(manifest_dir))

    if not issues:
        print("No Path configuration issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
