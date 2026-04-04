#!/usr/bin/env python3
"""Checker script for Prompt Builder Templates skill.

Scans Salesforce metadata to detect the most common prompt-template deployment
mistake: packaging or deploying prompt templates without ensuring the
'Manage Prompt Templates' permission is included in at least one permission set
in the target org metadata.

Also checks for Apex @InvocableMethod classes that reference a capabilityType
and warns when the capability type string does not follow the expected Flex or
standard template format (a common source of silent grounding failures).

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_prompt_builder_templates.py [--help]
    python3 check_prompt_builder_templates.py --manifest-dir path/to/force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Prompt Builder Templates configuration and metadata for "
            "common issues:\n"
            "  1. Missing 'Manage Prompt Templates' user permission in all "
            "     permission sets found in the manifest directory.\n"
            "  2. Apex @InvocableMethod classes with malformed capabilityType "
            "     strings that will silently break prompt grounding.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root directory of the Salesforce metadata tree "
            "(e.g. force-app/main/default). Default: current directory."
        ),
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Permission set check
# ---------------------------------------------------------------------------

MANAGE_PROMPT_TEMPLATES_PERMISSION = "ManagePromptTemplates"

# Salesforce Metadata API uses a default namespace; strip it for portability.
_NS_RE = re.compile(r"\{[^}]*\}")


def _strip_ns(tag: str) -> str:
    return _NS_RE.sub("", tag)


def _perm_set_has_manage_prompt_templates(perm_set_path: Path) -> bool:
    """Return True if the .permissionset-meta.xml file grants ManagePromptTemplates."""
    try:
        tree = ET.parse(perm_set_path)
    except ET.ParseError:
        return False

    root = tree.getroot()
    for user_perm in root.iter():
        if _strip_ns(user_perm.tag) != "userPermissions":
            continue
        name_elem = None
        enabled_elem = None
        for child in user_perm:
            tag = _strip_ns(child.tag)
            if tag == "name":
                name_elem = child
            elif tag == "enabled":
                enabled_elem = child
        if (
            name_elem is not None
            and name_elem.text == MANAGE_PROMPT_TEMPLATES_PERMISSION
            and enabled_elem is not None
            and enabled_elem.text and enabled_elem.text.strip().lower() == "true"
        ):
            return True
    return False


def check_manage_prompt_templates_permission(manifest_dir: Path) -> list[str]:
    """Warn if no permission set in the manifest grants ManagePromptTemplates."""
    issues: list[str] = []

    perm_set_files = list(manifest_dir.rglob("*.permissionset-meta.xml"))
    if not perm_set_files:
        # No permission sets in this manifest tree — skip rather than false-alarm.
        return issues

    covered = [p for p in perm_set_files if _perm_set_has_manage_prompt_templates(p)]

    if not covered:
        issues.append(
            "No permission set in the metadata grants 'Manage Prompt Templates' "
            f"(userPermission: {MANAGE_PROMPT_TEMPLATES_PERMISSION}). "
            "Prompt templates deployed to an org where no user has this permission "
            "will install silently but cannot be invoked. "
            "Add this permission to at least one permission set that is assigned "
            "to template authors and any user who invokes templates via agent actions. "
            f"Scanned {len(perm_set_files)} permission set file(s): "
            + ", ".join(str(p.relative_to(manifest_dir)) for p in perm_set_files[:5])
            + ("..." if len(perm_set_files) > 5 else "")
        )
    return issues


# ---------------------------------------------------------------------------
# Apex capability type check
# ---------------------------------------------------------------------------

# Valid capability type prefixes per Salesforce documentation.
_VALID_CAPABILITY_PREFIXES = (
    "FlexTemplate://",
    "PromptTemplateType://einstein_gpt__salesEmail",
    "PromptTemplateType://einstein_gpt__fieldCompletion",
    "PromptTemplateType://einstein_gpt__recordSummary",
)

_CAPABILITY_TYPE_RE = re.compile(
    r"""capabilityType\s*=\s*['"]([^'"]+)['"]""",
    re.IGNORECASE,
)


def _extract_capability_types(apex_path: Path) -> list[str]:
    """Return all capabilityType values found in an Apex source file."""
    try:
        content = apex_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return _CAPABILITY_TYPE_RE.findall(content)


def _is_valid_capability_type(cap_type: str) -> bool:
    return any(cap_type.startswith(prefix) for prefix in _VALID_CAPABILITY_PREFIXES)


def check_apex_capability_types(manifest_dir: Path) -> list[str]:
    """Warn about Apex @InvocableMethod classes with malformed capabilityType strings."""
    issues: list[str] = []

    apex_files = list(manifest_dir.rglob("*.cls"))
    for apex_path in apex_files:
        cap_types = _extract_capability_types(apex_path)
        for cap_type in cap_types:
            if not _is_valid_capability_type(cap_type):
                issues.append(
                    f"Apex file '{apex_path.relative_to(manifest_dir)}' contains "
                    f"capabilityType='{cap_type}' which does not match a known "
                    "Salesforce prompt template capability type format. "
                    "Valid formats: FlexTemplate://<TemplateAPIName>, "
                    "PromptTemplateType://einstein_gpt__salesEmail, "
                    "PromptTemplateType://einstein_gpt__fieldCompletion, "
                    "PromptTemplateType://einstein_gpt__recordSummary. "
                    "A mismatch silently excludes this Apex data from the resolved "
                    "prompt — the template activates and runs without error but "
                    "grounded data is absent."
                )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check_prompt_builder_templates(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found in the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_manage_prompt_templates_permission(manifest_dir))
    issues.extend(check_apex_capability_types(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir).resolve()
    issues = check_prompt_builder_templates(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
        print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
