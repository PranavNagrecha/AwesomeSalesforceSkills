#!/usr/bin/env python3
"""Checker script for FSL Mobile App Extensions skill.

Scans a Salesforce metadata project directory for common FSL Mobile extension
issues described in references/gotchas.md and references/llm-anti-patterns.md.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_fsl_mobile.py [--help]
    python3 check_fsl_mobile.py --manifest-dir path/to/metadata
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# LWC module imports that are invalid inside HTML5 Mobile Extension Toolkit files
INVALID_LWC_IMPORTS = re.compile(
    r"""import\s+.*?from\s+['"](?:lwc|lightning/|@salesforce/)""",
    re.MULTILINE,
)

# Imperative Apex calls in LWC JS files (call inside a function, not @wire)
IMPERATIVE_APEX_CALL = re.compile(
    r"""import\s+\w+\s+from\s+['"]@salesforce/apex/[^'"]+['"]""",
    re.MULTILINE,
)
# If the same import is used with @wire that is fine; flag only when called imperatively
WIRE_DECORATOR = re.compile(r"@wire\s*\(", re.MULTILINE)

# Deep link payload that embeds field values rather than just IDs (heuristic)
DEEP_LINK_FIELD_VALUE = re.compile(
    r"""(fsl://[^\s'"]+[?&][A-Za-z_]+=[A-Za-z_]+__c[^&'"\s]{20,})""",
    re.MULTILINE,
)

# CMT objects referenced in Briefcase Builder-like XML (rough heuristic)
CMT_IN_PRIMING = re.compile(
    r"""<objectName>[A-Za-z0-9_]+__mdt</objectName>""",
    re.MULTILINE,
)

# Quick Action XML that is a LightningWebComponent action
LWC_QUICK_ACTION_TYPE = re.compile(
    r"""<type>LightningWebComponent</type>""",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def find_files(root: Path, suffix: str) -> list[Path]:
    return list(root.rglob(f"*{suffix}"))


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_lwc_imports_in_html5_extensions(manifest_dir: Path) -> list[str]:
    """Flag LWC module imports inside HTML5 Mobile Extension Toolkit files."""
    issues: list[str] = []
    # HTML5 toolkit files are typically .html or .js files under a
    # directory named 'mobileExtensions' or similar (heuristic)
    for js_file in manifest_dir.rglob("*.js"):
        if "mobileExtension" in js_file.parts or "mobile_extension" in str(js_file):
            content = read_text(js_file)
            if INVALID_LWC_IMPORTS.search(content):
                issues.append(
                    f"[HTML5-EXTENSION] LWC module import found in HTML5 Mobile Extension "
                    f"file: {js_file}. HTML5 Toolkit files cannot use LWC modules. "
                    f"Use REST API for Apex calls instead."
                )
    return issues


def check_imperative_apex_in_lwc(manifest_dir: Path) -> list[str]:
    """Warn when an LWC JS file imports an Apex method but has no @wire decorator."""
    issues: list[str] = []
    for js_file in find_files(manifest_dir, ".js"):
        # Skip test files and meta files
        if "test" in js_file.name.lower() or "meta" in js_file.name.lower():
            continue
        content = read_text(js_file)
        if IMPERATIVE_APEX_CALL.search(content) and not WIRE_DECORATOR.search(content):
            issues.append(
                f"[OFFLINE-RISK] {js_file}: Apex method imported but no @wire decorator "
                f"found. Imperative Apex calls fail offline in FSL Mobile. "
                f"Use @wire(apexMethod, {{...}}) to enable LDS caching for offline access."
            )
    return issues


def check_cmt_in_briefcase_config(manifest_dir: Path) -> list[str]:
    """Flag Custom Metadata Types referenced in Briefcase Builder XML."""
    issues: list[str] = []
    # Briefcase Builder config is stored in BriefcaseDefinition metadata
    for xml_file in find_files(manifest_dir, ".briefcaseDefinition-meta.xml"):
        content = read_text(xml_file)
        if CMT_IN_PRIMING.search(content):
            issues.append(
                f"[CMT-PRIMING] {xml_file}: Custom Metadata Type (__mdt) found in "
                f"Briefcase Builder definition. CMTs cannot be primed via Briefcase Builder. "
                f"Use a Custom Object cache populated via Apex wire adapter instead."
            )
    return issues


def check_quick_action_layout_placement(manifest_dir: Path) -> list[str]:
    """Warn if LWC Quick Actions exist but cannot be confirmed on a page layout."""
    issues: list[str] = []
    lwc_actions: list[str] = []

    for qa_file in find_files(manifest_dir, ".quickAction-meta.xml"):
        content = read_text(qa_file)
        if LWC_QUICK_ACTION_TYPE.search(content):
            lwc_actions.append(qa_file.stem.replace(".quickAction", ""))

    if not lwc_actions:
        return issues

    # Check if any page layout files exist and contain these action names
    layout_files = find_files(manifest_dir, ".layout-meta.xml")
    for action_name in lwc_actions:
        found_in_layout = False
        for layout_file in layout_files:
            content = read_text(layout_file)
            if action_name in content:
                found_in_layout = True
                break
        if not found_in_layout and layout_files:
            issues.append(
                f"[OFFLINE-LAYOUT] Quick Action '{action_name}' (LWC type) not found in "
                f"any page layout. LWC actions must be added to the main page layout — "
                f"not just App Builder — to be available offline in FSL Mobile."
            )

    return issues


def check_deep_link_payload_size(manifest_dir: Path) -> list[str]:
    """Warn about deep link URIs with potentially large payloads (field values embedded)."""
    issues: list[str] = []
    for js_file in find_files(manifest_dir, ".js"):
        content = read_text(js_file)
        for match in DEEP_LINK_FIELD_VALUE.finditer(content):
            uri = match.group(0)
            payload_bytes = len(uri.encode("utf-8"))
            if payload_bytes > 900_000:
                issues.append(
                    f"[DEEP-LINK-SIZE] {js_file}: Deep link URI exceeds 900 KB "
                    f"({payload_bytes} bytes). FSL deep link payloads are limited to 1 MB. "
                    f"Pass record IDs instead of field values in deep link parameters."
                )
    return issues


def check_enable_lightning_sdk_permission_set(manifest_dir: Path) -> list[str]:
    """Info: remind operator to verify permission set assignment."""
    issues: list[str] = []
    lwc_action_found = False
    for qa_file in find_files(manifest_dir, ".quickAction-meta.xml"):
        content = read_text(qa_file)
        if LWC_QUICK_ACTION_TYPE.search(content):
            lwc_action_found = True
            break

    if lwc_action_found:
        # Check if the permission set is declared in the metadata
        ps_files = find_files(manifest_dir, ".permissionset-meta.xml")
        sdk_ps_found = any(
            "EnableLightningSDKForFSL" in read_text(ps)
            or "Enable_Lightning_SDK" in read_text(ps)
            for ps in ps_files
        )
        if not sdk_ps_found:
            issues.append(
                "[PERMISSION-SET] LWC Quick Action detected but 'Enable Lightning SDK for "
                "FSL Mobile' permission set assignment not found in metadata. Verify that "
                "all FSL Mobile users are assigned this permission set — it is NOT included "
                "in standard Field Service Mobile license assignments."
            )
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Salesforce metadata for common FSL Mobile App Extension issues. "
            "Covers: HTML5 Toolkit LWC import errors, imperative Apex offline risk, "
            "CMT priming misconfiguration, offline page layout placement, "
            "deep link payload size, and permission set assignment."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def run_checks(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_lwc_imports_in_html5_extensions(manifest_dir))
    issues.extend(check_imperative_apex_in_lwc(manifest_dir))
    issues.extend(check_cmt_in_briefcase_config(manifest_dir))
    issues.extend(check_quick_action_layout_placement(manifest_dir))
    issues.extend(check_deep_link_payload_size(manifest_dir))
    issues.extend(check_enable_lightning_sdk_permission_set(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = run_checks(manifest_dir)

    if not issues:
        print("No FSL Mobile extension issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1


if __name__ == "__main__":
    sys.exit(main())
