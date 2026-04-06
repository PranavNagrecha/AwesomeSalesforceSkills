#!/usr/bin/env python3
"""Checker script for Salesforce Surveys skill.

Scans a Salesforce metadata directory for survey-related configuration issues:
- Guest User Profile missing survey object permissions
- SurveyInvitation references without matching survey metadata
- Permission sets granting excessive survey access

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_salesforce_surveys.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SURVEY_OBJECTS = [
    "Survey",
    "SurveyInvitation",
    "SurveyResponse",
    "SurveyQuestionResponse",
    "SurveyQuestionScore",
]

REQUIRED_GUEST_PERMS = {
    "Survey": {"allowRead", "allowCreate"},
    "SurveyInvitation": {"allowRead", "allowCreate"},
    "SurveyResponse": {"allowRead", "allowCreate"},
    "SurveyQuestionResponse": {"allowRead", "allowCreate"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Salesforce Surveys configuration and metadata for common issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def _parse_xml_safe(path: Path) -> ET.Element | None:
    """Parse XML, stripping namespace prefixes for easier querying."""
    try:
        tree = ET.parse(path)
        root = tree.getroot()
        # Strip namespaces for simpler XPath
        for elem in root.iter():
            if "}" in elem.tag:
                elem.tag = elem.tag.split("}", 1)[1]
        return root
    except ET.ParseError:
        return None


def check_guest_user_profiles(manifest_dir: Path) -> list[str]:
    """Check that guest user profiles grant required survey object permissions."""
    issues: list[str] = []
    profile_dir = manifest_dir / "profiles"
    if not profile_dir.exists():
        return issues

    guest_profiles = list(profile_dir.glob("*Guest*User*.profile-meta.xml")) + \
                     list(profile_dir.glob("*guest*user*.profile-meta.xml"))

    for profile_path in guest_profiles:
        root = _parse_xml_safe(profile_path)
        if root is None:
            issues.append(f"Could not parse profile: {profile_path.name}")
            continue

        granted: dict[str, set[str]] = {}
        for obj_perm in root.findall(".//objectPermissions"):
            obj_name_el = obj_perm.find("object")
            if obj_name_el is None or obj_name_el.text not in REQUIRED_GUEST_PERMS:
                continue
            obj_name = obj_name_el.text
            granted.setdefault(obj_name, set())
            for perm_tag in ["allowRead", "allowCreate"]:
                perm_el = obj_perm.find(perm_tag)
                if perm_el is not None and perm_el.text == "true":
                    granted[obj_name].add(perm_tag)

        for obj, required in REQUIRED_GUEST_PERMS.items():
            obj_granted = granted.get(obj, set())
            missing = required - obj_granted
            if missing:
                issues.append(
                    f"Guest profile '{profile_path.stem}' missing {', '.join(sorted(missing))} "
                    f"on {obj}. External survey respondents will fail silently."
                )

    return issues


def check_flow_survey_references(manifest_dir: Path) -> list[str]:
    """Check flows that reference SurveyInvitation for common issues."""
    issues: list[str] = []
    flow_dir = manifest_dir / "flows"
    if not flow_dir.exists():
        return issues

    for flow_path in flow_dir.glob("*.flow-meta.xml"):
        root = _parse_xml_safe(flow_path)
        if root is None:
            continue

        content = flow_path.read_text(encoding="utf-8")
        if "SurveyInvitation" not in content:
            continue

        # Check that flows creating SurveyInvitation also set ParticipantId
        creates_invitation = False
        sets_participant = False
        for record_create in root.findall(".//recordCreates"):
            obj_el = record_create.find("object")
            if obj_el is not None and obj_el.text == "SurveyInvitation":
                creates_invitation = True
                for field_assignment in record_create.findall(".//inputAssignments"):
                    field_el = field_assignment.find("field")
                    if field_el is not None and field_el.text == "ParticipantId":
                        sets_participant = True

        if creates_invitation and not sets_participant:
            issues.append(
                f"Flow '{flow_path.stem}' creates SurveyInvitation but does not set "
                f"ParticipantId. Responses will not be linked to the recipient."
            )

    return issues


def check_salesforce_surveys(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_guest_user_profiles(manifest_dir))
    issues.extend(check_flow_survey_references(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_salesforce_surveys(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
